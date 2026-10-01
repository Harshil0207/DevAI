import sys
from typing import Dict, Iterable, List, Optional

from rich.console import Console
from rich.markdown import Markdown

from . import config

console = Console()


class EngineError(Exception):
    pass


def _client():
    try:
        import ollama
    except ImportError as exc:
        raise EngineError(
            "The 'ollama' python package is missing. Run: pip install ollama"
        ) from exc
    cfg = config.load()
    return ollama.Client(host=cfg["host"]), cfg


def installed_models() -> List[str]:
    client, _ = _client()
    try:
        data = client.list()
    except Exception as exc:
        raise EngineError(_connection_hint(exc)) from exc
    names = []
    for item in getattr(data, "models", None) or data.get("models", []):
        name = getattr(item, "model", None) or (
            item.get("model") if isinstance(item, dict) else None
        )
        if name:
            names.append(name)
    return names


def _connection_hint(exc: Exception) -> str:
    return (
        "Cannot reach the local Ollama server.\n"
        "  Start it with:  brew services start ollama\n"
        "  Or run:         ollama serve\n"
        "Underlying error: {0}".format(exc)
    )


def _ensure_model(client, model: str) -> None:
    try:
        available = installed_models()
    except EngineError:
        raise
    if not available:
        raise EngineError(
            "No models installed. Run:  ollama pull {0}".format(model)
        )
    if model in available:
        return
    base = model.split(":")[0]
    for name in available:
        if name.split(":")[0] == base:
            return
    raise EngineError(
        "Model '{0}' is not installed.\n  Install it:  ollama pull {1}\n"
        "  Installed:   {2}".format(model, model, ", ".join(available))
    )


def stream_chat(
    system: str,
    user: str,
    model: Optional[str] = None,
    raw: bool = False,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    client, cfg = _client()
    model = model or cfg["model"]
    _ensure_model(client, model)

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user})

    options = {
        "temperature": cfg.get("temperature", 0.2),
        "num_ctx": cfg.get("num_ctx", 8192),
    }

    try:
        chunks: Iterable = client.chat(
            model=model, messages=messages, stream=True, options=options
        )
    except Exception as exc:
        raise EngineError(_connection_hint(exc)) from exc

    parts: List[str] = []
    if raw or not sys.stdout.isatty():
        for chunk in chunks:
            piece = _chunk_text(chunk)
            if piece:
                parts.append(piece)
                sys.stdout.write(piece)
                sys.stdout.flush()
        sys.stdout.write("\n")
        return "".join(parts)

    # Render progressively, one COMPLETE markdown block at a time. Printing
    # finished blocks permanently (instead of re-rendering the whole answer on
    # every token, which floods the scrollback once the answer is taller than
    # the terminal) keeps output readable top to bottom.
    buf = ""
    started = False
    status = console.status("[dim]thinking\u2026[/dim]", spinner="dots")
    status.start()
    try:
        for chunk in chunks:
            piece = _chunk_text(chunk)
            if not piece:
                continue
            parts.append(piece)
            buf += piece
            ready, buf = _split_blocks(buf)
            if ready.strip():
                if not started:
                    status.stop()
                    started = True
                console.print(Markdown(ready))
    finally:
        if not started:
            status.stop()
    if buf.strip():
        console.print(Markdown(buf))
    return "".join(parts)


FENCE = "```"


def _split_blocks(buf: str):
    """Split `buf` into (complete markdown blocks, unfinished remainder).

    A split is only safe on a blank line outside a code fence, or right after a
    fence closes. The trailing line is always held back since more of it may
    still be streaming in.
    """
    lines = buf.split("\n")
    in_fence = False
    cut = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith(FENCE):
            in_fence = not in_fence
            if not in_fence:
                cut = i + 1
            continue
        if not in_fence and not line.strip():
            cut = i + 1
    if cut == 0 or cut >= len(lines):
        return "", buf
    return "\n".join(lines[:cut]), "\n".join(lines[cut:])


def _chunk_text(chunk) -> str:
    message = getattr(chunk, "message", None)
    if message is not None:
        return getattr(message, "content", "") or ""
    if isinstance(chunk, dict):
        return (chunk.get("message") or {}).get("content", "") or ""
    return ""
