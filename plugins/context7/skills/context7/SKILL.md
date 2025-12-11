---
name: Context7
description: This skill should be used when the user asks to "search for documentation", "get documentation", "find latest docs", "lookup library documentation", "search package docs", "get API docs", "find code examples", or needs to retrieve up-to-date, version-specific documentation for any library or package. Connects to Context7 server to fetch current documentation directly from the source.
---

# Context7 Skill

Search and retrieve up-to-date, version-specific documentation and examples for any library or package using the `context7-cli` tool with direct access to current documentation from the source.

## When to Use This Skill

Invoke when the user needs to:

- Search for documentation of a specific library or package
- Get the latest documentation for a framework (React, Next.js, Express, etc.)
- Find API reference documentation
- Retrieve code examples and usage patterns
- Look up specific topics within a library's documentation
- Access version-specific documentation
- Research library capabilities and features
- Get comprehensive documentation with pagination support

**Supported Libraries:** All libraries available in Context7, including but not limited to:
- Web frameworks (React, Next.js, Vue, Angular, Svelte, etc.)
- Backend frameworks (Laravel, Express, Django, Flask, Spring, etc.)
- Databases (MongoDB, PostgreSQL, MySQL, Redis, etc.)
- Cloud services (AWS, Vercel, Netlify, etc.)
- Programming languages and runtimes
- API services and SDKs
- And many more packages available on npm, PyPI, etc.

## Prerequisites

### 1. Install context7-cli Tool

The tool must be installed globally via npm:

```bash
npm install -g context7-cli
```

Verify installation:

```bash
npx context7-cli --version
```

### 2. Context7 Connection

Context7 requires a connection to the Context7 MCP server. The CLI tool handles this automatically.

**Note:** The first run may prompt for authentication or server connection details.

## Available Commands

### 1. resolve-library-id - Resolve Package Name to Library ID

Resolves a package/library name to a Context7-compatible library ID that can be used for fetching documentation.

**Syntax:**

```bash
npx context7-cli resolve-library-id '{"libraryName":"<package_name>"}'
```

**Parameters:**

- `libraryName` (required): Name of the package/library (e.g., "mongodb", "react", "express")

**Example:**

```bash
# Resolve MongoDB package name
npx context7-cli resolve-library-id '{"libraryName":"mongodb"}'

# Resolve Next.js package name
npx context7-cli resolve-library-id '{"libraryName":"next"}'

# Resolve React package name
npx context7-cli resolve-library-id '{"libraryName":"react"}'
```

**Output:**
Returns the Context7-compatible library ID (e.g., "/mongodb/docs", "/vercel/next.js") that can be used with `get-library-docs`.

### 2. get-library-docs - Fetch Documentation

Fetches comprehensive documentation for a library with optional topic focus and pagination.

**Syntax:**

```bash
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<library_id>","topic":"<topic>","page":<page_number>}'
```

**Parameters:**

- `context7CompatibleLibraryID` (required): Library ID from resolve-library-id (e.g., "/mongodb/docs", "/vercel/next.js")
- `topic` (optional): Specific topic to focus on (e.g., "routing", "authentication", "querying")
- `page` (optional): Page number for pagination (default: 1)

**Examples:**

```bash
# Get all documentation for MongoDB
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/mongodb/docs"}'

# Get Next.js documentation with focus on routing
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js","topic":"routing"}'

# Get specific page of React documentation
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/facebook/react","page":2}'

# Get Next.js authentication documentation, page 3
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js","topic":"authentication","page":3}'
```

**Output:**
Returns comprehensive documentation including:
- API references
- Code examples
- Usage patterns
- Configuration options
- Best practices
- Topic-specific guidance

## Execution Modes

### Headless Mode (Recommended for Skills)

Execute single commands and exit. Best for automation and skills.

```bash
npx context7-cli <command> '{"param":"value"}'
```

**For skills, ALWAYS use headless mode** for better error handling and output parsing.

## Best Practice: Save to Temporary File and Search

When working with documentation results, it's recommended to save outputs to temporary files and then search for specific information. This prevents overwhelming the context and makes it easier to find relevant details.

### Pattern: Save → Search → Analyze

