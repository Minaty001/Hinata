"""
Tests for the Hinata Reflex Brain.

Verifies pattern classification, dynamic template rendering, execution bypass,
and command routing dispatch.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.reflex.classifier import ReflexClassifier, ReflexMatch


def test_reflex_classification_open_app():
    classifier = ReflexClassifier()
    
    # Static package mappings
    match1 = classifier.classify("open youtube")
    assert match1 is not None
    assert match1.command == "android.open_app"
    assert match1.arguments == {"package": "com.google.android.youtube"}
    assert "YouTube" in match1.get_reply()

    match2 = classifier.classify("open chrome")
    assert match2 is not None
    assert match2.command == "android.open_app"
    assert match2.arguments == {"package": "com.android.chrome"}
    assert "Chrome" in match2.get_reply()

    # Dynamic regex group capture matching
    match3 = classifier.classify("open app spotify")
    assert match3 is not None
    assert match3.command == "android.open_app"
    assert match3.arguments == {"app_name": "spotify"}
    assert "spotify" in match3.get_reply()


def test_reflex_classification_volume_and_flashlight():
    classifier = ReflexClassifier()

    match_vol = classifier.classify("turn volume up")
    assert match_vol is not None
    assert match_vol.command == "android.volume_up"

    match_flash = classifier.classify("turn on flashlight")
    assert match_flash is not None
    assert match_flash.command == "android.flashlight"
    assert match_flash.arguments == {"state": "on"}
    assert "on" in match_flash.get_reply().lower()


def test_reflex_classification_system_time():
    classifier = ReflexClassifier()

    match_time = classifier.classify("what time is it")
    assert match_time is not None
    assert match_time.command == "system.time"
    reply = match_time.get_reply()
    assert "current time is" in reply.lower()
    # Check that time is formatted (e.g. contains numbers/colon/PM/AM)
    assert ":" in reply


def test_reflex_classification_no_match():
    classifier = ReflexClassifier()
    assert classifier.classify("how was your day?") is None
    assert classifier.classify("turn on the radio") is None


@pytest.mark.asyncio
async def test_reflex_execution_integration(client: AsyncClient):
    """Verify that a reflex query returns a fast deterministic response from the API."""
    # Send a reflex query to the chat endpoint
    res = await client.post(
        "/api/v1/chat/",
        json={"message": "flashlight off"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["provider"] == "reflex"
    assert body["model"] == "deterministic"
    assert "off" in body["reply"].lower()
