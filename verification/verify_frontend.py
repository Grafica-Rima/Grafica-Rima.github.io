
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate to frontend (Vite usually on 5173)
    try:
        page.goto("http://localhost:5173")

        # Wait for the search box to appear
        page.wait_for_selector('input[placeholder="BTC/USDT..."]')

        # Take a screenshot
        page.screenshot(path="verification/frontend_snapshot.png")
        print("Screenshot taken.")

    except Exception as e:
        print(f"Error: {e}")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
