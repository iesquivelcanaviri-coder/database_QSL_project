# ============================================================
# Portfolio Management Decision-Support Web Application
# Flask + PostgreSQL + SQLAlchemy ORM
# ============================================================

# ============================================================
# IMPORTS
# ============================================================
# ------------------------------------------------------------
# Standard Library Imports
# ------------------------------------------------------------
import os                      # Used for environment variables and operating system access
import re                      # Used for regular expression matching and text cleaning
import time                    # Used for dashboard caching timers
from datetime import datetime  # Used for timestamps and database dates

# ------------------------------------------------------------
# Third-Party Library Imports
# ------------------------------------------------------------
import numpy as np             # Used for financial calculations and volatility metrics
import yfinance as yf          # Used to download live Yahoo Finance market data

# Flask imports
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for 

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================
# ------------------------------------------------------------
# FLASK APPLICATION CONFIGURATION
# ------------------------------------------------------------
app = Flask(__name__)  # creating the main Flask app so everything can run from here

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-before-deployment"
)  # loading the secret key from environment variables (or using a default one if missing)

# ------------------------------------------------------------
# POSTGRESQL DATABASE CONFIGURATION
# ------------------------------------------------------------
database_url = os.environ.get(
    "DATABASE_URL", "sqlite:///portfolio_database.db"
)  # getting the database URL from Render/Neon, fallback to local SQLite for development

if database_url.startswith("postgres://"):  # checking for old Heroku-style URLs
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )  # fixing the prefix so SQLAlchemy doesn't complain

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url  # telling Flask where the database actually lives
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
    False  # turning this off to avoid unnecessary overhead + warnings
)

db = SQLAlchemy(app)  # creating the SQLAlchemy database object so we can define models

# ============================================================
# SQLALCHEMY DATABASE MODELS
# ============================================================
# ------------------------------------------------------------
# SQL TABLE: PORTFOLIO
# ------------------------------------------------------------
class Portfolio(db.Model):  # defining the Portfolio table as a Python class using SQLAlchemy
    """Stores one client portfolio mandate."""  # quick description so future me remembers what this model is for

    id = db.Column(db.Integer, primary_key=True)  # unique ID for each portfolio (auto-increment)
    key = db.Column(db.String(80), unique=True, nullable=False)  # short unique key to identify the portfolio
    client_id = db.Column(db.String(150), nullable=False)  # ID of the client this portfolio belongs to
    display_name = db.Column(db.String(200), nullable=False)  # friendly name shown in the UI
    benchmark_ticker = db.Column(db.String(20), nullable=False)  # benchmark index the portfolio compares against
    portfolio_value = db.Column(db.Float, nullable=False, default=0.0)  # total value of the portfolio (default 0)
    max_weight = db.Column(db.Float, nullable=False, default=10.0)  # max % weight allowed per stock
    profile_data = db.Column(db.JSON, nullable=False)  # storing the portfolio mandate as JSON (risk, objectives, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # timestamp for when the portfolio profile was created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # timestamp for when the portfolio profile was last edited

    holdings = db.relationship(
        "PortfolioHolding",  # linking to the PortfolioHolding table
        backref="portfolio",  # lets each holding know which portfolio it belongs to
        cascade="all, delete-orphan",  # delete holdings automatically if the portfolio is deleted
        lazy=True,  # loads holdings only when needed (saves performance)
    )

    analysis_records = db.relationship(
        "AnalysisRecord",  # linking to the AnalysisRecord table
        backref="portfolio",  # each analysis record knows its parent portfolio
        cascade="all, delete-orphan",  # delete analysis results if the portfolio is removed
        lazy=True,  # load analysis records only when accessed
    )


# ------------------------------------------------------------
# SQL TABLE: PORTFOLIO HOLDINGS
# ------------------------------------------------------------
class PortfolioHolding(db.Model):  # model representing each stock saved inside a portfolio
    """Stores a ticker saved into a portfolio."""  # quick description so it's clear what this table is for

    id = db.Column(db.Integer, primary_key=True)  # unique ID for each holding entry
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)  # links this holding to its parent portfolio
    ticker = db.Column(db.String(20), nullable=False)  # stock ticker symbol (e.g., AAPL)
    recommended_weight = db.Column(db.String(40), nullable=False)  # recommended % weight shown to the user (string version)
    weight_decimal = db.Column(db.Float, nullable=False, default=0.0)  # numeric version of the weight for calculations
    decision = db.Column(db.String(120), nullable=False)  # buy/hold/sell recommendation from the analysis
    tag = db.Column(db.String(80), nullable=True)  # optional tag to categorize the stock (e.g., "High Risk")
    sector = db.Column(db.String(120), nullable=True)  # sector of the company (e.g., Technology)
    industry = db.Column(db.String(160), nullable=True)  # more specific industry classification
    beta = db.Column(db.Float, nullable=True)  # beta value for volatility comparison vs benchmark
    score = db.Column(db.Integer, nullable=True)  # internal score from my analysis algorithm
    expected_return_1y = db.Column(db.Float, nullable=True)  # predicted 1-year return from the model
    volatility_1y = db.Column(db.Float, nullable=True)  # predicted 1-year volatility
    sharpe_like_1y = db.Column(db.Float, nullable=True)  # simplified Sharpe-like ratio for risk-adjusted performance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # timestamp for when this holding was added
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # timestamp for when this holding was last updated

    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="unique_portfolio_ticker"),  # prevents adding the same ticker twice to the same portfolio
    )

    def to_dict(self):  # helper method to convert this holding into a dictionary for JSON responses
        """Return one holding as a JSON-friendly dictionary."""  # makes API responses cleaner and easier to use
        return {
            "id": self.id,  # include holding ID
            "portfolio_id": self.portfolio_id,  # include portfolio ID
            "portfolio_name": self.portfolio.display_name,  # include portfolio name (nice for UI)
            "ticker": self.ticker,  # stock ticker
            "recommended_weight": self.recommended_weight,  # recommended weight (string)
            "weight_decimal": self.weight_decimal,  # numeric weight
            "decision": self.decision,  # buy/hold/sell decision
            "tag": self.tag,  # optional tag
            "sector": self.sector,  # sector info
            "industry": self.industry,  # industry info
            "beta": self.beta,  # beta value
            "score": self.score,  # analysis score
            "expected_return_1y": self.expected_return_1y,  # expected return
            "volatility_1y": self.volatility_1y,  # volatility
            "sharpe_like_1y": self.sharpe_like_1y,  # risk-adjusted return metric
        }

# ------------------------------------------------------------
# SQL TABLE: ANALYSIS RECORDS
# ------------------------------------------------------------
class AnalysisRecord(db.Model):  # model that stores each completed analysis result for a stock
    """Stores completed ticker analysis results."""  # quick description so I remember what this table is for

    id = db.Column(db.Integer, primary_key=True)  # unique ID for each analysis entry
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)  # links this analysis back to the portfolio it belongs to
    ticker = db.Column(db.String(20), nullable=False)  # the stock ticker that was analyzed (e.g., AAPL)
    beta = db.Column(db.Float, nullable=True)  # beta value calculated during the analysis (risk vs market)
    score = db.Column(db.Integer, nullable=True)  # internal score from my scoring system
    decision = db.Column(db.String(120), nullable=True)  # buy/hold/sell recommendation based on the analysis
    expected_return_1y = db.Column(db.Float, nullable=True)  # predicted 1-year return from the model
    volatility_1y = db.Column(db.Float, nullable=True)  # predicted 1-year volatility value
    sharpe_like_1y = db.Column(db.Float, nullable=True)  # simplified Sharpe-like ratio for risk-adjusted performance
    raw_result = db.Column(db.JSON, nullable=True)  # full raw analysis output stored as JSON (useful for debugging or UI)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # timestamp for when this analysis record was created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # timestamp for when this analysis record was last updated


# ------------------------------------------------------------
# SQL TABLE: CONTACT MESSAGES
# ------------------------------------------------------------
class ContactMessage(db.Model):  # model for storing messages sent through the contact form
    """Stores contact form submissions."""  # quick description so it's clear what this table is for

    id = db.Column(db.Integer, primary_key=True)  # unique ID for each message
    name = db.Column(db.String(120), nullable=False)  # name of the person who submitted the form
    email = db.Column(db.String(160), nullable=False)  # their email address so we know who contacted us
    message = db.Column(db.Text, nullable=False)  # the actual message text they typed in the form
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # timestamp for when the message was submitted
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # timestamp for when the message was last updated


