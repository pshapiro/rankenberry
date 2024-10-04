from typing import List, Dict, Optional
import sqlite3
from datetime import datetime
import logging
import json
from dateutil import parser
import os
from fastapi import HTTPException
from datetime import datetime, timedelta

# Determine the absolute path to the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'seo_rank_tracker.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS gsc_domains
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  domain TEXT NOT NULL,
                  project_id INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS gsc_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  domain_id INTEGER,
                  keyword TEXT NOT NULL,
                  date TEXT NOT NULL,
                  clicks INTEGER,
                  impressions INTEGER,
                  ctr REAL,
                  FOREIGN KEY (domain_id) REFERENCES gsc_domains (id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  domain TEXT NOT NULL,
                  branded_terms TEXT,
                  conversion_rate REAL,
                  conversion_value REAL,
                  active INTEGER DEFAULT 1,
                  user_id INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS keywords
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER,
                  keyword TEXT NOT NULL,
                  active INTEGER DEFAULT 1,
                  search_volume INTEGER DEFAULT 0,
                  last_volume_update TEXT,
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS serp_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  date TEXT NOT NULL,
                  rank INTEGER,
                  full_data TEXT,
                  search_volume INTEGER,
                  FOREIGN KEY (keyword_id) REFERENCES keywords (id))''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS ctr_cache (
            project_id INTEGER PRIMARY KEY,
            avg_ctr_per_position TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            date_range_start TEXT NOT NULL,
            date_range_end TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')

    conn.commit()
    conn.close()

def add_project(name, domain, branded_terms, conversion_rate, conversion_value, user_id):
    logging.info(f"Adding project to database: {name}, {domain}, user_id: {user_id}")
    try:
        conn = sqlite3.connect('seo_rank_tracker.db')
        c = conn.cursor()
        c.execute("INSERT INTO projects (name, domain, branded_terms, conversion_rate, conversion_value, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
                  (name, domain, branded_terms, conversion_rate, conversion_value, user_id))
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

def create_gsc_data_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gsc_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  keyword_id INTEGER,
                  date TEXT,
                  clicks INTEGER,
                  impressions INTEGER,
                  ctr REAL,
                  position REAL,
                  FOREIGN KEY (keyword_id) REFERENCES keywords (id))''')
    conn.commit()
    conn.close()

def get_domain_by_id(domain_id: int) -> str:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT domain FROM gsc_domains WHERE id = ?", (domain_id,))
    domain = c.fetchone()
    conn.close()
    if domain:
        return f"https://{domain[0]}"
    else:
        raise HTTPException(status_code=404, detail="Domain not found")
    
def get_projects(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, domain, COALESCE(active, 1) as active FROM projects WHERE user_id = ?", (user_id,))
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

def add_gsc_domain(user_id, domain, project_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO gsc_domains (user_id, domain, project_id) VALUES (?, ?, ?)", (user_id, domain, project_id))
    domain_id = c.lastrowid
    conn.commit()
    conn.close()
    return domain_id

def add_gsc_data(project_id, keyword, date, clicks, impressions, ctr, position, query, page):
    conn = get_db_connection()
    c = conn.cursor()
    # Only proceed if the keyword exists in the database
    c.execute("SELECT id FROM keywords WHERE project_id = ? AND keyword = ?", (project_id, keyword))
    result = c.fetchone()
    if result:
        keyword_id = result[0]
        # Insert the GSC data
        c.execute('''
            INSERT INTO gsc_data 
            (keyword_id, date, clicks, impressions, ctr, position, query, page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (keyword_id, date, clicks, impressions, ctr, position, query, page))
        conn.commit()
        logging.info(f"Added GSC data for keyword_id: {keyword_id}, date: {date}")
    else:
        # Keyword not being tracked; ignore
        logging.info(f"Keyword '{keyword}' not found in project_id {project_id}. Skipping GSC data.")
    conn.close()

