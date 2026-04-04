#!/usr/bin/env python3
"""
Transcript Parser

Extracts agent-browser commands and their outputs from Claude Code
session transcripts (JSONL format from ~/.claude/projects/).

Handles the real structure of Claude Code transcripts:
  - Tool use blocks contain bash commands
  - Tool result blocks contain the output
  - Assistant messages contain reasoning about what to do

The parser identifies:
  1. Every agent-browser command executed
  2. The output/error for each command
  3. The URL context (which page the agent was on)
  4. Groups of commands that form a logical task
"""

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Optional
from urllib.parse import urlparse

# ─── Data Structures ────────────────────────────────────────


@dataclass
class ParsedCommand:
    """A single agent-browser command extracted from the transcript."""

    raw: str  # full command string
    action: str  # open, click, fill, snapshot, wait, screenshot, etc.
    target: Optional[str] = None  # @e1, URL, selector
    value: Optional[str] = None  # fill text, wait condition
    output: Optional[str] = None  # stdout from execution
    error: Optional[str] = None  # stderr or error message
    success: bool = True
    output_tokens: int = 0  # estimated token cost of output
    url: Optional[str] = None  # URL when command was executed
    line_index: int = 0  # position in transcript


@dataclass
class ParsedPitfall:
    """An error that occurred and how it was handled."""

    error_type: (
        str  # timeout, element_not_found, navigation_error,
             # stale_ref, unexpected_state
    )
    error_message: str
    failed_command: Optional[str] = None
    resolution: Optional[str] = None
    resolved: bool = False
    avoid_tip: Optional[str] = None


@dataclass
class ParsedCheckpoint:
    """A logical task extracted from a group of commands."""

    domain: str
    path: Optional[str] = None
    full_url: Optional[str] = None
    task_summary: str = ""
    task_type: Optional[str] = (
        None  # login, navigate, fill_form, extract_data,
              # click_flow, verify, search
    )
    commands: list = field(default_factory=list)
    pitfalls: list = field(default_factory=list)
    success: bool = True
    start_index: int = 0
    end_index: int = 0
    tokens_estimated: int = 0
    entry_snapshot: Optional[str] = None
    exit_snapshot: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        d["commands"] = [
            asdict(c) if hasattr(c, "__dataclass_fields__") else c
            for c in self.commands
        ]
        d["pitfalls"] = [
            asdict(p) if hasattr(p, "__dataclass_fields__") else p
            for p in self.pitfalls
        ]
        return d


# ─── Command Parser ─────────────────────────────────────────

# All known agent-browser actions
AGENT_BROWSER_ACTIONS = {
    "open",
    "click",
    "dblclick",
    "fill",
    "snapshot",
    "screenshot",
    "wait",
    "select",
    "check",
    "uncheck",
    "hover",
    "scroll",
    "scrollintoview",
    "press",
    "type",
    "close",
    "back",
    "forward",
    "reload",
    "evaluate",
    "pdf",
    "network",
    "cookies",
    "storage",
    "console",
    "install",
    "session",
    "state",
    "set",
    "auth",
    "tabs",
    "find",
    "get",
}

AGENT_BROWSER_PATTERN = re.compile(
    r"agent-browser\s+"
    r"(?:--\S+\s+\S+\s+)*"  # optional flags like --session foo
    r"(\w+)"  # action
    r"(?:\s+(.+))?",  # rest of args
    re.DOTALL,
)

CHAINED_CMD_PATTERN = re.compile(r"&&\s*agent-browser\s+")


