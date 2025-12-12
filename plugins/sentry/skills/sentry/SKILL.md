---
name: Sentry
description: This skill should be used when interacting with Sentry. Use when the user says phrases like "get Sentry issue", "list Sentry issues", "analyze Sentry events", "check Sentry project", "debug Sentry errors", or needs to query Sentry issues, events, projects, or manage error tracking workflows.
---

# Sentry

Interact with Sentry directly from Claude Code using the sentry-api-cli tool. Query issues, analyze events, manage projects, and debug errors without leaving your development environment.

## When to Use This Skill

Invoke when:

- User asks to "get Sentry issue" or "show me issue details"
- User wants to "list Sentry issues" or "search for errors"
- User needs to "analyze Sentry events" or "check project events"
- User asks to "check Sentry project" or "list projects"
- User wants to "debug errors" or "find error trends"
- User mentions error tracking, exception monitoring, or performance issues
- User needs to query Sentry for specific error patterns or tags

## Prerequisites

### 1. Install sentry-api-cli

```bash
npm install -g sentry-api-cli
```

Verify installation:

```bash
npx sentry-api-cli test-connection
```

### 2. Create Auth Token

1. Navigate to **Sentry > Settings > Developer Settings**
2. Click "Create New Token"
3. Grant the following scopes:
   - `event:read` - Read event data
   - `issue:read` - Read issue data
   - `project:read` - Read project data
   - `org:read` - Read organization data
4. Copy the generated token

### 3. Configure Connection

Create `.claude/sentry-config.local.md` with your Sentry credentials:

````yaml
---
profiles:
  production:
    authToken: YOUR_AUTH_TOKEN_HERE
    orgSlug: your-org-slug
    defaultProject: your-default-project

  staging:
    authToken: STAGING_AUTH_TOKEN
    orgSlug: your-org-slug
    defaultProject: your-staging-project

defaultProfile: production
defaultFormat: json
---

# Sentry Configuration

This file stores your Sentry API credentials for accessing issues, events, and projects.

**Security Note:** This file should be listed in `.gitignore` and never committed to version control.

## Multiple Profiles

You can configure multiple Sentry organizations or environments:

```yaml
profiles:
  production:
    authToken: prod_token_here
    orgSlug: company-prod
    defaultProject: web-app

  staging:
    authToken: staging_token_here
    orgSlug: company-staging
    defaultProject: web-app-staging

  personal:
    authToken: personal_token_here
    orgSlug: my-personal-org
    defaultProject: my-project
```

Switch profiles using: `npx sentry-api-cli` then type `profile staging`
````

**IMPORTANT:** Add `*.local.md` to `.gitignore` to prevent credential leakage.

## Best Practices

### Handling Large Responses

Sentry API responses can be large, especially when retrieving event data with stack traces. To optimize:

1. **Always save responses to temporary files first**

```bash
npx sentry-api-cli get-issue '{"issueId":"123456"}' > /tmp/sentry-issue-123456.json
```

2. **Extract only relevant fields using jq**

```bash
cat /tmp/sentry-issue-123456.json | jq '{id: .id, title: .title, count: .count, userCount: .userCount, lastSeen: .lastSeen}'
```

3. **Clean up temp files when done**

```bash
rm /tmp/sentry-issue-123456.json
```

## Available Commands

### Connection Testing

**Test Connection:**

```bash
npx sentry-api-cli test-connection
```

**Expected Output:**

```json
{
  "status": "success",
  "message": "Connection successful",
  "organization": {
    "slug": "your-org-slug",
    "name": "Your Organization"
  }
}
```

### Project Operations

**List All Projects:**

```bash
npx sentry-api-cli list-projects
```

**Get Specific Project:**

```bash
npx sentry-api-cli get-project '{"orgSlug":"your-org","projectSlug":"your-project"}'
```

**Expected Output:**

