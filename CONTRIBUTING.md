# Cum corectezi traducerea

## 1. Găsește textul

Toată traducerea e în `translations/`, câte un fișier pentru fiecare tabel al jocului, de exemplu:

- `DT_ItemNameText_Common.json`, `DT_ItemDescriptionText_Common.json`: iteme
- `DT_PalLongDescriptionText.json`, `DT_PalFirstActivatedInfoText.json`: Paldeck
- `DT_NpcTalkText_Common.json`, `DT_UniqueNPCText_Common.json`: dialoguri NPC
- `DT_UI_Common_Text_Common.*.json`: meniuri și interfață
- `DT_TechnologyNameText_Common.json`, `DT_SkillNameText_Common.json`: tehnologii și abilități

Cel mai simplu: apasă `T` pe pagina repository-ului (sau folosește căutarea GitHub) și caută textul **în engleză**
sau o bucată din traducerea greșită.

## 2. Editează doar câmpul `"ro"`

```json
{
 "key": "CATEGORY_TYPE_A_Product_TextData",
 "en": "Production",
 "ro": "Producție"
}
```

- Schimbi **doar** `"ro"`. **Nu** schimba `"key"`, `"en"` sau `"table"`.
- Păstrează exact tagurile: `<characterName id=|...|/>`, `<itemName id=|...|/>`, `{PlayerName}` și rupturile de
  rând. Verificarea automată respinge textul dacă lipsesc sau apar în plus.
- Scrie **cu diacritice** (ă, â, î, ș, ț cu virgulă).

Din browser: deschizi fișierul pe GitHub, apeși creionul (Edit), modifici, apoi **Commit changes → Create a new branch
→ Propose changes**. GitHub face singur fork-ul și Pull Request-ul.

## 3. Regulile, pe scurt

- Româna de azi, firească, fără arhaisme; jocul e modern / semi-futurist.
- Jucătorului i se spune „tu”; formulări neutre ca gen acolo unde jocul nu știe dacă personajul e băiat sau fată.
- Numele Palilor rămân cele oficiale (Lamball, Cattiva, Chikipi...).
- Termenii din [glossary/glossary.json](glossary/glossary.json) se scriu **exact** așa (Pal / Pali, Sferă Pal,
  Paldium, aptitudinile de lucru). Dacă vrei să schimbi un termen, deschide întâi un Issue.
