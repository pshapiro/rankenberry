from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uvicorn
import os
from dotenv import load_dotenv
import aiohttp
from database import add_serp_data, get_keywords, get_all_keywords, delete_keyword_by_id, delete_keywords_by_project
import json
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
from asyncio import Semaphore
import logging
import aiohttp
import json
import base64
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import create_engine

load_dotenv()

app = FastAPI()

# Set up APScheduler
engine = create_engine('sqlite:///./rankenberry.db')
jobstores = {
    'default': SQLAlchemyJobStore(engine=engine)
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your Vue.js app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProjectBase(BaseModel):
    name: str
    domain: str

class Project(ProjectBase):
    id: int

class KeywordBase(BaseModel):
    keyword: str

class Keyword(KeywordBase):
    id: int
    project_id: int

class Tag(BaseModel):
    id: int
    name: str

class TagCreate(BaseModel):
    name: str

class SerpDataRequest(BaseModel):
    api_source: str

class ApiSourceUpdate(BaseModel):
    api_source: str

class Schedule(BaseModel):
    name: str
    project_id: Optional[int] = None
    tag_id: Optional[int] = None
    frequency: str

# Database functions
def get_db_connection():
    conn = sqlite3.connect('seo_rank_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  domain TEXT NOT NULL,
                  active INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER,
                  keyword TEXT NOT NULL,
                  active INTEGER DEFAULT 1,
                  search_volume INTEGER DEFAULT NULL,
                  last_volume_update TEXT,
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS serp_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  date TEXT NOT NULL,
                  rank INTEGER,
                  full_data TEXT NOT NULL,
                  search_volume INTEGER,
                  api_source TEXT DEFAULT 'spaceserp',
                  FOREIGN KEY (keyword_id) REFERENCES keywords (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS tags
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS keyword_tags
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  tag_id INTEGER,
                  FOREIGN KEY (keyword_id) REFERENCES keywords (id),
                  FOREIGN KEY (tag_id) REFERENCES tags (id),
                  UNIQUE(keyword_id, tag_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  project_id INTEGER,
                  tag_id INTEGER,
                  frequency TEXT NOT NULL,
                  last_run TEXT,
                  next_run TEXT,
                  FOREIGN KEY (project_id) REFERENCES projects (id),
                  FOREIGN KEY (tag_id) REFERENCES tags (id))''')

    # Add api_source column to serp_data table if it doesn't exist
    c.execute('''
        PRAGMA table_info(serp_data)
    ''')
    columns = [column[1] for column in c.fetchall()]
    if 'api_source' not in columns:
        c.execute('''
            ALTER TABLE serp_data
            ADD COLUMN api_source TEXT DEFAULT 'spaceserp'
        ''')

    conn.commit()
    conn.close()

# Initialize the database
init_db()

SPACESERP_API_KEY = os.getenv("SPACESERP_API_KEY")
GREPWORDS_API_KEY = os.getenv("GREPWORDS_API_KEY")
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.get("/api/projects")
async def get_projects():
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects').fetchall()
    conn.close()
    return [dict(project) for project in projects]

@app.post("/api/projects", response_model=Project)
async def create_project(project: ProjectBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO projects (name, domain) VALUES (?, ?)',
                   (project.name, project.domain))
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": project_id, **project.dict()}

@app.get("/api/projects/{project_id}/keywords")
async def get_keywords(project_id: int):
    conn = get_db_connection()
    keywords = conn.execute('SELECT * FROM keywords WHERE project_id = ?', 
                            (project_id,)).fetchall()
    conn.close()
    return [dict(keyword) for keyword in keywords]

@app.post("/api/projects/{project_id}/keywords", response_model=Keyword)
async def create_keyword(project_id: int, keyword: KeywordBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO keywords (project_id, keyword, search_volume, last_volume_update) VALUES (?, ?, NULL, NULL)',
                   (project_id, keyword.keyword))
    keyword_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": keyword_id, "project_id": project_id, **keyword.dict()}

CONCURRENT_REQUESTS = 5  # Adjust this number based on API limits and your server capacity

@app.post("/api/fetch-serp-data/{project_id}")
async def fetch_serp_data(project_id: int, request: SerpDataRequest = Body(None)):
    tag_id = request.tag_id if request else None
    keywords = await get_keywords(project_id, tag_id)
    active_keywords = [kw for kw in keywords if kw['active']]
    
    semaphore = Semaphore(CONCURRENT_REQUESTS)
    
    async def fetch_and_store(keyword):
        async with semaphore:
            serp_data = await fetch_serp_data(keyword['keyword'])
            
            # Check if we need to update the search volume
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT search_volume, last_volume_update FROM keywords WHERE id = ?", (keyword['id'],))
            result = c.fetchone()
            current_search_volume, last_update = result if result else (None, None)
            conn.close()

            current_time = datetime.now()
            should_update_volume = (
                current_search_volume is None or 
                last_update is None or 
                (current_time - datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")).days > 30
            )

            if should_update_volume:
                search_volume = await fetch_search_volume(keyword['keyword'])
            else:
                search_volume = current_search_volume

            add_serp_data(keyword['id'], serp_data, search_volume)
    
    tasks = [fetch_and_store(keyword) for keyword in active_keywords]
    await asyncio.gather(*tasks)
    
    return {"message": f"SERP data fetched and stored successfully for {len(active_keywords)} active keywords"}

@app.post("/api/fetch-serp-data-by-tag/{tag_id}")
async def fetch_and_store_serp_data_by_tag(tag_id: int):
    keywords = await get_keywords_by_tag(tag_id)
    for keyword in keywords:
        if keyword['active']:
            serp_data = await fetch_serp_data(keyword['keyword'])
            add_serp_data(keyword['id'], serp_data)
    return {"message": "SERP data fetched and stored successfully for active keywords with the specified tag"}

async def get_keywords(project_id: int, tag_id: Optional[int] = None):
    conn = get_db_connection()
    c = conn.cursor()
    if tag_id:
        c.execute('''
            SELECT DISTINCT k.* FROM keywords k
            JOIN keyword_tags kt ON k.id = kt.keyword_id
            WHERE k.project_id = ? AND kt.tag_id = ?
        ''', (project_id, tag_id))
    else:
        c.execute("SELECT * FROM keywords WHERE project_id = ?", (project_id,))
    keywords = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'project_id', 'keyword', 'active', 'search_volume', 'last_volume_update'], keyword)) for keyword in keywords]

async def get_keywords_by_tag(tag_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT k.* FROM keywords k
        JOIN keyword_tags kt ON k.id = kt.keyword_id
        WHERE kt.tag_id = ?
    ''', (tag_id,))
    keywords = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'project_id', 'keyword', 'active', 'search_volume', 'last_volume_update'], keyword)) for keyword in keywords]

