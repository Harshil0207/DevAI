import os
import select
import sys
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import config, prompts
from .engine import EngineError, console, installed_models, stream_chat

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="devai — offline coding assistant. Runs fully local via Ollama.",
)

err = Console(stderr=True)

MAX_FILE_BYTES = 200_000


def _fail(message: str) -> None:
    err.print(Panel(message, title="devai", border_style="red"))
    raise typer.Exit(code=1)


def _read_stdin() -> str:
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def _load_source(target: str) -> str:
    """Return a prompt block for `target`, which may be a file path or raw code."""
    if target and os.path.isfile(target):
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read(MAX_FILE_BYTES)
        except OSError as exc:
            _fail("Could not read {0}: {1}".format(target, exc))
        lang = prompts.language_for(target)
        tag = prompts.highlight_for(target)
        header = "File: {0}".format(target)
        if lang:
            header += "\nLanguage: {0}".format(lang)
        return "{0}\n\n```{1}\n{2}\n```".format(header, tag, body)
    return "```\n{0}\n```".format(target)


def _resolve_input(target: Optional[str], what: str) -> str:
    piped = _read_stdin()
    if target:
        return _load_source(target)
    if piped.strip():
        return "```\n{0}\n```".format(piped)
    _fail(
        "Nothing to {0}. Pass a file path or pipe code in.\n\n"
        "  devai {0} src/App.js\n"
        "  cat src/App.js | devai {0}".format(what)
    )
    return ""


def _run(system: str, user: str, model: Optional[str], raw: bool) -> None:
    try:
        stream_chat(system, user, model=model, raw=raw)
    except EngineError as exc:
        _fail(str(exc))
    except KeyboardInterrupt:
        err.print("\n[dim]stopped[/dim]")
        raise typer.Exit(code=130)


ModelOpt = typer.Option(None, "--model", "-m", help="Override the model for this run.")
RawOpt = typer.Option(False, "--raw", "-r", help="Plain text output, no markdown rendering.")


@app.command()
def ask(
    question: List[str] = typer.Argument(..., help="Your question."),
    model: Optional[str] = ModelOpt,
    raw: bool = RawOpt,
):
    """Ask any programming or IT question."""
    text = " ".join(question)
    piped = _read_stdin()
    if piped.strip():
        text += "\n\nContext:\n```\n{0}\n```".format(piped)
    _run(prompts.ASK, text, model, raw)


@app.command()
def explain(
    target: Optional[str] = typer.Argument(None, help="File path, or raw code."),
    model: Optional[str] = ModelOpt,
    raw: bool = RawOpt,
):
    """Explain what a file or snippet does."""
    _run(prompts.EXPLAIN, _resolve_input(target, "explain"), model, raw)


@app.command()
def fix(
    target: Optional[str] = typer.Argument(None, help="File path, or raw code."),
    model: Optional[str] = ModelOpt,
    raw: bool = RawOpt,
):
    """Find bugs and return corrected code."""
    _run(prompts.FIX, _resolve_input(target, "fix"), model, raw)


@app.command()
def review(
    target: Optional[str] = typer.Argument(None, help="File path, or raw code."),
    model: Optional[str] = ModelOpt,
    raw: bool = RawOpt,
):
    """Review code for correctness, security and performance."""
    _run(prompts.REVIEW, _resolve_input(target, "review"), model, raw)


@app.command()
def generate(
    description: List[str] = typer.Argument(..., help="What to build."),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Target language."),
    model: Optional[str] = ModelOpt,
    raw: bool = RawOpt,
):
    """Generate code from a description."""
    text = " ".join(description)
    if lang:
        text = "Language: {0}\n\n{1}".format(lang, text)
    _run(prompts.GENERATE, text, model, raw)


def _drain_pending(first_wait: float = 0.15) -> str:
    """Collect lines already sitting in the input buffer.

    A multi-line paste hits the terminal as one burst, but input() hands back
    only the first line \u2014 the rest would each be submitted as their own
    question. Grab them here so one paste stays one question.
    """
    if not sys.stdin.isatty():
        return ""
    extra = []
    wait = first_wait
    while True:
        try:
            ready = select.select([sys.stdin], [], [], wait)[0]
        except (OSError, ValueError):
            break
        if not ready:
            break
        line = sys.stdin.readline()
        if not line:
            break
        extra.append(line.rstrip("\n"))
        wait = 0.05
    return "\n".join(extra)


