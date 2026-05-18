# Portfolio Management Decision-Support Web Application with PostgreSQL

## Student Details

**Student:** Irene Esquivel Canaviri

---

# Project Title

**Portfolio Management Decision-Support Web Application with PostgreSQL Persistence**

---

# Project Overview

This project is a Flask web application connected to a PostgreSQL database using Flask-SQLAlchemy.

The application extends a previous portfolio-management project by replacing temporary in-memory storage with a fully integrated relational database. The system allows users to review portfolio profiles, analyse securities, manage portfolio holdings, monitor market dashboard results, and store contact form submissions.

The application demonstrates:

- Flask backend development
- PostgreSQL database integration
- SQLAlchemy ORM usage
- CRUD operations
- HTML templating with Jinja
- CSS styling and JavaScript interactivity
- REST-style API routes
- Deployment readiness using Render

The project was designed to simulate a simplified portfolio manager decision-support workflow while demonstrating modern web development and database concepts.

---

# Main Features

- Flask routing and Jinja templating
- PostgreSQL database persistence
- SQLAlchemy ORM models
- Create, Read, Update, and Delete (CRUD) operations
- Responsive HTML, CSS, and JavaScript
- Portfolio analysis workflows
- Market dashboard screening functionality
- Portfolio holding management
- Contact form database storage
- Render deployment configuration

---

# Main Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- PostgreSQL
- HTML5
- CSS3
- JavaScript
- NumPy
- yfinance
- Gunicorn
- Render

---

# Database Schema

## Portfolio

The `Portfolio` model represents a client portfolio mandate.

### Important Fields

- `id` — primary key
- `key` — unique portfolio key
- `client_id`
- `display_name`
- `benchmark_ticker`
- `portfolio_value`
- `max_weight`
- `profile_data` (JSON)

### Relationships

- one portfolio has many holdings
- one portfolio has many analysis records

---

## PortfolioHolding

The `PortfolioHolding` model stores securities saved into a portfolio.

### Important Fields

- `id` — primary key
- `portfolio_id` — foreign key
- `ticker`
- `recommended_weight`
- `weight_decimal`
- `decision`
- `tag`
- `sector`
- `industry`
- `beta`

### Constraint

A unique constraint exists on:

- `portfolio_id`
- `ticker`

This ensures the same ticker is updated rather than duplicated within the same portfolio.

---

## AnalysisRecord

The `AnalysisRecord` model stores completed ticker analysis results.

### Important Fields

- `id` — primary key
- `portfolio_id` — foreign key
- `ticker`
- `beta`
- `score`
- `decision`
- `expected_return_1y`
- `volatility_1y`
- `sharpe_like_1y`
- `raw_result` (JSON)

---

## ContactMessage

The `ContactMessage` model stores contact form submissions.

### Important Fields

- `id` — primary key
- `name`
- `email`
- `message`
- `created_at`

---

# Main Routes

## HTML Routes

- `/` — Home page
- `/portfolio_profiles` — Portfolio profile review page
- `/market_dashboard` — Market screening dashboard
- `/criteria` — Security analysis and portfolio workflow page
- `/contact` — Contact form page

---

## JSON / API Routes

- `POST /analyze` — analyses a ticker and stores an analysis record
- `POST /add-to-portfolio` — creates or updates a portfolio holding
- `GET /portfolio-stocks` — retrieves saved portfolio holdings
- `DELETE /delete-holding/<holding_id>` — deletes a saved holding

---

# CRUD Operations

The project demonstrates all major CRUD database operations.

| Operation | Example |
|---|---|
| Create | Save portfolio holdings and contact messages |
| Read | Retrieve holdings and portfolio data |
| Update | Update existing holdings |
| Delete | Remove saved holdings |

---

# Project Structure

```text
portfolio-database-project/
├── app.py
├── config.py
├── models.py
├── Procfile
├── requirements.txt
├── runtime.txt
├── README.md
├── .env.example
├── .gitignore
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── templates/
│   ├── base.html
│   ├── _navbar.html
│   ├── index.html
│   ├── contact.html
│   ├── criteria.html
│   ├── market_dashboard.html
│   └── portfolio_profiles.html
└── instance/
```

The project structure separates backend logic, templates, static files, and deployment configuration files to keep the application organised and maintainable.

---

# Flask Implementation

The Flask application handles:

- route management
- template rendering
- API endpoints
- database integration
- financial analysis logic
- CRUD workflows

The application uses:

- `render_template()` for HTML rendering
- `jsonify()` for API responses
- SQLAlchemy ORM models for database operations
- Jinja templating for reusable frontend components

---

# Frontend Design

## HTML

The application includes multiple HTML pages built using Jinja templating.

The templates inherit from a shared `base.html` layout and include reusable navigation components.

---

## CSS

The project uses a dedicated stylesheet located inside:

```text
static/css/style.css
```

The styling includes:

- responsive layouts
- cards and grid sections
- dashboard tables
- accordions
- forms
- buttons
- portfolio summaries
- responsive design

---

## JavaScript

JavaScript functionality is located inside:

```text
static/js/script.js
```

JavaScript is used for:

- asynchronous API requests using `fetch()`
- dynamic updates without page reloads
- market dashboard filtering
- sorting functionality
- accordion behaviour
- portfolio update workflows

---

# PostgreSQL Integration

The application integrates PostgreSQL using Flask-SQLAlchemy.

The database connection is configured using environment variables.

Example:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

The application supports both:

- local development
- cloud deployment on Render

---

# Local Setup

## 1. Create and activate a virtual environment

### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Create environment variables

Create a `.env` file based on `.env.example`:

```bash
SECRET_KEY=replace-this-with-a-secure-secret-key
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

The `.env` file should never be committed to GitHub.

---

## 4. Run the application

```bash
pip install flask flask_sqlalchemy psycopg2-binary yfinance numpy

python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

# Render Deployment Steps

## 1. Push the project to GitHub

Ensure the `.env` file is ignored using `.gitignore`.

---

## 2. Create a PostgreSQL database

Create a PostgreSQL database on Render or another PostgreSQL provider.

---

## 3. Create a Render Web Service

Connect the GitHub repository to Render and configure the service as a Python web application.

---

## 4. Add environment variables

Add the following environment variables inside the Render dashboard:

```text
SECRET_KEY=<your secret key>
DATABASE_URL=<your PostgreSQL database URL>
```

---

## 5. Configure build and start commands

### Build command

```bash
pip install -r requirements.txt
```

### Start command

```bash
gunicorn app:app
```

---

## 6. Deploy the application

Render will install dependencies, build the application, and provide a public deployment URL.

---

# Testing Checklist

Before submission, test the following:

- home page loads correctly
- portfolio profiles load from the database
- market dashboard loads correctly
- dashboard filters and sorting work
- ticker analysis works correctly
- holdings can be added to portfolios
- holdings remain after page refresh
- holdings can be updated
- holdings can be deleted
- contact messages save correctly
- deployed Render application functions correctly

---

# Best Practices Applied

The project demonstrates several software engineering best practices:

- separation of backend and frontend logic
- reusable helper functions
- SQLAlchemy ORM usage
- environment variable configuration
- modular project structure
- responsive frontend design
- reusable Jinja templates
- database normalization concepts
- REST-style API routes
- deployment-ready configuration

---

# Notes

This application was developed for academic demonstration purposes.

The portfolio scoring and forecast outputs are simplified educational calculations and should not be interpreted as professional financial advice.