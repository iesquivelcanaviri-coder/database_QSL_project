# ============================================================
# IMPORTS
# ============================================================
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import yfinance as yf
import numpy as np
import re
import time
from config import Config
from models import db, Portfolio, PortfolioHolding, AnalysisRecord, ContactMessage

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
dashboard_cache = {"rows": None, "timestamp": 0}
DASHBOARD_CACHE_SECONDS = 300

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




def get_portfolio_display_name(portfolio):
    """Return the best display name from a portfolio dictionary."""
    identity = portfolio.get("identity", {})
    return identity.get("name") or identity.get("company_name") or portfolio.get("client_id", "Unknown Portfolio")

def seed_portfolios():
    """Create the default portfolio records if they do not already exist."""
    for key, profile in PORTFOLIOS.items():
        if Portfolio.query.filter_by(key=key).first():
            continue
        db.session.add(Portfolio(key=key, client_id=profile["client_id"], display_name=get_portfolio_display_name(profile), benchmark_ticker=profile["ticker"], portfolio_value=float(profile.get("portfolio_value", 0)), max_weight=float(profile.get("max_weight", 0)) if profile.get("max_weight") is not None else None, profile_data=profile))
    db.session.commit()

def initialise_database():
    """Create all database tables and seed default portfolio records."""
    db.create_all()
    seed_portfolios()

with app.app_context():
    initialise_database()

def get_portfolio_choices():
    """Build dropdown options from the Portfolio database table."""
    return [{"key": p.key, "name": p.display_name} for p in Portfolio.query.order_by(Portfolio.id).all()]

def get_portfolio_by_key(portfolio_key):
    """Fetch one Portfolio record by its unique key."""
    return Portfolio.query.filter_by(key=portfolio_key).first()

def safe_div(a, b):  # Defines a helper function for safe division so the app does not crash on divide-by-zero or None
    return a / b if b not in (0, 0.0, None) else 0.0  # Divides a by b only if b is valid; otherwise returns 0.0 as a safe fallback

def parse_weight_to_decimal(weight_text):  # Defines a helper function to convert text like "6%" or "1-2%" into decimal portfolio weights
    if not weight_text:  # Checks whether the input is empty, None, or otherwise falsey
        return 0.0  # Returns 0.0 because there is no usable weight to convert

    numbers = re.findall(r"\d+\.?\d*", str(weight_text))  # Uses regex to extract all numbers from the text after converting input to string
    if not numbers:  # Checks whether the regex found any numeric values
        return 0.0  # Returns 0.0 because the text did not contain a usable number

    values = [float(num) for num in numbers]  # Converts all extracted numeric strings into float values

    if len(values) == 1:  # Checks whether only one number was found, for example "6%"
        return values[0] / 100.0  # Converts the percentage into decimal form, e.g. 6 becomes 0.06

    return (sum(values) / len(values)) / 100.0  # If a range like "1-2%" exists, averages the numbers and converts result to decimal

def get_effective_max_weight(portfolio):  # Defines a helper function that finds the strictest position-size limit for a portfolio
    limits = []  # Creates an empty list to store all possible maximum-weight constraints found
    constraints = portfolio.get("constraints", {})  # Safely gets the portfolio constraints dictionary or an empty dict if missing

    if portfolio.get("max_weight") is not None:  # Checks whether the base top-level max_weight exists
        limits.append(float(portfolio["max_weight"]))  # Adds the top-level maximum weight to the list after converting it to float

    if constraints.get("max_stock_weight_percent") is not None:  # Checks whether a stock-specific max weight exists in constraints
        limits.append(float(constraints["max_stock_weight_percent"]))  # Adds that stock weight limit to the list

    if constraints.get("max_asset_weight_percent") is not None:  # Checks whether a general asset-level max weight exists
        limits.append(float(constraints["max_asset_weight_percent"]))  # Adds that asset-level limit to the list

    if constraints.get("max_issuer_weight_percent") is not None:  # Checks whether an issuer concentration limit exists
        limits.append(float(constraints["max_issuer_weight_percent"]))  # Adds that issuer limit to the list

    if limits:  # Checks whether at least one limit was collected
        return min(limits)  # Returns the smallest limit because the strictest limit is the effective one

    return None  # Returns None if no limits were found at all