```json
{
  "id": "12345",
  "slug": "your-project",
  "name": "Your Project",
  "organization": {
    "slug": "your-org",
    "name": "Your Organization"
  },
  "isPublic": false,
  "isBookmarked": false
}
```

### Issue Management

**Get Issue Details:**

```bash
npx sentry-api-cli get-issue '{"issueId":"123456789"}'
```

**Expected Output:**

```json
{
  "id": "123456789",
  "shortId": "APP-123",
  "title": "TypeError: Cannot read property 'x' of undefined",
  "culprit": "src/components/UserProfile.js in render",
  "level": "error",
  "count": 47,
  "userCount": 23,
  "firstSeen": "2025-01-15T10:30:00.000Z",
  "lastSeen": "2025-01-20T14:45:00.000Z",
  "permalink": "https://sentry.io/org/project/issues/123456789/",
  "stats": {
    "24h": [[timestamp, count], ...],
    "30d": [[timestamp, count], ...]
  }
}
```

**List Project Issues:**

```bash
npx sentry-api-cli list-project-issues '{"projectSlug":"your-project"}'
```

**Common Queries:**

- All unresolved issues: Query by status
- Recent errors: Filter by `firstSeen`
- High-volume issues: Filter by `count`
- User-affecting issues: Filter by `userCount`

**Update Issue:**

```bash
npx sentry-api-cli update-issue '{
  "issueId": "123456789",
  "status": "resolved",
  "assignedTo": "user@example.com"
}'
```

### Event Operations

**Get Event Details:**

```bash
npx sentry-api-cli get-event '{"eventId":"abc123def456"}'
```

**Expected Output:**

```json
{
  "eventID": "abc123def456",
  "message": "TypeError: Cannot read property 'x' of undefined",
  "level": "error",
  "timestamp": "2025-01-20T14:45:00.000Z",
  "user": {
    "id": "user123",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "exception": {
    "values": [
      {
        "type": "TypeError",
        "value": "Cannot read property 'x' of undefined",
        "stacktrace": {
          "frames": [...]
        }
      }
    ]
  },
  "extra": {...},
  "tags": {...}
}
```

**List Project Events:**

```bash
npx sentry-api-cli list-project-events '{"projectSlug":"your-project"}'
```

**Expected Output:**

```json
[
  {
    "eventID": "abc123",
    "message": "Error message",
    "timestamp": "2025-01-20T14:45:00.000Z",
    "level": "error"
  },
  ...
]
```

### Tag Operations

**Get Tag Details:**

```bash
npx sentry-api-cli get-tag-details '{"orgSlug":"your-org","projectSlug":"your-project","tagKey":"browser"}'
```

**Expected Output:**

```json
{
  "key": "browser",
  "name": "Browser",
  "uniqueValues": 15,
  "totalValues": 423
}
```

**Get Tag Values:**

```bash
npx sentry-api-cli get-tag-values '{"orgSlug":"your-org","projectSlug":"your-project","tagKey":"browser"}'
```

**Expected Output:**

```json
[
  {
    "name": "Chrome",
    "value": "Chrome 120.0",
    "count": 245
  },
  {
    "name": "Firefox",
    "value": "Firefox 121.0",
    "count": 132
  },
  ...
]
```

### Source Map Debugging

**Debug Source Maps:**

```bash
npx sentry-api-cli debug-source-maps '{"orgSlug":"your-org","projectSlug":"your-project"}'
```

**Expected Output:**

```json
{
  "sourceMaps": {
    "configured": true,
    "valid": true,
    "totalCount": 45,
    "unreferencedCount": 3
  },
  "artifacts": [...],
  "issues": [
    {
      "type": "unreferenced",
      "message": "Artifact not referenced by any event"
    }
  ]
}
```

## Usage Patterns

### Pattern 1: Fetch Issue Details

**User Request:** "Get details for Sentry issue APP-123"

**Execution:**

```bash
npx sentry-api-cli get-issue '{"issueId":"123456789"}'
```

