# Text Formatting

Jira uses Atlassian's Wiki Markup notation for formatting text in descriptions, comments, and other text fields. This section provides a quick reference for common formatting needs when creating or updating issues.

## Headings

Create section headings to structure your content:

```
h1. Main Title
h2. Section Heading
h3. Subsection
h4. Sub-subsection
h5. Minor Heading
h6. Smallest Heading
```

**Example:**

```markdown
h1. Bug Report: Login Functionality

h2. Summary
User cannot login with valid credentials

h2. Steps to Reproduce
h3. Expected Behavior
h3. Actual Behavior

h2. Additional Notes
```

## Text Effects

Emphasize important information in content:

| Notation        | Effect            | Example                  |
| --------------- | ----------------- | ------------------------ |
| `*bold*`        | **Bold**          | `*Critical bug*`         |
| `_emphasis_`    | _Italic_          | `_Important note_`       |
| `??citation??`  | Citation          | `??Reference: RFC 123??` |
| `-deleted-`     | ~~Strikethrough~~ | `-Deprecated code-`      |
| `+inserted+`    | Underlined        | `+New feature+`          |
| `^superscript^` | Superscript       | `Version 2^nd^`          |
| `~subscript~`   | Subscript         | `H~2~O`                  |
| `{{monospace}}` | `Code style`      | `{{database-url}}`       |

**Example:**

```markdown
_Critical:_ The system crashes when users try to login.

_Expected behavior:_ User should be redirected to dashboard.

The +new API+ uses ??OAuth 2.0?? for authentication.

Version 2^nd^ edition includes H~2~O calculations.
```

## Lists

Organize information using bullet points and numbered lists:

**Bulleted Lists:**

```
* First item
* Second item
** Nested item
** Another nested item
* Third item
```

**Numbered Lists:**

```
# First step
# Second step
# Sub-step
# Another sub-step
# Third step
```

**Mixed Lists:**

```
# Step 1
# Step 2
* Bullet point A
* Bullet point B
# Step 3
```

**Example:**

```markdown
h2. Reproduction Steps

# Navigate to login page

# Enter valid credentials

# Click "Login" button

# Observe error message

h2. Affected Components

- Authentication module
- Session manager
- Database layer

h2. Priority Tasks

# Fix database connection pool

- Update error logging

# Review security protocols
```

## Links

Add links to documentation, tickets, or external resources:

```
[http://example.com]
[Atlassian Docs|http://docs.atlassian.com]
[#anchor-name]
[^attachment.ext]
[~username]
[mailto:user@example.com]
```

**Example:**

```markdown
h2. Related Documentation

See the [API Documentation|http://api.example.com/docs] for details.

Refer to ticket [PROJ-456] for similar issues.

Contact [~john.doe] for questions.

See [Setup Guide#database] for database configuration.

Check the attached file [^screenshot.png].
```

## Code Blocks

Display code snippets with syntax highlighting:

**Simple Code Block:**

```
{code}
function login(user, password) {
    if (validate(user, password)) {
        return authenticate(user);
    }
}
{code}
```

**Code Block with Language and Title:**

```
{code:title=auth.js|borderStyle=solid}
function login(user, password) {
    if (validate(user, password)) {
        return authenticate(user);
    }
}
{code}
```

**Code Block for Different Languages:**

```
{code:python}
def authenticate(user, password):
    return check_credentials(user, password)
{code}

{code:sql}
SELECT * FROM users WHERE username = ?
{code}

{code:json}
{
  "user": "john",
  "token": "abc123"
}
{code}
```

**Example:**

```markdown
h2. Error Stack Trace

{code:java}
Exception in thread "main" java.lang.NullPointerException
at com.example.auth.LoginService.authenticate(LoginService.java:45)
at com.example.auth.AuthController.login(AuthController.java:23)
{code}

h2. Configuration

{code:json}
{
"database": {
"host": "localhost",
"port": 5432,
"ssl": true
}
}
{code}
```

## Panels