def calculate_portfolio_summary(holdings):
    """Calculate summary statistics from database-backed holdings."""
    if not holdings:
        return {"position_count": 0, "total_allocated_percent": 0.0, "remaining_cash_percent": 100.0, "average_beta": None}
    total_allocated = sum(h.weight_decimal or 0.0 for h in holdings)
    betas = [h.beta for h in holdings if h.beta is not None]
    average_beta = round(sum(betas) / len(betas), 2) if betas else None
    return {"position_count": len(holdings), "total_allocated_percent": round(total_allocated * 100, 2), "remaining_cash_percent": round(max(0.0, 1.0 - total_allocated) * 100, 2), "average_beta": average_beta}

def build_grouped_portfolio_payload():
    """Read portfolios and holdings from the database for the JavaScript frontend."""
    grouped = {}
    for portfolio in Portfolio.query.order_by(Portfolio.id).all():
        holdings = sorted(portfolio.holdings, key=lambda h: h.weight_decimal or 0.0, reverse=True)
        grouped[portfolio.key] = {"portfolio_name": portfolio.display_name, "stocks": [h.to_dict() for h in holdings], "summary": calculate_portfolio_summary(holdings)}
    return grouped

def validate_portfolio_addition(portfolio_key, ticker, recommended_weight, sector, industry):
    """Validate a proposed holding against the selected portfolio mandate and database holdings."""
    portfolio_record = get_portfolio_by_key(portfolio_key)
    if not portfolio_record:
        return {"errors": ["Portfolio not found."], "warnings": [], "weight_decimal": 0.0}
    portfolio = portfolio_record.profile_data
    errors, warnings = [], []
    weight_decimal = parse_weight_to_decimal(recommended_weight)
    weight_percent = weight_decimal * 100
    max_weight_allowed = get_effective_max_weight(portfolio)
    if max_weight_allowed is not None and weight_percent > max_weight_allowed:
        errors.append(f"Recommended weight of {weight_percent:.2f}% exceeds the portfolio limit of {max_weight_allowed:.2f}%.")
    current_total = sum(h.weight_decimal or 0.0 for h in portfolio_record.holdings if h.ticker != ticker)
    projected_total = current_total + weight_decimal
    if projected_total > 1.0:
        errors.append(f"Projected total allocation would be {projected_total * 100:.2f}%, which exceeds 100%.")
    legal_rule = str(portfolio.get("constraints", {}).get("legal", "")).lower()
    if "prohibits equities" in legal_rule and ticker not in {"IEF", "SHY", "AGG", "BND", "TIP"}:
        errors.append("This mandate prohibits equities. Only fixed-income style instruments should be added.")
    esg_rule = str(portfolio.get("constraints", {}).get("esg", "")).lower()
    if "no tobacco" in esg_rule and ("tobacco" in str(sector).lower() or "tobacco" in str(industry).lower()):
        errors.append("This mandate excludes tobacco-related exposure.")
    currency_rule = portfolio.get("constraints", {}).get("currency")
    if currency_rule in ["EUR only", "CHF only"]:
        warnings.append(f"Manual currency review recommended because this mandate states {currency_rule}.")
    if portfolio.get("constraints", {}).get("esg") == "Required":
        warnings.append("Manual ESG review recommended before final approval.")
    return {"errors": errors, "warnings": warnings, "weight_decimal": weight_decimal}

