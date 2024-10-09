import numpy as np
from fastapi import FastAPI, HTTPException, Body, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import sqlite3
import uvicorn
import secrets
import os
from dotenv import load_dotenv
import aiohttp
from database import (
    init_db,
    # add_serp_data,
    get_keywords,
    get_all_keywords,
    delete_keyword_by_id,
    delete_keywords_by_project,
    get_serp_data_within_date_range,
    add_gsc_domain,
    add_gsc_data,
    get_gsc_domains,
    get_domain_by_id,
    get_projects,
    # backfill_gsc_data,
    update_gsc_credentials_in_db,
    get_gsc_credentials_from_db,
    create_gsc_data_table,
    add_gsc_data_by_keyword_id,
    update_search_volume_if_needed,
    update_project_in_db,
    get_project_by_id,
    add_project,
    get_ctr_cache,
    set_ctr_cache,
    get_gsc_data_by_project,
    get_gsc_data_by_domain,
    get_db_connection
)
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Union, Tuple, Any
import asyncio
from asyncio import Semaphore
import logging
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dateutil import parser
from gsc_auth import create_auth_flow, get_gsc_service
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from gsc_auth import create_auth_flow
import random
from services import fetch_search_volume

gsc_credentials = None

load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

app = FastAPI()

# Initialize the AsyncIOScheduler
scheduler = AsyncIOScheduler()
scheduler.start()

# Ensure the scheduler is shut down gracefully
atexit.register(lambda: scheduler.shutdown())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

# Pydantic models
class ProjectBase(BaseModel):
    name: str
    domain: str
    branded_terms: Optional[str] = None
    conversion_rate: Optional[float] = None
    conversion_value: Optional[float] = None

class Project(ProjectBase):
    id: int
    user_id: Optional[int] = None

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
    tag_id: Optional[int] = None

class DateRangeRequest(BaseModel):
    start: str
    end: str

class LineChartData(BaseModel):
    name: str
    dates: List[str]
    shares: List[float]

class DonutChartData(BaseModel):
    name: str
    share: float

class ShareOfVoiceResponse(BaseModel):
    lineChartData: List[LineChartData]
    donutChartData: List[DonutChartData]

class ShareOfVoiceRequest(BaseModel):
    date_range: DateRangeRequest
    tag_id: Optional[Union[int, str]] = None

class GSCDomain(BaseModel):
    domain: str
    project_id: int

class GSCDataRequest(BaseModel):
    domain_id: int
    start_date: str
    end_date: str

class GSCDomainUpdate(BaseModel):
    user_id: int
    project_id: Optional[int] = None

class ScheduledPull(BaseModel):
    id: int
    project_id: int
    project_name: str
    tag_id: Optional[int] = None
    tag_name: Optional[str] = None
    frequency: str
    last_run: Optional[str] = None
    next_pull: str

class SchedulePullRequest(BaseModel):
    project_id: int
    tag_id: Optional[int] = None
    frequency: str

class GSCDataForDate(BaseModel):
    position: Optional[float]
    clicks: Optional[int]
    impressions: Optional[int]
    ctr: Optional[float]
    query: Optional[str]
    page: Optional[str]

class LastGSCData(BaseModel):
    gscDataForDate: Optional[GSCDataForDate]
    date: Optional[str]

class RankDataEntry(BaseModel):
    id: int
    date: str
    keyword: str
    domain: str
    rank: int
    keyword_id: int
    project_id: int
    search_volume: Optional[int]
    estimated_business_impact: float
    gscDataForDate: Optional[GSCDataForDate]
    dataSourceDate: Optional[str]

class RankDataResponse(BaseModel):
    data: List[RankDataEntry]

# Initialize the database
init_db()