**Response Format:**

```markdown
# APP-123: TypeError: Cannot read property 'x' of undefined

**Level:** Error
**Count:** 47 occurrences
**Users:** 23 affected
**First Seen:** 2025-01-15 10:30:00
**Last Seen:** 2025-01-20 14:45:00

**Culprit:** src/components/UserProfile.js in render

**URL:** https://sentry.io/org/project/issues/123456789/

## Recent Activity

- 47 errors in the last 24h
- 15 unique users affected
- Trending up since 2025-01-18
```

### Pattern 2: Analyze Error Events

**User Request:** "Show me recent errors from the web-app project"

**Execution:**

```bash
npx sentry-api-cli list-project-events '{"projectSlug":"web-app"}'
```

**Response Format:**

```markdown
# Recent Errors in web-app (5 events)

1. **TypeError** (2025-01-20 14:45:00)
   - Message: Cannot read property 'x' of undefined
   - User: john@example.com
   - Browser: Chrome 120.0

2. **ReferenceError** (2025-01-20 13:22:15)
   - Message: y is not defined
   - User: jane@example.com
   - Browser: Safari 17.1

[...more events]
```

### Pattern 3: Check Project Health

**User Request:** "Check the health of my production project"

**Execution:**

```bash
npx sentry-api-cli list-project-issues '{"projectSlug":"production-web"}'
```

**Response Format:**

```markdown
# Project Health: production-web

**Total Active Issues:** 12
**Critical Issues:** 3
**Total Events (24h):** 847
**Affected Users (24h):** 234

## Critical Issues

1. **APP-123** - TypeError: Cannot read property 'x'
   - Count: 47 (↑ 23%)
   - Status: Resolved

2. **APP-145** - Network request failed
   - Count: 34 (↑ 45%)
   - Status: Resolved in next release

## Recommendations

- Investigate APP-123 - appears to be trending up
- Consider rollback of recent deployment
- Monitor APP-145 - resolved but watch for reoccurrence
```

### Pattern 4: Debug Source Maps

**User Request:** "Debug source map issues for the frontend project"

**Execution:**

```bash
npx sentry-api-cli debug-source-maps '{"orgSlug":"my-org","projectSlug":"frontend"}'
```

**Response Format:**

```markdown
# Source Map Debug Report

**Status:** ✅ Configured and Valid
**Total Artifacts:** 45
**Unreferenced:** 3

## Issues Found

### 1. Unreferenced Artifact

- **File:** `/static/js/vendor.abc123.js.map`
- **Issue:** Artifact not referenced by any event
- **Action:** Remove artifact or verify upload

## Recommendations

- All source maps are properly configured
- No issues detected
```

### Pattern 5: Analyze Error by Tag

**User Request:** "Show me error breakdown by browser"

**Step 1: Get Tag Details**

```bash
npx sentry-api-cli get-tag-details '{"projectSlug":"web-app","tagKey":"browser"}'
```

**Step 2: Get Tag Values**

```bash
npx sentry-api-cli get-tag-values '{"projectSlug":"web-app","tagKey":"browser"}'
```

**Response Format:**

```markdown
# Browser Distribution

- **Chrome 120.0:** 245 errors (58%)
- **Firefox 121.0:** 132 errors (31%)
- **Safari 17.1:** 32 errors (8%)
- **Edge 120.0:** 14 errors (3%)

**Analysis:** Chrome is the primary source of errors. Consider testing on Chrome 120.0.
```

## Output Formats

The CLI supports two output formats:

### JSON (Default)

Machine-readable format for parsing and processing.

### TOON (Token-Oriented Object Notation)

AI-friendly format optimized for Claude to read and understand.

**Switch Format:**

```bash
npx sentry-api-cli
sentry> format toon
```

## Interactive Mode

For exploratory work, use interactive mode:

```bash
npx sentry-api-cli
```

**Available REPL Commands:**