def analyze_stock(ticker: str, benchmark_ticker: str, portfolio_key: str):
    metrics_1y = compute_metrics(ticker, "1y")
    metrics_3m = compute_metrics(ticker, "3mo")
    benchmark_metrics = compute_metrics(benchmark_ticker, "1y")

    beta = 0.0
    benchmark_start_date = benchmark_metrics.get("return_start_date", "N/A")
    benchmark_end_date = benchmark_metrics.get("return_end_date", "N/A")
    beta_observations = 0

    if metrics_1y["returns_series"] is not None and benchmark_metrics["returns_series"] is not None:
        stock_aligned, bench_aligned = metrics_1y["returns_series"].align(
            benchmark_metrics["returns_series"],
            join="inner"
        )

        beta_observations = int(len(stock_aligned))

        if len(stock_aligned) > 1 and bench_aligned.var() != 0:
            beta = float(stock_aligned.cov(bench_aligned) / bench_aligned.var())

    decision_pack = score_and_decide(
        expected_return=metrics_1y["annualised_expected_return"],
        volatility=metrics_1y["annualised_volatility"],
        sharpe_like=metrics_1y["sharpe_like"],
        beta=beta
    )

    try:
        info = yf.Ticker(ticker).info or {}
        sector = (
            info.get("sector")
            or info.get("category")
            or info.get("fundCategory")
            or "Unknown"
        )
        industry = (
            info.get("industry")
            or info.get("quoteType")
            or info.get("fundFamily")
            or "Unknown"
        )
    except Exception:
        sector = "Unknown"
        industry = "Unknown"

    forecast_1y = build_quarterly_forecast(
        latest_price=metrics_1y["latest_price"],
        annualised_expected_return=metrics_1y["annualised_expected_return"]
    )

    forecast_3m = build_quarterly_forecast(
        latest_price=metrics_3m["latest_price"],
        annualised_expected_return=metrics_3m["annualised_expected_return"]
    )

    portfolio = PORTFOLIOS[portfolio_key]

    return {
        "ticker": ticker.upper(),
        "portfolio_key": portfolio_key,
        "portfolio_name": get_portfolio_display_name(portfolio),
        "beta": beta,
        "score": decision_pack["score"],
        "decision": decision_pack["decision"],
        "recommended_weight": decision_pack["recommended_weight"],
        "sector": sector,
        "industry": industry,
        "tag": decision_pack["tag"],
        "benchmark_ticker": benchmark_ticker,
        "benchmark_start_date": benchmark_start_date,
        "benchmark_end_date": benchmark_end_date,
        "beta_observations": beta_observations,
        "one_year": {
            "annualised_expected_return": metrics_1y["annualised_expected_return"],
            "annualised_volatility": metrics_1y["annualised_volatility"],
            "sharpe_like": metrics_1y["sharpe_like"],
            "latest_price": metrics_1y["latest_price"],
            "price_start_date": metrics_1y["price_start_date"],
            "price_end_date": metrics_1y["price_end_date"],
            "price_observations": metrics_1y["price_observations"],
            "return_start_date": metrics_1y["return_start_date"],
            "return_end_date": metrics_1y["return_end_date"],
            "return_observations": metrics_1y["return_observations"],
            "forecast": {
                "quarterly_return": forecast_1y["quarterly_return"],
                "q1_expected_price": forecast_1y["q1_expected_price"],
                "q2_expected_price": forecast_1y["q2_expected_price"],
                "q3_expected_price": forecast_1y["q3_expected_price"],
                "q4_expected_price": forecast_1y["q4_expected_price"],
            }
        },
        "three_month": {
            "annualised_expected_return": metrics_3m["annualised_expected_return"],
            "annualised_volatility": metrics_3m["annualised_volatility"],
            "sharpe_like": metrics_3m["sharpe_like"],
            "latest_price": metrics_3m["latest_price"],
            "price_start_date": metrics_3m["price_start_date"],
            "price_end_date": metrics_3m["price_end_date"],
            "price_observations": metrics_3m["price_observations"],
            "return_start_date": metrics_3m["return_start_date"],
            "return_end_date": metrics_3m["return_end_date"],
            "return_observations": metrics_3m["return_observations"],
            "forecast": {
                "quarterly_return": forecast_3m["quarterly_return"],
                "q1_expected_price": forecast_3m["q1_expected_price"],
                "q2_expected_price": forecast_3m["q2_expected_price"],
                "q3_expected_price": forecast_3m["q3_expected_price"],
                "q4_expected_price": forecast_3m["q4_expected_price"],
            }
        }
    }


