from __future__ import annotations

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.recommender import recommend


TRACE_DIR = ROOT / "data" / "GenAI_SampleConversations"


def parse_user_turns(text: str) -> list[str]:
    turns: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "**User**":
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].startswith("**Agent**") and not lines[i].startswith("### Turn"):
                if lines[i].startswith(">"):
                    buf.append(lines[i][1:].strip())
                i += 1
            if " ".join(buf).strip():
                turns.append(" ".join(buf).strip())
        else:
            i += 1
    return turns


def parse_expected_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\| \d+ \| ([^|]+) \|", line)
        if match:
            name = match.group(1).strip()
            if name not in names:
                names.append(name)
    return names


def main() -> None:
    total = 0.0
    count = 0
    for path in sorted(TRACE_DIR.glob("C*.md"), key=lambda p: int(re.search(r"\d+", p.name).group())):
        text = path.read_text(encoding="utf-8")
        messages: list[dict[str, str]] = []
        result = None
        for user_turn in parse_user_turns(text):
            messages.append({"role": "user", "content": user_turn})
            result = recommend(messages)
            messages.append({"role": "assistant", "content": result.reply})

        got = [r["name"] for r in (result.recommendations if result else [])]
        expected = parse_expected_names(text)
        recall = len(set(got) & set(expected)) / len(set(expected)) if expected else 1.0
        total += recall
        count += 1
        print(f"{path.name}: recall={recall:.2f} final={result.end_of_conversation if result else False} got={got}")

    print(f"mean_recall={total / count:.2f}")


if __name__ == "__main__":
    main()
