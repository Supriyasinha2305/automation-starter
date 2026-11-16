"""Page Object for PolicyHub's quote form (/quote/new) and quote detail page
(/quote/<id>). Wraps this screen's locators/actions behind plain methods, so
every test that touches a quote calls QuotePage instead of re-deriving
locators inline - if the form's markup changes, fix it here once.
"""
from __future__ import annotations

from playwright.sync_api import Page, expect


class QuotePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def open_new(self) -> None:
        self.page.goto(f"{self.base_url}/quote/new")

    def fill_auto_quote(
        self,
        customer_name: str,
        customer_email: str,
        driver_age: int,
        vehicle_year: int | None = None,
        vehicle_make: str | None = None,
        vehicle_model: str | None = None,
        coverage_type: str | None = None,
    ) -> None:
        self.page.fill("#customer_name", customer_name)
        self.page.fill("#customer_email", customer_email)
        self.page.select_option("#product_type", "auto")
        # Deliberately not a role/test-id locator - the driver_age input is
        # the seeded accessibility bug (Week 12), it has no <label>.
        self.page.fill("input[name='driver_age']", str(driver_age))
        if vehicle_year is not None:
            self.page.fill("#vehicle_year", str(vehicle_year))
        if vehicle_make is not None:
            self.page.fill("#vehicle_make", vehicle_make)
        if vehicle_model is not None:
            self.page.fill("#vehicle_model", vehicle_model)
        if coverage_type is not None:
            self.page.select_option("#coverage_type", coverage_type)

    def submit(self) -> None:
        self.page.get_by_role("button", name="Get Quote").click()

    # --- Quote detail page assertions, once submit() has navigated there ---

    def expect_status(self, status: str) -> None:
        expect(self.page.locator(".ph-badge")).to_contain_text(status)

    def premium_text(self) -> str:
        row = self.page.locator("tr", has_text="Annual premium")
        return row.locator("td").inner_text()

    def bind(self) -> None:
        self.page.get_by_role("button", name="Bind this Quote").click()
