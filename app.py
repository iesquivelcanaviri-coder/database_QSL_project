# ============================================================
# Portfolio Management Decision-Support Web Application
# Flask + PostgreSQL + SQLAlchemy ORM
# ============================================================

import os
import re
import time
from datetime import datetime

import numpy as np
import yfinance as yf
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


# ============================================================
# FLASK AND DATABASE CONFIGURATION
# ============================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-before-deployment")

database_url = os.environ.get("DATABASE_URL", "sqlite:///portfolio_database.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# SQLALCHEMY MODELS
# ============================================================

class Portfolio(db.Model):
    """Stores one client portfolio mandate."""

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    client_id = db.Column(db.String(150), nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    benchmark_ticker = db.Column(db.String(20), nullable=False)
    portfolio_value = db.Column(db.Float, nullable=False, default=0.0)
    max_weight = db.Column(db.Float, nullable=False, default=10.0)
    profile_data = db.Column(db.JSON, nullable=False)

    holdings = db.relationship(
        "PortfolioHolding",
        backref="portfolio",
        cascade="all, delete-orphan",
        lazy=True,
    )

    analysis_records = db.relationship(
        "AnalysisRecord",
        backref="portfolio",
        cascade="all, delete-orphan",
        lazy=True,
    )


class PortfolioHolding(db.Model):
    """Stores a ticker saved into a portfolio."""

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    recommended_weight = db.Column(db.String(40), nullable=False)
    weight_decimal = db.Column(db.Float, nullable=False, default=0.0)
    decision = db.Column(db.String(120), nullable=False)
    tag = db.Column(db.String(80), nullable=True)
    sector = db.Column(db.String(120), nullable=True)
    industry = db.Column(db.String(160), nullable=True)
    beta = db.Column(db.Float, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    expected_return_1y = db.Column(db.Float, nullable=True)
    volatility_1y = db.Column(db.Float, nullable=True)
    sharpe_like_1y = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="unique_portfolio_ticker"),
    )

    def to_dict(self):
        """Return one holding as a JSON-friendly dictionary."""
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "portfolio_name": self.portfolio.display_name,
            "ticker": self.ticker,
            "recommended_weight": self.recommended_weight,
            "weight_decimal": self.weight_decimal,
            "decision": self.decision,
            "tag": self.tag,
            "sector": self.sector,
            "industry": self.industry,
            "beta": self.beta,
            "score": self.score,
            "expected_return_1y": self.expected_return_1y,
            "volatility_1y": self.volatility_1y,
            "sharpe_like_1y": self.sharpe_like_1y,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalysisRecord(db.Model):
    """Stores completed ticker analysis results."""

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    beta = db.Column(db.Float, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    decision = db.Column(db.String(120), nullable=True)
    expected_return_1y = db.Column(db.Float, nullable=True)
    volatility_1y = db.Column(db.Float, nullable=True)
    sharpe_like_1y = db.Column(db.Float, nullable=True)
    raw_result = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    """Stores contact form submissions."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# PORTFOLIO CONFIGURATION  # Section title for all predefined portfolio scenarios
# ============================================================  

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


def get_portfolio_display_name(portfolio_dict):
    """Return the best available display name from a portfolio dictionary."""
    identity = portfolio_dict.get("identity", {})
    return identity.get("name") or identity.get("company_name") or portfolio_dict.get("client_id", "Unknown Portfolio")


def make_profile_data(name, client_type, risk_profile, objective, currency, benchmark_ticker, max_weight):
    """Build a JSON profile for a newly created portfolio from form dropdowns."""
    is_company = client_type == "Corporate / Family Office"
    identity = (
        {
            "company_name": name,
            "residency": "To be confirmed",
            "ownership": client_type,
            "signatories": ["To be confirmed"],
        }
        if is_company
        else {
            "name": name,
            "nationality": "To be confirmed",
            "tax_residency": "To be confirmed",
            "identification": "To be confirmed",
        }
    )

    return {
        "identity": identity,
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


def seed_default_portfolios():
    """Insert the original default portfolio scenarios if the database is empty."""
    if Portfolio.query.first():
        return

    for key, profile in PORTFOLIOS.items():
        portfolio = Portfolio(
            key=key,
            client_id=profile["client_id"],
            display_name=get_portfolio_display_name(profile),
            benchmark_ticker=profile.get("ticker", "SPY"),
            portfolio_value=float(profile.get("portfolio_value", 0)),
            max_weight=float(profile.get("max_weight", 10)),
            profile_data=profile,
        )
        db.session.add(portfolio)

    db.session.commit()


def get_portfolio_choices():
    """Return portfolio dropdown choices from the database."""
    return [
        {"key": p.key, "name": p.display_name, "id": p.id}
        for p in Portfolio.query.order_by(Portfolio.display_name).all()
    ]


def get_portfolio_by_key(key):
    """Find a portfolio by its unique key."""
    return Portfolio.query.filter_by(key=key).first()


def safe_div(a, b):
    """Divide safely and avoid zero-division errors."""
    return a / b if b not in (0, 0.0, None) else 0.0


def parse_weight_to_decimal(weight_text):
    """Convert text such as '6%' or '1-2%' into decimal weight."""
    if not weight_text:
        return 0.0

    numbers = re.findall(r"\d+\.?\d*", str(weight_text))
    if not numbers:
        return 0.0

    values = [float(num) for num in numbers]
    if len(values) == 1:
        return values[0] / 100.0

    return (sum(values) / len(values)) / 100.0


def get_effective_max_weight(portfolio):
    """Return the strictest maximum weight available for a portfolio."""
    limits = [float(portfolio.max_weight)] if portfolio.max_weight is not None else []
    profile = portfolio.profile_data or {}
    constraints = profile.get("constraints", {})

    for field in ["max_stock_weight_percent", "max_asset_weight_percent", "max_issuer_weight_percent", "max_position_weight_percent"]:
        if constraints.get(field) is not None:
            try:
                limits.append(float(constraints[field]))
            except (TypeError, ValueError):
                pass

    return min(limits) if limits else None


def calculate_portfolio_summary(holdings):
    """Calculate current portfolio holding summary metrics."""
    if not holdings:
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

    total_allocated = sum(h.weight_decimal or 0.0 for h in holdings)
    betas = [h.beta for h in holdings if h.beta is not None]
    scores = [h.score for h in holdings if h.score is not None]
    returns = [h.expected_return_1y for h in holdings if h.expected_return_1y is not None]
    vols = [h.volatility_1y for h in holdings if h.volatility_1y is not None]

    avg_score = round(sum(scores) / len(scores), 2) if scores else None
    avg_return = round((sum(returns) / len(returns)) * 100, 2) if returns else None
    avg_vol = round((sum(vols) / len(vols)) * 100, 2) if vols else None

    if avg_score is None:
        status = "Needs more analysis"
    elif avg_score >= 6:
        status = "Performing well"
    elif avg_score >= 3:
        status = "Mixed / monitor"
    else:
        status = "Weak / needs review"

    return {
        "position_count": len(holdings),
        "total_allocated_percent": round(total_allocated * 100, 2),
        "remaining_cash_percent": round(max(0.0, 1.0 - total_allocated) * 100, 2),
        "average_beta": round(sum(betas) / len(betas), 2) if betas else None,
        "average_score": avg_score,
        "average_expected_return": avg_return,
        "average_volatility": avg_vol,
        "status": status,
    }


def build_grouped_portfolio_payload():
    """Return all holdings grouped by portfolio for JavaScript display."""
    grouped = {}

    portfolios = Portfolio.query.order_by(Portfolio.display_name).all()
    for portfolio in portfolios:
        holdings = PortfolioHolding.query.filter_by(portfolio_id=portfolio.id).order_by(PortfolioHolding.weight_decimal.desc()).all()
        grouped[portfolio.key] = {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.display_name,
            "stocks": [h.to_dict() for h in holdings],
            "summary": calculate_portfolio_summary(holdings),
        }

    return grouped


def default_metrics(period_label):
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


def compute_metrics(ticker, period):
    """Download Yahoo Finance data and calculate expected return, volatility, and Sharpe-like ratio."""
    try:
        data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    except Exception:
        return default_metrics(period)

    if data is None or data.empty:
        return default_metrics(period)

    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)

    if "Close" not in data.columns:
        return default_metrics(period)

    close_prices = data["Close"].dropna()
    if close_prices.empty or len(close_prices) < 2:
        return default_metrics(period)

    returns = close_prices.pct_change().dropna()
    if returns.empty:
        return default_metrics(period)

    annualised_volatility = float(returns.std() * np.sqrt(252))
    annualised_expected_return = float(returns.mean() * 252)
    sharpe_like = safe_div(annualised_expected_return, annualised_volatility)

    return {
        "annualised_expected_return": annualised_expected_return,
        "annualised_volatility": annualised_volatility,
        "sharpe_like": sharpe_like,
        "latest_price": float(close_prices.iloc[-1]),
        "price_start_date": close_prices.index[0].strftime("%Y-%m-%d"),
        "price_end_date": close_prices.index[-1].strftime("%Y-%m-%d"),
        "price_observations": int(len(close_prices)),
        "return_start_date": returns.index[0].strftime("%Y-%m-%d"),
        "return_end_date": returns.index[-1].strftime("%Y-%m-%d"),
        "return_observations": int(len(returns)),
        "returns_series": returns,
        "period_label": period,
    }


def build_quarterly_forecast(latest_price, annualised_expected_return):
    """Build simple quarterly price forecast from annualised return."""
    adjusted_return = max(annualised_expected_return, -0.95)
    quarterly_return = (1 + adjusted_return) ** 0.25 - 1
    q1_price = latest_price * (1 + quarterly_return)
    q2_price = q1_price * (1 + quarterly_return)
    q3_price = q2_price * (1 + quarterly_return)
    q4_price = q3_price * (1 + quarterly_return)

    return {
        "quarterly_return": quarterly_return,
        "q1_expected_price": q1_price,
        "q2_expected_price": q2_price,
        "q3_expected_price": q3_price,
        "q4_expected_price": q4_price,
    }


def score_and_decide(expected_return, volatility, sharpe_like, beta):
    """Convert market metrics into a score, decision, and suggested weight."""
    score = 0

    if expected_return >= 0.02:
        score += 2
    if volatility <= 0.08:
        score += 3
    elif volatility <= 0.12:
        score += 1
    if sharpe_like > 0.6:
        score += 2
    elif sharpe_like > 0.3:
        score += 1
    if beta is not None:
        if beta <= 0.9:
            score += 2
        elif beta <= 1.1:
            score += 1

    if score >= 7:
        return {"score": score, "decision": "YES — high conviction", "recommended_weight": "6%", "tag": "High conviction"}
    if score >= 5:
        return {"score": score, "decision": "YES — core holding", "recommended_weight": "3.5%", "tag": "Core holding"}
    if score >= 3:
        return {"score": score, "decision": "YES — satellite", "recommended_weight": "3%", "tag": "Diversifier"}
    if score >= 1:
        return {"score": score, "decision": "LIMITED — high risk / exploratory", "recommended_weight": "1–2%", "tag": "Exploratory"}

    return {"score": score, "decision": "NO — hold as cash instead", "recommended_weight": "Cash (5%)", "tag": "Cash / Risk Control"}


def validate_portfolio_addition(portfolio, ticker, recommended_weight, sector, industry):
    """Allow any selected stock or ETF to be assigned to any portfolio.

    This version removes blocking validation rules. It still calculates the
    recommended weight as a decimal so the holding can be saved and used in
    portfolio performance calculations.

    Removed blocking checks:
    - maximum position weight
    - total allocation above 100%
    - equity restrictions
    - ESG/tobacco restrictions
    - currency warnings
    """
    weight_decimal = parse_weight_to_decimal(recommended_weight)

    return {
        "errors": [],
        "warnings": [],
        "weight_decimal": weight_decimal,
    }


def analyze_stock(ticker, benchmark_ticker, portfolio_key):
    """Analyse a stock or ETF and return JSON-friendly results."""
    metrics_1y = compute_metrics(ticker, "1y")
    metrics_3m = compute_metrics(ticker, "3mo")
    benchmark_metrics = compute_metrics(benchmark_ticker, "1y")

    beta = 0.0
    beta_observations = 0

    if metrics_1y["returns_series"] is not None and benchmark_metrics["returns_series"] is not None:
        stock_aligned, bench_aligned = metrics_1y["returns_series"].align(
            benchmark_metrics["returns_series"],
            join="inner",
        )
        beta_observations = int(len(stock_aligned))

        if len(stock_aligned) > 1 and bench_aligned.var() != 0:
            beta = float(stock_aligned.cov(bench_aligned) / bench_aligned.var())

    decision_pack = score_and_decide(
        expected_return=metrics_1y["annualised_expected_return"],
        volatility=metrics_1y["annualised_volatility"],
        sharpe_like=metrics_1y["sharpe_like"],
        beta=beta,
    )

    try:
        info = yf.Ticker(ticker).info or {}
        sector = info.get("sector") or info.get("category") or info.get("fundCategory") or "Unknown"
        industry = info.get("industry") or info.get("quoteType") or info.get("fundFamily") or "Unknown"
    except Exception:
        sector = "Unknown"
        industry = "Unknown"

    forecast_1y = build_quarterly_forecast(metrics_1y["latest_price"], metrics_1y["annualised_expected_return"])
    forecast_3m = build_quarterly_forecast(metrics_3m["latest_price"], metrics_3m["annualised_expected_return"])
    portfolio = get_portfolio_by_key(portfolio_key)

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





dashboard_cache = {"rows": None, "timestamp": 0}
DASHBOARD_CACHE_SECONDS = 300


def compute_metrics_from_batch(batch_data, ticker):
    """Calculate metrics for one ticker from batch-downloaded data."""
    try:
        if batch_data is None or batch_data.empty:
            return default_metrics("1y")

        if hasattr(batch_data.columns, "nlevels") and batch_data.columns.nlevels > 1:
            if ticker not in batch_data.columns.get_level_values(0):
                return default_metrics("1y")
            ticker_data = batch_data[ticker].copy()
        else:
            ticker_data = batch_data.copy()

        if "Close" not in ticker_data.columns:
            return default_metrics("1y")

        close_prices = ticker_data["Close"].dropna()
        if close_prices.empty or len(close_prices) < 2:
            return default_metrics("1y")

        returns = close_prices.pct_change().dropna()
        if returns.empty:
            return default_metrics("1y")

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
        return default_metrics("1y")


def build_market_rows():
    """Build dashboard table rows from the ticker universe."""
    dashboard_tickers = sorted({ticker for group in MASTER_TICKERS.values() for ticker in group})
    rows = []

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
        batch_data = None

    for ticker in dashboard_tickers:
        metrics_1y = compute_metrics_from_batch(batch_data, ticker)
        decision_pack = score_and_decide(
            expected_return=metrics_1y["annualised_expected_return"],
            volatility=metrics_1y["annualised_volatility"],
            sharpe_like=metrics_1y["sharpe_like"],
            beta=None,
        )

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
            "is_low_risk": metrics_1y["annualised_volatility"] <= 0.18 and decision_pack["decision"] != "NO — hold as cash instead",
            "is_high_conviction": decision_pack["decision"] == "YES — high conviction",
            "is_core_holding": decision_pack["decision"] == "YES — core holding",
            "is_satellite": decision_pack["decision"] == "YES — satellite",
            "is_exploratory": decision_pack["decision"] == "LIMITED — high risk / exploratory",
            "is_income_candidate": ticker in {"IEF", "SHY", "AGG", "BND", "TIP", "XLP", "XLV", "XLU"},
            "is_best_ranked": decision_pack["score"] >= 5 and metrics_1y["sharpe_like"] >= 0.3,
            "is_cash_candidate": decision_pack["decision"] == "NO — hold as cash instead",
        })

    rows.sort(key=lambda row: row["ranking_score"], reverse=True)
    return rows


def get_cached_market_rows():
    """Cache dashboard rows briefly to avoid repeated downloads."""
    now = time.time()
    if dashboard_cache["rows"] is None or now - dashboard_cache["timestamp"] > DASHBOARD_CACHE_SECONDS:
        dashboard_cache["rows"] = build_market_rows()
        dashboard_cache["timestamp"] = now
    return dashboard_cache["rows"]


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

    rows.sort(key=lambda row: row["average_score"] if row["average_score"] is not None else -1, reverse=True)
    return rows


# ============================================================
# ROUTES: HTML PAGES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html", active_page="home")


@app.route("/portfolio_profiles", methods=["GET", "POST"])
def portfolio_profiles():
    if request.method == "POST":
        name = request.form.get("display_name", "").strip()
        client_type = request.form.get("client_type", "Individual")
        risk_profile = request.form.get("risk_profile", "Balanced")
        objective = request.form.get("objective", "Balanced growth")
        currency = request.form.get("currency", "EUR base, global exposure allowed")
        benchmark_ticker = request.form.get("benchmark_ticker", "ACWI").strip().upper()
        portfolio_value = float(request.form.get("portfolio_value") or 0)
        max_weight = float(request.form.get("max_weight") or 10)

        if not name:
            flash("Portfolio name is required.", "error")
            return redirect(url_for("portfolio_profiles"))

        key_base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "portfolio"
        key = key_base
        counter = 1
        while Portfolio.query.filter_by(key=key).first():
            counter += 1
            key = f"{key_base}_{counter}"

        profile_data = make_profile_data(
            name=name,
            client_type=client_type,
            risk_profile=risk_profile,
            objective=objective,
            currency=currency,
            benchmark_ticker=benchmark_ticker,
            max_weight=max_weight,
        )

        portfolio = Portfolio(
            key=key,
            client_id=f"custom_{key}",
            display_name=name,
            benchmark_ticker=benchmark_ticker,
            portfolio_value=portfolio_value,
            max_weight=max_weight,
            profile_data=profile_data,
        )

        db.session.add(portfolio)
        db.session.commit()

        flash("New portfolio profile saved to the database.", "success")
        return redirect(url_for("portfolio_profiles"))

    return render_template(
        "portfolio_profiles.html",
        active_page="portfolio_profiles",
        portfolios=Portfolio.query.order_by(Portfolio.id).all(),
    )


@app.route("/market_dashboard")
def market_dashboard():
    rows = get_cached_market_rows()
    return render_template(
        "market_dashboard.html",
        active_page="market_dashboard",
        rows=rows,
        portfolio_choices=get_portfolio_choices(),
    )


@app.route("/portfolio_performance")
def portfolio_performance():
    return render_template(
        "portfolio_performance.html",
        active_page="portfolio_performance",
        performance_rows=build_portfolio_performance_rows(),
        grouped_portfolios=build_grouped_portfolio_payload(),
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        message = ContactMessage(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            message=request.form.get("message", "").strip(),
        )
        db.session.add(message)
        db.session.commit()

        flash("Contact message saved to the database.", "success")
        return redirect(url_for("contact"))

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(10).all()
    return render_template("contact.html", active_page="contact", messages=messages)


# ============================================================
# ROUTES: JSON / API ENDPOINTS
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.form.get("ticker", "").strip().upper()
    portfolio_key = request.form.get("portfolio_key", "").strip()

    portfolio = get_portfolio_by_key(portfolio_key)
    if not portfolio:
        return jsonify({"error": "Invalid portfolio selected."}), 400

    if not ticker:
        return jsonify({"error": "Please select a ticker."}), 400

    try:
        result = analyze_stock(ticker, portfolio.benchmark_ticker, portfolio.key)

        record = AnalysisRecord(
            portfolio_id=portfolio.id,
            ticker=ticker,
            beta=result["beta"],
            score=result["score"],
            decision=result["decision"],
            expected_return_1y=result["one_year"]["annualised_expected_return"],
            volatility_1y=result["one_year"]["annualised_volatility"],
            sharpe_like_1y=result["one_year"]["sharpe_like"],
            raw_result=result,
        )
        db.session.add(record)
        db.session.commit()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/add-to-portfolio", methods=["POST"])
def add_to_portfolio():
    """Analyse a selected ticker and save or update it as a portfolio holding.

    This route is called from the Market Dashboard page by JavaScript.
    It returns JSON in both success and error cases so the page can show
    a useful message instead of a generic failure.
    """
    try:
        data = request.get_json(force=True)

        ticker = data.get("ticker", "").strip().upper()
        portfolio_key = data.get("portfolio_key", "").strip()
        portfolio = get_portfolio_by_key(portfolio_key)

        if not ticker or not portfolio:
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
            return jsonify({
                "error": validation["errors"],
                "warnings": validation["warnings"],
            }), 400

        holding = PortfolioHolding.query.filter_by(
            portfolio_id=portfolio.id,
            ticker=ticker,
        ).first()

        if not holding:
            now = datetime.utcnow()
            holding = PortfolioHolding(
                portfolio_id=portfolio.id,
                ticker=ticker,
                recommended_weight=analysis["recommended_weight"],
                weight_decimal=validation["weight_decimal"],
                decision=analysis["decision"],
                created_at=now,
                updated_at=now,
            )
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
        print("ADD TO PORTFOLIO ERROR:", e)
        return jsonify({"error": f"Could not save holding: {str(e)}"}), 500


@app.route("/portfolio-stocks")
def portfolio_stocks():
    return jsonify(build_grouped_portfolio_payload())


@app.route("/delete-holding/<int:holding_id>", methods=["DELETE"])
def delete_holding(holding_id):
    holding = PortfolioHolding.query.get_or_404(holding_id)
    ticker = holding.ticker
    portfolio_name = holding.portfolio.display_name

    db.session.delete(holding)
    db.session.commit()

    return jsonify({
        "message": f"{ticker} deleted from {portfolio_name}.",
        "portfolio": build_grouped_portfolio_payload(),
    })


# ============================================================
# DATABASE INITIALISATION
# ============================================================

with app.app_context():
    db.create_all()
    seed_default_portfolios()


if __name__ == "__main__":
    app.run(debug=True)
