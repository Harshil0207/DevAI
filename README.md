# devai

Offline coding assistant for the terminal. Answers questions about C, C++, Java,
Kotlin, Swift, JavaScript, TypeScript, React, React Native, Node.js, Python, Go,
Rust, PHP, SQL, Bash, Git and Docker.

Everything runs locally through [Ollama](https://ollama.com). **No internet, no API
key, no data leaves the machine.**

## Requirements

- macOS (Apple Silicon recommended)
- Ollama
- Python 3.9+

## Install

```bash
brew install ollama
brew services start ollama
ollama pull qwen2.5-coder:7b

cd ~/devai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Add the shortcut to your shell so you can type `devai` anywhere:

```bash
echo 'alias devai="$HOME/devai/devai-run"' >> ~/.zshrc
source ~/.zshrc
```

## Usage

Just type `devai` and ask:

```bash
devai                      # opens an interactive session, type questions
devai "why is my useEffect running twice?"   # one-shot question
```

No subcommand needed — anything that isn't a known command is treated as a
question, and bare `devai` drops into chat.

## Commands

| Command | What it does |
|---|---|
| `devai` | Interactive session (same as `devai chat`) |
| `devai "..."` | One-shot question (same as `devai ask "..."`) |
| `devai ask "..."` | Any programming or IT question |
| `devai explain <file>` | Explain what code does |
| `devai fix <file>` | Find bugs and return corrected code |
| `devai review <file>` | Review for correctness, security, performance |
| `devai generate "..."` | Generate code from a description |
| `devai chat` | Interactive session that remembers context |
| `devai models` | List installed local models |
| `devai setup` | Show or change settings |

## Examples

```bash
devai "What is a closure in JavaScript?"
devai "Difference between useEffect and useLayoutEffect in React Native"

devai explain src/screens/FeedScreen.js
devai fix src/utils/parser.js
devai review src/api/client.js

devai generate --lang java "a thread-safe LRU cache"
devai generate --lang cpp "binary search tree with insert and delete"

devai          # or: devai chat
```

Inside the session:

```
/clear           forget the conversation so far
/model <name>    switch model mid-session
/models          list installed models
exit             quit (Ctrl-D also works)
```

Multi-line pastes are kept together — paste a whole question, error log or
snippet and it is sent as a single message, not one line at a time.

Code can also be piped in:

```bash
cat main.c | devai review
git diff | devai ask "Any bugs in this diff?"
pbpaste | devai explain
```

## Options

```
--model, -m   Use a different model for one run
--raw,   -r   Plain text output instead of rendered markdown
--lang,  -l   Target language (generate only)
```

## Settings

```bash
devai setup                              # show current config
devai setup --model qwen2.5-coder:14b    # change default model
devai setup --num-ctx 16384              # larger context window
```

Stored in `~/.devai/config.json`. `DEVAI_MODEL` and `OLLAMA_HOST` environment
variables override it.

## Models

| Model | Disk | RAM | Notes |
|---|---|---|---|
| `qwen2.5-coder:3b` | ~1.9 GB | ~3 GB | Fast, weaker on hard problems |
| `qwen2.5-coder:7b` | ~4.7 GB | ~6 GB | Default. Best balance for 16 GB Macs |
| `qwen2.5-coder:14b` | ~9 GB | ~11 GB | Best quality, tight on 16 GB |

Swap any time:

```bash
ollama pull qwen2.5-coder:3b
devai setup --model qwen2.5-coder:3b
```

## Troubleshooting

**"Cannot reach the local Ollama server"**

```bash
brew services start ollama     # or: ollama serve
```

**"Model is not installed"**

```bash
ollama pull qwen2.5-coder:7b
devai models
```

**Slow replies** — a smaller model helps, and closing other memory-heavy apps
matters a lot on 16 GB. Check what is using memory with `ollama ps`.