Create highlighted sections to draw attention to important information:

```
{panel}
This is a simple panel with important information.
{panel}

{panel:title=Security Warning}
This panel has a custom title and contains critical security information.
{panel}

{panel:title=Known Issues|borderStyle=dashed|borderColor=#ccc|bgColor=#ffe}
This is a panel with custom styling for known issues.
{panel}
```

**Example:**

```markdown
{panel:title=⚠️ Critical Bug}
This bug affects all users in production. Immediate attention required.
{panel}

h2. Workaround

{panel}
A temporary workaround is available:

1. Restart the service
2. Clear cache
3. Re-apply configuration
   {panel}
```

## Preformatted Text

Display text without any formatting:

```
{noformat}
This text will not be formatted at all.
No *bold* or _italic_ or [links] will work here.
{noformat}
```

**Example:**

```markdown
h2. Raw Configuration

{noformat}
DATABASE_URL=postgresql://localhost:5432/mydb
DEBUG=false
SESSION_TIMEOUT=3600
{noformat}
```

## Tables

Organize data in tabular format:

```
|| Column 1 || Column 2 || Column 3 ||
| Value A1 | Value A2 | Value A3 |
| Value B1 | Value B2 | Value B3 |
```

**Example:**

```markdown
h2. Test Results

|| Test Case || Status || Priority ||
| Login with valid credentials | ✅ PASS | High |
| Login with invalid credentials | ✅ PASS | High |
| Session timeout | ❌ FAIL | Critical |
| Password reset | ✅ PASS | Medium |

h2. Browser Compatibility

|| Browser || Version || Status ||
| Chrome | 120+ | ✅ Supported |
| Firefox | 121+ | ✅ Supported |
| Safari | 17+ | ⚠️ Partial |
| Edge | 120+ | ✅ Supported |
```

## Images

Embed screenshots and images:

```
!image.png!
!http://example.com/image.jpg!
!image.png|thumbnail!
!image.png|align=right, vspace=4!
```

**Example:**

```markdown
h2. Screenshot

!error-screenshot.png!

h2. Architecture Diagram

!https://example.com/diagram.svg|width=600!

h2. Attachment Reference

The logo is attached to this issue: [^logo.png]
```

## Text Breaks

Control spacing and line breaks:

```
Line break: \\
Horizontal rule: ----
Em dash: ---
En dash: --
```

**Example:**

```markdown
This is line one.
This is line two. (automatic paragraph break)

Line break: \\
This is on the next line. (manual line break)

---

# Section 1

Content here

--- Section separator

# Section 2

More content

Here is an em dash --- like this.
Here is an en dash -- like this.
```

## Block Quotes

Quote important information or specifications:

```
bq. This is a single paragraph block quote.

bq.
This is a multi-line
block quote that spans
multiple paragraphs.

{quote}
Multiple paragraphs
can be quoted using
the quote macro.
{quote}
```

**Example:**

```markdown
h2. Requirements

bq. The system shall authenticate users before granting access to protected resources.

bq.
From the security audit:
All password storage must use industry-standard hashing algorithms.
Multi-factor authentication is required for admin accounts.
{quote}
```

## Color Text

Highlight text with colors (use sparingly):

```
{color:red}Red text{color}
{color:blue}Blue text{color}
{color:green}Green text{color}
```

**Example:**

```markdown
{color:red}Critical: System is down{color}

Status: {color:green}Operational{color}

Priority: {color:orange}Medium{color}
```

## User Mentions

Reference team members:

```
[~username]
```

**Example:**

```markdown
h2. Assignment

{color:red}Assigned to{color} [~john.doe] for investigation.

Please review and update: [~jane.smith] [~bob.wilson]
```

## Escape Special Characters

Prevent wiki formatting:

```
\*
\_
\[
\~
\{color:red\}
```

**Example:**

```markdown
The \* wildcard character is used for search.
Use \_emphasis\_ to show italic text literally.
Special characters like \{ and \} need escaping.
```
