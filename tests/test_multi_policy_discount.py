import time

from pages.quote_page import QuotePage


def test_multi_policy_discount_is_applied_to_home_quote(page, base_url):
    quote = QuotePage(page, base_url)
    quote.open_new()

    unique_email = f"sam.test.{int(time.time() * 1000)}@example.com"
    quote.fill_home_quote(
        customer_name="Mac Test",
        customer_email=unique_email,
        home_value=120000,
    )
    page.locator("input[name='multi_policy']").check()
    quote.submit()

    quote.expect_status("quoted")
    discount = page.locator("tr", has_text="Multi-policy discount").locator("td").inner_text()
    assert discount == "Yes"
    assert quote.premium_text() == "$666.00"