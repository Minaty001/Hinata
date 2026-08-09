# Hinata APK → Render Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a release APK (`com.hinata.ai`, version `1.0.0+1`) that loads `https://hinata-m93w.onrender.com` in its WebView, built from the Flutter source via GitHub Actions, signed with a freshly generated keystore.

**Architecture:** The app is a Flutter WebView wrapper (`flutter_app/`) around the Hinata web backend. Its backend URL is a Dart string constant in `BackendConfig.defaultUrl` (with a SharedPreferences override). Building requires x86_64 Flutter, which is unavailable on this ARM64 host, so the build runs in the repo's existing GitHub Actions workflow. Release signing is driven by the `KEYSTORE_PATH` / `KEYSTORE_PASSWORD` / `KEY_ALIAS` / `KEY_PASSWORD` env vars already read by `flutter_app/android/app/build.gradle`.

**Tech Stack:** Flutter 3.29.0 (stable, CI), Java 17 (CI), GitHub Actions (`subosito/flutter-action@v2`), `keytool` (local keystore generation), `apksigner` (local verification).

## Global Constraints

- Backend URL, verbatim: `https://hinata-m93w.onrender.com`
- App id `com.hinata.ai`; `minSdk 28`, `targetSdk 35` (already configured — do not change)
- Version stays `1.0.0+1` (no bump)
- Keystore MUST live outside the repository; NEVER commit `.jks` or base64 blobs (per `docs/SECURITY.md`)
- Existing `flutter_app/android/keystore/hinata-keystore.jks` is compromised — do NOT use it
- No local Flutter SDK on this ARM64 host: Flutter commands run only in CI; local verification is static (grep/read) or via `apksigner`
- Git pushes and commits require explicit user approval at execution time

---

### Task 1: Point the app at the Render backend URL

**Files:**
- Modify: `flutter_app/lib/main.dart:10-28` (the `BackendConfig` class)
- Test: `flutter_app/test/widget_test.dart` (append a group)

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `BackendConfig.defaultUrl` must equal `'https://hinata-m93w.onrender.com'`; `getUrl()` / `setUrl()` unchanged. Task 4 verifies the built APK contains this exact string.

- [ ] **Step 1: Write the failing test**

Append to `flutter_app/test/widget_test.dart` (after the existing `Device Control MethodChannel Tests` group):

```dart
  group('BackendConfig', () {
    test('default URL points to the Render production backend', () {
      expect(BackendConfig.defaultUrl, 'https://hinata-m93w.onrender.com');
    });
  });
```

- [ ] **Step 2: Verify it fails**

Flutter is not available locally (ARM64 host, no Flutter SDK). Verification is deferred to CI: Task 3 adds `flutter test` to the workflow, and Task 4 confirms it passes. Locally, confirm the current value is NOT the target:

Run: `grep -n "defaultUrl" flutter_app/lib/main.dart`
Expected: current value `http://localhost:8000` — the new test would fail against it.

- [ ] **Step 3: Update the default URL**

In `flutter_app/lib/main.dart`, replace the `BackendConfig` doc comment + constant:

```dart
/// Manages backend URL configuration.
/// The URL is persisted in SharedPreferences and can be changed in Settings.
/// IMPORTANT: Never hardcode production URLs or emulator-only addresses here.
class BackendConfig {
  static const String _prefKey = 'backend_url';
  // Default is localhost for local development.
  // On a real device, open Settings and enter your server's address.
  static const String defaultUrl = 'http://localhost:8000';
```

with:

```dart
/// Manages backend URL configuration.
/// The URL is persisted in SharedPreferences and can be changed in Settings.
/// IMPORTANT: Never hardcode emulator-only addresses here.
class BackendConfig {
  static const String _prefKey = 'backend_url';
  // Default is the production backend hosted on Render.
  static const String defaultUrl = 'https://hinata-m93w.onrender.com';
```

Keep `getUrl()` and `setUrl()` exactly as they are (the SharedPreferences override stays functional).

- [ ] **Step 4: Verify the change statically**