# ============================================================
# DEFAULT CLIENT PORTFOLIO DATA
# ============================================================
#------------------------------------------------------------
# Default Portfolio Scenarios
#------------------------------------------------------------
PORTFOLIO_1 = {  # Dictionary defining the first client portfolio
    "client_id": "portfolio_1_conservative_retiree",  # Unique internal ID for this portfolio
    "identity": {  # Nested dictionary containing client identity details
        "name": "Marie-Claire Dubois",  # Client full name
        "date_of_birth": "1958-03-12",  # Client date of birth
        "nationality": "French",  # Client nationality
        "tax_residency": "France",  # Country where the client is tax resident
        "address": "Lyon, France",  # Client location/address summary
        "identification": "French passport",  # Main ID document used for KYC
    },  
    "compliance": {  # Nested dictionary for compliance and onboarding details
        "kyc": "Completed",  # Know Your Customer check status
        "aml": "No red flags",  # Anti-money laundering screening result
        "source_of_wealth": "Pension and inheritance",  # Where the client’s wealth came from
        "source_of_funds": "Retirement savings",  # Where the invested money specifically came from
        "fatca_crs": "CRS only",  # Tax reporting classification
        "pep": False,  # Politically exposed person flag; False means no
    },  
    "objectives": {  # Nested dictionary for investment goals
        "goals": "Capital preservation and stable income",  # Main investment objective
        "time_horizon_years": "5-7",  # Time horizon in years
        "expected_return_percent": "2-3",  # Expected return range in percentage terms
        "benchmark": "Eurozone government bond index",  # Benchmark used for comparison
    },  
    "risk_profile": {  # Nested dictionary describing client risk profile
        "risk_tolerance": "Conservative",  # Client willingness to accept risk
        "risk_capacity": "Low",  # Client ability to absorb losses
        "max_drawdown_percent": -8,  # Maximum acceptable portfolio decline
    },  
    "financials": {  # Nested dictionary for financial situation
        "net_worth": 850000,  # Total net worth
        "investments": 500000,  # Amount already invested or available for investment
        "real_estate": "Primary residence",  # Property situation
        "liabilities": 0,  # Total liabilities
        "income_monthly": 2200,  # Monthly income
        "expenses_monthly": 1800,  # Monthly expenses
        "liquidity_needs_monthly": 3000,  # Monthly cash need requirement
    },  
    "constraints": {  # Nested dictionary for mandate restrictions
        "legal": "UCITS-compliant",  # Legal restriction or framework
        "esg": "No tobacco",  # ESG restriction
        "max_equity_allocation_percent": 20,  # Maximum equity exposure allowed
        "currency": "EUR only",  # Allowed currency exposure
    },  
    "preferences": {  # Nested dictionary for client preferences
        "investment_style": "Income-focused",  # Preferred investment style
        "products": ["Bond funds", "Money-market funds"],  # Preferred product types
        "communication": "Monthly, simplified reports",  # Preferred reporting style
    },  
    "behavioural": {  # Nested dictionary for behavioural observations
        "past_reactions": "Panicked during 2020 market crash",  # Historical behaviour in stress periods
        "decision_style": "Hands-off",  # How involved the client likes to be
        "biases": ["Loss aversion"],  # Behavioural biases observed
    },  
    "mandate": {  # Nested dictionary for formal portfolio management rules
        "type": "Discretionary",  # Mandate type means manager can act on behalf of client
        "fees_percent": 0.8,  # Management fee percentage
        "rebalancing_frequency": "Quarterly",  # How often the portfolio should be rebalanced
        "ips": "Preserve capital, generate income, minimize volatility",  # Investment policy statement summary
    },  
    "portfolio_value": 500000,  # Total portfolio value used in sizing logic
    "max_weight": 20,  # Absolute maximum weight per position
    "volatility": 8.0,  # Example portfolio or benchmark volatility input
    "returns": [0.2, 0.1, 0.15, 0.05, 0.1],  # Example returns list used as embedded scenario data
    "ticker": "IEF",  # Default benchmark/reference ticker for this portfolio
}  

PORTFOLIO_2 = {
    "client_id": "portfolio_2_busy_executive",
    "identity": {
        "name": "James O'Connor",
        "date_of_birth": "1981-07-04",
        "nationality": "Irish",
        "tax_residency": "Ireland",
        "address": "Dublin, Ireland",
        "identification": "Irish passport",
    },
    "compliance": {
        "kyc": "Completed",
        "aml": "No issues",
        "source_of_wealth": "Salary and bonuses",
        "source_of_funds": "Corporate employment",
        "fatca_crs": "CRS only",
        "pep": False,
    },
    "objectives": {
        "goals": "Long-term growth",
        "time_horizon_years": "15+",
        "expected_return_percent": "6-8",
        "benchmark": "MSCI World",
    },
    "risk_profile": {
        "risk_tolerance": "Growth",
        "risk_capacity": "High",
        "max_drawdown_percent": -20,
    },
    "financials": {
        "net_worth": 1400000,
        "investments": 600000,
        "real_estate": "Home and rental property",
        "liabilities": 200000,
        "income_yearly": 180000,
        "expenses_yearly": 70000,
        "liquidity_needs": "Low",
    },
    "constraints": {
        "legal": "UCITS",
        "esg": "Required",
        "max_stock_weight_percent": 10,
        "currency": "EUR base, FX allowed",
    },
    "preferences": {
        "investment_style": "Passive",
        "products": ["ETFs only"],
        "communication": "Quarterly",
    },
    "behavioural": {
        "past_reactions": "Stayed invested during downturns",
        "decision_style": "Hands-off",
        "biases": ["Home bias toward Irish equities"],
    },
    "mandate": {
        "type": "Discretionary",
        "fees_percent": 0.6,
        "rebalancing_frequency": "Semi-annual",
        "ips": "Global equity exposure with ESG screening",
    },
    "portfolio_value": 600000,
    "max_weight": 10,
    "volatility": 22.0,
    "returns": [0.6, -0.3, 0.8, 0.4, 0.5],
    "ticker": "ACWI",
}

PORTFOLIO_3 = {
    "client_id": "portfolio_3_corporate_treasury",
    "identity": {
        "company_name": "Helvetic Precision Tools SA",
        "incorporation_year": 2012,
        "residency": "Geneva, Switzerland",
        "ownership": "Family-owned",
        "signatories": ["CFO", "CEO"],
    },
    "compliance": {
        "kyc": "Completed",
        "aml": "Clean",
        "source_of_wealth": "Operating profits",
        "source_of_funds": "Corporate cash reserves",
        "fatca_crs": "Corporate CRS",
        "pep": False,
    },
    "objectives": {
        "goals": "Preserve capital and earn yield",
        "time_horizon_years": "1-3",
        "expected_return_percent": "1-2",
        "benchmark": "CHF money-market index",
    },
    "risk_profile": {
        "risk_tolerance": "Very low",
        "risk_capacity": "Medium",
        "max_drawdown_percent": -3,
    },
    "financials": {
        "assets_cash": 5000000,
        "liabilities": 0,
        "income": "Business revenue",
        "expenses": "Operational",
        "liquidity_needs": 1000000,
    },
    "constraints": {
        "legal": "Corporate policy prohibits equities",
        "esg": "Neutral",
        "max_issuer_weight_percent": 5,
        "currency": "CHF only",
    },
    "preferences": {
        "investment_style": "Capital protection",
        "products": ["Money-market funds", "Short-duration bonds"],
        "communication": "Monthly, detailed",
    },
    "behavioural": {
        "past_reactions": "CFO is extremely risk-averse",
        "decision_style": "Very involved",
        "biases": ["Cash bias"],
    },
    "mandate": {
        "type": "Advisory",
        "fees_percent": 0.4,
        "rebalancing_frequency": "Monthly liquidity checks",
        "ips": "No equities, short-duration fixed income only",
    },
    "portfolio_value": 5000000,
    "max_weight": 5,
    "volatility": 3.0,
    "returns": [0.05, 0.03, 0.04, 0.02, 0.03],
    "ticker": "SHY",
}

PORTFOLIO_4 = {
    "client_id": "portfolio_4_international_entrepreneur",
    "identity": {
        "name": "Alejandro Torres",
        "date_of_birth": "1986-11-22",
        "nationality": "Spanish",
        "residency": "Dubai",
        "identification": "Spanish passport",
    },
    "compliance": {
        "kyc": "Completed",
        "aml": "No issues",
        "source_of_wealth": "Tech company founder",
        "source_of_funds": "Business sale and dividends",
        "fatca_crs": "CRS",
        "pep": False,
    },
    "objectives": {
        "goals": "Growth and diversification",
        "time_horizon_years": "10+",
        "expected_return_percent": "8-12",
        "benchmark": "MSCI ACWI",
    },
    "risk_profile": {
        "risk_tolerance": "Aggressive",
        "risk_capacity": "Very high",
        "max_drawdown_percent": -30,
    },
    "financials": {
        "net_worth": 12000000,
        "investments": 4000000,
        "real_estate": "Three properties",
        "liabilities": 0,
        "income": "Irregular business income",
        "expenses_yearly": 200000,
        "liquidity_needs": "Medium",
    },
    "constraints": {
        "legal": "None",
        "esg": "Prefers clean energy",
        "concentration": "Avoids competitor industries",
        "currency": ["USD", "EUR", "CHF"],
    },
    "preferences": {
        "investment_style": "Thematic and opportunistic",
        "products": ["Direct equities", "Thematic ETFs"],
        "communication": "Weekly",
    },
    "behavioural": {
        "past_reactions": "Buys aggressively during market dips",
        "decision_style": "Collaborative",
        "biases": ["Overconfidence"],
    },
    "mandate": {
        "type": "Advisory",
        "fees_percent": 1.0,
        "rebalancing_frequency": "Opportunistic",
        "ips": "High-growth, multi-currency, thematic focus",
    },
    "portfolio_value": 4000000,
    "max_weight": 15,
    "volatility": 35.0,
    "returns": [1.2, -0.8, 2.0, -0.5, 1.5],
    "ticker": "QQQ",
}