```bash
# Step 1: Save documentation to a temporary file
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js"}' > /tmp/nextjs-docs.md

# Step 2: Read the file to search for specific information
Read: /tmp/nextjs-docs.md

# Step 3: Use grep or search within the file for specific topics
Grep: "routing" /tmp/nextjs-docs.md
Grep: "getStaticProps" /tmp/nextjs-docs.md
```

### Example Workflows

#### Example 1: Find Specific API Method

```bash
# Save comprehensive docs
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/mongodb/docs"}' > /tmp/mongodb-docs.md

# Search for specific method
Grep: "findOne" /tmp/mongodb-docs.md

# Or read and manually review
Read: /tmp/mongodb-docs.md
```

#### Example 2: Find Code Examples

```bash
# Save documentation
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/facebook/react","topic":"hooks"}' > /tmp/react-hooks.md

# Search for useEffect examples
Grep: "useEffect" /tmp/react-hooks.md

# Or find specific patterns
Grep: "example" /tmp/react-hooks.md
```

#### Example 3: Compare Features

```bash
# Save documentation for multiple libraries
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js","topic":"ssg"}' > /tmp/nextjs-ssg.md
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/nuxt/nuxt","topic":"ssg"}' > /tmp/nuxt-ssg.md

# Compare features
Grep: "static" /tmp/nextjs-ssg.md
Grep: "static" /tmp/nuxt-ssg.md
```

### Temporary File Naming Convention

Use descriptive names for temporary files:

```bash
# Good naming
/tmp/<library>-<topic>.md
/tmp/mongodb-querying.md
/tmp/react-hooks.md
/tmp/nextjs-routing.md

# Good naming with version
/tmp/express-middleware-v4.md
/tmp/express-middleware-v5.md
```

### Why Save to Files?

1. **Prevents Context Overflow**: Large documentation doesn't overwhelm the conversation
2. **Reusable**: Can search multiple times without re-fetching
3. **Shareable**: Can reference specific sections easily
4. **Organized**: Keep track of different documentation searches
5. **Searchable**: Use Grep, Read, and other tools to find specific information

### Combining with Other Tools

```bash
# Save docs
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/lodash/lodash"}' > /tmp/lodash-docs.md

# Extract specific functions
Grep: "function" /tmp/lodash-docs.md

# Count occurrences
Grep: -c "debounce" /tmp/lodash-docs.md

# Show context around matches
Grep: -C 5 "throttle" /tmp/lodash-docs.md
```

## Workflow for Common Tasks

### Task 1: Find Documentation for a Package

```bash
# Step 1: Resolve package name to library ID
npx context7-cli resolve-library-id '{"libraryName":"express"}'

# Step 2: Use the returned ID to get full documentation
# Suppose the ID is "/expressjs/express"
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/expressjs/express"}' > /tmp/express-docs.md

# Step 3: Search for specific information
Grep: "middleware" /tmp/express-docs.md
Read: /tmp/express-docs.md
```

### Task 2: Get Specific Topic Documentation

```bash
# Step 1: Resolve the package
npx context7-cli resolve-library-id '{"libraryName":"next"}'

# Step 2: Get documentation for specific topic
# Suppose the ID is "/vercel/next.js"
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js","topic":"routing"}' > /tmp/nextjs-routing.md

# Step 3: Find specific routing concepts
Grep: "Dynamic Routes" /tmp/nextjs-routing.md
Grep: "Link component" /tmp/nextjs-routing.md
```

### Task 3: Explore Documentation with Pagination

```bash
# Get first page and save to file
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/mongodb/docs","page":1}' > /tmp/mongodb-page1.md

# Get second page
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/mongodb/docs","page":2}' > /tmp/mongodb-page2.md

# Continue for more pages...

# Search across all pages
Grep: "findOne" /tmp/mongodb-page1.md
Grep: "findOne" /tmp/mongodb-page2.md
```

### Task 4: Find Code Examples

```bash
# Step 1: Resolve package
npx context7-cli resolve-library-id '{"libraryName":"react"}'

# Step 2: Get examples-focused documentation
# Suppose the ID is "/facebook/react"
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/facebook/react","topic":"examples"}' > /tmp/react-examples.md

# Step 3: Search for specific example types
Grep: "useState" /tmp/react-examples.md
Grep: "component" /tmp/react-examples.md
```

