"""Palworld EN->RO translation core: tag masking, context (names behind tags, neighbouring lines,
glossary, setting), prompts, Ollama calls and validation. Used by test_slice.py and the full run."""
import json, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
ROWS = json.load(open(ROOT / "data" / "en_strings.json", encoding="utf-8"))
GLOSSARY = {k: v for k, v in json.load(open(ROOT / "glossary.json", encoding="utf-8")).items() if not k.startswith("_")}
BY_TABLE_KEY = {(r["table"], r["key"]): r for r in ROWS}
_JA_PATH = ROOT / "data" / "ja_strings.json"
JA = json.load(open(_JA_PATH, encoding="utf-8")) if _JA_PATH.exists() else {}
NAME_TABLES = {"DT_ItemNameText_Common", "DT_MapObjectNameText_Common", "DT_SkillNameText_Common",
               "DT_TechnologyNameText_Common", "DT_HumanNameText_Common", "DT_UniqueNPCText_Common",
               "DT_NamePrefixText_Common", "DT_DungeonNameText", "DT_WorldMap_Common_Text_Common",
               "DT_BuildObjectCategoryText", "DT_FishPondTargetTypeNameText", "DT_CharacterTeamMissionText",
               "DT_UI_Common_Text_Common", "DT_PalNameText_Common"}


def ja_context(table, key):
    """Japanese original with its tags shown as ⟦…⟧ (numbering differs from the English markers), or None.
    Not given for names/UI terms: the official names come from the English localisation."""
    if table in NAME_TABLES:
        return None
    s = JA.get(table, {}).get(key)
    if not s or not s.strip():
        return None
    return TAG_RE.sub("⟦…⟧", s)

SETTING = (
    "Palworld is an open-world survival and crafting game on the Palpagos Islands. The player catches "
    "creatures called Pals, builds bases and progresses from stone tools to factories, firearms, electricity "
    "and advanced Paldium technology. Factions include syndicates, the PIDF (an armed security force), "
    "researchers and cults. The world is MODERN to NEAR-FUTURE (semi-futuristic) - NOT medieval and NOT a "
    "fairy tale. Tone: light-hearted with dark humour; item and Pal descriptions are often witty."
)

KIND = {
    "DT_ItemNameText_Common": "item names (short)",
    "DT_ItemDescriptionText_Common": "item descriptions",
    "DT_NpcTalkText_Common": "NPC dialogue lines, quest texts and the player's dialogue choices",
    "DT_UI_Common_Text_Common": "user interface text: buttons, labels, menus, system messages (keep short)",
    "DT_NoteDescText": "in-world journals and diaries written by characters (first person)",
    "DT_PalLongDescriptionText": "Paldeck encyclopedia entries about a Pal",
    "DT_PalFirstActivatedInfoText": "Pal partner-skill explanations",
    "DT_PalNameText_Common": "Pal names (proper names: keep unchanged)",
    "DT_HumanNameText_Common": "human character names and job titles",
    "DT_UniqueNPCText_Common": "unique NPC names and titles",
    "DT_SkillNameText_Common": "skill names (short)",
    "DT_SkillDescText_Common": "skill descriptions",
    "DT_TechnologyNameText_Common": "technology tree entry names",
    "DT_TechnologyDescText_Common": "technology tree descriptions",
    "DT_MapObjectNameText_Common": "names of buildable structures and world objects",
    "DT_BuildObjectDescText_Common": "descriptions of buildable structures",
    "DT_HelpGuideDescText": "help pages explaining game mechanics",
    "DT_TutorialMessage_Text": "short tutorial hints",
    "DT_WorldMap_Common_Text_Common": "map region and place names",
    "DT_MapRespawnPointInfoText": "respawn point names and short descriptions",
    "DT_NamePrefixText_Common": "boss and special Pal titles",
    "DT_DungeonNameText": "dungeon names",
    "DT_LabResearchText": "research lab upgrade names and descriptions",
}