PORTFOLIO_5 = {
    "client_id": "portfolio_5_family_office",
    "identity": {
        "name": "The Beaumont Family Office",
        "incorporation_year": 1998,
        "residency": "London, UK",
        "ownership": "Multi-generational family",
        "signatories": ["CIO", "Family council"],
    },
    "compliance": {
        "kyc": "Completed",
        "aml": "Clean",
        "source_of_wealth": "Real estate and private equity",
        "source_of_funds": "Family assets",
        "fatca_crs": "CRS",
        "pep": "One family member (low-risk)",
    },
    "objectives": {
        "goals": "Preserve wealth and achieve moderate growth",
        "time_horizon_years": "30+",
        "expected_return_percent": "5-7",
        "benchmark": "40/60 global portfolio",
    },
    "risk_profile": {
        "risk_tolerance": "Balanced",
        "risk_capacity": "Very high",
        "max_drawdown_percent": -15,
    },
    "financials": {
        "net_worth": 50000000,
        "investments": 30000000,
        "real_estate": 20000000,
        "liabilities": 0,
        "income": "Rental income and dividends",
        "expenses_yearly": 1000000,
        "liquidity_needs_yearly": 500000,
    },
    "constraints": {
        "legal": "Must include alternatives",
        "esg": "Required",
        "max_asset_weight_percent": 10,
        "currency": "GBP base, global exposure allowed",
    },
    "preferences": {
        "investment_style": "Diversified and institutional",
        "products": ["Hedge funds", "Private equity", "Real estate", "ETFs"],
        "communication": "Monthly plus quarterly deep-dive reports",
    },
    "behavioural": {
        "past_reactions": "Calm during crises",
        "decision_style": "Committee-based",
        "biases": ["None significant"],
    },
    "mandate": {
        "type": "Discretionary",
        "fees_percent": 1.2,
        "rebalancing_frequency": "Quarterly",
        "ips": "Multi-asset, ESG-aligned, long-term preservation",
    },
    "portfolio_value": 30000000,
    "max_weight": 10,
    "volatility": 15.0,
    "returns": [0.4, -0.1, 0.5, 0.3, 0.2],
    "ticker": "AOR",
}

PORTFOLIOS = {
    "scenario1": PORTFOLIO_1,
    "scenario2": PORTFOLIO_2,
    "scenario3": PORTFOLIO_3,
    "scenario4": PORTFOLIO_4,
    "scenario5": PORTFOLIO_5,
}

# ============================================================
# BUSINESS LOGIC AND HELPER FUNCTIONS
# ============================================================

#------------------------------------------------------------
#Portfolio Utility Functions
#------------------------------------------------------------
def get_portfolio_display_name(portfolio_dict):  # helper to pick the best name to show for a portfolio
    """Return the best available display name from a portfolio dictionary."""  # description so I remember what this does
    identity = portfolio_dict.get("identity", {})  # safely get the identity section (or empty dict if missing)
    return identity.get("name") or identity.get("company_name") or portfolio_dict.get("client_id", "Unknown Portfolio")  # fallback chain to avoid missing names

#------------------------------------------------------------
#Form Cleaning and Validation Functions
#------------------------------------------------------------
def clean_form_value(field_name, default="Not recorded"):  # cleans text fields so empty values don't break things
    """Return a trimmed form value or a safe default."""  # description of the function
    value = request.form.get(field_name, "")  # get the raw value from the form
    value = value.strip() if isinstance(value, str) else value  # remove extra spaces if it's a string
    return value if value not in ("", None) else default  # return default if the field was empty

def clean_float(field_name, default=0.0):  # safely convert form input into a float
    """Return a numeric form value without breaking if the field is empty."""  # description
    try:
        return float(request.form.get(field_name) or default)  # try converting to float, fallback if empty
    except (TypeError, ValueError):
        return float(default)  # if conversion fails, return the default number

def split_selected_list(value):  # turns comma-separated form values into a clean Python list
    """Convert comma-separated select values into a clean list."""  # description
    if not value:
        return []  # return empty list if nothing was selected
    return [item.strip() for item in str(value).split(",") if item.strip()]  # split, trim, and remove empty items


# ------------------------------------------------------------
# DATABASE CLIENT KEY GENERATION FUNCTIONS
# ------------------------------------------------------------
def get_next_client_number():  # generates the next client number so portfolios stay uniquely numbered
    """Return the next available automated client number.

    Example:
    - existing client_1, client_2, client_3
    - next generated value becomes client_4

    If old records still use scenario1/scenario2 keys, the function falls back
    to total portfolio count + 1 so the next record does not restart at client_1.
    """
    portfolios = Portfolio.query.all()  # get all existing portfolios from the database
    highest_client_number = 0  # track the biggest client number found so far

    for portfolio in portfolios:  # loop through each portfolio
        for value in [portfolio.key, portfolio.client_id]:  # check both key and client_id fields
            match = re.search(r"client[_\s-]*(\d+)", str(value).lower())  # look for patterns like client_3 or client 3
            if match:
                highest_client_number = max(highest_client_number, int(match.group(1)))  # update highest number found

    if highest_client_number > 0:
        return highest_client_number + 1  # continue numbering from the highest existing client number

    return len(portfolios) + 1  # fallback: use total count + 1 if no client numbers were found


    # ------------------------------------------------------------
    # PROFILE DATA BUILDER (MAIN FORM PROCESSOR)
    # ------------------------------------------------------------
def build_profile_data_from_form():  # builds the full JSON profile_data object from the form inputs
    """Build the profile_data JSON object from the easy portfolio profile form."""
    client_type = clean_form_value("client_type", "Individual")  # get client type or default
    display_name = clean_form_value("display_name", "Unnamed Portfolio")  # fallback name

    # -------------------------
    # IDENTITY SECTION
    # -------------------------
    if client_type in ["Corporate", "Family Office", "Trust"]:  # corporate-style identity block
        identity = {
            "company_name": clean_form_value("client_name", display_name),  # company name
            "entity_type": client_type,  # type of entity
            "incorporation_year": clean_form_value("date_of_birth", "Not recorded"),  # reused field
            "residency": clean_form_value("nationality", "Not recorded"),  # residency info
            "tax_residency": clean_form_value("tax_residency", "Not recorded"),  # tax residency
            "address_or_location": clean_form_value("address", "Not recorded"),  # address
            "identification": clean_form_value("identification", "Not recorded"),  # ID number
        }
    else:  # individual-style identity block
        identity = {
            "name": clean_form_value("client_name", display_name),  # person's name
            "client_type": client_type,  # individual type
            "date_of_birth": clean_form_value("date_of_birth", "Not recorded"),  # DOB
            "nationality": clean_form_value("nationality", "Not recorded"),  # nationality
            "tax_residency": clean_form_value("tax_residency", "Not recorded"),  # tax residency
            "address": clean_form_value("address", "Not recorded"),  # address
            "identification": clean_form_value("identification", "Not recorded"),  # ID number
        }

    # -------------------------
    # RETURN FULL PROFILE JSON
    # -------------------------
    return {
        "identity": identity,  # identity block created above
        # -------------------------
        # COMPLIANCE SECTION
        # -------------------------
        "compliance": {
            "kyc": clean_form_value("kyc", "Pending"),
            "aml": clean_form_value("aml", "Pending review"),
            "source_of_wealth": clean_form_value("source_of_wealth", "Not recorded"),
            "source_of_funds": clean_form_value("source_of_funds", "Not recorded"),
            "fatca_crs": clean_form_value("fatca_crs", "Not recorded"),
            "pep": clean_form_value("pep", "Not recorded"),
        },
        # -------------------------
        # OBJECTIVES SECTION
        # -------------------------         
        "objectives": {
            "goals": clean_form_value("goals", "Balanced growth"),  # investment goals
            "time_horizon_years": clean_form_value("time_horizon_years", "Not recorded"),  # time horizon
            "expected_return_percent": clean_form_value("expected_return_percent", "Not recorded"),  # expected return
            "benchmark": clean_form_value("benchmark", clean_form_value("benchmark_ticker", "ACWI")),  # benchmark ticker
        },
        # -------------------------
        # RISK PROFILE SECTION
        # -------------------------
        "risk_profile": {
            "risk_tolerance": clean_form_value("risk_tolerance", "Balanced"),  # tolerance
            "risk_capacity": clean_form_value("risk_capacity", "Medium"),  # capacity
            "max_drawdown_percent": clean_float("max_drawdown_percent", -15),  # max drawdown
        },
        # -------------------------
        # FINANCIALS SECTION
        # -------------------------
        "financials": {
            "net_worth": clean_float("net_worth", 0),  # net worth
            "investments": clean_float("investments", 0),  # investments
            "real_estate": clean_form_value("real_estate", "Not recorded"),  # real estate
            "liabilities": clean_float("liabilities", 0),  # liabilities
            "income": clean_form_value("income", "Not recorded"),  # income
            "expenses": clean_form_value("expenses", "Not recorded"),  # expenses
            "liquidity_needs": clean_form_value("liquidity_needs", "Not recorded"),  # liquidity needs
        },
        # -------------------------
        # CONSTRAINTS SECTION
        # -------------------------
        "constraints": {
            "legal": clean_form_value("legal", "Not recorded"),  # legal constraints
            "esg": clean_form_value("esg", "Not recorded"),  # ESG preferences
            "currency": clean_form_value("currency", "Not recorded"),  # base currency
            "max_position_weight_percent": clean_float("max_weight", 10),  # max weight per position
        },
        # -------------------------
        # PREFERENCES SECTION
        # -------------------------
        "preferences": {
            "investment_style": clean_form_value("investment_style", "Not recorded"),  # style
            "products": split_selected_list(clean_form_value("products", "")),  # preferred products
            "communication": clean_form_value("communication", "Not recorded"),  # communication preference
        },
        # -------------------------
        # BEHAVIOURAL SECTION
        # -------------------------
        "behavioural": {
            "past_reactions": clean_form_value("past_reactions", "Not recorded"),  # past reactions
            "decision_style": clean_form_value("decision_style", "Not recorded"),  # decision style
            "biases": split_selected_list(clean_form_value("biases", "")),  # behavioural biases
        },
        # -------------------------
        # MANDATE SECTION
        # -------------------------
        "mandate": {
            "type": clean_form_value("mandate_type", "Advisory"),  # mandate type
            "fees_percent": clean_float("fees_percent", 0.0),  # fees
            "rebalancing_frequency": clean_form_value("rebalancing_frequency", "Quarterly"),  # rebalancing
            "ips": clean_form_value("ips", "Not recorded"),  # IPS notes
        },
    }

        # ------------------------------------------------------------
        # BACKWARD COMPATIBILITY WRAPPER
        # ------------------------------------------------------------
