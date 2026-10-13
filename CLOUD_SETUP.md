# Kotoba cloud sync activation

The delivered build has **no configured cloud backend**. It opens and saves progress locally with or without internet. The cloud integration and controls are implemented, but no production progress has been uploaded and no live Firebase service/rules test has been performed.

## Publisher setup

1. Use a Firebase project owned by the publisher. Enable Firebase Authentication's Anonymous provider. Create a Cloud Firestore **Standard / Native mode** database named `(default)` in the region the publisher chooses.
2. Deploy `cloud/firestore.rules` and `cloud/firestore.indexes.json` to that project. The rules restrict each installation identity to its own documents. The large progress payload is not indexed. Never use public read/write test-mode rules.
3. Put the project's public Web API key and project ID in `cloud/firebase-config.json`, and set `enabled` to `true`. A Firebase Web app configuration supplies these two values. They are public client configuration; **do not bundle a service-account key, administrator credentials, private signing key or existing user's refresh token**.
4. Review API restrictions for the Firebase REST clients, anonymous-auth abuse protection, quotas/budget alerts and the publisher's data retention process. Update the privacy policy with the actual project/operator and practices. Declare optional cloud progress/preferences and identifiers accurately in Play Data safety. These Console settings cannot be completed without project access.
5. Run `python sync_android.py`, increase the Android version code, and build/sign the APK and AAB with the preserved upload key. Set up the live service before enabling the published configuration; a client API key alone is not a functioning backend.
6. Run the live and phone checks below before publishing. Tests in `test_cloud_sync.py` simulate the provider; they do not prove deployed Firebase rules, network certificates, quotas or real cloud availability.

## App behavior

- Local data is authoritative until a cloud operation succeeds. Startup and lesson saving never wait for Firebase, Wi-Fi or mobile data.
- Cloud sync is optional and off initially. When enabled, an anonymous identity is created automatically; there is no signup/login screen. Cloud credentials stay in private learner storage and are excluded from normal progress backups, APK/AAB assets and the source ZIP.
- Successful learning mutations queue the latest selected study-data snapshot durably. Reconnection retries run in a separate daemon worker while the app process runs. Unchanged progress does not upload duplicate copies. Android may stop the process; pending progress is retried after reopening. This is not a guaranteed background scheduler when the app is force-stopped.
- Cloud progress includes learner history/SRS, mistakes, favorites, roadmap, deck progress, streak dates and selected preferences. Wallpapers, recordings, reminder schedules, old passwords and private connection credentials are excluded. Standard file backups remain available offline, or can be saved to a cloud drive through the system picker.
- Each installation begins separately. **Save private cloud key** exports a separate credential file. **Connect with this key** on another installation verifies the identity online and joins the same cloud study profile. This is also how a user reconnects after reinstalling. The key grants access to that anonymous identity's progress; keep it private. Ordinary progress backups never contain this key.
- Connecting explicitly uses the existing cloud copy and keeps the previous local copy in `before_restore_*.json`. Subsequent clean devices receive changed cloud progress automatically. If both devices make changes offline, both copies are retained and the user explicitly chooses which copy to keep. No claim of automatic event-by-event merging is made.
- Firestore update-time/existence preconditions protect uploads against races. Failed/expired identities are refreshed or reported; they are never silently replaced with a new anonymous user. Invalid cloud payloads are rejected before changing local progress.
- Delete cloud copy requires confirmation. Offline deletion is queued durably; once it succeeds sync turns off and local progress remains. Other connected devices do not silently recreate a removed cloud copy. Uninstalling or clearing app storage does not itself delete cloud data. The publisher must document retention and support deletion requests where the user has lost their key.
- A progress snapshot is limited to 750,000 UTF-8 bytes to stay below the Firestore document limit. Larger progress remains local and the app offers file backup rather than discarding records. Production needs a chunked/event model if real histories exceed this bound.

## Required live checks

1. Fresh install in airplane mode: home, N4 kanji, search, practice and backup must open; record progress and restart. Repeat with mobile data and Wi-Fi enabled, and toggle connectivity during practice.
2. Enable cloud sync online, verify an anonymous UID and its protected progress document, then turn off internet, study, force-stop and reopen. Confirm the last offline changes upload after reconnecting.
3. Save a private key; connect a second phone. Verify cloud progress downloads and prior local data remains in the recovery backup. Study on each clean device and check automatic transfer. Make conflicting offline changes on both and confirm neither copy is silently overwritten.
4. Try an invalid/revoked key, wrong project, invalid payload, permission-denied rules, service failure and an expired ID token. Local studying/saving must keep working.
5. Attempt reading/writing another UID's document, listing unrelated documents and anonymous unauthenticated access. Deployed rules must deny them. The REST client uses a Firebase user ID token, not an administrator token.
6. Delete the cloud copy offline and reopen online. Verify deletion succeeds, local progress stays and the other phone does not resurrect the removed copy. Verify reset, local study-record deletion and ordinary backup/restore retain their documented behavior.
7. Check that data is absent from release packages, signing/source archives, normal backups, logs and feedback, except user-authorized cloud progress and separately exported private keys.

Official implementation references:
- https://firebase.google.com/docs/reference/rest/auth
- https://firebase.google.com/docs/firestore/use-rest-api
- https://firebase.google.com/docs/rules/basics
- https://docs.cloud.google.com/firestore/docs/reference/rest/v1/projects.databases.documents/patch
