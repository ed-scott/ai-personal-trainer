# AI Personal Trainer - Stage 1 Deployment Guide

## Overview

This is a **Snowflake Native Streamlit Application** for **Stage 1: Personalized Workout and Meal Plan Generation** using **Cortex Prompt Complete**.

**Key Features:**
- ✅ Client profile management
- ✅ AI-powered workout generation (using Cortex)
- ✅ AI-powered meal plan generation (using Cortex)
- ✅ Weight tracking and body measurements
- ✅ Full Snowflake data integration

---

## Prerequisites

1. **Snowflake Account** with:
   - ACCOUNTADMIN role access
   - Cortex enabled (available in most modern Snowflake accounts)
   - SQL editing capabilities

2. **Required Snowflake Features:**
   - Snowflake Native Streamlit (available in most accounts)
   - Cortex Prompt Complete API access
   - Internal stages enabled

3. **Local Development (Optional):**
   - Python 3.9+
   - Streamlit CLI: `pip install streamlit`
   - Snowflake Snowpark: `pip install snowflake-snowpark-python`

---

## Deployment Steps

### Step 1: Execute SQL Setup Scripts

Execute the SQL scripts in order in your Snowflake Web UI or SnowSQL:

#### 1a. Setup Database, Warehouse, and Roles
```bash
# File: sql/01_stage1_setup.sql
```

**What it does:**
- Creates `TRAINING_DB` database
- Creates `TRAINING_WH` warehouse (XSMALL)
- Creates `TRAINING_APP_ROLE` and `TRAINING_APP_ADMIN` roles
- Grants necessary privileges
- Creates `app_logs` table

**Verification:**
```sql
SHOW DATABASES LIKE 'TRAINING_DB';
SHOW WAREHOUSES LIKE 'TRAINING_WH';
SHOW ROLES LIKE 'TRAINING_APP%';
```

#### 1b. Create Core Tables
```bash
# File: sql/02_stage1_create_tables.sql
```

**What it does:**
- Creates 7 core tables:
  - `clients` - Client profiles
  - `weigh_ins` - Weight tracking
  - `body_measurements` - Measurements tracking
  - `exercises_library` - Exercise reference
  - `generated_workouts` - AI-generated workouts
  - `recipes` - Recipe library
  - `meal_plans` - AI-generated meal plans

**Verification:**
```sql
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_CATALOG = 'TRAINING_DB'
ORDER BY TABLE_NAME;
```

Expected output: 8 tables (7 above + 1 app_logs)

#### 1c. Create Streamlit Stage and App
```bash
# File: sql/03_stage1_create_streamlit.sql
```

**What it does:**
- Creates `streamlit_app_stage` internal stage
- Creates Snowflake Native Streamlit app
- Grants permissions

**Verification:**
```sql
SHOW STREAMLITS IN TRAINING_DB.PUBLIC;
SHOW STAGES IN TRAINING_DB.PUBLIC;
```

---

### Step 2: Upload Streamlit App Files to Stage

You need to upload 3 files to the `streamlit_app_stage`:

#### Files to Upload
- `streamlit_app/app.py` (main application)
- `streamlit_app/config.py` (configuration module)
- `streamlit_app/requirements.txt` (dependencies)

#### Upload Methods

**Option A: Using Snowflake WebUI (Easiest)**
1. Snowflake UI → Data → TRAINING_DB → PUBLIC → Stages
2. Click `streamlit_app_stage`
3. Click "Upload Files" button
4. Select and upload the 3 files
5. Verify with: `LIST @streamlit_app_stage;`

**Option B: Using SnowSQL CLI**
```bash
snowsql -a <account_id> -u <username>

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

PUT file:///path/to/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///path/to/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///path/to/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;

LIST @streamlit_app_stage;
```

**Option C: Using Python/Snowpark**
```python
from snowflake.snowpark import Session

session = Session.builder.configs(connection_params).create()

session.file.put(
    "/path/to/streamlit_app/app.py",
    "@TRAINING_DB.PUBLIC.streamlit_app_stage/",
    auto_compress=False,
    overwrite=True
)
# Repeat for config.py and requirements.txt
```

