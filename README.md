# ![rankenberry-logo](https://github.com/user-attachments/assets/7222a62b-52e2-4474-afa7-653362a0dfa1) Rankenberry: SEO Rank Tracker

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

"A simple rank tracking application leveraging a 3rd party API with advanced data features."

__Note:__ Requires [SpaceSERP API](https://appsumo.8odi.net/nLaMra) (lifetime deal on AppSumo)

## Project Overview

This SEO Rank Tracker is a web application that allows users to track search engine rankings for specified keywords across different projects. It utilizes multiple 3rd party APIs to fetch ranking and SERP data, such as [SpaceSERP](https://appsumo.8odi.net/nLaMra) (lifetime deal on AppSumo), and search volume information, providing advanced features for data analysis and visualization.

### Key Features

- Project-based keyword tracking
- SERP data fetching and storage
- Rank tracking over time
- Search volume tracking with 30-day update intervals (via Grepwords or [DataForSEO](https://dataforseo.com/?aff=167680))
- Advanced data filtering and visualization
- Keyword tagging system
- Historical data viewing and exporting
- User-friendly interface built with Vue.js

## Tech Stack

- Frontend: Vue.js 3 with Vite
- Backend: Python with FastAPI
- Database: SQLite
- API Integrations: 
  - [SpaceSERP](https://appsumo.8odi.net/nLaMra) for SERP data (lifetime deal on AppSumo)
  - Grepwords or [DataForSEO](https://dataforseo.com/?aff=167680) for search volume data

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/seo-rank-tracker.git
   cd seo-rank-tracker
   ```

2. Set up the backend:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```
   cd ../frontend/rankenberry-frontent
   npm install
   ```

4. Install additional JavaScript libraries:
   ```
   npm install axios pinia v-calendar plotly.js-dist-min
   ```

5. Create a `.env` file in the backend directory and add your API keys:
   ```
   SPACESERP_API_KEY=your_spaceserp_api_key_here
   GREPWORDS_API_KEY=your_grepwords_api_key_here
   DATAFORSEO_LOGIN=your_login_here
DATAFORSEO_PASSWORD=your_password_here
   ```

### Additional JavaScript Libraries

- **axios**: Promise-based HTTP client for making API requests.
- **pinia**: State management library for Vue.js applications.
- **v-calendar**: Calendar and date picker component for Vue.js.
- **plotly.js-dist-min**: JavaScript graphing library for creating interactive charts.

These libraries are essential for the functionality of the frontend application. They handle API communication, state management, date selection, and data visualization respectively.

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- Python (v3.8 or later)
- pip (Python package manager)

### Running the Application

1. Start the backend server:
   ```
   cd backend
   uvicorn app:app --reload
   ```

2. In a new terminal, start the frontend development server:
   ```
   cd frontend/rankenberry-frontent
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:5173` to use the application.

## Usage

1. Add a new project with a domain
2. Add keywords to track for each project
3. Fetch SERP data for your keywords
4. View and analyze ranking data over time
5. Use the tagging system to organize and filter keywords
6. View historical data for individual keywords
7. Export keyword history data as needed

## New Features

- Search volume tracking: The application now fetches and stores search volume data for keywords, updating every 30 days.
- Keyword tagging: Users can now add tags to keywords for better organization and filtering.
- Historical data viewing: A new modal allows users to view and export historical data for individual keywords.
- Improved data visualization: The rank table now includes more detailed metrics and allows for advanced filtering.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Thanks to [SpaceSERP](https://appsumo.8odi.net/nLaMra) for providing the SERP data API
- Thanks to Grepwords for providing the search volume data API
- Vue.js and FastAPI communities for their excellent documentation and tools

## TODO

For a list of planned features and improvements, please see our [TODO list](https://github.com/pshapiro/rankenberry/blob/main/TODO.md).

---

*Note: The SpaceSERP link is an affiliate link, which means I may receive commission if you sign up from those links.*
