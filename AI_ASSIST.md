
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


## Entry 2: Negative Driver Age Validation

**AI Tool:** ChatGPT

**Exact Prompt:**

"Create a Playwright Python test for a page with Name, Email ID and Driver's Age. If the driver's age is less than 16, the error message should be 'Value must be greater than or equal to 16.'"

**AI-generated suggestion:**
Use Playwright locators to fill in the customer details, enter an invalid driver age (15), submit the form and verify that the expected validation error is displayed.

**Review and Changes Made:**
- Reviewed the test flow for entering customer details and submitting the form.
- Verified the actual validation message displayed by the application.
- Replaced the initially suggested error message with the actual application message: "Value must be greater than or equal to 16."
- Reviewed the locator used to identify the validation message.
- Used a Python assertion to verify that the validation error is displayed.
- Executed the test locally to check the validation behaviour.

**Outcome:**ss
Created a negative test scenario to verify that the application rejects a driver age below the minimum allowed age of 16.
