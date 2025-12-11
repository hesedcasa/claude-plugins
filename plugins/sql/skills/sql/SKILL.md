---
name: SQL
description: This skill should be used when the user asks to "execute MySQL query", "execute PostgreSQL query", "query MySQL database", "query PostgreSQL database", "query database", "connect to MySQL", "connect to PostgreSQL", "run SQL query", "show database tables", "explain query", "analyze query performance", or needs to interact with MySQL or PostgreSQL databases. Provides direct database access with safety features.
---

# MySQL/PostgreSQL Skill

Execute SQL queries and perform database operations on MySQL and PostgreSQL databases using the `mysqldb-cli` tool with built-in safety features and multiple output formats.

## When to Use This Skill

Invoke when the user needs to:

- Execute SQL queries (SELECT, INSERT, UPDATE, DELETE)
- List databases or tables
- Describe table structure and schema
- Show table indexes
- Explain query execution plans
- Test database connectivity
- Perform database introspection
- Export query results to CSV/JSON/TOON

**Supported Databases:** This skill supports both MySQL and PostgreSQL databases with a unified command interface.

## Prerequisites

### 1. Install mysqldb-cli Tool

The tool must be installed globally via npm:

```bash
npm install -g mysqldb-cli
```

Verify installation:

```bash
npx mysqldb-cli --version
```

### 2. Configure Database Profiles

Database profiles are configured in `.claude/sql-config.local.md` with YAML formatter:

```yaml
---
profiles:
  local-dev:
    type: mysql
    host: localhost
    port: 3306
    user: root
    password: dev_password
    database: myapp_dev

  postgres-dev:
    type: postgresql
    host: localhost
    port: 5432
    user: postgres
    password: dev_password
    database: myapp_dev
    schema: public

  production:
    type: mysql
    host: db.example.com
    port: 3306
    user: app_user
    password: secure_password
    database: myapp_prod
    ssl: true

safety:
  defaultLimit: 100
  requireConfirmationFor:
    - DELETE
    - UPDATE
    - DROP
    - TRUNCATE
    - ALTER
  blacklistedOperations:
    - DROP DATABASE

defaultProfile: local-dev
defaultFormat: toon
---
```

**Profile Configuration Fields:**

- `type` (optional): Database type - `mysql` or `postgresql` (defaults to `mysql` for backward compatibility)
- `host` (required): Database server hostname
- `port` (required): Database server port (3306 for MySQL, 5432 for PostgreSQL)
- `user` (required): Database username
- `password` (required): Database password
- `database` (required): Database name
- `schema` (optional): PostgreSQL schema name (defaults to `public`, PostgreSQL only)
- `ssl` (optional): Enable SSL connection (true/false)

**IMPORTANT:** Always read `.claude/sql-config.local.md` first to get available profiles and safety settings before executing queries.

## Available Commands

### 1. query - Execute SQL Queries

Execute any SQL query with configurable output format.

**Syntax:**

```bash
npx mysqldb-cli query '{"query":"<SQL>","profile":"<profile>","format":"<format>"}'
```

**Parameters:**

- `query` (required): SQL statement to execute
- `profile` (optional): Profile name from config (defaults to `defaultProfile`)
- `format` (optional): Output format - `table`, `json`, `csv` or `toon` (defaults to `toon`)

**Examples:**

```bash
# Simple SELECT with table output (MySQL)
npx mysqldb-cli query '{"query":"SELECT * FROM users LIMIT 5"}'

# Use specific PostgreSQL profile
npx mysqldb-cli query '{"query":"SELECT COUNT(*) FROM orders","profile":"postgres-dev"}'

# JSON output for parsing
npx mysqldb-cli query '{"query":"SELECT id, email FROM users WHERE active = 1","format":"json"}'

# CSV export (MySQL date function)
npx mysqldb-cli query '{"query":"SELECT * FROM logs WHERE created_at > NOW() - INTERVAL 1 DAY","format":"csv"}'

# PostgreSQL date function
npx mysqldb-cli query '{"query":"SELECT * FROM logs WHERE created_at > NOW() - INTERVAL '\''1 day'\''","profile":"postgres-dev","format":"toon"}'
```

**Safety Features:**

