"""Shared fixtures for the whole suite.

base_url comes from the POLICYHUB_URL environment variable - never hardcode
a PolicyHub instance's URL into a test file. Set it before running pytest:

    # macOS/Linux
    export POLICYHUB_URL=http://127.0.0.1:6001
    # Windows PowerShell
    $env:POLICYHUB_URL = "http://127.0.0.1:6001"

pytest-playwright already provides a `page` fixture (a fresh browser page
per test); this file only adds the PolicyHub-specific pieces on top of it.
"""
import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("POLICYHUB_URL")
    if not url:
        pytest.exit(
            "POLICYHUB_URL is not set. Launch your PolicyHub instance and "
            "set POLICYHUB_URL to its address before running pytest, e.g. "
            "POLICYHUB_URL=http://127.0.0.1:6001 pytest",
            returncode=1,
        )
    return url.rstrip("/")


@pytest.fixture
def home_page(page, base_url):
    """A page already navigated to PolicyHub's home screen."""
    page.goto(base_url)
    return page
