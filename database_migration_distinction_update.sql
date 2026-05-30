-- ============================================================
-- Distinction Update Migration
-- Adds timestamp defaults required by the updated SQLAlchemy models.
-- Run this once in Neon SQL Editor before deploying updated app.py.
-- ============================================================

ALTER TABLE portfolio
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

ALTER TABLE portfolio
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

UPDATE portfolio
SET created_at = NOW()
WHERE created_at IS NULL;

UPDATE portfolio
SET updated_at = NOW()
WHERE updated_at IS NULL;

ALTER TABLE portfolio_holding
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE portfolio_holding
ALTER COLUMN updated_at SET DEFAULT NOW();

UPDATE portfolio_holding
SET updated_at = NOW()
WHERE updated_at IS NULL;

ALTER TABLE analysis_record
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE analysis_record
ALTER COLUMN updated_at SET DEFAULT NOW();

UPDATE analysis_record
SET updated_at = NOW()
WHERE updated_at IS NULL;

ALTER TABLE contact_message
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE contact_message
ALTER COLUMN updated_at SET DEFAULT NOW();

UPDATE contact_message
SET updated_at = NOW()
WHERE updated_at IS NULL;
