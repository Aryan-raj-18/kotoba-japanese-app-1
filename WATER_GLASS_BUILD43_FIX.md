# Build 43 — Water Glass toggle and JLPT setup artifact

- The existing Settings switch has been renamed **Water Glass effect**. Its state persists in localStorage (`kotoba:liquid-glass`).
- OFF now disables glass backdrop filters throughout the shared component styling, not just the header/footer.
- JLPT exam setup/results use a single rounded stable tint without GPU backdrop compositing, to avoid rectangular plates on Windows Chromium. Quiz wrappers stay transparent.
- Android and desktop style/template copies synchronized; offline cache bumped to 43.
- Learning data and app release version 1.0.0 unchanged.
