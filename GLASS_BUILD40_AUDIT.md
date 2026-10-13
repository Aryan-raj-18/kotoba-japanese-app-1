# Kotoba Liquid Glass — build 40

Source: build 39, unchanged learning datasets and routing.

## Bug fix

The existing SVG displacement filter was attached to sticky navigation and could render outside its rounded rectangle, causing the translucent rectangle visible behind the header. The real SVG displacement is now limited to contained major content panels, and header/footer instead use native bounded backdrop blur and theme/wallpaper translucency.

## Section coverage

A consistent translucent finish now covers shared shell navigation and main cards in Home, Roadmap, Kana, Kanji, Radicals, Everyday vocabulary, Grammar, Verbs, Flashcards, Practice, JLPT, Speaking, Conversations, Stories, Writing, Japan Explorer, Search, Favorites, Review, Progress, Backup, Settings and supporting forms/modals.

Large repeated grids and word tables use translucent tinted panels without per-row live blur; quiz correctness and handwriting feedback remain distinct and legible. Desktop Settings maintains independent vertical scrolling. Reduced-transparency and low-memory styling are retained.

## Validation

`python test_glass_coverage.py`, `python test_glass_integration.py`, `node test_liquid_glass.cjs` and the existing CI suite. Desktop/mobile browser regression checks also verify no navigation ghost plate, scroll and horizontal overflow. Full Android build should be verified through GitHub Actions.
