# Kotoba v1.0.0 — layout fix (asset build 37)

- Desktop: settings dropdown now has a viewport-bounded internal scroll area,
  usable with mouse wheel, trackpad, touch and keyboard while the page behind
  it stays locked. Its full list of controls remains accessible.
- Mobile: the glass header and five-tab bottom navigation extend nearly from
  edge to edge, with 4px visual gutters rather than 8–10px. Main content gains
  horizontal space and the reserved bottom navigation clearance is reduced.
- Native Android status/navigation/cutout insets are deliberately unchanged;
  content does not overlap system controls. Wallpaper, glass mode, lessons,
  speech, and routing were not modified.
- Cache version 37 refreshes styles in both browser/PWA and Android WebView.
- Changes mirrored to the Android embedded Python/static bundle.