# --- tags -------------------------------------------------------------------------------------------
TAG_RE = re.compile(r"<[^<>\r\n]{0,80}>|\{[A-Za-z0-9_]+\}")
ID_TAG = re.compile(r"<(\w+) id=\|([^|]*)\|[^<>]*?/?>")  # may carry extra attrs, e.g. style=|Elem_Water|
TAG_TABLES = {
    "itemname": [("DT_ItemNameText_Common", "ITEM_NAME_{}_TextData")],
    "mapobjectname": [("DT_MapObjectNameText_Common", "MAPOBJECT_NAME_{}_TextData")],
    "charactername": [("DT_PalNameText_Common", "PAL_NAME_{}_TextData"), ("DT_HumanNameText_Common", "NAME_{}_TextData")],
    "uicommon": [("DT_UI_Common_Text_Common", "{}_TextData")],
    "activeskillname": [("DT_SkillNameText_Common", "ACTION_SKILL_{}_TextData"), ("DT_SkillNameText_Common", "{}_TextData")],
}
PLACEHOLDER_HINT = {
    "PlayerName": "the player's name", "PalName": "a Pal's name", "CharacterName": "a character's name",
    "ItemName": "an item name", "TargetName": "a target's name",
}


def mask(src):
    """Replace every tag / placeholder with ⟦n⟧. Returns (masked_text, [original tags])."""
    tags = []

    def rep(m):
        tags.append(m.group(0))
        return f"⟦{len(tags)}⟧"
    return TAG_RE.sub(rep, src), tags


def unmask(text, tags):
    return re.sub(r"⟦(\d+)⟧", lambda m: tags[int(m.group(1)) - 1] if 0 < int(m.group(1)) <= len(tags) else m.group(0), text)


def resolve(tag, ro_names=None):
    """(table, key, english) the tag points to, or None."""
    m = ID_TAG.fullmatch(tag)
    if not m:
        return None
    for table, pat in TAG_TABLES.get(m.group(1).lower(), []):
        r = BY_TABLE_KEY.get((table, pat.format(m.group(2))))
        if r:
            return table, r["key"], r["src"]
    return None


def describe_tag(tag, ro_names=None):
    """Human-readable meaning of one tag for the model (and the review page)."""
    ro_names = ro_names or {}
    m = ID_TAG.fullmatch(tag)
    if m:
        kind = m.group(1).lower()
        if kind in ("img", "keyguideicon"):
            return "button/icon picture (no text)"
        res = resolve(tag)
        label = {"itemname": "item name", "mapobjectname": "structure name", "charactername": "Pal/character name",
                 "uicommon": "game term", "activeskillname": "skill name"}.get(kind, kind)
        if res:
            ro = ro_names.get((res[0], res[1]))
            return f"{label} inserted by the game: \"{res[2]}\"" + (f" (RO: \"{ro}\")" if ro else "")
        return f"{label} inserted by the game (id {m.group(2)})"
    if tag.startswith("{"):
        name = tag.strip("{}")
        return f"value inserted at runtime: {PLACEHOLDER_HINT.get(name, name)}"
    if tag == "</>":
        return "end of colour formatting"
    return "start of colour formatting (text until the end marker is highlighted)"


# --- what needs translating -----------------------------------------------------------------------------
def skip_reason(src):
    s = src.strip()
    if s in ("", "en Text", "-", "--"):
        return "placeholder"
    if not re.search(r"[A-Za-z]{2,}", TAG_RE.sub("", s)):
        return "no words"
    return None


# --- prompts ----------------------------------------------------------------------------------------
RULES = """Translate English game text into natural, fluent, MODERN Romanian.
- Setting: {setting}
- Never use archaic, folkloric or regional words (no "ciomag", "poruncă", "dârzenie", "voinic", "hăt").
- Address the player with "tu". The player can be male or female: when speaking TO the player, never use
  adjectives or participles that show gender ("Fii liniștit", "ești răsplătit", "nesăbuitule"); rephrase
  ("Nu-ți face griji", "te voi răsplăti", "novice ce ești"). Third-person speakers keep their own gender.
- Markers like ⟦1⟧ stand for tags the game fills in. Keep EVERY marker exactly once, unchanged; move it
  where Romanian word order needs it. Names inserted through markers cannot be declined, so phrase the
  sentence so the inserted name works in its basic form (e.g. "Necesită: ⟦1⟧" or "Folosește ⟦1⟧ pentru...").
- Keep the same number of line breaks (\\r\\n) as the source; they control the on-screen layout.
- Keep Pal names, people's names and invented proper nouns unchanged. Translate descriptive place names,
  titles and epithets (e.g. "Guardian of Lightning" -> "Păzitorul Fulgerului", "X's Diary" -> "Jurnalul lui X").
- Never leave English words in the Romanian (no "damage", "minigame", "token", "skill", "Schematic"); only
  the glossary decides which English terms stay (boss, raid, HP).
- Before a name inserted through a marker, use the possessive/dative form with "lui": "a lui ⟦1⟧", "lui ⟦1⟧".
- Item and object names: short natural Romanian noun phrases in sentence case (only the first word and
  proper nouns capitalised), with the right prepositions: "Ou uriaș de dragon", "Schemă de talisman Frostallion".
- Puns and jokes: recreate them in Romanian or keep the tone; never translate them into nonsense.
- UI labels stay short; do not add a final period if the source has none; Romanian sentence case.
- Use these fixed terms (English -> Romanian):
{glossary}

Examples of the expected quality:
{examples}"""

