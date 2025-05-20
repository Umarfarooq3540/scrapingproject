from datetime import datetime
from playwright.async_api import async_playwright
import asyncio
from updateNotion import update_notion_value

async def scrape_and_update(source: str):
    data = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            if source == "gmx":
                url = "https://gmx.io/#/"
            elif source == "jupiter":
                url = "https://community.chaoslabs.xyz/jupiter/risk/overview"
            else:
                raise ValueError("Unknown source")

            await page.goto(url, timeout=60000)

            if source == "jupiter":
                await page.wait_for_selector('[data-testid="value-card-open-interest"]', timeout=10000)
                parent_handle = page.locator('[data-testid="value-card-open-interest"]').locator('..')
                aria_label = await parent_handle.get_attribute('aria-label')

                print(f"[GMX] Open Interest (aria-label): {aria_label}")

                if aria_label:
                    price_value = float(aria_label.replace('$', '').replace(',', '').strip())
                    await update_notion_value(
                        exchange_name="Jupiter",
                        column="OI",
                        value=price_value,
                    )
                    return price_value

            elif source == "gmx":
                await page.wait_for_selector('.Home-latest-info-block', timeout=30000)

                value_elements = await page.query_selector_all('.Home-latest-info__value')
                tvl_elements = await page.query_selector_all('.Home-latest-info__title')

                data['timestamp'] = datetime.now().isoformat()
                data['total_tvl'] = await tvl_elements[1].inner_text() if len(tvl_elements) > 1 else None
                data['price'] = await value_elements[1].inner_text() if len(value_elements) > 1 else None

                print(f"[Chaos Labs] TVL: {data['total_tvl']}, Price: {data['price']}")

                if data['price']:
                    price_value = float(data['price'].replace('$', '').replace(',', '').strip())
                    await update_notion_value(
                        exchange_name="GMX",
                        column="OI",
                        value=price_value,
                    )
                    return price_value

        except Exception as e:
            print(f"[{source.upper()}] Error: {str(e)}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    async def run_all():
        result = await scrape_and_update("gmx")
        if result:
            print("Success:", result)
        else:
            print("Operation failed")
        result = await scrape_and_update("jupiter")
        if result:
            print("Success:", result)
        else:
            print("Operation failed")
    asyncio.run(run_all())
   
