import aiohttp
import logging
from fastapi import HTTPException
import json
from datetime import datetime, timezone, timedelta
import os
# from database import add_gsc_data_by_keyword_id, get_db_connection

GREPWORDS_API_KEY = os.getenv("GREPWORDS_API_KEY")  # Ensure this is set

async def fetch_search_volume(keyword: str) -> int:
    url = "https://data.grepwords.com/v1/keywords/lookup"
    headers = {
        "accept": "application/json",
        "api_key": GREPWORDS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "term": keyword,
        "country": "us",
        "language": "en"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            logging.info(f"Grepwords API request for '{keyword}': URL: {url}, Headers: {headers}, Payload: {payload}")
            data = await response.json()
            logging.info(f"Grepwords API response for '{keyword}': {json.dumps(data, indent=2)}")
            
            if response.status == 200 and data and 'data' in data:
                volume = data['data'].get('volume', 0)
                logging.info(f"Search volume for '{keyword}': {volume}")
                return volume
            else:
                logging.warning(f"No search volume data found for '{keyword}'. Status: {response.status}, Response: {data}")
                return 0

# async def backfill_gsc_data(project_id, keyword_id, keyword):
#     # Example implementation
#     # Fetch historical data (mock implementation)
#     start_date = datetime.now().date() - timedelta(days=60)
#     end_date = datetime.now().date() - timedelta(days=30)
#     # Assume fetch_gsc_data is a function that fetches data
#     gsc_data = await fetch_gsc_data(project_id, keyword, start_date, end_date)
    
#     for data in gsc_data:
#         await add_gsc_data_by_keyword_id(
#             keyword_id=data['keyword_id'],
#             date=data['date'],
#             clicks=data['clicks'],
#             impressions=data['impressions'],
#             ctr=data['ctr'],
#             position=data['position'],
#             query=data['query'],
#             page=data['page']
#         )
#     logging.info(f"Backfilled GSC data for keyword_id {keyword_id}")