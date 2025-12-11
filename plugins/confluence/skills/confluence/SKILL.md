---
name: Confluence
description: This skill should be used when interacting with Confluence. Use when the user says phrases like "get Confluence page", "list Confluence spaces", "create Confluence page", "search Confluence", "add comment to page", or needs to query, create, update, or delete Confluence pages and spaces.
---

# Confluence

Interact with Confluence directly from Claude Code using the conni-cli tool. Manage pages, spaces, and comments without leaving your development environment.

## When to Use This Skill

Invoke when:

- User asks to "get Confluence page" or "read Confluence documentation"
- User wants to "list Confluence spaces" or "search Confluence"
- User needs to "create a Confluence page" or "update page"
- User asks to "add comment to page" or "delete Confluence page"
- User wants to see space details or page hierarchy
- User mentions a Confluence space key (e.g., "DOCS", "TEAM")
- User needs to query Confluence using CQL (Confluence Query Language)

## Prerequisites

### 1. Install conni-cli

```bash
npm install -g conni-cli
```

Verify installation:

```bash
npx conni-cli test-connection
```

### 2. Create API Token

1. Visit [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Label it (e.g., "Claude Code Confluence CLI")
4. Copy the generated token

### 3. Configure Connection

Create `.claude/atlassian-config.local.md` with your Confluence credentials:

````yaml
---
profiles:
  cloud:
    host: https://your-domain.atlassian.net/wiki
    email: your-email@example.com
    apiToken: YOUR_API_TOKEN_HERE

defaultProfile: cloud
defaultFormat: json
---

# Atlassian Configuration

This file stores your Atlassian API credentials for both Jira and Confluence.

**Security Note:** This file should be listed in `.gitignore` and never committed to version control.

## Multiple Profiles

You can configure multiple Confluence instances:

```yaml
profiles:
  cloud:
    host: https://company.atlassian.net/wiki
    email: work@company.com
    apiToken: token1

  personal:
    host: https://personal.atlassian.net/wiki
    email: personal@email.com
    apiToken: token2
```

Switch profiles using: `npx conni-cli` then type `profile personal`
````

**IMPORTANT:** Add `*.local.md` to `.gitignore` to prevent credential leakage.

## Best Practices

### Handling Large Responses

**CRITICAL:** Confluence API responses can be very large (50-100KB+) due to extensive page content, HTML storage format, version history, comments, and metadata. To avoid consuming excessive context:

1. **Always save responses to temporary files first**

```bash
npx conni-cli get-page '{"pageId":"98765"}' > /tmp/confluence-page-98765.json
```

2. **Extract only relevant fields using jq or grep**

```bash
cat /tmp/confluence-page-98765.json | jq '{
  id: .id,
  title: .title,
  status: .status,
  spaceId: .spaceId,
  version: .version.number,
  lastModified: .version.when,
  author: .version.by.displayName
}'
```

3. **Extract page content separately if needed**

```bash
# Get just the HTML content
cat /tmp/confluence-page-98765.json | jq -r '.body.storage.value'

# Get plain text approximation (remove HTML tags)
cat /tmp/confluence-page-98765.json | jq -r '.body.storage.value' | sed 's/<[^>]*>//g'
```

4. **Clean up temp files when done**

```bash
rm /tmp/confluence-page-98765.json
```

**Why This Matters:**

- A single page response can be 50,000+ characters with full HTML content
- Page content includes all formatting, macros, and embedded media references
- Version history and metadata add significant overhead
- Most of that data is irrelevant for quick queries
- Using temp files + jq filtering reduces context usage by 90%+
- Enables faster analysis and better performance

**Pattern: Efficient Page Retrieval**

Instead of loading the entire response into context:

```bash
# Step 1: Save to temp file
npx conni-cli get-page '{"pageId":"98765"}' > /tmp/conf-page.json

# Step 2: Extract metadata only
cat /tmp/conf-page.json | jq '{
  id: .id,
  title: .title,
  spaceKey: .spaceKey,
  status: .status,
  version: .version.number,
  updated: .version.when,
  updatedBy: .version.by.displayName,
  contentLength: (.body.storage.value | length)
}'

# Step 3: If you need the content, extract it separately
cat /tmp/conf-page.json | jq -r '.body.storage.value' | head -100

# Step 4: Clean up
rm /tmp/conf-page.json
```

**Benefits:**

- **Context Efficiency:** Only load essential data instead of 50KB+ JSON
- **Faster Processing:** Use system tools (jq, grep) for filtering
- **Better Analysis:** Focus on relevant fields without HTML noise
- **Reusable:** Keep temp file if you need to extract different fields later

See **Pattern 1a: Handling Large Page Responses** in the Usage Patterns section for detailed examples.

## Available Commands

### Connection Testing

**Test Connection:**

```bash
npx conni-cli test-connection
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

### Space Operations

**List All Spaces:**

```bash
npx conni-cli list-spaces
```

**Expected Output:**

```json
{
  "results": [
    {
      "id": "123456",
      "key": "DOCS",
      "name": "Documentation",
      "type": "global",
      "status": "current"
    },
    {
      "id": "789012",
      "key": "TEAM",
      "name": "Team Space",
      "type": "global",
      "status": "current"
    }
  ]
}
```

**Get Specific Space:**

```bash
npx conni-cli get-space '{"spaceKey":"DOCS"}'
```

**Expected Output:**

```json
{
  "id": "123456",
  "key": "DOCS",
  "name": "Documentation",
  "type": "global",
  "status": "current",
  "homepageId": "98765",
  "_links": {
    "webui": "/spaces/DOCS"
  }
}
```

### Page Management

**List Pages in a Space:**

```bash
npx conni-cli list-pages '{"spaceKey":"DOCS","limit":10}'
```

**Expected Output:**

```json
{
  "results": [
    {
      "id": "98765",
      "type": "page",
      "status": "current",
      "title": "Getting Started",
      "spaceId": "123456",
      "version": {
        "number": 3,
        "when": "2025-01-15T10:30:00.000Z"
      }
    }
  ]
}
```

**Get Page Details:**

```bash
npx conni-cli get-page '{"pageId":"98765"}'
```

**Expected Output:**

```json
{
  "id": "98765",
  "type": "page",
  "status": "current",
  "title": "Getting Started",
  "spaceId": "123456",
  "body": {
    "storage": {
      "value": "<p>Page content here</p>",
      "representation": "storage"
    }
  },
  "version": {
    "number": 3,
    "when": "2025-01-15T10:30:00.000Z",
    "message": "Updated installation instructions"
  }
}
```

**Create Page:**

```bash
npx conni-cli create-page '{
  "spaceKey": "DOCS",
  "title": "New Documentation Page",
  "body": "<p>This is the page content in HTML format.</p><h2>Section 1</h2><p>Content here.</p>"
}'
```

**Create Child Page:**

```bash
npx conni-cli create-page '{
  "spaceKey": "DOCS",
  "title": "Child Page",
  "parentId": "98765",
  "body": "<p>This is a child page.</p>"
}'
```

**Expected Output:**

```json
{
  "id": "99999",
  "type": "page",
  "status": "current",
  "title": "New Documentation Page",
  "spaceId": "123456",
  "_links": {
    "webui": "/spaces/DOCS/pages/99999"
  }
}
```

**Update Page:**

```bash
npx conni-cli update-page '{
  "pageId": "98765",
  "title": "Updated Title",
  "body": "<p>Updated content</p>",
  "version": 4
}'
```

**Important:** You must provide the next version number when updating. Get the current version from `get-page` first.

**Delete Page:**

```bash
npx conni-cli delete-page '{"pageId":"98765"}'
```

### Comment Operations

**Add Comment to Page:**

```bash
npx conni-cli add-comment '{
  "pageId": "98765",
  "body": "<p>This is a comment on the page.</p>"
}'
```

**Expected Output:**

```json
{
  "id": "77777",
  "type": "comment",
  "status": "current",
  "title": "Re: Getting Started",
  "body": {
    "storage": {
      "value": "<p>This is a comment on the page.</p>",
      "representation": "storage"
    }
  }
}
```

### Attachment Operations

**List Page Attachments:**

```bash
npx conni-cli list-attachments '{"pageId":"98765"}'
```

**Expected Output:**

```json
{
  "results": [
    {
      "id": "12345",
      "type": "attachment",
      "status": "current",
      "title": "diagram.png",
      "metadata": {
        "mediaType": "image/png",
        "fileSize": 45678
      },
      "version": {
        "number": 1,
        "when": "2025-01-15T10:30:00.000Z"
      },
      "_links": {
        "download": "/download/attachments/98765/diagram.png",
        "webui": "/pages/viewpageattachments.action?pageId=98765&imageId=12345"
      }
    }
  ]
}
```

**Download Attachment:**

```bash
npx conni-cli download-attachment '{"pageId":"98765","attachmentId":"12345"}' > diagram.png
```

Or specify output file:

```bash
npx conni-cli download-attachment '{"pageId":"98765","attachmentId":"12345","outputFile":"/tmp/diagram.png"}'
```

**Upload Attachment to Page:**

```bash
npx conni-cli upload-attachment '{
  "pageId": "98765",
  "filePath": "/local/path/to/document.pdf",
  "title": "Documentation.pdf"
}'
```

**Expected Output:**

```json
{
  "id": "67890",
  "type": "attachment",
  "status": "current",
  "title": "Documentation.pdf",
  "metadata": {
    "mediaType": "application/pdf",
    "fileSize": 234567
  },
  "version": {
    "number": 1,
    "when": "2025-01-15T11:45:00.000Z"
  }
}
```

**Delete Attachment:**

```bash
npx conni-cli delete-attachment '{"attachmentId":"12345"}'
```

### User Operations

**Get User Info:**

```bash
npx conni-cli get-user '{"accountId":"557058:f5b...abc"}'
```

Or search by email:

```bash
npx conni-cli get-user '{"email":"john@example.com"}'
```

## Usage Patterns

### Pattern 1: Read Confluence Documentation

**User Request:** "Get the Getting Started page from DOCS space"

**Step 1: Find the Page**

```bash
# Search for the page by title
npx conni-cli list-pages '{"spaceKey":"DOCS","title":"Getting Started"}'
```

**Step 2: Get Page Content**

```bash
# Get full page details including content
npx conni-cli get-page '{"pageId":"98765"}'
```

**Response Format:**

```markdown
# Getting Started

