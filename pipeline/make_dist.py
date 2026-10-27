"""Package the built mod for distribution:
  dist/workshop/PalworldRO/   Steam Workshop folder (Info.json + thumbnail.png + Paks/) for Palworld's mod uploader
  dist/nexus/PalworldRO_vX.zip   archive for Nexus Mods / Vortex (the .pak at the root + a README)
usage: make_dist.py [version]"""
import json, shutil, sys, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
PAK = ROOT / "build" / "ZZ_PalworldRO_P.pak"
DIST = ROOT / "dist"
DESC = ("Traducere completă a jocului în limba română (meniuri, iteme, Pali, dialoguri, misiuni, jurnale, tutoriale). "
        "Înlocuiește limba spaniolă: în Steam, click dreapta pe Palworld > Properties > General > Language > "
        "Español (España sau Latinoamérica). Engleza și celelalte limbi rămân neatinse. "
        "Complete Romanian translation of Palworld over the Spanish slots: set Palworld's language in Steam to "
        "either Spanish option.")


def thumbnail(path, size=627):
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for i, col in enumerate(((0, 43, 127), (252, 209, 22), (206, 17, 38))):   # Romanian tricolour
        d.rectangle([i * size // 3, 0, (i + 1) * size // 3, size], fill=col)
    band = Image.new("RGBA", (size, 250), (15, 18, 28, 215))
    img.paste(band, (0, (size - 250) // 2), band)
    bold = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 74)
    mid = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 58)
    small = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 30)
    y0 = (size - 250) // 2
    for text, font, y, fill in (("PALWORLD", bold, y0 + 20, (255, 255, 255)), ("în Română", mid, y0 + 110, (252, 209, 22)),
                                ("traducere completă · peste Español", small, y0 + 192, (225, 225, 230))):
        w = d.textlength(text, font=font)
        d.text(((size - w) / 2, y), text, font=font, fill=fill)
    img.save(path, optimize=True)


def workshop():
    out = DIST / "workshop" / "PalworldRO"
    if out.exists():
        shutil.rmtree(out)
    (out / "Paks").mkdir(parents=True)
    shutil.copy2(PAK, out / "Paks" / PAK.name)
    thumbnail(out / "thumbnail.png")
    info = {
        "ModName": "Palworld în Română - varianta pak (fără PalSchema)",
        "PackageName": "PalworldROPak",
        "Thumbnail": "thumbnail.png",
        "Version": VERSION,
        "DebugMode": False,
        "MinRevision": 82182,
        "Author": "oance",
        "Description": DESC,
        "Dependencies": None,
        "Tags": ["User Interface"],
        "InstallRule": [{"Type": "Paks", "Targets": ["./Paks/"]}],
    }
    json.dump(info, open(out / "Info.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("workshop folder:", out, [p.name for p in out.rglob("*") if p.is_file()])


README = f"""Palworld în Română v{VERSION}
=============================

Traducere completă a jocului Palworld în limba română: meniuri, iteme, Pali (Paldeck),
dialoguri NPC, misiuni, jurnale, tutoriale, abilități, tehnologii, construcții, hartă.

Traducerea înlocuiește limbile SPANIOLĂ (España și Latinoamérica) și INDONEZIANĂ (Bahasa Indonesia). Engleza și restul limbilor rămân neatinse.

INSTALARE
- Vortex: adaugă arhiva, instalează și activează; Vortex pune fișierul .pak în Pal\\Content\\Paks\\~mods.
- Manual: copiază ZZ_PalworldRO_P.pak în
  <Palworld>\\Pal\\Content\\Paks\\~mods\\   (creează folderul ~mods dacă nu există)

FOLOSIRE
- Limba jocului se alege din Steam, nu din joc:
  Steam > click dreapta pe Palworld > Properties > General > Language > „Español - España”
  sau „Español - Latinoamérica” sau „Bahasa Indonesia” (oricare). Apoi pornește jocul.
  Sfat: cu „Bahasa Indonesia”, mod-urile care au traduceri proprii (ex. Map Collectables) rămân în engleză.
- Ca să revii la engleză: aceeași setare din Steam > English.

DEZINSTALARE
- Șterge ZZ_PalworldRO_P.pak (sau dezactivează mod-ul în Vortex).

NOTE
- Numele Palilor sunt cele oficiale (Lamball, Cattiva...).
- După un update mare al jocului, textele noi apar în limba slotului (spaniolă/indoneziană) până la o versiune nouă.
- Corecturi: https://github.com/ionut27001/palworld-romana

---
Complete Romanian translation of Palworld, installed over the Spanish (Spain, Latin America) and Indonesian slots.
Install: put ZZ_PalworldRO_P.pak into <Palworld>\\Pal\\Content\\Paks\\~mods\\ (Vortex does this for you),
then in Steam: right-click Palworld > Properties > General > Language > either Spanish option or Bahasa Indonesia.
"""


def nexus():
    out = DIST / "nexus"
    out.mkdir(parents=True, exist_ok=True)
    z = out / f"PalworldRO_v{VERSION}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        f.write(PAK, PAK.name)
        f.writestr("README_PalworldRO.txt", README.encode("utf-8"))
    print("nexus/vortex archive:", z, [i.filename for i in zipfile.ZipFile(z).infolist()])


if __name__ == "__main__":
    assert PAK.exists(), "run build_mod.py first"
    workshop()
    nexus()