### Task 5: Research Library Capabilities

```bash
# Step 1: Resolve package
npx context7-cli resolve-library-id '{"libraryName":"lodash"}'

# Step 2: Get comprehensive documentation
# Suppose the ID is "/lodash/lodash"
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/lodash/lodash"}' > /tmp/lodash-docs.md

# Step 3: Explore available functions
Grep: "function" /tmp/lodash-docs.md | head -20

# Step 4: Find specific utility functions
Grep: "map" /tmp/lodash-docs.md
Grep: "filter" /tmp/lodash-docs.md
```

## Error Handling

### Common Errors and Solutions

**"Library not found":**

```
- Verify the package name is correct
- Check if the package exists on npm, PyPI, or other package managers
- Try alternative package names (e.g., "next" instead of "next.js")
```

**"Context7 server connection failed":**

```
- Ensure Context7 MCP server is running
- Check network connectivity
- Verify authentication credentials if required
- Try restarting the context7-cli tool
```

**"Invalid library ID":**

```
- Always use library ID from resolve-library-id command
- Verify the ID format starts with "/"
- Check if the library is available in Context7
```

**"Topic not found":**

```
- Verify the topic name is correct
- Try a broader topic or omit topic parameter
- Check available topics in the main documentation
```

**"Invalid page number":**

```
- Page numbers start from 1
- Check if the requested page exists
- Use page=1 if unsure
```

## Best Practices

### 1. Always Save Documentation to Temporary Files

```bash
# Save documentation to a file for later searching
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js"}' > /tmp/nextjs-docs.md

# Then search for specific information
Grep: "routing" /tmp/nextjs-docs.md
Read: /tmp/nextjs-docs.md
```

**Benefits:**
- Prevents context overflow
- Allows multiple searches without re-fetching
- Makes it easy to find specific information
- Enables comparison across different libraries

### 2. Always Resolve Library ID First

```bash
# Before fetching documentation, resolve the library ID
npx context7-cli resolve-library-id '{"libraryName":"<package_name>"}'

# Then use the returned ID for documentation and save to file
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<returned_id>"}' > /tmp/<library>-docs.md
```

This ensures:
- Correct library identification
- Valid library ID format
- Library availability verification

### 3. Use Specific Topics for Targeted Results

```bash
# Good - targeted search saved to file
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js","topic":"routing"}' > /tmp/nextjs-routing.md
Grep: "Dynamic Routes" /tmp/nextjs-routing.md

# General - broader results
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js"}' > /tmp/nextjs-all.md
```

### 4. Use Pagination with File Output

```bash
# For comprehensive libraries like React or MongoDB
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/facebook/react","page":1}' > /tmp/react-page1.md
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/facebook/react","page":2}' > /tmp/react-page2.md

# Search across pages
Grep: "useState" /tmp/react-page1.md
Grep: "useState" /tmp/react-page2.md
```

### 5. Verify Package Names

```bash
# Common package name variations:
# "react" not "react.js"
# "next" not "next.js" (for package name)
# "express" not "express.js"
# "mongodb" not "mongo"
```

### 6. Check Documentation Freshness

Context7 provides:
- Current documentation from official sources
- Version-specific content
- Recent updates and changes

Always note the version of documentation retrieved for accuracy.

### 7. Use Descriptive File Names

```bash
# Good - descriptive and searchable
/tmp/<library>-<topic>.md
/tmp/mongodb-querying.md
/tmp/react-hooks.md
/tmp/nextjs-routing.md

# Bad - not searchable
/tmp/docs1.md
/tmp output.txt
/tmp file123.md
```

### 8. Clean Up Temporary Files

```bash
# Remove temporary files when done
rm /tmp/nextjs-docs.md
rm /tmp/react-*.md

# Or keep for future reference if needed
```

## Integration Examples

### Example 1: Research Before Implementation

```bash
# User wants to use Redis for caching
# Step 1: Resolve Redis documentation
npx context7-cli resolve-library-id '{"libraryName":"redis"}'

# Step 2: Get comprehensive docs and save to file
# Suppose ID is "/redis/node-redis"
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/redis/node-redis"}' > /tmp/redis-docs.md

# Step 3: Get specific caching examples
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/redis/node-redis","topic":"caching"}' > /tmp/redis-caching.md

# Step 4: Search for specific patterns
Grep: "setex" /tmp/redis-caching.md
Grep: "TTL" /tmp/redis-caching.md
```