**Space:** DOCS - Documentation
**Status:** Current
**Version:** 3 (Updated: 2025-01-15)
**Last Updated By:** John Doe

## Content

[Page content rendered from HTML storage format]

[View in Confluence](https://company.atlassian.net/wiki/spaces/DOCS/pages/98765)
```

### Pattern 1a: Handling Large Page Responses (RECOMMENDED)

**When to Use:** Confluence responses often contain extensive data (large HTML content, version history, metadata, macros, etc.) that can consume large amounts of context. For any page query, save the raw response to a temporary file first, then extract only the relevant information.

**User Request:** "Get the Getting Started page from DOCS space"

**Step 1: Find the Page and Save to Temp File**

```bash
# Search for the page by title and save response
npx conni-cli list-pages '{"spaceKey":"DOCS","title":"Getting Started"}' > /tmp/confluence-search.json

# Extract the page ID
PAGE_ID=$(cat /tmp/confluence-search.json | jq -r '.results[0].id')
echo "Found page ID: $PAGE_ID"
```

**Step 2: Fetch Page and Save to Temp File**

```bash
# Fetch full page details and save to temp file
npx conni-cli get-page "{\"pageId\":\"$PAGE_ID\"}" > /tmp/confluence-page-$PAGE_ID.json
```

**Step 3: Extract Metadata Using jq**

Extract only essential fields:

```bash
# Extract core page metadata
cat /tmp/confluence-page-$PAGE_ID.json | jq '{
  id: .id,
  title: .title,
  spaceKey: .spaceKey,
  status: .status,
  type: .type,
  version: {
    number: .version.number,
    when: .version.when,
    by: .version.by.displayName,
    message: .version.message
  },
  parentId: .parentId,
  position: .position,
  contentLength: (.body.storage.value | length),
  webUrl: ._links.webui
}'
```

**Step 4: Extract Content Separately (if needed)**

For the actual page content:

```bash
# Get full HTML content
cat /tmp/confluence-page-$PAGE_ID.json | jq -r '.body.storage.value' > /tmp/page-content.html