Run: `grep -n "defaultUrl\|onrender.com" flutter_app/lib/main.dart`
Expected: line `static const String defaultUrl = 'https://hinata-m93w.onrender.com';` and no remaining `localhost` reference.

- [ ] **Step 5: Commit**

```bash
git add flutter_app/lib/main.dart flutter_app/test/widget_test.dart
git commit -m "fix(android): point APK WebView at Render production backend"
```

---

### Task 2: Generate a fresh release keystore + GitHub secrets block

**Files:**
- Create (OUTSIDE the repo — never inside `/root/Hinata`): `/root/hinata-release-keystore.jks`, `/root/hinata-release-keystore.b64`
- Modify: nothing in the repo

**Interfaces:**
- Consumes: nothing
- Produces: keystore file, its base64, and four secret values consumed by Task 3's workflow env vars: `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD` (alias = `hinata`)

- [ ] **Step 1: Generate random passwords**

```bash
KS_PASS=$(openssl rand -base64 24 | tr -d '=+/')
KEY_PASS=$(openssl rand -base64 24 | tr -d '=+/')
echo "KS_PASS=$KS_PASS"   # keep for the secrets block below
echo "KEY_PASS=$KEY_PASS"
```

- [ ] **Step 2: Create the keystore with keytool**

```bash
keytool -genkeypair -v \
  -keystore /root/hinata-release-keystore.jks \
  -alias hinata \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass "$KS_PASS" -keypass "$KEY_PASS" \
  -dname "CN=Hinata AI, OU=Mobile, O=Hinata, L=New Delhi, ST=Delhi, C=IN"
```

Expected: `keytool` prints a confirmation and the file exists (`ls -l /root/hinata-release-keystore.jks`).

- [ ] **Step 3: Encode the keystore for GitHub secrets**

```bash
base64 -w 0 /root/hinata-release-keystore.jks > /root/hinata-release-keystore.b64
wc -c /root/hinata-release-keystore.b64   # ~3700 bytes, well under GitHub's 48 KB secret limit
```

- [ ] **Step 4: Verify the keystore is readable**

```bash
keytool -list -keystore /root/hinata-release-keystore.jks -storepass "$KS_PASS" -alias hinata
```

Expected: shows the RSA key entry for alias `hinata`.

- [ ] **Step 5: Print the secrets block for the user**

Print the four values and tell the user to add them at GitHub → Settings → Secrets and variables → Actions → New repository secret:

```
KEYSTORE_BASE64  = <contents of /root/hinata-release-keystore.b64>
KEYSTORE_PASSWORD = <KS_PASS>
KEY_ALIAS         = hinata
KEY_PASSWORD      = <KEY_PASS>
```

Do NOT write passwords into any repo file. (No commit in this task.)

---

### Task 3: Wire release signing + tests into the CI workflow

**Files:**
- Modify: `.github/workflows/flutter-build.yml`

**Interfaces:**
- Consumes: Task 2 secrets (`KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD`) — the file is inert until the user adds them to the repo
- Produces: a workflow whose `flutter build apk --release` step signs with the release keystore when secrets exist (debug-key fallback preserved otherwise), and which runs `flutter test` before building. Task 4 consumes the `app-release.apk` artifact.

- [ ] **Step 1: Read the current workflow**

Read `.github/workflows/flutter-build.yml` to confirm its exact current content (it triggers on push to `master` for `flutter_app/**`, runs `flutter pub get` then `flutter build apk --release`, and uploads the artifact).

- [ ] **Step 2: Add a test run + keystore materialization + signing env**

Replace the `- run: flutter pub get` through `- run: flutter build apk --release` block with:

```yaml
      - run: flutter pub get

      - run: flutter test

      - name: Materialize release keystore
        if: ${{ secrets.KEYSTORE_BASE64 != '' }}
        shell: bash
        run: |
          echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 -d > "${{ github.workspace }}/hinata-release.jks"
          ls -l "${{ github.workspace }}/hinata-release.jks"

      - name: Build release APK
        run: flutter build apk --release
        env:
          KEYSTORE_PATH: ${{ secrets.KEYSTORE_BASE64 != '' && github.workspace + '/hinata-release.jks' || '' }}
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
```

