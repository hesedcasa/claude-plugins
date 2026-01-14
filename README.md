# Hesed Claude Plugins

Version: 1.4.0 <!-- x-release-please-version -->

A collection of custom plugins (skills) for [Claude Code](https://claude.com/claude-code) that extend Claude's capabilities with external integrations.

## Available Plugins

### context7

Search and retrieve up-to-date documentation from Context7.

### google-chat

Send messages to Google Chat spaces and reply to threads.

### jira

Query, create, update, and manage Jira issues using JQL.

### confluence

Interact with Confluence pages, spaces, and comments.

### sql

Execute SQL queries on MySQL and PostgreSQL databases with built-in safety features.

### sentry

Query, analyze, and manage Sentry issues, events, and projects.

## Installation

To use these plugins with Claude Code:

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd claude-plugins
   ```

2. Install the plugin marketplace in your Claude Code settings by adding the marketplace path to your configuration.

3. Configure individual plugins as needed (see plugin-specific configuration files).

## Plugin Structure

Each plugin follows the Claude Code plugin structure:

- `.claude-plugin/plugin.json` - Plugin metadata
- `skills/` - Skill implementations with prompts and scripts

## Author

Hesed

## License

Apache-2.0
