#!/usr/bin/env python3
"""
Reply to existing thread in Google Chat

Usage:
    python reply_message.py --thread-name "spaces/AAQAKA6hsFw/threads/D1NI3W2B6vA" --message "Your message here"
    python reply_message.py --thread-name "spaces/AAQAKA6hsFw/threads/D1NI3W2B6vA" --message "Task completed" --formatted
"""

import argparse
import json
import sys
from pathlib import Path

from jsonc import JsonC

try:
    import requests  # type: ignore[reportMissingModuleSource]
except ImportError:
    print("Error: requests library not installed. Run: pip install requests")
    sys.exit(1)


def load_config():
    """Load configuration from environment or config file."""
    config_path = Path(__file__).parent.parent / "config.jsonc"

    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f, cls=JsonC)
    else:
        config = {}

    return config


def reply_message(
    thread_name, space_id, api_key, api_token, message_text, formatted=False
):
    """
    Send a message to existing thread.

    Args:
        thread_name: The Google Chat thread name
        message_text: The message text to send
        formatted: Whether to use formatted text (supports markdown-like syntax)

    Returns:
        Response from Google Chat API
    """

    url = f"https://chat.googleapis.com/v1/spaces/{space_id}/messages?key={api_key}&token={api_token}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"

    # Build message payload
    if formatted:
        # Use formatted text with basic formatting support
        payload = {
            "text": message_text,
            "formattedText": message_text,
            "thread": {"name": f"{thread_name}"},
        }
    else:
        # Plain text message
        payload = {
            "text": message_text,
            "thread": {"name": f"{thread_name}"},
        }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        return {
            "success": False,
            "error": response.text,
            "status_code": response.status_code,
        }


def main():
    parser = argparse.ArgumentParser(description="Reply messages to Google Chat")
    parser.add_argument("--message", "-m", required=True, help="Message text to send")
    parser.add_argument(
        "--formatted",
        "-f",
        action="store_true",
        help="Enable formatted text (bold, italic, links)",
    )
    parser.add_argument("--thread-name", help="Thread name to send the message")

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    api_key = config["key"]

    # parse space and thread from thread-name, e.g.: spaces/AAQAKA6hsFw/threads/D1NI3W2B6vA
    space_id = None
    parts = args.thread_name.strip().split("/")
    if len(parts) >= 2 and parts[0] == "spaces":
        space_id = parts[1]

    api_token = None
    tokens = config.get("tokens")
    if isinstance(tokens, dict):
        api_token = tokens.get(space_id)

    if not space_id:
        print("Error: Space ID not available")
        sys.exit(1)

    if not api_key:
        print("Error: API key is missing in config.jsonc")
        sys.exit(1)

    if not api_token:
        print("Error: API token is not found config.jsonc")
        sys.exit(1)

    try:
        result = reply_message(
            args.thread_name, space_id, api_key, api_token, args.message, args.formatted
        )

        if result["success"]:
            print("Message sent successfully!")
            print(f"Thread: {result['data'].get('name', 'N/A')}")
        else:
            print("Failed to send message")
            print(f"Status code: {result['status_code']}")
            print(f"Error: {result['error']}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
