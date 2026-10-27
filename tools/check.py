"""Checks translation files: valid JSON, nothing missing, the game's tags kept, comma diacritics.

Tags are what the game fills in or formats: <characterName id=|...|/>, <itemName id=|...|/>, <br>, {PlayerName}...
They must be the same in "ro" as in "en" (order may change where Romanian word order needs it).

Usage: python tools/check.py [file ...]   (no arguments = every file under translations/)
"""
import collections
import json
import pathlib
import re
import sys

TAG = re.compile(r"<[^<>\r\n]{0,80}>|\{[A-Za-z0-9_]+\}")
ROOT = pathlib.Path(__file__).resolve().parent.parent


def problems_for(en, ro):
    out = []
    if en.strip() and not ro.strip():
        out.append("empty translation")
    if re.search(r"[şţŞŢ]", ro):
        out.append("cedilla ş/ţ instead of ș/ț")
    if collections.Counter(TAG.findall(en)) != collections.Counter(TAG.findall(ro)):
        out.append(f"tags differ: {TAG.findall(en)} vs {TAG.findall(ro)}")
    if en.count("\n") != ro.count("\n"):
        out.append("different number of line breaks")
    return out


def check(path):
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"{path}: invalid JSON ({e})"]
    if not isinstance(doc, dict) or "table" not in doc or not isinstance(doc.get("entries"), list):
        return [f"{path}: expected {{\"table\": ..., \"entries\": [...]}}"]
    found = []
    for e in doc["entries"]:
        if not isinstance(e.get("en"), str) or not isinstance(e.get("ro"), str):
            found.append(f"{path} {e.get('key')}: \"en\" and \"ro\" must be text")
            continue
        found += [f"{path} {e.get('key')}: {p}" for p in problems_for(e["en"], e["ro"])]
    return found


def main():
    files = [pathlib.Path(a) for a in sys.argv[1:] if a.endswith(".json")] or \
        sorted((ROOT / "translations").glob("*.json"))
    problems = [p for f in files if f.exists() for p in check(f)]
    for p in problems:
        print(p)
    print(f"{len(files)} files checked, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
