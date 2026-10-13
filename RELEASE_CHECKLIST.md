# Kotoba 1.0.0 — source build 47 release handoff

Package `com.kotoba.app` · version 1.0.0 · version code 47 · min API 24 · target API 36. Existing ABI configuration is preserved.

This handoff contains source only. A new APK/AAB has not been compiled, linted, signed or validated in this task. Previous signed-artifact evidence belongs to earlier builds and is archived; it does not certify build 47. Current checks and their scope are recorded in VERIFICATION.json.

## Build and verify

Use the project's configured Python 3.13 / Chaquopy environment, JDK 17, Gradle 8.13 and Android API/build tools 36. Install requirements.txt and jsdom@26.1.0 for DOM tests, then run:

```sh
python sync_android.py
python run_release_checks.py
python smoke_test_android.py
cd android
gradle :app:assembleRelease :app:bundleRelease :app:lintRelease
```

The source-package smoke run in this task used desktop Python 3.12.14, not compiled Chaquopy modules. CI/native builds must exercise their actual Python/runtime versions. The browser scripts in verification require Playwright and Chromium; set KOTOBA_CHROME to the browser executable and use the localhost app on port 5059. They test both glass states, stored preferences, narrow layouts, enlarged CSS text, dialogs and interactive choices. Enlarged CSS text is not a physical-device font-scaling test.

Use the existing private upload keystore/signing properties for a signed build. Signing secrets and runtime learner files are excluded from this source ZIP. Public version stays 1.0.0; increase versionCode beyond any version already uploaded in the publisher's Play Console. Build 47 is the proposed next source version, not evidence of a Play upload.

## Physical device and Play checks

- Install a signed build over the existing compatible installation and confirm progress/preferences survive. Export a backup first, and verify backup/restore using the Android document picker.
- Check offline and online cold/warm opening, subsequent launches, the original intro, native opening OFF/ON glass preference, app resume/recreation and Android Back gestures.
- In Settings toggle Liquid Glass, reopen the app and check every screen, logo frame and dialog. Check readable Japanese glyphs, large system text and narrow screens. Measure scrolling and rendering on a lower-memory phone.
- In Japan Explorer press several cities, scroll the lesson drawer, close it and check zoom/pinch/pan. Check kanji levels, roadmap return position, quiz selection states and speech stopping when changing screens or using the microphone.
- Test actual Japanese TTS, microphone denied/allowed and provider offline behavior. Browser/native-bridge simulations do not establish real audio behavior.
- Check notification permission, rotating kanji, selection scroll, hide/stop, reboot and lock-screen/AOD behavior on the phone.
- Build and verify the final APK/AAB, signing certificate, payload/version, alignment and native 16 KB runtime behavior. Run lint, internal-track installation and the Play pre-launch report before production.
- Complete listing artwork/screenshots, contact, content rating, audience/app access and accurate Data safety. Preserve learning-content attribution and distribution permissions.

## Privacy policy

The previous handoff supplied `https://kotoba-privacy-policy.swiftlamb64.chatgpt.site` as the public policy URL and `Aryanrajr868@gmail.com` as contact. The in-app `/privacy` page and standalone privacy-policy.html remain. Verify the public URL is reachable and its text matches actual publisher practices before submitting. No site publishing or Play Console change was performed in this task. Optional system speech or cloud flows must be reflected accurately in the publisher's declarations.

Earlier release notes and evidence are retained under verification/previous-build46-input/. The app content and features were preserved.
