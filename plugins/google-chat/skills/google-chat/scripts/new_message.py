#!/usr/bin/env python3
"""
Google Chat Message Sender

Sends messages to Google Chat spaces using service account authentication.
Supports basic text formatting (bold, italic, links, etc.)

Usage:
    python send_message.py --message "Your message here"
    python send_message.py --message "Task completed" --formatted
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


def send_message(space_id, api_key, api_token, message_text, formatted=False):
    """
    Send a message to Google Chat space.

    Args:
        space_id: The Google Chat space ID
        message_text: The message text to send
        formatted: Whether to use formatted text (supports markdown-like syntax)

    Returns:
        Response from Google Chat API
    """
    url = f"https://chat.googleapis.com/v1/spaces/{space_id}/messages?key={api_key}&token={api_token}"

    # Build message payload
    if formatted:
        # Use formatted text with basic formatting support
        payload = {
            "text": message_text,
            "formattedText": message_text,
        }
    else:
        # Plain text message
        payload = {
            "text": message_text,
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
    parser = argparse.ArgumentParser(description="Send messages to Google Chat")
    parser.add_argument("--message", "-m", required=True, help="Message text to send")
    parser.add_argument(
        "--formatted",
        "-f",
        action="store_true",
        help="Enable formatted text (bold, italic, links)",
    )
    parser.add_argument("--space-id", help="Space ID to send the message")

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    api_key = config["key"]

    # Use command line args
    space_id = args.space_id

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

    if not space_id:
        print("Error: Space ID not configured")
        sys.exit(1)

    if not api_key:
        print(
            "Error: Credentials path not configured. Set GOOGLE_CHAT_API_KEY or add to config.json"
        )
        sys.exit(1)

    try:
        # Send message
        result = send_message(
            space_id, api_key, api_token, args.message, args.formatted
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
