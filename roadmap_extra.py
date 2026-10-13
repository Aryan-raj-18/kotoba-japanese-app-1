"""Restored original kana row, dakuten and combined-sound guidance."""
import unicodedata

_ROW_NAMES = {"vowel": "vowel (A)", "k": "K", "s": "S", "t": "T", "n": "N", "h": "H", "m": "M", "y": "Y",
              "r": "R", "w": "W", "n-special": "N", "g": "G", "z": "Z", "d": "D", "b": "B", "p": "P"}

def kana_explain(script, entry, data):
    """Explanation shown after a kana quiz answer."""
    c, r, t, g = entry["char"], entry["romaji"], entry["type"], entry["group"]
    name = "hiragana" if script == "hiragana" else "katakana"
    if t == "basic":
        row = [x for x in data if x["type"] == "basic" and x["group"] == g]
        rowtxt = " ".join(x["char"] for x in row) + " (" + " ".join(x["romaji"] for x in row) + ")"
        return f"{c} is {name} for \u201c{r}\u201d. It sits in the {_ROW_NAMES.get(g, g)} row: {rowtxt}."
    if t == "dakuten":
        base = unicodedata.normalize("NFD", c)[0]
        b = next((x for x in data if x["char"] == base), None)
        mark = "a small circle (handakuten \u309c)" if g == "p" else "two small marks (dakuten \u309b)"
        if b:
            return f"{c} is {b['char']} ({b['romaji']}) plus {mark}, which changes the sound to \u201c{r}\u201d."
        return f"{c} is {name} for \u201c{r}\u201d (a voiced sound)."
    first, small = c[0], c[1:]
    b = next((x for x in data if x["char"] == first), None)
    if b:
        return f"{c} = {first} ({b['romaji']}) + small {small}: the two blend into one syllable, \u201c{r}\u201d."
    return f"{c} is {name} for \u201c{r}\u201d."
