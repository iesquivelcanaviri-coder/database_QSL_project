"""
I use this file to define my database 'Models.' 
Think of these classes like blueprints for tables in my database. 
Each class is a table, and each variable inside is a column where I store 
specific data like stock tickers, client names, or analysis results.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# I initialize the database object here so I can use it throughout the app
db = SQLAlchemy()

class Portfolio(db.Model):
    """I use this table to store the high-level details of a client's portfolio mandate."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    client_id = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    benchmark_ticker = db.Column(db.String(20), nullable=False)
    portfolio_value = db.Column(db.Float, nullable=False, default=0.0)
    max_weight = db.Column(db.Float, nullable=True)
    # I use JSON here to store a flexible blob of profile data without needing 50 columns
    profile_data = db.Column(db.JSON, nullable=False)
    
    # RELATIONS: These aren't actual columns in the DB, but they tell SQLAlchemy 
    # how to 'look up' connected data. 
    # If I delete a portfolio, 'delete-orphan' makes sure I also delete its holdings automatically.
    holdings = db.relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan", lazy=True)
    analysis_records = db.relationship("AnalysisRecord", back_populates="portfolio", cascade="all, delete-orphan", lazy=True)

class PortfolioHolding(db.Model):
    """I use this to keep track of every stock/security I actually add to a portfolio."""
    id = db.Column(db.Integer, primary_key=True)
    # This links this holding back to a specific Portfolio ID (Foreign Key)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    recommended_weight = db.Column(db.String(30), nullable=False)
    weight_decimal = db.Column(db.Float, nullable=False, default=0.0)
    decision = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(100), nullable=True)
    sector = db.Column(db.String(150), nullable=True)
    industry = db.Column(db.String(150), nullable=True)
    beta = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    portfolio = db.relationship("Portfolio", back_populates="holdings")

    # This is a rule I set: I can't have the same stock ticker twice in the same portfolio ID.
    # It forces an update instead of a duplicate entry.
    __table_args__ = (db.UniqueConstraint("portfolio_id", "ticker", name="uq_portfolio_ticker"),)

    def to_dict(self):
        """I use this helper to turn database objects into JSON so my JavaScript can read them easily."""
        return {
            "id": self.id, 
            "ticker": self.ticker, 
            "recommended_weight": self.recommended_weight, 
            "weight_decimal": self.weight_decimal, 
            "decision": self.decision, 
            "tag": self.tag, 
            "sector": self.sector, 
            "industry": self.industry, 
            "beta": self.beta
        }

class AnalysisRecord(db.Model):
    """I use this to save every analysis I perform so I have a history of the results."""
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    beta = db.Column(db.Float, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    decision = db.Column(db.String(100), nullable=True)
    expected_return_1y = db.Column(db.Float, nullable=True)
    volatility_1y = db.Column(db.Float, nullable=True)
    sharpe_like_1y = db.Column(db.Float, nullable=True)
    raw_result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    portfolio = db.relationship("Portfolio", back_populates="analysis_records")

class ContactMessage(db.Model):
    """I use this simple table to store messages sent from the Contact Us page."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)