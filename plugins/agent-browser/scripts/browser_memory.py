#!/usr/bin/env python3
"""
Browser Memory CLI

Unified entry point for all browser memory operations. Called by hooks
and can be used directly for debugging/inspection.

Commands:
  context <domain> [task]    Generate warm-start context for injection (PreToolUse)
  extract-session            Extract memories from latest session transcript (Stop hook)
  recall <query> [--domain]  Search memories by meaning
  save <type> <domain> <content>  Manually save a memory
  stats                      Show memory statistics
  domains                    List all known domains
  domain-info <domain>       Show detailed info for a domain
  decay                      Run memory decay on stale entries
  maintain                   Run full maintenance (decay + cleanup)

Environment:
  BROWSER_MEMORY_DIR    Base directory for memory storage (default: ~/.ai-browser-workflow)
  CHROMA_AVAILABLE      Set to "0" to force SQLite-only mode
"""

import json
import os
import re
import sys
from urllib.parse import urlparse

# Add scripts directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def _chroma_available():
    try:
        import chromadb
        return True
    except ImportError:
        return False


def _get_store():
    """Get memory store, or None if ChromaDB unavailable."""
    if os.environ.get("CHROMA_AVAILABLE") == "0":
        return None
    if not _chroma_available():
        return None
    from memory_store import BrowserMemoryStore
    return BrowserMemoryStore()


def _get_checkpoint_db():
    """Get the existing checkpoint database."""
    try:
        from checkpoint_db import CheckpointDB
        return CheckpointDB()
    except Exception:
        return None


def _extract_domain(url_str):
    """Extract domain from a URL string."""
    if not url_str:
        return None
    if not url_str.startswith("http"):
        url_str = f"https://{url_str}"
    try:
        parsed = urlparse(url_str)
        return parsed.hostname
    except Exception:
        return None


# ─── Commands ──────────────────────────────────────────────


def cmd_context_from_env(args):
    """
    Generate warm-start context by reading TOOL_INPUT from the environment.
    Called by the PreToolUse hook — more portable than shell regex (no grep -P needed).
    Extracts the URL from the bash command in TOOL_INPUT, then calls cmd_context.
    """
    tool_input = os.environ.get("TOOL_INPUT", "")
    if not tool_input:
        return

    # Match: agent-browser open <url>
    m = re.search(r"agent-browser\s+open\s+(https?://\S+)", tool_input)
    if not m:
        return

    url = m.group(1).rstrip('"\'')
    domain = _extract_domain(url)
    if not domain:
        return

    cmd_context([domain, url])


def cmd_context(args):
    """
    Generate warm-start context for a browsing session.
    Combines both ChromaDB semantic memory and SQLite checkpoint knowledge.
    This is called by the PreToolUse hook before agent-browser navigation.
    """
    if not args:
        return

    domain = _extract_domain(args[0]) or args[0]
    task_description = " ".join(args[1:]) if len(args) > 1 else None

    sections = []

    # 1. ChromaDB semantic memories (rich, cross-domain)
    store = _get_store()
    if store:
        chroma_context = store.generate_context(domain, task_description)
        if chroma_context:
            sections.append(chroma_context)

    # 2. SQLite checkpoint knowledge (structured, domain-specific)
    db = _get_checkpoint_db()
    if db:
        checkpoint_context = db.generate_warm_context(domain)
        # Only add if it has real content (not just the header)
        if checkpoint_context and len(checkpoint_context.strip().split("\n")) > 2:
            sections.append(checkpoint_context)
        db.close()

    if sections:
        print("\n\n".join(sections))


def cmd_extract_session(args):
    """
    Extract memories from the latest session transcript.
    Called by the Stop hook after a browsing session ends.

    Runs the existing checkpoint extraction AND extracts semantic memories
    into ChromaDB for future semantic search.
    """
    # Step 1: Run existing checkpoint extraction
    try:
        from checkpoint_extractor import find_latest_transcript, extract_from_transcript
        from checkpoint_db import CheckpointDB

        transcript_path = find_latest_transcript()
        if transcript_path:
            result = extract_from_transcript(transcript_path, source_type="file")

            # Step 2: Extract semantic memories from the checkpoints
            store = _get_store()
            if store and result and result.get("status") == "success":
                _extract_memories_from_result(store, result, transcript_path)

    except Exception as e:
        print(f"Note: Session extraction encountered an issue: {e}", file=sys.stderr)