@app.get("/api/rankData")
async def get_rank_data():
    conn = get_db_connection()
    rank_data = conn.execute('''
        SELECT s.id, s.date, k.keyword, p.domain, s.rank, k.id as keyword_id, p.id as project_id, s.search_volume
        FROM serp_data s
        JOIN keywords k ON s.keyword_id = k.id
        JOIN projects p ON k.project_id = p.id
        ORDER BY s.date DESC
    ''').fetchall()
    conn.close()
    result = [dict(zip(['id', 'date', 'keyword', 'domain', 'rank', 'keyword_id', 'project_id', 'search_volume'], row)) for row in rank_data]
    logging.info(f"Rank data: {result}")
    return result

@app.get("/api/serp-data/{serp_data_id}")
async def get_full_serp_data(serp_data_id: int):
    if serp_data_id is None:
        raise HTTPException(status_code=400, detail="SERP data ID is required")
    conn = get_db_connection()
    serp_data = conn.execute('SELECT * FROM serp_data WHERE id = ?', (serp_data_id,)).fetchone()
    conn.close()
    if serp_data:
        result = {
            "id": serp_data['id'],
            "keyword_id": serp_data['keyword_id'],
            "date": serp_data['date'],
            "rank": serp_data['rank'],
            "full_data": json.loads(serp_data['full_data'])
        }
        print("Returning SERP data:", result)
        return result
    raise HTTPException(status_code=404, detail="SERP data not found")