def parse_single_command(
    cmd_str: str, line_index: int = 0
) -> list[ParsedCommand]:
    """
    Parse one or more agent-browser commands from a string.
    Handles chained commands (&&) too.
    """
    # Split chained commands
    parts = re.split(r"\s*&&\s*", cmd_str.strip())
    results = []

    for part in parts:
        part = part.strip()
        m = AGENT_BROWSER_PATTERN.search(part)
        if not m:
            continue

        action = m.group(1).lower()
        if action not in AGENT_BROWSER_ACTIONS:
            # Skip false positives (e.g., "agent-browser" in comments)
            continue
        rest = (m.group(2) or "").strip()

        target = None
        value = None
        url = None

        if action == "open":
            target = rest.split()[0] if rest else None
            if target:
                target = target.strip("\"'")
            url = target
        elif action in (
            "click", "dblclick", "hover", "check", "uncheck", "scrollintoview"
        ):
            target = rest.split()[0] if rest else None
        elif action == "get":
            # e.g. get text @e1 / get value @e1 / get title / get url
            parts_split = rest.split(None, 1)
            # sub-command: text/value/title/url
            value = parts_split[0] if parts_split else None
            target = (
                parts_split[1].strip() if len(parts_split) > 1 else None
            )
        elif action == "find":
            # e.g. find role button click --name "Submit"
            target = rest  # pass the full args as target
        elif action == "state":
            # e.g. state save auth.json / state load auth.json
            target = rest
        elif action == "fill":
            fill_match = re.match(r'(@?\S+)\s+["\'](.+?)["\']', rest)
            if fill_match:
                target = fill_match.group(1)
                value = fill_match.group(2)
            else:
                parts_split = rest.split(None, 1)
                target = parts_split[0] if parts_split else None
                value = (
                    parts_split[1].strip("\"'")
                    if len(parts_split) > 1
                    else None
                )
        elif action == "select":
            sel_match = re.match(r'(@?\S+)\s+["\'](.+?)["\']', rest)
            if sel_match:
                target = sel_match.group(1)
                value = sel_match.group(2)
        elif action == "wait":
            target = rest  # e.g. "--load networkidle"
        elif action == "press":
            target = rest  # key name
        elif action == "scroll":
            target = rest
        elif action == "snapshot":
            target = rest  # flags like "-i"
        elif action == "screenshot":
            target = rest  # file path and flags
        elif action == "type":
            type_match = re.match(r'["\'](.+?)["\']', rest)
            if type_match:
                value = type_match.group(1)
            else:
                value = rest
        elif action == "evaluate":
            value = rest

        results.append(
            ParsedCommand(
                raw=part,
                action=action,
                target=target,
                value=value,
                url=url,
                line_index=line_index,
            )
        )

    return results


# ─── Error Classifier ───────────────────────────────────────

ERROR_PATTERNS = [
    (r"timeout|timed?\s*out|waiting.*exceeded", "timeout"),
    (
        r"element\s+not\s+found|no\s+element|cannot\s+find|ref.*not\s+found",
        "element_not_found",
    ),
    (r"stale|detached|disposed", "stale_ref"),
    (
        r"navigat|net::err|err_name|err_connection|failed\s+to\s+load",
        "navigation_error",
    ),
    (r"unexpected|assertion|expect.*fail", "unexpected_state"),
    (r"permission|forbidden|403|401|unauthorized", "auth_error"),
    (r"not\s+visible|not\s+interactable|obscured", "visibility_error"),
]


def classify_error(error_text: str) -> str:
    """Classify an error message into a category."""
    lower = error_text.lower()
    for pattern, error_type in ERROR_PATTERNS:
        if re.search(pattern, lower):
            return error_type
    return "unknown"


# ─── Transcript Parser ──────────────────────────────────────


def extract_commands_from_transcript(
    transcript_lines: list[str],
) -> list[ParsedCommand]:
    """
    Extract agent-browser commands and their outputs from raw transcript lines.

    Handles multiple transcript formats:
    - Plain text (command on one line, output on next lines)
    - JSONL (Claude Code's native format)
    - Markdown-formatted transcripts
    """
    commands = []
    i = 0

    while i < len(transcript_lines):
        line = transcript_lines[i].strip()

        # Skip empty lines and non-command lines
        if not line or "agent-browser" not in line:
            i += 1
            continue

        # Try to extract agent-browser command(s)
        parsed = parse_single_command(line, line_index=i)
        if not parsed:
            i += 1
            continue

        # Collect output lines (everything until next command or section break)
        output_lines = []
        j = i + 1
        while j < len(transcript_lines):
            next_line = transcript_lines[j].strip()
            # Stop at next command, empty line after output, or section marker
            if (
                "agent-browser" in next_line
                and AGENT_BROWSER_PATTERN.search(next_line)
            ):
                break
            if next_line.startswith("$") or next_line.startswith(">>>"):
                break
            if next_line.startswith("## ") or next_line.startswith("# "):
                break
            # Common Claude Code transcript markers
            if next_line in ("---", "===", "```"):
                j += 1
                break
            output_lines.append(transcript_lines[j])
            j += 1

        output_text = "\n".join(output_lines).strip()

        # Assign output to the last command in a chain
        for idx, cmd in enumerate(parsed):
            if idx == len(parsed) - 1 and output_text:
                cmd.output = output_text
                cmd.output_tokens = len(output_text) // 4
                # Check for errors
                if any(
                    err in output_text.lower()
                    for err in ["error", "failed", "timeout", "not found"]
                ):
                    cmd.success = False
                    cmd.error = output_text
            elif output_text and "Done" in output_text:
                cmd.output = "Done"
                cmd.output_tokens = 1

        commands.extend(parsed)
        i = j

    return commands


