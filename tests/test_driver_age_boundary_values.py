"""Boundary tests for the auto quote driver age field."""
import time

import pytest
from playwright.sync_api import Page

from pages.quote_page import QuotePage

@pytest.mark.parametrize(
    "driver_age, expected_error",
    [
        pytest.param(15, "Value must be greater than or equal to 16.", id="age-below-minimum-15"),
        pytest.param(16, None, id="age-at-minimum-16"),
        pytest.param(99, None, id="age-at-maximum-99"),
        pytest.param(100, "Value must be less than or equal to 99.", id="age-above-maximum-100"),
    ]
)
def test_driver_age_boundary_values(
    page: Page,
    base_url,
    driver_age,
    expected_error,
):
    quote = QuotePage(page, base_url)
    quote.open_new()

    unique_email = f"sam.test.{int(time.time() * 1000)}@example.com"
    quote.fill_auto_quote(
        customer_name="Sam Test",
        customer_email=unique_email,
        driver_age=driver_age,
        vehicle_year=2021,
        vehicle_make="Toyota",
        vehicle_model="Camry",
        coverage_type="collision",
    )
    quote.submit()

    age_input = page.locator("input[name='driver_age']")
    if expected_error:
        assert not age_input.evaluate("(input) => input.validity.valid"), (
            f"Age {driver_age} should fail HTML validation"
        )
        assert age_input.evaluate("(input) => input.validationMessage") == expected_error
    else:
        # Valid ages submit the form and navigate away from the quote form,
        # so the age input no longer exists after submission.
        quote.expect_status("quoted")
