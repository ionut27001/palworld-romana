"""Build the PalSchema version of the translation (recommended method).

PalSchema's translation loader edits the game's text DataTables in memory at start-up:
  <mod>/translations/global/*.json  -> applied whatever the game language is
  {"DT_TableName": {"RowId": "text"}}  (table = the name the game reads, i.e. the composite DT_X for DT_X_Common)
No game files are replaced, so the mod shows up (and toggles) in the in-game Mods menu when installed from the
Workshop, other mods keep their own language, and rows added by future game updates simply stay untranslated.

usage: make_palschema.py [version] [--install-local]"""
import json, shutil, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
VERSION = next((a for a in sys.argv[1:] if not a.startswith("--")), "1.1.0")
COMPOSITE_PARENTS = {  # measured with tools/composites.py: each composite DT_X is built from DT_X_Common
    "DT_BuildObjectDescText_Common", "DT_HumanNameText_Common", "DT_ItemDescriptionText_Common",
    "DT_ItemNameText_Common", "DT_MapObjectNameText_Common", "DT_NamePrefixText_Common", "DT_NpcTalkText_Common",
    "DT_PalNameText_Common", "DT_SkillDescText_Common", "DT_SkillNameText_Common", "DT_TechnologyDescText_Common",
    "DT_TechnologyNameText_Common", "DT_UI_Common_Text_Common", "DT_UniqueNPCText_Common",
    "DT_WorldMap_Common_Text_Common"}
LOCAL = Path(r"D:\SteamLibrary\steamapps\common\Palworld\Mods\NativeMods\UE4SS\Mods\PalSchema\mods\PalworldRO")


def tables():
    out, n = defaultdict(dict), 0
    for r in json.load(open(ROOT / "data" / "ro_strings.json", encoding="utf-8")):
        if r["how"] not in ("gemini", "local"):          # names kept as-is, placeholders, untranslated: leave alone
            continue
        t = r["table"][:-len("_Common")] if r["table"] in COMPOSITE_PARENTS else r["table"]
        out[t][r["key"][:-len("_TextData")]] = r["ro"]
        n += 1
    return out, n


def write_translations(dest):
    data, n = tables()
    g = dest / "translations" / "global"
    if g.exists():
        shutil.rmtree(g)
    g.mkdir(parents=True)
    for t, rows in sorted(data.items()):
        json.dump({t: rows}, open(g / f"{t}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{n} rows in {len(data)} tables -> {g}")


def workshop():
    sys.path.insert(0, str(ROOT))
    from make_dist import thumbnail
    out = ROOT / "dist" / "workshop_palschema" / "PalworldRO"
    if out.exists():
        shutil.rmtree(out)
    write_translations(out / "PalSchema")
    thumbnail(out / "thumbnail.png")
    info = {
        "ModName": "Palworld în Română (Romanian Translation)",
        "PackageName": "PalworldRO",
        "Thumbnail": "thumbnail.png",
        "Version": VERSION,
        "DebugMode": False,
        "MinRevision": 82182,
        "Author": "oance",
        "Description": ("Traducere completă a jocului în limba română: meniuri, iteme, Pali, dialoguri, misiuni, jurnale, "
                        "tutoriale. Se activează/dezactivează din meniul Mods; nu schimbă limba din Steam și nu "
                        "înlocuiește fișiere ale jocului. Necesită PalSchema. / Complete Romanian translation of Palworld "
                        "(menus, items, Pals, dialogue, quests, journals). Toggle it in the Mods menu. Requires PalSchema."),
        "Dependencies": ["UE4SSExperimentalPW", "PalSchema"],
        "Tags": ["PalSchema", "User Interface"],
        "InstallRule": [{"Type": "PalSchema", "Targets": ["./PalSchema/"]}],
    }
    json.dump(info, open(out / "Info.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("workshop (PalSchema) folder:", out)


NEXUS_README = f"""Palworld în Română v{VERSION} — varianta PalSchema (recomandată)
==============================================================

Traducere completă în română (meniuri, iteme, Pali, dialoguri, misiuni, jurnale, tutoriale), aplicată de PalSchema
în memorie. Limba din Steam rămâne English; celelalte mod-uri rămân în engleză.

NECESITĂ: UE4SS pentru Palworld + PalSchema (ambele există pe Steam Workshop și pe Nexus).

INSTALARE MANUALĂ
  Copiază folderul PalworldRO în:
  <Palworld>\\Mods\\NativeMods\\UE4SS\\Mods\\PalSchema\\mods\\
  (dacă ai UE4SS clasic: <Palworld>\\Pal\\Binaries\\Win64\\ue4ss\\Mods\\PalSchema\\mods\\)
  Pornește jocul.

DEZINSTALARE: șterge folderul PalworldRO din PalSchema\\mods.

Alternativa fără PalSchema: fișierul PalworldRO_vX.zip (pak peste limba spaniolă/indoneziană).
"""


def nexus():
    import zipfile
    out = ROOT / "dist" / "nexus"
    out.mkdir(parents=True, exist_ok=True)
    src = ROOT / "dist" / "workshop_palschema" / "PalworldRO" / "PalSchema"
    z = out / f"PalworldRO_PalSchema_v{VERSION}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for p in sorted(src.rglob("*.json")):
            f.write(p, "PalworldRO/" + p.relative_to(src).as_posix())
        f.writestr("README_PalworldRO_PalSchema.txt", NEXUS_README.encode("utf-8"))
    print("nexus (PalSchema) archive:", z, f"{z.stat().st_size} bytes")


if __name__ == "__main__":
    workshop()
    nexus()
    if "--install-local" in sys.argv:
        write_translations(LOCAL)
        print("installed for a local test:", LOCAL)