def extract_commands_from_jsonl(jsonl_path: str) -> list[ParsedCommand]:
    """
    Extract agent-browser commands from Claude Code's JSONL transcript.

    Claude Code transcript format (each line is a JSON object):
    - Assistant entry: {"type": "assistant", "message": {..., "content":
        [{"type": "tool_use", "name": "Bash", "input": {"command": "..."}}]}}
    - User/result entry: {"type": "user", "message": {..., "content":
        [{"type": "tool_result", "tool_use_id": "...", "content": "..."}]}}
    """
    commands = []
    pending_cmd = None

    with open(jsonl_path, "r") as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")

            # Real Claude Code format: assistant message wraps content
            # under "message" key
            if entry_type == "assistant":
                content = entry.get("message", {}).get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_use"
                            and block.get("name", "").lower() == "bash"
                        ):
                            cmd_text = (
                                block.get("input", {}).get("command", "")
                            )
                            if (
                                isinstance(cmd_text, str)
                                and "agent-browser" in cmd_text
                            ):
                                parsed = parse_single_command(
                                    cmd_text, line_index=line_num
                                )
                                if parsed:
                                    pending_cmd = parsed
                                    commands.extend(parsed)

            # Real Claude Code format: tool results inside "user" entries
            elif entry_type == "user" and pending_cmd:
                content = entry.get("message", {}).get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_result"
                        ):
                            output_text = block.get("content", "")
                            if isinstance(output_text, list):
                                output_text = "\n".join(
                                    item.get("text", "")
                                    for item in output_text
                                    if isinstance(item, dict)
                                )
                            if (
                                isinstance(output_text, str)
                                and output_text.strip()
                            ):
                                last = pending_cmd[-1]
                                last.output = output_text.strip()
                                last.output_tokens = len(output_text) // 4
                                if any(
                                    err in output_text.lower()
                                    for err in [
                                        "error", "failed",
                                        "timeout", "not found",
                                    ]
                                ):
                                    last.success = False
                                    last.error = output_text.strip()
                                pending_cmd = None
                                break

            # Legacy/alternative formats: direct tool_use or tool_result
            elif (
                entry_type in ("tool_use", "bash")
                or entry.get("name", "").lower() == "bash"
            ):
                cmd_text = (
                    entry.get("input", {}).get("command", "")
                    or entry.get("command", "")
                    or entry.get("content", "")
                )
                if isinstance(cmd_text, str) and "agent-browser" in cmd_text:
                    parsed = parse_single_command(
                        cmd_text, line_index=line_num
                    )
                    if parsed:
                        pending_cmd = parsed
                        commands.extend(parsed)

            elif entry_type in ("tool_result", "result") and pending_cmd:
                output_text = (
                    entry.get("content", "")
                    or entry.get("output", "")
                    or entry.get("stdout", "")
                )
                if isinstance(output_text, list):
                    output_text = "\n".join(
                        item.get("text", "")
                        for item in output_text
                        if isinstance(item, dict)
                    )
                if isinstance(output_text, str) and output_text.strip():
                    last = pending_cmd[-1]
                    last.output = output_text.strip()
                    last.output_tokens = len(output_text) // 4
                    if any(
                        err in output_text.lower()
                        for err in ["error", "failed", "timeout", "not found"]
                    ):
                        last.success = False
                        last.error = output_text.strip()
                pending_cmd = None

            # Fallback: assistant message with content directly
            # (no "message" wrapper)
            elif entry_type in ("message",):
                content = entry.get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_use"
                            and block.get("name", "").lower() == "bash"
                        ):
                            cmd_text = (
                                block.get("input", {}).get("command", "")
                            )
                            if (
                                isinstance(cmd_text, str)
                                and "agent-browser" in cmd_text
                            ):
                                parsed = parse_single_command(
                                    cmd_text, line_index=line_num
                                )
                                if parsed:
                                    pending_cmd = parsed
                                    commands.extend(parsed)

    return commands


