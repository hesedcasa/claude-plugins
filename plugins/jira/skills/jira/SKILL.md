---
name: Jira
description: This skill should be used when interacting with Jira. Use when the user says phrases like "get Jira ticket", "list Jira issues", "create Jira issue", "search Jira", "show me ticket", or needs to query, create, update, or delete Jira issues. Supports JQL queries, project management, and user lookup.
---

# Jira

Interact with Jira directly from Claude Code using the jira-api-cli tool. Query issues, create tickets, update existing work items, and manage projects without leaving your development environment.

## When to Use This Skill

Invoke when:

- User asks to "get Jira ticket PROJ-123"
- User wants to "list Jira issues" or "search Jira for bugs"
- User needs to "create a Jira ticket"
- User asks to "update Jira issue" or "delete Jira ticket"
- User wants to see project details or boards
- User mentions a Jira ticket ID (e.g., "PROJ-123", "HESED-456")
- User needs to query Jira using JQL (Jira Query Language)

## Prerequisites

### 1. Install jira-api-cli

```bash
npm install -g jira-api-cli
```

Verify installation:

```bash
npx jira-api-cli test-connection
```

### 2. Create API Token

1. Visit [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Label it (e.g., "Claude Code Jira CLI")
4. Copy the generated token

### 3. Configure Connection

Create `.claude/atlassian-config.local.md` with your Jira credentials:

````yaml
---
profiles:
  cloud:
    host: https://your-domain.atlassian.net
    email: your-email@example.com
    apiToken: YOUR_API_TOKEN_HERE

defaultProfile: cloud
defaultFormat: json
---

# Jira Configuration

This file stores your Atlassian API credentials for both Jira and Confluence.

**Security Note:** This file should be listed in `.gitignore` and never committed to version control.

## Multiple Profiles

You can configure multiple Jira instances:

```yaml
profiles:
  cloud:
    host: https://company.atlassian.net
    email: work@company.com
    apiToken: token1

  personal:
    host: https://personal.atlassian.net
    email: personal@email.com
    apiToken: token2
```

Switch profiles using: `npx jira-api-cli` then type `profile personal`
````

**IMPORTANT:** Add `*.local.md` to `.gitignore` to prevent credential leakage.

## Best Practices

### Handling Large Responses

**CRITICAL:** Jira API responses are often very large (50-100KB+) due to numerous custom fields, worklogs, comments, and metadata. To avoid consuming excessive context:

1. **Always save responses to temporary files first**

```bash
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}' > /tmp/jira-PROJ-123.json
```

2. **Extract only relevant fields using jq or grep**

```bash
cat /tmp/jira-PROJ-123.json | jq '{key, summary: .fields.summary, status: .fields.status.name}'
```

3. **Clean up temp files when done**

```bash
rm /tmp/jira-PROJ-123.json
```

**Why This Matters:**

- A single ticket response can be 50,000+ characters
- Most of that data is irrelevant (custom fields, metadata)
- Using temp files + jq filtering reduces context usage by 90%+
- Enables faster analysis and better performance

See **Pattern 1a: Handling Large Ticket Responses** in the Usage Patterns section for detailed examples.

### Helper Script: get-ticket-summary.sh

For convenience, use the bundled helper script to automatically fetch and extract ticket summaries:

```bash
# Basic summary (no description/comments)
scripts/get-ticket-summary.sh PROJ-123

# Full details (includes description, comments, worklogs)
scripts/get-ticket-summary.sh PROJ-123 --full
```

**What it does:**

1. Fetches ticket from Jira API
2. Saves to `/tmp/jira-TICKET-ID.json`
3. Extracts and formats key fields using jq
4. Displays clean summary
5. Cleans up temp file automatically

**Requirements:**

- `jq` must be installed: `brew install jq` (macOS) or `apt-get install jq` (Linux)

## Available Commands

### Connection Testing

**Test Connection:**

```bash
npx jira-api-cli test-connection
```

**Expected Output:**

```json
{
  "status": "success",
  "message": "Connection successful",
  "user": {
    "displayName": "John Doe",
    "emailAddress": "john@example.com"
  }
}
```

### Project Operations

**List All Projects:**

```bash
npx jira-api-cli list-projects
```

**Get Specific Project:**

```bash
npx jira-api-cli get-project '{"projectIdOrKey":"PROJ"}'
```

**Expected Output:**

```json
{
  "id": "10000",
  "key": "PROJ",
  "name": "Project Name",
  "projectTypeKey": "software",
  "lead": {
    "displayName": "Project Lead"
  }
}
```

### Issue Management

**Get Issue Details:**

```bash
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}'
```

**Expected Output:**

```json
{
  "key": "PROJ-123",
  "fields": {
    "summary": "Issue title",
    "description": "Issue description",
    "status": {
      "name": "In Progress"
    },
    "assignee": {
      "displayName": "John Doe"
    },
    "priority": {
      "name": "High"
    },
    "created": "2025-01-15T10:30:00.000Z",
    "updated": "2025-01-20T14:45:00.000Z"
  }
}
```

**List Issues with JQL:**

```bash
npx jira-api-cli list-issues '{"jql":"project=PROJ AND status=\"In Progress\""}'
```

**Common JQL Queries:**

- All open issues: `project=PROJ AND status!=Done`
- My issues: `assignee=currentUser() AND status!=Done`
- Recent bugs: `project=PROJ AND issuetype=Bug AND created>=-7d`
- High priority: `project=PROJ AND priority=High`
- Sprint issues: `project=PROJ AND sprint in openSprints()`

**Create Issue:**

```bash
npx jira-api-cli create-issue '{
  "fields": {
    "project": {"key": "PROJ"},
    "summary": "Issue title",
    "description": "# Updated the issue'\''s description\n## TODO:\n- Task 1\n- Task 2",
    "issuetype": {"name": "Task"},
    "priority": {"name": "Medium"}
  }
  "markdown":true
}'
```

**Update Issue:**

```bash
npx jira-api-cli update-issue '{
  "issueIdOrKey": "PROJ-123",
  "fields": {
    "summary": "Updated title",
    "description": "# Updated the issue'\''s description\n## TODO:\n- Task 1\n- Task 2"
  },
  "markdown":true
}'
```

**Add Comment:**

```bash
npx jira-api-cli add-comment '{
  "issueIdOrKey": "PROJ-123",
  "body": "# Test\n## This is one of the issue'\''s comment",
  "markdown":true
}'
```

### Attachment Operations

**Download Attachment:**

```bash
npx jira-api-cli download-attachment '{"issueIdOrKey":"PROJ-123","attachmentId":"12345"}'
```

**Download to Custom Location:**

```bash
npx jira-api-cli download-attachment '{"issueIdOrKey":"PROJ-123","attachmentId":"12345","outputPath":"./downloads/screenshot.png"}'
```

**Expected Output:**

```json
{
  "status": "success",
  "message": "Attachment downloaded successfully",
  "filename": "screenshot.png",
  "path": "./downloads/screenshot.png"
}
```

### User Operations

**Get User Info:**

```bash
npx jira-api-cli get-user '{"accountId":"557058:f5b...abc"}'
```

Or search by email:

```bash
npx jira-api-cli get-user '{"query":"john@example.com"}'
```

### Board Operations (Experimental)

**List Boards:**

```bash
npx jira-api-cli list-boards
```

## Usage Patterns

### Pattern 1: Fetch Ticket Details

**User Request:** "Get details for PROJ-123"

**Execution:**

```bash
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}'
```

**Response Format:**

```markdown
# PROJ-123: Issue Title

**Status:** In Progress
**Assignee:** John Doe
**Priority:** High
**Created:** 2025-01-15
**Updated:** 2025-01-20

## Description

[Issue description here]

## Comments

- User A (2025-01-16): First comment
- User B (2025-01-18): Second comment
```

### Pattern 1a: Handling Large Ticket Responses (RECOMMENDED)

**When to Use:** Jira responses often contain extensive data (100+ custom fields, worklogs, comments, etc.) that can consume large amounts of context. For any ticket query, save the raw response to a temporary file first, then extract only the relevant information.

**User Request:** "Get details for PROJ-123"

**Step 1: Fetch and Save to Temp File**

```bash
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}' > /tmp/jira-PROJ-123.json
```

**Step 2: Extract Key Information Using jq or grep**

Extract only essential fields:

```bash
# Extract core fields using jq
cat /tmp/jira-PROJ-123.json | jq '{
  key: .key,
  summary: .fields.summary,
  status: .fields.status.name,
  assignee: .fields.assignee.displayName,
  reporter: .fields.reporter.displayName,
  priority: .fields.priority.name,
  created: .fields.created,
  updated: .fields.updated,
  description: .fields.description,
  parent: .fields.parent.key,
  labels: .fields.labels,
  timetracking: {
    originalEstimate: .fields.timeoriginalestimate,
    timeSpent: .fields.timespent,
    remaining: .fields.timeremaining
  },
  issuelinks: [.fields.issuelinks[] | {
    type: .type.name,
    key: (.inwardIssue.key // .outwardIssue.key),
    summary: (.inwardIssue.fields.summary // .outwardIssue.fields.summary)
  }]
}'
```

**Step 3: Read and Process Description/Comments**

For description content:

```bash
# Extract description text
cat /tmp/jira-PROJ-123.json | jq -r '.fields.description.content[].content[]?.text' 2>/dev/null | grep -v "^$"
```

For comments:

```bash
# Extract recent comments
cat /tmp/jira-PROJ-123.json | jq -r '.fields.comment.comments[-5:] | .[] | "[\(.author.displayName)] \(.created): \(.body.content[].content[]?.text)"' 2>/dev/null
```

For worklogs:

```bash
# Extract work log entries
cat /tmp/jira-PROJ-123.json | jq '.fields.worklog.worklogs[] | {
  author: .author.displayName,
  started: .started,
  timeSpent: .timeSpent,
  comment: .comment.content[]?.content[]?.text
}'
```

**Step 4: Clean Up Temp File**

```bash
rm /tmp/jira-PROJ-123.json
```

**Alternative: Using grep for Quick Searches**

```bash
# Save response
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}' > /tmp/jira-temp.json

# Search for specific custom fields
grep -o '"customfield_[0-9]*":[^,}]*' /tmp/jira-temp.json | head -20

# Find specific text in description
cat /tmp/jira-temp.json | jq -r '.fields.description.content[].content[]?.text' | grep -i "database"

# Clean up
rm /tmp/jira-temp.json
```

**Benefits:**

- **Context Efficiency:** Only load essential data into context instead of 50KB+ JSON
- **Faster Processing:** Use system tools (jq, grep) for filtering
- **Better Analysis:** Focus on relevant fields without noise from custom fields
- **Reusable:** Keep temp file if you need to extract different fields later

**Response Format (Summarized):**

```markdown
# PROJ-123: Add login function with email OTP

**Type:** Task
**Status:** In Progress
**Parent:** PROJ-100 - Revamp user authentication module
**Priority:** P2 - Medium
**Assignee:** John Doe
**Labels:** no-qa

## Time Tracking

- Original Estimate: 22h
- Time Spent: 18h (81% complete)
- Remaining: 4h

## Key TODO Items:

1. Create new login module for email OTP
2. Remove deprecated password login
3. Setup 3rd party email OTP service
4. Add/update test cases

## Related Issues

- PROJ-456: Deprecate login with password

[View in Jira](https://company.atlassian.net/browse/PROJ-123)
```

### Pattern 2: Search Issues

**User Request:** "Show me all open bugs in HESED project"

**Execution:**

```bash
npx jira-api-cli list-issues '{
  "jql": "project=HESED AND issuetype=Bug AND status!=Done"
}'
```

**Response Format:**

```markdown
# Open Bugs in HESED (5 issues)

1. **HESED-101** - Login fails on Safari
   - Status: In Progress
   - Assignee: Alice
   - Priority: High

2. **HESED-102** - Profile image upload broken
   - Status: To Do
   - Assignee: Bob
   - Priority: Medium

[...more issues]
```

### Pattern 3: Create Issue

**User Request:** "Create a bug ticket for the login issue"

**Execution:**

```bash
npx jira-api-cli create-issue '{
  "fields": {
    "project": {"key": "HESED"},
    "summary": "Login fails on Safari browser",
    "description": "Users report unable to login using Safari. Error: Invalid credentials.",
    "issuetype": {"name": "Bug"},
    "priority": {"name": "High"}
  }
}'
```

**Response Format:**

```markdown
✓ Created issue: HESED-456

**Title:** Login fails on Safari browser
**Type:** Bug
**Priority:** High
**Link:** https://company.atlassian.net/browse/HESED-456
```

### Pattern 4: Update Issue

**User Request:** "Update PROJ-123 to mark it as done"

**Execution:**

```bash
npx jira-api-cli update-issue '{
  "issueIdOrKey": "PROJ-123",
  "fields": {
    "status": {"name": "Done"}
  }
}'
```

### Pattern 5: Download and Analyze Attachments

**When to Use:** When a Jira ticket contains attachments (screenshots, logs, documents) that need to be analyzed to understand the issue better. This is especially useful for bug reports with error screenshots or log files.

**User Request:** "Get details for PROJ-123 and analyze the attachments"

**Step 1: Fetch Issue and Extract Attachment Info**

```bash
# Save issue to temp file
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}' > /tmp/jira-PROJ-123.json

# Extract attachment information
cat /tmp/jira-PROJ-123.json | jq '.fields.attachment[] | {
  id: .id,
  filename: .filename,
  mimeType: .mimeType,
  size: .size,
  created: .created,
  author: .author.displayName,
  content: .content,
  thumbnail: .thumbnail
}'
```

**Example Output:**

```json
{
  "id": "235270",
  "filename": "error-screenshot.png",
  "mimeType": "image/png",
  "size": 357567,
  "created": "2025-12-02T18:19:50.629-0800",
  "author": "John Doe",
  "content": "https://company.atlassian.net/rest/api/3/attachment/content/235270",
  "thumbnail": "https://company.atlassian.net/rest/api/3/attachment/thumbnail/235270"
}
{
  "id": "235271",
  "filename": "application.log",
  "mimeType": "text/plain",
  "size": 52841,
  "created": "2025-12-02T18:19:51.048-0800",
  "author": "John Doe",
  "content": "https://company.atlassian.net/rest/api/3/attachment/content/235271",
  "thumbnail": null
}
```

**Step 2: Download Attachments for Analysis**

**Note:** Attachments can be referenced in issue descriptions, comments (in `mediaSingle` blocks), or directly attached to the issue. All attachments appear in the `fields.attachment[]` array regardless of where they're referenced.

```bash
# Download screenshot to temp directory
npx jira-api-cli download-attachment '{"issueIdOrKey":"PROJ-123","attachmentId":"235270","outputPath":"/tmp/jira-attachments/error-screenshot.png"}'

# Download log file
npx jira-api-cli download-attachment '{"issueIdOrKey":"PROJ-123","attachmentId":"235271","outputPath":"/tmp/jira-attachments/application.log"}'
```

**Step 3: Analyze Attachments**

For images (screenshots, diagrams):

```bash
# Use Claude's vision capability to analyze the image
# Simply read the downloaded image file - Claude can analyze it directly
```

For log files:

```bash
# Search for errors in log files
grep -i "error\|exception\|failed" /tmp/jira-attachments/application.log

# Or read the entire log if it's small
cat /tmp/jira-attachments/application.log
```

For text/code files:

```bash
# Read and analyze the content directly
cat /tmp/jira-attachments/config.json | jq '.'
```

**Step 4: Clean Up**

```bash
rm -rf /tmp/jira-attachments/
rm /tmp/jira-PROJ-123.json
```

**Response Format (with Attachment Analysis):**

```markdown
# PROJ-123: Login Button Not Working

**Status:** Open
**Assignee:** Jane Smith
**Priority:** High

## Description

Users report that the login button is unresponsive on the homepage.

## Attachments Analysis

### 1. error-screenshot.png

- **Type:** Screenshot
- **Analysis:** The screenshot shows a JavaScript console error: "Uncaught TypeError: Cannot read property 'submit' of null". The login form element appears to be missing from the DOM when the button click handler executes.

### 2. application.log

- **Type:** Log file
- **Key Findings:**
  - Line 142: `ERROR [2025-01-15 10:28:45] FormHandler - Form element #loginForm not found`
  - Line 145: `WARN [2025-01-15 10:28:45] DOMLoader - Script executed before DOM ready`
- **Root Cause:** The login script is executing before the DOM is fully loaded.

## Recommended Fix

Move the script tag to the end of the body or wrap initialization in a DOMContentLoaded event listener.
```

**Supported Attachment Types:**

| Type                   | Analysis Method                  |
| ---------------------- | -------------------------------- |
| Images (png, jpg, gif) | Claude vision analysis           |
| Log files (log, txt)   | Text search and pattern matching |
| JSON/XML files         | Parse and inspect structure      |
| PDF documents          | Extract and analyze text content |
| Code files             | Syntax analysis and review       |

## Output Formats

The CLI supports two output formats:

### JSON (Default)

Machine-readable format for parsing and processing.

### TOON (Token-Oriented Object Notation)

AI-friendly format optimized for Claude to read and understand.

**Switch Format:**

```bash
npx jira-api-cli
jira> format toon
```

## Interactive Mode

For exploratory work, use interactive mode:

```bash
npx jira-api-cli
```

**Available REPL Commands:**

- `commands` - List all commands
- `profile <name>` - Switch profiles
- `format <type>` - Change output format (json/toon)
- `test-connection` - Verify connectivity
- `exit` or `quit` - Close CLI

## Common Issue Types

When creating issues, use these common issue types:

- **Bug** - Something is broken
- **Task** - Work item to complete
- **Story** - User story with acceptance criteria
- **Epic** - Large body of work
- **Sub-task** - Child of another issue
- **Spike** - Research or investigation task

## Error Handling

**Connection Failures:**

```json
{
  "error": "Connection failed",
  "message": "Invalid API token or host"
}
```

**Action:** Verify credentials in `.claude/atlassian-config.local.md`

**Issue Not Found:**

```json
{
  "error": "Issue does not exist",
  "issueKey": "PROJ-999"
}
```

**Action:** Check ticket ID and project key

**Permission Denied:**

```json
{
  "error": "Forbidden",
  "message": "User lacks permission to perform this action"
}
```

**Action:** Request appropriate Jira permissions from admin

## Security Best Practices

1. **Never commit `.local.md` files**
   - Add `*.local.md` to `.gitignore`
   - Store credentials securely

2. **Use API tokens, not passwords**
   - Generate tokens from Atlassian account settings
   - Rotate tokens periodically

3. **Limit token permissions**
   - Grant only necessary Jira permissions
   - Use separate tokens for different projects

4. **Audit token usage**
   - Review Atlassian security logs
   - Revoke unused tokens

## Troubleshooting

### CLI Not Found

```bash
npm install -g jira-api-cli
```

### Connection Timeout

Check network connection and Jira instance status:

```bash
curl -I https://your-domain.atlassian.net
```

### Invalid JQL Syntax

Use Jira's JQL autocomplete in the web UI to validate queries before using in CLI.

### Rate Limiting

Atlassian Cloud has rate limits:

- **20 requests per second** for Cloud instances
- **No limit** for Data Center

If rate-limited, retry after delay:

```bash
sleep 5 && npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}'
```

## Advanced Usage

### Bulk Operations

**List multiple issues:**

```bash
npx jira-api-cli list-issues '{
  "jql": "key in (PROJ-1, PROJ-2, PROJ-3)"
}'
```

### Custom Fields

**Include custom fields in issue creation:**

```bash
npx jira-api-cli create-issue '{
  "fields": {
    "project": {"key": "PROJ"},
    "summary": "Title",
    "issuetype": {"name": "Task"},
    "customfield_10001": "Custom value"
  }
}'
```

To find custom field IDs, fetch an existing issue and inspect the JSON output.

### Transitions

**Move issue through workflow:**

```bash
# Get available transitions
npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123","expand":"transitions"}'

# Apply transition
npx jira-api-cli update-issue '{
  "issueIdOrKey": "PROJ-123",
  "transition": {"id": "31"}
}'
```

## Quick Reference

| Task                | Command                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------- |
| Test connection     | `npx jira-api-cli test-connection`                                                          |
| Get issue           | `npx jira-api-cli get-issue '{"issueIdOrKey":"PROJ-123"}'`                                  |
| Search issues       | `npx jira-api-cli list-issues '{"jql":"project=PROJ"}'`                                     |
| Create issue        | `npx jira-api-cli create-issue '{...}'`                                                     |
| Update issue        | `npx jira-api-cli update-issue '{...}'`                                                     |
| Download attachment | `npx jira-api-cli download-attachment '{"issueIdOrKey":"PROJ-123","attachmentId":"12345"}'` |
| List projects       | `npx jira-api-cli list-projects`                                                            |
| Get user            | `npx jira-api-cli get-user '{"query":"email@example.com"}'`                                 |

## Notes

- **Always test connection** before running commands
- **Use JQL** for advanced issue searching
- **TOON format** is optimized for AI consumption
- **Interactive mode** is great for exploration
- **Headless mode** is ideal for automation and scripting
- **Keep credentials secure** using `.local.md` pattern
