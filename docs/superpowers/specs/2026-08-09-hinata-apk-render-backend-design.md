# Hinata Android APK → Render Backend — Design Doc

Date: 2026-08-09

## Problem

The Android APK for Hinata AI must connect to the production backend at
`https://hinata-m93w.onrender.com`. Currently:

1. The Flutter app source (`flutter_app/lib/main.dart`) defaults to
   `http://localhost:8000` — dead on a real phone.
2. The shipped APKs (`web/hinata-android*.apk`) are a legacy hand-built Kotlin
   WebView wrapper pointing at a dead LAN IP (`http://10.99.189.237:2027`),
   not the Flutter source.
3. The host machine is ARM64 Linux; Flutter publishes no official ARM64 Linux
   SDK, so local `flutter build apk` is impossible. The repo already has a
   GitHub Actions workflow (`.github/workflows/flutter-build.yml`) that builds
   on x86_64 with Flutter 3.29.0.
4. The existing `flutter_app/android/keystore/hinata-keystore.jks` was
   publicly exposed (password `hinata123`) and is documented as compromised
   in `docs/SECURITY.md` / `docs/AUDIT.md`.

## Goal

Ship a release APK (`com.hinata.ai`) that loads `https://hinata-m93w.onrender.com`
in its WebView, built from the Flutter source via the existing CI workflow,
signed with a brand-new keystore.

## Approach

Rebuild from Flutter source via GitHub Actions (user-approved over patching
the legacy APK), signed with a freshly generated keystore (user-approved over
the compromised one).

## Changes

### 1. `flutter_app/lib/main.dart`

- Change `BackendConfig.defaultUrl` from `http://localhost:8000` to
  `https://hinata-m93w.onrender.com`.
- Keep the SharedPreferences override mechanism
  (`BackendConfig.getUrl()` / `setUrl()`) — harmless and future-proof.
- Fix the stale comment that references a "Settings > Backend URL" UI, which
  does not exist in the app.

### 2. Signing — fresh keystore

- Generate `hinata-release.jks` via `keytool` (RSA 2048, validity 10000 days,
  alias `hinata`).
- Store the keystore **outside the repository** (e.g. `/root/hinata-release-keystore.jks`)
  per `docs/SECURITY.md` ("Store the generated keystore in a secure location
  outside the repository").
- Generate strong random keystore password and key password at build time.
- Provide the user a copy-paste block for the four GitHub secrets.

### 3. `.github/workflows/flutter-build.yml`

- Add a "materialize keystore" step: decode the `KEYSTORE_BASE64` secret to a
  file on the runner.
- Pass `KEYSTORE_PATH`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD` env
  vars to the `flutter build apk --release` step.
- No change to `flutter_app/android/app/build.gradle` — its release signing
  config already reads exactly these environment variables.
- Result: properly release-signed APK (removes the current debug-key
  fallback).

### 4. Build & delivery

1. User adds 4 GitHub secrets: `KEYSTORE_BASE64` (base64 of the .jks),
   `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD`. (Creating secrets needs a
   token the agent does not have; this is a manual user step.)
2. Push to `master` — triggers `flutter-build.yml` on `flutter_app/**` paths.
   CI runs `flutter build apk --release` (Flutter 3.29.0 stable, Java 17,
   x86_64 ubuntu-latest).
3. Download the `app-release.apk` artifact.
4. Verify:
   - `apksigner verify --print-certs` → new certificate, `debuggable=false`.
   - The string `https://hinata-m93w.onrender.com` is present in the built
     DEX / `libapp.so`.

## Non-Goals

- No version bump (`1.0.0+1` stays).
- No launcher icon / theme changes.
- No changes to the web app or to the legacy `web/hinata-android*.apk` files.
- No Play Store publishing.

## Risks / Dependencies

- GitHub push auth is unproven (anonymous `ls-remote` succeeds on public
  repos); the user must confirm push access or push the commit themselves.
- CI builds on the default runner; the workflow has no keystore secrets yet —
  the user must add them before the first push.
- New signing key means the new APK cannot auto-update over APKs signed with
  the old compromised key (acceptable — the old APKs point to a dead server).
