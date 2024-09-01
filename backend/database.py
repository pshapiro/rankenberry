import sqlite3
from datetime import datetime
import logging
import json

def init_db():
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  domain TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER,
                  keyword TEXT NOT NULL,
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS serp_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  date TEXT NOT NULL,
                  rank INTEGER,
                  full_data TEXT,
                  FOREIGN KEY (keyword_id) REFERENCES keywords (id))''')

    conn.commit()
    conn.close()

def add_project(name, domain):
    logging.info(f"Adding project to database: {name}, {domain}")
    try:
        conn = sqlite3.connect('seo_rank_tracker.db')
        c = conn.cursor()
        c.execute("INSERT INTO projects (name, domain) VALUES (?, ?)", (name, domain))
        project_id = c.lastrowid
        conn.commit()
        logging.info(f"Project added successfully with ID: {project_id}")
        return project_id
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def add_keyword(project_id, keyword):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("INSERT INTO keywords (project_id, keyword) VALUES (?, ?)", (project_id, keyword))
    keyword_id = c.lastrowid
    conn.commit()
    conn.close()
    return keyword_id

def add_serp_data(keyword_id, serp_data):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Find the rank of the project's domain
    project_domain = c.execute("SELECT domain FROM projects WHERE id = (SELECT project_id FROM keywords WHERE id = ?)", (keyword_id,)).fetchone()[0]
    rank = next((result['position'] for result in serp_data['organic_results'] if project_domain in result['domain']), None)
    
    # Store only the organic_results
    organic_results = serp_data.get('organic_results', [])
    
    c.execute("INSERT INTO serp_data (keyword_id, date, rank, full_data) VALUES (?, ?, ?, ?)",
              (keyword_id, date_time, rank, json.dumps(organic_results)))
    conn.commit()
    conn.close()

def get_projects():
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("SELECT * FROM projects")
    projects = c.fetchall()
    conn.close()
    return projects

async def get_keywords(project_id):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("SELECT * FROM keywords WHERE project_id = ?", (project_id,))
    keywords = c.fetchall()
    conn.close()
    return [dict(zip(['id', 'project_id', 'keyword'], keyword)) for keyword in keywords]

def get_serp_data(keyword_id):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("SELECT * FROM serp_data WHERE keyword_id = ? ORDER BY date DESC", (keyword_id,))
    serp_data = c.fetchall()
    conn.close()
    return serp_data

def get_all_keywords():
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("SELECT * FROM keywords")
    keywords = c.fetchall()
    conn.close()
    return [{"id": k[0], "project_id": k[1], "keyword": k[2]} for k in keywords]

def delete_keyword_by_id(keyword_id):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
    c.execute("DELETE FROM serp_data WHERE keyword_id = ?", (keyword_id,))
    conn.commit()
    conn.close()

def delete_keywords_by_project(project_id):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("DELETE FROM serp_data WHERE keyword_id IN (SELECT id FROM keywords WHERE project_id = ?)", (project_id,))
    c.execute("DELETE FROM keywords WHERE project_id = ?", (project_id,))
    conn.commit()
    conn.close()