def get_gsc_domains(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, domain FROM gsc_domains WHERE user_id = ?", (user_id,))
    domains = c.fetchall()
    conn.close()
    return [{"id": d[0], "domain": d[1]} for d in domains]

def get_gsc_data(domain_id, start_date, end_date):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT keyword, date, clicks, impressions, ctr
        FROM gsc_data
        WHERE domain_id = ? AND date BETWEEN ? AND ?
    """, (domain_id, start_date, end_date))
    data = c.fetchall()
    conn.close()
    return [{"keyword": d[0], "date": d[1], "clicks": d[2], "impressions": d[3], "ctr": d[4]} for d in data]

def get_serp_data_within_date_range(project_id, start_date, end_date, tag_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT s.date, s.rank, s.search_volume, p.domain, s.full_data
        FROM serp_data s
        JOIN keywords k ON s.keyword_id = k.id
        JOIN projects p ON k.project_id = p.id
        WHERE k.project_id = ? AND s.date BETWEEN ? AND ?
    '''
    params = (project_id, start_date, end_date)

    if tag_id:
        query += ' AND k.id IN (SELECT keyword_id FROM keyword_tags WHERE tag_id = ?)'
        params += (tag_id,)

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()

    return [
        {
            'date': parser.parse(row['date']).date().isoformat(),
            'rank': row['rank'],
            'search_volume': row['search_volume'],
            'domain': row['domain'],
            'full_data': row['full_data']
        }
        for row in data
    ]

def create_gsc_data_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gsc_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER,
                date TEXT NOT NULL,
                clicks INTEGER,
                impressions INTEGER,
                ctr REAL,
                position REAL,
                query TEXT,
                page TEXT,
                FOREIGN KEY (keyword_id) REFERENCES keywords (id)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gsc_credentials
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project_id INTEGER UNIQUE,
                  credentials TEXT,
                  FOREIGN KEY (project_id) REFERENCES projects (id))''')
    conn.commit()
    conn.close()

def get_gsc_credentials_from_db(project_id):
    try:
        conn = sqlite3.connect('seo_rank_tracker.db')
        c = conn.cursor()
        c.execute("SELECT credentials FROM gsc_credentials WHERE project_id = ?", (project_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"SQLite error in get_gsc_credentials_from_db: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")

def update_gsc_credentials_in_db(project_id, credentials_json):
    try:
        conn = sqlite3.connect('seo_rank_tracker.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO gsc_credentials (project_id, credentials)
            VALUES (?, ?)
            ON CONFLICT(project_id) DO UPDATE SET credentials=excluded.credentials
        """, (project_id, credentials_json))
        conn.commit()
        conn.close()
        logging.info(f"GSC credentials updated for project_id={project_id}")
    except sqlite3.Error as e:
        logging.error(f"SQLite error in update_gsc_credentials_in_db: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")