def _read_prompt() -> str:
    """Read one question, keeping a pasted multi-line block together."""
    line = console.input("\n[bold cyan]you \u203a[/bold cyan] ")
    rest = _drain_pending()
    if rest:
        line = line + "\n" + rest
        n = rest.count("\n") + 2
        console.print(
            "[dim]({0} lines pasted \u2014 sent as one question)[/dim]".format(n)
        )
    return line.strip()


@app.command()
def chat(model: Optional[str] = ModelOpt):
    """Interactive session that remembers the conversation."""
    cfg = config.load()
    active = model or cfg["model"]
    console.print(
        Panel(
            "Ask anything about code. Answers stream in, and the session "
            "remembers what you already said.\n\n"
            "[dim]/clear[/dim]  forget the conversation      "
            "[dim]/model <name>[/dim]  switch model\n"
            "[dim]/models[/dim] list installed models        "
            "[dim]exit[/dim]  or Ctrl-D to quit",
            title="devai · [bold]{0}[/bold]".format(active),
            border_style="cyan",
        )
    )
    history: List[Dict[str, str]] = []
    while True:
        try:
            line = _read_prompt()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            return
        if not line:
            continue
        if line.lower() in {"exit", "quit", ":q"}:
            console.print("[dim]bye[/dim]")
            return
        if line.lower() in {"/clear", "/reset"}:
            history.clear()
            console.print("[dim]context cleared[/dim]")
            continue
        if line.lower() == "/models":
            try:
                for name in installed_models():
                    mark = "✓" if name == active else " "
                    console.print("  {0} {1}".format(mark, name))
            except EngineError as exc:
                console.print("[red]{0}[/red]".format(exc))
            continue
        if line.lower().startswith("/model"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                active = parts[1].strip()
                history.clear()
                console.print("[dim]model → {0} (context cleared)[/dim]".format(active))
            else:
                console.print("[dim]model: {0}[/dim]".format(active))
            continue
        console.print()
        try:
            reply = stream_chat(prompts.ASK, line, model=active, history=history)
        except EngineError as exc:
            console.print(Panel(str(exc), title="devai", border_style="red"))
            continue
        except KeyboardInterrupt:
            _drain_pending(0.05)
            console.print("\n[dim]stopped[/dim]")
            continue
        history.append({"role": "user", "content": line})
        history.append({"role": "assistant", "content": reply})
        del history[:-12]


@app.command()
def models():
    """List locally installed models."""
    try:
        names = installed_models()
    except EngineError as exc:
        _fail(str(exc))
    cfg = config.load()
    table = Table(title="Installed models (offline)")
    table.add_column("Model")
    table.add_column("Default", justify="center")
    for name in names:
        table.add_row(name, "✓" if name == cfg["model"] else "")
    console.print(table)
    if not names:
        console.print("[yellow]None. Run: ollama pull qwen2.5-coder:7b[/yellow]")


@app.command()
def setup(
    model: Optional[str] = typer.Option(None, "--model", help="Set the default model."),
    temperature: Optional[float] = typer.Option(None, "--temperature"),
    num_ctx: Optional[int] = typer.Option(None, "--num-ctx", help="Context window size."),
):
    """Show or change devai settings."""
    changed = any(v is not None for v in (model, temperature, num_ctx))
    cfg = (
        config.save(model=model, temperature=temperature, num_ctx=num_ctx)
        if changed
        else config.load()
    )
    table = Table(title="devai config")
    table.add_column("Key")
    table.add_column("Value")
    for key in ("model", "host", "temperature", "num_ctx"):
        table.add_row(key, str(cfg.get(key)))
    console.print(table)
    console.print("[dim]{0}[/dim]".format(config.CONFIG_PATH))


_COMMANDS = {"ask", "explain", "fix", "review", "generate", "chat", "models", "setup"}
_GROUP_FLAGS = {"--help", "-h"}


def main() -> None:
    """Entry point.

    Routing so the common cases need no subcommand:
      devai                     -> interactive chat
      devai <anything else>     -> ask
      devai <known command> ... -> that command, unchanged
    """
    argv = sys.argv[1:]
    if not argv:
        if sys.stdin.isatty():
            sys.argv.insert(1, "chat")
    elif argv[0] not in _COMMANDS and argv[0] not in _GROUP_FLAGS:
        sys.argv.insert(1, "ask")
    app(prog_name="devai")
