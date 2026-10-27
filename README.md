# Palworld — Traducere în limba română

Traducere neoficială, făcută de fani, a textului din **Palworld**: meniuri, iteme și descrieri, Pali (Paldeck),
dialoguri NPC, misiuni, jurnale, tutoriale, abilități, tehnologii, construcții, locuri de pe hartă
(27 de tabele de text, ~14.700 de intrări). Numele Palilor rămân cele oficiale (Lamball, Cattiva...).

**Descarcă mod-ul:** Nexus Mods: https://www.nexusmods.com/palworld/mods/6001

Acest repository e locul unde **oricine poate corecta traducerea**: o replică ciudată, un termen tradus inconsecvent,
o descriere care nu sună românește. Corecturile acceptate intră în următoarea versiune a mod-ului.

## Instalare

1. Copiază `ZZ_PalworldRO_P.pak` în `<Palworld>\Pal\Content\Paks\~mods\` (creează folderul `~mods` dacă nu există;
   Vortex face asta singur).
2. Limba se alege din **Steam**, nu din joc: click dreapta pe Palworld → Properties → General → Language →
   **Español - España**, **Español - Latinoamérica** sau **Bahasa Indonesia** (mod-ul le acoperă pe toate trei).
   Înapoi la engleză: aceeași setare → English.

Dezinstalare: ștergi fișierul `.pak`. Engleza și celelalte limbi ale jocului rămân neatinse.

## Cum ajuți

- **Ai găsit o greșeală, dar nu vrei să editezi fișiere?** Deschide un
  [Issue „Greșeală de traducere”](../../issues/new/choose): scrii unde apare, ce e greșit și ce ai propune.
- **Vrei să corectezi direct?** Vezi [CONTRIBUTING.md](CONTRIBUTING.md): găsești textul în `translations/`, editezi
  câmpul `"ro"` și trimiți un Pull Request. Se poate face și din browser.

## Ce e în repository

| Folder | Ce conține |
|---|---|
| `translations/` | Tot textul, câte un fișier JSON pentru fiecare tabel al jocului: cheia, originalul (`en`) și traducerea (`ro`) |
| `glossary/glossary.json` | Termenii ficși (Pal, Sferă Pal, aptitudinile de lucru...) folosiți la fiecare traducere |
| `tools/check.py` | Verificarea automată rulată pe fiecare Pull Request |
| `pipeline/` | Scripturile cu care a fost făcută traducerea și construit mod-ul |

## Cum a fost făcută

Textul a fost tradus cu modelul Gemini 3.8 Flash, ales prin teste oarbe pe replici reale (notate fără să se știe
modelul), cu: setarea jocului (modern, fără arhaisme), glosar fix, replicile vecine ca context, originalul japonez la
texte, adresare cu „tu”. Fiecare replică e verificată automat (taguri, rânduri, litere străine, engleză rămasă,
arhaisme); unde n-a ieșit nimic curat, rămâne engleza. Testat în joc.

## Alte traduceri și susținere

Am tradus și [Cyberpunk 2077](https://github.com/ionut27001/cp77-romana),
[Assassin's Creed Shadows](https://github.com/ionut27001/acs-romana),
[Kingdom Come: Deliverance](https://github.com/ionut27001/kcd1-romana) și
[Kingdom Come: Deliverance II](https://github.com/ionut27001/kcd2-romana). Vrei alt joc în română? Scrie-mi pe Nexus în
comentarii. Dacă vrei să mă susții, îmi poți face cadou jocul pe care vrei să-l traduc, pe
[Steam](https://steamcommunity.com/profiles/76561199120542317). Nu e obligatoriu: traducerile rămân gratuite.

Licențe și drepturi: vezi [NOTICE.md](NOTICE.md).
