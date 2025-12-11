# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of custom Claude Code plugins (skills) that extend Claude's capabilities with external integrations. It contains 4 plugins:

- **context7** - Search and retrieve documentation from Context7
- **google-chat** - Send messages to Google Chat spaces
- **jira** - Query, create, update, and manage Jira issues
- **sql** - Execute SQL queries on MySQL and PostgreSQL databases

## Repository Structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Plugin marketplace configuration
├── plugins/
│   ├── context7/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/context7/
│   │       ├── SKILL.md
│   ├── google-chat/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/google-chat/
│   │       ├── SKILL.md
│   │       ├── config.jsonc      # API keys and tokens (gitignored)
│   │       └── scripts/
│   │           ├── new_message.py
│   │           ├── reply_message.py
│   │           └── jsonc.py
│   ├── jira/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/jira/
│   │       ├── SKILL.md
│   │       └── scripts/
│   │           └── get-ticket-summary.sh
│   └── sql/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/sql/
│           └── SKILL.md
├── .claude/                       # Local configuration (gitignored)
│   ├── sql-config.local.md       # Database credentials
│   └── atlassian-config.local.md # Jira credentials
├── .github/workflows/
│   ├── release-please.yml         # Automated releases
│   └── convetional-commit.yml    # PR validation
├── release-please-config.json     # Release configuration
└── CHANGELOG.md                   # Auto-generated changelog
```

## Plugin Architecture

Each plugin follows the Claude Code plugin structure:

- **`.claude-plugin/plugin.json`** - Plugin metadata (name, description, author)
- **`skills/<name>/SKILL.md`** - Detailed documentation with:
  - When to use the skill
  - Prerequisites and setup instructions
  - Available commands and usage patterns
  - Configuration examples
- **`skills/<name>/scripts/`** - Implementation scripts (Python/bash)
- **Configuration files** - `.local.md` or `config.jsonc` files for credentials (gitignored)

## Development Workflow

### Required Global Tools

Install these npm packages globally:

```bash
npm install -g jira-api-cli
npm install -g mysqldb-cli
npm install -g context7-cli
```

### Configuration Setup

Each plugin requires local configuration files that are gitignored:

**For Jira plugin:**
- Create `.claude/atlassian-config.local.md` with Atlassian credentials
- See `plugins/jira/skills/jira/SKILL.md` for setup instructions

**For SQL plugin:**
- Create `.claude/sql-config.local.md` with database connection details
- See `plugins/sql/skills/sql/SKILL.md` for setup instructions

**For Google Chat plugin:**
- Create `plugins/google-chat/skills/google-chat/config.jsonc` with API keys
- See `plugins/google-chat/skills/google-chat/SKILL.md` for setup instructions

**For Context7 plugin:**
- No local config required
- See `plugins/context7/skills/context7/SKILL.md` for setup instructions

### Testing Plugins

**Google Chat:**
```bash
python scripts/send_message.py --space-id "space_id" --message "Test message"
python scripts/reply_message.py --thread-name "space/..." --message "Test reply"
```

**Jira:**
```bash
npx jira-api-cli test-connection
```

**SQL:**
```bash
npx mysqldb-cli query '{"query":"SELECT 1"}'
```

**Context7:**
```bash
npx context7-cli resolve-library-id '{"libraryName":"react"}'
```

## Release Management

This repository uses **release-please** for automated versioning and releases:

### Commit Message Format

Follow **Conventional Commits** specification:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

Example:
```bash
git commit -m "feat: add new Context7 documentation search feature"
```

### Release Process

1. All changes merged to `main` branch
2. GitHub Action runs release-please automatically
3. Updates `CHANGELOG.md` and creates GitHub release
4. Bumps version based on commit messages
5. Updates version in:
   - `version.txt`
   - `.claude-plugin/marketplace.json`

See `release-please-config.json` for release configuration.

## Important Files

- **`README.md`** - Project overview and installation instructions
- **`CHANGELOG.md`** - Auto-generated release notes
- **`.gitignore`** - Excludes `*.local.md`, `config.jsonc`, and other sensitive files
- **`release-please-config.json`** - Release automation configuration
- **Individual SKILL.md files** - Detailed plugin documentation

## Key Configuration Files (Gitignored)

- **`.claude/*.local.md`** - All local credential files
- **`config.jsonc`** - Google Chat API configuration
- **`node_modules/`** - npm dependencies
- **`.env*`** - Environment variables

## Plugin-Specific Notes

### Google Chat Plugin
- Python scripts require `requests` library: `pip install requests`
- Uses `config.jsonc` for API keys and space tokens
- Supports formatted messages (markdown-like syntax)
- Scripts located in `skills/google-chat/scripts/`

### Jira Plugin
- Uses `jira-api-cli` npm package
- Responses are large (50KB+), always save to temp files first
- Helper script: `get-ticket-summary.sh` for quick summaries
- Requires Atlassian API token

### SQL Plugin
- Uses `mysqldb-cli` npm package
- Supports both MySQL and PostgreSQL
- Built-in safety features (row limits, destructive operation warnings)
- Multiple output formats: table, json, csv, toon

### Context7 Plugin
- Uses `context7-cli` npm package
- Fetches live documentation from Context7 server
- No local configuration required
- Supports pagination and topic-specific searches

## Security Best Practices

1. **Never commit credential files** - All `*.local.md` and `config.jsonc` are gitignored
2. **Use API tokens, not passwords** - Especially for Jira
3. **Enable SSL for remote databases** - Set `ssl: true` in SQL config
4. **Use read-only users when possible** - For production database access
5. **Review `.gitignore`** before committing - Ensure sensitive files are excluded

## Common Tasks

### Adding a New Plugin

1. Create plugin directory structure:
   ```
   plugins/<name>/
     .claude-plugin/plugin.json
     skills/<name>/
       SKILL.md
       scripts/
   ```

2. Add plugin to `.claude-plugin/marketplace.json`

3. Document setup and usage in SKILL.md

4. Test the plugin thoroughly

5. Update README.md with new plugin

### Modifying Existing Plugins

- Edit scripts in `skills/<plugin>/scripts/`
- Update SKILL.md for documentation changes
- Test changes before committing
- Follow conventional commit format

### Version Bumping

Just merge changes to `main` with proper commit messages - release-please handles the rest!