# ============================================================
# MARKET DASHBOARD SECTION
# Used by market_dashboard.html
# ============================================================
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



def build_market_rows():
    dashboard_tickers = sorted({
        ticker
        for group in MASTER_TICKERS.values()
        for ticker in group
    })

    rows = []

    try:
        batch_data = yf.download(
            tickers=dashboard_tickers,
            period="1y",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False
        )
    except Exception as e:
        print(f"Dashboard batch download failed: {e}")
        batch_data = None

    for ticker in dashboard_tickers:
        metrics_1y = compute_metrics_from_batch(batch_data, ticker)

        beta = None

        decision_pack = score_and_decide(
            expected_return=metrics_1y["annualised_expected_return"],
            volatility=metrics_1y["annualised_volatility"],
            sharpe_like=metrics_1y["sharpe_like"],
            beta=beta
        )

        expected_return_percent = round(metrics_1y["annualised_expected_return"] * 100, 2)
        volatility_percent = round(metrics_1y["annualised_volatility"] * 100, 2)
        sharpe_like_value = round(metrics_1y["sharpe_like"], 2)
        latest_price = round(metrics_1y["latest_price"], 2)

        ranking_score = (
            (metrics_1y["annualised_expected_return"] * 0.50)
            + (metrics_1y["sharpe_like"] * 0.30)
            - (metrics_1y["annualised_volatility"] * 0.20)
        )

        is_low_risk = (
            metrics_1y["annualised_volatility"] <= 0.18
            and decision_pack["decision"] != "NO — hold as cash instead"
        )

        is_high_conviction = (
            decision_pack["decision"] == "YES — high conviction"
            and decision_pack["score"] >= 7
        )

        is_income_candidate = ticker in {"IEF", "SHY", "AGG", "BND", "TIP", "XLP", "XLV", "XLU"}

        is_best_ranked = (
            decision_pack["score"] >= 5
            and metrics_1y["sharpe_like"] >= 0.3
        )

        is_core_holding = decision_pack["decision"] == "YES — core holding"
        is_satellite = decision_pack["decision"] == "YES — satellite"
        is_exploratory = decision_pack["decision"] == "LIMITED — high risk / exploratory"
        is_cash_candidate = decision_pack["decision"] == "NO — hold as cash instead"

        rows.append({
            "ticker": ticker,
            "latest_price": latest_price,
            "score": decision_pack["score"],
            "decision": decision_pack["decision"],
            "tag": decision_pack["tag"],
            "suggested_weight": decision_pack["recommended_weight"],
            "expected_return_percent": expected_return_percent,
            "volatility": volatility_percent,
            "sharpe_like": sharpe_like_value,
            "ranking_score": round(ranking_score, 3),
            "is_low_risk": is_low_risk,
            "is_high_conviction": is_high_conviction,
            "is_core_holding": is_core_holding,
            "is_satellite": is_satellite,
            "is_exploratory": is_exploratory,
            "is_income_candidate": is_income_candidate,
            "is_best_ranked": is_best_ranked,
            "is_cash_candidate": is_cash_candidate,
        })

    rows.sort(key=lambda row: row["ranking_score"], reverse=True)
    return rows



def get_cached_market_rows():
    now = time.time()

    if (
        dashboard_cache["rows"] is None
        or now - dashboard_cache["timestamp"] > DASHBOARD_CACHE_SECONDS
    ):
        dashboard_cache["rows"] = build_market_rows()
        dashboard_cache["timestamp"] = now

    return dashboard_cache["rows"]




@app.route("/")
def home():
    """Render the home page."""
    return render_template("index.html", active_page="home")

@app.route("/criteria")
def criteria():
    """Render the ticker analysis and portfolio holdings workflow page."""
    choices = get_portfolio_choices()
    default_key = choices[0]["key"] if choices else "scenario1"
    default_name = choices[0]["name"] if choices else "Unknown Portfolio"
    return render_template("criteria.html", active_page="criteria", portfolio_choices=choices, default_portfolio_key=default_key, default_portfolio_name=default_name)

