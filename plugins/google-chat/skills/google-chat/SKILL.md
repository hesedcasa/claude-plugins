---
name: google-chat
description: This skill should be used when sending messages to Google Chat. Use when the user says phrases like "send to chat", "notify the team", "post to Google Chat", "reply to thread", or requests to send status updates, notifications, or messages to a Google Chat space. Supports text with basic formatting (bold, italic, links) and can reply to existing threads.
---

# Google Chat

Send messages to Google Chat spaces using API key and token. Supports plain text and formatted messages with bold, italic, links, emoji, and more.

## When to Use This Skill

Use this skill when the user wants to:

- Send messages to Google Chat (e.g., "Send to chat: Task completed")
- Notify a team in Google Chat (e.g., "Notify the team about the deployment")
- Post status updates to a chat space
- Share task completion updates or error alerts
- Reply to an existing thread in Google Chat (e.g., "Reply to that thread with an update")

### Step 1: Create config.json

Create a `config.jsonc` file in the skill directory with the following structure:

```jsonc
{
  "key": "<api_key>",
  "tokens": {
    "<space_id1>": "<space_token1>", // deployment
    "<space_id2>": "<space_token2>", // sentry-alerts
  },
}
```

### Step 2: Verify Setup

Test the configuration by sending a test message:

```bash
python scripts/send_message.py --space-id "space_id1" --message "Test message from Claude"

python scripts/reply_message.py --thread-name "space/space_id1/thread/thread_id1" --message "Test message from Claude"
```

## Sending Messages

### Basic Usage

To send a plain text message, run the script:

```bash
python scripts/send_message.py --space-id "space_id1" --message "Your message here"
```

### Formatted Messages

To send messages with formatting (bold, italic, links, etc.), use the `--formatted` flag:

```bash
python scripts/send_message.py --space-id "space_id1" --message "*Important:* Task completed ✅" --formatted
```

### Message Formatting Options

Refer to `references/message_formatting.md` for detailed formatting examples, including:

- **Bold**, _italic_, ~strikethrough~, `code`
- Links: `<https://example.com|Link Text>`
- Lists (bullet and numbered)
- Emoji support (✅, ⚠️, 🚀, etc.)
- Code blocks
- User mentions

Load the reference file when the user needs help with message formatting or wants to send rich formatted messages.

## Replying to Threads

To reply to an existing thread in Google Chat, use the `reply_message.py` script with the thread name:

```bash
python scripts/reply_message.py --thread-name "space/space_id1/thread/thread_id1" --message "Your reply here"
```

### Getting Thread Names

Thread names follow the format: `spaces/{SPACE_ID}/threads/{THREAD_ID}`

You can obtain thread names from:

- Previous message responses (the API returns thread names when messages are sent)
- User providing the thread name

### Reply with Formatting

Like send_message.py, you can use the `--formatted` flag for rich text:

```bash
python scripts/reply_message.py --thread-name "space/space_id1/thread/thread_id1" --message "*Update:* Task completed ✅" --formatted
```

### Example Thread Replies

**User:** "Reply to thread space/space_id1/thread/thread_id1 with: Tests are now passing"

**Action:**

```bash
python scripts/reply_message.py --thread-name "space/space_id1/thread/thread_id1" --message "Tests are now passing"
```

## Workflow

When the user requests to send a message to Google Chat:

1. **Determine if it's a new message or thread reply**:
   - If user mentions "thread" or provides a thread name, use `reply_message.py`
   - Otherwise, use `send_message.py` for new messages
2. **Extract the message content** from the user's request
3. **Determine if formatting is needed**:
   - If the message includes markdown-like syntax (\*, \_, ~, `), use `--formatted`
   - For plain text, omit the flag
4. **Run the appropriate script** with parameters:
   - `send_message.py` for new messages
   - `reply_message.py --thread-name <thread>` for thread replies
5. **Report the result** to the user (success or error)

### Example Interactions

**User:** "Send to chat: Tests passed successfully ✅"

**Action:**

```bash
python scripts/send_message.py --space-id "space_id1" --message "Tests passed successfully ✅"
```

**User:** "Notify the team: _Deployment Complete_ - All services are now live"

**Action:**

```bash
python scripts/send_message.py --space-id "space_id1" --message "*Deployment Complete* - All services are now live" --formatted
```

**User:** "Post an update about the bug fix with a link to the PR"

**Action:**

```bash
python scripts/send_message.py --space-id "space_id1" --message "🐛 *Bug Fix Deployed*\n\nFixed authentication issue\n<https://github.com/user/repo/pull/123|View PR>" --formatted
```

## Error Handling

Common errors and solutions:

- **"Space ID not configured"**: Ensure `config.jsonc` exists or environment variable is set
- **"Permission denied"**: Ensure the service account has access to the Google Chat space
- **"requests library not installed"**: Run `pip install requests`

## Resources

### scripts/new_message.py

Python script that handles sending new messages to Google Chat. Supports both plain text and formatted messages.

### scripts/reply_message.py

Python script that handles replying to existing threads in Google Chat. Takes a thread name parameter and sends a reply to that specific thread. Supports both plain text and formatted messages.

### references/message_formatting.md

Comprehensive guide to Google Chat message formatting options, including examples of bold, italic, links, lists, emoji, code blocks, and message templates for common scenarios (status updates, error alerts, build notifications).
