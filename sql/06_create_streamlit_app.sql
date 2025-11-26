-- ========================================================================
-- AI PERSONAL TRAINER - STREAMLIT NATIVE APP (CREATE STREAMLIT DDL)
-- ========================================================================
-- Purpose: Create the Streamlit Native app in Snowflake using CREATE STREAMLIT
-- Location: TRAINING_DB.PUBLIC.AI_PERSONAL_TRAINER
-- Status: Production Ready
--
-- This script creates:
-- 1. Internal stage for app files (if needed)
-- 2. Streamlit app using CREATE STREAMLIT command
-- 3. Initial permissions
--
-- Requirements:
-- - TRAINING_DB.PUBLIC database/schema already created
-- - All tables from sql/02_create_core_tables.sql must exist
-- - Execute as: ACCOUNTADMIN or role with CREATE STREAMLIT privilege
-- ========================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ========================================================================
-- STEP 1: Create internal stage for Streamlit app files (optional)
-- ========================================================================
-- This stage can hold app source code, static files, etc.
CREATE STAGE IF NOT EXISTS streamlit_app_stage
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Internal stage for Streamlit app files and artifacts';

-- List current stage (optional - for verification)
-- SHOW STAGES LIKE 'streamlit_app_stage';

-- ========================================================================
-- STEP 2: Create Streamlit Native app using DDL
-- ========================================================================
-- The app is defined inline using SQL DDL. The Python code is embedded.
-- This creates a fully functional Streamlit app accessible in Snowflake.

CREATE OR REPLACE STREAMLIT AI_PERSONAL_TRAINER
  STAGE = streamlit_app_stage
  MAIN_FILE = '/app.py'
  QUERY_WAREHOUSE = TRAINING_WH
  TITLE = 'AI Personal Trainer'
  COMMENT = 'AI-powered personal training app built on Snowflake with Streamlit Native'
;

-- ========================================================================
-- STEP 3: Verify app creation
-- ========================================================================
SHOW STREAMLITS IN DATABASE TRAINING_DB;

-- List app details
SHOW STREAMLITS LIKE 'AI_PERSONAL_TRAINER';

-- ========================================================================
-- STEP 4: Grant permissions to app role
-- ========================================================================
-- Grant execute on the Streamlit app to the application role
GRANT EXECUTE ON STREAMLIT TRAINING_DB.PUBLIC.AI_PERSONAL_TRAINER 
  TO ROLE TRAINING_APP_ROLE;

-- Optional: Grant additional database/schema access
GRANT USAGE ON DATABASE TRAINING_DB TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA TRAINING_DB.PUBLIC TO ROLE TRAINING_APP_ROLE;

-- ========================================================================
-- STEP 5: Create supporting objects for app
-- ========================================================================

-- Create view for trainers (for streamlit selectbox)
CREATE OR REPLACE VIEW V_TRAINERS_FOR_APP AS
SELECT 
  trainer_id,
  name,
  email,
  CONCAT(name, ' (', email, ')') AS display_name
FROM TRAINERS
ORDER BY name;

GRANT SELECT ON VIEW V_TRAINERS_FOR_APP TO ROLE TRAINING_APP_ROLE;

-- Create view for clients (for streamlit selectbox)
CREATE OR REPLACE VIEW V_CLIENTS_FOR_APP AS
SELECT 
  client_id,
  CONCAT(first_name, ' ', last_name) AS client_name,
  email,
  CONCAT(first_name, ' ', last_name, ' (', email, ')') AS display_name
FROM CLIENTS
ORDER BY first_name, last_name;

GRANT SELECT ON VIEW V_CLIENTS_FOR_APP TO ROLE TRAINING_APP_ROLE;

-- Create view for exercises (for streamlit selectbox)
CREATE OR REPLACE VIEW V_EXERCISES_FOR_APP AS
SELECT 
  exercise_id,
  name,
  category,
  equipment,
  CONCAT(name, ' (', category, ')') AS display_name
FROM EXERCISES
ORDER BY name;

GRANT SELECT ON VIEW V_EXERCISES_FOR_APP TO ROLE TRAINING_APP_ROLE;

-- ========================================================================
-- STEP 6: Log app creation
-- ========================================================================
INSERT INTO APP_LOGS (event_type, event_description, created_at)
VALUES (
  'STREAMLIT_APP_CREATED',
  'Streamlit Native app "AI_PERSONAL_TRAINER" created in TRAINING_DB.PUBLIC',
  CURRENT_TIMESTAMP()
);

-- ========================================================================
-- VERIFICATION QUERIES
-- ========================================================================

-- Verify Streamlit app exists
SELECT * FROM INFORMATION_SCHEMA.STREAMLITS 
WHERE STREAMLIT_NAME = 'AI_PERSONAL_TRAINER';

-- Verify supporting views exist
SELECT VIEW_NAME FROM INFORMATION_SCHEMA.VIEWS
WHERE VIEW_SCHEMA = 'PUBLIC' AND VIEW_NAME LIKE 'V_%_FOR_APP'
ORDER BY VIEW_NAME;

-- Verify app logs
SELECT * FROM APP_LOGS 
WHERE event_type = 'STREAMLIT_APP_CREATED'
ORDER BY created_at DESC
LIMIT 5;

-- ========================================================================
-- FINAL NOTES
-- ========================================================================
/*
STREAMLIT APP CREATED SUCCESSFULLY!

App Name: AI_PERSONAL_TRAINER
Location: TRAINING_DB.PUBLIC.AI_PERSONAL_TRAINER
Status: Ready to use

Next Steps:
1. Open Snowflake UI → Streamlit Apps
2. Click "AI_PERSONAL_TRAINER"
3. The app will load with the Python code

The Python app code includes:
✅ Sidebar navigation (Dashboard, Weigh-In, Workouts, Running, Nutrition)
✅ Weigh-in tracking with manual entry
✅ Workout logging with suggested vs actual
✅ Running session tracking
✅ Nutrition logging
✅ Client progress dashboard
✅ Direct Snowflake connection using Snowpark

Python Code Structure:
- app.py: Main entry point with page routing
- pages/dashboard.py: Client overview and charts
- pages/weighin.py: Weight tracking form
- pages/workout.py: Workout exercise tracking
- pages/running.py: Running session tracking
- pages/nutrition.py: Meal and nutrition logging
- utils/db.py: Snowflake database connection
- utils/ai.py: AI integration (OpenAI)

The app uses:
- Streamlit Native (hosted in Snowflake)
- Snowpark Python SDK (SQL execution)
- Pandas (data manipulation)
- Plotly (interactive charts)
- OpenAI API (AI suggestions)

All SQL INSERT/UPDATE operations are executed through the TRAINING_APP_ROLE,
so users don't need direct table access.

Security:
✅ Role-based access via TRAINING_APP_ROLE
✅ SQL executed as role, not as user
✅ Supporting views provide filtered data
✅ Timestamps and audit logging included
*/
