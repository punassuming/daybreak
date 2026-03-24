import json
import re
from pathlib import Path


def load_jsonc_file(path: Path):
    raw_text = path.read_text(encoding="utf-8")
    return parse_jsonc(raw_text)


def dump_json_file(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_jsonc(text: str):
    stripped = _strip_comments(text)
    stripped = _remove_trailing_commas(stripped)
    return json.loads(stripped)


def _strip_comments(text: str) -> str:
    result = []
    in_string = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < length else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            if ch == "\n":
                result.append(ch)
            i += 1
            continue

        if in_string:
            result.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch == '"':
            in_string = True

        result.append(ch)
        i += 1

    return "".join(result)


def _remove_trailing_commas(text: str) -> str:
    pattern = re.compile(r",(\s*[}\]])")
    previous = None
    current = text
    while previous != current:
        previous = current
        current = pattern.sub(r"\1", current)
    return current
