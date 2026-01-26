
const { test, expect } = require('@playwright/test');

test('App loads and has basic elements', async ({ page }) => {
  // 1. Go to the app URL (assuming it is running on localhost:5173 for dev or hosted)
  // For this test, we assume the user will run it against their dev server
  await page.goto('http://localhost:5173');

  // 2. Check title or header
  await expect(page).toHaveTitle(/Vite \+ React/);

  // 3. Check for Search Input
  const searchInput = page.locator('input.search-input');
  await expect(searchInput).toBeVisible();

  // 4. Check for Price Display
  const priceDisplay = page.locator('.price-display');
  await expect(priceDisplay).toBeVisible();

  // 5. Check for Signal Card
  const signalCard = page.locator('.signal-card');
  await expect(signalCard).toBeVisible();
});
