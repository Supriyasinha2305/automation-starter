import re
import time

from pages.policy_page import HomePage
from pages.quote_page import QuotePage


def test_home_quote_shows_a_premium(page, base_url):
 quote = QuotePage(page, base_url)
 quote.open_new()

 unique_email = f"sam.test.{int(time.time() * 1000)}@example.com"
 quote.fill_home_quote(
 customer_name="Mac Test",
 customer_email=unique_email,
 home_value=2000000,
   )
 quote.submit()

 quote.expect_status("quoted")
 premium = quote.premium_text()
 assert re.match(r"\$\d[\d,]*\.\d{2}", premium), f"expected a dollar amount, got {premium!r}"    