---
name: Terminal Recorder
description: This skill should be used when the user wants to record a terminal session and convert it to an animated GIF. Use when the user says phrases like "record my terminal", "capture terminal session", "create a terminal GIF", "record a demo", "make a terminal recording", "convert cast to GIF", or needs to produce shareable terminal demos.
allowed-tools: Read, Write, Execute, Bash(asciinema rec:*), Bash(agg:*), Bash(python3:*), Bash(gifsicle:*)
---

# Terminal Recorder

Record terminal sessions and convert them to animated GIF files using **asciinema** (for recording) and **agg** (for GIF conversion). Perfect for creating documentation demos, tutorials, and shareable terminal walkthroughs.

## When to Use This Skill

Invoke when:

- User asks to "record my terminal" or "capture a terminal session"
- User wants to "create a terminal GIF" or "make an animated demo"
- User needs to "record a demo" for documentation or sharing
- User wants to convert an existing `.cast` file to a GIF
- User mentions asciinema, agg, or terminal recording workflows

## Prerequisites

### 1. Install asciinema

**macOS:**

```bash
brew install asciinema
```

**Ubuntu/Debian:**

```bash
sudo apt install asciinema
```

**Arch Linux:**

```bash
sudo pacman -S asciinema
```

**Fedora:**

```bash
sudo dnf install asciinema
```

**Via Cargo (latest v3.x from source):**

```bash
cargo install --locked --git https://github.com/asciinema/asciinema
```

Verify installation:

```bash
asciinema --version
```

### 2. Install agg (asciinema GIF generator)

**Via Cargo:**

```bash
cargo install --git https://github.com/asciinema/agg
```

**Prebuilt binaries** (no Rust required):
Download from https://github.com/asciinema/agg/releases/latest for your platform (x86_64, aarch64/Apple Silicon, arm), then:

```bash
chmod a+x agg
sudo mv agg /usr/local/bin
```

**Via Docker:**

```bash
docker build -t agg https://github.com/asciinema/agg.git
```

Verify installation:

```bash
agg --version
```

### 3. (Optional) Install gifsicle for GIF optimization

```bash
brew install gifsicle        # macOS
sudo apt install gifsicle    # Ubuntu/Debian
```

## Usage

### Full Workflow: Record and Convert to GIF

#### Step 1 — Record a terminal session

```bash
asciinema rec --output-format asciicast-v2 demo.cast
```

- Perform the terminal actions you want to capture
- Press `ctrl+d` or type `exit` to stop recording
- The session is saved to `demo.cast` (asciicast v2 format)
- **`--output-format asciicast-v2` is required** — asciinema 3.x defaults to v3, which `agg` does not yet support

#### Step 2 — Convert the recording to GIF

```bash
agg demo.cast demo.gif
```

The GIF is generated at `demo.gif` with default settings (Dracula theme, 14px font).

---

### Recording Options

**Specify output file:**

```bash
asciinema rec --output-format asciicast-v2 my-session.cast
```

**Record with a title:**

```bash
asciinema rec --output-format asciicast-v2 --title "My Demo" demo.cast
```

**Set max idle time between keystrokes** (useful to trim long pauses):

```bash
asciinema rec --output-format asciicast-v2 --idle-time-limit 2 demo.cast
```

**Append to an existing recording:**

```bash
asciinema rec --output-format asciicast-v2 --append demo.cast
```

**Overwrite existing file:**

```bash
asciinema rec --output-format asciicast-v2 --overwrite demo.cast
```

**Set terminal dimensions:**

```bash
asciinema rec --output-format asciicast-v2 --cols 120 --rows 30 demo.cast
```

**Capture stdin (keyboard input) as well:**

```bash
asciinema rec --output-format asciicast-v2 --stdin demo.cast
```

---

### GIF Conversion Options

**Basic conversion:**

```bash
agg demo.cast demo.gif
```

**Change theme:**

```bash
agg --theme monokai demo.cast demo.gif
# Available: asciinema, dracula (default), monokai, solarized-dark, solarized-light
```

**Custom theme via hex colors** (background, foreground text, 8 standard colors, optionally 8 bright colors):

```bash
agg --theme "1e1e2e,cdd6f4,45475a,f38ba8,a6e3a1,f9e2af,89b4fa,f5c2e7,bac2de,f38ba8,a6e3a1,f9e2af,89b4fa,f5c2e7,94e2d5,a6adc8" demo.cast demo.gif
```

**Change font size:**

```bash
agg --font-size 16 demo.cast demo.gif
```