### Example 2: API Documentation Lookup

```bash
# User needs AWS SDK documentation
npx context7-cli resolve-library-id '{"libraryName":"aws-sdk"}'
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/aws/aws-sdk-js"}' > /tmp/aws-sdk.md

# Search for specific service
Grep: "S3" /tmp/aws-sdk.md
Grep: "EC2" /tmp/aws-sdk.md
```

### Example 3: Framework Feature Research

```bash
# User comparing Next.js vs Nuxt.js
npx context7-cli resolve-library-id '{"libraryName":"next"}'
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/vercel/next.js","topic":"ssg"}' > /tmp/nextjs-ssg.md

# Then do similar for Nuxt
npx context7-cli resolve-library-id '{"libraryName":"nuxt"}'
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/nuxt/nuxt","topic":"ssg"}' > /tmp/nuxt-ssg.md

# Compare features
Grep: "generate" /tmp/nextjs-ssg.md
Grep: "generate" /tmp/nuxt-ssg.md
```

### Example 4: Quick API Reference Lookup

```bash
# Save documentation
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"/facebook/react"}' > /tmp/react-api.md

# Find specific API quickly
Grep: "useEffect" /tmp/react-api.md | head -5

# Get full useEffect details
Grep: -A 20 "useEffect" /tmp/react-api.md
```

## Troubleshooting Guide

### Issue: resolve-library-id returns no results

**Diagnose:**

```bash
# Try alternative package names
npx context7-cli resolve-library-id '{"libraryName":"next"}'     # Try "next"
npx context7-cli resolve-library-id '{"libraryName":"next.js"}'  # Try "next.js"

# Check official package name on npm
# Visit https://www.npmjs.com/package/<package-name>
```

**Common fixes:**
- Check spelling
- Try variations of the package name
- Verify package exists on package manager
- Check if package is available in Context7

### Issue: get-library-docs returns error

**Diagnose:**

```bash
# First, verify the library ID is correct
npx context7-cli resolve-library-id '{"libraryName":"<package>"}'

# Then use exactly that ID
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<exact_id_from_resolve>"}'
```

**Common fixes:**
- Use exact library ID from resolve-library-id
- Check for typos in library ID
- Verify library is available in Context7
- Try without topic parameter first

### Issue: Documentation is outdated or incorrect

**Context7 Advantages:**
- Documentation fetched directly from official sources
- Version-specific content
- Current as of retrieval time

**If issues persist:**
- Check version information in output
- Verify you're looking at the correct version
- Note that Context7 reflects the current state of documentation

## Quick Reference

### Command Cheat Sheet

```bash
# Resolve package name to library ID
npx context7-cli resolve-library-id '{"libraryName":"<package_name>"}'

# Get all documentation
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<library_id>"}'

# Get topic-specific documentation
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<library_id>","topic":"<topic>"}'

# Get paginated documentation
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<library_id>","page":<page_number>}'

# Get topic-specific with pagination
npx context7-cli get-library-docs '{"context7CompatibleLibraryID":"<library_id>","topic":"<topic>","page":<page_number>}'
```

### Common Library IDs

```bash
# Note: Always use resolve-library-id to get the correct ID
# These are examples of what the IDs might look like:

/mongodb/docs                          # MongoDB
/vercel/next.js                        # Next.js
/facebook/react                        # React
/expressjs/express                     # Express
/aws/aws-sdk-js                        # AWS SDK
/lodash/lodash                         # Lodash
/redis/node-redis                      # Redis
/microsoft/TypeScript                  # TypeScript
/vuejs/core                            # Vue.js
```

### Workflow Summary

```
1. Resolve package name → get library ID
2. Fetch documentation using library ID
3. Use topic parameter for focused results
4. Use pagination for comprehensive coverage
5. Verify version and freshness
```

---

**Remember:** Always resolve the library ID first, use specific topics for targeted results, and leverage pagination for comprehensive documentation access. Context7 provides the most current documentation directly from official sources.
