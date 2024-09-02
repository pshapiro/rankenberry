# Rankenberry: SEO Rank Tracker

A simple rank tracking application leveraging a 3rd party API with advanced data features.

## Project Overview

This SEO Rank Tracker is a web application that allows users to track search engine rankings for specified keywords across different projects. It utilizes a 3rd party API to fetch SERP (Search Engine Results Page) data and provides advanced features for data analysis and visualization.

### Key Features

- Project-based keyword tracking
- SERP data fetching and storage
- Rank tracking over time
- Advanced data filtering and visualization
- User-friendly interface built with Vue.js

## Tech Stack

- Frontend: Vue.js 3 with Vite
- Backend: Python with FastAPI
- Database: SQLite
- API Integration: 3rd party SERP API (spaceserp)

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- Python (v3.8 or later)
- pip (Python package manager)

### Installation

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

4. Create a `.env` file in the backend directory and add your API key:
   ```
   API_KEY=your_api_key_here
   ```

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Thanks to SpaceSERP for providing the SERP data API
- Vue.js and FastAPI communities for their excellent documentation and tools

## TODO

For a list of planned features and improvements, please see our [TODO list](https://github.com/pshapiro/rankenberry/blob/main/TODO.md).