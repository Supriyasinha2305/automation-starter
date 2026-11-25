"""Verify that the auto quote premium changes with the deductible."""
import time

import pytest
from playwright.sync_api import Page

from pages.quote_page import QuotePage


@pytest.mark.parametrize(
    "deductible, expected_premium",
    [
        (250, "$1050.00"),
        (500, "$975.00"),
        (1000, "$900.00"),
        (2500, "$800.00"),
    ],
)
def test_premium_based_on_deductible(
    page: Page,
    base_url,
    deductible: int,
    expected_premium: str,
):
    quote = QuotePage(page, base_url)
    quote.open_new()

    unique_email = f"sam.test.{int(time.time() * 1000)}@example.com"
    quote.fill_auto_quote(
        customer_name="Sam Test",
        customer_email=unique_email,
        driver_age=30,
        vehicle_year=2021,
        vehicle_make="Toyota",
        vehicle_model="Camry",
        coverage_type="collision",
    )
    page.locator("#deductible").select_option(str(deductible))
    quote.submit()

    quote.expect_status("quoted")
    assert quote.premium_text() == expected_premium
