---
name: agent-browser
description: Automates browser interactions for web testing, form filling, screenshots, and data extraction. Learns from every browsing session — remembers navigation patterns, pitfalls, and proven workflows so repeat visits are faster and more reliable. Use when the user needs to navigate websites, interact with web pages, fill forms, take screenshots, test web applications, or extract information from web pages.
context: fork
agent: Explore
allowed-tools: Read, Write, Glob, Grep, Bash(agent-browser *), Bash(python3 *)
---

# Browser Automation with agent-browser

## Quick start

```bash
agent-browser open <url>        # Navigate to page
agent-browser snapshot -i       # Get interactive elements with refs
agent-browser click @e1         # Click element by ref
agent-browser fill @e2 "text"   # Fill input by ref
agent-browser close             # Close browser
```

## Core workflow

1. Navigate: `agent-browser open <url>`
2. Snapshot: `agent-browser snapshot -i` (returns elements with refs like `@e1`, `@e2`)
3. Interact using refs from the snapshot
4. Re-snapshot after navigation or significant DOM changes

## Agentic Memory System

This plugin learns from every browsing session using a two-layer memory system:

### How It Works

**Before browsing** (automatic via PreToolUse hook):
- Queries **ChromaDB** for semantically relevant memories (facts about the site, navigation tips, proven workflows)
- Queries **SQLite** for structured checkpoint knowledge (exact command sequences, pitfalls, navigation graph)
- Injects the combined context so you start each session with everything learned from previous visits

**After browsing** (automatic via Stop hook):
- Extracts all agent-browser commands from the session transcript
- Groups them into logical task checkpoints (login, search, form fill, etc.)
- Classifies and stores three types of memories:
  - **Semantic**: Facts about websites (page structure, element types, auth methods)
  - **Procedural**: Tips for effective navigation (wait strategies, pitfall avoidance)
  - **Episodic**: Proven task sequences that can be replayed
- Runs memory maintenance (decays stale memories, cleans up unreliable ones)

**Cross-domain learning**: Patterns learned on one website help with similar sites. If you've logged into 5 different apps, the agent knows the general "login flow" pattern.

**Self-correcting**: If stored steps no longer work (website redesigned), the agent proceeds with fresh snapshots and the new information is learned for next time. Outdated memories automatically decay.

### Memory CLI (for inspection/debugging)

```bash
# See what the agent has learned
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py stats
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py domains
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py domain-info example.com

# Search memories by meaning
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py recall "how to log in"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py recall "user settings page" --domain example.com

# Manually teach the agent
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py save procedural example.com "Always wait for networkidle after clicking the Save button"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py save semantic example.com "Login page uses email + password, OTP is required for admin accounts"

# Maintenance
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py maintain    # Decay stale + cleanup
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/browser_memory.py decay 14    # Decay memories older than 14 days
```

### Prerequisites

The memory system requires ChromaDB:

```bash
pip install chromadb
```

Without ChromaDB, the plugin still works using the SQLite checkpoint system only. ChromaDB adds semantic search (finding relevant memories by meaning, not just exact domain match).

Memory is stored at `~/.ai-browser-workflow/` (configurable via `BROWSER_MEMORY_DIR` env var):
- `chroma_db/` — ChromaDB vector database for semantic memory
- `checkpoints.db` — SQLite database for structured checkpoints

## Commands

### Navigation
```bash
agent-browser open <url>      # Navigate to URL
agent-browser back            # Go back
agent-browser forward         # Go forward  
agent-browser reload          # Reload page
agent-browser close           # Close browser
```

### Snapshot (page analysis)
```bash
agent-browser snapshot        # Full accessibility tree
agent-browser snapshot -i     # Interactive elements only (recommended)
agent-browser snapshot -c     # Compact output
agent-browser snapshot -d 3   # Limit depth to 3
```

### Interactions (use @refs from snapshot)
```bash
agent-browser click @e1           # Click
agent-browser dblclick @e1        # Double-click
agent-browser fill @e2 "text"     # Clear and type
agent-browser type @e2 "text"     # Type without clearing
agent-browser press Enter         # Press key
agent-browser press Control+a     # Key combination
agent-browser hover @e1           # Hover
agent-browser check @e1           # Check checkbox
agent-browser uncheck @e1         # Uncheck checkbox
agent-browser select @e1 "value"  # Select dropdown
agent-browser scroll down 500     # Scroll page
agent-browser scrollintoview @e1  # Scroll element into view
```

### Get information
```bash
agent-browser get text @e1        # Get element text
agent-browser get value @e1       # Get input value
agent-browser get title           # Get page title
agent-browser get url             # Get current URL
```

### Screenshots
```bash
agent-browser screenshot          # Screenshot to stdout
agent-browser screenshot path.png # Save to file
agent-browser screenshot --full   # Full page
```

### Wait
```bash
agent-browser wait @e1                     # Wait for element
agent-browser wait 2000                    # Wait milliseconds
agent-browser wait --text "Success"        # Wait for text
agent-browser wait --load networkidle      # Wait for network idle
```

### Semantic locators (alternative to refs)
```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
```

## Example: Form submission

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# Output shows: textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check result
```

## Example: Authentication with saved state

```bash
# Login once
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "username"
agent-browser fill @e2 "password"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

# Later sessions: load saved state
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

## Sessions (parallel browsers)

```bash
agent-browser --session test1 open site-a.com
agent-browser --session test2 open site-b.com
agent-browser session list
```

## JSON output (for parsing)

Add `--json` for machine-readable output:
```bash
agent-browser snapshot -i --json
agent-browser get text @e1 --json
```

## Debugging

```bash
agent-browser open example.com --headed  # Show browser window
agent-browser console                    # View console messages
agent-browser errors                     # View page errors
```
