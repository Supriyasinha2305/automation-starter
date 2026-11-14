import { test, expect } from '@playwright/test';

test('Verify successful login', async ({ page }) => {

  // 1. Open the login page
  await page.goto('https://practicetestautomation.com/practice-test-login/');

  // 2. Enter username
  await page.locator('#username').fill('student');

  // 3. Enter password
  await page.locator('#password').fill('Password123');

  // 4. Click Submit button
  await page.locator('#submit').click();

  // 5. Verify the new page URL
  await expect(page).toHaveURL(/practicetestautomation\.com\/logged-in-successfully\//);

  // 6. Verify successful login message
  await expect(
    page.locator('text=Congratulations')
  ).toBeVisible();

  // 7. Verify Log out button is displayed
  await expect(
    page.getByRole('link', { name: 'Log out' })
  ).toBeVisible();

});