"""Merge translations, patch the target culture's tables and install the mod pak.

Primary: data/ro_gemini.db (Gemini 3.8 Flash). Where Gemini's line still has a serious problem, use the local
gemma4:26b line from data/ro.db if that one is clean; otherwise keep the English (never ship a broken line).
Cosmetic flags (english left, too long, archaic word, foreign letters, line breaks) still ship the translation.

usage: build_mod.py [culture=es] [--install]"""
import json, shutil, sqlite3, subprocess, sys
from collections import Counter
from pathlib import Path
import ro
import patch_tables

ROOT = ro.ROOT
SERIOUS = {"markers", "bad control characters", "empty", "no output"}
REPAK = Path(r"D:\palworld-ro\tools\repak\bin\repak.exe")  # repak_cli 0.2.3 from github.com/trumank/repak
PAKS = Path(r"D:\SteamLibrary\steamapps\common\Palworld\Pal\Content\Paks\~mods")


def load(db):
    c = sqlite3.connect(db)
    units = {(t, m): (st, r, json.loads(e or "[]")) for t, m, st, r, e in
             c.execute("SELECT tbl, masked, status, ro, errors FROM units")}
    rows = c.execute("SELECT tbl, key, src, uid FROM rows").fetchall()
    masked_of = dict(c.execute("SELECT uid, masked FROM units").fetchall())
    return units, rows, masked_of


def usable(u):
    if not u:
        return None
    st, text, errs = u
    if st not in ("done", "flagged") or not text:
        return None
    return None if SERIOUS & set(errs) else (text, errs)


def merge():
    gem, rows, masked_of = load(ROOT / "data" / "ro_gemini.db")
    loc, _, _ = load(ROOT / "data" / "ro.db") if (ROOT / "data" / "ro.db").exists() else ({}, None, None)
    out, how = [], Counter()
    for tbl, key, src, uid in rows:
        if uid is None:
            out.append({"table": tbl, "key": key, "ro": src, "how": "kept"}); how["kept (names/placeholders)"] += 1
            continue
        masked = masked_of[uid]
        pick, origin = usable(gem.get((tbl, masked))), "gemini"
        if pick is None:
            pick, origin = usable(loc.get((tbl, masked))), "local"
        if pick is None:
            out.append({"table": tbl, "key": key, "ro": src, "how": "english"}); how["english (no clean translation)"] += 1
            continue
        text, errs = pick
        final = ro.unmask(ro.finalize(text, masked), ro.mask(src)[1])
        out.append({"table": tbl, "key": key, "ro": final, "how": origin, "flags": errs})
        how[origin + (" (flagged)" if errs else "")] += 1
    p = ROOT / "data" / "ro_strings.json"
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("merged:", dict(how))
    return how


PAK_NAME = "ZZ_PalworldRO_P.pak"
OLD_PAKS = ("ZZ_PalworldRO_test_P.pak", "ZZ_PalworldRO_es_P.pak")   # earlier builds this one replaces


def build(cultures, install):
    """One pak that puts Romanian over every listed culture (default: both Spanish slots, es and es-MX:
    Steam's "Spanish - Spain" maps to es, "Spanish - Latin America" (latam) to es-MX)."""
    how = merge()
    stage = ROOT / "build" / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    for culture in cultures:
        src = ROOT / "data" / "extract" / "Pal" / "Content" / "L10N" / culture
        sys.argv = ["patch_tables.py", culture, str(src), str(stage)]
        patch_tables.main()
    pak = ROOT / "build" / PAK_NAME
    subprocess.run([str(REPAK), "pack", "--version", "V11", "--mount-point", "../../../", "-q", str(stage), str(pak)],
                   check=True)
    listed = subprocess.run([str(REPAK), "list", str(pak)], capture_output=True, text=True, check=True).stdout.split()
    for culture in cultures:
        assert sum(f"L10N/{culture}/" in x for x in listed) == 54, f"{culture}: wrong file count in pak"
    print(f"pak: {pak} ({pak.stat().st_size} bytes, {len(listed)} files, cultures {cultures})")
    if install:
        PAKS.mkdir(parents=True, exist_ok=True)
        for old in OLD_PAKS:
            if (PAKS / old).exists():
                (PAKS / old).unlink()          # fails with PermissionError while the game has it open
                print("removed older pak:", old)
        shutil.copy2(pak, PAKS / PAK_NAME)
        print("installed:", PAKS / PAK_NAME)
    return how


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    build(args[0].split(",") if args else ["es", "es-MX"], "--install" in sys.argv)
