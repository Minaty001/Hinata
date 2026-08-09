"""
Hinata - Phase 0 Security Tests

Verifies that all critical Phase 0 security issues have been resolved.
These tests must pass before Phase 1 begins.

Run: pytest tests/security/test_phase0_security.py -v
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestKeystoreNotInRepo:
    """Verify that the compromised keystore is not tracked by git."""

    def test_keystore_not_git_tracked(self):
        """No .jks or .keystore files should be tracked by git."""
        result = subprocess.run(
            ["git", "ls-files", "*.jks", "*.keystore", "*.p12"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        tracked = result.stdout.strip()
        assert tracked == "", (
            f"Signing key files are still tracked by git:\n{tracked}\n"
            "Run: git rm --cached <file>"
        )

    def test_keystore_directory_not_git_tracked(self):
        """keystore/ directories should not be tracked by git."""
        result = subprocess.run(
            ["git", "ls-files", "flutter_app/android/keystore/"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        tracked = result.stdout.strip()
        assert tracked == "", (
            f"keystore directory still tracked by git:\n{tracked}"
        )

    def test_gitignore_blocks_keystores(self):
        """`.gitignore` must contain patterns for keystore files."""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()
        assert "*.jks" in gitignore, ".gitignore must exclude *.jks"
        assert "*.keystore" in gitignore, ".gitignore must exclude *.keystore"


class TestNoHardcodedPasswords:
    """Verify no hardcoded secrets in source code."""

    def test_no_hinata123_password(self):
        """The compromised keystore password must not appear in source code."""
        forbidden = "hinata123"
        for ext in ("*.py", "*.gradle", "*.dart", "*.json", "*.yaml", "*.yml", "*.sh"):
            for fpath in PROJECT_ROOT.rglob(ext):
                # Skip git history, docs, and this test file
                if ".git" in str(fpath) or "AUDIT.md" in str(fpath) or "SECURITY.md" in str(fpath):
                    continue
                if fpath.samefile(Path(__file__)):
                    continue
                content = fpath.read_text(errors="replace")
                assert forbidden not in content, (
                    f"Hardcoded password '{forbidden}' found in {fpath}"
                )

    def test_no_hardcoded_emulator_url(self):
        """Android emulator-only URL 10.0.2.2 must not be hardcoded in source."""
        forbidden = "10.0.2.2"
        for fpath in PROJECT_ROOT.rglob("*.dart"):
            if ".git" in str(fpath):
                continue
            content = fpath.read_text(errors="replace")
            assert forbidden not in content, (
                f"Emulator-only URL '10.0.2.2' found in {fpath}. "
                "Use BackendConfig.getUrl() instead."
            )

    def test_no_hardcoded_fake_user_id(self):
        """The old hardcoded web user ID (999999) must not be used as an identity literal."""
        forbidden_pattern = "WEB_USER_TELEGRAM_ID = 999999"
        for fpath in PROJECT_ROOT.rglob("*.py"):
            if ".git" in str(fpath):
                continue
            # Skip test files — they necessarily contain the forbidden string
            # as string literals inside assertions.
            if "tests/" in str(fpath) or "test_" in fpath.name:
                continue
            content = fpath.read_text(errors="replace")
            assert forbidden_pattern not in content, (
                f"Hardcoded web user ID found in {fpath}"
            )


class TestNoCORSWildcard:
    """Verify wildcard CORS has been removed from Python source."""

    def test_no_wildcard_cors_in_python(self):
        """No Python file should send `Access-Control-Allow-Origin: *`."""
        for fpath in PROJECT_ROOT.rglob("*.py"):
            if ".git" in str(fpath):
                continue
            # Skip test files — they contain the forbidden string
            # as string literals inside assertions.
            if "tests/" in str(fpath) or "test_" in fpath.name:
                continue
            content = fpath.read_text(errors="replace")
            assert '"Access-Control-Allow-Origin", "*"' not in content, (
                f"Wildcard CORS found in {fpath}. Use _WEB_ORIGINS allowlist."
            )
            assert "'Access-Control-Allow-Origin', '*'" not in content, (
                f"Wildcard CORS found in {fpath}. Use _WEB_ORIGINS allowlist."
            )


class TestNoAPKsInRepo:
    """Verify APK release artifacts are not tracked by git."""

    def test_apks_not_git_tracked(self):
        """APK files should not be tracked by git."""
        result = subprocess.run(
            ["git", "ls-files", "*.apk", "*.aab"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        tracked = result.stdout.strip()
        assert tracked == "", (
            f"APK/AAB files still tracked by git:\n{tracked}\n"
            "Run: git rm --cached <file>"
        )

    def test_gitignore_blocks_apks(self):
        """`.gitignore` must contain patterns for APK files."""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()
        assert "*.apk" in gitignore, ".gitignore must exclude *.apk"


class TestEnvExample:
    """Verify .env.example is properly structured."""

    def test_env_example_exists(self):
        assert (PROJECT_ROOT / ".env.example").exists(), ".env.example must exist"

    def test_env_example_has_jwt_secret(self):
        content = (PROJECT_ROOT / ".env.example").read_text()
        assert "JWT_SECRET" in content, ".env.example must document JWT_SECRET"

    def test_env_example_has_web_origins(self):
        content = (PROJECT_ROOT / ".env.example").read_text()
        assert "WEB_ORIGINS" in content, ".env.example must document WEB_ORIGINS"

    def test_env_example_has_keystore_docs(self):
        content = (PROJECT_ROOT / ".env.example").read_text()
        assert "KEYSTORE_PATH" in content, ".env.example must document KEYSTORE_PATH"

    def test_env_not_committed(self):
        """The actual .env file should not be tracked by git."""
        result = subprocess.run(
            ["git", "ls-files", ".env"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        tracked = result.stdout.strip()
        assert tracked == "", ".env file must not be tracked by git"


class TestUserServiceMigrationShim:
    """Verify the migration shim in user_service.py is correct."""

    def test_placeholder_id_not_999999(self):
        """The placeholder ID must not be the original 999999."""
        user_service = (PROJECT_ROOT / "services" / "user_service.py").read_text()
        assert "WEB_USER_TELEGRAM_ID = 999999" not in user_service, (
            "Original hardcoded ID 999999 must be removed"
        )

    def test_deprecation_warning_present(self):
        """The migration shim must have a deprecation warning."""
        user_service = (PROJECT_ROOT / "services" / "user_service.py").read_text()
        assert "DEPRECATED" in user_service or "deprecated" in user_service, (
            "get_or_create_web_user must have deprecation documentation"
        )
        assert "migration shim" in user_service.lower() or "phase 1" in user_service.lower(), (
            "Migration shim must reference Phase 1 removal"
        )