Keep the existing `Upload APK` step unchanged.

- [ ] **Step 3: Verify the YAML is valid**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/flutter-build.yml')); print('YAML OK')"`
Expected: `YAML OK`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/flutter-build.yml
git commit -m "ci(android): run flutter test and release-sign the APK via secrets"
```

---

### Task 4: Push to master and trigger the CI build

**Files:** none

**Interfaces:**
- Consumes: Task 1 + Task 3 commits, Task 2 secrets (must be added by user before this step)
- Produces: a GitHub Actions run on `master`; on success, artifact `hinata-android-release` containing `app-release.apk`

- [ ] **Step 1: Confirm user added the four secrets**

Ask the user to confirm the four GitHub secrets (Task 2, Step 5) are configured. If not, wait — otherwise CI signs with the debug key.

- [ ] **Step 2: Get explicit approval for the push, then push**

The push mutates the shared GitHub repository — ask the user to approve this exact action first.

```bash
git push origin master
```

Expected: push succeeds; the `flutter-build.yml` workflow starts automatically (paths: `flutter_app/**`).

- [ ] **Step 3: Watch the workflow run**

The workflow is triggered on push; check the run on GitHub (Actions tab). Expected green: `flutter test` passes (verifies Task 1's test), the keystore materializes, `flutter build apk --release` succeeds with the release signing config, and the artifact uploads.

---

### Task 5: Download and verify the APK

**Files:**
- Create (OUTSIDE the repo): `/root/hinata-android-release.apk`

**Interfaces:**
- Consumes: the `hinata-android-release` artifact from Task 4
- Produces: a verified release APK at `/root/hinata-android-release.apk`

- [ ] **Step 1: Obtain the APK**

Options (pick the one that works with available auth):
- `gh` CLI is NOT installed. If the user provides a GitHub token with `actions:read` scope: `curl -H "Authorization: Bearer $TOKEN" -L "https://api.github.com/repos/Minaty001/Hinata/actions/artifacts"` → find the latest artifact id → download via `https://api.github.com/repos/Minaty001/Hinata/actions/artifacts/<id>/zip`.
- Otherwise: ask the user to download `hinata-android-release` → `app-release.apk` from the Actions run page and place it at `/root/hinata-android-release.apk`.

- [ ] **Step 2: Verify the signature**

```bash
/opt/android-sdk/build-tools/35.0.0/apksigner verify --print-certs /root/hinata-android-release.apk
```

Expected: prints the new RSA certificate (CN=Hinata AI, not the debug cert), no "ERROR: CERTIFICATE MISSING"/"DOES NOT VERIFY".

- [ ] **Step 3: Verify it is a non-debuggable Flutter release**

```bash
/opt/android-sdk/build-tools/35.0.0/apksigner verify --verbose /root/hinata-android-release.apk
unzip -l /root/hinata-android-release.apk | grep -c "libflutter.so"   # expect > 0 (it IS the Flutter app)
```

Expected: `Verifies` / `Verified using v1 scheme` (or v2/v3) with no `Debuggable` flag warnings from a debug keystore.

- [ ] **Step 4: Verify the backend URL is compiled in**

```bash
mkdir -p /tmp/hinata-apk-verify && cd /tmp/hinata-apk-verify
unzip -o -q /root/hinata-android-release.apk "lib/arm64-v8a/libapp.so" "classes*.dex" 2>/dev/null
grep -c "hinata-m93w.onrender.com" lib/arm64-v8a/libapp.so classes*.dex 2>/dev/null
```

Expected: the string `hinata-m93w.onrender.com` appears (grep count > 0) in `libapp.so` (release AOT Dart) and/or DEX. Also confirm the OLD values are absent: `grep -c "localhost:8000\|10.99.189.237" lib/arm64-v8a/libapp.so classes*.dex` → 0.

- [ ] **Step 5: Report**

Summarize for the user: artifact location, signing cert, verified URL, and the fact that a new signing key means this APK won't auto-update over the old legacy APKs. Ask if they want it copied into the repo (e.g. `web/hinata-android-v3.apk`) — do NOT copy without asking.
