# Google Chat Message Formatting Reference

This document provides examples of text formatting options available in Google Chat messages.

## Basic Text Formatting

Google Chat supports basic text formatting using simple markup:

### Bold
```
*bold text*
```
Example: `*Important:* Task completed` → **Important:** Task completed

### Italic
```
_italic text_
```
Example: `_Note:_ Check the logs` → _Note:_ Check the logs

### Strikethrough
```
~strikethrough text~
```
Example: `~Old approach~ New approach` → ~~Old approach~~ New approach

### Monospace (Code)
```
`monospace text`
```
Example: `` Run `npm install` to continue`` → Run `npm install` to continue

### Code Block
````
```
code block
multiple lines
```
````

## Links

### Inline Links
```
<https://example.com|Link Text>
```
Example: `<https://github.com/user/repo|View PR>` → [View PR](https://github.com/user/repo)

### Auto-linking URLs
URLs are automatically converted to links:
```
Visit https://example.com for details
```

## Lists

### Bullet Lists
```
• Item 1
• Item 2
• Item 3
```

### Numbered Lists
```
1. First item
2. Second item
3. Third item
```

## Line Breaks

Use `\n` for line breaks in your message text.

## User Mentions

Mention users in messages:
```
<users/USER_ID>
```
Example: `Hey <users/123456789>, the build is ready`

## Common Message Templates

### Status Update
```
*Status Update*

Task: Deploy feature X
Status: ✅ Completed
Duration: 15 minutes

Details:
• All tests passed
• Deployed to production
• Monitoring active
```

### Error Alert
```
⚠️ *Alert: Error Detected*

Service: API Gateway
Error: Connection timeout
Time: 2025-01-22 14:30:00

Action required: Please investigate
```

### Build Notification
```
🚀 *Build Complete*

Branch: `feature/new-dashboard`
Result: ✅ Success
Tests: 45/45 passed
Coverage: 87%

<https://ci.example.com/build/123|View Build Details>
```

### Task Completion
```
✅ *Task Completed*

`Fix user authentication bug`

Changes:
• Updated token validation
• Added error handling
• Deployed to staging

Ready for review!
```

## Emoji Support

Google Chat supports standard emoji:
- ✅ Checkmark
- ⚠️ Warning
- 🚀 Rocket
- 💡 Light bulb
- 📊 Chart
- 🔧 Wrench
- 🐛 Bug

## Character Limits

- Maximum message length: 4,096 characters
- For longer content, consider splitting into multiple messages or using cards

## Best Practices

1. **Use formatting sparingly** - Bold for emphasis, code blocks for technical details
2. **Include context** - Who, what, when, why
3. **Add visual indicators** - Emoji for status (✅/⚠️)
4. **Structure information** - Use lists and line breaks for readability
5. **Link to details** - Provide URLs for more information
