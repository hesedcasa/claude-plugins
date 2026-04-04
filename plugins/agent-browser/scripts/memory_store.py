#!/usr/bin/env python3
"""
Agentic Browser Memory Store

Uses ChromaDB for semantic search over three types of browser navigation
memories, following the agentic memory patterns from Chroma's documentation:

- Semantic: Facts about websites (structure, quirks, auth methods, layouts)
- Procedural: Patterns and instructions for effective navigation
  (wait strategies, element selection tips, site-specific workarounds)
- Episodic: Successful task sequences that can be replayed or adapted

Sits alongside the existing SQLite checkpoint_db for structured data.
ChromaDB provides semantic similarity search so the agent can find
relevant memories by meaning, not just exact domain match — enabling
cross-domain pattern transfer.

Usage:
  from memory_store import BrowserMemoryStore

  store = BrowserMemoryStore()
  store.save(
      "Login form uses email + password, submit button labeled 'Sign in'",
      type="semantic", domain="app.example.com", path="/login")
  store.save(
      "Always wait for networkidle after clicking login — SPA redirect",
      type="procedural", domain="app.example.com", path="/login")
  store.save(
      "Login: open /login → fill @e1 email → fill @e2 password → click",
      type="episodic", domain="app.example.com", path="/login",
      task_type="login")

  # Semantic recall before browsing
  memories = store.recall(
      "how to log in to the admin panel", domain="app.example.com")

  # Generate injection context for a session
  context = store.generate_context(
      "app.example.com",
      task_description="navigate to user settings")
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

MEMORY_DIR = os.environ.get(
    "BROWSER_MEMORY_DIR", os.path.expanduser("~/.ai-browser-workflow")
)
CHROMA_DIR = os.path.join(MEMORY_DIR, "chroma_db")


def _chroma_available():
    """Check if chromadb is installed."""
    try:
        import importlib.util

        return importlib.util.find_spec("chromadb") is not None
    except Exception:
        return False


@dataclass
class MemoryRecord:
    """A single memory record retrieved from the store."""

    id: str
    content: str
    type: str  # semantic, procedural, episodic
    domain: str
    path: str = "/"
    confidence: float = 1.0
    access_count: int = 0
    created_at: str = ""
    last_accessed: str = ""
    source: str = "agent"  # agent, user, extraction
    task_type: str = ""
    distance: float = 0.0  # semantic distance (lower = more similar)


class BrowserMemoryStore:
    """
    ChromaDB-backed semantic memory for browser automation.

    Three memory types following the agentic memory pattern:
    - semantic: Facts about websites (layout, auth, quirks)
    - procedural: Instructions for effective navigation (tips, wait patterns)
    - episodic: Proven task sequences (step-by-step workflows)
    """

    def __init__(self, chroma_dir=None):
        import chromadb  # type: ignore[import-untyped]

        self.chroma_dir = chroma_dir or CHROMA_DIR
        os.makedirs(self.chroma_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name="browser_memory",
            metadata={"hnsw:space": "cosine"},
        )

    # ─── Write ──────────────────────────────────────────────
    def save(
        self,
        content: str,
        type: Literal["semantic", "procedural", "episodic"],
        domain: str,
        path: str = "/",
        confidence: float = 1.0,
        source: str = "agent",
        task_type: str = "",
    ) -> str:
        """
        Save a memory record. Returns the memory ID.

        Checks for near-duplicate content on the same domain before adding.
        If a very similar memory exists (distance < 0.15), the existing one
        is updated instead of creating a duplicate.
        """
        # Check for near-duplicates
        existing = self._find_duplicate(content, domain, type)
        if existing:
            return self._merge_memory(existing, content, confidence)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        mem_id = f"{type}_{domain}_{ts}"
        now = datetime.utcnow().isoformat()

        metadata = {
            "type": type,
            "domain": domain,
            "path": path,
            "confidence": confidence,
            "source": source,
            "access_count": 0,
            "created_at": now,
            "last_accessed": now,
            "task_type": task_type or "",
        }

        self.collection.add(
            ids=[mem_id],
            documents=[content],
            metadatas=[metadata],
        )
        return mem_id

    def _find_duplicate(self, content, domain, memory_type):
        """Check if a very similar memory exists for this domain+type."""
        if self.collection.count() == 0:
            return None

        try:
            where = {"$and": [{"domain": domain}, {"type": memory_type}]}
            results = self.collection.query(
                query_texts=[content],
                where=where,
                n_results=1,
            )
            if (
                results["ids"]
                and results["ids"][0]
                and results["distances"]
                and results["distances"][0]
            ):
                dist = results["distances"][0][0]
                if dist < 0.15:  # Very similar
                    return {
                        "id": results["ids"][0][0],
                        "content": results["documents"][0][0],
                        "metadata": results["metadatas"][0][0],
                        "distance": dist,
                    }
        except Exception:
            pass
        return None

    def _merge_memory(self, existing, new_content, new_confidence):
        """
        Merge new information into an existing memory (conflict resolution).
        Uses the 'version' strategy: keeps the newer content if confidence
        is higher, otherwise bumps access count to reinforce the memory.
        """
        meta = existing["metadata"]
        now = datetime.utcnow().isoformat()

        if new_confidence >= meta.get("confidence", 0.5):
            # Newer info has equal or higher confidence — update content
            self.collection.update(
                ids=[existing["id"]],
                documents=[new_content],
                metadatas=[
                    {
                        **meta,
                        "confidence": new_confidence,
                        "last_accessed": now,
                        "access_count": meta.get("access_count", 0) + 1,
                    }
                ],
            )
        else:
            # Just reinforce the existing memory
            self.collection.update(
                ids=[existing["id"]],
                metadatas=[
                    {
                        **meta,
                        "last_accessed": now,
                        "access_count": meta.get("access_count", 0) + 1,
                    }
                ],
            )
        return existing["id"]

    # ─── Read ───────────────────────────────────────────────
    def recall(
        self,
        query: str,
        domain: str | None = None,
        memory_type: str | None = None,
        n_results: int = 5,
        min_confidence: float = 0.0,
    ) -> list[MemoryRecord]:
        """
        Semantic search for relevant memories.

        Args:
            query: Natural language description of what you're looking for
            domain: Filter to a specific domain (optional — omit for
                cross-domain search)
            memory_type: Filter to semantic/procedural/episodic (optional)
            n_results: Max results to return
            min_confidence: Minimum confidence threshold
        """
        if self.collection.count() == 0:
            return []

        # Build where clause
        conditions = []
        if domain:
            conditions.append({"domain": domain})
        if memory_type:
            conditions.append({"type": memory_type})
        if min_confidence > 0:
            conditions.append({"confidence": {"$gte": min_confidence}})

        where = None
        if len(conditions) == 1:
            where = conditions[0]
        elif len(conditions) > 1:
            where = {"$and": conditions}

        kwargs = {
            "query_texts": [query],
            "n_results": min(n_results, self.collection.count()),
        }
        if where:
            kwargs["where"] = where

        try:
            results = self.collection.query(**kwargs)
        except Exception:
            return []

        records = []
        if results["ids"] and results["ids"][0]:
            for i, mem_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i]
                dist = results["distances"][0][i] if results.get("distances") else 0

                # Filter out low-relevance results
                # (distance > 1.0 in cosine = barely related)
                if dist > 1.2:
                    continue

                # Update access tracking
                now = datetime.utcnow().isoformat()
                try:
                    self.collection.update(
                        ids=[mem_id],
                        metadatas=[
                            {
                                **meta,
                                "access_count": (meta.get("access_count", 0) + 1),
                                "last_accessed": now,
                            }
                        ],
                    )
                except Exception:
                    pass

                records.append(
                    MemoryRecord(
                        id=mem_id,
                        content=results["documents"][0][i],
                        type=meta.get("type", ""),
                        domain=meta.get("domain", ""),
                        path=meta.get("path", "/"),
                        confidence=meta.get("confidence", 1.0),
                        access_count=meta.get("access_count", 0),
                        created_at=meta.get("created_at", ""),
                        last_accessed=meta.get("last_accessed", ""),
                        source=meta.get("source", ""),
                        task_type=meta.get("task_type", ""),
                        distance=dist,
                    )
                )

        return records

    def for_planning(
        self, domain: str, task_description: str | None = None
    ) -> list[MemoryRecord]:
        """
        Get memories useful for PLANNING a browser task.
        Returns semantic facts + episodic (past successful workflows).
        """
        query = task_description or f"browsing and navigating {domain}"

        # Domain-specific facts
        facts = self.recall(query, domain=domain, memory_type="semantic", n_results=5)

        # Past successful workflows (domain-specific)
        episodes = self.recall(
            query, domain=domain, memory_type="episodic", n_results=3
        )

        # Cross-domain episodes for similar tasks (if task_description given)
        cross_domain = []
        if task_description:
            cross_domain = self.recall(
                task_description, memory_type="episodic", n_results=2
            )
            # Remove duplicates already in episodes
            seen_ids = {e.id for e in episodes}
            cross_domain = [m for m in cross_domain if m.id not in seen_ids]

        return facts + episodes + cross_domain

    def for_execution(
        self, domain: str, action_context: str | None = None
    ) -> list[MemoryRecord]:
        """
        Get memories useful during EXECUTION (procedural tips).
        These are navigation instructions, wait strategies, and workarounds.
        """
        query = action_context or f"interacting with elements on {domain}"
        return self.recall(query, domain=domain, memory_type="procedural", n_results=5)

    # ─── Context Generation ─────────────────────────────────
    def generate_context(self, domain: str, task_description: str | None = None) -> str:
        """
        Generate a compact context block for injection into a browsing session.
        This is the primary output — what gets fed to Claude before browsing.
        """
        planning = self.for_planning(domain, task_description)
        execution = self.for_execution(domain, task_description)

        facts = [m for m in planning if m.type == "semantic"]
        episodes = [m for m in planning if m.type == "episodic"]
        procedures = execution

        # Nothing to inject
        if not facts and not episodes and not procedures:
            return ""

        lines = [f"# Browser Memory: {domain}\n"]

        if facts:
            lines.append("## Site Knowledge:")
            for f in facts:
                conf = f"[{f.confidence:.0%}]" if f.confidence < 1.0 else ""
                lines.append(f"- {f.content} {conf}".strip())

        if procedures:
            lines.append("\n## Navigation Tips:")
            for p in procedures:
                lines.append(f"- {p.content}")

        if episodes:
            lines.append("\n## Proven Workflows:")
            for e in episodes:
                domain_note = f" (from {e.domain})" if e.domain != domain else ""
                lines.append(f"- {e.content}{domain_note}")

        lines.append(
            "\n> If any of these memories seem outdated (elements not found, "
            "pages restructured), proceed with a fresh snapshot and the new "
            "information will be learned for next time."
        )

        return "\n".join(lines)

    # ─── Memory Maintenance ─────────────────────────────────
    def flag_outdated(self, memory_id: str, reason: str = ""):
        """
        Flag a memory as potentially outdated (e.g., website changed).
        Reduces its confidence so it ranks lower in future queries.
        """
        try:
            result = self.collection.get(ids=[memory_id], include=["metadatas"])
            if result["metadatas"]:
                meta = result["metadatas"][0]
                new_conf = max(0.1, meta.get("confidence", 1.0) * 0.5)
                self.collection.update(
                    ids=[memory_id],
                    metadatas=[{**meta, "confidence": new_conf}],
                )
        except Exception:
            pass

    def decay_stale_memories(self, days_threshold: int = 30):
        """
        Reduce confidence of memories not accessed in `days_threshold` days.
        Memories that are never accessed naturally fade.
        """
        if self.collection.count() == 0:
            return 0

        all_data = self.collection.get(include=["metadatas"])
        now = datetime.utcnow()
        decayed = 0

        for i, meta in enumerate(all_data["metadatas"]):
            last_accessed = meta.get("last_accessed", "")
            if not last_accessed:
                continue
            try:
                accessed_dt = datetime.fromisoformat(last_accessed)
                age_days = (now - accessed_dt).days
                if age_days > days_threshold and meta.get("confidence", 1.0) > 0.3:
                    decay_factor = 0.9 ** (age_days // days_threshold)
                    new_conf = max(0.1, meta["confidence"] * decay_factor)
                    self.collection.update(
                        ids=[all_data["ids"][i]],
                        metadatas=[{**meta, "confidence": new_conf}],
                    )
                    decayed += 1
            except (ValueError, TypeError):
                pass

        return decayed

    def delete_low_confidence(self, threshold: float = 0.15):
        """Remove memories with very low confidence (effectively forgotten)."""
        if self.collection.count() == 0:
            return 0

        all_data = self.collection.get(include=["metadatas"])
        to_delete = []
        for i, meta in enumerate(all_data["metadatas"]):
            if meta.get("confidence", 1.0) < threshold:
                to_delete.append(all_data["ids"][i])

        if to_delete:
            self.collection.delete(ids=to_delete)
        return len(to_delete)

    # ─── Stats ──────────────────────────────────────────────
    def get_stats(self) -> dict:
        """Get memory store statistics."""
        count = self.collection.count()
        if count == 0:
            return {
                "total": 0,
                "semantic": 0,
                "procedural": 0,
                "episodic": 0,
                "domains": [],
            }

        all_data = self.collection.get(include=["metadatas"])
        types = {}
        domains = set()
        sources = {}

        for meta in all_data["metadatas"]:
            t = meta.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
            domains.add(meta.get("domain", "unknown"))
            s = meta.get("source", "unknown")
            sources[s] = sources.get(s, 0) + 1

        return {
            "total": count,
            "semantic": types.get("semantic", 0),
            "procedural": types.get("procedural", 0),
            "episodic": types.get("episodic", 0),
            "domains": sorted(domains),
            "sources": sources,
        }

    def get_domain_summary(self, domain: str) -> dict:
        """Get a summary of memories for a specific domain."""
        if self.collection.count() == 0:
            return {"domain": domain, "total": 0}

        try:
            results = self.collection.get(
                where={"domain": domain},
                include=["metadatas", "documents"],
            )
        except Exception:
            return {"domain": domain, "total": 0}

        types = {}
        task_types = set()
        for meta in results["metadatas"]:
            t = meta.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
            if meta.get("task_type"):
                task_types.add(meta["task_type"])

        return {
            "domain": domain,
            "total": len(results["ids"]),
            "semantic": types.get("semantic", 0),
            "procedural": types.get("procedural", 0),
            "episodic": types.get("episodic", 0),
            "task_types": sorted(task_types),
        }
