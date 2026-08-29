"""
Splits source code into chunks for embedding.

Strategy: prefer logical boundaries (function/class/method definitions) using
simple regex heuristics per language family. Falls back to fixed-size line
windows for languages/files where no logical boundary is detected. This keeps
the implementation easy to follow while avoiding tiny or oversized chunks.
"""
import re
from typing import List, Dict

# Patterns that mark the start of a new logical block, by language.
BLOCK_START_PATTERNS = {
    "python": re.compile(r"^\s*(def |class |async def )"),
    "javascript": re.compile(r"^\s*(function |class |const .+=.*=>|export (default )?function|export class)"),
    "typescript": re.compile(r"^\s*(function |class |const .+=.*=>|export (default )?function|export class|interface )"),
    "java": re.compile(r"^\s*(public|private|protected)?\s*(static\s+)?(class |[\w<>\[\]]+\s+\w+\s*\()"),
    "c": re.compile(r"^[\w\*]+\s+\w+\s*\("),
    "cpp": re.compile(r"^[\w:<>\*]+\s+\w+\s*\("),
}

MIN_CHUNK_LINES = 4
MAX_CHUNK_LINES = 80
FALLBACK_WINDOW = 40


def chunk_code(text: str, language: str) -> List[Dict]:
    """
    Returns a list of chunks: {"text": str, "start_line": int, "end_line": int}
    Line numbers are 1-indexed and inclusive.
    """
    lines = text.splitlines()
    if not lines:
        return []

    pattern = BLOCK_START_PATTERNS.get(language)
    if pattern is None:
        return _fixed_window_chunks(lines)

    boundaries = [i for i, line in enumerate(lines) if pattern.match(line)]

    # If we found too few boundaries, logical chunking isn't useful; fall back.
    if len(boundaries) < 2:
        return _fixed_window_chunks(lines)

    chunks = []
    for idx, start in enumerate(boundaries):
        end = boundaries[idx + 1] - 1 if idx + 1 < len(boundaries) else len(lines) - 1
        # Merge tiny leading chunk (imports etc.) into the first block if very small
        chunk_lines = lines[start:end + 1]
        if len(chunk_lines) > MAX_CHUNK_LINES:
            # split an overly large block into fixed windows
            sub = _fixed_window_chunks(chunk_lines, base_offset=start)
            chunks.extend(sub)
        else:
            chunks.append({
                "text": "\n".join(chunk_lines),
                "start_line": start + 1,
                "end_line": end + 1,
            })

    # Capture any leading code before the first boundary (imports, globals)
    if boundaries[0] > 0:
        leading = lines[0:boundaries[0]]
        if len("\n".join(leading).strip()) > 0:
            chunks.insert(0, {
                "text": "\n".join(leading),
                "start_line": 1,
                "end_line": boundaries[0],
            })

    return [c for c in chunks if c["text"].strip()]


def _fixed_window_chunks(lines: List[str], base_offset: int = 0) -> List[Dict]:
    chunks = []
    i = 0
    while i < len(lines):
        window = lines[i:i + FALLBACK_WINDOW]
        if window:
            chunks.append({
                "text": "\n".join(window),
                "start_line": base_offset + i + 1,
                "end_line": base_offset + i + len(window),
            })
        i += FALLBACK_WINDOW
    return chunks