- Queries without LIMIT are automatically limited to `default_limit` rows
- Destructive operations (DELETE, UPDATE, DROP, etc.) require confirmation
- Blacklisted operations are blocked completely

### 2. list-databases - Show All Databases

Display all accessible databases on the server.

**Syntax:**

```bash
npx mysqldb-cli list-databases '{"profile":"<profile>"}'
```

**Example:**

```bash
npx mysqldb-cli list-databases '{"profile":"production"}'
```

### 3. list-tables - Show Tables in Database

Display all tables in the current database.

**Syntax:**

```bash
npx mysqldb-cli list-tables '{"profile":"<profile>"}'
```

**Example:**

```bash
npx mysqldb-cli list-tables '{"profile":"local-dev"}'
```

### 4. describe-table - Show Table Structure

Display table schema including columns, types, keys, and constraints.

**Syntax:**

```bash
npx mysqldb-cli describe-table '{"table":"<table_name>","profile":"<profile>"}'
```

**Example:**

```bash
npx mysqldb-cli describe-table '{"table":"users","profile":"local-dev"}'
```

**Output includes:**

- Column names and data types
- NULL/NOT NULL constraints
- Default values
- Primary keys
- Auto-increment settings

### 5. show-indexes - Display Table Indexes

List all indexes on a specific table.

**Syntax:**

```bash
npx mysqldb-cli show-indexes '{"table":"<table_name>","profile":"<profile>"}'
```

**Example:**

```bash
npx mysqldb-cli show-indexes '{"table":"orders","profile":"production"}'
```

**Useful for:**

- Query optimization
- Identifying missing indexes
- Understanding query performance

### 6. explain-query - Analyze Query Execution Plan

Show how the database will execute a query (equivalent to EXPLAIN for MySQL or EXPLAIN ANALYZE for PostgreSQL).

**Syntax:**

```bash
npx mysqldb-cli explain-query '{"query":"<SQL>","profile":"<profile>"}'
```

**Example:**

```bash
npx mysqldb-cli explain-query '{"query":"SELECT * FROM users WHERE email = '\''user@example.com'\''","profile":"local-dev"}'
```

**Output includes:**

- Query execution plan
- Index usage
- Join types
- Row estimates
- Performance warnings

**Note:** Escape single quotes in queries using `'\''` pattern.

### 7. test-connection - Verify Database Connectivity

Test connection to a database profile.

**Syntax:**

```bash
npx mysqldb-cli test-connection '{"profile":"<profile>"}'
```

**Example:**

```bash
npx mysqldb-cli test-connection '{"profile":"production"}'
```

**Returns:**

- Connection status (success/failure)
- Server version
- Connection details
- Error messages if connection fails

## Execution Modes

### Headless Mode (Recommended for Skills)

Execute single commands and exit. Best for automation and skills.

```bash
npx mysqldb-cli <command> '{"param":"value"}'
```

### Interactive Mode

Start a REPL session for multiple operations.

```bash
npx mysqldb-cli
sql> query '{"query":"SELECT COUNT(*) FROM users"}'
sql> describe-table '{"table":"users"}'
sql> exit
```

**For skills, ALWAYS use headless mode** for better error handling and output parsing.

## Workflow for Common Tasks

### Task 1: Explore Database Structure

```bash
# Step 1: List all databases
npx mysqldb-cli list-databases '{"profile":"local-dev"}'

# Step 2: List tables in database
npx mysqldb-cli list-tables '{"profile":"local-dev"}'

# Step 3: Describe specific table
npx mysqldb-cli describe-table '{"table":"users","profile":"local-dev"}'

# Step 4: Check indexes
npx mysqldb-cli show-indexes '{"table":"users","profile":"local-dev"}'
```

### Task 2: Query Data

```bash
# Step 1: Test connection
npx mysqldb-cli test-connection '{"profile":"production"}'

# Step 2: Execute query with table output
npx mysqldb-cli query '{"query":"SELECT * FROM users WHERE created_at > '\''2024-01-01'\''","profile":"production"}'

# Step 3: Export to JSON if needed
npx mysqldb-cli query '{"query":"SELECT id, email, status FROM users","profile":"production","format":"json"}'
```

### Task 3: Optimize Queries

