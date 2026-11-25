
# AI Assistance Log

This file documents AI-assisted contributions to the Playwright automation project.
All suggestions were reviewed and verified before being used.

## Entry 1: Fixing the Driver Age Validation Test

**AI Tool:** GitHub Copilot using VS Code

**Assistance requested:**
Fix the `test_auto_quote_driver_age_validation` script so that it correctly verifies browser-native HTML validation for the driver's age field.

**AI-generated suggestion:**
- Move the validation assertions inside the test function.
- Locate the driver-age input by its `name` attribute.
- Use the input element's `validity.rangeUnderflow` property.
- Read the browser-generated `validationMessage`.
- Correct the policy-count assertion in the same test file from an increase of zero to an increase of one.

**Review and Changes Made:**
- Reviewed the existing test and confirmed that it was attempting to use the validation message outside the test function.
- Confirmed that the policyhub form sets `min="16"` on the driver-age input.
- Replaced the DOM text lookup with HTML constraint-validation checks.
- Verified that age 15 produces `rangeUnderflow` and the message "Value must be greater than or equal to 16."
- Reviewed the binding test and corrected the policy-count expectation to `policies_before + 1`.

**Outcome:**
Used the reviewed fixes to correct the driver-age validation test and the policy-count assertion.


## Entry 2: Fixing the Driver Age Boundary Values Test

**AI Tool:** GitHub Copilot using VS Code

**Assistance requested:**
Fix the parameterized driver-age boundary test script and address errors in its pytest parameters and fixture usage.

**AI-generated suggestion:**
- Import `Page` from `playwright.sync_api`.
- Include `base_url` as a pytest fixture argument.
- Use `driver_age` and `expected_error` in the test function signature.
- Check `input.validity.valid` for the four boundary scenarios.
- Verify the browser validation message for ages 15 and 100.
- Verify the quote status for valid ages 16 and 99.

**Review and Changes Made:**
- Reviewed the parameterized test and identified mismatched parameter and fixture names.
- Updated the test signature to match the `driver_age, expected_error` parameterization.
- Added the required `base_url` fixture so `QuotePage` can open the quote form.
- Replaced text-based validation lookups with constraint-validation properties.
- Verified that ages 16 and 99 pass validation and navigate to a quoted quote.
- Verified that ages 15 and 100 fail validation with their respective browser messages.

**Outcome:**
Used the reviewed fixes to correct the boundary-value test and align it with the pytest and Playwright patterns in the project.


## Entry 3: Fixing the Multi-Policy Discount Test

**AI Tool:** GitHub Copilot using VS Code

**Assistance requested:**
Investigate why the multi-policy discount test failed and correct the test script.

**AI-generated suggestion:**
- Select the multi-policy checkbox by its `name` instead of using a generic checkbox selector.
- Assert that the quote detail page reflects the selected discount and shows the corresponding premium.

**Review and Changes Made:**
- Reviewed the quote form and found that it has multiple checkboxes, including an auto-only anti-theft checkbox that is hidden for a home quote.
- Updated the test to select `input[name='multi_policy']` specifically.
- Updated assertions to verify the quote status, displayed multi-policy value, and premium.
- Confirmed from the premium calculation that a $120,000 home value with the 10% multi-policy discount yields `$666.00`.
- The browser test was not run during this assistance session.

**Outcome:**
Used the reviewed changes to make the test target the intended checkbox and verify the resulting discount.


## Entry 4: Fixing the Premium-by-Deductible Test

**AI Tool:** GitHub Copilot using VS Code

**Assistance requested:**
Explain why the deductible premium test was failing, then correct the script. The fix was later accidentally undone and requested again.

**AI-generated suggestion:**
- Set each deductible on the quote form before submitting.
- Assert the premium displayed on the quote details page instead of querying form controls or a nonexistent `#discounted_premium` element after navigation.
- Use expected premium strings that match the application’s currency formatting and rating calculation.

**Review and Changes Made:**
- Reviewed `QuotePage.fill_auto_quote` and confirmed it does not accept a `deductible` argument.
- Reviewed the quote page flow and confirmed that submission navigates away from the form; the quote details template renders the premium as “Annual premium” and has no deductible dropdown or `#discounted_premium` element.
- Used the current rating factors for age 30, collision coverage, and the selected deductible to set the expected values: `$1,050.00`, `$975.00`, `$900.00`, and `$800.00`.
- Reapplied the fix after the original changes were undone.
- Pylance reported no errors; the browser test was not run.

**Outcome:**
Updated the test to select the deductible before submission and verify the formatted premium on the quote details page.
