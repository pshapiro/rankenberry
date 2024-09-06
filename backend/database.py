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
                  domain TEXT NOT NULL,
                  active INTEGER DEFAULT 1)''')

    c.execute('''CREATE TABLE IF NOT EXISTS keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER,
                  keyword TEXT NOT NULL,
                  active INTEGER DEFAULT 1,
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')

    c.execute('ALTER TABLE keywords ADD COLUMN active INTEGER DEFAULT 1')

    c.execute('''CREATE TABLE IF NOT EXISTS serp_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  date TEXT NOT NULL,
                  rank INTEGER,
                  full_data TEXT,
                  api_source TEXT DEFAULT 'grepwords',
                  FOREIGN KEY (keyword_id) REFERENCES keywords (id))''')

    c.execute('''ALTER TABLE keywords ADD COLUMN search_volume INTEGER DEFAULT 0''')
    c.execute('''ALTER TABLE keywords ADD COLUMN last_volume_update TEXT''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')

    # Insert default value for search_volume_api_source if it doesn't exist
    c.execute('''INSERT OR IGNORE INTO settings (key, value) 
                 VALUES ('search_volume_api_source', 'grepwords')''')

    # Add api_source column to serp_data table if it doesn't exist
    c.execute('''
        PRAGMA table_info(serp_data)
    ''')
    columns = [column[1] for column in c.fetchall()]
    if 'api_source' not in columns:
        c.execute('''
            ALTER TABLE serp_data
            ADD COLUMN api_source TEXT DEFAULT 'grepwords'
        ''')

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
    c.execute("INSERT INTO keywords (project_id, keyword, active) VALUES (?, ?, 1)", (project_id, keyword))
    keyword_id = c.lastrowid
    conn.commit()
    conn.close()
    return keyword_id

def add_serp_data(keyword_id, serp_data, search_volume):
    conn = get_db_connection()
    c = conn.cursor()
    project_domain = c.execute("SELECT domain FROM projects WHERE id = (SELECT project_id FROM keywords WHERE id = ?)", (keyword_id,)).fetchone()[0]
    rank = next((item['position'] for item in serp_data.get('organic_results', []) if project_domain in item.get('domain', '')), -1)
    full_data = json.dumps(serp_data)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('INSERT INTO serp_data (keyword_id, date, rank, full_data, search_volume) VALUES (?, ?, ?, ?, ?)',
              (keyword_id, current_time, rank, full_data, search_volume))
    
    conn.commit()
    conn.close()

def get_projects():
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    c.execute("SELECT id, name, domain, COALESCE(active, 1) as active FROM projects")
    projects = c.fetchall()
    conn.close()
    return [{"id": p[0], "name": p[1], "domain": p[2], "active": bool(p[3])} for p in projects]

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
    c.execute("SELECT id, project_id, keyword, COALESCE(active, 1) as active FROM keywords")
    keywords = c.fetchall()
    conn.close()
    return [{"id": k[0], "project_id": k[1], "keyword": k[2], "active": bool(k[3])} for k in keywords]

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