def _extract_memories_from_result(store, result, transcript_path):
    """
    After checkpoint extraction, derive semantic/procedural/episodic memories
    and store them in ChromaDB.
    """
    db = _get_checkpoint_db()
    if not db:
        return

    session_id = result.get("session_id", "")
    domains = result.get("domains", [])

    for domain in domains:
        checkpoints = db.get_checkpoints_for_domain(domain)

        for cp in checkpoints:
            # Skip if from a different session (already processed)
            if cp.get("session_id") != session_id:
                continue

            path = cp.get("path", "/")
            task_type = cp.get("task_type", "")
            task_summary = cp.get("task_summary", "")

            # ── Episodic: Save successful task sequences ──
            if cp.get("success"):
                commands = json.loads(cp.get("commands_json", "[]"))
                if commands:
                    # Build a compact workflow description
                    steps = []
                    for cmd in commands:
                        action = cmd.get("action", "")
                        target = cmd.get("target", "")
                        value = cmd.get("value", "")
                        if action == "fill" and value:
                            # Redact potential secrets
                            if any(s in value.lower() for s in ["password", "secret", "token", "key"]):
                                value = "[REDACTED]"
                            steps.append(f"{action} {target} '{value}'")
                        elif action in ("open", "click", "wait", "snapshot", "press", "select"):
                            steps.append(f"{action} {target}".strip())

                    if steps:
                        workflow = f"{task_summary}: {' → '.join(steps[:10])}"
                        store.save(
                            content=workflow,
                            type="episodic",
                            domain=domain,
                            path=path,
                            confidence=cp.get("reliability", 1.0),
                            source="extraction",
                            task_type=task_type,
                        )

            # ── Semantic: Extract facts about the site from snapshots ──
            entry_snap = cp.get("entry_snapshot", "")
            if entry_snap and len(entry_snap) > 50:
                # Extract high-level page structure info
                fact = _summarize_snapshot_fact(domain, path, entry_snap, task_type)
                if fact:
                    store.save(
                        content=fact,
                        type="semantic",
                        domain=domain,
                        path=path,
                        confidence=0.8,
                        source="extraction",
                    )

            # ── Procedural: Extract lessons from pitfalls ──
            pitfalls = json.loads(cp.get("pitfalls_json", "[]"))
            for pit in pitfalls:
                tip = pit.get("avoid_tip") or pit.get("resolution") or pit.get("error_message", "")
                if tip and len(tip) > 10:
                    store.save(
                        content=f"On {domain}{path}: {tip}",
                        type="procedural",
                        domain=domain,
                        path=path,
                        confidence=0.9 if pit.get("resolved") else 0.6,
                        source="extraction",
                    )

    db.close()


def _summarize_snapshot_fact(domain, path, snapshot_text, task_type):
    """
    Extract a compact fact from a page snapshot.
    We look for key interactive elements to describe the page layout.
    """
    # Count interactive elements
    ref_count = len(re.findall(r'\[ref=e\d+\]', snapshot_text))
    if ref_count == 0:
        return None

    # Identify element types from the snapshot
    elements = []
    if re.search(r'textbox|input|text field', snapshot_text, re.I):
        elements.append("text inputs")
    if re.search(r'button', snapshot_text, re.I):
        elements.append("buttons")
    if re.search(r'link', snapshot_text, re.I):
        elements.append("links")
    if re.search(r'checkbox', snapshot_text, re.I):
        elements.append("checkboxes")
    if re.search(r'select|dropdown|combobox', snapshot_text, re.I):
        elements.append("dropdowns")
    if re.search(r'table', snapshot_text, re.I):
        elements.append("tables")

    if not elements:
        return None

    elem_desc = ", ".join(elements)
    fact = f"Page {path} on {domain} has {ref_count} interactive elements including {elem_desc}"
    if task_type:
        fact += f" (used for {task_type})"

    return fact


def cmd_recall(args):
    """Search memories by semantic similarity."""
    if not args:
        print("Usage: browser_memory.py recall <query> [--domain <domain>]")
        return

    domain = None
    query_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--domain" and i + 1 < len(args):
            domain = args[i + 1]
            i += 2
        else:
            query_parts.append(args[i])
            i += 1

    query = " ".join(query_parts)
    store = _get_store()
    if not store:
        print("ChromaDB not available. Install with: pip install chromadb")
        return

    records = store.recall(query, domain=domain, n_results=10)
    if not records:
        print(f"No memories found for: {query}")
        return

    print(f"\nMemories matching: {query}\n")
    for r in records:
        type_icon = {"semantic": "📌", "procedural": "🔧", "episodic": "📋"}.get(r.type, "❓")
        print(f"  {type_icon} [{r.type}] {r.content}")
        print(f"     Domain: {r.domain}{r.path} | Confidence: {r.confidence:.0%} | Used: {r.access_count}x")
        print()


def cmd_save(args):
    """Manually save a memory record."""
    if len(args) < 3:
        print("Usage: browser_memory.py save <semantic|procedural|episodic> <domain> <content>")
        return

    memory_type = args[0]
    domain = args[1]
    content = " ".join(args[2:])

    if memory_type not in ("semantic", "procedural", "episodic"):
        print(f"Invalid type: {memory_type}. Use semantic, procedural, or episodic.")
        return

    store = _get_store()
    if not store:
        print("ChromaDB not available. Install with: pip install chromadb")
        return

    mem_id = store.save(content, type=memory_type, domain=domain, source="user")
    print(f"Saved {memory_type} memory: {mem_id}")