def make_profile_data(name, client_type, risk_profile, objective, currency, benchmark_ticker, max_weight):
    """Backward-compatible wrapper used only if older code calls this function."""
    return {
        "identity": {
            "name": name,
            "client_type": client_type,
            "nationality": "To be confirmed",
            "tax_residency": "To be confirmed",
            "identification": "To be confirmed",
        },
        "compliance": {
            "kyc": "Pending",
            "aml": "Pending review",
            "source_of_wealth": "To be confirmed",
            "source_of_funds": "To be confirmed",
            "fatca_crs": "To be confirmed",
            "pep": "To be confirmed",
        },
        "objectives": {
            "goals": objective,
            "time_horizon_years": "To be confirmed",
            "expected_return_percent": "To be confirmed",
            "benchmark": benchmark_ticker,
        },
        "risk_profile": {
            "risk_tolerance": risk_profile,
            "risk_capacity": risk_profile,
            "max_drawdown_percent": -10 if risk_profile == "Conservative" else -20 if risk_profile == "Balanced" else -30,
        },
        "financials": {
            "portfolio_value": "Entered in database record",
            "liquidity_needs": "To be confirmed",
        },
        "constraints": {
            "legal": "UCITS / suitable instruments only",
            "esg": "To be confirmed",
            "currency": currency,
            "max_position_weight_percent": max_weight,
        },
        "preferences": {
            "investment_style": objective,
            "products": ["ETFs", "Equities", "Bonds"],
            "communication": "Quarterly review",
        },
        "behavioural": {
            "past_reactions": "To be confirmed",
            "decision_style": "To be confirmed",
            "biases": ["To be confirmed"],
        },
        "mandate": {
            "type": "Advisory",
            "fees_percent": 0.0,
            "rebalancing_frequency": "Quarterly",
            "ips": objective,
        },
    }

        # ------------------------------------------------------------
        # DATABASE SEEDING FUNCTIONS
        # ------------------------------------------------------------
def seed_default_portfolios():  # seeds the database with default portfolios if it's empty
    """Insert the default portfolio scenarios if the database is empty.

    The default records now use automated client-style keys:
    client_1, client_2, client_3, etc.
    """
    if Portfolio.query.first():  # if at least one portfolio exists, stop (no need to seed)
        return

    for number, (_, profile) in enumerate(PORTFOLIOS.items(), start=1):  # loop through default profiles
        automated_key = f"client_{number}"  # generate a client-style key like client_1

        portfolio = Portfolio(  # create a new Portfolio object
            key=automated_key,  # assign generated key
            client_id=automated_key,  # same key used as client_id
            display_name=get_portfolio_display_name(profile),  # pick best display name
            benchmark_ticker=profile.get("ticker", "SPY"),  # fallback benchmark
            portfolio_value=float(profile.get("portfolio_value", 0)),  # convert to float safely
            max_weight=float(profile.get("max_weight", 10)),  # default max weight
            profile_data=profile,  # store the whole profile JSON
        )
        db.session.add(portfolio)  # add to session

    db.session.commit()  # save all seeded portfolios to the database



        # ------------------------------------------------------------
        # PORTFOLIO CHOICE HELPERS
        # ------------------------------------------------------------
def get_portfolio_choices():  # builds dropdown list for forms
    """Return portfolio dropdown choices from the database."""
    return [
        {"key": p.key, "name": p.display_name, "id": p.id}  # return simple dict for UI
        for p in Portfolio.query.order_by(Portfolio.display_name).all()  # sorted alphabetically
    ]


def get_portfolio_by_key(key):  # fetch a portfolio using its unique key
    """Find a portfolio by its unique key."""
    return Portfolio.query.filter_by(key=key).first()  # return first match or None


        # ------------------------------------------------------------
        # SAFE MATH HELPERS
        # ------------------------------------------------------------
def safe_div(a, b):  # avoids division-by-zero errors
    """Divide safely and avoid zero-division errors."""
    return a / b if b not in (0, 0.0, None) else 0.0  # return 0 if denominator is invalid


def parse_weight_to_decimal(weight_text):  # converts "6%" or "1-2%" into decimals
    """Convert text such as '6%' or '1-2%' into decimal weight."""
    if not weight_text:
        return 0.0  # empty input defaults to 0

    numbers = re.findall(r"\d+\.?\d*", str(weight_text))  # extract all numbers
    if not numbers:
        return 0.0  # no numbers found

    values = [float(num) for num in numbers]  # convert to floats
    if len(values) == 1:
        return values[0] / 100.0  # simple case: "6%" → 0.06

    return (sum(values) / len(values)) / 100.0  # average case: "1-2%" → 0.015


        # ------------------------------------------------------------
        # PORTFOLIO LIMIT CALCULATIONS
        # ------------------------------------------------------------
def get_effective_max_weight(portfolio):  # finds the strictest max weight rule
    """Return the strictest maximum weight available for a portfolio."""
    limits = [float(portfolio.max_weight)] if portfolio.max_weight is not None else []  # start with DB value
    profile = portfolio.profile_data or {}  # load profile JSON
    constraints = profile.get("constraints", {})  # get constraints section

    for field in ["max_stock_weight_percent", "max_asset_weight_percent", "max_issuer_weight_percent", "max_position_weight_percent"]:
        if constraints.get(field) is not None:  # if constraint exists
            try:
                limits.append(float(constraints[field]))  # add it to list
            except (TypeError, ValueError):
                pass  # ignore invalid values

    return min(limits) if limits else None  # strictest rule wins


        # ------------------------------------------------------------
        # PORTFOLIO SUMMARY CALCULATIONS
        # ------------------------------------------------------------
def calculate_portfolio_summary(holdings):  # computes summary stats for a portfolio
    """Calculate current portfolio holding summary metrics."""
    if not holdings:  # no holdings → return defaults
        return {
            "position_count": 0,
            "total_allocated_percent": 0.0,
            "remaining_cash_percent": 100.0,
            "average_beta": None,
            "average_score": None,
            "average_expected_return": None,
            "average_volatility": None,
            "status": "No holdings yet",
        }

    total_allocated = sum(h.weight_decimal or 0.0 for h in holdings)  # sum of weights
    betas = [h.beta for h in holdings if h.beta is not None]  # collect betas
    scores = [h.score for h in holdings if h.score is not None]  # collect scores
    returns = [h.expected_return_1y for h in holdings if h.expected_return_1y is not None]  # collect returns
    vols = [h.volatility_1y for h in holdings if h.volatility_1y is not None]  # collect volatilities

    avg_score = round(sum(scores) / len(scores), 2) if scores else None  # average score
    avg_return = round((sum(returns) / len(returns)) * 100, 2) if returns else None  # convert to %
    avg_vol = round((sum(vols) / len(vols)) * 100, 2) if vols else None  # convert to %

    # determine portfolio status based on score
    if avg_score is None:
        status = "Needs more analysis"
    elif avg_score >= 6:
        status = "Performing well"
    elif avg_score >= 3:
        status = "Mixed / monitor"
    else:
        status = "Weak / needs review"

    return {
        "position_count": len(holdings),  # number of stocks
        "total_allocated_percent": round(total_allocated * 100, 2),  # % allocated
        "remaining_cash_percent": round(max(0.0, 1.0 - total_allocated) * 100, 2),  # leftover cash %
        "average_beta": round(sum(betas) / len(betas), 2) if betas else None,  # avg beta
        "average_score": avg_score,  # avg score
        "average_expected_return": avg_return,  # avg expected return
        "average_volatility": avg_vol,  # avg volatility
        "status": status,  # performance label
    }

        # ------------------------------------------------------------
        # GROUPED PORTFOLIO PAYLOAD (FOR JAVASCRIPT)
        # ------------------------------------------------------------
