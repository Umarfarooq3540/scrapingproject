from playwright.async_api import async_playwright

async def fetch_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Run in visible mode for debugging
        page = await browser.new_page()

        # Set consistent viewport/user-agent (avoid platform differences)
        await page.set_viewport_size({"width": 1280, "height": 720})
        
        # Navigate to the URL
        await page.goto("https://community.chaoslabs.xyz/jupiter/risk/overview",timeout=60000)
        
        # Wait for the root element (React app)
        await page.wait_for_selector('[data-testid="value-card-open-interest"]', timeout=60000)

        # Get the full HTML content
        html_content = await page.content()

        # Optional: Save to a file for inspection
        with open("page_content.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        await browser.close()

# Run the function
import asyncio
asyncio.run(fetch_html())