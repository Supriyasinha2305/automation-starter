"""Week 8's example test: submit an auto quote, confirm a premium renders,
and confirm the home page's policy count tile reflects what's actually
being bound. This is the test that must pass locally before you touch
anything else - it's the proof your framework is wired up correctly.
"""
import re
import time

from pages.policy_page import HomePage
from pages.quote_page import QuotePage


def test_auto_quote_shows_a_premium(page, base_url):
    quote = QuotePage(page, base_url)
    quote.open_new()

    unique_email = f"sam.test.{int(time.time() * 1000)}@example.com"
    quote.fill_auto_quote(
        customer_name="Sam Test",
        customer_email=unique_email,
        driver_age=32,
        vehicle_year=2021,
        vehicle_make="Toyota",
        vehicle_model="Camry",
        coverage_type="collision",
    )
    quote.submit()

    quote.expect_status("quoted")
    premium = quote.premium_text()
    assert re.match(r"\$\d[\d,]*\.\d{2}", premium), f"expected a dollar amount, got {premium!r}"


def test_binding_a_quote_increases_the_policy_count(page, base_url):
    home = HomePage(page, base_url)
    home.open()
    policies_before = home.policy_count()

    quote = QuotePage(page, base_url)
    quote.open_new()
    unique_email = f"bind.test.{int(time.time() * 1000)}@example.com"
    quote.fill_auto_quote(
        customer_name="Bind Test", customer_email=unique_email,
        driver_age=40, vehicle_year=2020, vehicle_make="Honda", vehicle_model="Civic",
    )
    quote.submit()
    quote.bind()
    # bind() redirects PolicyHub to the new policy's detail page, where a
    # freshly-bound policy's status is "active" (the quote itself becomes
    # "bound", but we've already navigated away from the quote page).
    quote.expect_status("active")

    home.open()
    assert home.policy_count() == policies_before + 1