EXAMPLES = [
    ("⟦1⟧'s exclusive skill.\\r\\nRaises its front legs and slams them into the ground,",
     "Abilitatea exclusivă a lui ⟦1⟧.\\r\\nÎși ridică picioarele din față și le izbește de pământ,"),
    ("Huge Dragon Egg", "Ou uriaș de dragon"),
    ("Proof of defeating [Dinossom Lux, Guardian of Lightning].",
     "Dovada că l-ai învins pe [Dinossom Lux, Păzitorul Fulgerului]."),
    ("A ⟦1⟧.\\r\\nPlace in an ⟦2⟧ to incubate it.", "Un ⟦1⟧.\\r\\nPune-l într-un ⟦2⟧ pentru a-l incuba."),
    ("Can be ridden.\\r\\n\\r\\nWhile in party,\\r\\nfishing minigame begins with the capture gauge ⟦1⟧⟦2⟧%⟦3⟧ higher",
     "Poate fi călărit.\\r\\n\\r\\nCât timp este în echipă,\\r\\nminijocul de pescuit începe cu bara de captură cu ⟦1⟧⟦2⟧%⟦3⟧ mai plină"),
    ("My focus is completely fried today.\\r\\nCome back tomorrow if you want to push the boundaries of Pal science!",
     "Azi am creierul complet prăjit.\\r\\nRevino mâine dacă vrei să împingi mai departe granițele științei Pal!"),
    ("Marcus Dryden's Diary - 1\\r\\n\\r\\nWhat a joke. All the idiots do around here is snort up stims.",
     "Jurnalul lui Marcus Dryden - 1\\r\\n\\r\\nCe glumă. Tot ce fac idioții pe-aici e să prizeze stimulante."),
    ("Rest assured, I have prepared a suitable reward for your efforts.",
     "Nu-ți face griji, am pregătit o recompensă pe măsura eforturilor tale."),
    ("Party", "Echipă"),
    ("10 each", "Câte 10"),
]

SYSTEM_TRANSLATE = RULES + """

You get JSON: the text type, optional earlier lines for context, and the items to translate. Each item may
carry "markers" (what each ⟦n⟧ stands for) and "about" (extra context such as the item it describes).
Some items also carry "ja": the original Japanese line the English was localised from. Translate the ENGLISH
(it holds the official names, terms and jokes); use the Japanese only to understand meaning, tone, who
speaks and what an ambiguous English phrase refers to. Never take names or ⟦…⟧ positions from the Japanese.
Return JSON {{"t": [one Romanian string per item, same order]}}."""

SYSTEM_POSTEDIT = RULES + """

You get JSON: the text type, optional earlier lines, and items with the English source plus a machine
"draft" in Romanian. Produce the final Romanian: keep what is good, fix meaning errors, grammar, terms,
register, markers and line breaks. Return JSON {{"t": [one final Romanian string per item, same order]}}."""


def system_prompt(kind="translate"):
    gl = "\n".join(f"  {k} -> {v}" for k, v in GLOSSARY.items())
    ex = "\n".join(f"  EN: {e}\n  RO: {r}" for e, r in EXAMPLES)
    base = SYSTEM_TRANSLATE if kind == "translate" else SYSTEM_POSTEDIT
    return base.format(setting=SETTING, glossary=gl, examples=ex)


TG_PROMPT = ("You are a professional English (en) to Romanian (ro) translator. Your goal is to accurately convey the "
             "meaning and nuances of the original English text while adhering to Romanian grammar, vocabulary, and "
             "cultural sensitivities. Produce only the Romanian translation, without any additional explanations or "
             "commentary. Please translate the following English text into Romanian:\n\n\n")

SCHEMA = {"type": "object", "properties": {"t": {"type": "array", "items": {"type": "string"}}}, "required": ["t"]}


