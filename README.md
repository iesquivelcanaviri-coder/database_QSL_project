# Portfolio Management Decision-Support Web Application with PostgreSQL

---

# Student Details

| Field               | Information                                          |
| ------------------- | ---------------------------------------------------- |
| Student Name        | Irene Esquivel Canaviri                              |
| Module              | Databases                                            |
| Assignment          | Building a Web Application with Flask and a Database |


---

# Project Title

## Portfolio Management Decision-Support Web Application with PostgreSQL Persistence

---

# Live Deployment

## Public Render Deployment URL

```text
https://database-qsl-project.onrender.com
```

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

The project demonstrates full-stack web-development concepts including:

* backend Flask development
* PostgreSQL database integration
* CRUD operations
* responsive frontend design
* JavaScript interactivity
* REST-style API routes
* cloud deployment using Render
* Neon PostgreSQL cloud database hosting

The application was designed to simulate a simplified institutional portfolio-management environment while demonstrating modern database and software-engineering best practices.

---

# Main Features

## Core Application Features

* Flask backend routing
* PostgreSQL database persistence
* SQLAlchemy ORM integration
* Full CRUD operations
* Portfolio profile management
* Portfolio holding management
* Market dashboard analytics
* Financial metric calculations
* REST-style API endpoints
* Contact message persistence
* Dynamic dashboard filtering
* Live portfolio updates
* Responsive dashboard layouts
* Cloud deployment using Render

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

The application uses a relational PostgreSQL database connected through Flask-SQLAlchemy ORM.

The schema demonstrates:

* relational database design
* primary keys
* foreign keys
* one-to-many relationships
* unique constraints
* timestamp tracking
* JSON profile storage
* cascade deletion

---

# Entity Relationship Diagram (ERD)

```mermaid
erDiagram

    Portfolio ||--o{ PortfolioHolding : contains
    Portfolio ||--o{ AnalysisRecord : stores

    Portfolio {
        int id PK
        string key
        string client_id
        string display_name
        string benchmark_ticker
        float portfolio_value
        float max_weight
        json profile_data
        datetime created_at
        datetime updated_at
    }

    PortfolioHolding {
        int id PK
        int portfolio_id FK
        string ticker
        string recommended_weight
        float weight_decimal
        string decision
        string tag
        string sector
        string industry
        float beta
        int score
        datetime created_at
        datetime updated_at
    }

    AnalysisRecord {
        int id PK
        int portfolio_id FK
        string ticker
        float beta
        int score
        string decision
        float expected_return_1y
        float volatility_1y
        float sharpe_like_1y
        json raw_result
        datetime created_at
        datetime updated_at
    }

    ContactMessage {
        int id PK
        string name
        string email
        text message
        datetime created_at
    }
```

---

# Database Models

## Portfolio Model

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

## PortfolioHolding Model

The `PortfolioHolding` model stores securities assigned to portfolios.

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

## AnalysisRecord Model

The `AnalysisRecord` model stores completed market-analysis outputs.

### Key Fields

* `ticker`
* `beta`
* `score`
* `decision`
* `expected_return_1y`
* `volatility_1y`
* `sharpe_like_1y`

---

## ContactMessage Model

The `ContactMessage` model stores contact-form submissions.

### Key Fields

* `name`
* `email`
* `message`
* `created_at`

---

# CRUD Operations

The project demonstrates complete database CRUD functionality.

| CRUD Operation | Example                                                 |
| -------------- | ------------------------------------------------------- |
| Create         | save portfolio profiles, holdings, and contact messages |
| Read           | retrieve portfolios, holdings, and dashboard data       |
| Update         | update existing holdings and portfolio records          |
| Delete         | remove saved holdings from portfolios                   |

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
| `POST /analyze`               | analyse a selected ticker       |
| `POST /add-to-portfolio`      | add or update portfolio holding |
| `GET /portfolio-stocks`       | retrieve portfolio holdings     |
| `DELETE /delete-holding/<id>` | delete holding                  |

---

# Frontend Design

## HTML and Jinja Templates

The project uses Jinja templating with reusable template inheritance.

Features include:

* reusable base template
* reusable navigation bar
* reusable dashboard layouts
* responsive page structure
* modular page components