```bash
# Step 1: Explain the slow query
npx mysqldb-cli explain-query '{"query":"SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE u.email LIKE '\''%@example.com'\''","profile":"local-dev"}'

# Step 2: Check for missing indexes
npx mysqldb-cli show-indexes '{"table":"orders","profile":"local-dev"}'

# Step 3: Verify table structure
npx mysqldb-cli describe-table '{"table":"orders","profile":"local-dev"}'
```

### Task 4: Safe Data Modifications

```bash
# Step 1: Preview affected rows
npx mysqldb-cli query '{"query":"SELECT COUNT(*) FROM users WHERE last_login < NOW() - INTERVAL 1 YEAR","profile":"local-dev"}'

# Step 2: Execute DELETE (will require confirmation)
npx mysqldb-cli query '{"query":"DELETE FROM users WHERE last_login < NOW() - INTERVAL 1 YEAR","profile":"local-dev"}'

# Note: The tool will prompt for confirmation before executing destructive operations
```

## Safety Considerations

### 1. Confirmation Required Operations

These operations will prompt for user confirmation:

- `DELETE` - Deleting rows
- `UPDATE` - Modifying data
- `DROP` - Dropping tables/indexes
- `TRUNCATE` - Emptying tables
- `ALTER` - Modifying table structure

**When executing these, inform the user:**

```
⚠️  This query requires confirmation. The tool will prompt you to confirm before execution.
```

### 2. Blacklisted Operations

These operations are completely blocked:

- `DROP DATABASE` - Dropping entire databases
- Any custom blacklisted operations from config

**Always check the config file for blacklisted operations before executing queries.**

### 3. Query Limits

- SELECT queries without LIMIT are automatically capped at `default_limit` rows
- Prevents accidentally fetching millions of rows
- Override by adding explicit LIMIT clause

**Recommended practice:**

```sql
-- Bad (will be limited to default_limit)
SELECT * FROM large_table

-- Good (explicit limit)
SELECT * FROM large_table LIMIT 1000

-- Good (specific filtering)
SELECT * FROM large_table WHERE created_at > '2024-01-01' LIMIT 500
```

### 4. Production Database Safety

**ALWAYS:**

- Use read-only users for production queries when possible
- Enable SSL for remote connections (`ssl: true` in profile)
- Use specific profiles (never use `root` user for production)
- Test queries on dev/staging before production
- Review EXPLAIN output for expensive queries

**NEVER:**

- Execute untested queries on production
- Use wildcards in UPDATE/DELETE without WHERE clause
- Bypass confirmation prompts without understanding impact
- Share database credentials in code or logs

## Error Handling

### Common Errors and Solutions

**"Configuration file not found":**

```
Ensure `.claude/sql-config.local.md` exists in project root
```

**"Profile not found: xyz":**

```bash
# Read config to see available profiles
Read: .claude/sql-config.local.md
```

**"Access denied for user":**

```
- Verify username and password in profile
- Check user has permission to access database
- Confirm IP whitelist allows connection
```

**"Connection refused":**

```
- Verify database server is running
- Check host and port are correct
- Ensure firewall allows connection on port 3306 (MySQL) or 5432 (PostgreSQL)
```

**"Unknown database":**

```
- Verify database name is correct
- User may not have permission to access database
- Database may not exist
```

**"Syntax error in SQL":**

```
- Check SQL syntax
- Verify table/column names are correct
- Escape special characters properly
```

## Output Formats

### TOON Format (Default)

Compact encoding of JSON that minimizes tokens and makes structure easy for LLMs to follow:

```
id|email|status
1|user1@example.com|active
2|user2@example.com|active
```

**Best for:** LLM processing, token efficiency, programmatic parsing by Claude

### Table Format

Human-readable ASCII table:

```
+----+------------------+--------+
| id | email            | status |
+----+------------------+--------+
| 1  | user1@example.com| active |
| 2  | user2@example.com| active |
+----+------------------+--------+
```

**Best for:** Interactive queries, human-readable output, quick data inspection

### JSON Format

Structured JSON array:

```json
[
  { "id": 1, "email": "user1@example.com", "status": "active" },
  { "id": 2, "email": "user2@example.com", "status": "active" }
]
```

**Best for:** Programmatic parsing, data processing, API responses

### CSV Format

Comma-separated values:

```csv
id,email,status
1,user1@example.com,active
2,user2@example.com,active
```

