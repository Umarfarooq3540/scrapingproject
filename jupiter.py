from playwright.async_api import async_playwright
import asyncio

async def scrape_jupiter():
    async with async_playwright() as p:
        # Launch browser with stealth settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        # Create new context with custom permissions
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True
        )
        
        page = await context.new_page()

        try:
            # Navigate to page with extended timeout
            await page.goto(
                "https://community.chaoslabs.xyz/jupiter/risk/overview",
                wait_until="networkidle",
                timeout=60000
            )

            # Debug: Save full page HTML
            html = await page.content()
            with open("page.html", "w") as f:
                f.write(html)

            # Check for iframes
            frames = page.frames
            print(f"Found {len(frames)} frames on page")
            
            # Alternative: Try finding element using text content
            try:
                element = await page.wait_for_selector(
                    ':has-text("Open Interest")',
                    state="visible",
                    timeout=30000
                )
                print("Found element using text matching!")
            except:
                print("Couldn't find element via text")

            # Final attempt with different selectors
            selectors = [
                '[data-testid="value-card-open-interest"]',
                '.MuiBox-root >> text=Open Interest',
                'div:has-text("Open Interest")'
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(
                        selector,
                        state="visible",
                        timeout=20000
                    )
                    print(f"Found with selector: {selector}")
                    break
                except:
                    continue

            if not element:
                raise Exception("All selectors failed")

            # Interact with element
            parent = await element.evaluate_handle('el => el.parentElement')
            aria_label = await parent.get_attribute('aria-label')
            print(f"Found aria-label: {aria_label}")

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="error.png")
        finally:
            await browser.close()

asyncio.run(scrape_jupiter())