---

## CSS Styling

Main stylesheet:

```text
static/css/style.css
```

The CSS implementation includes:

* responsive layouts
* dashboard cards
* accordions
* responsive tables
* form layouts
* responsive navigation
* mobile-friendly design
* hover states
* transitions
* financial dashboard styling

---

## JavaScript Functionality

Main JavaScript file:

```text
static/js/script.js
```

Features include:

* asynchronous fetch API requests
* live dashboard filtering
* sortable market tables
* accordion interactions
* dynamic portfolio updates
* CRUD operations without full page refresh
* delete handling
* interactive dashboard controls

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

# Automated Testing

The project includes automated route testing using Flask test clients.

Test file:

```text
test_app.py
```

Implemented tests include:

* home page route testing
* contact page route testing
* portfolio page route testing
* HTTP status-code validation

Example execution:

```bash
pytest
```

---

# Project Structure

```text
portfolio-database-project/
├── app.py
├── test_app.py
├── Procfile
├── requirements.txt
├── runtime.txt
├── README.md
├── .env.example
├── .gitignore
├── screenshots/
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│       ├── home.png
│       ├── portfolio_profiles.png
│       ├── market_dashboard.png
│       ├── portfolio_performance.png
│       └── contact.png
├── templates/
│   ├── base.html
│   ├── _navbar.html
│   ├── index.html
│   ├── contact.html
│   ├── market_dashboard.html
│   ├── portfolio_profiles.html
│   ├── portfolio_performance.html
│   └── 404.html
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

* Render web hosting
* Neon PostgreSQL cloud database
* Gunicorn production WSGI server

---

## Render Build Command

```bash
pip install -r requirements.txt
```

---

## Render Start Command

```bash
gunicorn app:app
```

---

## Required Environment Variables

```text
SECRET_KEY=<secure-secret-key>
DATABASE_URL=<neon-postgresql-connection-string>
```

The real environment variables are intentionally excluded from GitHub for security purposes.

---

# Testing Checklist

The following functionality was tested successfully:

* home page loads correctly
* portfolio profiles load from PostgreSQL
* new portfolios can be created
* holdings can be added to portfolios
* holdings persist after refresh
* holdings can be updated
* holdings can be deleted
* dashboard filtering works
* dashboard sorting works
* ticker analysis works
* contact form saves correctly
* deployed Render application functions correctly

---

# Best Practices Applied

The project demonstrates multiple software-engineering best practices including:

* relational database design
* SQLAlchemy ORM usage
* reusable helper functions
* REST-style API design
* responsive frontend design
* reusable Jinja templates
* environment-variable configuration
* deployment-ready architecture
* database normalization concepts
* CRUD separation
* clean code organization
* inline comments and docstrings

---

# Security and Configuration

The application uses environment variables to protect sensitive configuration data.

The `.env` file is excluded from GitHub using `.gitignore`.

Sensitive information such as database credentials and secret keys are not hardcoded into the application.

---

# Screenshots

## Recommended Screenshots for Submission

Include screenshots of:

* Home page
![Home Page](static/images/home.png)
* Portfolio Profiles page
![Portfolio Profiles](static/images/portfolio_profiles.png)
* Market Dashboard
![Market Dashboard](static/images/market_dashboard.png)
* Portfolio Performance page
![Portfolio Performance](static/images/portfolio_performance.png)
* Contact page
![Contact Page](static/images/contact.png)
* PostgreSQL database tables
* Render deployment dashboard
* CRUD workflow example

---

# Deployment Notes for Marker

## Live Deployment URL

```text
https://database-qsl-project.onrender.com
```

---

## Render Build Command

```bash
pip install -r requirements.txt
```

---

## Render Start Command

```bash
gunicorn app:app
```

---

## Required Render Environment Variables

```text
SECRET_KEY=<secure-secret-key>
DATABASE_URL=<Neon PostgreSQL connection string>
```

The real `.env` file is intentionally not submitted because it contains private credentials.

---

# Academic Note

This application was developed for educational and academic purposes.

The portfolio analysis calculations and investment outputs are simplified educational models and should not be interpreted as professional financial advice.
