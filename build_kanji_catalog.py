#!/usr/bin/env python3
"""Build the full Kanji-browser catalog from data already shipped with Kotoba.

The original kanji_data.json is intentionally kept as the richer 408-entry
textbook/vocabulary source used by Everyday and the general vocabulary engine.
This generated catalog is for the Kanji browser/practice/writing surfaces and
merges:
  * all original kanji_data.json entries;
  * all JLPT N5-N1 entries from jlpt_kanji.json;
  * extra single-kanji words explicitly taught elsewhere in Kotoba
    (frequency list, picture dictionary, verbs and non-radical roadmap lessons).

No outside dictionary data is introduced here. If Kotoba does not already have
a reliable stroke count or on/kun reading for an added character, that field is
left empty rather than guessed.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parent.resolve()
DATA = ROOT / "data"


def load(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return json.load(f)


def is_single_kanji(text):
    return isinstance(text, str) and len(text) == 1 and "\u4e00" <= text <= "\u9fff"


def vocab_record(word, reading="", romaji="", meaning="", source="", rank=None, example_ja="", example_en=""):
    return {
        "word": word or "",
        "reading": reading or "",
        "romaji": romaji or "",
        "meaning": meaning or "",
        "source": source,
        "rank": rank,
        "example_ja": example_ja or "",
        "example_en": example_en or "",
        "extra_kanji": sum(1 for c in (word or "") if "\u4e00" <= c <= "\u9fff") > 1,
    }


core = load("kanji_data.json")
core_extras = load("kanji_vocab_extra.json")
jlpt = load("jlpt_kanji.json")
frequency = load("frequency_words.json")
picture = load("picture_dict.json")
verbs = load("verbs.json")
roadmap = load("roadmap.json")

# Gather grounded vocabulary examples from the app's existing word sources.
word_sources = []
for x in frequency:
    word_sources.append(vocab_record(
        x.get("word"), x.get("reading"), x.get("romaji"), x.get("meaning"),
        "frequency", x.get("rank"), x.get("example_ja"), x.get("example_en"),
    ))
for x in picture:
    word_sources.append(vocab_record(
        x.get("word"), x.get("reading"), x.get("romaji"), x.get("meaning"), "picture_dictionary"
    ))
for x in verbs:
    word_sources.append(vocab_record(
        x.get("word"), x.get("reading"), "", x.get("meaning"), "verbs"
    ))
for section in roadmap:
    for chapter in section.get("chapters", []):
        # Radical lessons contain component forms such as 亻/氵/扌. They belong
        # in the Radicals section, not as extra standalone Kanji-browser items.
        identity = (chapter.get("id", "") + " " + chapter.get("title", "")).lower()
        is_radical_lesson = "radical" in identity
        for x in chapter.get("vocab", []):
            word_sources.append(vocab_record(
                x.get("jp"), x.get("reading"), x.get("romaji"), x.get("meaning"),
                "roadmap_radical" if is_radical_lesson else "roadmap"
            ))

# Keep best record for duplicate written words. Frequency entries have context
# sentences/rank and are preferred, then picture dictionary, verbs, roadmap.
source_priority = {"frequency": 0, "picture_dictionary": 1, "verbs": 2, "roadmap": 3, "roadmap_radical": 9}
by_word = {}
for item in word_sources:
    w = item["word"]
    if not w:
        continue
    cur = by_word.get(w)
    if cur is None or source_priority.get(item["source"], 8) < source_priority.get(cur["source"], 8):
        by_word[w] = item
word_sources = list(by_word.values())


def vocab_for_char(ch, limit=8):
    matches = [x for x in word_sources if ch in x["word"] and x["source"] != "roadmap_radical"]
    # exact standalone item first, then high-frequency words, then short words.
    matches.sort(key=lambda x: (
        0 if x["word"] == ch else 1,
        x["rank"] if isinstance(x.get("rank"), int) else 999999,
        len(x["word"]),
        source_priority.get(x["source"], 8),
        x["word"],
    ))
    out, seen = [], set()
    for x in matches:
        if x["word"] in seen:
            continue
        seen.add(x["word"])
        out.append({k: x[k] for k in ("word", "reading", "romaji", "meaning", "extra_kanji")})
        if len(out) >= limit:
            break
    return out


catalog = []
seen = set()
next_id = 1
jlpt_by_char = {e["kanji"]: e for e in jlpt}

# Preserve the original beginner-textbook order and rich vocabulary exactly.
for src in core:
    e = dict(src)
    e["id"] = next_id
    next_id += 1
    match = jlpt_by_char.get(e["kanji"])
    e["jlpt_level"] = match.get("level") if match else None
    e["difficulty"] = match.get("difficulty") if match else None
    e["catalog_source"] = "core"
    catalog.append(e)
    seen.add(e["kanji"])

# Then add every JLPT kanji not already represented in the original section.
for src in jlpt:
    ch = src["kanji"]
    if ch in seen:
        continue
    catalog.append({
        "id": next_id,
        "kanji": ch,
        "meaning": src.get("meaning", ""),
        "strokes": None,
        "on_yomi": src.get("on_yomi", ""),
        "kun_yomi": src.get("kun_yomi", ""),
        "vocab": vocab_for_char(ch),
        "jlpt_level": src.get("level"),
        "difficulty": src.get("difficulty"),
        "catalog_source": "jlpt",
    })
    next_id += 1
    seen.add(ch)

# Finally add single-kanji lexical items the app explicitly teaches elsewhere,
# but which are absent from both dedicated kanji datasets. Only direct lexical
# records are accepted: radical-component-only roadmap records are excluded.
extra_candidates = {}
for x in word_sources:
    w = x["word"]
    if not is_single_kanji(w) or w in seen or x["source"] == "roadmap_radical":
        continue
    cur = extra_candidates.get(w)
    if cur is None or source_priority.get(x["source"], 8) < source_priority.get(cur["source"], 8):
        extra_candidates[w] = x

for ch in sorted(extra_candidates):
    x = extra_candidates[ch]
    # A direct word reading is useful as a vocabulary reading, but it is not
    # automatically labelled on-yomi or kun-yomi unless Kotoba's dedicated
    # kanji source says so. Keep on/kun blank rather than inventing metadata.
    catalog.append({
        "id": next_id,
        "kanji": ch,
        "meaning": x.get("meaning", ""),
        "strokes": None,
        "on_yomi": "",
        "kun_yomi": "",
        "vocab": vocab_for_char(ch),
        "jlpt_level": None,
        "difficulty": "medium",
        "catalog_source": "app",
    })
    next_id += 1
    seen.add(ch)

# Reattach words whose textbook heading was lost during PDF extraction.
# The target character is in the expanded catalog, even when absent in core.
catalog_by_char = {k['kanji']: k for k in catalog}
for w in core_extras:
    ch = w['kanji']
    if ch not in catalog_by_char:
        # These lost headings are absent in the old JLPT file too. Meanings
        # agree with the existing 合う/合計 and 向く/向ける vocabulary.
        meaning = {'合': 'fit, join', '向': 'face, turn toward'}[ch]
        parent = {'id': next_id, 'kanji': ch, 'meaning': meaning,
                  'strokes': None, 'on_yomi': '', 'kun_yomi': '',
                  'vocab': vocab_for_char(ch), 'jlpt_level': None,
                  'difficulty': 'medium', 'catalog_source': 'app'}
        catalog.append(parent)
        catalog_by_char[ch] = parent
        next_id += 1
    parent = catalog_by_char[ch]
    lexical = {k: v for k, v in w.items() if k != 'kanji'}
    if not any((v['word'], v['reading'], v['meaning']) == (w['word'], w['reading'], w['meaning']) for v in parent['vocab']):
        parent['vocab'].append(lexical)

out = DATA / "kanji_catalog.json"
with out.open("w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)
    f.write("\n")

from collections import Counter
levels = Counter(e.get("jlpt_level") or "Other" for e in catalog)
sources = Counter(e.get("catalog_source") for e in catalog)
print(f"wrote {out.name}: {len(catalog)} unique kanji")
print("levels:", dict(levels))
print("sources:", dict(sources))
print("entries with vocabulary:", sum(bool(e.get("vocab")) for e in catalog))
