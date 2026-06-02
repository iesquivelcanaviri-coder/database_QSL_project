
-- ============================================================
-- DATABASE MIGRATION: TIMESTAMP COLUMN UPDATE
-- ============================================================
-- This file is a one-time PostgreSQL database migration script.
-- I used it because my Neon PostgreSQL tables had already been
-- created before I added the new timestamp fields to my
-- SQLAlchemy models in app.py.
--
-- The db.create_all() command in Flask creates missing tables,
-- but it does not automatically add new columns to tables that
-- already exist. I therefore used this SQL file in the Neon SQL
-- Editor to update the existing database structure safely.
--
-- The IF NOT EXISTS checks make the migration safer because the
-- script will not try to create a column again if it is already
-- present in the database.
--
-- I only need to run this migration once after updating app.py.
-- ============================================================


-- ============================================================
-- 1. PORTFOLIO TABLE TIMESTAMP UPDATE
-- ============================================================

-- ------------------------------------------------------------
-- Add created_at Column to the Portfolio Table
-- ------------------------------------------------------------
-- I added this column so the database can record when each
-- portfolio profile was originally created. This is useful when
-- reviewing client records and showing that the database keeps
-- an audit-style history of portfolio creation.

ALTER TABLE portfolio
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();


-- ------------------------------------------------------------
-- Add updated_at Column to the Portfolio Table
-- ------------------------------------------------------------
-- I added this column so the database can record when a saved
-- portfolio profile was last edited. This supports the Update
-- part of CRUD because portfolio details can be changed from
-- the Portfolio Profiles page.

ALTER TABLE portfolio
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();


-- ------------------------------------------------------------
-- Populate Missing created_at Values for Existing Portfolios
-- ------------------------------------------------------------
-- Some portfolio records were already stored in Neon before the
-- created_at column was added. This statement fills any missing
-- values with the current date and time so older records are not
-- left blank.

UPDATE portfolio
SET created_at = NOW()
WHERE created_at IS NULL;


-- ------------------------------------------------------------
-- Populate Missing updated_at Values for Existing Portfolios
-- ------------------------------------------------------------
-- This statement gives existing portfolio records an updated_at
-- value if they do not already have one. It keeps old and new
-- portfolio records consistent.

UPDATE portfolio
SET updated_at = NOW()
WHERE updated_at IS NULL;


-- ============================================================
-- 2. PORTFOLIO HOLDING TABLE TIMESTAMP UPDATE
-- ============================================================

-- ------------------------------------------------------------
-- Add updated_at Column to the PortfolioHolding Table
-- ------------------------------------------------------------
-- I added this column because a saved holding can be updated when
-- the same ticker is analysed and saved again for the same
-- portfolio. The timestamp helps record when the holding details
-- were most recently refreshed.

ALTER TABLE portfolio_holding
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();


-- ------------------------------------------------------------
-- Set Default Timestamp for Future Holding Updates
-- ------------------------------------------------------------
-- This statement ensures that newly created holding records
-- receive the current timestamp automatically if no value is
-- supplied directly by the Flask application.

ALTER TABLE portfolio_holding
ALTER COLUMN updated_at SET DEFAULT NOW();


-- ------------------------------------------------------------
-- Populate Missing updated_at Values for Existing Holdings
-- ------------------------------------------------------------
-- Existing holdings may have been stored before this new column
-- was added. This updates older records so the timestamp field is
-- not left empty.

UPDATE portfolio_holding
SET updated_at = NOW()
WHERE updated_at IS NULL;


-- ============================================================
-- 3. ANALYSIS RECORD TABLE TIMESTAMP UPDATE
-- ============================================================

-- ------------------------------------------------------------
-- Add updated_at Column to the AnalysisRecord Table
-- ------------------------------------------------------------
-- I added this column so each saved market-analysis result can
-- include a last-updated timestamp. This improves consistency
-- across the database models and supports clearer record keeping.

ALTER TABLE analysis_record
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();


-- ------------------------------------------------------------
-- Set Default Timestamp for Future Analysis Records
-- ------------------------------------------------------------
-- This ensures that future analysis records automatically receive
-- a timestamp when they are inserted into the PostgreSQL database.

ALTER TABLE analysis_record
ALTER COLUMN updated_at SET DEFAULT NOW();


-- ------------------------------------------------------------
-- Populate Missing updated_at Values for Existing Analysis Records
-- ------------------------------------------------------------
-- This fills missing timestamp values in analysis records that
-- existed before the database schema was updated.

UPDATE analysis_record
SET updated_at = NOW()
WHERE updated_at IS NULL;


-- ============================================================
-- 4. CONTACT MESSAGE TABLE TIMESTAMP UPDATE
-- ============================================================

-- ------------------------------------------------------------
-- Add updated_at Column to the ContactMessage Table
-- ------------------------------------------------------------
-- I added this column to keep the ContactMessage table aligned
-- with the updated SQLAlchemy model in app.py. It records the
-- latest update timestamp for each saved contact-form message.

ALTER TABLE contact_message
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();


-- ------------------------------------------------------------
-- Set Default Timestamp for Future Contact Messages
-- ------------------------------------------------------------
-- This ensures that newly saved contact messages receive a
-- timestamp automatically when they are inserted into the table.

ALTER TABLE contact_message
ALTER COLUMN updated_at SET DEFAULT NOW();


-- ------------------------------------------------------------
-- Populate Missing updated_at Values for Existing Contact Messages
-- ------------------------------------------------------------
-- This fills missing timestamps for contact messages that were
-- already stored before the column was added.

UPDATE contact_message
SET updated_at = NOW()
WHERE updated_at IS NULL;


-- ============================================================
-- END OF DATABASE MIGRATION
-- ============================================================
-- After running this script once in the Neon SQL Editor, the
-- PostgreSQL database structure matches the updated SQLAlchemy
-- models in app.py.
--
-- I kept this file in my GitHub repository to document how the
-- existing cloud database was upgraded safely without deleting
-- or recreating the stored records.
-- ============================================================

