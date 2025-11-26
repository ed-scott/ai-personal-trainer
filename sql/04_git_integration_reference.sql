-- ============================================================================
-- Git Integration Configuration Reference
-- Purpose: Show available Git setup options and commands
-- ============================================================================

-- ============================================================================
-- OPTION 1: Create Git Secret with Password Authentication
-- ============================================================================

-- GitHub Personal Access Token (PAT) Method
CREATE SECRET IF NOT EXISTS ai_personal_trainer_git_secret
  TYPE = 'PASSWORD'
  USERNAME = 'github'
  PASSWORD = 'ghp_your_token_here'  -- Replace with actual GitHub PAT
  COMMENT = 'Git credentials for AI Personal Trainer repository'
;

-- ============================================================================
-- OPTION 2: Create Git Repository Reference
-- ============================================================================

-- Using HTTPS with Secret-based Authentication
CREATE GIT REPOSITORY IF NOT EXISTS ai_personal_trainer_repo
  API_PROVIDER = 'GITHUB'
  GIT_CREDENTIALS_SECRET = ai_personal_trainer_git_secret
  ORIGIN = 'https://github.com/ed-scott/ai-personal-trainer.git'  -- Replace with your repo
  COMMENT = 'Git repository for AI Personal Trainer Streamlit application'
;

-- ============================================================================
-- OPTION 3: Create Streamlit App from Git Repository
-- ============================================================================

-- Method A: Using Git Repository (Recommended)
CREATE STREAMLIT IF NOT EXISTS training_db.public.ai_personal_trainer
  FROM @ai_personal_trainer_repo/branches/main/streamlit_app
  MAIN_FILE = 'app.py'
  QUERY_WAREHOUSE = training_wh
  TITLE = 'AI Personal Trainer - Stage 1'
  COMMENT = 'Personalized Workout and Meal Plan Generation with Cortex Prompt Complete'
;

-- Method B: Using Internal Stage (Alternative - Legacy)
-- CREATE STREAMLIT IF NOT EXISTS training_db.public.ai_personal_trainer
--   ROOT_LOCATION = '@training_db.public.streamlit_app_stage'
--   MAIN_FILE = '/app.py'
--   QUERY_WAREHOUSE = training_wh
--   TITLE = 'AI Personal Trainer - Stage 1'
--   COMMENT = 'Personalized Workout and Meal Plan Generation with Cortex Prompt Complete'
-- ;

-- ============================================================================
-- Privilege Management
-- ============================================================================

-- Grant secret access to roles
GRANT READ ON SECRET ai_personal_trainer_git_secret 
  TO ROLE TRAINING_APP_ROLE;
GRANT READ ON SECRET ai_personal_trainer_git_secret 
  TO ROLE TRAINING_APP_ADMIN;

-- Grant Git repository access to roles
GRANT USAGE ON GIT REPOSITORY ai_personal_trainer_repo 
  TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON GIT REPOSITORY ai_personal_trainer_repo 
  TO ROLE TRAINING_APP_ADMIN;

-- Grant Streamlit app access to roles
GRANT USAGE ON STREAMLIT training_db.public.ai_personal_trainer 
  TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON STREAMLIT training_db.public.ai_personal_trainer 
  TO ROLE TRAINING_APP_ADMIN;

-- ============================================================================
-- Update/Modify Operations
-- ============================================================================

-- Update Git secret with new token (if expired/rotated)
-- ALTER SECRET ai_personal_trainer_git_secret 
--   SET PASSWORD = 'new_github_pat_here';

-- Update Git repository URL
-- ALTER GIT REPOSITORY ai_personal_trainer_repo 
--   SET ORIGIN = 'https://github.com/your-username/your-repo.git';

-- Update Streamlit app to use different main file (if restructured)
-- ALTER STREAMLIT training_db.public.ai_personal_trainer 
--   SET MAIN_FILE = '/streamlit_app/app.py';

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- List all secrets in the database
SELECT 
  SECRET_NAME,
  SECRET_TYPE,
  CREATED_ON,
  UPDATED_ON
FROM INFORMATION_SCHEMA.SECRETS
WHERE SCHEMA_NAME = 'PUBLIC'
ORDER BY CREATED_ON DESC;

-- List all Git repositories
SELECT 
  REPOSITORY_NAME,
  REPOSITORY_URL,
  API_PROVIDER,
  CREATED_ON,
  UPDATED_ON
FROM INFORMATION_SCHEMA.GIT_REPOSITORIES
WHERE SCHEMA_NAME = 'PUBLIC'
ORDER BY CREATED_ON DESC;

-- Alternative: SHOW commands
SHOW SECRETS IN TRAINING_DB.PUBLIC;
SHOW GIT REPOSITORIES IN TRAINING_DB.PUBLIC;

-- Describe Git repository details
DESC GIT REPOSITORY ai_personal_trainer_repo;

-- List Streamlit apps
SHOW STREAMLITS IN TRAINING_DB.PUBLIC;

-- Describe Streamlit app (shows source)
DESC STREAMLIT training_db.public.ai_personal_trainer;

-- ============================================================================
-- Troubleshooting Queries
-- ============================================================================

-- Check if Git integration is enabled in your account
SELECT * FROM TABLE(INFORMATION_SCHEMA.DATABASE_USAGE_METRICS()) 
WHERE METRIC_NAME LIKE '%GIT%';

-- Verify role has necessary privileges
SHOW GRANTS ON SECRET ai_personal_trainer_git_secret 
TO ROLE TRAINING_APP_ROLE;

SHOW GRANTS ON GIT REPOSITORY ai_personal_trainer_repo 
TO ROLE TRAINING_APP_ROLE;

-- List all objects and their ownership
SELECT 
  OBJECT_SCHEMA,
  OBJECT_NAME,
  OBJECT_TYPE,
  OWNER
FROM INFORMATION_SCHEMA.OBJECTS
WHERE OBJECT_SCHEMA = 'PUBLIC'
ORDER BY OBJECT_TYPE, OBJECT_NAME;

-- ============================================================================
-- Cleanup (Optional - Use with Caution)
-- ============================================================================

-- Drop Streamlit app
-- DROP STREAMLIT IF EXISTS training_db.public.ai_personal_trainer;

-- Drop Git repository
-- DROP GIT REPOSITORY IF EXISTS ai_personal_trainer_repo;

-- Drop Git secret
-- DROP SECRET IF EXISTS ai_personal_trainer_git_secret;

-- ============================================================================
-- Reference Documentation
-- ============================================================================
/*
Snowflake Git Integration Documentation:
- CREATE GIT REPOSITORY: https://docs.snowflake.com/en/sql-reference/sql/create-git-repository
- CREATE SECRET: https://docs.snowflake.com/en/sql-reference/sql/create-secret
- CREATE STREAMLIT: https://docs.snowflake.com/en/sql-reference/sql/create-streamlit
- Git Integration Guide: https://docs.snowflake.com/en/user-guide/git-intro

GitHub Personal Access Tokens:
- Creating PAT: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Token Scopes: https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps
*/