@app.post("/api/fetch-serp-data-single/{keyword_id}")
async def fetch_and_store_single_serp_data(keyword_id: int, request: SerpDataRequest):
    api_source = request.api_source
    logging.info(f"Fetching SERP data for keyword ID {keyword_id} using {api_source}")
    conn = get_db_connection()
    keyword = conn.execute('SELECT keyword, search_volume, last_volume_update FROM keywords WHERE id = ?', (keyword_id,)).fetchone()
    conn.close()
    
    if keyword:
        current_time = datetime.now()
        should_update_volume = (
            keyword['search_volume'] is None or 
            keyword['last_volume_update'] is None or 
            (current_time - datetime.strptime(keyword['last_volume_update'], "%Y-%m-%d %H:%M:%S")).days > 30
        )
        logging.info(f"Should update volume for '{keyword['keyword']}': {should_update_volume}")

        serp_data = await fetch_serp_data(keyword['keyword'])
        
        if should_update_volume and api_source != "disabled":
            search_volume = await fetch_search_volume(keyword['keyword'], api_source)
            logging.info(f"Fetched search volume for '{keyword['keyword']}': {search_volume}")
            # Update the keywords table with the new search volume
            conn = get_db_connection()
            conn.execute('UPDATE keywords SET search_volume = ?, last_volume_update = ? WHERE id = ?',
                         (search_volume, current_time.strftime("%Y-%m-%d %H:%M:%S"), keyword_id))
            conn.commit()
            conn.close()
        else:
            search_volume = keyword['search_volume']
            logging.info(f"Using existing search volume for '{keyword['keyword']}': {search_volume}")

        add_serp_data(keyword_id, serp_data, search_volume, api_source)
        
        return {"message": f"SERP data fetched and stored successfully for keyword ID {keyword_id}"}
    raise HTTPException(status_code=404, detail="Keyword not found")

import logging
import aiohttp
import asyncio