**Best for:** Data export, Excel import, reporting

## Best Practices

### 1. Always Read Config First

```bash
# Before any database operation, read the config
Read: .claude/sql-config.local.md
```

This provides:

- Available profiles
- Safety settings
- Default configurations

### 2. Choose Appropriate Profile

- Use `local-dev` for development queries
- Use `readonly` or read-replica profiles for production queries
- Use specific profiles rather than `defaultProfile` for clarity

### 3. Use Explicit Limits

```sql
-- Always add LIMIT for large tables
SELECT * FROM users WHERE active = 1 LIMIT 100

-- Use COUNT(*) first to estimate result size
SELECT COUNT(*) FROM users WHERE active = 1
```

### 4. Test Destructive Queries

```sql
-- Step 1: Count affected rows
SELECT COUNT(*) FROM users WHERE last_login < '2023-01-01'

-- Step 2: Preview data
SELECT id, email, last_login FROM users WHERE last_login < '2023-01-01' LIMIT 10

-- Step 3: Execute delete
DELETE FROM users WHERE last_login < '2023-01-01'
```

### 5. Use EXPLAIN for Slow Queries

```bash
# Always explain before running expensive queries
npx mysqldb-cli explain-query '{"query":"SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE o.created_at > '\''2024-01-01'\''","profile":"production"}'
```

### 6. Escape Special Characters

For queries with quotes, escape properly:

```bash
# Use '\'' to escape single quotes in bash
npx mysqldb-cli query '{"query":"SELECT * FROM users WHERE email = '\''user@example.com'\''","profile":"local-dev"}'
```

### 7. Format Complex Queries

For readability, format multi-line queries:

```sql
SELECT
    u.id,
    u.email,
    COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id
LIMIT 100
```

## Troubleshooting Guide

### Issue: Query returns no results

**Diagnose:**

```bash
# Check table structure
npx mysqldb-cli describe-table '{"table":"users","profile":"local-dev"}'

# Check if table has data
npx mysqldb-cli query '{"query":"SELECT COUNT(*) FROM users","profile":"local-dev"}'

# Verify column names
npx mysqldb-cli query '{"query":"SHOW COLUMNS FROM users","profile":"local-dev"}'
```

### Issue: Query is slow

**Diagnose:**

```bash
# Explain query execution plan
npx mysqldb-cli explain-query '{"query":"<slow-query>","profile":"local-dev"}'

# Check for missing indexes
npx mysqldb-cli show-indexes '{"table":"<table>","profile":"local-dev"}'

# Add LIMIT to reduce result set
npx mysqldb-cli query '{"query":"<slow-query> LIMIT 10","profile":"local-dev"}'
```

### Issue: Cannot connect to database

**Diagnose:**

```bash
# Test connection
npx mysqldb-cli test-connection '{"profile":"local-dev"}'

# Verify profile configuration
Read: .claude/sql-config.local.md
```

**Common fixes:**

- Check host and port are correct (3306 for MySQL, 5432 for PostgreSQL)
- Verify username and password
- Ensure database server is running
- Check firewall rules
- Confirm IP whitelist

## Quick Reference

### Command Cheat Sheet

```bash
# Query
npx mysqldb-cli query '{"query":"<SQL>","profile":"<profile>","format":"<format>"}'

# List databases
npx mysqldb-cli list-databases '{"profile":"<profile>"}'

# List tables
npx mysqldb-cli list-tables '{"profile":"<profile>"}'

# Describe table
npx mysqldb-cli describe-table '{"table":"<table>","profile":"<profile>"}'

# Show indexes
npx mysqldb-cli show-indexes '{"table":"<table>","profile":"<profile>"}'

# Explain query
npx mysqldb-cli explain-query '{"query":"<SQL>","profile":"<profile>"}'

# Test connection
npx mysqldb-cli test-connection '{"profile":"<profile>"}'
```

### Output Formats

- `toon` - Compact encoding of the JSON that minimizes tokens and makes structure easy for LLM to follow (default)
- `table` - Human-readable ASCII table
- `json` - Structured JSON array
- `csv` - Comma-separated values

---

**Remember:** Always read the config file first, choose the appropriate profile, use explicit limits, and test queries before executing destructive operations.
