#!/bin/bash

# Jira Ticket Summary Extractor
# Usage: ./get-ticket-summary.sh TICKET-ID [--full]
# Example: ./get-ticket-summary.sh PROJ-40859
# Example: ./get-ticket-summary.sh PROJ-40859 --full (includes description)

set -e

TICKET_ID=$1
SHOW_FULL=${2:-""}

if [ -z "$TICKET_ID" ]; then
    echo "Usage: $0 TICKET-ID [--full]"
    echo "Example: $0 PROJ-40859"
    echo "Example: $0 PROJ-40859 --full"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed."
    echo "Install: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

TEMP_FILE="/tmp/jira-${TICKET_ID}.json"

npx jira-api-cli get-issue "{\"issueIdOrKey\":\"${TICKET_ID}\"}" > "$TEMP_FILE"

echo "# Ticket Summary"
echo ""

# Extract core fields
cat "$TEMP_FILE" | jq -r '
  "- Key: " + .key,
  "- Summary: " + .fields.summary,
  "- Type: " + .fields.issuetype.name,
  "- Status: " + .fields.status.name,
  "- Priority: " + (.fields.priority.name // "None"),
  "- Assignee: " + (.fields.assignee.displayName // "Unassigned"),
  "- Reporter: " + (.fields.reporter.displayName // "Unknown"),
  "- Created: " + .fields.created,
  "- Updated: " + .fields.updated,
  "- Labels: " + (.fields.labels | join(", "))
'

# Parent ticket if exists
PARENT=$(cat "$TEMP_FILE" | jq -r 'if .fields.parent then "- Parent: " + .fields.parent.key + " - " + .fields.parent.fields.summary else empty end')
if [ -n "$PARENT" ]; then
    echo "$PARENT"
fi

# Time tracking
cat "$TEMP_FILE" | jq -r '
  if .fields.timeoriginalestimate then
    "- Original Estimate: " + (.fields.timeoriginalestimate / 3600 | tostring) + "h"
  else empty end,
  if .fields.timespent then
    "- Time Spent: " + (.fields.timespent / 3600 | tostring) + "h"
  else empty end,
  if .fields.timeremaining then
    "- Remaining: " + (.fields.timeremaining / 3600 | tostring) + "h"
  else empty end,
  if .fields.progress.percent then
    "- Progress: " + (.fields.progress.percent | tostring) + "%"
  else empty end
'

# Sprint info if exists
SPRINT=$(cat "$TEMP_FILE" | jq -r 'if .fields.customfield_10020 then .fields.customfield_10020[0].name else empty end')
if [ -n "$SPRINT" ]; then
    echo "- Sprint: $SPRINT"
fi

# Issue links
ISSUE_LINKS=$(cat "$TEMP_FILE" | jq -r 'if .fields.issuelinks | length > 0 then "\n# Related Issues:" else empty end')
if [ -n "$ISSUE_LINKS" ]; then
    echo "$ISSUE_LINKS"
    cat "$TEMP_FILE" | jq -r '.fields.issuelinks[] |
      "- " + (.type.inward // .type.outward) + ": " +
      ((.inwardIssue.key // .outwardIssue.key) + " - " +
      (.inwardIssue.fields.summary // .outwardIssue.fields.summary))'
fi

# Description if --full flag is provided
if [ "$SHOW_FULL" == "--full" ]; then
    echo ""
    echo "# Description"

    cat "$TEMP_FILE" | jq -r '
        def extract_text:
            if .type == "text" then .text
            elif .type == "inlineCard" then .attrs.url
            elif .type == "mention" then .attrs.text
            else empty
            end;

        def process_paragraph:
            if .content then
                [.content[] | extract_text] | join("")
            else ""
            end;

        def process_list_item($prefix):
            if .content then
                .content[] |
                if .type == "paragraph" then
                    $prefix + (process_paragraph)
                elif .type == "orderedList" or .type == "bulletList" then
                    .content[] | process_list_item("  " + $prefix)
                elif .type == "codeBlock" then
                    "\n```\n" + ([.content[]? | extract_text] | join("")) + "\n```"
                else ""
                end
            else ""
            end;

        def repeat_hash($level):
            if $level == 1 then "#"
            elif $level == 2 then "##"
            elif $level == 3 then "###"
            elif $level == 4 then "####"
            elif $level == 5 then "#####"
            elif $level == 6 then "######"
            else "###"
            end;

        .fields.description.content[]? |
        if .type == "heading" then
            "\n" + repeat_hash(.attrs.level) + " " + ([.content[]? | extract_text] | join(""))
        elif .type == "paragraph" then
            process_paragraph
        elif .type == "orderedList" or .type == "bulletList" then
            .content[] | process_list_item("- ")
        elif .type == "codeBlock" then
            "\n```\n" + ([.content[]? | extract_text] | join("")) + "\n```"
        else
            process_paragraph
        end
    ' 2>/dev/null | grep -v "^$\|^null$" || echo "No description available"

    # Recent comments
    echo ""
    echo "# Recent Comments (Last 5)"
    cat "$TEMP_FILE" | jq -r '.fields.comment.comments[-5:] | .[] |
      "- " + .author.displayName + ": " + .created + ":" +
      (if .body.content then
        "\n  -" + (
          [ .body.content[]? |
          if .type == "paragraph" then (
            [ .content[]? |
              if .type == "inlineCard" then (.attrs.url // "")
              else (.text // "")
              end
            ] | join("")
          )
            elif .type == "orderedList" or .type == "bulletList" then
              (.content[]? | "  - " + (if .content then (.content[]?.content[]?.text // "") else "" end))
            else (.content[]?.text // "")
            end
          ] | join("")
        )
      else "No text" end)' 2>/dev/null | grep -v "^$\|^null$" || echo "No comments available"

    # Work logs
    WORKLOG_COUNT=$(cat "$TEMP_FILE" | jq -r '.fields.worklog.total // 0')
    if [ "$WORKLOG_COUNT" -gt 0 ]; then
        echo ""
        echo "# Work Logs"
        cat "$TEMP_FILE" | jq -r '.fields.worklog.worklogs[] |
          "- " + .author.displayName + ": " + .started + " - " + .timeSpent' 2>/dev/null
    fi
fi

# Clean up
rm "$TEMP_FILE"
echo ""
echo "Temp file cleaned up: $TEMP_FILE"