def build_grouped_portfolio_payload():  # groups holdings by portfolio for frontend display
    """Return all holdings grouped by portfolio for JavaScript display."""
    grouped = {}  # final dictionary

    portfolios = Portfolio.query.order_by(Portfolio.display_name).all()  # sorted list
    for portfolio in portfolios:
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio.id).order_by(PortfolioHolding.weight_decimal.desc()).all()  # sorted by weight
        grouped[portfolio.key] = {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.display_name,
            "stocks": [h.to_dict() for h in holdings],  # convert holdings to dicts
            "summary": calculate_portfolio_summary(holdings),  # attach summary
        }

    return grouped


        # ------------------------------------------------------------
        # DEFAULT METRICS (WHEN MARKET DATA IS MISSING)
        # ------------------------------------------------------------
def default_metrics(period_label):  # fallback metrics when API data is unavailable
    """Return default metrics when market data is unavailable."""
    return {
        "annualised_expected_return": 0.0,
        "annualised_volatility": 0.0,
        "sharpe_like": 0.0,
        "latest_price": 0.0,
        "price_start_date": "N/A",
        "price_end_date": "N/A",
        "price_observations": 0,
        "return_start_date": "N/A",
        "return_end_date": "N/A",
        "return_observations": 0,
        "returns_series": None,
        "period_label": period_label,
    }

# ============================================================
# FINANCIAL ANALYSIS ENGINE
# ============================================================
        # ------------------------------------------------------------
        #  PRICE + RETURN METRICS (Yahoo Finance data download)
        # ------------------------------------------------------------
def compute_metrics(ticker, period):  # main function that downloads data + calculates return/volatility
    """Download Yahoo Finance data and calculate expected return, volatility, and Sharpe-like ratio."""
    try:
        data = yf.download(ticker, period=period, auto_adjust=True, progress=False)  # fetch price history from Yahoo
    except Exception:
        return default_metrics(period)  # if Yahoo fails, return safe defaults

    if data is None or data.empty:  # no data returned
        return default_metrics(period)

    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:  # fix multi-index columns (common with ETFs)
        data.columns = data.columns.get_level_values(0)

    if "Close" not in data.columns:  # if no closing price column, we can't compute anything
        return default_metrics(period)

    close_prices = data["Close"].dropna()  # clean closing prices
    if close_prices.empty or len(close_prices) < 2:  # need at least 2 prices to compute returns
        return default_metrics(period)

    returns = close_prices.pct_change().dropna()  # daily returns
    if returns.empty:
        return default_metrics(period)

    annualised_volatility = float(returns.std() * np.sqrt(252))  # convert daily volatility → annual
    annualised_expected_return = float(returns.mean() * 252)  # convert daily return → annual
    sharpe_like = safe_div(annualised_expected_return, annualised_volatility)  # avoid divide-by-zero

    return {  # return all metrics in a clean dictionary
        "annualised_expected_return": annualised_expected_return,
        "annualised_volatility": annualised_volatility,
        "sharpe_like": sharpe_like,
        "latest_price": float(close_prices.iloc[-1]),  # most recent price
        "price_start_date": close_prices.index[0].strftime("%Y-%m-%d"),
        "price_end_date": close_prices.index[-1].strftime("%Y-%m-%d"),
        "price_observations": int(len(close_prices)),
        "return_start_date": returns.index[0].strftime("%Y-%m-%d"),
        "return_end_date": returns.index[-1].strftime("%Y-%m-%d"),
        "return_observations": int(len(returns)),
        "returns_series": returns,  # used later for beta calculation
        "period_label": period,
    }

        # ------------------------------------------------------------
        # QUARTERLY FORECASTING (simple compounding model)
        # ------------------------------------------------------------
def build_quarterly_forecast(latest_price, annualised_expected_return):  # builds 4-quarter price forecast
    """Build simple quarterly price forecast from annualised return."""
    adjusted_return = max(annualised_expected_return, -0.95)  # cap downside so forecast doesn't explode
    quarterly_return = (1 + adjusted_return) ** 0.25 - 1  # convert annual → quarterly

    q1_price = latest_price * (1 + quarterly_return)  # quarter 1 forecast
    q2_price = q1_price * (1 + quarterly_return)  # quarter 2
    q3_price = q2_price * (1 + quarterly_return)  # quarter 3
    q4_price = q3_price * (1 + quarterly_return)  # quarter 4

    return {  # return all forecasted prices
        "quarterly_return": quarterly_return,
        "q1_expected_price": q1_price,
        "q2_expected_price": q2_price,
        "q3_expected_price": q3_price,
        "q4_expected_price": q4_price,
    }

        # ------------------------------------------------------------
        # SCORING ENGINE (turns metrics → decision)
        # ------------------------------------------------------------
def score_and_decide(expected_return, volatility, sharpe_like, beta):  # converts metrics into a score + decision
    """Convert market metrics into a score, decision, and suggested weight."""
    score = 0  # start at zero and add points based on quality

    # --- return scoring ---
    if expected_return >= 0.02:  # strong expected return
        score += 2

    # --- volatility scoring ---
    if volatility <= 0.08:  # low volatility = safer
        score += 3
    elif volatility <= 0.12:  # medium volatility
        score += 1

    # --- Sharpe-like scoring ---
    if sharpe_like > 0.6:  # strong risk-adjusted return
        score += 2
    elif sharpe_like > 0.3:
        score += 1

    # --- beta scoring ---
    if beta is not None:
        if beta <= 0.9:  # defensive stock
            score += 2
        elif beta <= 1.1:  # neutral stock
            score += 1

    # --- final decision buckets ---
    if score >= 7:
        return {"score": score, "decision": "YES — high conviction", "recommended_weight": "6%", "tag": "High conviction"}
    if score >= 5:
        return {"score": score, "decision": "YES — core holding", "recommended_weight": "3.5%", "tag": "Core holding"}
    if score >= 3:
        return {"score": score, "decision": "YES — satellite", "recommended_weight": "3%", "tag": "Diversifier"}
    if score >= 1:
        return {"score": score, "decision": "LIMITED — high risk / exploratory", "recommended_weight": "1–2%", "tag": "Exploratory"}

    return {"score": score, "decision": "NO — hold as cash instead", "recommended_weight": "Cash (5%)", "tag": "Cash / Risk Control"}


        # ------------------------------------------------------------
        # 4) PORTFOLIO VALIDATION (checks if a stock can be added)
        # ------------------------------------------------------------
def validate_portfolio_addition(portfolio, ticker, recommended_weight, sector, industry):  # ensures holding respects rules
    """Validate whether a proposed holding is allowed inside the selected portfolio."""
    errors = []  # hard stops
    warnings = []  # soft alerts

    weight_decimal = parse_weight_to_decimal(recommended_weight)  # convert "6%" → 0.06
    weight_percent = weight_decimal * 100
    max_weight_allowed = get_effective_max_weight(portfolio)  # strictest rule

    # --- weight limit check ---
    if max_weight_allowed is not None and weight_percent > max_weight_allowed:
        errors.append(f"Recommended weight of {weight_percent:.2f}% exceeds the portfolio limit of {max_weight_allowed:.2f}%.")

    # --- total allocation check ---
    current_total_excluding_same_ticker = sum(
        h.weight_decimal or 0.0
        for h in portfolio.holdings
        if h.ticker != ticker
    )

    projected_total = current_total_excluding_same_ticker + weight_decimal
    if projected_total > 1.0:  # cannot exceed 100%
        errors.append(f"Projected total allocation would be {projected_total * 100:.2f}%, which exceeds 100%.")

    # --- mandate constraints ---
    constraints = (portfolio.profile_data or {}).get("constraints", {})
    legal_rule = str(constraints.get("legal", "")).lower()

    if "prohibits equities" in legal_rule:  # equity restriction
        fixed_income_tickers = {"IEF", "SHY", "AGG", "BND", "TIP"}
        if ticker not in fixed_income_tickers:
            errors.append("This mandate prohibits equities. Only fixed-income style instruments should be added.")

    esg_rule = str(constraints.get("esg", "")).lower()
    if "no tobacco" in esg_rule:  # ESG restriction
        if "tobacco" in str(sector).lower() or "tobacco" in str(industry).lower():
            errors.append("This mandate excludes tobacco-related exposure.")

    currency_rule = constraints.get("currency")
    if currency_rule in ["EUR only", "CHF only"]:  # soft warning
        warnings.append(f"Manual currency review recommended because this mandate states {currency_rule}.")

    return {"errors": errors, "warnings": warnings, "weight_decimal": weight_decimal}


        # ------------------------------------------------------------
        # 5) FULL STOCK ANALYSIS (metrics + beta + forecast + decision)
        # ------------------------------------------------------------