async def fetch_serp_data(project_id):
    logging.info(f"Fetching SERP data for project {project_id}")
    keywords = await get_keywords(project_id)
    active_keywords = [kw for kw in keywords if kw['active']]
    
    for keyword in active_keywords:
        try:
            serp_data = await fetch_serp_data_for_keyword(keyword['keyword'])
            logging.info(f"Fetched SERP data for keyword: {keyword['keyword']}")
            
            # Check if we need to update the search volume
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT search_volume, last_volume_update FROM keywords WHERE id = ?", (keyword['id'],))
            result = c.fetchone()
            current_search_volume, last_update = result if result else (None, None)
            conn.close()

            current_time = datetime.now()
            should_update_volume = (
                current_search_volume is None or 
                last_update is None or 
                (current_time - datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")).days > 30
            )

            if should_update_volume:
                search_volume = await fetch_search_volume(keyword['keyword'])
                logging.info(f"Updated search volume for keyword: {keyword['keyword']}")
            else:
                search_volume = current_search_volume

            add_serp_data(keyword['id'], serp_data, search_volume, api_source='spaceserp')
            logging.info(f"Added SERP data for keyword: {keyword['keyword']}")
            
            # Add a small delay to avoid overwhelming the API
            await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Error fetching SERP data for keyword {keyword['keyword']}: {str(e)}")

    logging.info(f"Completed fetching SERP data for project {project_id}")

async def fetch_serp_data_for_keyword(keyword):
    url = "https://api.spaceserp.com/google/search"
    params = {
        "apiKey": SPACESERP_API_KEY,
        "q": keyword,
        "domain": "google.com",
        "gl": "us",
        "hl": "en",
        "resultFormat": "json",
        "device": "desktop",
        "pageSize": 100,
        "pageNumber": 1
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                logging.error(f"Error fetching SERP data for {keyword}. Status: {response.status}")
                return None

def add_serp_data(keyword_id, serp_data, search_volume, api_source='spaceserp'):
    if not serp_data:
        logging.error(f"No SERP data to add for keyword_id: {keyword_id}")
        return

    conn = get_db_connection()
    c = conn.cursor()
    project_domain = c.execute("SELECT domain FROM projects WHERE id = (SELECT project_id FROM keywords WHERE id = ?)", (keyword_id,)).fetchone()[0]
    rank = next((item['position'] for item in serp_data.get('organic_results', []) if project_domain in item.get('domain', '')), -1)
    full_data = json.dumps(serp_data)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('INSERT INTO serp_data (keyword_id, date, rank, full_data, search_volume, api_source) VALUES (?, ?, ?, ?, ?, ?)',
              (keyword_id, current_time, rank, full_data, search_volume, api_source))
    
    conn.commit()
    conn.close()
    logging.info(f"Added SERP data for keyword_id: {keyword_id}, rank: {rank}, time: {current_time}, api_source: {api_source}")

@app.post("/api/keywords")
async def add_keywords(data: dict):
    project_id = data.get('project_id')
    keywords = data.get('keywords')
    if not project_id or not keywords:
        raise HTTPException(status_code=400, detail="Missing project_id or keywords")
    
    conn = get_db_connection()
    c = conn.cursor()
    added_keywords = []
    
    for keyword in keywords:
        c.execute('INSERT INTO keywords (project_id, keyword, active, search_volume, last_volume_update) VALUES (?, ?, 1, NULL, NULL)', (project_id, keyword))
        keyword_id = c.lastrowid
        added_keywords.append({"id": keyword_id, "project_id": project_id, "keyword": keyword, "active": True, "search_volume": 0})
    
    conn.commit()
    conn.close()
    
    # Update search volumes asynchronously
    for keyword in added_keywords:
        await update_search_volume(keyword['id'], keyword['keyword'])
    
    return added_keywords

@app.get("/api/keywords")
async def get_all_keywords_route():
    return get_all_keywords()

@app.delete("/api/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int):
    delete_keyword_by_id(keyword_id)
    return {"message": "Keyword deleted successfully"}

@app.delete("/projects/{project_id}/keywords")
async def delete_all_keywords(project_id: int):
    delete_keywords_by_project(project_id)
    return {"message": "All keywords for the project deleted successfully"}

@app.put("/api/keywords/{keyword_id}/deactivate")
async def deactivate_keyword(keyword_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE keywords SET active = 0 WHERE id = ?', (keyword_id,))
    conn.commit()
    conn.close()
    return {"message": f"Keyword ID {keyword_id} deactivated successfully"}

@app.put("/api/keywords/{keyword_id}/activate")
async def activate_keyword(keyword_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE keywords SET active = 1 WHERE id = ?', (keyword_id,))
    conn.commit()
    conn.close()
    return {"message": f"Keyword ID {keyword_id} activated successfully"}

@app.delete("/api/serp_data/{serp_data_id}")
async def delete_serp_data(serp_data_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM serp_data WHERE id = ?', (serp_data_id,))
    conn.commit()
    conn.close()
    return {"message": f"SERP data ID {serp_data_id} deleted successfully"}

@app.put("/api/projects/{project_id}/toggle-status")
async def toggle_project_status(project_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE projects SET active = NOT active WHERE id = ?', (project_id,))
    c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    updated_project = c.fetchone()
    conn.commit()
    conn.close()
    return {"id": updated_project[0], "name": updated_project[1], "domain": updated_project[2], "active": bool(updated_project[3])}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM serp_data WHERE keyword_id IN (SELECT id FROM keywords WHERE project_id = ?)', (project_id,))
    c.execute('DELETE FROM keywords WHERE project_id = ?', (project_id,))
    c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
    return {"message": f"Project ID {project_id} deleted successfully"}

@app.post("/api/tags", response_model=Tag)
async def create_tag(tag: TagCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag.name,))
        tag_id = cursor.lastrowid
        conn.commit()
        return {"id": tag_id, "name": tag.name}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Tag already exists")
    finally:
        conn.close()

@app.get("/api/tags", response_model=List[Tag])
async def get_all_tags():
    conn = get_db_connection()
    tags = conn.execute('SELECT * FROM tags').fetchall()
    conn.close()
    return [{"id": tag['id'], "name": tag['name']} for tag in tags]

@app.post("/api/keywords/{keyword_id}/tags/{tag_id}")
async def add_tag_to_keyword(keyword_id: int, tag_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO keyword_tags (keyword_id, tag_id) VALUES (?, ?)', (keyword_id, tag_id))
        conn.commit()
        return {"message": "Tag added to keyword successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Tag already added to this keyword")
    finally:
        conn.close()

@app.delete("/api/keywords/{keyword_id}/tags/{tag_id}")
async def remove_tag_from_keyword(keyword_id: int, tag_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM keyword_tags WHERE keyword_id = ? AND tag_id = ?', (keyword_id, tag_id))
    conn.commit()
    conn.close()
    return {"message": "Tag removed from keyword successfully"}

@app.delete("/api/tags/{tag_id}")
async def delete_tag(tag_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM keyword_tags WHERE tag_id = ?', (tag_id,))
    cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
    conn.commit()
    conn.close()
    return {"message": "Tag deleted successfully"}

@app.post("/api/keywords/bulk-tag")
async def bulk_tag_keywords(data: dict):
    keyword_ids = data.get('keyword_ids', [])
    tag_id = data.get('tag_id')
    if not keyword_ids or not tag_id:
        raise HTTPException(status_code=400, detail="Missing keyword_ids or tag_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for keyword_id in keyword_ids:
            cursor.execute('INSERT OR IGNORE INTO keyword_tags (keyword_id, tag_id) VALUES (?, ?)', (keyword_id, tag_id))
        conn.commit()
        return {"message": "Tags added to keywords successfully"}
    finally:
        conn.close()

@app.get("/api/keywords/{keyword_id}/tags", response_model=List[Tag])
async def get_keyword_tags(keyword_id: int):
    conn = get_db_connection()
    tags = conn.execute('''
        SELECT t.id, t.name
        FROM tags t
        JOIN keyword_tags kt ON t.id = kt.tag_id
        WHERE kt.keyword_id = ?
    ''', (keyword_id,)).fetchall()
    conn.close()
    return [{"id": tag['id'], "name": tag['name']} for tag in tags]

from typing import Optional

class KeywordHistoryEntry(BaseModel):
    date: str
    rank: int
    search_volume: Optional[int] = None

@app.get("/api/keyword-history/{keyword_id}", response_model=List[KeywordHistoryEntry])
async def get_keyword_history(keyword_id: int):
    conn = get_db_connection()
    history = conn.execute('''
        SELECT s.date, s.rank, s.search_volume
        FROM serp_data s
        WHERE s.keyword_id = ?
        ORDER BY s.date DESC
    ''', (keyword_id,)).fetchall()
    conn.close()
    
    if not history:
        raise HTTPException(status_code=404, detail="No history found for this keyword")
    
    return [KeywordHistoryEntry(date=entry['date'], rank=entry['rank'], search_volume=entry['search_volume']) for entry in history]

async def fetch_search_volume_grepwords(keyword):
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

async def fetch_search_volume_dataforseo(keyword):
    url = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    payload = json.dumps([{
        "keywords": [keyword],
        "language_code": "en",
        "sort_by": "relevance",
        "include_adult_keywords": True
    }])
    
    logging.info(f"DataForSEO API request for '{keyword}': URL: {url}, Headers: {headers}, Payload: {payload}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload) as response:
            data = await response.json()
            logging.info(f"DataForSEO API response for '{keyword}': {json.dumps(data, indent=2)}")
            
            if response.status == 200 and data.get("tasks"):
                result = data["tasks"][0]["result"][0]
                volume = result.get("search_volume", 0)
                logging.info(f"Search volume for '{keyword}': {volume}")
                return volume
            else:
                logging.warning(f"No search volume data found for '{keyword}'. Status: {response.status}, Response: {data}")
                return 0

async def fetch_search_volume(keyword, api_source):
    logging.info(f"Fetching search volume for '{keyword}' using {api_source}")
    if api_source == "grepwords":
        return await fetch_search_volume_grepwords(keyword)
    elif api_source == "dataforseo":
        return await fetch_search_volume_dataforseo(keyword)
    else:
        logging.warning(f"API source '{api_source}' not recognized or disabled. Returning 0.")
        return 0

async def update_search_volume(keyword_id, keyword):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    
    c.execute("SELECT search_volume, last_volume_update FROM keywords WHERE id = ?", (keyword_id,))
    result = c.fetchone()
    search_volume, last_update = result if result else (None, None)
    
    current_time = datetime.now()
    should_update = (
        search_volume is None or 
        last_update is None or 
        (current_time - datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")).days > 30
    )
    
    if should_update:
        volume = await fetch_search_volume(keyword)
        c.execute("UPDATE keywords SET search_volume = ?, last_volume_update = ? WHERE id = ?", 
                  (volume, current_time.strftime("%Y-%m-%d %H:%M:%S"), keyword_id))
        conn.commit()
        logging.info(f"Updated search volume for keyword '{keyword}' (ID: {keyword_id}): {volume}")
    else:
        logging.info(f"Skipped updating search volume for keyword '{keyword}' (ID: {keyword_id}): last update was less than 30 days ago")
    
    conn.close()

@app.get("/api/search-volume-api-source")
async def get_search_volume_api_source():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'search_volume_api_source'")
    result = c.fetchone()
    conn.close()
    api_source = result[0] if result else "grepwords"
    logging.info(f"Current API source: {api_source}")
    return {"api_source": api_source}

@app.post("/api/search-volume-api-source")
async def update_search_volume_api_source(data: ApiSourceUpdate):
    logging.info(f"Received data: {data}")
    try:
        if data.api_source not in ["grepwords", "dataforseo", "disabled"]:
            raise HTTPException(status_code=400, detail="Invalid API source")
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("search_volume_api_source", data.api_source))
        conn.commit()
        conn.close()
        return {"message": "API source updated successfully"}
    except Exception as e:
        logging.error(f"Error updating API source: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def calculate_next_run(frequency):
    now = datetime.now()
    if frequency == 'hourly':
        return (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    elif frequency == 'daily':
        return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif frequency == 'weekly':
        return (now + timedelta(weeks=1) - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif frequency == 'monthly':
        next_month = now.replace(day=1) + timedelta(days=32)
        return next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("Invalid frequency")

@app.post("/api/schedules")
async def create_schedule(schedule: Schedule):
    next_run = calculate_next_run(schedule.frequency)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO schedules (name, project_id, tag_id, frequency, next_run)
                 VALUES (?, ?, ?, ?, ?)''',
              (schedule.name, schedule.project_id, schedule.tag_id, schedule.frequency, next_run))
    schedule_id = c.lastrowid
    conn.commit()
    conn.close()

    # Add job to APScheduler
    cron_expression = frequency_to_cron(schedule.frequency)
    scheduler.add_job(
        run_schedule,
        CronTrigger.from_crontab(cron_expression),
        args=[schedule_id],
        id=f"schedule_{schedule_id}",
        replace_existing=True
    )

    return {"id": schedule_id, **schedule.dict(), "next_run": next_run}

@app.get("/api/schedules")
async def get_schedules():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM schedules")
    schedules = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'name', 'project_id', 'tag_id', 'frequency', 'last_run', 'next_run'], schedule)) for schedule in schedules]

@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

    # Remove job from APScheduler
    scheduler.remove_job(f"schedule_{schedule_id}")

    return {"message": f"Schedule {schedule_id} deleted"}

@app.post("/api/schedules/{schedule_id}/run")
async def trigger_schedule(schedule_id: int):
    await run_schedule(schedule_id)
    return {"message": f"Schedule {schedule_id} executed successfully"}

@app.post("/api/schedules/{schedule_id}/run-in-1-minute")
async def schedule_run_in_1_minute(schedule_id: int):
    run_time = datetime.now() + timedelta(minutes=1)
    scheduler.add_job(
        run_schedule,
        trigger=DateTrigger(run_date=run_time),
        args=[schedule_id],
        id=f"onetime_schedule_{schedule_id}_{run_time.timestamp()}",
        replace_existing=False
    )
    return {"message": f"Schedule {schedule_id} set to run at {run_time}"}

async def run_schedule(schedule_id: int):
    logging.info(f"Running schedule {schedule_id}")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
    schedule = c.fetchone()
    
    if not schedule:
        logging.error(f"Schedule {schedule_id} not found")
        conn.close()
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule_dict = dict(zip(['id', 'name', 'project_id', 'tag_id', 'frequency', 'last_run', 'next_run'], schedule))
    
    logging.info(f"Schedule details: {schedule_dict}")

    try:
        if schedule_dict['project_id']:
            logging.info(f"Fetching SERP data for project {schedule_dict['project_id']}")
            await asyncio.create_task(fetch_serp_data(schedule_dict['project_id']))
        elif schedule_dict['tag_id']:
            logging.info(f"Fetching SERP data for tag {schedule_dict['tag_id']}")
            await asyncio.create_task(fetch_serp_data_by_tag(schedule_dict['tag_id']))
        else:
            logging.error("Neither project_id nor tag_id found in schedule")
    except Exception as e:
        logging.error(f"Error fetching SERP data: {str(e)}")
        raise

    now = datetime.now()
    next_run = calculate_next_run(schedule_dict['frequency'])
    logging.info(f"Updating schedule: last_run={now.isoformat()}, next_run={next_run.isoformat()}")
    c.execute("UPDATE schedules SET last_run = ?, next_run = ? WHERE id = ?", 
              (now.isoformat(), next_run.isoformat(), schedule_id))
    conn.commit()
    conn.close()
    logging.info(f"Schedule {schedule_id} execution completed")

def frequency_to_cron(frequency):
    if frequency == 'hourly':
        return '0 * * * *'
    elif frequency == 'daily':
        return '0 0 * * *'
    elif frequency == 'weekly':
        return '0 0 * * 0'
    elif frequency == 'monthly':
        return '0 0 1 * *'
    else:
        raise ValueError("Invalid frequency")

@app.on_event("startup")
async def start_scheduler():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)