SPACESERP_API_KEY = os.getenv("SPACESERP_API_KEY")
GREPWORDS_API_KEY = os.getenv("GREPWORDS_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

standard_ctr_curve = {
    1: 0.2688,  # 26.88%
    2: 0.1173,  # 11.73%
    3: 0.0708,  # 7.08%
    4: 0.0466,  # 4.66%
    5: 0.0329,  # 3.29%
    6: 0.0235,  # 2.35%
    7: 0.0177,  # 1.77%
    8: 0.0135,  # 1.35%
    9: 0.0109,  # 1.09%
    10: 0.0088,  # 0.88%
    11: 0.0072,  # 0.72%
    12: 0.007,  # 0.7%
    13: 0.0066,  # 0.66%
    14: 0.0063,  # 0.63%
    15: 0.0066,  # 0.66%
    16: 0.0068,  # 0.68%
    17: 0.0075,  # 0.75%
    18: 0.008,  # 0.8%
    19: 0.0067,  # 0.67%
    20: 0.0069,  # 0.69%
    21: 0.0069,  # 0.69%
    22: 0.0069,  # 0.69%
    23: 0.0069,  # 0.69%
    24: 0.0069,  # 0.69%
    25: 0.0069,  # 0.69%
    26: 0.0069,  # 0.69%
    27: 0.0069,  # 0.69%
    28: 0.0069,  # 0.69%
    29: 0.0069,  # 0.69%
    30: 0.0039,  # 0.39%
    31: 0.0039,  # 0.39%
    32: 0.0039,  # 0.39%
    33: 0.0039,  # 0.39%
    34: 0.0039,  # 0.39%
    35: 0.0039,  # 0.39%
    36: 0.0039,  # 0.39%
    37: 0.0039,  # 0.39%
    38: 0.0039,  # 0.39%
    39: 0.0039,  # 0.39%
    40: 0.0019,  # 0.19%
    41: 0.0019,  # 0.19%
    42: 0.0019,  # 0.19%
    43: 0.0019,  # 0.19%
    44: 0.0019,  # 0.19%
    45: 0.0019,  # 0.19%
    46: 0.0019,  # 0.19%
    47: 0.0019,  # 0.19%
    48: 0.0019,  # 0.19%
    49: 0.0019,  # 0.19%
    50: 0.00095,  # 0.095%
    51: 0.00095,  # 0.095%
    52: 0.00095,  # 0.095%
    53: 0.00095,  # 0.095%
    54: 0.00095,  # 0.095%
    55: 0.00095,  # 0.095%
    56: 0.00095,  # 0.095%
    57: 0.00095,  # 0.095%
    58: 0.00095,  # 0.095%
    59: 0.00095,  # 0.095%
    60: 0.000475,  # 0.0475%
    61: 0.000475,  # 0.0475%
    62: 0.000475,  # 0.0475%
    63: 0.000475,  # 0.0475%
    64: 0.000475,  # 0.0475%
    65: 0.000475,  # 0.0475%
    66: 0.000475,  # 0.0475%
    67: 0.000475,  # 0.0475%
    68: 0.000475,  # 0.0475%
    69: 0.000475,  # 0.0475%
    70: 0.0002375,  # 0.02375%
    71: 0.0002375,  # 0.02375%
    72: 0.0002375,  # 0.02375%
    73: 0.0002375,  # 0.02375%
    74: 0.0002375,  # 0.02375%
    75: 0.0002375,  # 0.02375%
    76: 0.0002375,  # 0.02375%
    77: 0.0002375,  # 0.02375%
    78: 0.0002375,  # 0.02375%
    79: 0.0002375,  # 0.02375%
    80: 0.00011875,  # 0.011875%
    81: 0.00011875,  # 0.011875%
    82: 0.00011875,  # 0.011875%
    83: 0.00011875,  # 0.011875%
    84: 0.00011875,  # 0.011875%
    85: 0.00011875,  # 0.011875%
    86: 0.00011875,  # 0.011875%
    87: 0.00011875,  # 0.011875%
    88: 0.00011875,  # 0.011875%
    89: 0.00011875,  # 0.011875%
    90: 0.000059375,  # 0.0059375%
    91: 0.000059375,  # 0.0059375%
    92: 0.000059375,  # 0.0059375%
    93: 0.000059375,  # 0.0059375%
    94: 0.000059375,  # 0.0059375%
    95: 0.000059375,  # 0.0059375%
    96: 0.000059375,  # 0.0059375%
    97: 0.000059375,  # 0.0059375%
    98: 0.000059375,  # 0.0059375%
    99: 0.000059375,  # 0.0059375%
    100: 0.000059375,  # 0.0059375%
}
# From https://www.advancedwebranking.com/free-seo-tools/google-organic-ctr
# Non-branded CTR curve August 2024 (only from 1-20)

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_avg_ctr_for_project_rank(project_id: int, rank: int) -> float:
    """
    Retrieves the average CTR for a given project and rank position from the ctr_cache.

    Args:
        project_id (int): The ID of the project.
        rank (int): The rank position.

    Returns:
        float: The average CTR for the specified rank. Returns 0.0 if not found.
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT avg_ctr_per_position
            FROM ctr_cache
            WHERE project_id = ?
        """, (project_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            avg_ctr_per_position = json.loads(result['avg_ctr_per_position'])
            ctr = avg_ctr_per_position.get(str(rank), 0.0)
            logging.info(f"Retrieved CTR for project_id={project_id}, rank={rank}: {ctr}")
            return float(ctr)
        else:
            logging.warning(f"No CTR cache found for project_id={project_id}. Returning 0.0 CTR.")
            return 0.0
    except sqlite3.Error as e:
        logging.error(f"SQLite error in get_avg_ctr_for_project_rank: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while retrieving CTR data.")
    except Exception as e:
        logging.error(f"Error in get_avg_ctr_for_project_rank: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving CTR data.")

def get_previous_estimated_business_impact(c, keyword_id, current_date, avg_ctr_per_position, conversion_rate_decimal, conversion_value):
    c.execute('''
        SELECT s.date, s.rank, s.search_volume
        FROM serp_data s
        WHERE s.keyword_id = ? AND s.date < ?
        ORDER BY s.date DESC
        LIMIT 1
    ''', (keyword_id, current_date))
    previous_data = c.fetchone()

    if previous_data:
        previous_rank = previous_data['rank']
        if previous_rank is None or previous_rank < 1:
            previous_estimated_business_impact = 0.0
        else:
            if previous_rank > 100:
                previous_rank = 100

            # Use the same avg_ctr_per_position
            avg_ctr = avg_ctr_per_position.get(str(previous_rank), standard_ctr_curve.get(previous_rank, 0.01))
            search_volume = previous_data['search_volume'] or 0

            previous_estimated_traffic = avg_ctr * search_volume
            previous_estimated_business_impact = previous_estimated_traffic * conversion_rate_decimal * conversion_value

        return {'estimated_business_impact': previous_estimated_business_impact}
    else:
        return None

def extract_domain(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    domain = domain.split(':')[0]  # Remove port if present
    return domain.lower().replace('www.', '')

async def perform_pull(pull_id: int):
    try:
        logging.info(f"Starting perform_pull for ID: {pull_id}")
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM scheduled_pulls WHERE id = ?", (pull_id,))
        pull = c.fetchone()
        
        if pull:
            project_id = pull['project_id']
            tag_id = pull['tag_id']
            frequency = pull['frequency']
            current_time = datetime.now(timezone.utc)
            
            # Perform the current pull, regardless of missed pulls
            await update_project_rankings(project_id, tag_id)
            
            # Update last_run and next_pull in the database
            next_pull = calculate_next_pull(frequency, current_time)
            c.execute("UPDATE scheduled_pulls SET last_run = ?, next_pull = ? WHERE id = ?", 
                        (current_time.isoformat(), next_pull.isoformat(), pull_id))
            conn.commit()
            
            logging.info(f"Completed perform_pull for ID: {pull_id}. Next pull scheduled for {next_pull}")
        else:
            logging.warning(f"Scheduled pull with ID {pull_id} not found")
        
        conn.close()
        
        # Reschedule the next pull
        await reschedule_pull(pull_id)
    except Exception as e:
        logging.error(f"Error in perform_pull for ID {pull_id}: {e}")
        # You might want to implement a retry mechanism or alert system here

def reschedule_pull(pull_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scheduled_pulls WHERE id = ?", (pull_id,))
    pull = c.fetchone()
    
    if pull:
        frequency = pull['frequency']
        next_pull = calculate_next_pull(frequency)
        c.execute("UPDATE scheduled_pulls SET next_pull = ? WHERE id = ?", (next_pull.isoformat(), pull_id))
        conn.commit()
        
        scheduler.add_job(
            perform_pull,  # This is an async function
            'date',
            run_date=next_pull,
            args=[pull_id],
            id=f"pull_{pull_id}"
        )
    
    conn.close()

def create_gsc_data_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS gsc_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword_id INTEGER,
            date TEXT NOT NULL,
            clicks INTEGER,
            impressions INTEGER,
            ctr REAL,
            position REAL,
            query TEXT,
            page TEXT,
            FOREIGN KEY (keyword_id) REFERENCES keywords (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_columns_to_gsc_data():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE gsc_data ADD COLUMN query TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        c.execute("ALTER TABLE gsc_data ADD COLUMN page TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

def calculate_next_pull(frequency: str, start_time: Optional[datetime] = None) -> datetime:
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    if frequency == 'daily':
        next_pull = start_time + timedelta(days=1)
    elif frequency == 'weekly':
        next_pull = start_time + timedelta(weeks=1)
    elif frequency == 'monthly':
        next_month = start_time.month + 1
        next_year = start_time.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        next_pull = datetime(next_year, next_month, start_time.day, start_time.hour, start_time.minute, tzinfo=timezone.utc)
    elif frequency == 'test':
        next_pull = start_time + timedelta(minutes=1)  # For testing purposes
    else:
        raise ValueError(f"Invalid frequency: {frequency}")
    return next_pull

async def update_project_rankings(project_id: int, tag_id: Optional[int]):
    try:
        logging.info(f"Starting update_project_rankings for project_id: {project_id}, tag_id: {tag_id}")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Fetch the project details
        c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = c.fetchone()
        
        if project:
            logging.info(f"Project details: {project}")
            # Fetch keywords for the project (and tag if provided)
            if tag_id:
                c.execute("SELECT * FROM keywords WHERE project_id = ? AND id IN (SELECT keyword_id FROM keyword_tags WHERE tag_id = ?)", (project_id, tag_id))
            else:
                c.execute("SELECT * FROM keywords WHERE project_id = ?", (project_id,))
            keywords = c.fetchall()
            
            logging.info(f"Found {len(keywords)} keywords for project")
            
            # Fetch and update rankings for each keyword
            for keyword in keywords:
                logging.info(f"Updating rankings for keyword: {keyword['keyword']}")
                await fetch_and_update_rankings(conn, project, keyword, tag_id)
            
            logging.info(f"Completed update_project_rankings for project_id: {project_id}, tag_id: {tag_id}")
        else:
            logging.warning(f"Project with ID {project_id} not found")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error in update_project_rankings for project_id: {project_id}, tag_id: {tag_id}: {e}")

async def fetch_and_update_rankings(conn, project, keyword, tag_id):
    try:
        serp_data = await fetch_serp_data(keyword['keyword'])
        search_volume = await fetch_search_volume(keyword['keyword'])
        add_serp_data(keyword['id'], serp_data, search_volume)
        logging.info(f"Updated rankings for keyword: {keyword['keyword']}")
    except Exception as e:
        logging.error(f"Error updating rankings for keyword {keyword['keyword']}: {e}")

def initialize_scheduled_pulls():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scheduled_pulls")
    scheduled_pulls = c.fetchall()
    conn.close()

    for pull in scheduled_pulls:
        next_pull = datetime.fromisoformat(pull['next_pull']).replace(tzinfo=timezone.utc)
        if next_pull < datetime.now(timezone.utc):
            next_pull = calculate_next_pull(pull['frequency'])

        scheduler.add_job(
            perform_pull,
            'date',
            run_date=next_pull,
            args=[pull['id']],
            id=f"pull_{pull['id']}"
        )
        logging.info(f"Initialized scheduled pull: ID {pull['id']}, Next pull: {next_pull}")

# Call this function after initializing the scheduler
initialize_scheduled_pulls()

async def fetch_serp_data_for_project(project_id: int, request: SerpDataRequest):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Fetch the project details
    c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = c.fetchone()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Fetch active keywords for the project (and tag if provided)
    if request and request.tag_id:
        c.execute("""
            SELECT k.* FROM keywords k
            JOIN keyword_tags kt ON k.id = kt.keyword_id
            WHERE k.project_id = ? AND kt.tag_id = ? AND k.active = 1
        """, (project_id, request.tag_id))
    else:
        c.execute("SELECT * FROM keywords WHERE project_id = ? AND active = 1", (project_id,))
    
    keywords = c.fetchall()
    conn.close()
    
    serp_data = []
    for keyword in keywords:
        keyword_serp_data = await fetch_serp_data(keyword['keyword'])
        search_volume = await fetch_search_volume(keyword['keyword'])
        add_serp_data(keyword['id'], keyword_serp_data, search_volume)
        serp_data.append({
            "keyword": keyword['keyword'],
            "serp_data": keyword_serp_data,
            "search_volume": search_volume
        })
    
    return serp_data

def extrapolate_ctr(avg_ctr_per_position):
    import numpy as np
    positions = np.array([pos for pos, ctr in avg_ctr_per_position.items() if ctr > 0])
    ctr_values = np.array([ctr for ctr in avg_ctr_per_position.values() if ctr > 0])

    if len(positions) < 2:
        logging.warning("Not enough data points for extrapolation. Skipping extrapolation.")
        return

    # Fit a logarithmic model: CTR = a * ln(Position) + b
    try:
        params = np.polyfit(np.log(positions), ctr_values, 1)
        a, b = params
        # Extrapolate for positions 1 to 100
        for position in range(1, 101):
            if position not in avg_ctr_per_position:
                avg_ctr = a * np.log(position) + b
                # Ensure CTR is not negative
                avg_ctr_per_position[position] = max(avg_ctr, 0.0)
    except Exception as e:
        logging.error(f"Error in CTR extrapolation: {e}")
        # Fallback to standard CTR curve or default value
        pass

def fetch_gsc_data_for_domain(project_id, start_date, end_date):
    conn = get_db_connection()
    c = conn.cursor()
    c.row_factory = sqlite3.Row  # Return rows as dictionaries

    # Fetch the project to get branded terms
    c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    project_row = c.fetchone()
    if not project_row:
        conn.close()
        raise Exception("Project not found")

    project = dict(project_row)

    # Ensure branded_terms is a list of non-empty strings
    branded_terms_raw = project.get('branded_terms') or ''
    branded_terms = [term.strip() for term in branded_terms_raw.split(',') if term.strip()]
    logging.info(f"Branded Terms: {branded_terms}")

    # Fetch GSC data for the project's keywords
    c.execute('''
        SELECT * FROM gsc_data
        WHERE date BETWEEN ? AND ?
        AND keyword_id IN (SELECT id FROM keywords WHERE project_id = ?)
    ''', (start_date, end_date, project_id))

    gsc_data_rows = c.fetchall()
    conn.close()

    # Exclude queries containing branded terms
    non_branded_gsc_data = []
    for row in gsc_data_rows:
        data = dict(row)
        query = data.get('query') or ''
        query_lower = query.lower()
        logging.info(f"Processing query: {query_lower}")
        if not any(branded_term.lower() in query_lower for branded_term in branded_terms):
            non_branded_gsc_data.append(data)

    return non_branded_gsc_data

def compute_avg_ctr_per_position(gsc_data):
    position_data = {}
    for data in gsc_data:
        position = int(float(data['position']))
        if position > 100 or position < 1:
            continue
        position_str = str(position)
        if position_str not in position_data:
            position_data[position_str] = {'clicks': 0, 'impressions': 0}
        position_data[position_str]['clicks'] += data.get('clicks', 0)
        position_data[position_str]['impressions'] += data.get('impressions', 0)

    avg_ctr_per_position = {}
    for position_str in position_data:
        clicks = position_data[position_str]['clicks']
        impressions = position_data[position_str]['impressions']
        if impressions > 0:
            avg_ctr = clicks / impressions
            avg_ctr_per_position[position_str] = avg_ctr
        else:
            pass  # Do not assign zero CTR here

    # Extrapolate missing CTRs
    extrapolate_ctr(avg_ctr_per_position)

    # Incorporate standard CTR values
    for position in range(1, 101):
        position_str = str(position)
        if position_str not in avg_ctr_per_position or avg_ctr_per_position[position_str] == 0.0:
            avg_ctr_per_position[position_str] = standard_ctr_curve.get(position, 0.01)

    return avg_ctr_per_position

def get_cached_avg_ctr_per_position(project_id: int) -> Optional[Dict]:
    cache_entry = get_ctr_cache(project_id)
    now = datetime.now(timezone.utc)
    
    if cache_entry:
        last_updated = cache_entry["last_updated"]
        # Ensure last_updated is timezone-aware
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        
        days_since_update = (now - last_updated).days
        if days_since_update < 90:
            logging.info(f"Using cached avg_ctr_per_position for project {project_id}")
            return cache_entry["avg_ctr_per_position"]
    
    # If cache is missing or expired, recalculate
    avg_ctr_per_position, start_date, end_date = calculate_and_cache_avg_ctr_per_position(project_id)
    set_ctr_cache(project_id, avg_ctr_per_position, now, start_date, end_date)
    logging.info(f"Recalculated and cached avg_ctr_per_position for project {project_id}")
    return avg_ctr_per_position

def calculate_and_cache_avg_ctr_per_position(project_id: int) -> Tuple[Dict, str, str]:
    # Define fixed date range: last 90 days from yesterday
    end_date = datetime.now(timezone.utc).date() - timedelta(days=1)  # Exclude today
    start_date = end_date - timedelta(days=89)  # Total of 90 days

    # Fetch GSC data for the domain
    gsc_data = fetch_gsc_data_for_domain(project_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    avg_ctr_per_position = compute_avg_ctr_per_position(gsc_data)

    return avg_ctr_per_position, start_date.isoformat(), end_date.isoformat()

@app.on_event("startup")
async def startup_event():
    try:
        init_db()  # Initialize the database using database.py's init_db()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise e

@app.get("/api/gsc/oauth2callback")
async def gsc_oauth2callback(state: str, code: str):
    try:
        logging.info(f"Received OAuth callback with state={state} and code={code}")
        
        # Decode the state parameter
        state_data = json.loads(state)
        project_id = state_data.get("project_id")
        csrf_token = state_data.get("csrf_token")
        
        logging.info(f"Parsed project_id: {project_id} and csrf_token: {csrf_token}")
        
        if project_id is None:
            logging.error("Missing project_id in state parameter.")
            raise HTTPException(status_code=400, detail="Missing project ID in state.")
        
        # Verify CSRF token
        expected_project_id = csrf_tokens.get(csrf_token)
        if expected_project_id != project_id:
            logging.error("CSRF token mismatch.")
            raise HTTPException(status_code=400, detail="CSRF token mismatch.")
        
        # Remove the CSRF token as it's single-use
        del csrf_tokens[csrf_token]
        
        flow = create_auth_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        credentials_json = credentials.to_json()
        
        # Store credentials in the database
        update_gsc_credentials_in_db(project_id, credentials_json)
        logging.info(f"GSC credentials updated for project_id={project_id}")
        
        # Redirect frontend to the domain selection page with the project_id
        redirect_url = f"http://localhost:5173/gsc-domain-selection?project_id={project_id}"
        logging.info(f"Redirecting to {redirect_url}")
        return RedirectResponse(url=redirect_url)
    except json.JSONDecodeError:
        logging.exception("Failed to decode state parameter.")
        raise HTTPException(status_code=400, detail="Invalid state parameter format.")
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.exception("An error occurred during the OAuth callback.")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule-rank-pull", response_model=ScheduledPull)
async def schedule_rank_pull(pull: SchedulePullRequest):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Validate project_id
        c.execute("SELECT name FROM projects WHERE id = ?", (pull.project_id,))
        project = c.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=422, detail="Invalid project_id")
        project_name = project['name']
        
        # Validate tag_id if provided
        if pull.tag_id is not None:
            c.execute("SELECT name FROM tags WHERE id = ?", (pull.tag_id,))
            tag = c.fetchone()
            if not tag:
                conn.close()
                raise HTTPException(status_code=422, detail="Invalid tag_id")
            tag_name = tag['name']
        else:
            tag_name = None
        
        next_pull = calculate_next_pull(pull.frequency)
        c.execute("""
            INSERT INTO scheduled_pulls (project_id, tag_id, frequency, next_pull)
            VALUES (?, ?, ?, ?)
        """, (pull.project_id, pull.tag_id, pull.frequency, next_pull.isoformat()))
        pull_id = c.lastrowid
        conn.commit()
        
        # Fetch the inserted scheduled pull with project_name and tag_name
        c.execute("""
            SELECT sp.id, sp.project_id, p.name as project_name, 
                    sp.tag_id, t.name as tag_name, 
                    sp.frequency, sp.next_pull
            FROM scheduled_pulls sp
            LEFT JOIN projects p ON sp.project_id = p.id
            LEFT JOIN tags t ON sp.tag_id = t.id
            WHERE sp.id = ?
        """, (pull_id,))
        scheduled_pull = c.fetchone()
        conn.close()
        
        # Add job to AsyncIOScheduler
        scheduler.add_job(
            perform_pull,
            'date',
            run_date=next_pull,
            args=[pull_id],
            id=f"pull_{pull_id}"
        )
        
        return ScheduledPull(
            id=scheduled_pull['id'],
            project_id=scheduled_pull['project_id'],
            project_name=scheduled_pull['project_name'] or "Unknown Project",
            tag_id=scheduled_pull['tag_id'],
            tag_name=scheduled_pull['tag_name'],
            frequency=scheduled_pull['frequency'],
            last_run=None,
            next_pull=scheduled_pull['next_pull']
        )
    except Exception as e:
        logging.error(f"Error in schedule_rank_pull: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/scheduled-pulls")
async def get_scheduled_pulls():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT sp.id, sp.project_id, p.name as project_name, 
                    sp.tag_id, t.name as tag_name, 
                    sp.frequency, sp.last_run, sp.next_pull
            FROM scheduled_pulls sp
            LEFT JOIN projects p ON sp.project_id = p.id
            LEFT JOIN tags t ON sp.tag_id = t.id
        """)
        scheduled_pulls = c.fetchall()
        conn.close()
        
        return [
            ScheduledPull(
                id=pull['id'],
                project_id=pull['project_id'],
                project_name=pull['project_name'] or "Unknown Project",
                tag_id=pull['tag_id'],
                tag_name=pull['tag_name'],
                frequency=pull['frequency'],
                last_run=pull['last_run'],
                next_pull=pull['next_pull']
            )
            for pull in scheduled_pulls
        ]
    except Exception as e:
        logging.error(f"Error in get_scheduled_pulls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/scheduled-pulls/{pull_id}")
async def delete_scheduled_pull(pull_id: int):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM scheduled_pulls WHERE id = ?", (pull_id,))
        if c.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Scheduled pull not found")
        conn.commit()
        conn.close()
        
        # Remove the job from the scheduler
        try:
            scheduler.remove_job(f"pull_{pull_id}")
        except JobLookupError:
            pass  # Job wasn't scheduled, which is fine
        
        return {"message": "Scheduled pull deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting scheduled pull {pull_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def update_search_volume(keyword_id, keyword):
    conn = sqlite3.connect('seo_rank_tracker.db')
    c = conn.cursor()
    
    c.execute("SELECT search_volume, last_volume_update FROM keywords WHERE id = ?", (keyword_id,))
    result = c.fetchone()
    search_volume, last_update = result if result else (None, None)
    
    current_time = datetime.now(timezone.utc)
    should_update = (
        search_volume is None or 
        last_update is None or 
        (current_time - datetime.fromisoformat(last_update).replace(tzinfo=timezone.utc)).days > 30
    )
    
    if should_update:
        volume = await fetch_search_volume(keyword)
        c.execute("UPDATE keywords SET search_volume = ?, last_volume_update = ? WHERE id = ?", 
                    (volume, current_time.isoformat(), keyword_id))
        conn.commit()
        logging.info(f"Updated search volume for keyword '{keyword}' (ID: {keyword_id}): {volume}")
    else:
        logging.info(f"Skipped updating search volume for keyword '{keyword}' (ID: {keyword_id}): last update was less than 30 days ago")
    
    conn.close()

csrf_tokens = {}

@app.get("/api/gsc/auth")
async def gsc_auth(project_id: int = Query(..., description="Project ID")):
    try:
        flow = create_auth_flow()
        
        csrf_token = secrets.token_urlsafe(16)
        state = json.dumps({"project_id": project_id, "csrf_token": csrf_token})
        
        # Store the csrf_token associated with the project_id
        csrf_tokens[csrf_token] = project_id
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='false',
            state=state
        )
        
        logging.info(f"Generated authorization URL: {authorization_url}")
        logging.info(f"State parameter set to: {state}")
        
        return {"authorization_url": authorization_url}
    except Exception as e:
        logging.error(f"Error in /api/gsc/auth: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/gsc/domains")
async def get_gsc_domains(project_id: int):
    try:
        credentials_json = get_gsc_credentials_from_db(project_id)
        if not credentials_json:
            raise HTTPException(status_code=401, detail="Not authenticated with Google Search Console for this project.")
        
        credentials = Credentials.from_authorized_user_info(json.loads(credentials_json), SCOPES)
        
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Save the refreshed credentials back to the database
            update_gsc_credentials_in_db(project_id, credentials.to_json())
        
        service = build('webmasters', 'v3', credentials=credentials)
        
        sites = service.sites().list().execute()
        domains = [site['siteUrl'] for site in sites.get('siteEntry', [])]
        
        return {"domains": domains}
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error fetching GSC domains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching GSC domains: {str(e)}")

@app.post("/api/gsc/domains")
async def create_gsc_domain(domain: GSCDomain):
    try:
        user_id = 1  # Replace with actual user ID from authentication
        logging.info(f"Adding GSC domain: {domain.domain} for project ID: {domain.project_id} by user ID: {user_id}")
        domain_id = add_gsc_domain(user_id, domain.domain, domain.project_id)
        logging.info(f"GSC domain added successfully with ID: {domain_id}")
        return {"domain_id": domain_id}
    except sqlite3.Error as e:
        logging.error(f"Database error in create_gsc_domain: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        logging.error(f"Unexpected error in create_gsc_domain: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
        
async def fetch_gsc_data_for_project(project_id, request: Optional[SerpDataRequest] = None):
    logging.info(f"Fetching GSC data for project_id: {project_id}")

    # Get the GSC domain for this project
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT domain FROM gsc_domains WHERE project_id = ?", (project_id,))
    domain_result = c.fetchone()

    if not domain_result:
        logging.warning(f"No GSC domain found for project_id: {project_id}")
        return

    domain = domain_result[0]

    # Use the date range from the request, or default to last 7 days
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=90)
    if request and hasattr(request, 'start_date') and hasattr(request, 'end_date'):
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()

    logging.info(f"Fetching GSC data for domain: {domain}, start_date: {start_date}, end_date: {end_date}")

    # Get the keywords being tracked
    c.execute("SELECT id, keyword FROM keywords WHERE project_id = ?", (project_id,))
    keywords = c.fetchall()
    conn.close()

    if not keywords:
        logging.info(f"No keywords found for project_id: {project_id}")
        return

    # Prepare the credentials and GSC service
    credentials_json = get_gsc_credentials_from_db(project_id)
    if not credentials_json:
        logging.error(f"No GSC credentials found for project_id: {project_id}")
        return

    credentials = Credentials.from_authorized_user_info(json.loads(credentials_json), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        # Save the refreshed credentials back to the database
        update_gsc_credentials_in_db(project_id, credentials.to_json())

    service = build('webmasters', 'v3', credentials=credentials)
    site_url = domain

    # Fetch GSC data for each keyword
    for keyword_row in keywords:
        keyword_id = keyword_row['id']
        keyword = keyword_row['keyword']

        # Fetch data for the keyword
        body = {
            'startDate': start_date.strftime("%Y-%m-%d"),
            'endDate': end_date.strftime("%Y-%m-%d"),
            'dimensions': ['date', 'query', 'page'],
            'dimensionFilterGroups': [{
                'filters': [{
                    'dimension': 'query',
                    'operator': 'equals',
                    'expression': keyword
                }]
            }],
            'rowLimit': 25000
        }

        try:
            response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
            if 'rows' in response:
                for row in response['rows']:
                    keys = row.get('keys', [])
                    date = keys[0] if len(keys) > 0 else ''
                    query_value = keys[1] if len(keys) > 1 else ''
                    page = keys[2] if len(keys) > 2 else ''
                    clicks = row.get('clicks', 0)
                    impressions = row.get('impressions', 0)
                    ctr = row.get('ctr', 0)
                    position = row.get('position', 0)
                    # Store the data in the database
                    add_gsc_data_by_keyword_id(keyword_id, date, clicks, impressions, ctr, position, query_value, page)
            else:
                logging.info(f"No GSC data for keyword: {keyword}")
        except Exception as e:
            logging.error(f"Error fetching GSC data for keyword '{keyword}': {str(e)}")
            continue

    logging.info(f"GSC data fetched and stored successfully for project_id: {project_id}")

@app.get("/api/gsc/data")
async def get_gsc_data_endpoint(domain_id: int, start_date: str, end_date: str):
    data = get_gsc_data(domain_id, start_date, end_date)
    return data

@app.get("/api/projects")
async def get_projects():
    conn = get_db_connection()
    try:
        projects = conn.execute('SELECT * FROM projects').fetchall()
        return [dict(project) for project in projects]
    finally:
        conn.close()
    return [dict(project) for project in projects]

@app.post("/api/projects", response_model=Project)
async def create_project(project: ProjectBase):
    user_id = 1  # Use a placeholder user ID for now
    project_id = add_project(project.name, project.domain, project.branded_terms, 
                             project.conversion_rate, project.conversion_value, user_id)
    return {"id": project_id, "user_id": user_id, **project.dict()}

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
    cursor.execute('INSERT INTO keywords (project_id, keyword, active, search_volume, last_volume_update) VALUES (?, ?, 1, NULL, NULL)',
                   (project_id, keyword.keyword))
    keyword_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": keyword_id, "project_id": project_id, **keyword.dict()}

CONCURRENT_REQUESTS = 3  # Adjust this number based on API limits and your server capacity

@app.post("/api/fetch-serp-data/{project_id}")
async def fetch_serp_data_endpoint(project_id: int, request: SerpDataRequest = Body(None)):
    tag_id = request.tag_id if request else None
    keywords = await get_keywords(project_id, tag_id)
    active_keywords = [kw for kw in keywords if kw['active']]

    semaphore = Semaphore(CONCURRENT_REQUESTS)

    async def fetch_and_store(keyword):
        async with semaphore:
            serp_data = await fetch_serp_data(keyword['keyword'])
            # Fetch GSC data for the keyword and store it
            try:
                logging.info(f"Fetching GSC data for keyword: {keyword['keyword']}")
                await fetch_gsc_data_for_keyword(project_id, keyword)
                logging.info(f"GSC data fetched for keyword: {keyword['keyword']}")
            except Exception as e:
                logging.error(f"Error fetching GSC data for keyword {keyword['keyword']}: {e}")
            # Update search volume if needed
            await update_search_volume_if_needed(keyword)
            add_serp_data(keyword['id'], serp_data, keyword['search_volume'])

    tasks = [fetch_and_store(keyword) for keyword in active_keywords]
    await asyncio.gather(*tasks)

    return {"message": f"SERP and GSC data fetched and stored successfully for {len(active_keywords)} keywords"}

@app.get("/api/gsc-data")
async def get_gsc_data(
    project_id: Optional[int] = Query(None, description="Filter by Project ID"),
    domain_id: Optional[int] = Query(None, description="Filter by Domain ID"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD")
):
    if not project_id and not domain_id:
        raise HTTPException(status_code=400, detail="Either project_id or domain_id must be provided.")
    
    # Set default dates if not provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if project_id:
            data = get_gsc_data_by_project(project_id, start_date, end_date)
        else:
            data = get_gsc_data_by_domain(domain_id, start_date, end_date)
        return {"data": data}
    except Exception as e:
        # Log the error details
        logging.error(f"Error fetching GSC data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.post("/api/fetch-serp-data-by-tag/{tag_id}")
async def fetch_and_store_serp_data_by_tag(tag_id: int):
    keywords = await get_keywords_by_tag(tag_id)
    for keyword in keywords:
        if keyword['active']:
            serp_data = await fetch_serp_data(keyword['keyword'])
            # Fetch the search volume for the keyword
            search_volume = await fetch_search_volume(keyword['keyword'])
            add_serp_data(keyword['id'], serp_data, search_volume)
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
def get_rank_data():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT s.id, s.date, k.keyword, p.domain, s.rank, k.id as keyword_id, 
                   p.id as project_id, s.search_volume, p.conversion_rate, p.conversion_value
            FROM serp_data s
            JOIN keywords k ON s.keyword_id = k.id
            JOIN projects p ON k.project_id = p.id
        ''')
        rank_data_rows = c.fetchall()
        conn.close()

        processed_data = []
        for item in rank_data_rows:
            # Calculate estimated_business_impact
            conversion_rate = item['conversion_rate'] or 0.0
            conversion_value = item['conversion_value'] or 0.0
            avg_ctr = get_avg_ctr_for_project_rank(item['project_id'], item['rank'])  # Ensure this returns a float

            if item['search_volume'] is not None and avg_ctr is not None:
                estimated_traffic = avg_ctr * item['search_volume']
                estimated_business_impact = estimated_traffic * conversion_rate * conversion_value
            else:
                estimated_business_impact = 0.0  # Default value

            # Fetch GSC data for the keyword and date
            gsc_data = get_gsc_data_for_keyword_and_date(item['keyword_id'], item['date'])

            if gsc_data:
                # Use current GSC data
                gsc_data_for_date = gsc_data['gscDataForDate']
                data_source_date = item['date']
            else:
                # Fetch the last available GSC data
                last_gsc_data = get_last_available_gsc_data(item['keyword_id'], item['date'])
                if last_gsc_data and 'gscDataForDate' in last_gsc_data:
                    gsc_data_for_date = last_gsc_data['gscDataForDate']
                    data_source_date = last_gsc_data['date']
                else:
                    gsc_data_for_date = {}
                    data_source_date = None
                    logging.warning(f"'gscDataForDate' is missing for keyword_id={item['keyword_id']}, date={item['date']}")

            processed_data.append({
                'id': item['id'],
                'date': item['date'],
                'keyword': item['keyword'],
                'domain': item['domain'],
                'rank': item['rank'],
                'keyword_id': item['keyword_id'],
                'project_id': item['project_id'],
                'search_volume': item['search_volume'],
                'estimated_business_impact': estimated_business_impact,
                'gscDataForDate': gsc_data_for_date,
                'dataSourceDate': data_source_date
            })

        return {"data": processed_data}

    except Exception as e:
        logging.error(f"Error in get_rank_data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_gsc_data_for_keyword_and_date(keyword_id: int, date: str) -> Optional[Dict]:
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT position, clicks, impressions, ctr, query, page
            FROM gsc_data
            WHERE keyword_id = ? AND date = ?
        ''', (keyword_id, date))
        gsc_data = c.fetchone()
        conn.close()
        if gsc_data:
            logging.info(f"GSC data found for keyword_id={keyword_id}, date={date}")
            return {
                'gscDataForDate': {
                    'position': gsc_data['position'],
                    'clicks': gsc_data['clicks'],
                    'impressions': gsc_data['impressions'],
                    'ctr': gsc_data['ctr'],
                    'query': gsc_data['query'],
                    'page': gsc_data['page']
                }
            }
        logging.warning(f"No GSC data found for keyword_id={keyword_id}, date={date}")
        return None
    except sqlite3.Error as e:
        logging.error(f"SQLite error in get_gsc_data_for_keyword_and_date: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while retrieving GSC data.")
    except Exception as e:
        logging.error(f"Error in get_gsc_data_for_keyword_and_date: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving GSC data.")
    
def get_last_available_gsc_data(keyword_id: int, current_date: str) -> Optional[Dict]:
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT date, position, clicks, impressions, ctr
            FROM gsc_data
            WHERE keyword_id = ? AND date < ?
            ORDER BY date DESC
            LIMIT 1
        ''', (keyword_id, current_date))
        last_data = c.fetchone()
        conn.close()
        if last_data:
            logging.info(f"Last available GSC data found for keyword_id={keyword_id}, derived from date={last_data['date']}")
            return {
                'gscDataForDate': {
                    'position': last_data['position'],
                    'clicks': last_data['clicks'],
                    'impressions': last_data['impressions'],
                    'ctr': last_data['ctr']
                },
                'date': last_data['date']
            }
        logging.warning(f"No previous GSC data found for keyword_id={keyword_id} before date={current_date}")
        return None
    except sqlite3.Error as e:
        logging.error(f"SQLite error in get_last_available_gsc_data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while retrieving last available GSC data.")
    except Exception as e:
        logging.error(f"Error in get_last_available_gsc_data: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving last available GSC data.")

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
    keyword = conn.execute('SELECT keyword, search_volume, last_volume_update FROM keywords WHERE id = ?', (keyword_id,)).fetchone()
    conn.close()
    
    if keyword:
        current_time = datetime.now(timezone.utc)
        should_update_volume = (
            keyword['search_volume'] is None or 
            keyword['last_volume_update'] is None or 
            (current_time - datetime.fromisoformat(keyword['last_volume_update']).replace(tzinfo=timezone.utc)).days > 30
        )

        serp_data = await fetch_serp_data(keyword['keyword'])
        
        if should_update_volume:
            search_volume = await fetch_search_volume(keyword['keyword'])
            # Update the keywords table with the new search volume
            conn = get_db_connection()
            conn.execute('UPDATE keywords SET search_volume = ?, last_volume_update = ? WHERE id = ?',
                         (search_volume, current_time.isoformat(), keyword_id))
            conn.commit()
            conn.close()
        else:
            search_volume = keyword['search_volume']

        add_serp_data(keyword_id, serp_data, search_volume)
        
        return {"message": f"SERP data fetched and stored successfully for keyword ID {keyword_id}"}
    raise HTTPException(status_code=404, detail="Keyword not found")

async def fetch_with_retry(session, url, params, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params) as response:
                if response.status == 403:
                    raise HTTPException(status_code=403, detail="SpaceSERP API concurrency limit reached")
                return await response.json()
        except HTTPException as e:
            if e.status_code == 403 and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                raise

async def fetch_serp_data(keyword):
    url = "https://api.spaceserp.com/google/search"
    params = {
        "apiKey": SPACESERP_API_KEY,
        "q": keyword,
        # "location": "Midtown Manhattan,New York,United States",
        "domain": "google.com",
        "gl": "us",
        "hl": "en",
        "resultFormat": "json",
        "device": "desktop",
        "pageSize": 100,
        "pageNumber": 1
    }
    async with aiohttp.ClientSession() as session:
        return await fetch_with_retry(session, url, params)

def add_serp_data(keyword_id, serp_data, search_volume):
    conn = get_db_connection()
    c = conn.cursor()
    # Fetch and normalize project_domain
    project_domain = c.execute("""
        SELECT domain FROM projects WHERE id = (SELECT project_id FROM keywords WHERE id = ?)
    """, (keyword_id,)).fetchone()[0]
    project_domain = extract_domain('http://' + project_domain)

    rank = -1
    for item in serp_data.get('organic_results', []):
        link = item.get('link', '')
        result_domain = extract_domain(link)
        if project_domain == result_domain:
            rank = item.get('position')
            break

    # Log domains for debugging
    logging.info(f"Project domain: {project_domain}")
    logging.info(f"Matched rank: {rank}")
    logging.info(f"Inserted SERP data for keyword_id: {keyword_id}, rank: {rank}")

    full_data = json.dumps(serp_data)
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    c.execute('INSERT INTO serp_data (keyword_id, date, rank, full_data, search_volume) VALUES (?, ?, ?, ?, ?)',
              (keyword_id, current_time, rank, full_data, search_volume))

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
async def get_all_keywords():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM keywords")
        keywords = c.fetchall()
        conn.close()
        return [dict(kw) for kw in keywords]
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Delete associated SERP data
        c.execute("DELETE FROM serp_data WHERE keyword_id = ?", (keyword_id,))
        # Delete the keyword
        c.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Keyword not found")
        conn.commit()
        return {"message": "Keyword and associated data deleted successfully"}
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.delete("/projects/{project_id}/keywords")
async def delete_all_keywords(project_id: int):
    delete_keywords_by_project(project_id)
    return {"message": "All keywords for the project deleted successfully"}

@app.put("/api/keywords/{keyword_id}/deactivate")
async def deactivate_keyword(keyword_id: int):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE keywords SET active = 0 WHERE id = ?", (keyword_id,))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Keyword not found")
        conn.commit()
        return {"message": "Keyword deactivated successfully"}
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@app.put("/api/keywords/{keyword_id}/activate")
async def activate_keyword(keyword_id: int):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE keywords SET active = 1 WHERE id = ?", (keyword_id,))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Keyword not found")
        conn.commit()
        return {"message": "Keyword activated successfully"}
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

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
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Get current status
        c.execute("SELECT active FROM projects WHERE id = ?", (project_id,))
        project = c.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        new_status = 0 if project['active'] else 1
        c.execute("UPDATE projects SET active = ? WHERE id = ?", (new_status, project_id))
        conn.commit()

        # Fetch updated project
        c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        updated_project = c.fetchone()

        return {"message": "Project status toggled successfully", "project": dict(updated_project)}
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

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

async def fetch_search_volume(keyword):
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

@app.post("/api/share-of-voice/{project_id}", response_model=ShareOfVoiceResponse)
async def get_share_of_voice(
    project_id: int, 
    request: ShareOfVoiceRequest
):
    try:
        start_date = request.date_range.start
        end_date = request.date_range.end
        tag_id = request.tag_id

        logging.info(f"Fetching Share of Voice for Project ID {project_id} from {start_date} to {end_date} with Tag ID {tag_id}")

        serp_data = get_serp_data_within_date_range(project_id, start_date, end_date, tag_id)
        logging.info(f"Fetched SERP data: {serp_data}")

        if not serp_data:
            raise HTTPException(status_code=404, detail="No SERP data found for the given criteria.")

        # Calculate Share of Voice (SOV)
        daily_sov = defaultdict(lambda: defaultdict(float))
        total_search_volume = defaultdict(float)
        all_domains = set()

        for entry in serp_data:
            date = parser.parse(entry['date']).date().isoformat()
            rank = entry['rank']
            search_volume = entry['search_volume'] or 0

            # Only consider ranks 1-10 for SOV calculation
            if rank and 1 <= rank <= 10:
                # Parse the full_data to get all domains in top 10
                full_data = json.loads(entry['full_data'])
                for result in full_data.get('organic_results', [])[:10]:
                    domain = result.get('domain')
                    if domain:
                        all_domains.add(domain)
                        position = result.get('position')
                        if position and 1 <= position <= 10:
                            sov_score = (11 - position) / 55  # Example SOV calculation
                            daily_sov[date][domain] += sov_score * search_volume
                total_search_volume[date] += search_volume

        if not daily_sov:
            raise HTTPException(status_code=404, detail="No Share of Voice data available for the given criteria.")

        # Normalize SOV scores
        for date in daily_sov:
            if total_search_volume[date] > 0:
                for domain in daily_sov[date]:
                    daily_sov[date][domain] = (daily_sov[date][domain] / total_search_volume[date]) * 100
            else:
                logging.warning(f"Total search volume for date {date} is 0, skipping normalization")

        # Log the daily_sov for debugging
        logging.info(f"Daily SOV: {dict(daily_sov)}")

        # Prepare data for line chart
        line_chart_data = [
            LineChartData(
                name=domain,
                dates=sorted(daily_sov.keys()),
                shares=[daily_sov[date].get(domain, 0) for date in sorted(daily_sov.keys())]
            )
            for domain in all_domains
        ]

        # Prepare data for donut chart (most recent date)
        most_recent_date = max(daily_sov.keys())
        logging.info(f"Most recent date: {most_recent_date}")
        logging.info(f"SOV for most recent date: {daily_sov[most_recent_date]}")
        
        donut_chart_data = [
            DonutChartData(
                name=domain, 
                share=daily_sov[most_recent_date].get(domain, 0)
            )
            for domain in all_domains
        ]

        logging.info(f"Returning Share of Voice data with {len(line_chart_data)} domains for line chart and {len(donut_chart_data)} domains for donut chart.")

        return ShareOfVoiceResponse(
            lineChartData=line_chart_data,
            donutChartData=donut_chart_data
        )
    except HTTPException as he:
        # Re-raise HTTPException without modification
        raise he
    except Exception as e:
        logging.exception("An error occurred while processing Share of Voice request")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/api/gsc/domains/{domain_id}")
async def set_gsc_domain(domain_id: int, update: GSCDomainUpdate):
    logging.info(f"Received update request for domain {domain_id}: {update}")
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Set row factory to return rows as dictionaries
        cursor = conn.cursor()

        # First, check if the domain exists
        cursor.execute("SELECT id FROM gsc_domains WHERE id = ?", (domain_id,))
        domain = cursor.fetchone()

        if not domain:
            raise HTTPException(status_code=404, detail="GSC domain not found")

        # Update the domain with the new user_id and project_id
        update_query = """
        UPDATE gsc_domains
        SET user_id = ?, project_id = ?
        WHERE id = ?
        """
        cursor.execute(update_query, (update.user_id, update.project_id, domain_id))

        # If a project_id is provided, ensure it exists
        if update.project_id is not None:
            cursor.execute("SELECT id FROM projects WHERE id = ?", (update.project_id,))
            project = cursor.fetchone()
            if not project:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Project not found")

        conn.commit()

        # Fetch the updated domain details
        cursor.execute("""
        SELECT gd.id, gd.domain, gd.user_id, gd.project_id, p.name as project_name
        FROM gsc_domains gd
        LEFT JOIN projects p ON gd.project_id = p.id
        WHERE gd.id = ?
        """, (domain_id,))
        updated_domain = cursor.fetchone()

        return {
            "domain_id": updated_domain['id'],
            "domain": updated_domain['domain'],
            "user_id": updated_domain['user_id'],
            "project_id": updated_domain['project_id'],
            "project_name": updated_domain['project_name']
        }

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/api/gsc/domains/{domain_id}")
async def get_gsc_domain(domain_id: int):
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Set row factory to return rows as dictionaries
        cursor = conn.cursor()
        cursor.execute("""
        SELECT gd.id, gd.domain, gd.user_id, gd.project_id, p.name as project_name
        FROM gsc_domains gd
        LEFT JOIN projects p ON gd.project_id = p.id
        WHERE gd.id = ?
        """, (domain_id,))
        domain = cursor.fetchone()
        conn.close()

        if not domain:
            raise HTTPException(status_code=404, detail="GSC domain not found")

        return {
            "domain_id": domain['id'],
            "domain": domain['domain'],
            "user_id": domain['user_id'],
            "project_id": domain['project_id'],
            "project_name": domain['project_name']
        }
    except Exception as e:
        logging.error(f"Error retrieving GSC domain: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving GSC domain")
    
async def fetch_gsc_data_for_keyword(project_id, keyword):
    try:
        # Retrieve GSC credentials from the database
        credentials_json = get_gsc_credentials_from_db(project_id)
        if not credentials_json:
            logging.warning(f"No GSC credentials found for project_id: {project_id}")
            return

        # Load credentials and refresh if necessary
        credentials = Credentials.from_authorized_user_info(json.loads(credentials_json), SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Save the refreshed credentials back to the database
            update_gsc_credentials_in_db(project_id, credentials.to_json())

        # Build the GSC service
        service = build('webmasters', 'v3', credentials=credentials)

        # Get the domain associated with the project
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT domain FROM gsc_domains WHERE project_id = ?", (project_id,))
        result = c.fetchone()
        if not result:
            logging.warning(f"No GSC domain associated with project_id: {project_id}")
            conn.close()
            return
        site_url = result[0]
        conn.close()

        # Use the date range, e.g., last 7 days
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=7)

        # Adjust the dimensions to include 'query' and 'page'
        body = {
            'startDate': start_date.strftime("%Y-%m-%d"),
            'endDate': end_date.strftime("%Y-%m-%d"),
            'dimensions': ['date', 'query', 'page'],
            'dimensionFilterGroups': [{
                'filters': [{
                    'dimension': 'query',
                    'operator': 'equals',
                    'expression': keyword['keyword']
                }]
            }],
            'rowLimit': 25000
        }

        logging.info(f"Fetching GSC data for keyword '{keyword['keyword']}' from {start_date} to {end_date}")
        response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        logging.info(f"GSC API response for '{keyword['keyword']}': {json.dumps(response, indent=2)}")

        if 'rows' in response:
            for row in response['rows']:
                keys = row.get('keys', [])
                date = keys[0] if len(keys) > 0 else ''
                query_value = keys[1] if len(keys) > 1 else ''
                page = keys[2] if len(keys) > 2 else ''
                clicks = row.get('clicks', 0)
                impressions = row.get('impressions', 0)
                ctr = row.get('ctr', 0)
                position = row.get('position', 0)
                # Store the data in the database
                add_gsc_data_by_keyword_id(keyword['id'], date, clicks, impressions, ctr, position, query_value, page)
            logging.info(f"Stored GSC data for keyword '{keyword['keyword']}'")
        else:
            logging.info(f"No GSC data for keyword: {keyword['keyword']}")
    except Exception as e:
        logging.error(f"Error fetching GSC data for keyword '{keyword['keyword']}': {str(e)}")
    
@app.put("/api/projects/{project_id}", response_model=Project)
async def update_project(project_id: int, project: ProjectBase):
    updated_project = update_project_in_db(project_id, project.dict())
    if updated_project:
        return updated_project
    raise HTTPException(status_code=404, detail="Project not found")

@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    try:
        project = get_project_by_id(project_id)
        if project:
            # Ensure all fields from the Project model are present
            for field in Project.__fields__:
                if field not in project:
                    project[field] = None
            return Project(**project)
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        logging.error(f"Error in get_project endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
def refresh_ctr_cache():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT project_id FROM projects")
    project_ids = [row['project_id'] for row in c.fetchall()]
    conn.close()

    for project_id in project_ids:
        avg_ctr_per_position, start_date, end_date = calculate_and_cache_avg_ctr_per_position(project_id)
        set_ctr_cache(project_id, avg_ctr_per_position, datetime.now(timezone.utc), start_date, end_date)
        logging.info(f"Refreshed avg_ctr_per_position cache for project {project_id}")

# Initialize and start the scheduler
# scheduler = BackgroundScheduler()
# scheduler.add_job(refresh_ctr_cache, 'interval', days=90)
# scheduler.start()

# Ensure scheduler is shut down gracefully
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)