**Specify font family:**

```bash
agg --font-family "JetBrains Mono,Fira Code" demo.cast demo.gif
```

**Point to custom font directory:**

```bash
agg --font-dir ~/.fonts demo.cast demo.gif
```

**Adjust playback speed:**

```bash
agg --speed 1.5 demo.cast demo.gif   # 1.5x faster
agg --speed 0.5 demo.cast demo.gif   # half speed
```

**Verbose output** (useful for debugging font selection):

```bash
agg -v demo.cast demo.gif
```

**Use a remote asciinema.org recording:**

```bash
agg https://asciinema.org/a/569727 demo.gif
```

---

### Simulating Human-Like Typing

Use the `scripts/type-human.py` script to replay text into the terminal with realistic timing — random per-character delays, longer pauses on punctuation, occasional mid-word "thinking" pauses, and natural hesitation around Enter.

**Usage inside a recording session:**

```bash
# Start recording
asciinema rec --output-format asciicast-v2 demo.cast

# Type a single command with human-like timing
python3 scripts/type-human.py "git diff --stat HEAD~1"

# Or pipe multi-line input
printf 'ls -la\ncd src\ncat README.md\n' | python3 scripts/type-human.py

# Stop recording
exit
```

**Embed into a self-contained demo script:**

```bash
#!/usr/bin/env bash
# demo-script.sh — run inside asciinema rec demo.cast
type() { python3 scripts/type-human.py "$*"; }

type "echo 'Hello, world!'"
eval "echo 'Hello, world!'"
sleep 1

type "git log --oneline -5"
eval "git log --oneline -5"
sleep 1
```

```bash
asciinema rec --output-format asciicast-v2 --idle-time-limit 2 --command "bash demo-script.sh" demo.cast
```

> **Note:** `type-human.py` writes directly to stdout — it does **not** execute the command. Pair each `type` call with an `eval` (or just press Enter manually) to actually run the typed command.

---

### GIF Optimization (reduce file size)

After generating the GIF, use gifsicle to optimize:

```bash
gifsicle --lossy=80 -k 128 -O2 -Okeep-empty demo.gif -o demo-optimized.gif
```

Options:

- `--lossy=80` — lossy compression (0–200, higher = smaller but lower quality)
- `-k 128` — reduce color palette to 128 colors
- `-O2` — optimization level 2
- `-Okeep-empty` — preserve empty frames (important for timing accuracy)

---

### Common Workflows

#### Quick demo for a README

```bash
# Record
asciinema rec --output-format asciicast-v2 --idle-time-limit 2 --cols 100 --rows 28 demo.cast

# Convert with a clean theme
agg --theme monokai --font-size 14 demo.cast demo.gif

# Optimize
gifsicle --lossy=80 -k 128 -O2 -Okeep-empty demo.gif -o demo.gif
```

Then embed in your README:

```markdown
![Demo](demo.gif)
```

#### Convert an existing asciinema.org recording

```bash
agg https://asciinema.org/a/<id> output.gif
```

#### High-quality recording with custom font

```bash
asciinema rec --output-format asciicast-v2 --idle-time-limit 3 session.cast
agg --font-family "JetBrains Mono" --font-size 15 --theme dracula session.cast session.gif
```

---

## Tips

- **Idle time limit** (`--idle-time-limit`) is highly recommended during recording — it automatically trims long pauses so the GIF doesn't drag.
- **Terminal size** matters: set `--cols` and `--rows` during recording so the GIF dimensions are predictable.
- The `.cast` file is plain JSON (asciicast v2 format) — you can inspect or edit it with any text editor.
- `agg` reads the terminal dimensions from the `.cast` file, so GIF width/height is determined at record time.
- For emoji support in GIFs, install Noto Color Emoji fonts.
- The `ASCIINEMA_SESSION` environment variable is set during recording — useful for customizing your shell prompt to indicate a recording is in progress.

## Troubleshooting

| Issue                      | Fix                                                                  |
| -------------------------- | -------------------------------------------------------------------- |
| `agg` not found            | Ensure `~/.cargo/bin` is in your `$PATH` after installing via Cargo  |
| GIF has wrong fonts        | Use `agg -v` to see which fonts are being selected                   |
| Recording captures nothing | Ensure your shell is supported (bash, zsh, fish)                     |
| GIF file is too large      | Use gifsicle to optimize; also try `--speed 1.5` to shorten duration |
| Blank/empty GIF            | Check that the `.cast` file has content with `cat demo.cast`         |