def analyze_stock(ticker, benchmark_ticker, portfolio_key):  # main analysis function used by the UI
    """Analyse a stock or ETF and return JSON-friendly results."""
    metrics_1y = compute_metrics(ticker, "1y")  # 1-year metrics
    metrics_3m = compute_metrics(ticker, "3mo")  # 3-month metrics
    benchmark_metrics = compute_metrics(benchmark_ticker, "1y")  # benchmark metrics

    beta = 0.0  # default beta
    beta_observations = 0

    # --- beta calculation ---
    if metrics_1y["returns_series"] is not None and benchmark_metrics["returns_series"] is not None:
        stock_aligned, bench_aligned = metrics_1y["returns_series"].align(
            benchmark_metrics["returns_series"],
            join="inner",
        )
        beta_observations = int(len(stock_aligned))

        if len(stock_aligned) > 1 and bench_aligned.var() != 0:  # avoid divide-by-zero
            beta = float(stock_aligned.cov(bench_aligned) / bench_aligned.var())

    # --- scoring + decision ---
    decision_pack = score_and_decide(
        expected_return=metrics_1y["annualised_expected_return"],
        volatility=metrics_1y["annualised_volatility"],
        sharpe_like=metrics_1y["sharpe_like"],
        beta=beta,
    )

    # --- sector + industry lookup ---
    try:
        info = yf.Ticker(ticker).info or {}
        sector = info.get("sector") or info.get("category") or info.get("fundCategory") or "Unknown"
        industry = info.get("industry") or info.get("quoteType") or info.get("fundFamily") or "Unknown"
    except Exception:
        sector = "Unknown"
        industry = "Unknown"

    # --- forecasts ---
    forecast_1y = build_quarterly_forecast(metrics_1y["latest_price"], metrics_1y["annualised_expected_return"])
    forecast_3m = build_quarterly_forecast(metrics_3m["latest_price"], metrics_3m["annualised_expected_return"])
    portfolio = get_portfolio_by_key(portfolio_key)

    # --- final JSON response ---
    return {
        "ticker": ticker.upper(),
        "portfolio_key": portfolio_key,
        "portfolio_name": portfolio.display_name if portfolio else "Unknown Portfolio",
        "beta": beta,
        "score": decision_pack["score"],
        "decision": decision_pack["decision"],
        "recommended_weight": decision_pack["recommended_weight"],
        "sector": sector,
        "industry": industry,
        "tag": decision_pack["tag"],
        "benchmark_ticker": benchmark_ticker,
        "benchmark_start_date": benchmark_metrics.get("return_start_date", "N/A"),
        "benchmark_end_date": benchmark_metrics.get("return_end_date", "N/A"),
        "beta_observations": beta_observations,
        "one_year": {
            "annualised_expected_return": metrics_1y["annualised_expected_return"],
            "annualised_volatility": metrics_1y["annualised_volatility"],
            "sharpe_like": metrics_1y["sharpe_like"],
            "latest_price": metrics_1y["latest_price"],
            "forecast": forecast_1y,
        },
        "three_month": {
            "annualised_expected_return": metrics_3m["annualised_expected_return"],
            "annualised_volatility": metrics_3m["annualised_volatility"],
            "sharpe_like": metrics_3m["sharpe_like"],
            "latest_price": metrics_3m["latest_price"],
            "forecast": forecast_3m,
        },
    }

# ============================================================
# MARKET DASHBOARD DATA
# ============================================================

# This dictionary is basically the “universe” of tickers that my dashboard uses.
# I grouped them by category so the dashboard feels more like a real investment tool.
MASTER_TICKERS = {
    "fixed_income": [
        "SHY", "IEF", "TLT", "BND", "AGG", "TIP", "LQD", "HYG", "VGIT", "VCIT",
        "MINT", "BIL", "JPST", "SCHR", "SCHZ", "IGIB", "SPTI", "GOVT", "BSV", "VGSH"
    ],
    "defensive_equities": [
        "XLP", "XLV", "XLU", "PG", "KO", "PEP", "JNJ", "MRK", "PFE",
        "WMT", "MCD", "CL", "KMB", "DUK", "SO", "NEE", "GIS", "MDT", "HSY", "EL"
    ],
    "core_equities": [
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", "JPM", "V", "MA", "UNH",
        "HD", "ADBE", "CRM", "ORCL", "CSCO", "INTU", "AVGO", "NFLX",
        "QCOM", "LIN", "TXN", "HON", "CAT", "IBM", "AMGN", "NOW", "BKNG",
        "AXP", "GS", "BLK", "SPGI"
    ],
    "growth_equities": [
        "TSLA", "NVDA", "AMD", "SHOP", "SQ", "UBER", "PANW", "CRWD", "SNOW", "PLTR",
        "MDB", "DDOG", "NET", "ZS", "TEAM", "ABNB", "MELI", "SE", "TTD", "ROKU",
        "ARKK", "QQQ", "SMH", "SOXX", "IWF", "VUG", "XLK", "FTEC", "SCHG", "MGK"
    ],
    "international_equities": [
        "VEA", "IEFA", "EWG", "EWQ", "EWI", "EWJ", "EWS", "EWA", "EWU", "EWP",
        "VGK", "EZU", "FEZ", "AAXJ", "VWO", "EEM", "INDA", "EWY", "MCHI", "FXI",
        "EWZ", "EWT", "EIDO", "EPHE", "EZA", "ERUS", "EWC", "EWL", "EWD", "EWN"
    ],
    "alternatives": [
        "GLD", "SLV", "VNQ", "REET", "SCHH", "REM", "DBC", "PDBC", "USO", "IAU",
        "VNQI", "RWO", "FTGC", "COMT", "GSG", "DBA", "UUP", "FXE", "FXF", "FXY",
        "BITO", "ETHE", "PALL", "PLTM", "URA", "COPX", "WOOD", "HACK", "CIBR", "KWEB"
    ]
}
        # ------------------------------------------------------------
        # DASHBOARD CACHE CONFIGURATION
        # ------------------------------------------------------------
dashboard_cache = {"rows": None, "timestamp": 0}  # tiny in-memory cache so we don't hammer Yahoo every time someone opens the dashboard
DASHBOARD_CACHE_SECONDS = 300  # cache for 5 minutes — short enough to stay reasonably fresh, long enough to save API calls

        # ------------------------------------------------------------
        # BATCH METRIC COMPUTATION (used for the dashboard)
        # ------------------------------------------------------------
def compute_metrics_from_batch(batch_data, ticker):
    """Calculate metrics for one ticker from batch-downloaded data."""
    try:
        if batch_data is None or batch_data.empty:
            return default_metrics("1y")  # If the batch download failed, return safe defaults so the UI doesn’t break.

        # Yahoo sometimes returns multi‑index columns when downloading many tickers at once.
        if hasattr(batch_data.columns, "nlevels") and batch_data.columns.nlevels > 1:
            # Check if the ticker exists in the batch — sometimes Yahoo omits tickers silently.
            if ticker not in batch_data.columns.get_level_values(0):
                return default_metrics("1y")
            ticker_data = batch_data[ticker].copy()  # Extract the sub‑DataFrame for this ticker.
        else:
            ticker_data = batch_data.copy()  # Single‑ticker or flattened case.

        if "Close" not in ticker_data.columns:
            return default_metrics("1y")  # Without closing prices, we can’t compute returns.

        close_prices = ticker_data["Close"].dropna()
        if close_prices.empty or len(close_prices) < 2:
            return default_metrics("1y")  # Need at least two prices to compute returns.

        returns = close_prices.pct_change().dropna()
        if returns.empty:
            return default_metrics("1y")

        # Convert daily metrics → annual metrics.
        annualised_volatility = float(returns.std() * np.sqrt(252))
        annualised_expected_return = float(returns.mean() * 252)
        sharpe_like = safe_div(annualised_expected_return, annualised_volatility)

        return {
            "annualised_expected_return": annualised_expected_return,
            "annualised_volatility": annualised_volatility,
            "sharpe_like": sharpe_like,
            "latest_price": float(close_prices.iloc[-1]),
            "returns_series": returns,
            "period_label": "1y",
        }
    except Exception:
        return default_metrics("1y")  # Any unexpected error → safe fallback.

        # ------------------------------------------------------------
        # BUILD MARKET DASHBOARD ROWS
        # ------------------------------------------------------------