def cmd_stats(args):
    """Show memory store statistics."""
    store = _get_store()
    db = _get_checkpoint_db()

    print("\n=== Browser Memory Statistics ===\n")

    if store:
        stats = store.get_stats()
        print("ChromaDB (Semantic Memory):")
        print(f"  Total memories:  {stats['total']}")
        print(f"  Semantic (facts): {stats['semantic']}")
        print(f"  Procedural (tips): {stats['procedural']}")
        print(f"  Episodic (workflows): {stats['episodic']}")
        print(f"  Domains: {', '.join(stats['domains']) if stats['domains'] else 'none'}")
    else:
        print("ChromaDB: not available (install with: pip install chromadb)")

    if db:
        cp_stats = db.get_stats()
        print(f"\nSQLite (Checkpoint DB):")
        print(f"  Sessions:     {cp_stats.get('sessions', 0)}")
        print(f"  Checkpoints:  {cp_stats.get('checkpoints', 0)}")
        print(f"  Commands:     {cp_stats.get('commands', 0)}")
        print(f"  Pitfalls:     {cp_stats.get('pitfalls', 0)}")
        print(f"  Nav edges:    {cp_stats.get('nav_edges', 0)}")
        avg = cp_stats.get('avg_success_rate')
        if avg is not None:
            print(f"  Success rate: {avg * 100:.0f}%")
        db.close()

    print()


def cmd_domains(args):
    """List all known domains across both stores."""
    all_domains = set()
    db_domains = []

    store = _get_store()
    if store:
        stats = store.get_stats()
        all_domains.update(stats.get("domains", []))

    db = _get_checkpoint_db()
    if db:
        db_domains = db.get_all_domains()
        for d in db_domains:
            all_domains.add(d["domain"])
        db.close()

    if not all_domains:
        print("No domains learned yet.")
        return

    print("\nKnown Domains:\n")
    for domain in sorted(all_domains):
        parts = []

        if store:
            summary = store.get_domain_summary(domain)
            if summary["total"] > 0:
                parts.append(
                    f"memories: {summary['total']} "
                    f"(S:{summary['semantic']} P:{summary['procedural']} E:{summary['episodic']})"
                )

        for d in db_domains:
            if d["domain"] == domain:
                parts.append(
                    f"checkpoints: {d['checkpoint_count']}, "
                    f"success: {d['success_rate'] * 100:.0f}%"
                )

        print(f"  {domain}")
        for p in parts:
            print(f"    {p}")
        print()


def cmd_domain_info(args):
    """Show detailed info for a specific domain."""
    if not args:
        print("Usage: browser_memory.py domain-info <domain>")
        return

    domain = args[0]
    store = _get_store()

    if store:
        # Show all memories for this domain
        all_types = ["semantic", "procedural", "episodic"]
        for mtype in all_types:
            records = store.recall(f"everything about {domain}", domain=domain, memory_type=mtype, n_results=20)
            if records:
                type_icon = {"semantic": "📌", "procedural": "🔧", "episodic": "📋"}[mtype]
                print(f"\n{type_icon} {mtype.upper()} memories:")
                for r in records:
                    print(f"  - {r.content}")
                    print(f"    conf={r.confidence:.0%} accessed={r.access_count}x")


def cmd_maintain(args):
    """Run maintenance: decay stale memories and clean up low-confidence ones."""
    store = _get_store()
    if not store:
        print("ChromaDB not available.")
        return

    decayed = store.decay_stale_memories(days_threshold=30)
    deleted = store.delete_low_confidence(threshold=0.15)

    print(f"Maintenance complete: {decayed} memories decayed, {deleted} removed")


def cmd_decay(args):
    """Run memory decay on stale entries."""
    store = _get_store()
    if not store:
        print("ChromaDB not available.")
        return

    days = int(args[0]) if args else 30
    decayed = store.decay_stale_memories(days_threshold=days)
    print(f"Decayed {decayed} stale memories (threshold: {days} days)")


# ─── Main ──────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "context": cmd_context,
        "context-from-env": cmd_context_from_env,
        "extract-session": cmd_extract_session,
        "recall": cmd_recall,
        "save": cmd_save,
        "stats": cmd_stats,
        "domains": cmd_domains,
        "domain-info": cmd_domain_info,
        "maintain": cmd_maintain,
        "decay": cmd_decay,
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"Unknown command: {cmd}")
        print_help()


def print_help():
    print("""
Browser Memory — Agentic Memory for Browser Automation

  Context (called by hooks):
    context <domain> [task]       Generate warm-start context for a session
    context-from-env              Generate context by reading TOOL_INPUT env var (PreToolUse hook)
    extract-session               Extract memories from latest transcript

  Query:
    recall <query> [--domain d]   Search memories by meaning
    domain-info <domain>          Show all memories for a domain

  Manual:
    save <type> <domain> <text>   Save a memory (semantic/procedural/episodic)

  Admin:
    stats                         Show memory statistics
    domains                       List all known domains
    maintain                      Run decay + cleanup
    decay [days]                  Decay stale memories (default: 30 days)

  Examples:
    python3 browser_memory.py context app.example.com "login to dashboard"
    python3 browser_memory.py recall "how to navigate to user settings"
    python3 browser_memory.py save procedural app.example.com "Wait for networkidle after login click"
    python3 browser_memory.py stats
    """)


if __name__ == "__main__":
    main()
