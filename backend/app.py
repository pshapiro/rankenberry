from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uvicorn
import os
from dotenv import load_dotenv
import aiohttp
from database import add_serp_data, get_keywords, get_all_keywords, delete_keyword_by_id, delete_keywords_by_project
import json
from datetime import datetime
from typing import List

load_dotenv()

app = FastAPI()

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
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS serp_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  date TEXT NOT NULL,
                  rank INTEGER,
                  full_data TEXT NOT NULL,
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
    conn.commit()
    conn.close()

# Initialize the database
init_db()

SPACESERP_API_KEY = os.getenv("SPACESERP_API_KEY")

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
    cursor.execute('INSERT INTO keywords (project_id, keyword) VALUES (?, ?)',
                   (project_id, keyword.keyword))
    keyword_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": keyword_id, "project_id": project_id, **keyword.dict()}

@app.post("/api/fetch-serp-data/{project_id}")
async def fetch_and_store_serp_data(project_id: int):
    keywords = await get_keywords(project_id)
    for keyword in keywords:
        if keyword['active']:
            serp_data = await fetch_serp_data(keyword['keyword'])
            add_serp_data(keyword['id'], serp_data)
    return {"message": "SERP data fetched and stored successfully for active keywords"}

@app.get("/api/rankData")
async def get_rank_data():
    conn = get_db_connection()
    rank_data = conn.execute('''
        SELECT s.id, s.date, k.keyword, p.domain, s.rank, k.id as keyword_id, p.id as project_id
        FROM serp_data s
        JOIN keywords k ON s.keyword_id = k.id
        JOIN projects p ON k.project_id = p.id
        ORDER BY s.date DESC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in rank_data]

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
async def fetch_and_store_single_serp_data(keyword_id: int):
    conn = get_db_connection()
    keyword = conn.execute('SELECT keyword FROM keywords WHERE id = ?', (keyword_id,)).fetchone()
    conn.close()
    if keyword:
        serp_data = await fetch_serp_data(keyword['keyword'])
        add_serp_data(keyword_id, serp_data)
        return {"message": f"SERP data fetched and stored successfully for keyword ID {keyword_id}"}
    raise HTTPException(status_code=404, detail="Keyword not found")

async def fetch_serp_data(keyword):
    url = "https://api.spaceserp.com/google/search"
    params = {
        "apiKey": SPACESERP_API_KEY,
        "q": keyword,
        "location": "Midtown Manhattan,New York,United States",
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
            return await response.json()

def add_serp_data(keyword_id, serp_data):
    conn = get_db_connection()
    c = conn.cursor()
    project_domain = c.execute("SELECT domain FROM projects WHERE id = (SELECT project_id FROM keywords WHERE id = ?)", (keyword_id,)).fetchone()[0]
    rank = next((item['position'] for item in serp_data.get('organic_results', []) if project_domain in item.get('domain', '')), -1)
    full_data = json.dumps(serp_data)
    conn.execute('INSERT INTO serp_data (keyword_id, date, rank, full_data) VALUES (?, ?, ?, ?)',
                 (keyword_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), rank, full_data))
    conn.commit()
    conn.close()

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
        c.execute('INSERT INTO keywords (project_id, keyword, active) VALUES (?, ?, 1)', (project_id, keyword))
        keyword_id = c.lastrowid
        added_keywords.append({"id": keyword_id, "project_id": project_id, "keyword": keyword, "active": True})
    
    conn.commit()
    conn.close()
    
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

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)