# --- Ollama -------------------------------------------------------------------------------------------
def chat(url, model, messages, fmt=None, num_ctx=16384, timeout=1800):
    body = {"model": model, "stream": False, "think": False, "keep_alive": "15m",
            "options": {"temperature": 0.2, "num_ctx": num_ctx}, "messages": messages}
    if fmt:
        body["format"] = fmt
    req = urllib.request.Request(url.rstrip("/") + "/api/chat", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    r["_wall"] = time.time() - t0
    return r


def ask_batch(url, model, payload, kind="translate"):
    """Send one batch; returns (list_of_strings_or_None, ollama_response)."""
    r = chat(url, model, [{"role": "system", "content": system_prompt(kind)},
                          {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], SCHEMA)
    try:
        out = json.loads(r["message"]["content"])["t"]
    except Exception:
        out = None
    return out, r


def openrouter_key():
    import os
    k = os.environ.get("OPENROUTER_API_KEY")
    if not k:  # set with setx but the app was not restarted: read the user environment from the registry
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            k = winreg.QueryValueEx(h, "OPENROUTER_API_KEY")[0]
    return k


def chat_openrouter(model, messages, schema=None, extra=None, timeout=600):
    body = {"model": model, "messages": messages, "temperature": 0.2, "usage": {"include": True},
            "provider": {"require_parameters": True, "sort": "price"}}
    if schema:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "translations", "strict": True, "schema": schema}}
    body.update(extra or {})
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {openrouter_key()}",
                                  "X-Title": "PalworldRO translation"})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    u = r.get("usage", {})
    return {"message": {"content": r["choices"][0]["message"].get("content") or ""},
            "eval_count": u.get("completion_tokens", 0), "prompt_eval_count": u.get("prompt_tokens", 0),
            "cost": u.get("cost", 0.0), "provider": r.get("provider"), "_wall": time.time() - t0}


def ask_batch_api(model, payload, kind="translate", extra=None):
    r = chat_openrouter(model, [{"role": "system", "content": system_prompt(kind)},
                                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], SCHEMA, extra)
    try:
        txt = r["message"]["content"].strip()
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt)
        out = json.loads(txt)["t"]
    except Exception:
        out = None
    return out, r


def ask_translategemma(url, model, text):
    r = chat(url, model, [{"role": "user", "content": TG_PROMPT + text}], num_ctx=4096)
    return r["message"]["content"].strip(), r


# --- validation ---------------------------------------------------------------------------------------
ARCHAIC = re.compile(r"\b(ciomag\w*|porunc\w*|dârzeni\w*|darzeni\w*|voinic\w*|hăt|ostaş\w*|ostaș\w*|"
                     r"pricina|carele|însă-i|dumneata|domniile?|mări\b)", re.I)
FOREIGN = re.compile(r"[çğıöüÇĞİÖÜßñЀ-ӿ぀-ヿ一-鿿가-힯]")
ENGLISH = re.compile(r"\b(the|and|with|of|your|you|damage|minigame|skill|token|schematic|guardian|poison|"
                     r"while|when|can|will|this|that)\b", re.I)


def norm_breaks(s):
    return s.replace("\\r\\n", "\n").replace("\r\n", "\n").replace("\\n", "\n")


def check(src_masked, ro, n_tags):
    errs = []
    if not ro or not ro.strip():
        return ["empty"]
    if sorted(re.findall(r"⟦(\d+)⟧", ro)) != sorted(str(i) for i in range(1, n_tags + 1)):
        errs.append("markers")
    if norm_breaks(src_masked).count("\n") != norm_breaks(ro).count("\n"):
        errs.append("line breaks")
    if re.search(r"\r(?!\n)|\t", ro.replace("\\r\\n", "\n")):
        errs.append("bad control characters")
    if FOREIGN.search(ro):
        errs.append("foreign letters")
    if ARCHAIC.search(ro):
        errs.append("archaic word")
    if len(ENGLISH.findall(ro)) > len(ENGLISH.findall(src_masked)) // 3 and ENGLISH.search(ro):
        errs.append("english left")
    if len(ro) > 2.5 * len(src_masked) + 25:
        errs.append("too long")
    if ro.strip() == src_masked.strip() and re.search(r"[A-Za-z]{4,} [a-z]{3,}", src_masked):
        errs.append("untranslated")
    return errs


def finalize(ro, src_masked=""):
    """Model text -> game text: CRLF line breaks; drop a final period the source does not have."""
    out = norm_breaks(ro).replace("\n", "\r\n")
    if src_masked and not src_masked.rstrip().endswith(".") and out.rstrip().endswith(".") \
            and not out.rstrip().endswith(".."):
        out = out.rstrip()[:-1]
    return out
