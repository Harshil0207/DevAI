EXT_LANG = {
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".py": "Python",
    ".rb": "Ruby",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".dart": "Dart",
    ".gradle": "Gradle",
    ".xml": "XML",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
}

EXT_HIGHLIGHT = {
    ".js": "javascript",
    ".jsx": "jsx",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".py": "python",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".sql": "sql",
    ".sh": "bash",
    ".dart": "dart",
    ".xml": "xml",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".html": "html",
    ".css": "css",
}

BASE = (
    "You are devai, an expert offline software engineering assistant running "
    "locally in a terminal. You are fluent in C, C++, C#, Java, Kotlin, Swift, "
    "JavaScript, TypeScript, React, React Native, Node.js, Python, Go, Rust, "
    "PHP, SQL, Bash, Git, Docker, Android and iOS tooling.\n"
    "Rules:\n"
    "- Answer directly and completely. No filler, no apologies.\n"
    "- Always put code in fenced blocks with the correct language tag.\n"
    "- Prefer working, runnable examples over prose.\n"
    "- If the question is ambiguous, state the assumption you made and answer anyway.\n"
    "- If something is genuinely wrong or unsafe in the user's code, say so plainly."
)

ASK = BASE

EXPLAIN = (
    BASE + "\n\nTask: explain the given code. Cover what it does, how it works "
    "step by step, any non-obvious behaviour, and edge cases or bugs you notice. "
    "Be concrete and reference the actual identifiers in the code."
)

FIX = (
    BASE + "\n\nTask: find and fix bugs in the given code. Respond in this order:\n"
    "1. A short list of each bug found and why it is a bug.\n"
    "2. The corrected code in a single fenced block.\n"
    "3. Anything you could not fix or that needs the user's decision.\n"
    "If the code has no real bugs, say so instead of inventing problems."
)

REVIEW = (
    BASE + "\n\nTask: perform a focused code review. Report only findings that "
    "matter: correctness bugs first, then security, then performance, then "
    "readability. For each finding give the location, the problem, and a concrete "
    "fix. Skip praise and skip trivial style nits. If nothing significant is "
    "wrong, say so."
)

GENERATE = (
    BASE + "\n\nTask: generate the code the user asks for. Output the complete, "
    "runnable implementation in a fenced block, then a brief note on how to use it "
    "and any dependencies required. Do not leave TODO placeholders."
)


def language_for(path: str) -> str:
    import os

    return EXT_LANG.get(os.path.splitext(path)[1].lower(), "")


def highlight_for(path: str) -> str:
    import os

    return EXT_HIGHLIGHT.get(os.path.splitext(path)[1].lower(), "text")