def add_gsc_data(project_id, keyword, date, clicks, impressions, ctr, position):
    conn = get_db_connection()
    c = conn.cursor()
    
    # First, get the keyword_id
    c.execute("SELECT id FROM keywords WHERE project_id = ? AND keyword = ?", (project_id, keyword))
    result = c.fetchone()
    if result:
        keyword_id = result[0]
    else:
        # If the keyword doesn't exist, create it
        c.execute("INSERT INTO keywords (project_id, keyword) VALUES (?, ?)", (project_id, keyword))
        keyword_id = c.lastrowid
    
    c.execute('''INSERT OR REPLACE INTO gsc_data 
                 (keyword_id, date, clicks, impressions, ctr, position)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (keyword_id, date, clicks, impressions, ctr, position))
    conn.commit()
    conn.close()
    logging.info(f"Added GSC data for keyword_id: {keyword_id}, date: {date}")

async def backfill_gsc_data(project_id, keyword_id, keyword):
    # Get the earliest date we have data for
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT MIN(date) FROM gsc_data WHERE keyword_id = ?", (keyword_id,))
    earliest_date = c.fetchone()[0]
    conn.close()

    if earliest_date:
        earliest_date = datetime.strptime(earliest_date, "%Y-%m-%d").date()
        end_date = earliest_date - timedelta(days=1)
        start_date = end_date - timedelta(days=30)  # Backfill up to 30 days

        gsc_data = await fetch_gsc_data(project_id, keyword, start_date, end_date)
        add_gsc_data(project_id, keyword_id, gsc_data)
    
def add_gsc_data_by_keyword_id(keyword_id, date, clicks, impressions, ctr, position, query, page):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO gsc_data (keyword_id, date, clicks, impressions, ctr, position, query, page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (keyword_id, date, clicks, impressions, ctr, position, query, page))
        conn.commit()
        logging.info(f"Added GSC data for keyword_id: {keyword_id}, date: {date}")
    except Exception as e:
        logging.error(f"Error adding GSC data for keyword_id {keyword_id}: {str(e)}")
    finally:
        conn.close()

async def update_search_volume_if_needed(keyword):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT search_volume, last_volume_update FROM keywords WHERE id = ?", (keyword['id'],))
    result = c.fetchone()
    search_volume, last_update = result if result else (None, None)
    
    current_time = datetime.now()
    should_update = (
        search_volume is None or 
        last_update is None or 
        (current_time - datetime.fromisoformat(last_update)).days > 30
    )
    
    if should_update:
        search_volume = await fetch_search_volume(keyword['keyword'])
        c.execute("UPDATE keywords SET search_volume = ?, last_volume_update = ? WHERE id = ?", 
                  (search_volume, current_time.strftime("%Y-%m-%d %H:%M:%S"), keyword['id']))
        conn.commit()
        keyword['search_volume'] = search_volume  # Update the keyword dictionary
    else:
        keyword['search_volume'] = search_volume
    conn.close()

def update_project_in_db(project_id, project_data):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE projects
            SET name = ?, domain = ?, branded_terms = ?, conversion_rate = ?, conversion_value = ?
            WHERE id = ?
        """, (project_data['name'], project_data['domain'], project_data['branded_terms'], 
              project_data['conversion_rate'], project_data['conversion_value'], project_id))
        conn.commit()
        if c.rowcount > 0:
            return get_project_by_id(project_id)
        return None
    finally:
        conn.close()

def get_project_by_id(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Get the list of columns in the projects table
        c.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in c.fetchall()]
        
        # Construct the SELECT statement based on existing columns
        select_columns = ["id", "name", "domain"]
        if "branded_terms" in columns:
            select_columns.append("branded_terms")
        if "conversion_rate" in columns:
            select_columns.append("conversion_rate")
        if "conversion_value" in columns:
            select_columns.append("conversion_value")
        if "user_id" in columns:
            select_columns.append("user_id")
        
        select_statement = f"SELECT {', '.join(select_columns)} FROM projects WHERE id = ?"
        
        logging.info(f"Executing SQL: {select_statement} with project_id: {project_id}")
        c.execute(select_statement, (project_id,))
        project = c.fetchone()
        
        if project:
            result = {
                "id": project[0],
                "name": project[1],
                "domain": project[2],
            }
            column_index = 3  # Start after id, name, and domain
            if "branded_terms" in columns and column_index < len(project):
                result["branded_terms"] = project[column_index]
                column_index += 1
            if "conversion_rate" in columns and column_index < len(project):
                result["conversion_rate"] = project[column_index]
                column_index += 1
            if "conversion_value" in columns and column_index < len(project):
                result["conversion_value"] = project[column_index]
                column_index += 1
            if "user_id" in columns and column_index < len(project):
                result["user_id"] = project[column_index]
            
            logging.info(f"Retrieved project: {result}")
            return result
        else:
            logging.info(f"No project found with id: {project_id}")
            return None
    except Exception as e:
        logging.error(f"Error in get_project_by_id: {str(e)}")
        raise
    finally:
        conn.close()

def get_ctr_cache(project_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT avg_ctr_per_position, last_updated, date_range_start, date_range_end
        FROM ctr_cache
        WHERE project_id = ?
    ''', (project_id,))
    cache_entry = c.fetchone()
    conn.close()
    
    if cache_entry:
        parsed_last_updated = parser.parse(cache_entry["last_updated"])
        # Ensure the datetime is timezone-aware. If not, set it to UTC.
        if parsed_last_updated.tzinfo is None:
            parsed_last_updated = parsed_last_updated.replace(tzinfo=timezone.utc)
        
        return {
            "avg_ctr_per_position": json.loads(cache_entry["avg_ctr_per_position"]),
            "last_updated": parsed_last_updated,
            "date_range_start": cache_entry["date_range_start"],
            "date_range_end": cache_entry["date_range_end"]
        }
    return None

def set_ctr_cache(project_id: int, avg_ctr_per_position: Dict, last_updated: datetime, start_date: str, end_date: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        REPLACE INTO ctr_cache (project_id, avg_ctr_per_position, last_updated, date_range_start, date_range_end)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        project_id,
        json.dumps(avg_ctr_per_position),
        last_updated.isoformat(),
        start_date,
        end_date
    ))
    last_updated.isoformat()
    conn.commit()
    conn.close()