# Get plain text approximation (strip HTML tags)
cat /tmp/page-content.html | sed 's/<[^>]*>//g' | sed 's/&nbsp;/ /g' | sed 's/&lt;/</g' | sed 's/&gt;/>/g' | sed 's/&amp;/\&/g'

# Or just show first 50 lines
cat /tmp/page-content.html | head -50
```

**Step 5: Extract Specific Content Sections**

```bash
# Find specific headings or sections in the content
cat /tmp/page-content.html | grep -o '<h[1-6][^>]*>.*</h[1-6]>' | sed 's/<[^>]*>//g'

# Search for specific text in content
cat /tmp/page-content.html | sed 's/<[^>]*>//g' | grep -i "installation"
```

**Step 6: Check for Comments or Attachments**

```bash
# Check if page has children
cat /tmp/confluence-page-$PAGE_ID.json | jq '.children'

# Check for attachments (if included in response)
cat /tmp/confluence-page-$PAGE_ID.json | jq '.attachments'
```

**Step 7: Clean Up Temp Files**

```bash
rm /tmp/confluence-search.json
rm /tmp/confluence-page-$PAGE_ID.json
rm /tmp/page-content.html
```

**Alternative: Using grep for Quick Content Searches**

```bash
# Save page response
npx conni-cli get-page '{"pageId":"98765"}' > /tmp/conf-temp.json

