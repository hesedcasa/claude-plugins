# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A collection of Claude Code plugins that extend Claude's capabilities. Currently contains 2 plugins:

- **agent-browser** - Automates browser interactions with agentic memory (learns navigation patterns across sessions)
- **terminal-recorder** - Records terminal sessions and converts them to animated GIF files

## Repository Structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Plugin marketplace config (version bumped by release-please)
├── plugins/
│   ├── agent-browser/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── hooks/hooks.json      # PreToolUse/PostToolUse/Stop hooks for memory system
│   │   ├── scripts/              # Memory system Python scripts
│   │   └── skills/agent-browser/SKILL.md
│   └── terminal-recorder/
│       ├── .claude-plugin/plugin.json
│       └── skills/terminal-recorder/
│           ├── SKILL.md
│           └── scripts/type-human.py
├── .claude-plugin/marketplace.json
├── .github/workflows/
│   ├── release-please.yml        # Automated releases
│   └── convetional-commit.yml    # PR title validation
├── install-lint-tools.sh         # Installs shellcheck, flake8, black
├── package.json                  # Dev toolchain (eslint, prettier, husky)
├── release-please-config.json
└── version.txt
```

## Plugin Architecture

Each plugin follows this structure:

- **`.claude-plugin/plugin.json`** - Plugin metadata (name, description, author)
- **`skills/<name>/SKILL.md`** - Skill documentation with frontmatter (trigger conditions, allowed tools)
- **`scripts/`** - Implementation scripts (Python/bash)
- **`hooks/hooks.json`** - Optional event hooks (PreToolUse, PostToolUse, Stop)

## Development Workflow

### Dev Setup

```bash
npm install                    # Install eslint, prettier, husky
bash install-lint-tools.sh    # Install shellcheck, flake8, black
```

### Lint & Format

```bash
npm run lint       # Run eslint + shellcheck + flake8
npm run format     # Run prettier + black
npm run build      # install-lint-tools + lint + format (full CI-equivalent check)
```

Husky runs pre-commit hooks automatically after `npm install`.

### Adding a New Plugin

1. Create the directory structure:
   ```
   plugins/<name>/
     .claude-plugin/plugin.json
     skills/<name>/SKILL.md
     scripts/        (if needed)
     hooks/hooks.json  (if needed)
   ```
2. Add entry to `.claude-plugin/marketplace.json` under `"plugins"`
3. Document setup and usage in SKILL.md
4. Run `npm run build` to verify linting passes

## Plugin-Specific Notes

### agent-browser Plugin

- Requires `agent-browser` CLI installed (`brew install agent-browser` or equivalent)
- **Memory system** uses two layers: ChromaDB (semantic/vector) + SQLite (structured checkpoints)
  - Memory stored at `~/.ai-browser-workflow/` (override with `BROWSER_MEMORY_DIR`)
  - ChromaDB is optional — without it, only SQLite checkpoints are used
  - Install ChromaDB: `pip install chromadb`
- **Hooks** in `hooks/hooks.json` fire automatically:
  - `PreToolUse` — injects relevant memories before `agent-browser open`
  - `PostToolUse` — updates memories after each `agent-browser` command
  - `Stop` — extracts session checkpoints and runs memory maintenance
- Memory CLI for inspection: `python3 scripts/browser_memory.py stats|domains|recall|save|maintain`

### terminal-recorder Plugin

- Requires `asciinema` and `agg`: `brew install asciinema && cargo install --git https://github.com/asciinema/agg`
- No API credentials or config files required
- Use `--idle-time-limit` with asciinema to trim pauses before GIF conversion
- Optional post-processing: `gifsicle` for GIF optimization

## Release Management

Uses **release-please** for automated versioning. All commits to `main` trigger it.

### Commit Format (Conventional Commits)

- `feat:` — new feature (bumps minor)
- `fix:` — bug fix (bumps patch)
- `docs:` — documentation only
- `refactor:` / `chore:` — maintenance

### What Gets Bumped on Release

- `version.txt`
- `package.json`
- `.claude-plugin/marketplace.json` (`$.version`)

## Security

- No credential files in this repo — both plugins require no API keys
- If adding a plugin that needs credentials, use `.claude/*.local.md` (gitignored pattern: `*.local.md`)
