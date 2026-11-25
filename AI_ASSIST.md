
# AI Assistance Log

This file documents AI-assisted contributions to the Playwright automation project.
All suggestions were reviewed and verified before being used.

## Entry 1: Parameterized Driver Age Validation

**AI assistance:** Used ChatGPT to help design a Pytest parameterized test for driver age boundary validation.

**Suggestion received:**
- Use pytest.mark.parametrize to test multiple age values in one test function.
- Cover boundary values 15, 16, 99 and 100.
- Use meaningful test IDs for each scenario.

**My review and verification:**
- Reviewed the parameterization and verified that each age is passed to the form using str(age).
- Checked that age 15 triggers the minimum age validation message.
- Checked that age 100 triggers the maximum age validation message.
- Verified that ages 16 and 99 do not trigger age validation errors.
- Ran the test locally and reviewed the results.

**Outcome:** Used the reviewed parameterized test in the automation suite.

## Entry 2: Reusable Test Data and Unique Email Generation

**AI assistance:** Used ChatGPT to understand how to generate unique email addresses for automated quote creation.

**Suggestion received:**
- Use Python's time module to generate a timestamp-based unique email.
- Pass the generated email and parameterized driver age to the Page Object Model method.

**My review and verification:**
- Reviewed the Python f-string and timestamp generation logic.
- Verified that a different email address is generated for each test execution.
- Checked that the fill_auto_quote method accepts the driver_age argument.
- Ran the test to verify that the form receives the expected values.

**Outcome:** Used the reviewed approach to avoid duplicate email addresses during test execution.
