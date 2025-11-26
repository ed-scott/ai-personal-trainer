-- ============================================================================
-- AI Personal Trainer Stage 1 - Snowflake Native Streamlit Deployment
-- Purpose: Create the Streamlit app object in Snowflake using Git Repository
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ============================================================================
-- Create Git Secret for Authentication
-- ============================================================================

-- Create a secret to store Git credentials
-- NOTE: Replace PLACEHOLDER_TOKEN with your actual GitHub personal access token
CREATE SECRET IF NOT EXISTS ai_personal_trainer_git_secret
  TYPE = 'PASSWORD'
  USERNAME = 'github'
  PASSWORD = 'PLACEHOLDER_GITHUB_PAT_TOKEN'
  COMMENT = 'Git credentials for AI Personal Trainer Streamlit app repository'
;

-- Grant secret privileges
GRANT READ ON SECRET ai_personal_trainer_git_secret TO ROLE TRAINING_APP_ROLE;
GRANT READ ON SECRET ai_personal_trainer_git_secret TO ROLE TRAINING_APP_ADMIN;

-- ============================================================================
-- Create Git Repository Integration
-- ============================================================================

-- Create a Git repository reference for the Streamlit app
-- NOTE: Replace PLACEHOLDER_REPO_URL with your actual repository URL
CREATE GIT REPOSITORY IF NOT EXISTS ai_personal_trainer_repo
  API_PROVIDER = 'GITHUB'
  GIT_CREDENTIALS_SECRET = ai_personal_trainer_git_secret
  ORIGIN = 'https://github.com/ed-scott/ai-personal-trainer.git'
  COMMENT = 'Git repository for AI Personal Trainer Streamlit application'
;

-- Grant repository privileges
GRANT USAGE ON GIT REPOSITORY ai_personal_trainer_repo TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON GIT REPOSITORY ai_personal_trainer_repo TO ROLE TRAINING_APP_ADMIN;

-- ============================================================================
-- Create Internal Stage (Backup - Optional)
-- ============================================================================

-- Kept for reference/backup purposes
CREATE STAGE IF NOT EXISTS streamlit_app_stage
  DIRECTORY = (ENABLE = true)
  COMMENT = 'Backup internal stage for Streamlit app files'
;

-- Grant stage privileges
GRANT USAGE ON STAGE streamlit_app_stage TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON STAGE streamlit_app_stage TO ROLE TRAINING_APP_ADMIN;

-- ============================================================================
-- Create Snowflake Native Streamlit App (Git Repository Method)
-- ============================================================================

-- Use ACCOUNTADMIN to create the Streamlit object
-- This uses the Git repository instead of internal stage
CREATE STREAMLIT IF NOT EXISTS training_db.public.ai_personal_trainer
  FROM @ai_personal_trainer_repo/branches/main/streamlit_app
  MAIN_FILE = '/streamlit_app/app.py'
  QUERY_WAREHOUSE = training_wh
  TITLE = 'AI Personal Trainer - Stage 1'
  COMMENT = 'Personalized Workout and Meal Plan Generation with Cortex Prompt Complete'
;

-- ============================================================================
-- Grant Streamlit Permissions
-- ============================================================================

GRANT USAGE ON STREAMLIT training_db.public.ai_personal_trainer TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON STREAMLIT training_db.public.ai_personal_trainer TO ROLE TRAINING_APP_ADMIN;

-- ============================================================================
-- Verification
-- ============================================================================

SHOW SECRETS IN TRAINING_DB.PUBLIC;
SHOW GIT REPOSITORIES IN TRAINING_DB.PUBLIC;
SHOW STREAMLITS IN TRAINING_DB.PUBLIC;
SHOW STAGES IN TRAINING_DB.PUBLIC;

-- Verify Git repository reference
SELECT REPOSITORY_URL, CREATED_ON FROM INFORMATION_SCHEMA.GIT_REPOSITORIES 
WHERE REPOSITORY_NAME = 'AI_PERSONAL_TRAINER_REPO';
-- LIST @training_db.public.streamlit_app_stage;