def extract_from_file(file_path: str) -> list[ParsedCommand]:
    """Auto-detect format and extract commands."""
    with open(file_path, "r") as f:
        first_line = f.readline().strip()

    # Try JSONL first
    try:
        json.loads(first_line)
        return extract_commands_from_jsonl(file_path)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fall back to plain text
    with open(file_path, "r") as f:
        lines = f.readlines()
    return extract_commands_from_transcript(lines)


# ─── URL Tracker ────────────────────────────────────────────


class URLTracker:
    """Tracks the current URL as commands are processed."""

    def __init__(self):
        self.current_url = None
        self.current_domain = None
        self.current_path = None
        self.history = []

    def update(self, command: ParsedCommand):
        if command.action == "open" and command.target:
            url = command.target.strip("\"'")
            if not url.startswith("http"):
                url = f"https://{url}"
            try:
                parsed = urlparse(url)
                self.current_url = url
                self.current_domain = parsed.hostname
                self.current_path = parsed.path or "/"
                self.history.append(
                    {
                        "url": url,
                        "domain": self.current_domain,
                        "path": self.current_path,
                        "action": "navigate",
                    }
                )
            except Exception:
                pass

        # Detect navigation from output (redirects, SPA navigation)
        if command.output and "navigated to" in (command.output or "").lower():
            url_match = re.search(r"https?://\S+", command.output)
            if url_match:
                url = url_match.group()
                try:
                    parsed = urlparse(url)
                    old_path = self.current_path
                    self.current_url = url
                    self.current_domain = parsed.hostname
                    self.current_path = parsed.path or "/"
                    if old_path != self.current_path:
                        self.history.append(
                            {
                                "url": url,
                                "domain": self.current_domain,
                                "path": self.current_path,
                                "action": "redirect",
                            }
                        )
                except Exception:
                    pass

        command.url = self.current_url


# ─── Task Grouper ───────────────────────────────────────────

# Heuristics for detecting task boundaries
TASK_BOUNDARY_ACTIONS = {"open"}  # new page = likely new task
TASK_TYPE_SIGNALS = {
    "login": ["password", "sign in", "log in", "login", "username", "email"],
    "search": ["search", "query", "filter", "find"],
    "fill_form": ["fill", "select", "check", "submit"],
    "extract_data": ["snapshot", "evaluate", "innertext", "textcontent"],
    "navigate": ["open", "click", "back", "forward"],
    "verify": ["screenshot", "assert", "expect", "verify"],
}


def infer_task_type(commands: list[ParsedCommand]) -> str:
    """Infer the task type from the commands and their context."""
    all_text = " ".join(
        [
            f"{c.action} {c.target or ''} {c.value or ''} {c.output or ''}"
            for c in commands
        ]
    ).lower()

    scores = {}
    for task_type, signals in TASK_TYPE_SIGNALS.items():
        scores[task_type] = sum(1 for s in signals if s in all_text)

    if not any(scores.values()):
        return "navigate"

    return max(scores, key=lambda k: scores[k])


def generate_task_summary(
    commands: list[ParsedCommand], task_type: str, domain: str, path: str
) -> str:
    """Generate a human-readable summary of what the task did."""
    action_verbs = {
        "login": "Log in to",
        "search": "Search on",
        "fill_form": "Fill form on",
        "extract_data": "Extract data from",
        "navigate": "Navigate",
        "verify": "Verify state of",
        "click_flow": "Click through",
    }

    verb = action_verbs.get(task_type, "Interact with")

    # Try to add specifics from the commands
    details = []
    for c in commands:
        if c.action == "fill" and c.value:
            target_name = c.target or "field"
            # Don't include actual passwords/secrets
            if any(
                s in (c.value or "").lower()
                for s in ["password", "secret", "token", "key"]
            ):
                details.append(f"fill {target_name} with [REDACTED]")
            else:
                details.append(f"fill {target_name}")
        elif c.action == "click" and c.target:
            details.append(f"click {c.target}")
        elif c.action == "open":
            details.append(f"open {path}")

    summary = f"{verb} {domain}{path}"
    if details:
        summary += f" ({', '.join(details[:3])})"

    return summary


