"""Page Object for PolicyHub's policy detail page (/policy/<id>) and home
page (/) - the second starting pattern alongside QuotePage. Extend this the
same way in Week 9+: one class per screen, tests call methods, never raw
locators.
"""
from __future__ import annotations

from playwright.sync_api import Page, expect


class HomePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        self.page.goto(self.base_url)

    def policy_count(self) -> int:
        tile = self.page.locator(".ph-tile", has_text="Policies")
        return int(tile.locator(".count").inner_text())

    def claim_count(self) -> int:
        tile = self.page.locator(".ph-tile", has_text="Claims")
        return int(tile.locator(".count").inner_text())


class PolicyPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open(self, policy_id: str) -> None:
        self.page.goto(f"{self.base_url}/policies/{policy_id}")

    def expect_status(self, status: str) -> None:
        expect(self.page.locator(".ph-badge")).to_contain_text(status)
