#!/usr/bin/env python3
"""Simulate human-like typing with realistic timing delays."""

import sys
import time
import random

PUNCTUATION_PAUSE = {'-', '_', '/', '=', '"'}
BASE_DELAY_MIN = 0.040   # 40 ms
BASE_DELAY_MAX = 0.110   # 110 ms
THINK_PROBABILITY = 0.03  # 3% chance per character
THINK_DELAY_MIN = 0.200  # 200 ms
THINK_DELAY_MAX = 0.500  # 500 ms
ENTER_PRE_PAUSE  = (0.100, 0.300)
ENTER_POST_PAUSE = (0.050, 0.150)


def type_human(text: str) -> None:
    for ch in text:
        if ch == '\n':
            time.sleep(random.uniform(*ENTER_PRE_PAUSE))
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(random.uniform(*ENTER_POST_PAUSE))
            continue

        # Occasional mid-word thinking pause (before the character)
        if random.random() < THINK_PROBABILITY:
            time.sleep(random.uniform(THINK_DELAY_MIN, THINK_DELAY_MAX))

        sys.stdout.write(ch)
        sys.stdout.flush()

        delay = random.uniform(BASE_DELAY_MIN, BASE_DELAY_MAX)
        if ch in PUNCTUATION_PAUSE:
            delay *= random.uniform(1.8, 3.0)   # noticeably longer on punctuation
        time.sleep(delay)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Text passed as a command-line argument
        type_human(' '.join(sys.argv[1:]) + '\n')
    else:
        # Read from stdin (pipe mode)
        type_human(sys.stdin.read())
