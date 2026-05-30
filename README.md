# Portfolio Management Decision-Support Web Application with PostgreSQL

## Student Details

**Student Name:** Irene Esquivel Canaviri

---

# Project Title

## Portfolio Management Decision-Support Web Application with PostgreSQL Persistence

---


# Live Deployment

## Public Render Deployment URL

https://database-qsl-project.onrender.com

The application is fully deployed using Render and connected to a Neon PostgreSQL cloud database.

---

# Project Overview

This project is a Flask-based portfolio management and investment decision-support web application connected to a PostgreSQL cloud database using Flask-SQLAlchemy ORM.

The application simulates a professional portfolio management workflow where portfolio managers can:

* create portfolio profiles
* review client investment mandates
* analyse securities and ETFs
* monitor market dashboard metrics
* manage portfolio holdings
* save and update portfolio allocations
* store client contact messages
* persist all records inside a PostgreSQL database

The project demonstrates full-stack web development concepts including backend Flask development, PostgreSQL database integration, CRUD operations, frontend JavaScript interactivity, responsive CSS design, and cloud deployment.

The application was designed to simulate a simplified institutional portfolio-management environment while demonstrating modern database and web-development best practices.

---

# Main Features

* Flask backend routing
* PostgreSQL database persistence
* SQLAlchemy ORM integration
* Full CRUD operations
* Responsive HTML5/CSS3 frontend
* JavaScript dashboard interactivity
* Portfolio profile creation
* Portfolio holding management
* Market dashboard analytics
* Financial metric calculations
* REST-style API endpoints
* Render cloud deployment
* Neon PostgreSQL cloud database integration

---

# Main Technologies Used

| Technology       | Purpose                           |
| ---------------- | --------------------------------- |
| Python           | Backend programming               |
| Flask            | Web application framework         |
| Flask-SQLAlchemy | ORM and database integration      |
| PostgreSQL       | Relational database               |
| Neon PostgreSQL  | Cloud database hosting            |
| HTML5            | Frontend structure                |
| CSS3             | Responsive styling                |
| JavaScript       | Interactivity and dynamic updates |
| NumPy            | Financial calculations            |
| yfinance         | Market data retrieval             |
| Gunicorn         | Production WSGI server            |
| Render           | Cloud deployment platform         |

---

# Database Schema

## Portfolio

The `Portfolio` model stores client portfolio mandates and investment profiles.

### Key Fields

* `id`
* `key`
* `client_id`
* `display_name`
* `benchmark_ticker`
* `portfolio_value`
* `max_weight`
* `profile_data`

### Relationships

* one portfolio can contain many holdings
* one portfolio can contain many analysis records

---

## PortfolioHolding

The `PortfolioHolding` model stores securities saved inside portfolios.

### Key Fields

* `portfolio_id`
* `ticker`
* `recommended_weight`
* `weight_decimal`
* `decision`
* `tag`
* `sector`
* `industry`
* `beta`
* `score`

### Database Constraint

A unique database constraint prevents duplicate securities from being inserted into the same portfolio.

This ensures holdings are updated instead of duplicated.

---

## AnalysisRecord

The `AnalysisRecord` model stores completed analysis outputs.

### Key Fields

* `ticker`
* `beta`
* `score`
* `decision`
* `expected_return_1y`
* `volatility_1y`
* `sharpe_like_1y`

---

## ContactMessage

The `ContactMessage` model stores contact form submissions.

### Key Fields

* `name`
* `email`
* `message`
* `created_at`

---

# CRUD Operations

The project demonstrates complete database CRUD functionality.

| CRUD Operation | Example                            |
| -------------- | ---------------------------------- |
| Create         | Save holdings and contact messages |
| Read           | Retrieve portfolios and holdings   |
| Update         | Update existing portfolio holdings |
| Delete         | Remove saved holdings              |

---

# Main Application Pages

| Route                    | Description                         |
| ------------------------ | ----------------------------------- |
| `/`                      | Home page                           |
| `/portfolio_profiles`    | Portfolio profile management        |
| `/market_dashboard`      | Market screening dashboard          |
| `/portfolio_performance` | Portfolio analytics and performance |
| `/contact`               | Contact form page                   |

---

# API Routes

| Route                         | Function                        |
| ----------------------------- | ------------------------------- |
| `POST /analyze`               | Analyse a selected ticker       |
| `POST /add-to-portfolio`      | Add or update portfolio holding |
| `GET /portfolio-stocks`       | Retrieve portfolio holdings     |
| `DELETE /delete-holding/<id>` | Delete holding                  |

---

# Frontend Design

## HTML

The project uses Jinja templating with reusable templates and inheritance.

The application includes:

* base template inheritance
* reusable navigation bar
* reusable dashboard layouts
* responsive page structure

---

## CSS

The application uses a dedicated stylesheet:

```text
static/css/style.css
```

The CSS includes:

* responsive layouts
* portfolio dashboard cards
* accordions
* data tables
* forms
* responsive navigation
* mobile-friendly design

---

## JavaScript

JavaScript functionality is implemented inside:

```text
static/js/script.js
```

Features include:

