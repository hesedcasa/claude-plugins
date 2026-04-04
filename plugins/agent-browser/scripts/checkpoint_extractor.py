#!/usr/bin/env python3
"""
Checkpoint Extractor

The main post-session tool. Run this after a Claude Code session ends to:

1. Parse the session transcript
2. Extract all agent-browser commands + outputs
3. Group them into logical task checkpoints
4. Detect errors and generate pitfall avoidance tips
5. Store everything in the checkpoint database
6. Generate a warm-start context for next session

Usage:
  # Process a transcript file
  python3 checkpoint_extractor.py extract /path/to/transcript.jsonl

  # Process from Claude Code's default transcript location
  python3 checkpoint_extractor.py extract-latest

  # Process raw text piped from stdout
  cat session.log | python3 checkpoint_extractor.py extract-stdin

  # Generate warm context for a domain
  python3 checkpoint_extractor.py context example.com

  # Show all learned pitfalls for a domain
  python3 checkpoint_extractor.py pitfalls example.com

  # Show stats
  python3 checkpoint_extractor.py stats

Claude Code Hook (PostSession):
  Add to .claude/hooks.json:
  {
    "hooks": {
      "Stop": [{
        "command": "python3 /path/to/checkpoint_extractor.py extract-latest"
      }]
    }
  }
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from checkpoint_db import CheckpointDB
from transcript_parser import (
    ParsedCheckpoint,
    extract_commands_from_transcript,
    extract_from_file,
    group_commands_into_checkpoints,
    parse_single_command,
)


# ─── Transcript Discovery ──────────────────────────────────
def find_latest_transcript() -> str | None:
    """Find the most recent Claude Code transcript."""
    # Claude Code stores transcripts in ~/.claude/projects/
    claude_dir = Path.home() / ".claude" / "projects"

    if not claude_dir.exists():
        # Try alternative locations
        alternatives = [
            Path.home() / ".claude" / "sessions",
            Path.home() / ".config" / "claude" / "transcripts",
            Path.cwd() / ".claude" / "transcripts",
        ]
        for alt in alternatives:
            if alt.exists():
                claude_dir = alt
                break
        else:
            return None

    # Find most recent JSONL file
    jsonl_files = sorted(
        claude_dir.rglob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if jsonl_files:
        return str(jsonl_files[0])

    # Also check for .json files
    json_files = sorted(
        claude_dir.rglob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    return str(json_files[0]) if json_files else None


# ─── Main Extraction ───────────────────────────────────────
def extract_from_transcript(
    source: str, source_type: str = "file", db: CheckpointDB | None = None
) -> dict:
    """
    Main extraction pipeline.

    Args:
        source: file path, or text content
        source_type: 'file', 'text', or 'stdin'
        db: optional CheckpointDB instance

    Returns:
        dict with extraction results
    """
    own_db = db is None
    if own_db:
        db = CheckpointDB()

    try:
        # Step 1: Parse commands
        if source_type == "file":
            with open(source, "rb") as _f:
                transcript_hash = hashlib.md5(_f.read()).hexdigest()

            # Check if already processed
            existing = db.session_exists(transcript_hash)
            if existing:
                print(f"Session already processed (ID: {existing}). Skipping.")
                return {"status": "skipped", "session_id": existing}

            commands = extract_from_file(source)
        elif source_type == "text":
            transcript_hash = hashlib.md5(source.encode()).hexdigest()
            existing = db.session_exists(transcript_hash)
            if existing:
                return {"status": "skipped", "session_id": existing}
            lines = source.strip().split("\n")
            commands = extract_commands_from_transcript(lines)
        else:
            return {
                "status": "error",
                "message": f"Unknown source type: {source_type}",
            }

        if not commands:
            print("No agent-browser commands found in transcript.")
            return {"status": "empty", "commands_found": 0}

        # Step 2: Group into checkpoints
        checkpoints = group_commands_into_checkpoints(commands)

        if not checkpoints:
            print("Commands found but could not group into checkpoints.")
            return {
                "status": "no_checkpoints",
                "commands_found": len(commands),
            }

        # Step 3: Create session
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        domains = list(set(cp.domain for cp in checkpoints if cp.domain))
        total_errors = sum(1 for c in commands if not c.success)

        session_summary = _generate_session_summary(checkpoints, commands)

        db.create_session(
            session_id=session_id,
            transcript_hash=transcript_hash,
            source_file=source if source_type == "file" else None,
            summary=session_summary,
            domains=domains,
            total_cmds=len(commands),
            total_errors=total_errors,
        )

        # Step 4: Save checkpoints
        saved_ids = []
        for cp in checkpoints:
            cp_id = db.save_checkpoint(session_id, cp.to_dict())
            saved_ids.append(cp_id)

        # Step 5: Build navigation map
        _build_navigation_map(db, commands, checkpoints)

        # Step 6: Print summary
        result = {
            "status": "success",
            "session_id": session_id,
            "commands_found": len(commands),
            "checkpoints_created": len(checkpoints),
            "domains": domains,
            "errors_detected": total_errors,
            "pitfalls_recorded": sum(len(cp.pitfalls) for cp in checkpoints),
            "summary": session_summary,
        }

        _print_extraction_report(result, checkpoints)
        return result

    finally:
        if own_db:
            db.close()


def _generate_session_summary(
    checkpoints: list[ParsedCheckpoint], commands: list
) -> str:
    """Generate a one-paragraph summary of the session."""
    domains = list(set(cp.domain for cp in checkpoints if cp.domain))
    task_types = list(set(cp.task_type for cp in checkpoints if cp.task_type))
    total_errors = sum(1 for c in commands if not c.success)
    total_cmds = len(commands)

    domains_str = ", ".join(domains)
    parts = [
        f"Session with {total_cmds} agent-browser commands across"
        f" {len(domains)} domain(s): {domains_str}."
    ]
    parts.append(f"Tasks performed: {', '.join(task_types)}.")

    if total_errors:
        error_rate = total_errors / max(total_cmds, 1) * 100
        parts.append(
            f"Encountered {total_errors} errors"
            f" ({error_rate:.0f}% error rate)."
        )
    else:
        parts.append("No errors encountered.")

    successes = sum(1 for cp in checkpoints if cp.success)
    parts.append(
        f"{successes}/{len(checkpoints)} tasks completed successfully."
    )

    return " ".join(parts)


def _build_navigation_map(db: CheckpointDB, commands: list, checkpoints: list):
    """Build navigation graph from open/click commands."""
    prev_domain = None
    prev_path = None

    for cmd in commands:
        if cmd.action == "open" and cmd.url:
            try:
                from urllib.parse import urlparse

                url = (
                    cmd.url
                    if cmd.url.startswith("http")
                    else f"https://{cmd.url}"
                )
                parsed = urlparse(url)
                domain = parsed.hostname
                path = parsed.path or "/"

                if prev_domain == domain and prev_path and prev_path != path:
                    db.record_navigation(
                        domain, prev_path, path, action_type="navigate"
                    )

                prev_domain = domain
                prev_path = path
            except Exception:
                pass

        elif cmd.action == "click" and prev_domain:
            # If click leads to navigation (detected by subsequent
            # open or snapshot on different path).
            # We record potential navigations; confirmed on next 'open'
            pass


def _print_extraction_report(
    result: dict, checkpoints: list[ParsedCheckpoint]
):
    """Print a human-readable extraction report."""
    print()
    print("=" * 60)
    print("  CHECKPOINT EXTRACTION REPORT")
    print("=" * 60)
    print()
    print(f"  Session:      {result['session_id']}")
    print(f"  Commands:     {result['commands_found']}")
    print(f"  Checkpoints:  {result['checkpoints_created']}")
    print(f"  Domains:      {', '.join(result['domains'])}")
    print(f"  Errors:       {result['errors_detected']}")
    print(f"  Pitfalls:     {result['pitfalls_recorded']}")
    print()

    for i, cp in enumerate(checkpoints, 1):
        status = "✓" if cp.success else "✗"
        print(f"  {status} Checkpoint {i}: {cp.task_summary}")
        print(f"    Type: {cp.task_type} | Domain: {cp.domain}{cp.path or ''}")
        print(
            f"    Commands: {len(cp.commands)}"
            f" | Tokens: ~{cp.tokens_estimated}"
        )

        if cp.pitfalls:
            for pit in cp.pitfalls:
                pit_dict = pit if isinstance(pit, dict) else pit.__dict__
                tip = pit_dict.get(
                    "avoid_tip", pit_dict.get("error_message", "")
                )
                print(f"    ⚠️  {tip}")
        print()

    print("=" * 60)
    print()


# ─── Warm Context Generator ────────────────────────────────
def generate_warm_context(
    domain: str, task_type: str | None = None, db: CheckpointDB | None = None
) -> str:
    """
    Generate compact context to inject at the start of a new session.
    This is the primary output that makes future sessions more efficient.
    """
    own_db = db is None
    if own_db:
        db = CheckpointDB()

    try:
        return db.generate_warm_context(domain, task_type)
    finally:
        if own_db:
            db.close()


# ─── Manual Checkpoint Recording ────────────────────────────
def record_manual_checkpoint(
    domain: str,
    task_summary: str,
    task_type: str,
    commands_text: list[str],
    pitfall_notes: list[str] | None = None,
    path: str = "/",
    db: CheckpointDB | None = None,
):
    """
    Manually record a checkpoint from a list of command strings.
    Useful when you want to teach the system a known-good flow.
    """
    own_db = db is None
    if own_db:
        db = CheckpointDB()

    try:
        # Parse commands
        parsed_cmds = []
        for cmd_str in commands_text:
            result = parse_single_command(cmd_str)
            if result:
                for r in result:
                    parsed_cmds.append(
                        {
                            "raw": r.raw,
                            "action": r.action,
                            "target": r.target,
                            "value": r.value,
                            "output": None,
                            "success": True,
                            "output_tokens": 0,
                            "error": None,
                            "url": None,
                        }
                    )

        # Parse pitfalls
        pitfalls = []
        for note in pitfall_notes or []:
            pitfalls.append(
                {
                    "error_type": "manual_note",
                    "error_message": note,
                    "failed_command": None,
                    "resolution": None,
                    "resolved": True,
                    "avoid_tip": note,
                }
            )

        # Create a session for manual entries
        session_id = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        db.create_session(
            session_id=session_id,
            transcript_hash=hashlib.md5(
                json.dumps(commands_text).encode()
            ).hexdigest(),
            summary=f"Manual checkpoint: {task_summary}",
            domains=[domain],
            total_cmds=len(parsed_cmds),
        )

        # Save checkpoint
        cp_id = db.save_checkpoint(
            session_id,
            {
                "domain": domain,
                "path": path,
                "full_url": f"https://{domain}{path}",
                "task_summary": task_summary,
                "task_type": task_type,
                "commands": parsed_cmds,
                "pitfalls": pitfalls,
                "success": True,
                "tokens_estimated": 0,
            },
        )

        print(f"Recorded manual checkpoint (ID: {cp_id}): {task_summary}")
        return cp_id

    finally:
        if own_db:
            db.close()


# ─── CLI ────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print_help()
        return

    action = sys.argv[1]

    if action == "extract":
        if len(sys.argv) < 3:
            print(
                "Usage: python3 checkpoint_extractor.py"
                " extract <transcript_file>"
            )
            sys.exit(1)
        extract_from_transcript(sys.argv[2], source_type="file")

    elif action == "extract-latest":
        path = find_latest_transcript()
        if not path:
            print(
                "No Claude Code transcript found."
                " Checked ~/.claude/projects/ and alternatives."
            )
            print(
                "Provide a path manually:"
                " python3 checkpoint_extractor.py extract <file>"
            )
            sys.exit(1)
        print(f"Processing: {path}")
        extract_from_transcript(path, source_type="file")

    elif action == "extract-stdin":
        text = sys.stdin.read()
        extract_from_transcript(text, source_type="text")

    elif action == "context":
        if len(sys.argv) < 3:
            print(
                "Usage: python3 checkpoint_extractor.py"
                " context <domain> [task_type]"
            )
            sys.exit(1)
        domain = sys.argv[2]
        task_type = sys.argv[3] if len(sys.argv) > 3 else None
        print(generate_warm_context(domain, task_type))

    elif action == "pitfalls":
        if len(sys.argv) < 3:
            print("Usage: python3 checkpoint_extractor.py pitfalls <domain>")
            sys.exit(1)
        db = CheckpointDB()
        pitfalls = db.get_pitfalls_for_domain(sys.argv[2])
        if not pitfalls:
            print(f"No pitfalls recorded for {sys.argv[2]}")
        else:
            print(f"\nPitfalls for {sys.argv[2]}:\n")
            for p in pitfalls:
                msg = p["avoid_tip"] or p["error_message"]
                print(f"  [{p['error_type']}] {msg}")
                if p.get("failed_command"):
                    print(f"    → Failed: {p['failed_command']}")
                if p.get("resolution"):
                    print(f"    → Fix: {p['resolution']}")
                print(
                    f"    → Occurred: {p['occurrence_count']}x"
                    f" on {p.get('path', '/')}"
                )
                print()
        db.close()

    elif action == "domains":
        db = CheckpointDB()
        domains = db.get_all_domains()
        if not domains:
            print("No domains in checkpoint database yet.")
        else:
            print("\nLearned Domains:\n")
            for d in domains:
                print(f"  {d['domain']}")
                print(
                    f"    Checkpoints: {d['checkpoint_count']}"
                    f" | Commands: {d['total_commands']}"
                )
                print(
                    f"    Success: {d['success_rate'] * 100:.0f}%"
                    f" | Tasks: {d['task_types']}"
                )
                print()
        db.close()

    elif action == "stats":
        db = CheckpointDB()
        stats = db.get_stats()
        print(json.dumps(stats, indent=2, default=str))
        db.close()

    elif action == "record":
        # Manual recording:
        # record <domain> <task_type> <summary> -- cmd1 cmd2 ... -- pitfall ...
        if len(sys.argv) < 5:
            print(
                "Usage: python3 checkpoint_extractor.py record"
                " <domain> <task_type> <summary>"
                " -- <cmd1> <cmd2> ... [-- <pitfall1> ...]"
            )
            sys.exit(1)

        domain = sys.argv[2]
        task_type = sys.argv[3]
        summary = sys.argv[4]

        # Split on -- separator
        rest = sys.argv[5:]
        commands_text = []
        pitfall_notes = []
        current = commands_text

        for arg in rest:
            if arg == "--":
                if current is commands_text:
                    current = pitfall_notes
                continue
            current.append(arg)

        record_manual_checkpoint(
            domain, summary, task_type, commands_text, pitfall_notes
        )

    elif action == "nav":
        if len(sys.argv) < 3:
            print("Usage: python3 checkpoint_extractor.py nav <domain>")
            sys.exit(1)
        db = CheckpointDB()
        nav = db.get_navigation_graph(sys.argv[2])
        if not nav:
            print(f"No navigation data for {sys.argv[2]}")
        else:
            print(f"\nNavigation Map for {sys.argv[2]}:\n")
            for n in nav:
                label = f' "{n["link_text"]}"' if n.get("link_text") else ""
                print(
                    f"  {n['from_path']} →{label} {n['to_path']}"
                    f"  ({n['times_traversed']}x, {n['action_type']})"
                )
        db.close()

    else:
        print_help()


def print_help():
    print("""
Checkpoint Extractor — Post-Session Learning Tool

  Extract & Learn:
    extract <file>           Process a transcript file (JSONL or text)
    extract-latest           Auto-find and process the latest transcript
    extract-stdin            Process transcript from stdin

  Query Knowledge:
    context <domain> [type]  Generate warm-start context for a domain
    pitfalls <domain>        Show all pitfalls for a domain
    domains                  List all learned domains
    nav <domain>             Show navigation map for a domain
    stats                    Show global statistics

  Manual Recording:
    record <domain> <type> <summary> -- <cmd1> <cmd2> ... [-- <pitfall1> ...]
      Record a known-good checkpoint manually

  Example:
    python3 checkpoint_extractor.py record seeking.dev login \
      "Login to Seeking" -- \\
      'agent-browser open https://seeking.dev/login' \\
      'agent-browser fill @e2 "user@test.com"' \\
      'agent-browser fill @e3 "password123"' \\
      'agent-browser click @e1' -- \\
      'Wait for networkidle after clicking login button' \\
      'Login form refs change after page refresh — re-snapshot if stale'
    """)


if __name__ == "__main__":
    main()
