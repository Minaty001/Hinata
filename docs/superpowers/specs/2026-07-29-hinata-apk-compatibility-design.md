# APK Compatibility Fix & Icon Update — Design Doc

## Problem

The existing `web/hinata-android.apk` is a WebView-based Android wrapper for the Hinata AI
companion web app. It fails to install on newer Android versions (14/15/16) due to:

1. **No explicit minSdkVersion / targetSdkVersion** — defaults to API 1, causing
   incompatibility with Android 14+ runtime requirements.
2. **compileSdkVersion 33** — lacks support for Android 14+ API contracts (exported
   receivers, foreground service type enforcement, notification permissions).
3. **`debuggable=true`** — prevents installation on production devices.
4. **Missing adaptive icon** — currently uses a placeholder XML vector; no visible
   PNG/WebP icon for pre-API-26 devices.

## Approach

Since Flutter SDK is unavailable for ARM64 Linux (the host architecture), the fastest
path is to **patch the existing APK directly** using `apktool` → modify manifest →
replace icon → rebuild → zipalign → sign. This avoids the multi-GB download and
cross-architecture emulation that a full Flutter setup would require.

The user-visible result is identical: a working APK installable on Android 9–16 with
an anime-girl launcher icon.

## Changes

### 1. AndroidManifest.xml

| Field | Current | New | Reason |
|-------|---------|-----|--------|
| `android:minSdkVersion` | (omitted, defaults to 1) | `28` | Android 9 (Pie) minimum — covers target range |
| `android:targetSdkVersion` | (omitted, defaults to 33) | `34` | Android 14 — latest stable SDK with modern API contracts |
| `android:debuggable` | `true` | remove attribute | Production APK must not be debuggable |
| `android:allowBackup` | `true` | `false` | Security hardening |
| Keep: `requestLegacyExternalStorage`, `usesCleartextTraffic`, `foregroundServiceType` | | | Still needed for WebView localhost access |

### 2. Launcher Icon

Replace `res/mipmap-*` adaptive icon XMLs with a real anime-girl PNG icon at multiple
densities. Generate via Python/Pillow with an SVG-like drawn character.

### 3. Build & Sign

```
apktool b → zipalign → apksigner (with new keystore)
```

Keystore generated self-signed for development purposes (user can replace for
production).

## Non-Goals

- Not rebuilding the entire app from scratch (the APK logic is fine)
- Not converting to native Android/Flutter (SDK constraint)
- Not modifying app behavior or WebView loading logic
- Not publishing to Play Store
