#!/usr/bin/env python3
"""
Smoke-test the *packaged* Android copy of the app, the way the phone runs it.
============================================================================

`python app.py` on a desktop proves nothing about the APK. On the phone:
  * Chaquopy imports `kotoba_app.app` from the package root - neither the
    project folder nor the kotoba_app folder is on sys.path, so a bare
    `import some_sibling` fails;
  * the interpreter is Python 3.13 (Chaquopy 17 default), which rejects syntax
    that newer Pythons accept (e.g. a backslash inside an f-string expression).
Both made the app crash on launch while every desktop check passed.

So this script (run it with a Python 3.13 interpreter, as CI does):
  1. recreates the phone's import environment and imports kotoba_app.app
  2. requests every page and API, with every real ID in the data
  3. exercises the POST endpoints with realistic bodies
  4. checks run_server() is safe to call repeatedly (Android recreates the
     Activity while the server thread lives on; a second bind used to kill
     the app)

Run after `python sync_android.py`:   python smoke_test_android.py
Exits non-zero on any failure.
"""
import os
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
PY_ROOT = Path(os.environ.get("KOTOBA_TEST_PACKAGE", str(ROOT / "android" / "app" / "src" / "main" / "python")))

sys.path[:] = [str(PY_ROOT)] + [
    p for p in sys.path if Path(p or ".").resolve() not in (ROOT, PY_ROOT / "kotoba_app")
]
os.chdir(tempfile.mkdtemp())
os.environ["KOTOBA_DATA_DIR"] = tempfile.mkdtemp(prefix="kotoba-smoke-")