@app.route("/market_dashboard")
def market_dashboard():
    """Render the market screening dashboard."""
    try:
        rows = get_cached_market_rows()
    except Exception as exc:
        print(f"Market dashboard route failed: {exc}")
        rows = []
    return render_template("market_dashboard.html", active_page="market_dashboard", rows=rows)

@app.route("/portfolio_profiles")
def portfolio_profiles():
    """Render portfolio profiles from the Portfolio database table."""
    return render_template("portfolio_profiles.html", active_page="portfolio_profiles", portfolios=Portfolio.query.order_by(Portfolio.id).all())

@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Create and read contact messages using the database."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please complete all contact form fields.", "error")
        else:
            db.session.add(ContactMessage(name=name, email=email, message=message))
            db.session.commit()
            flash("Contact message saved to the database.", "success")
            return redirect(url_for("contact"))
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    return render_template("contact.html", active_page="contact", messages=messages)

@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyse a ticker and create an AnalysisRecord in the database."""
    ticker = request.form.get("ticker", "").strip().upper()
    portfolio_key = request.form.get("portfolio_key", "")
    portfolio_record = get_portfolio_by_key(portfolio_key)
    if not portfolio_record:
        return jsonify({"error": "Invalid portfolio selected."}), 400
    if not ticker:
        return jsonify({"error": "Please select a ticker."}), 400
    try:
        result = analyze_stock(ticker, portfolio_record.benchmark_ticker, portfolio_key)
        one_year = result.get("one_year", {})
        db.session.add(AnalysisRecord(portfolio_id=portfolio_record.id, ticker=ticker, beta=result.get("beta"), score=result.get("score"), decision=result.get("decision"), expected_return_1y=one_year.get("annualised_expected_return"), volatility_1y=one_year.get("annualised_volatility"), sharpe_like_1y=one_year.get("sharpe_like"), raw_result=result))
        db.session.commit()
        return jsonify(result)
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Analysis failed: {str(exc)}"}), 500

@app.route("/add-to-portfolio", methods=["POST"])
def add_to_portfolio():
    """Create or update a PortfolioHolding record."""
    data = request.get_json(force=True)
    ticker = data.get("ticker")
    portfolio_record = get_portfolio_by_key(data.get("portfolio_key"))
    if not ticker or not portfolio_record:
        return jsonify({"error": "Invalid stock or portfolio."}), 400
    validation = validate_portfolio_addition(data.get("portfolio_key"), ticker, data.get("recommended_weight"), data.get("sector"), data.get("industry"))
    if validation["errors"]:
        return jsonify({"error": validation["errors"], "warnings": validation["warnings"]}), 400
    holding = PortfolioHolding.query.filter_by(portfolio_id=portfolio_record.id, ticker=ticker).first()
    if holding:
        message = f"{ticker} updated in portfolio."
    else:
        holding = PortfolioHolding(portfolio_id=portfolio_record.id, ticker=ticker)
        db.session.add(holding)
        message = f"{ticker} added to portfolio."
    holding.recommended_weight = data.get("recommended_weight")
    holding.weight_decimal = validation["weight_decimal"]
    holding.decision = data.get("decision")
    holding.tag = data.get("tag")
    holding.sector = data.get("sector")
    holding.industry = data.get("industry")
    holding.beta = data.get("beta")
    db.session.commit()
    return jsonify({"message": message, "warnings": validation["warnings"], "portfolio": build_grouped_portfolio_payload()})

@app.route("/portfolio-stocks")
def portfolio_stocks():
    """Read grouped holdings from the database."""
    return jsonify(build_grouped_portfolio_payload())

@app.route("/delete-holding/<int:holding_id>", methods=["DELETE"])
def delete_holding(holding_id):
    """Delete a saved PortfolioHolding record."""
    holding = PortfolioHolding.query.get_or_404(holding_id)
    ticker = holding.ticker
    db.session.delete(holding)
    db.session.commit()
    return jsonify({"message": f"{ticker} deleted from portfolio.", "portfolio": build_grouped_portfolio_payload()})

if __name__ == "__main__":
    app.run(debug=True)
