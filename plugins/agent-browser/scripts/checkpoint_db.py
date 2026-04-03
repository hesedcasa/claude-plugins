#!/usr/bin/env python3
"""
Checkpoint Database

Stores post-session checkpoint data extracted from Claude Code transcripts.
Each checkpoint represents one logical task (login, search, fill form, etc.)
with the exact commands, errors encountered, and lessons learned.

Schema design:
  sessions       → one row per Claude Code session processed
  checkpoints    → one row per logical task extracted from a session
  commands       → individual agent-browser commands within a checkpoint
  pitfalls       → errors/failures and how they were resolved
  navigation_map → discovered URL structure per domain
"""

import json
import os
import sqlite3
from datetime import datetime

DB_DIR = os.environ.get(
    "CHECKPOINT_DB_DIR", os.path.expanduser("~/.ai-browser-workflow")
)
DB_PATH = os.path.join(DB_DIR, "checkpoints.db")

SCHEMA = """
-- Sessions: one per Claude Code session processed
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,       -- session ID or timestamp-based
    transcript_hash TEXT UNIQUE,            -- deduplicate re-processing
    source_file     TEXT,                   -- path to transcript file
    processed_at    TEXT DEFAULT (datetime('now')),
    total_commands  INTEGER DEFAULT 0,
    total_errors    INTEGER DEFAULT 0,
    domains_visited TEXT,                   -- JSON array of domains
    summary         TEXT                    -- AI-generated session summary
);

-- Checkpoints: one per logical task
CREATE TABLE IF NOT EXISTS checkpoints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    domain          TEXT NOT NULL,
    path            TEXT,                   -- URL path where task was performed
    full_url        TEXT,
    task_summary    TEXT NOT NULL,           -- e.g. "Login to dashboard", "Search for user"
    task_type       TEXT,                   -- login, navigate, fill_form, extract_data, click_flow, verify, search

    -- The full command sequence for replay
    commands_json   TEXT NOT NULL,           -- JSON array of {cmd, output, success, tokens_est}
    command_count   INTEGER DEFAULT 0,

    -- What was learned
    pitfalls_json   TEXT,                   -- JSON array of {error, cause, resolution, avoid_tip}
    success         INTEGER DEFAULT 1,      -- overall task succeeded?

    -- Timing & cost
    start_index     INTEGER,                -- position in transcript
    end_index       INTEGER,
    tokens_estimated INTEGER DEFAULT 0,

    -- For warm-start: snapshot of page state at task start
    entry_snapshot  TEXT,                   -- compact snapshot before task
    exit_snapshot   TEXT,                   -- compact snapshot after task

    -- Learning metadata
    replay_count    INTEGER DEFAULT 0,      -- how many times this was replayed
    last_replayed   TEXT,
    reliability     REAL DEFAULT 1.0,       -- success rate when replayed (0-1)

    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Commands: individual agent-browser invocations
CREATE TABLE IF NOT EXISTS commands (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id   INTEGER NOT NULL,
    sequence_num    INTEGER NOT NULL,       -- order within the checkpoint

    -- The raw command
    raw_command     TEXT NOT NULL,           -- exact command string
    action          TEXT NOT NULL,           -- open, click, fill, snapshot, wait, etc.
    target          TEXT,                   -- @e1, URL, selector
    value           TEXT,                   -- fill value, wait condition

    -- The output
    output          TEXT,                   -- raw output from agent-browser
    output_tokens   INTEGER DEFAULT 0,      -- estimated tokens consumed
    success         INTEGER DEFAULT 1,
    error_message   TEXT,                   -- if failed, what error

    -- Context
    url_at_execution TEXT,                  -- URL when command ran

    FOREIGN KEY (checkpoint_id) REFERENCES checkpoints(id) ON DELETE CASCADE
);

-- Pitfalls: errors encountered and lessons learned
CREATE TABLE IF NOT EXISTS pitfalls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id   INTEGER,                -- NULL if domain-level pitfall
    domain          TEXT NOT NULL,
    path            TEXT,

    -- What went wrong
    error_type      TEXT NOT NULL,           -- timeout, element_not_found, navigation_error, stale_ref, unexpected_state
    error_message   TEXT NOT NULL,
    failed_command  TEXT,                   -- the command that triggered it

    -- How it was fixed
    resolution      TEXT,                   -- what the agent did to recover
    resolved        INTEGER DEFAULT 0,

    -- Advice for future sessions
    avoid_tip       TEXT,                   -- human-readable tip: "Wait for networkidle before clicking submit"

    -- Frequency tracking
    occurrence_count INTEGER DEFAULT 1,
    last_occurred   TEXT DEFAULT (datetime('now')),

    created_at      TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (checkpoint_id) REFERENCES checkpoints(id) ON DELETE SET NULL
);

-- Navigation map: discovered URL structure
CREATE TABLE IF NOT EXISTS navigation_map (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain          TEXT NOT NULL,
    from_path       TEXT NOT NULL,
    to_path         TEXT NOT NULL,
    link_text       TEXT,                   -- text of the link/button clicked
    action_type     TEXT,                   -- click, navigate, redirect
    times_traversed INTEGER DEFAULT 1,
    last_traversed  TEXT DEFAULT (datetime('now')),
    UNIQUE(domain, from_path, to_path, action_type)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_checkpoints_domain ON checkpoints(domain);
CREATE INDEX IF NOT EXISTS idx_checkpoints_task ON checkpoints(domain, task_type);
CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_commands_checkpoint ON commands(checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_pitfalls_domain ON pitfalls(domain);
CREATE INDEX IF NOT EXISTS idx_pitfalls_type ON pitfalls(error_type);
CREATE INDEX IF NOT EXISTS idx_navmap_domain ON navigation_map(domain);
CREATE INDEX IF NOT EXISTS idx_navmap_from ON navigation_map(domain, from_path);
"""


class CheckpointDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ─── Sessions ──────────────────────────────────────────

    def create_session(
        self,
        session_id,
        transcript_hash,
        source_file=None,
        summary=None,
        domains=None,
        total_cmds=0,
        total_errors=0,
    ):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO sessions (id, transcript_hash, source_file, summary, domains_visited, total_commands, total_errors)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                transcript_hash,
                source_file,
                summary,
                json.dumps(domains or []),
                total_cmds,
                total_errors,
            ),
        )
        self.conn.commit()
        return session_id

    def session_exists(self, transcript_hash):
        row = self.conn.execute(
            "SELECT id FROM sessions WHERE transcript_hash = ?", (transcript_hash,)
        ).fetchone()
        return dict(row)["id"] if row else None

    # ─── Checkpoints ───────────────────────────────────────

    def save_checkpoint(self, session_id, checkpoint):
        """Save a single checkpoint. Returns the checkpoint ID."""
        cur = self.conn.execute(
            """
            INSERT INTO checkpoints (
                session_id, domain, path, full_url, task_summary, task_type,
                commands_json, command_count, pitfalls_json, success,
                start_index, end_index, tokens_estimated,
                entry_snapshot, exit_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                checkpoint["domain"],
                checkpoint.get("path"),
                checkpoint.get("full_url"),
                checkpoint["task_summary"],
                checkpoint.get("task_type"),
                json.dumps(checkpoint.get("commands", [])),
                len(checkpoint.get("commands", [])),
                json.dumps(checkpoint.get("pitfalls", [])),
                1 if checkpoint.get("success", True) else 0,
                checkpoint.get("start_index"),
                checkpoint.get("end_index"),
                checkpoint.get("tokens_estimated", 0),
                checkpoint.get("entry_snapshot"),
                checkpoint.get("exit_snapshot"),
            ),
        )
        cp_id = cur.lastrowid

        # Save individual commands
        for i, cmd in enumerate(checkpoint.get("commands", [])):
            self.conn.execute(
                """
                INSERT INTO commands (
                    checkpoint_id, sequence_num, raw_command, action, target, value,
                    output, output_tokens, success, error_message, url_at_execution
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    cp_id,
                    i + 1,
                    cmd.get("raw", ""),
                    cmd.get("action", ""),
                    cmd.get("target"),
                    cmd.get("value"),
                    cmd.get("output"),
                    cmd.get("output_tokens", 0),
                    1 if cmd.get("success", True) else 0,
                    cmd.get("error"),
                    cmd.get("url"),
                ),
            )

        # Save pitfalls
        for pit in checkpoint.get("pitfalls", []):
            self.conn.execute(
                """
                INSERT INTO pitfalls (
                    checkpoint_id, domain, path,
                    error_type, error_message, failed_command,
                    resolution, resolved, avoid_tip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    cp_id,
                    checkpoint["domain"],
                    checkpoint.get("path"),
                    pit.get("error_type", "unknown"),
                    pit.get("error_message", ""),
                    pit.get("failed_command"),
                    pit.get("resolution"),
                    1 if pit.get("resolved") else 0,
                    pit.get("avoid_tip"),
                ),
            )

        self.conn.commit()
        return cp_id

    # ─── Navigation Map ────────────────────────────────────

    def record_navigation(
        self, domain, from_path, to_path, link_text=None, action_type="click"
    ):
        self.conn.execute(
            """
            INSERT INTO navigation_map (domain, from_path, to_path, link_text, action_type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(domain, from_path, to_path, action_type) DO UPDATE SET
                times_traversed = times_traversed + 1,
                last_traversed = datetime('now'),
                link_text = COALESCE(?, link_text)
        """,
            (domain, from_path, to_path, link_text, action_type, link_text),
        )
        self.conn.commit()

    # ─── Queries ───────────────────────────────────────────

    def get_checkpoints_for_domain(self, domain, task_type=None):
        if task_type:
            rows = self.conn.execute(
                "SELECT * FROM checkpoints WHERE domain = ? AND task_type = ? ORDER BY reliability DESC, created_at DESC",
                (domain, task_type),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM checkpoints WHERE domain = ? ORDER BY created_at DESC",
                (domain,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_pitfalls_for_domain(self, domain):
        rows = self.conn.execute(
            """
            SELECT error_type, error_message, failed_command, resolution, avoid_tip,
                   occurrence_count, path
            FROM pitfalls WHERE domain = ?
            ORDER BY occurrence_count DESC
        """,
            (domain,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_navigation_graph(self, domain):
        rows = self.conn.execute(
            """
            SELECT from_path, to_path, link_text, action_type, times_traversed
            FROM navigation_map WHERE domain = ?
            ORDER BY times_traversed DESC
        """,
            (domain,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_best_checkpoint(self, domain, task_type):
        """Get the most reliable checkpoint for a task on a domain."""
        row = self.conn.execute(
            """
            SELECT * FROM checkpoints
            WHERE domain = ? AND task_type = ? AND success = 1
            ORDER BY reliability DESC, replay_count DESC, created_at DESC
            LIMIT 1
        """,
            (domain, task_type),
        ).fetchone()
        return dict(row) if row else None

    def get_all_domains(self):
        rows = self.conn.execute("""
            SELECT domain,
                   COUNT(*) as checkpoint_count,
                   SUM(command_count) as total_commands,
                   AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                   GROUP_CONCAT(DISTINCT task_type) as task_types
            FROM checkpoints GROUP BY domain ORDER BY checkpoint_count DESC
        """).fetchall()
        return [dict(r) for r in rows]

    def generate_warm_context(self, domain, task_type=None):
        """
        Generate a compact context block to inject into a new session.
        This is the key output — what gets fed to the AI before browsing.
        """
        lines = [f"# Checkpoint Knowledge: {domain}\n"]

        # Best checkpoints for known tasks
        checkpoints = self.get_checkpoints_for_domain(domain, task_type)
        if checkpoints:
            lines.append("## Known Tasks:")
            seen_tasks = set()
            for cp in checkpoints:
                if cp["task_type"] in seen_tasks:
                    continue
                seen_tasks.add(cp["task_type"])
                cmds = json.loads(cp["commands_json"])
                cmd_summary = " → ".join(
                    f"{c['action']} {c.get('target', '')}".strip() for c in cmds[:8]
                )
                lines.append(f"\n### {cp['task_summary']} ({cp['task_type']})")
                lines.append(f"Path: {cp.get('path', '/')}")
                lines.append(f"Steps: {cmd_summary}")
                lines.append(
                    f"Reliability: {cp['reliability'] * 100:.0f}% ({cp['command_count']} commands)"
                )

        # Pitfalls to avoid
        pitfalls = self.get_pitfalls_for_domain(domain)
        if pitfalls:
            lines.append("\n## Pitfalls to Avoid:")
            for pit in pitfalls[:10]:
                tip = (
                    pit.get("avoid_tip")
                    or pit.get("resolution")
                    or pit["error_message"]
                )
                lines.append(f"- ⚠️ {tip}")
                if pit.get("failed_command"):
                    lines.append(f"  Failed cmd: {pit['failed_command']}")

        # Navigation shortcuts
        nav = self.get_navigation_graph(domain)
        if nav:
            lines.append("\n## Navigation Shortcuts:")
            for n in nav[:10]:
                label = f' "{n["link_text"]}"' if n.get("link_text") else ""
                lines.append(
                    f"  {n['from_path']} →{label} {n['to_path']} (used {n['times_traversed']}x)"
                )

        return "\n".join(lines)

    def record_replay(self, checkpoint_id, success):
        """Update replay stats after a checkpoint is replayed."""
        cp = self.conn.execute(
            "SELECT replay_count, reliability FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        ).fetchone()
        if not cp:
            return
        cp = dict(cp)
        count = cp["replay_count"] + 1
        # Exponential moving average for reliability
        alpha = 0.3
        new_rel = alpha * (1.0 if success else 0.0) + (1 - alpha) * cp["reliability"]
        self.conn.execute(
            """
            UPDATE checkpoints SET replay_count = ?, reliability = ?, last_replayed = datetime('now'), updated_at = datetime('now')
            WHERE id = ?
        """,
            (count, new_rel, checkpoint_id),
        )
        self.conn.commit()

    def get_stats(self):
        return dict(
            self.conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM sessions) as sessions,
                (SELECT COUNT(*) FROM checkpoints) as checkpoints,
                (SELECT COUNT(*) FROM commands) as commands,
                (SELECT COUNT(*) FROM pitfalls) as pitfalls,
                (SELECT COUNT(DISTINCT domain) FROM checkpoints) as domains,
                (SELECT COUNT(*) FROM navigation_map) as nav_edges,
                (SELECT AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) FROM checkpoints) as avg_success_rate
        """).fetchone()
        )

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import sys

    db = CheckpointDB()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "stats":
        print(json.dumps(db.get_stats(), indent=2, default=str))
    elif cmd == "domains":
        for d in db.get_all_domains():
            print(
                f"  {d['domain']}: {d['checkpoint_count']} checkpoints, {d['task_types']}, {d['success_rate'] * 100:.0f}% success"
            )
    elif cmd == "context" and len(sys.argv) > 2:
        print(
            db.generate_warm_context(
                sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None
            )
        )
    elif cmd == "pitfalls" and len(sys.argv) > 2:
        for p in db.get_pitfalls_for_domain(sys.argv[2]):
            print(f"  [{p['error_type']}] {p['avoid_tip'] or p['error_message']}")
            if p.get("failed_command"):
                print(f"    cmd: {p['failed_command']}")
    else:
        print(
            "Usage: python3 checkpoint_db.py [stats|domains|context <domain>|pitfalls <domain>]"
        )
    db.close()
