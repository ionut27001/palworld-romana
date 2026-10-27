"""Export the Palworld Romanian translation into the public repo (D:\\palworld-ro\\github\\palworld-romana).

translations/<table>[.NNN].json = {"table", "entries": [{"key", "en", "ro"}]}, at most 2,000 entries per file.
Source: the PalworldRO project (data/en_strings.json = English, data/ro_strings.json = what the shipped pak contains;
rows the build keeps in English, Pal names and filler rows, have "ro" equal to "en"). Also copies glossary.json and
the scripts that build the mod.

Usage: python -I -X utf8 pal_repo_export.py
"""
import json
import pathlib
import shutil
from collections import defaultdict

SRC = pathlib.Path(r"E:\dev\alte-proiecte\palworld\PalworldRO")
REPO = pathlib.Path(r"D:\palworld-ro\github\palworld-romana")
CHUNK = 2000


def main():
    en = {(r["table"], r["key"]): r["src"] for r in json.load(open(SRC / "data" / "en_strings.json", encoding="utf-8"))}
    tables = defaultdict(list)
    for r in json.load(open(SRC / "data" / "ro_strings.json", encoding="utf-8")):
        e = en.get((r["table"], r["key"]))
        if e is None or not e.strip():
            continue
        tables[r["table"]].append({"key": r["key"], "en": e, "ro": r["ro"] if r["how"] != "kept" else e})
    out = REPO / "translations"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    files = n = 0
    for t, entries in sorted(tables.items()):
        parts = [entries[i:i + CHUNK] for i in range(0, len(entries), CHUNK)]
        for i, part in enumerate(parts, 1):
            fn = f"{t}.{i:03}.json" if len(parts) > 1 else f"{t}.json"
            (out / fn).write_text(json.dumps({"table": t, "entries": part}, ensure_ascii=False, indent=1) + "\n",
                                  encoding="utf-8", newline="\n")
            files += 1
        n += len(entries)
    (REPO / "glossary").mkdir(exist_ok=True)
    shutil.copy2(SRC / "glossary.json", REPO / "glossary" / "glossary.json")
    (REPO / "pipeline").mkdir(exist_ok=True)
    for f in ("ro.py", "build_mod.py", "patch_tables.py", "make_dist.py", "make_palschema.py"):
        shutil.copy2(SRC / f, REPO / "pipeline" / f)
    shutil.copy2(__file__, REPO / "pipeline" / pathlib.Path(__file__).name)
    print(f"exported {n} rows in {files} files")


if __name__ == "__main__":
    main()