# Find all macros used in the page
grep -o '<ac:structured-macro ac:name="[^"]*"' /tmp/conf-temp.json | sort -u

# Search for specific keywords in content
cat /tmp/conf-temp.json | jq -r '.body.storage.value' | grep -i "api endpoint"

# Get page version history info
cat /tmp/conf-temp.json | jq '.version'

# Clean up
rm /tmp/conf-temp.json
```

**Benefits:**

- **Context Efficiency:** Only load essential data into context instead of 50KB+ JSON with full HTML
- **Faster Processing:** Use system tools (jq, grep, sed) for filtering
- **Better Analysis:** Focus on relevant fields without HTML markup noise
- **Reusable:** Keep temp file if you need to extract different fields later
- **Content Control:** Separate metadata from content for better organization

**Response Format (Summarized):**

```markdown
# Getting Started

**Space:** DOCS - Documentation
**Type:** page
**Status:** current
**Version:** 3 (Updated: 2025-01-15T10:30:00.000Z)
**Last Updated By:** John Doe
**Version Message:** Updated installation instructions
**Content Size:** 12,453 characters

## Page Structure

Headings found in page:

1. Getting Started
2. Installation
3. Configuration
4. Quick Start
5. Troubleshooting

## Key Content Sections

**Installation:**
Run: npm install -g our-tool

**Configuration:**
Create config file at .config/tool.yml...

[View in Confluence](https://company.atlassian.net/wiki/spaces/DOCS/pages/98765)
```

### Pattern 2: Create Documentation Page

**User Request:** "Create a new page about API documentation in DOCS space"

**Execution:**

```bash
npx conni-cli create-page '{
  "spaceKey": "DOCS",
  "title": "API Documentation",
  "body": "<h1>API Documentation</h1><h2>Overview</h2><p>This page documents our REST API endpoints.</p><h2>Authentication</h2><p>All endpoints require API key authentication.</p>"
}'
```

**Response Format:**

```markdown
✓ Created page: API Documentation

**Space:** DOCS
**Page ID:** 99999
**Link:** https://company.atlassian.net/wiki/spaces/DOCS/pages/99999
```

### Pattern 3: Update Existing Page

**User Request:** "Update the Getting Started page with new installation instructions"

**Step 1: Get Current Version**

```bash
npx conni-cli get-page '{"pageId":"98765"}' | jq '.version.number'
# Output: 3
```

**Step 2: Update with Next Version**

```bash
npx conni-cli update-page '{
  "pageId": "98765",
  "title": "Getting Started",
  "body": "<h1>Getting Started</h1><h2>Installation</h2><p>Run: npm install -g our-tool</p><h2>Configuration</h2><p>Create config file...</p>",
  "version": 4
}'
```

**Response Format:**

```markdown
✓ Updated page: Getting Started

**Version:** 3 → 4
**Link:** https://company.atlassian.net/wiki/spaces/DOCS/pages/98765
```

### Pattern 4: Search Confluence

**User Request:** "Find all pages about authentication in our wiki"

**Execution:**

```bash
# List all pages and grep for authentication
npx conni-cli list-pages '{"limit":100}' | jq -r '.results[] | select(.title | test("authentication"; "i")) | "\(.title) (ID: \(.id), Space: \(.spaceId))"'
```

**Response Format:**

```markdown
# Pages about Authentication (3 results)

1. **API Authentication** (ID: 12345, Space: DOCS)
2. **User Authentication Flow** (ID: 23456, Space: TEAM)
3. **OAuth Authentication Guide** (ID: 34567, Space: DOCS)
```

### Pattern 5: Comment on Page

**User Request:** "Add a comment to page 98765 about the missing examples"

**Execution:**

```bash
npx conni-cli add-comment '{
  "pageId": "98765",
  "body": "<p>Great documentation! Could we add more code examples in the Authentication section?</p>"
}'
```

**Response Format:**

```markdown
✓ Added comment to: Getting Started