def build_market_rows():
    """Build dashboard table rows from the ticker universe."""
    # Flatten all ticker groups into one sorted list.
    dashboard_tickers = sorted({ticker for group in MASTER_TICKERS.values() for ticker in group})
    rows = []

    # Try downloading all tickers in one batch — much faster than individual calls.
    try:
        batch_data = yf.download(
            tickers=dashboard_tickers,
            period="1y",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False,
        )
    except Exception:
        batch_data = None  # If the batch fails, we still compute rows using default metrics.

    for ticker in dashboard_tickers:
        metrics_1y = compute_metrics_from_batch(batch_data, ticker)

        # Use the same scoring engine as the main analysis page.
        decision_pack = score_and_decide(
            expected_return=metrics_1y["annualised_expected_return"],
            volatility=metrics_1y["annualised_volatility"],
            sharpe_like=metrics_1y["sharpe_like"],
            beta=None,  # Beta not used in dashboard ranking.
        )

        # Ranking score: a simple weighted formula to sort tickers by attractiveness.
        ranking_score = (
            (metrics_1y["annualised_expected_return"] * 0.50)
            + (metrics_1y["sharpe_like"] * 0.30)
            - (metrics_1y["annualised_volatility"] * 0.20)
        )

        rows.append({
            "ticker": ticker,
            "latest_price": round(metrics_1y["latest_price"], 2),
            "score": decision_pack["score"],
            "decision": decision_pack["decision"],
            "tag": decision_pack["tag"],
            "suggested_weight": decision_pack["recommended_weight"],
            "expected_return_percent": round(metrics_1y["annualised_expected_return"] * 100, 2),
            "volatility": round(metrics_1y["annualised_volatility"] * 100, 2),
            "sharpe_like": round(metrics_1y["sharpe_like"], 2),
            "ranking_score": round(ranking_score, 3),

            # Flags used by the UI to highlight certain types of opportunities.
            "is_low_risk": metrics_1y["annualised_volatility"] <= 0.18 and decision_pack["decision"] != "NO — hold as cash instead",
            "is_high_conviction": decision_pack["decision"] == "YES — high conviction",
            "is_core_holding": decision_pack["decision"] == "YES — core holding",
            "is_satellite": decision_pack["decision"] == "YES — satellite",
            "is_exploratory": decision_pack["decision"] == "LIMITED — high risk / exploratory",
            "is_income_candidate": ticker in {"IEF", "SHY", "AGG", "BND", "TIP", "XLP", "XLV", "XLU"},
            "is_best_ranked": decision_pack["score"] >= 5 and metrics_1y["sharpe_like"] >= 0.3,
            "is_cash_candidate": decision_pack["decision"] == "NO — hold as cash instead",
        })

    # Sort by ranking score so the best ideas appear at the top of the dashboard.
    rows.sort(key=lambda row: row["ranking_score"], reverse=True)
    return rows

        # ------------------------------------------------------------
        # CACHED MARKET ROWS (avoid repeated downloads)
        # ------------------------------------------------------------
def get_cached_market_rows():
    """Cache dashboard rows briefly to avoid repeated downloads."""
    now = time.time()
    if dashboard_cache["rows"] is None or now - dashboard_cache["timestamp"] > DASHBOARD_CACHE_SECONDS:
        dashboard_cache["rows"] = build_market_rows()
        dashboard_cache["timestamp"] = now
    return dashboard_cache["rows"]

        # ------------------------------------------------------------
        # PORTFOLIO PERFORMANCE DASHBOARD
        # ------------------------------------------------------------
def build_portfolio_performance_rows():
    """Build performance dashboard rows for the Criteria page."""
    portfolios = Portfolio.query.order_by(Portfolio.display_name).all()
    rows = []

    for portfolio in portfolios:
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio.id).all()
        summary = calculate_portfolio_summary(holdings)

        rows.append({
            "portfolio_name": portfolio.display_name,
            "portfolio_key": portfolio.key,
            "benchmark_ticker": portfolio.benchmark_ticker,
            "portfolio_value": portfolio.portfolio_value,
            "max_weight": portfolio.max_weight,
            "position_count": summary["position_count"],
            "total_allocated_percent": summary["total_allocated_percent"],
            "remaining_cash_percent": summary["remaining_cash_percent"],
            "average_beta": summary["average_beta"],
            "average_score": summary["average_score"],
            "average_expected_return": summary["average_expected_return"],
            "average_volatility": summary["average_volatility"],
            "status": summary["status"],
        })

    # Sort portfolios by score (best performing first).
    rows.sort(key=lambda row: row["average_score"] if row["average_score"] is not None else -1, reverse=True)
    return rows


# ============================================================
# FLASK APPLICATION ROUTES
# ROUTES: HTML PAGES
# ============================================================
        # ------------------------------------------------------------
        # HOME PAGE ROUTE
        # ------------------------------------------------------------
@app.route("/")  # This is the root URL of the entire application — the first page users see.
def home():  # Very simple route: just renders the homepage template.
    return render_template("index.html", active_page="home")  # Passes 'active_page' so the navbar highlights correctly.

        # ------------------------------------------------------------
        # PORTFOLIO PROFILES PAGE (CREATE + VIEW PORTFOLIOS)
        # ------------------------------------------------------------
@app.route("/portfolio_profiles", methods=["GET", "POST"])  # Supports both GET (view page) and POST (submit form).
def portfolio_profiles():  # This route handles the entire workflow for creating new portfolio profiles.
    if request.method == "POST":  # If the user submitted the form, we need to validate and save the data.
        display_name = clean_form_value("display_name", "").strip()  # Clean and trim the portfolio name.
        benchmark_ticker = clean_form_value("benchmark_ticker", "ACWI").upper()  # Default benchmark is ACWI; uppercase for consistency.
        portfolio_value = clean_float("portfolio_value", 0)  # Convert portfolio value safely to float.
        max_weight = clean_float("max_weight", 10)  # Convert max weight safely to float.

        # --- BASIC VALIDATION ---
        if not display_name:  # If the user forgot to enter a name, we stop here.
            flash("Portfolio name is required.", "error")  # Flash a friendly error message.
            return redirect(url_for("portfolio_profiles"))  # Redirect back so the user can fix the issue.

        # --- GENERATE UNIQUE CLIENT KEY ---
        client_number = get_next_client_number()  # Get the next available client number (client_1, client_2, etc.)
        automated_key = f"client_{client_number}"  # Build the key string.

        # Ensure the generated key is truly unique — avoid collisions if DB already has similar keys.
        while Portfolio.query.filter_by(key=automated_key).first() or Portfolio.query.filter_by(client_id=automated_key).first():
            client_number += 1  # Increment the number until we find a free one.
            automated_key = f"client_{client_number}"

        # --- BUILD PROFILE JSON FROM FORM ---
        profile_data = build_profile_data_from_form()  # This collects all form fields into a structured JSON object.

        # --- CREATE PORTFOLIO OBJECT ---
        portfolio = Portfolio(
            key=automated_key,  # Unique internal key.
            client_id=automated_key,  # Mirrors the key for simplicity.
            display_name=display_name,  # Human-friendly name shown in the UI.
            benchmark_ticker=benchmark_ticker,  # Benchmark used for comparisons.
            portfolio_value=portfolio_value,  # Total portfolio value.
            max_weight=max_weight,  # Maximum allowed weight per position.
            profile_data=profile_data,  # Full JSON profile.
        )

        db.session.add(portfolio)  # Stage the new portfolio for saving.
        db.session.commit()  # Commit to the database — this is where the record is actually created.

        flash(f"New portfolio profile saved as {automated_key}.", "success")  # Confirmation message for the user.
        return redirect(url_for("portfolio_profiles"))  # Redirect to avoid duplicate submissions.

    # --- GET REQUEST: SHOW PAGE ---
    next_client_number = get_next_client_number()  # Suggest the next client key for the UI.
    return render_template(
        "portfolio_profiles.html",
        active_page="portfolio_profiles",  # Highlights the correct navbar item.
        portfolios=Portfolio.query.order_by(Portfolio.id).all(),  # Pass all existing portfolios to the template.
        next_client_key=f"client_{next_client_number}",  # Pre-fill the next available client key.
    )


        # ------------------------------------------------------------
        # UPDATE PORTFOLIO PROFILE ROUTE
        # ------------------------------------------------------------
@app.route("/portfolio_profiles/<int:portfolio_id>/update", methods=["POST"])
def update_portfolio_profile(portfolio_id):
    """Update an existing portfolio profile.

    This route demonstrates the UPDATE part of CRUD for the Portfolio table.
    It reuses the same simplified questionnaire fields as the Create form.
    """
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    display_name = clean_form_value("display_name", "").strip()
    benchmark_ticker = clean_form_value("benchmark_ticker", portfolio.benchmark_ticker).upper()
    portfolio_value = clean_float("portfolio_value", portfolio.portfolio_value)
    max_weight = clean_float("max_weight", portfolio.max_weight)

    if not display_name:
        flash("Portfolio name is required before updating.", "error")
        return redirect(url_for("portfolio_profiles"))

    portfolio.display_name = display_name
    portfolio.benchmark_ticker = benchmark_ticker
    portfolio.portfolio_value = portfolio_value
    portfolio.max_weight = max_weight
    portfolio.profile_data = build_profile_data_from_form()
    portfolio.updated_at = datetime.utcnow()

    db.session.commit()

    flash(f"Portfolio profile {portfolio.client_id} was updated successfully.", "success")
    return redirect(url_for("portfolio_profiles"))


        # ------------------------------------------------------------
        # DELETE PORTFOLIO PROFILE ROUTE
        # ------------------------------------------------------------
