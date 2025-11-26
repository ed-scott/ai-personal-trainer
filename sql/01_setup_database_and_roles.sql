-- ============================================================================
-- AI Personal Trainer - Snowflake Setup Script
-- Purpose: Create database, roles, warehouse, and foundational objects
-- ============================================================================

-- Use accountadmin role to set up database infrastructure
USE ROLE ACCOUNTADMIN;

-- Create the main database
CREATE DATABASE IF NOT EXISTS TRAINING_DB
  COMMENT = 'AI Personal Trainer app database - stores workouts, meals, weigh-ins, and more';

CREATE SCHEMA IF NOT EXISTS TRAINING_DB.PUBLIC
  COMMENT = 'Default schema for personal trainer app objects';

-- Create compute warehouse for the app
CREATE WAREHOUSE IF NOT EXISTS TRAINING_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  COMMENT = 'Warehouse for AI Personal Trainer Streamlit app';

-- ============================================================================
-- Create Roles and Assign Privileges
-- ============================================================================

-- Create the primary application role
CREATE ROLE IF NOT EXISTS TRAINING_APP_ROLE
  COMMENT = 'Role for AI Personal Trainer app users (trainers, clients, etc.)';

-- Create the admin role
CREATE ROLE IF NOT EXISTS TRAINING_APP_ADMIN
  COMMENT = 'Admin role for AI Personal Trainer app (manages objects, users)';

-- Grant TRAINING_APP_ADMIN to SYSADMIN (for better privilege inheritance)
GRANT ROLE TRAINING_APP_ADMIN TO ROLE SYSADMIN;

-- Grant warehouse usage to both roles
GRANT USAGE ON WAREHOUSE TRAINING_WH TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON WAREHOUSE TRAINING_WH TO ROLE TRAINING_APP_ADMIN;

-- Grant database privileges to TRAINING_APP_ADMIN (full control)
GRANT OWNERSHIP ON DATABASE TRAINING_DB TO ROLE TRAINING_APP_ADMIN;

-- Grant schema privileges to TRAINING_APP_ADMIN
GRANT OWNERSHIP ON SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ADMIN;

-- Grant database privileges to TRAINING_APP_ROLE (read/write access)
GRANT USAGE ON DATABASE TRAINING_DB TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;

-- Grant future object privileges for TRAINING_APP_ROLE
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;

-- Set default role and warehouse for the app role (if you create app user)
-- ALTER ROLE TRAINING_APP_ROLE SET DEFAULT_WAREHOUSE = 'TRAINING_WH';

-- ============================================================================
-- Create Internal Stages and File Formats
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;
USE WAREHOUSE TRAINING_WH;

-- Create internal stage for CSV/JSON ingestion
CREATE STAGE IF NOT EXISTS RAW_CSV_STAGE
  TYPE = INTERNAL
  COMMENT = 'Stage for uploading CSV/JSON data for bulk ingestion';

-- Create JSON file format
CREATE FILE FORMAT IF NOT EXISTS JSON_FORMAT
  TYPE = JSON
  COMPRESSION = AUTO
  COMMENT = 'File format for JSON data ingestion';

-- Grants for stages and file formats
GRANT USAGE ON STAGE RAW_CSV_STAGE TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON FILE FORMAT JSON_FORMAT TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Create Logging Table for Observability
-- ============================================================================

CREATE TABLE IF NOT EXISTS APP_LOGS (
  log_id VARCHAR(36),
  timestamp TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  level VARCHAR(20),
  source VARCHAR(255),
  message VARCHAR(4000),
  context VARIANT,
  PRIMARY KEY (log_id)
);

GRANT SELECT, INSERT ON APP_LOGS TO ROLE TRAINING_APP_ROLE;

ALTER TABLE APP_LOGS ADD SEARCH OPTIMIZATION ON EQUALITY(log_id), SUBSTRING(message);

COMMENT ON TABLE APP_LOGS IS 'Application logs for monitoring and debugging';

-- ============================================================================
-- Verification
-- ============================================================================

SHOW DATABASES LIKE 'TRAINING_DB';
SHOW ROLES LIKE 'TRAINING_APP%';
SHOW WAREHOUSES LIKE 'TRAINING_WH';
SHOW SCHEMAS IN DATABASE TRAINING_DB;
SHOW STAGES IN SCHEMA TRAINING_DB.PUBLIC;