**Comment ID:** 77777
**Link:** https://company.atlassian.net/wiki/spaces/DOCS/pages/98765#comment-77777
```

### Pattern 6: Create Page Hierarchy

**User Request:** "Create a parent page 'Developer Guide' with child pages for 'Setup' and 'API Reference'"

**Step 1: Create Parent Page**

```bash
npx conni-cli create-page '{
  "spaceKey": "DOCS",
  "title": "Developer Guide",
  "body": "<h1>Developer Guide</h1><p>Complete guide for developers.</p>"
}'
# Output: {"id": "100000", ...}
```

**Step 2: Create Child Pages**

```bash
# Create first child
npx conni-cli create-page '{
  "spaceKey": "DOCS",
  "title": "Setup",
  "parentId": "100000",
  "body": "<h1>Setup</h1><p>How to set up your development environment.</p>"
}'

# Create second child
npx conni-cli create-page '{
  "spaceKey": "DOCS",
  "title": "API Reference",
  "parentId": "100000",
  "body": "<h1>API Reference</h1><p>Complete API documentation.</p>"
}'
```

**Response Format:**

```markdown
✓ Created page hierarchy:

**Parent:** Developer Guide (ID: 100000)
├── Setup (ID: 100001)
└── API Reference (ID: 100002)

**Links:**

- https://company.atlassian.net/wiki/spaces/DOCS/pages/100000
```

## Output Formats

The CLI supports two output formats:

### JSON (Default)

Machine-readable format for parsing and processing.

### TOON (Token-Oriented Object Notation)

AI-friendly format optimized for Claude to read and understand.

**Switch Format:**

```bash
npx conni-cli
confluence> format toon
```

## Interactive Mode

For exploratory work, use interactive mode:

```bash
npx conni-cli
```

**Available REPL Commands:**

- `commands` - List all commands
- `help` - Show help information
- `profile <name>` - Switch profiles
- `profiles` - List available profiles
- `format <type>` - Change output format (json/toon)
- `test-connection` - Verify connectivity
- `clear` - Clear the screen
- `exit` or `quit` - Close CLI

**Interactive Examples:**

```bash
npx conni-cli
confluence> list-spaces
confluence> get-space {"spaceKey":"DOCS"}
confluence> list-pages {"spaceKey":"DOCS","limit":5}
confluence> exit
```

## Content Formatting

Confluence uses HTML storage format for page content. Here are common patterns:

### Basic HTML Elements

```html
<p>Paragraph text</p>
<h1>Heading 1</h1>
<h2>Heading 2</h2>
<h3>Heading 3</h3>
<strong>Bold text</strong>
<em>Italic text</em>
<u>Underlined text</u>
```

### Lists

```html
<ul>
  <li>Unordered item 1</li>
  <li>Unordered item 2</li>
</ul>

<ol>
  <li>Ordered item 1</li>
  <li>Ordered item 2</li>
</ol>
```

### Links

```html
<a href="https://example.com">External Link</a>
<ac:link>
  <ri:page ri:content-title="Page Title" />
  <ac:plain-text-link-body
    ><![CDATA[Link to another page]]></ac:plain-text-link-body
  >
</ac:link>
```

### Code Blocks

```html
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body
    ><![CDATA[ def hello(): print("Hello, World!") ]]></ac:plain-text-body
  >
</ac:structured-macro>
```

### Tables

```html
<table>
  <thead>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Cell 1</td>
      <td>Cell 2</td>
    </tr>
  </tbody>
</table>
```

### Info/Warning Panels

```html
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>This is an info panel.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="warning">
  <ac:rich-text-body>
    <p>This is a warning panel.</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

## Error Handling

**Connection Failures:**

```json
{
  "error": "Connection failed",
  "message": "Invalid API token or host"
}
```

**Action:** Verify credentials in `.claude/atlassian-config.local.md`

**Page Not Found:**

```json
{
  "error": "Page does not exist",
  "pageId": "99999"
}
```

**Action:** Check page ID and space key

**Permission Denied:**

```json
{
  "error": "Forbidden",
  "message": "User lacks permission to perform this action"
}
```

**Action:** Request appropriate Confluence permissions from admin

**Version Conflict:**

```json
{
  "error": "Version conflict",
  "message": "Page has been updated since you last read it"
}
```

**Action:** Fetch latest version and retry update with correct version number

## Security Best Practices

