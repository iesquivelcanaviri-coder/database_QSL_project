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

# GitHub Repository

## Public GitHub Repository URL

```text
https://github.com/iesquivelcanaviri-coder/database_QSL_project.git
```

This repository contains the Flask application source code, Jinja templates, static CSS and JavaScript assets, deployment files, and README documentation for the database web application assignment.

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


# Application Architecture

The application follows a full-stack Flask architecture:

```text
Browser / User Interface
        ↓
HTML + CSS + JavaScript
        ↓
Flask Routes and REST-style API Endpoints
        ↓
SQLAlchemy ORM Models
        ↓
Neon PostgreSQL Cloud Database
        ↓
Rendered HTML Templates / JSON Responses
```

The frontend uses Jinja templates for page rendering and JavaScript `fetch()` requests for dynamic database-backed actions such as adding and deleting portfolio holdings. The backend uses Flask routes to process requests, SQLAlchemy models to interact with PostgreSQL, and JSON responses to update the interface without requiring a full page reload.

---

# Validation and Error Handling

The application includes validation and defensive programming to make the database workflow more reliable.

Examples include:

* required form fields for portfolio and contact creation
* safe numeric conversion for portfolio values and weights
* prevention of duplicate holdings through a unique portfolio-and-ticker constraint
* backend validation before adding a holding to a portfolio
* portfolio mandate checks, such as maximum position weight and restricted equity exposure
* fallback market metrics if Yahoo Finance data is unavailable
* JSON error responses for failed API requests
* user-facing success and error messages through Flask flash messages and JavaScript feedback blocks

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

The following screenshots provide evidence that the application is deployed, database-backed, and functioning through the full Flask + PostgreSQL workflow.

## Application Page Screenshots

### Home Page

![Home Page](static/images/home.png)

The Home page introduces the project workflow and summarises the database features demonstrated in the application.

### Portfolio Profiles Page

![Portfolio Profiles](static/images/portfolio_profiles.png)

The Portfolio Profiles page demonstrates the Create and Read parts of CRUD for client portfolio records. It allows the user to create a portfolio profile and review saved portfolio mandate data.

### Market Dashboard Page

![Market Dashboard](static/images/market_dashboard.png)

The Market Dashboard provides a stock and ETF screening interface. It includes filtering, ranking, suggested allocation weights, and the ability to send selected holdings to the database through a Flask API route.

### Portfolio Performance Page

![Portfolio Performance](static/images/portfolio_performance.png)

The Portfolio Performance page reads saved holdings from PostgreSQL and displays portfolio-level performance summaries, allocation status, average scores, volatility, beta, and saved holdings.

### Contact Page

![Contact Page](static/images/contact.png)

The Contact page demonstrates form submission and database persistence using the ContactMessage SQLAlchemy model.

---

## PostgreSQL Database Evidence

### Portfolio Table

![Portfolio Database Table](static/images/porfolio_database.png)

This screenshot shows saved portfolio records in the PostgreSQL database. It evidences the Create and Read functionality for the Portfolio model.

### Portfolio Holding Table

![Portfolio Holding Database Table](static/images/portfolio_holding_database.png)

This screenshot shows saved holdings in the PostgreSQL database. It evidences database persistence for selected stocks and ETFs assigned to client portfolios.

### Contact Message Table

![Contact Message Database Table](static/images/contact_database.png)

This screenshot shows a saved contact message record in PostgreSQL. It demonstrates that contact form submissions are stored in the database.

---

## Deployment Evidence

### Render Deployment Dashboard

![Render Deployment](static/images/render_deploymnet.png)

This screenshot shows the Render web service deployed successfully and live. It provides evidence that the application is hosted and accessible through the public deployment URL.

---

## CRUD Workflow Evidence

The screenshots above collectively demonstrate the complete CRUD workflow:

| CRUD Operation | Evidence in Application | Evidence in Database |
| -------------- | ----------------------- | -------------------- |
| Create | Portfolio Profiles form, Contact form, Add Stock workflow | Portfolio, PortfolioHolding, and ContactMessage tables |
| Read | Portfolio Profiles page, Market Dashboard, Portfolio Performance page | Saved database rows visible in PostgreSQL tables |
| Update | Existing portfolios and repeated saved holdings can be updated | Existing records are reused rather than duplicated |
| Delete | Delete buttons for saved portfolio holdings | Records can be removed from the PortfolioHolding table |

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