* asynchronous fetch API requests
* live dashboard filtering
* table sorting
* accordion interactions
* dynamic portfolio updates
* CRUD interaction without page refresh

---

# PostgreSQL Integration

The application integrates PostgreSQL using Flask-SQLAlchemy ORM.

The database connection is configured through environment variables.

Example:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

The application supports:

* local development
* Render deployment
* Neon PostgreSQL cloud hosting

---

# Project Structure

```text
portfolio-database-project/
├── app.py
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
│   ├── market_dashboard.html
│   ├── portfolio_profiles.html
│   └── portfolio_performance.html
└── instance/
```

---

# Local Installation

## 1. Create Virtual Environment

### macOS/Linux

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file:

```bash
SECRET_KEY=replace-with-secure-key
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

---

## 4. Run the Application

```bash
python app.py
```

---

# Render Deployment

## Deployment Platform

The project is deployed using:

* Render (web hosting)
* Neon PostgreSQL (cloud database)

---

## Render Configuration

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

---

## Environment Variables

The following environment variables were configured inside Render:

```text
SECRET_KEY=<secret_key>
DATABASE_URL=<neon_postgresql_connection_string>
```

---

# Testing Checklist

The following functionality was tested successfully:

* home page loads correctly
* portfolio profiles load from PostgreSQL
* new portfolios can be created
* holdings can be added to portfolios
* holdings remain after refresh
* holdings can be updated
* holdings can be deleted
* dashboard filtering works
* dashboard sorting works
* ticker analysis works
* contact form saves correctly
* deployed Render application functions correctly

---


# Best Practices Applied

The project demonstrates multiple software engineering best practices including:

* relational database design
* SQLAlchemy ORM usage
* reusable helper functions
* REST-style API design
* responsive frontend design
* reusable Jinja templates
* environment variable configuration
* deployment-ready architecture
* database normalization concepts
* CRUD separation
* clean code organization
* inline comments and docstrings

---

# Security and Configuration

The project uses environment variables to protect sensitive configuration data.

The `.env` file is excluded from GitHub using `.gitignore`.

Sensitive information such as database credentials and secret keys are not hardcoded into the application.

---

# Screenshots

## Recommended Screenshots for Submission

Include screenshots of:

* Home page
* Portfolio Profiles page
* Market Dashboard
* Portfolio Performance page
* Contact page
* PostgreSQL database tables
* Render deployment dashboard

---

# Academic Note

This application was developed for educational and academic purposes.

The portfolio analysis calculations and investment outputs are simplified educational models and should not be interpreted as professional financial advice.

---

# Distinction-Level Evidence Map

This section explains how the project meets the assignment rubric.

## Database Schema and CRUD Logic

The application defines four SQLAlchemy ORM models:

* `Portfolio`
* `PortfolioHolding`
* `AnalysisRecord`
* `ContactMessage`

The schema demonstrates relational database design through:

* primary keys
* foreign keys
* one-to-many relationships
* cascade deletion
* JSON profile storage
* unique database constraints
* timestamp fields for created and updated records

CRUD evidence:

| CRUD Area | Evidence |
| --------- | -------- |
| Create | new portfolio profiles, new holdings, analysis records, contact messages |
| Read | saved profiles, dashboard rows, holdings, contact messages |
| Update | edit saved portfolio profiles and update existing holdings |
| Delete | delete holdings and delete portfolio profiles with linked records |

## Flask and PostgreSQL Integration

The project uses Flask-SQLAlchemy to connect Flask to PostgreSQL through the `DATABASE_URL` environment variable.

The app is deployment-ready because it:

* supports Neon PostgreSQL
* supports Render environment variables
* uses Gunicorn in production
* keeps database credentials outside source code
* provides a local development fallback database

## Frontend Design and JavaScript

The frontend includes:

* reusable Jinja base template
* reusable navbar
* responsive card layout
* form grids
* dashboard filters
* sortable market tables
* accordion sections
* JavaScript fetch API requests
* dynamic portfolio holdings rendering
* delete actions without full page rebuild

## Deployment Evidence

Live deployed application:

https://database-qsl-project.onrender.com

Deployment stack:

* GitHub repository
* Render web service
* Neon PostgreSQL cloud database
* Gunicorn production server

## Testing Evidence

Before submission, test these flows on both local Flask and Render:

* create a new portfolio profile
* edit an existing portfolio profile
* assign a stock or ETF to a profile
* update an existing holding by saving the same ticker again
* delete a holding
* delete a test portfolio profile
* submit a contact form message
* refresh the browser and confirm records persist
* confirm the Render URL shows the newest GitHub version

---

# Deployment Notes for Marker

## Render Build Command

```bash
pip install -r requirements.txt
```

## Render Start Command

```bash
gunicorn app:app
```

## Required Render Environment Variables

```text
SECRET_KEY=<secure secret key>
DATABASE_URL=<Neon PostgreSQL connection string>
```

The real `.env` file is intentionally not submitted because it contains private credentials.

---

# Database Migration Note

If the hosted PostgreSQL database was created before the final timestamp update, run:

```text
database_migration_distinction_update.sql
```

inside the Neon SQL Editor before redeploying the final version.