failures = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (f"  {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


print("Python", sys.version.split()[0])
try:
    import kotoba_app.app as K
    check("import kotoba_app.app", True)
except Exception as e:  # noqa: BLE001
    check("import kotoba_app.app", False, repr(e))
    raise SystemExit(1)

# Runtime state (progress, users, ...) goes to a temp folder, not into data/.
tmp = Path(tempfile.mkdtemp())
for name in dir(K):
    val = getattr(K, name)
    if name.isupper() and name.endswith(("_FILE", "_PATH")) and isinstance(val, Path):
        setattr(K, name, tmp / val.name)

K.app.config["PROPAGATE_EXCEPTIONS"] = False
client = K.app.test_client()

if os.environ.get("KOTOBA_TEST_COMPILED") == "1":
    check("final AAB imports compiled Python modules", str(K.__file__).endswith(".pyc") and not list(PY_ROOT.rglob("*.py")))
check("login/signup/logout routes are absent", all(client.get(path).status_code == 404 and client.post(path).status_code == 404 for path in ("/login", "/signup", "/logout")))

# Pages that legitimately answer 4xx without parameters.
EXPECTED_400 = {"/api/jlpt_quiz", "/api/jlpt_exam_quiz", "/api/kanji_quiz", "/api/search", "/api/jlpt_mock"}

bad = []
count = 0


def hit(url, ok_codes=()):
    global count
    count += 1
    try:
        r = client.get(url)
    except Exception as e:  # noqa: BLE001
        bad.append((url, repr(e)))
        return None
    if r.status_code >= 400 and r.status_code not in ok_codes and not (
            r.status_code == 400 and url.split("?")[0] in EXPECTED_400):
        bad.append((url, r.status_code))
    return r


for rule in sorted(K.app.url_map.iter_rules(), key=str):
    if "GET" in rule.methods and "<" not in str(rule) and rule.endpoint != "static":
        hit(str(rule),ok_codes=(403,) if rule.endpoint=="native_bootstrap" else ())


def ids(data, key="id"):
    return [x[key] for x in data if isinstance(x, dict) and key in x]


def listify(data, key):
    return data if isinstance(data, list) else data.get(key, [])


check("restored rich kanji coverage", len(K.KANJI_DATA) == 408, str(len(K.KANJI_DATA)))
check("restored full kanji catalog", len(K.KANJI_CATALOG) >= 2103, str(len(K.KANJI_CATALOG)))
check("full Kanji catalog IDs unique", len({e["id"] for e in K.KANJI_CATALOG}) == len(K.KANJI_CATALOG))
check("full Kanji catalog characters unique", len({e["kanji"] for e in K.KANJI_CATALOG}) == len(K.KANJI_CATALOG))
check("full Kanji catalog contains every JLPT kanji", {e["kanji"] for e in K.JLPT_KANJI}.issubset({e["kanji"] for e in K.KANJI_CATALOG}))

# Mobile setup/presentation regressions: daily goal belongs in Settings, while
# wallpaper uploads must pass through the drag/zoom framing editor.
packaged_root = PY_ROOT / "kotoba_app"
index_template = (packaged_root / "templates" / "index.html").read_text(encoding="utf-8")
ui_shell_js = (packaged_root / "static" / "js" / "ui-shell.js").read_text(encoding="utf-8")
check("first-run onboarding no longer embeds Daily goal controls", 'id="goal-chips"' not in index_template and 'class="onboarding-goal"' not in index_template)
check("wallpaper upload has drag/zoom framing editor", "Choose the visible area" in ui_shell_js and "wallpaper-crop-zoom" in ui_shell_js and "wallpaper-reposition" in ui_shell_js)
style_css = (packaged_root / "static" / "css" / "style.css").read_text(encoding="utf-8")
ui_shell_css = (packaged_root / "static" / "css" / "ui-shell.css").read_text(encoding="utf-8")
japan_js = (packaged_root / "static" / "js" / "japan_explorer.js").read_text(encoding="utf-8")
check("Japan drawer hides mobile bottom navigation", "body.japan-drawer-open .kotoba-bottom-nav" in ui_shell_css)
check("Japan mobile lesson actions are full-width", ".japan-lesson-actions{display:grid;grid-template-columns:1fr" in style_css)
check("Japan mini quiz scrolls into visible drawer area", "block:'start'" in japan_js and "japan-mini-quiz" in japan_js)
base_template = (packaged_root / "templates" / "base.html").read_text(encoding="utf-8")
voice_js = (packaged_root / "static" / "js" / "voice-search.js").read_text(encoding="utf-8")
intro_js = (packaged_root / "static" / "js" / "intro.js").read_text(encoding="utf-8")
search_template = (packaged_root / "templates" / "search.html").read_text(encoding="utf-8")
check("opening intro is wired into Home", 'id="kotoba-intro"' in base_template and "kotoba:intro:done" in intro_js)
check("global voice search is present", 'id="voice-search-global"' in base_template and "KotobaVoiceSearch" in voice_js)
check("voice search covers local filter inputs", ".filter-input" in voice_js and "voice-inline-btn" in voice_js)
check("Search results page has a mobile-refinable search form", "search-page-form" in search_template and 'name="q"' in search_template)
main_activity = (ROOT / "android" / "app" / "src" / "main" / "java" / "com" / "kotoba" / "app" / "MainActivity.kt").read_text(encoding="utf-8")
manifest = (ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
check("Android native voice-recognition bridge is present", "KotobaVoiceRecognitionNative" in main_activity and "SpeechRecognizer.createSpeechRecognizer" in main_activity)
check("Android speech-recognition service is discoverable", "android.speech.RecognitionService" in manifest and "android.permission.RECORD_AUDIO" in manifest)
for i in ids(K.KANJI_CATALOG):
    hit(f"/kanji/{i}")
for i in ids(K.KANJI_DATA)[:40]:
    hit(f"/api/practice/quiz/{i}")
for r in K.RADICALS:
    hit(f"/radicals/{r['id']}")
for lvl in K.JLPT_LEVELS:
    hit(f"/jlpt/{lvl}")
    hit(f"/jlpt/{lvl}/practice")
    hit(f"/api/jlpt_quiz?level={lvl}")
    if K.JLPT_EXAM_QUESTIONS.get(lvl):
        hit(f"/jlpt/{lvl}/exam-practice")
        hit(f"/api/jlpt_exam_quiz?level={lvl}&count=10")
        hit(f"/jlpt/{lvl}/mock")
        hit(f"/api/jlpt_mock?level={lvl}")
for g in K.GRAMMAR_DATA:
    hit(f"/grammar/{g['id']}")
for game in ("match", "audio", "kana", "verbs", "sentence"):
    for difficulty in ("easy", "medium", "hard"):
        hit(f"/api/games/deck?game={game}&difficulty={difficulty}")
for i in range(len(K.EVERYDAY_WORDS)):
    hit(f"/api/everyday/{i}")
for c in listify(K.CONVERSATIONS_DATA, "conversations"):
    hit(f"/conversations/{c['id']}")
for s in listify(K.STORIES_DATA, "stories"):
    hit(f"/stories/{s['id']}")
for i in range(len(K.VERBS_DATA)):
    hit(f"/api/verb/{i}")
# Every roadmap chapter, several times: quizzes are built randomly, and the
# Hiragana/Katakana chapters lazily import roadmap_extra.
for ch in K.ROADMAP_CHAPTER_ORDER:
    for _ in range(3):
        hit(f"/roadmap/{ch}")
check("Japan Explorer has all 47 places", len(K.JAPAN_PLACES) == 47, str(len(K.JAPAN_PLACES)))
check("Japan Explorer place IDs unique", len({p["id"] for p in K.JAPAN_PLACES}) == 47)
check("Japan Explorer has four train routes", len(K.JAPAN_EXPLORER_DATA.get("train_routes", [])) == 4)
check("Japan Explorer has four seasons", set(K.JAPAN_EXPLORER_DATA.get("seasons", {}).keys()) == {"spring","summer","autumn","winter"})
check("Japan Explorer has dialect data for every region", all(r in K.JAPAN_EXPLORER_DATA.get("dialects", {}) for r in K.JAPAN_EXPLORER_DATA.get("regions", [])))
for route in K.JAPAN_EXPLORER_DATA.get("train_routes", []):
    check(f"Japan train route {route.get('id')} uses known stops", len(route.get("stops", [])) >= 2 and all(x in K.JAPAN_PLACE_BY_ID for x in route.get("stops", [])))
for p in K.JAPAN_PLACES:
    check(f"Japan place {p['id']} has level words", all(p.get("level_words",{}).get(l) for l in ("beginner","intermediate","advanced")))
    check(f"Japan place {p['id']} has situation levels", all(p.get("situations",{}).get(l,{}).get("correct") for l in ("beginner","intermediate","advanced")))
    check(f"Japan place {p['id']} has seasonal guidance", bool(p.get("best_seasons")))
for deck in ("kanji", "vocab", "verbs", "radicals", "hiragana", "katakana",
             "N5", "N4", "N3", "N2", "N1"):
    hit(f"/api/flashcards?deck={deck}", ok_codes=(404,))
    hit(f"/api/flashcards_mcq?deck={deck}", ok_codes=(404,))
# Regression check: the Review Cards UI exposes 60, so the API must not silently cap it at 40.
r60 = client.get("/api/flashcards_mcq?deck=vocab&difficulty=all&count=60")
q60 = (r60.get_json() or {}).get("questions", []) if r60.status_code == 200 else []
check("Review Cards supports a 60-card session", r60.status_code == 200 and len(q60) == 60, str(len(q60)))

# Expanded Kanji browser/practice/writing should all expose the same catalog.
kpool = client.get("/api/kanji_pool")
kpool_data = kpool.get_json() if kpool.status_code == 200 else []
check("Writing Practice exposes full Kanji catalog", kpool.status_code == 200 and len(kpool_data) == len(K.KANJI_CATALOG), str(len(kpool_data)))
kquiz = client.get("/api/kanji_quiz?level=all&count=60")
kquiz_data = (kquiz.get_json() or {}).get("questions", []) if kquiz.status_code == 200 else []
check("Kanji Practice safely limits a large request to available unique kanji", kquiz.status_code == 200 and len(kquiz_data) == min(60,len(K.KANJI_CATALOG)), str(len(kquiz_data)))
for q in ("water", "水", "みず", "mizu", "氵", "eat", "食べる", "a", "日本", "Tokyo", "京都", "Hokkaido", "possessive", "The Cat and the Rain", "Introducing Yourself"):
    hit(f"/api/search?q={q}")
    hit(f"/search?q={q}")

check(f"{count} GET requests all OK", not bad, str(bad[:6]))

# --- POST endpoints with realistic bodies --------------------------------
posts = []
first_ch = K.ROADMAP_CHAPTER_ORDER[0]
for url, body in (
    ("/api/streak/mark", {}),
    ("/api/progress/mark", {"deck": "kanji", "item_id": 1, "known": True}),
    ("/api/roadmap/start", {"level": "beginner", "goal": 10}),
    ("/api/roadmap/start", {"start_chapter": first_ch}),
    ("/api/roadmap/complete", {"chapter_id": first_ch, "score": 10, "total": 10}),
    ("/api/roadmap/complete", {"chapter": first_ch, "score": 10, "total": 10}),
    ("/api/practice/new_session", {}),
    ("/api/feedback", {"message": "hello", "rating": 5}),
    ("/api/learner/record", {"kind":"smoke","id":"one","front":"一","answer":"one","correct":True,"quality":4}),
    ("/api/learner/action", {"action":"audio","amount":1}),
    ("/api/favorites/toggle", {"item":{"kind":"vocab","id":"水","front":"水","meaning":"water"}}),
    ("/api/favorites/list", {"name":"Smoke list"}),
    ("/api/placement/save", {"score":70,"breakdown":{"N5":{"right":4,"total":5},"N4":{"right":3,"total":4}}}),
    ("/api/jlpt_mock/save", {"level":"N5","score":3,"total":5,"categories":{"Grammar":{"right":3,"total":5}}}),
    ("/api/japan/visit", {"id":"tokyo"}),
):
    try:
        r = client.post(url, json=body)
        if r.status_code >= 500:
            posts.append((url, r.status_code))
    except Exception as e:  # noqa: BLE001
        posts.append((url, repr(e)))
check("POST endpoints answer without a server error", not posts, str(posts[:5]))
backup = client.get("/api/backup/data")
check("learner backup exports", backup.status_code == 200 and backup.get_json().get("format") == "kotoba-backup-v1")
if backup.status_code == 200:
    restored = client.post("/api/backup/data", json=backup.get_json())
    check("learner backup restores", restored.status_code == 200, str(restored.status_code))
# the home page after onboarding/progress state exists
check("home page renders after progress is recorded", client.get("/").status_code == 200)

# --- run_server() must be idempotent -------------------------------------
results = {}


def call(name):
    try:
        K.run_server()
        results[name] = "returned"
    except BaseException as e:  # noqa: BLE001  (SystemExit included on purpose)
        results[name] = "RAISED " + repr(e)


first = threading.Thread(target=call, args=("first",), daemon=True)
first.start()
time.sleep(1.5)
dupes = [threading.Thread(target=call, args=(f"dupe{i}",), daemon=True) for i in range(3)]
for t in dupes:
    t.start()
for t in dupes:
    t.join(5)
check("repeat run_server() calls return without raising",
      all(v == "returned" for k, v in results.items() if k.startswith("dupe")) and len(results) == 3,
      str(results))
try:
    status = urllib.request.urlopen("http://127.0.0.1:5000/", timeout=5).status
    check("server still serving after repeat calls", status == 200, str(status))
except Exception as e:  # noqa: BLE001
    check("server still serving after repeat calls", False, repr(e))

print()
if failures:
    print(f"{len(failures)} check(s) FAILED")
    raise SystemExit(1)
print("All smoke checks passed.")
raise SystemExit(0)