1. **Never commit `.local.md` files**
   - Add `*.local.md` to `.gitignore`
   - Store credentials securely

2. **Use API tokens, not passwords**
   - Generate tokens from Atlassian account settings
   - Rotate tokens periodically

3. **Limit token permissions**
   - Grant only necessary Confluence permissions
   - Use separate tokens for different spaces

4. **Audit token usage**
   - Review Atlassian security logs
   - Revoke unused tokens

## Troubleshooting

### CLI Not Found

```bash
npm install -g conni-cli
```

### Connection Timeout

Check network connection and Confluence instance status:

```bash
curl -I https://your-domain.atlassian.net/wiki
```

### Invalid Space Key

Space keys are case-sensitive and must match exactly. Use `list-spaces` to find the correct key.

### Rate Limiting

Atlassian Cloud has rate limits:

- **20 requests per second** for Cloud instances
- **No limit** for Data Center

If rate-limited, retry after delay:

```bash
sleep 5 && npx conni-cli get-page '{"pageId":"98765"}'
```

### HTML Encoding Issues

When creating pages with special characters, ensure proper HTML encoding:

- `<` becomes `&lt;`
- `>` becomes `&gt;`
- `&` becomes `&amp;`
- `"` becomes `&quot;`

## Advanced Usage

### Bulk Page Creation

Create multiple pages using a loop:

```bash
for title in "Setup" "Configuration" "Deployment"; do
  npx conni-cli create-page "{
    \"spaceKey\": \"DOCS\",
    \"title\": \"$title\",
    \"body\": \"<h1>$title</h1><p>Content for $title</p>\"
  }"
done
```

### Page Templates

Save common page structures as templates:

```bash
# Save template
cat > /tmp/api-doc-template.html <<'EOF'
<h1>API Endpoint Documentation</h1>
<h2>Overview</h2>
<p>Endpoint description</p>
<h2>Request</h2>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[
curl -X GET https://api.example.com/endpoint
]]></ac:plain-text-body>
</ac:structured-macro>
<h2>Response</h2>
<p>Response description</p>
EOF

# Use template
BODY=$(cat /tmp/api-doc-template.html)
npx conni-cli create-page "{
  \"spaceKey\": \"DOCS\",
  \"title\": \"GET /users\",
  \"body\": \"$BODY\"
}"
```

### Export Page Content

Extract and save page content to local files:

```bash
# Get page content and save to markdown
npx conni-cli get-page '{"pageId":"98765"}' | \
  jq -r '.body.storage.value' | \
  html2text > getting-started.md
```

## Quick Reference

| Task                | Command                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| Test connection     | `npx conni-cli test-connection`                                                                      |
| List spaces         | `npx conni-cli list-spaces`                                                                          |
| Get space           | `npx conni-cli get-space '{"spaceKey":"DOCS"}'`                                                      |
| List pages          | `npx conni-cli list-pages '{"spaceKey":"DOCS"}'`                                                     |
| Get page            | `npx conni-cli get-page '{"pageId":"98765"}'`                                                        |
| Create page         | `npx conni-cli create-page '{"spaceKey":"DOCS","title":"Title","body":"<p>Content</p>"}'`            |
| Update page         | `npx conni-cli update-page '{"pageId":"98765","title":"Title","body":"<p>Content</p>","version":4}'` |
| Delete page         | `npx conni-cli delete-page '{"pageId":"98765"}'`                                                     |
| Add comment         | `npx conni-cli add-comment '{"pageId":"98765","body":"<p>Comment</p>"}'`                             |
| List attachments    | `npx conni-cli list-attachments '{"pageId":"98765"}'`                                                |
| Download attachment | `npx conni-cli download-attachment '{"pageId":"98765","attachmentId":"12345"}'`                      |
| Upload attachment   | `npx conni-cli upload-attachment '{"pageId":"98765","filePath":"/path/to/file.pdf"}'`                |
| Delete attachment   | `npx conni-cli delete-attachment '{"attachmentId":"12345"}'`                                         |
| Get user            | `npx conni-cli get-user '{"email":"john@example.com"}'`                                              |

## Notes

- **Always test connection** before running commands
- **Get current version** before updating pages
- **Use HTML storage format** for page content
- **TOON format** is optimized for AI consumption
- **Interactive mode** is great for exploration
- **Headless mode** is ideal for automation and scripting
- **Keep credentials secure** using `.local.md` pattern
- **Confluence and Jira** can share the same `.claude/atlassian-config.local.md` file