- `commands` - List all commands
- `profile <name>` - Switch profiles
- `format <type>` - Change output format (json/toon)
- `test-connection` - Verify connectivity
- `exit` or `quit` - Close CLI

## Error Handling

**Connection Failures:**

```json
{
  "error": "Connection failed",
  "message": "Invalid auth token or organization"
}
```

**Action:** Verify credentials in `.claude/sentry-config.local.md`

**Issue Not Found:**

```json
{
  "error": "Issue does not exist",
  "issueId": "123456789"
}
```

**Action:** Check issue ID and verify access to the project

**Permission Denied:**

```json
{
  "error": "Forbidden",
  "message": "Token lacks required scope"
}
```

**Action:** Regenerate token with proper scopes (event:read, issue:read, project:read)

**Rate Limiting:**

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests"
}
```

**Action:** Add delays between requests or upgrade Sentry plan

## Security Best Practices

1. **Never commit `.local.md` files**
   - Add `*.local.md` to `.gitignore`
   - Store credentials securely

2. **Use scoped tokens**
   - Grant only necessary permissions
   - Separate tokens for different environments

3. **Rotate tokens regularly**
   - Update tokens periodically
   - Revoke unused tokens

4. **Audit token usage**
   - Review Sentry security logs
   - Monitor for suspicious activity

## Troubleshooting

### CLI Not Found

```bash
npm install -g sentry-api-cli
```

### Connection Timeout

Check network connection and Sentry instance status:

```bash
curl -I https://sentry.io/api/0/organizations/your-org/
```

### Invalid Token

Ensure token has correct scopes:

- `event:read` for event data
- `issue:read` for issue data
- `project:read` for project data
- `org:read` for organization data

### Project Not Found

Verify:

- Organization slug is correct
- Project slug is correct
- Token has access to the project

## Advanced Usage

### Bulk Operations

**List multiple projects:**

```bash
npx sentry-api-cli list-projects
```

### Filtering Issues

Use query parameters to filter:

```bash
# Get only unresolved issues
npx sentry-api-cli list-project-issues '{"projectSlug":"web-app","query":"is:unresolved"}'

# Get issues from last 7 days
npx sentry-api-cli list-project-issues '{"projectSlug":"web-app","query":"age:-7d"}'
```

### Event Analysis

**Get event stack trace:**

```bash
npx sentry-api-cli get-event '{"eventId":"abc123"}' > /tmp/event.json
cat /tmp/event.json | jq '.exception.values[0].stacktrace.frames'
```

## Quick Reference

| Task                | Command                                                                                |
| ------------------- | -------------------------------------------------------------------------------------- |
| Test connection     | `npx sentry-api-cli test-connection`                                                   |
| List projects       | `npx sentry-api-cli list-projects`                                                     |
| Get issue           | `npx sentry-api-cli get-issue '{"issueId":"123"}'`                                     |
| List project issues | `npx sentry-api-cli list-project-issues '{"projectSlug":"my-project"}'`                |
| Get event           | `npx sentry-api-cli get-event '{"eventId":"abc123"}'`                                  |
| List events         | `npx sentry-api-cli list-project-events '{"projectSlug":"my-project"}'`                |
| Get tag details     | `npx sentry-api-cli get-tag-details '{"projectSlug":"my-project","tagKey":"browser"}'` |
| Get tag values      | `npx sentry-api-cli get-tag-values '{"projectSlug":"my-project","tagKey":"browser"}'`  |
| Debug source maps   | `npx sentry-api-cli debug-source-maps '{"projectSlug":"my-project"}'`                  |

## Notes

- **Always test connection** before running commands
- **Use query filters** to narrow down results
- **TOON format** is optimized for AI consumption
- **Interactive mode** is great for exploration
- **Headless mode** is ideal for automation and scripting
- **Keep credentials secure** using `.local.md` pattern
- **Review token scopes** regularly for security
