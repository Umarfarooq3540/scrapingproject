from datetime import datetime
from playwright.async_api import async_playwright
import asyncio
from updateNotion import update_notion_value
import os

async def scrape_and_update():
    url = "https://gmx.io/#/"
    data = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('.Home-latest-info-block', timeout=30000)
            
            tvl_elements = await page.query_selector_all('.Home-latest-info__title')
            value_elements = await page.query_selector_all('.Home-latest-info__value')
            
            data['timestamp'] = datetime.now().isoformat()
            data['total_tvl'] = await tvl_elements[1].inner_text() if len(tvl_elements) > 1 else None
            data['price'] = await value_elements[1].inner_text() if len(value_elements) > 1 else None
            
            if data['price']:
                price_value = float(data['price'].replace('$', '').replace(',', '').strip())
                await update_notion_value(
                    exchange_name="GMX",
                    column="OI",
                    value=price_value,
                    # notion_api_key=os.getenv("NOTION_API_KEY"),
                    # notion_database_id=os.getenv("NOTION_DATABASE_ID")
                )
            
            return data
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(scrape_and_update())
    if result:
        print("Success:", result)
    else:
        print("Operation failed")