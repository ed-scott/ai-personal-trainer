-- ============================================================================
-- AI Personal Trainer Stage 1 - Database and Role Setup
-- Snowflake Native Streamlit Application
-- Purpose: Create database, roles, warehouse, and foundational objects
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- Create Database and Schema
-- ============================================================================

CREATE DATABASE IF NOT EXISTS TRAINING_DB
  COMMENT = 'AI Personal Trainer app database - Stage 1: Workout & Meal Plan Generation';

CREATE SCHEMA IF NOT EXISTS TRAINING_DB.PUBLIC
  COMMENT = 'Default schema for personal trainer app objects (Stage 1)';

-- ============================================================================
-- Create Compute Warehouse
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS TRAINING_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = FALSE
  COMMENT = 'Warehouse for AI Personal Trainer Streamlit Native app';

-- ============================================================================
-- Create Roles and Assign Privileges
-- ============================================================================

CREATE ROLE IF NOT EXISTS TRAINING_APP_ROLE
  COMMENT = 'Role for AI Personal Trainer app users';

CREATE ROLE IF NOT EXISTS TRAINING_APP_ADMIN
  COMMENT = 'Admin role for AI Personal Trainer app';

-- Grant role hierarchy
GRANT ROLE TRAINING_APP_ADMIN TO ROLE SYSADMIN;

-- Grant warehouse privileges
GRANT USAGE ON WAREHOUSE TRAINING_WH TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON WAREHOUSE TRAINING_WH TO ROLE TRAINING_APP_ADMIN;
GRANT OPERATE ON WAREHOUSE TRAINING_WH TO ROLE TRAINING_APP_ADMIN;

-- Grant database privileges
GRANT OWNERSHIP ON DATABASE TRAINING_DB TO ROLE TRAINING_APP_ADMIN;
GRANT OWNERSHIP ON SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ADMIN;

GRANT USAGE ON DATABASE TRAINING_DB TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;

-- Grant future object privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON ALL FUNCTIONS IN SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;

-- Grant Cortex privileges
GRANT USAGE ON DATABASE SNOWFLAKE TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.ML TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Create Application Logging Table
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;
USE WAREHOUSE TRAINING_WH;

CREATE TABLE IF NOT EXISTS app_logs (
  log_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  log_timestamp TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  event_type VARCHAR(100) NOT NULL COMMENT 'workout_generated, meal_plan_generated, client_created, etc.',
  severity VARCHAR(20) DEFAULT 'INFO' COMMENT 'INFO, WARNING, ERROR',
  client_id VARCHAR(36),
  message VARCHAR(2000),
  context VARIANT COMMENT 'Additional context as JSON',
  PRIMARY KEY (log_id)
)
COMMENT = 'Application logs for monitoring and debugging';

GRANT SELECT, INSERT ON app_logs TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Verification
-- ============================================================================

SHOW DATABASES LIKE 'TRAINING_DB';
SHOW WAREHOUSES LIKE 'TRAINING_WH';
SHOW ROLES LIKE 'TRAINING_APP%';
SHOW TABLES IN TRAINING_DB.PUBLIC;