def group_commands_into_checkpoints(
    commands: list[ParsedCommand],
) -> list[ParsedCheckpoint]:
    """
    Group sequential commands into logical task checkpoints.

    Boundaries are detected by:
    - 'open' command (navigating to a new page)
    - Domain change
    - Long gap in sequence numbers
    - Snapshot after a sequence of actions (likely end of task)
    """
    if not commands:
        return []

    tracker = URLTracker()
    checkpoints = []
    current_group = []
    current_domain = None
    current_path = None

    def flush_group():
        nonlocal current_group
        if not current_group:
            return

        domain = current_domain or "unknown"
        path = current_path or "/"

        # Detect task type
        task_type = infer_task_type(current_group)

        # Collect pitfalls from failed commands
        pitfalls = []
        for idx, cmd in enumerate(current_group):
            if not cmd.success and cmd.error:
                error_type = classify_error(cmd.error)
                # Look ahead for resolution
                resolution = None
                if idx + 1 < len(current_group):
                    next_cmd = current_group[idx + 1]
                    if next_cmd.success:
                        resolution = f"Resolved by: {next_cmd.raw}"

                # Generate avoid tip
                avoid_tip = _generate_avoid_tip(error_type, cmd)

                pitfalls.append(
                    ParsedPitfall(
                        error_type=error_type,
                        error_message=cmd.error[:500],
                        failed_command=cmd.raw,
                        resolution=resolution,
                        resolved=resolution is not None,
                        avoid_tip=avoid_tip,
                    )
                )

        # Find entry/exit snapshots
        entry_snap = None
        exit_snap = None
        for cmd in current_group:
            if cmd.action == "snapshot" and cmd.output and cmd.success:
                if entry_snap is None:
                    entry_snap = cmd.output[:2000]
                exit_snap = cmd.output[:2000]

        # Total tokens
        total_tokens = sum(c.output_tokens for c in current_group)

        # Generate summary
        summary = generate_task_summary(current_group, task_type, domain, path)

        cp = ParsedCheckpoint(
            domain=domain,
            path=path,
            full_url=current_group[0].url if current_group else None,
            task_summary=summary,
            task_type=task_type,
            commands=[asdict(c) for c in current_group],
            pitfalls=[asdict(p) for p in pitfalls],
            success=all(c.success for c in current_group)
            or any(c.success for c in current_group[-2:]),
            start_index=current_group[0].line_index,
            end_index=current_group[-1].line_index,
            tokens_estimated=total_tokens,
            entry_snapshot=entry_snap,
            exit_snapshot=exit_snap,
        )
        checkpoints.append(cp)
        current_group = []

    for cmd in commands:
        tracker.update(cmd)

        # Check for task boundaries
        is_boundary = False

        # New page navigation
        if cmd.action == "open":
            is_boundary = True

        # Domain changed
        if (
            tracker.current_domain
            and tracker.current_domain != current_domain
            and current_domain is not None
        ):
            is_boundary = True

        if is_boundary and current_group:
            flush_group()

        current_domain = tracker.current_domain
        current_path = tracker.current_path
        current_group.append(cmd)

    # Flush remaining
    flush_group()

    return checkpoints


def _generate_avoid_tip(error_type: str, cmd: ParsedCommand) -> str:
    """Generate a human-readable tip for avoiding this error in the future."""
    tips = {
        "timeout": (
            f"Add explicit wait before '{cmd.action}'."
            " Use: agent-browser wait --load networkidle"
        ),
        "element_not_found": (
            f"Element '{cmd.target}' may have changed."
            " Take a fresh snapshot before interacting."
        ),
        "stale_ref": (
            f"Ref '{cmd.target}' became stale."
            " Re-snapshot the page to get updated refs."
        ),
        "navigation_error": (
            f"Navigation failed for '{cmd.target}'."
            " Verify URL is correct and accessible."
        ),
        "unexpected_state": (
            "Page was not in expected state."
            " Add a snapshot check before this step."
        ),
        "auth_error": (
            "Authentication required."
            " Ensure login checkpoint runs first."
        ),
        "visibility_error": (
            f"Element '{cmd.target}' not visible."
            " Try scrolling to it or waiting for it to appear."
        ),
    }
    return tips.get(
        error_type,
        f"Command '{cmd.raw}' failed. Review page state before retrying.",
    )