#### Verification
```sql
LIST @streamlit_app_stage;
-- Should show:
-- app.py
-- config.py  
-- requirements.txt
```

---

### Step 3: Configure Cortex Privileges (Important!)

Grant Cortex privileges to enable AI generation:

```sql
USE ROLE ACCOUNTADMIN;

-- Grant Cortex privileges
GRANT USAGE ON DATABASE SNOWFLAKE TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.ML TO ROLE TRAINING_APP_ROLE;
```

---

### Step 4: Access the Streamlit App

#### In Snowflake Web UI
1. Go to **Projects** → **Streamlit Apps**
2. Click **ai_personal_trainer**
3. The app will load in your browser

#### Or Direct URL
```
https://<account_id>.snowflakecomputing.com/projects/ai_personal_trainer
```

---

## Testing the Application

### Test 1: Create a Client

1. Navigate to **Home** page
2. Fill in the "Create New Client" form:
   - Name: "Test Client"
   - Age: 30
   - Gender: Male
   - Weight: 75 kg
   - Height: 180 cm
   - Fitness Level: Intermediate
   - Goals: Muscle Gain
   - Equipment: Dumbbells
   - Days/week: 4
   - Duration: 60 min
3. Click "Create Client"
4. Verify success message and client ID

**Verification in SQL:**
```sql
SELECT * FROM TRAINING_DB.PUBLIC.clients ORDER BY created_at DESC LIMIT 1;
```

### Test 2: Generate a Workout

1. Navigate to **Workout Generator**
2. Select the test client
3. Leave Week=1, Day=1
4. Click "Generate Workout with AI"
5. Wait for Cortex to generate (30-60 seconds)
6. Review generated workout
7. Click "Save Workout to Database"

**Verification in SQL:**
```sql
SELECT * FROM TRAINING_DB.PUBLIC.generated_workouts ORDER BY generation_date DESC LIMIT 1;
```

### Test 3: Generate a Meal Plan

1. Navigate to **Meal Plan Generator**
2. Select the test client
3. Click "Generate Meal Plan with AI"
4. Wait for Cortex to generate (30-60 seconds)
5. Review generated meal plan
6. Click "Save Meal Plan to Database"

**Verification in SQL:**
```sql
SELECT * FROM TRAINING_DB.PUBLIC.meal_plans ORDER BY generation_date DESC LIMIT 1;
```

### Test 4: Record Weight Entry

1. Navigate to **Weight & Measurements Tracking**
2. Select test client
3. Fill in "Record Weigh-in" tab:
   - Date: Today
   - Weight: 75.5 kg
   - Body Fat: 20%
4. Click "Record Weigh-in"
5. Check "Weight History" tab to see chart and data

**Verification in SQL:**
```sql
SELECT * FROM TRAINING_DB.PUBLIC.weigh_ins WHERE client_id = '<client_id>' ORDER BY recorded_at DESC;
```

### Test 5: Application Logging

All events are logged to `app_logs` table:

```sql
SELECT event_type, severity, message, log_timestamp 
FROM TRAINING_DB.PUBLIC.app_logs 
ORDER BY log_timestamp DESC 
LIMIT 10;
```

Expected events:
- `client_created`
- `workout_generated`
- `meal_plan_generated`
- `weigh_in_recorded`

---

## Syntax Validation

All SQL syntax has been validated against [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference).

### Key SQL Features Used:

✅ **CREATE ROLE** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-role.html)
✅ **CREATE DATABASE** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-database.html)
✅ **CREATE WAREHOUSE** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-warehouse.html)
✅ **CREATE TABLE** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-table.html)
✅ **DEFAULT VALUES** - UUID_STRING(), CURRENT_TIMESTAMP()
✅ **CONSTRAINTS** - PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL
✅ **CREATE STAGE** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-stage.html)
✅ **CREATE STREAMLIT** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-streamlit.html)
✅ **GRANT/REVOKE** - [Documentation](https://docs.snowflake.com/en/sql-reference/sql/grant-privilege.html)
✅ **SHOW COMMANDS** - SHOW TABLES, SHOW ROLES, SHOW STREAMLITS

---

## Python/Streamlit Syntax Validation

### Snowpark Usage:
✅ `Session.builder.configs()` - Correct connection pattern
✅ `session.sql()` - SQL execution
✅ `.to_pandas()` - DataFrame conversion
✅ `@st.cache_resource` - Resource caching

### Streamlit API Usage:
✅ `st.set_page_config()` - Page configuration
✅ `st.markdown()` - Markdown rendering
✅ `st.columns()` - Layout management
✅ `st.form()` - Form submission
✅ `st.tabs()` - Tab navigation
✅ `st.button()`, `st.text_input()`, `st.number_input()` - Input components
✅ `st.dataframe()` - Table display
✅ `plotly.express.line()` - Chart generation
✅ `st.session_state` - State management (implicit)

---

## Cortex Prompt Complete Integration

### API Call Pattern (Validated):

```python
# Correct syntax for Cortex Prompt Complete in Snowflake SQL
cortex_sql = """
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-7b',
    'Your prompt here'
) AS response
"""
```

**Reference:** [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/cortex/cortex-overview)

### Available Models:
- `mistral-7b` (default, good for all tasks)
- `snowflake-arctic` (larger, more capable)
- `llama2-7b` (alternative)

---

## Troubleshooting

### Issue: "CORTEX_FUNCTIONS not found"
**Solution:** Grant Cortex privileges:
```sql
GRANT USAGE ON DATABASE SNOWFLAKE TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE TRAINING_APP_ROLE;
```

### Issue: "Stage files not found"
**Solution:** Verify files uploaded:
```sql
LIST @streamlit_app_stage;
```

### Issue: "Streamlit app not loading"
**Solution:** Check query warehouse is running:
```sql
SHOW WAREHOUSES LIKE 'TRAINING_WH';
-- Should show AUTO_SUSPEND = 300, AUTO_RESUME = TRUE
```

### Issue: "JSON parsing error from Cortex"
**Solution:** Cortex may return text before/after JSON. The app includes regex extraction:
```python
import re
json_match = re.search(r'\{[\s\S]*\}', response_text)
workout_json = json.loads(json_match.group())
```

### Issue: "Permission denied on CORTEX schema"
**Solution:** Ensure ACCOUNTADMIN grants permissions:
```sql
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE SNOWFLAKE TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE TRAINING_APP_ROLE;
```

---

## Performance Optimization

### Query Optimization:
- All tables have indexes on frequently queried columns:
  - `idx_clients_created` - Filter by client creation date
  - `idx_weighins_client_date` - Weight history queries
  - `idx_workouts_client_week` - Workout retrieval

### Cortex Performance:
- Timeout set to 60 seconds (suitable for mistral-7b)
- Caching enabled to avoid redundant API calls
- Temperature set to 0.7 (balanced creativity/consistency)

### Database Optimization:
- Foreign key constraints for data integrity
- Unique constraints on email/name to prevent duplicates
- Proper data types (NUMBER, VARCHAR, TIMESTAMP_LTZ) for performance

---

## Next Steps (Future Stages)

- **Stage 2:** Add workout logging and actual performance tracking
- **Stage 3:** Add running/cardio tracking with auto-generation
- **Stage 4:** Add nutrition logging and recipe recommendations
- **Stage 5:** Add progress analytics and prediction models
- **Stage 6:** Add progress photos and visual tracking

---

## Support

For Snowflake documentation:
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference)
- [Snowpark Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about)
- [Cortex Prompt Complete](https://docs.snowflake.com/en/user-guide/cortex/cortex-overview)

---

**Created:** November 26, 2025
**Version:** 1.0.0
**Status:** Production Ready