@app.route("/portfolio_profiles/<int:portfolio_id>/delete", methods=["POST"])
def delete_portfolio_profile(portfolio_id):
    """Delete an existing portfolio profile and its related holdings.

    This route demonstrates DELETE for the Portfolio table. The SQLAlchemy
    relationship cascade also removes linked holdings and analysis records.
    """
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    portfolio_name = portfolio.display_name

    db.session.delete(portfolio)
    db.session.commit()

    flash(f"Portfolio profile '{portfolio_name}' and its related records were deleted.", "success")
    return redirect(url_for("portfolio_profiles"))


        # ------------------------------------------------------------
        # MARKET DASHBOARD ROUTE
        # ------------------------------------------------------------
@app.route("/market_dashboard")  # This page shows the big market dashboard with all tickers + metrics.
def market_dashboard():  # Fetches cached rows to avoid re-downloading data every time.
    rows = get_cached_market_rows()  # Cached for 5 minutes to reduce API load.
    return render_template(
        "market_dashboard.html",
        active_page="market_dashboard",
        rows=rows,  # The computed market rows (scores, volatility, Sharpe-like, etc.)
        portfolio_choices=get_portfolio_choices(),  # Allows user to assign tickers to portfolios.
    )

        # ------------------------------------------------------------
        # PORTFOLIO PERFORMANCE ROUTE
        # ------------------------------------------------------------
@app.route("/portfolio_performance")  # This page shows a high-level summary of each portfolio's performance.
def portfolio_performance():  # Builds both summary rows and grouped holdings for charts.
    return render_template(
        "portfolio_performance.html",
        active_page="portfolio_performance",
        performance_rows=build_portfolio_performance_rows(),  # Summary metrics per portfolio.
        grouped_portfolios=build_grouped_portfolio_payload(),  # Detailed holdings grouped for JS rendering.
    )

        # ------------------------------------------------------------
        # CONTACT PAGE ROUTE
        # ------------------------------------------------------------
@app.route("/contact", methods=["GET", "POST"])  # Users can submit messages; admin can view recent ones.
def contact():  # Handles both saving new messages and displaying recent ones.
    if request.method == "POST":  # If the form was submitted, save the message.
        message = ContactMessage(
            name=request.form.get("name", "").strip(),  # Clean sender name.
            email=request.form.get("email", "").strip(),  # Clean sender email.
            message=request.form.get("message", "").strip(),  # Clean message body.
        )
        db.session.add(message)  # Stage for saving.
        db.session.commit()  # Commit to DB.

        flash("Contact message saved to the database.", "success")  # Confirmation for the user.
        return redirect(url_for("contact"))  # Redirect to clear the form.

    # GET request: show the 10 most recent messages.
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(10).all()
    return render_template("contact.html", active_page="contact", messages=messages)


        # ------------------------------------------------------------
        # REST API ROUTES
        # ------------------------------------------------------------
@app.route("/analyze", methods=["POST"])  # This endpoint is called when the user clicks “Analyze” on the dashboard.
def analyze():  # It performs a full stock analysis and returns the results as JSON.
    ticker = request.form.get("ticker", "").strip().upper()  # Clean the ticker: remove spaces + uppercase for consistency.
    portfolio_key = request.form.get("portfolio_key", "").strip()  # Identify which portfolio the user selected.

    portfolio = get_portfolio_by_key(portfolio_key)  # Fetch the portfolio object from the database.
    if not portfolio:  # If the portfolio doesn’t exist, we stop immediately.
        return jsonify({"error": "Invalid portfolio selected."}), 400  # Return a JSON error with HTTP 400.

    if not ticker:  # If the user didn’t choose a ticker, we can’t analyze anything.
        return jsonify({"error": "Please select a ticker."}), 400

    try:
        # --- RUN THE FULL ANALYSIS ENGINE ---
        # This calls compute_metrics(), score_and_decide(), build_forecast(), etc.
        result = analyze_stock(ticker, portfolio.benchmark_ticker, portfolio.key)

        # --- SAVE ANALYSIS RECORD TO DATABASE ---
        # This creates a permanent log of the analysis so the portfolio history is preserved.
        record = AnalysisRecord(
            portfolio_id=portfolio.id,  # Link the analysis to the correct portfolio.
            ticker=ticker,  # Store the analyzed ticker.
            beta=result["beta"],  # Save beta value.
            score=result["score"],  # Save the computed score.
            decision=result["decision"],  # Save the decision text.
            expected_return_1y=result["one_year"]["annualised_expected_return"],  # Save expected return.
            volatility_1y=result["one_year"]["annualised_volatility"],  # Save volatility.
            sharpe_like_1y=result["one_year"]["sharpe_like"],  # Save Sharpe-like ratio.
            raw_result=result,  # Store the entire JSON result for transparency and debugging.
        )
        db.session.add(record)  # Stage the record for saving.
        db.session.commit()  # Commit to the database.

        return jsonify(result)  # Return the full analysis result to the frontend.

    except Exception as e:  # If anything unexpected happens, we catch it so the app doesn’t crash.
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500  # Return a safe error message.


        # ------------------------------------------------------------
        # ADD STOCK TO PORTFOLIO (AFTER ANALYSIS)
        # ------------------------------------------------------------
@app.route("/add-to-portfolio", methods=["POST"])  # This endpoint is called when the user clicks “Add to Portfolio”.
def add_to_portfolio():  # It validates the holding, applies constraints, and saves it.
    """Analyse a selected ticker and save or update it as a portfolio holding.

    This endpoint demonstrates CREATE and UPDATE for the PortfolioHolding table.
    The same ticker in the same portfolio is updated instead of duplicated because
    of the unique database constraint on portfolio_id + ticker.
    """
    try:
        data = request.get_json(force=True)  # Parse JSON body from the request.

        ticker = data.get("ticker", "").strip().upper()  # Clean ticker.
        portfolio_key = data.get("portfolio_key", "").strip()  # Identify portfolio.
        portfolio = get_portfolio_by_key(portfolio_key)  # Fetch portfolio object.

        if not ticker or not portfolio:  # Basic validation.
            return jsonify({"error": "Invalid stock or portfolio."}), 400

        analysis = analyze_stock(ticker, portfolio.benchmark_ticker, portfolio.key)

        validation = validate_portfolio_addition(
            portfolio=portfolio,
            ticker=ticker,
            recommended_weight=analysis["recommended_weight"],
            sector=analysis["sector"],
            industry=analysis["industry"],
        )

        if validation["errors"]:
            return jsonify({"error": validation["errors"], "warnings": validation["warnings"]}), 400

        holding = PortfolioHolding.query.filter_by(portfolio_id=portfolio.id, ticker=ticker).first()
        if not holding:
            holding = PortfolioHolding(portfolio_id=portfolio.id, ticker=ticker)
            db.session.add(holding)
            message = f"{ticker} added to {portfolio.display_name}."
        else:
            message = f"{ticker} updated in {portfolio.display_name}."

        holding.recommended_weight = analysis["recommended_weight"]
        holding.weight_decimal = validation["weight_decimal"]
        holding.decision = analysis["decision"]
        holding.tag = analysis["tag"]
        holding.sector = analysis["sector"]
        holding.industry = analysis["industry"]
        holding.beta = analysis["beta"]
        holding.score = analysis["score"]
        holding.expected_return_1y = analysis["one_year"]["annualised_expected_return"]
        holding.volatility_1y = analysis["one_year"]["annualised_volatility"]
        holding.sharpe_like_1y = analysis["one_year"]["sharpe_like"]
        holding.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "message": message,
            "warnings": validation["warnings"],
            "portfolio": build_grouped_portfolio_payload(),
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Could not save holding: {str(e)}"}), 500

        # ------------------------------------------------------------
        # GET ALL PORTFOLIO STOCKS (USED BY JAVASCRIPT)
        # ------------------------------------------------------------
@app.route("/portfolio-stocks")  # This endpoint returns all holdings grouped by portfolio.
def portfolio_stocks():  # Used by the frontend to refresh the holdings table dynamically.
    return jsonify(build_grouped_portfolio_payload())  # Return the grouped holdings as JSON.

        # ------------------------------------------------------------
        # DELETE A HOLDING FROM A PORTFOLIO
        # ------------------------------------------------------------
@app.route("/delete-holding/<int:holding_id>", methods=["DELETE"])  # Called when user clicks “Delete” on a holding.
def delete_holding(holding_id):  # Deletes the holding and returns updated portfolio data.
    holding = PortfolioHolding.query.get_or_404(holding_id)  # If holding doesn’t exist → 404 error.
    ticker = holding.ticker  # Save ticker for message.
    portfolio_name = holding.portfolio.display_name  # Save portfolio name for message.

    db.session.delete(holding)  # Remove the holding from the database.
    db.session.commit()  # Commit deletion.

    return jsonify({
        "message": f"{ticker} deleted from {portfolio_name}.",  # Friendly confirmation.
        "portfolio": build_grouped_portfolio_payload(),  # Updated portfolio data.
    })

# ============================================================
# APPLICATION STARTUP AND DATABASE INITIALISATION
# ============================================================
with app.app_context():
    db.create_all()
    seed_default_portfolios()


if __name__ == "__main__":
    app.run(debug=True)
