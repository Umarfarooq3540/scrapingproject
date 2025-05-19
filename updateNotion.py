import os
import time
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to add delay
def sleep(ms: int) -> None:
    time.sleep(ms / 1000)

# Helper function to retry a request operation with exponential backoff
async def retry_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    retries: int = 3,
    backoff: int = 300
) -> requests.Response:
    last_error = None
    headers = headers or {}
    
    for attempt in range(retries):
        try:
            logger.info(f"[retry_request] Attempt {attempt + 1}/{retries} for {url}")
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                timeout=30
            )
            return response
        except Exception as error:
            last_error = error
            logger.warning(f"[retry_request] Attempt {attempt + 1} failed: {str(error)}")
            
            if attempt < retries - 1:
                wait_time = backoff * (2 ** attempt)
                logger.info(f"[retry_request] Waiting {wait_time}ms before retry...")
                sleep(wait_time)
    
    raise last_error if last_error else Exception(f"Failed after {retries} attempts")

async def update_notion_value(
    exchange_name: str,
    column: str,
    value: float,
    notion_api_key: Optional[str] = None,
    notion_database_id: Optional[str] = None
) -> Dict[str, Any]:
    """Update a Notion database with new values for a specific exchange."""
    logger.info(f"[update_notion_value] Starting for exchange: {exchange_name}, column: {column}, value: {value}")
    
    try:
        # Get environment variables if not provided
        notion_api_key = notion_api_key or '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'
        notion_database_id = notion_database_id or '1dc9db39ff5a81809fc0d345c252de45'
        
        logger.info(f"[update_notion_value] NOTION_API_KEY exists: {notion_api_key is not None}")
        logger.info(f"[update_notion_value] NOTION_DATABASE_ID exists: {notion_database_id is not None}")
        
        if not notion_api_key:
            raise ValueError("NOTION_API_KEY is not defined")
        if not notion_database_id:
            raise ValueError("NOTION_DATABASE_ID is not defined")
            
        # Prepare headers for all Notion API requests
        headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # Step 1: Query the database to find the page for the exchange
        logger.info(f"[update_notion_value] Querying database for exchange: {exchange_name}")
        
        query_url = f"https://api.notion.com/v1/databases/{notion_database_id}/query"
        query_body = {
            "filter": {
                "property": "Exchange",
                "title": {
                    "equals": exchange_name
                }
            }
        }
        
        query_response = await retry_request(
            url=query_url,
            method="POST",
            headers=headers,
            json=query_body,
            retries=3,
            backoff=500
        )
        
        logger.info(f"[update_notion_value] Query response status: {query_response.status_code}")
        
        if not query_response.ok:
            error_text = query_response.text
            logger.error(f"[update_notion_value] Notion API error (query): {query_response.status_code} {error_text}")
            raise Exception(f"Notion API error (query): {query_response.status_code} {error_text}")
            
        query_data = query_response.json()
        results = query_data.get("results", [])
        logger.info(f"[update_notion_value] Query results count: {len(results)}")
        
        if not results:
            logger.error(f'[update_notion_value] Exchange "{exchange_name}" not found in Notion database')
            raise Exception(f'Exchange "{exchange_name}" not found in Notion database')
            
        page_id = results[0]["id"]
        logger.info(f"[update_notion_value] Found page ID: {page_id} for exchange: {exchange_name}")
        
        # Step 2: Get the database schema to check for available properties
        logger.info("[update_notion_value] Fetching database schema")
        
        db_url = f"https://api.notion.com/v1/databases/{notion_database_id}"
        
        db_response = await retry_request(
            url=db_url,
            method="GET",
            headers=headers,
            retries=5,
            backoff=500
        )
        
        logger.info(f"[update_notion_value] Database schema response status: {db_response.status_code}")
        
        if not db_response.ok:
            error_text = db_response.text
            logger.error(f"[update_notion_value] Notion API error (database): {db_response.status_code} {error_text}")
            raise Exception(f"Notion API error (database): {db_response.status_code} {error_text}")
            
        db_data = db_response.json()
        properties = list(db_data.get("properties", {}).keys())
        logger.info(f"[update_notion_value] Database properties: {', '.join(properties)}")
        
        has_last_updated = "Last Updated" in properties
        logger.info(f'[update_notion_value] Has "Last Updated" property: {has_last_updated}')
        
        # Check if the column exists in the database
        if column not in properties:
            logger.warning(
                f'[update_notion_value] Column "{column}" not found in database properties. '
                f'Available columns: {", ".join(properties)}'
            )
            
        # Step 3: Update the page with the new value
        logger.info(f"[update_notion_value] Preparing to update page {page_id}")
        
        # Prepare the properties to update
        update_properties = {
            column: {
                "number": value
            }
        }
        
        # Only add Last Updated if it exists
        if has_last_updated:
            update_properties["Last Updated"] = {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
            
        logger.info(f"[update_notion_value] Updating page with properties: {update_properties}")
        
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        update_body = {
            "properties": update_properties
        }
        
        update_response = await retry_request(
            url=update_url,
            method="PATCH",
            headers=headers,
            json=update_body,
            retries=5,
            backoff=500
        )
        
        logger.info(f"[update_notion_value] Update response status: {update_response.status_code}")
        
        if not update_response.ok:
            error_text = update_response.text
            logger.error(f"[update_notion_value] Notion API error (update): {update_response.status_code} {error_text}")
            raise Exception(f"Notion API error (update): {update_response.status_code} {error_text}")
            
        logger.info(f"[update_notion_value] Successfully updated {column} for {exchange_name} to {value}")
        return {"success": True, "message": f"Updated {column} for {exchange_name} to {value}"}
        
    except Exception as error:
        logger.error("[update_notion_value] Error updating Notion value:", exc_info=True)
        raise Exception(f"Failed to update Notion value: {str(error)}")