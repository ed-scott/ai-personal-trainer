# Streamlit Native App Deployment Guide
## AI Personal Trainer - Snowflake Edition

**Status:** ✅ Ready for Deployment  
**Date:** November 26, 2025  
**Version:** 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Methods](#deployment-methods)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Features](#features)

---

## Overview

The AI Personal Trainer is a **Streamlit Native** app hosted directly in Snowflake. It provides:

✅ **Weigh-in Tracking** - Manual weight entry with optional body fat and muscle mass  
✅ **Workout Logging** - Exercise tracking with suggested vs actual performance  
✅ **Running Sessions** - Distance, pace, and performance tracking  
✅ **Progress Dashboards** - Weight trends and performance analysis  
✅ **Role-Based Access** - Secure access via Snowflake roles  

**Architecture:**
- **Frontend:** Streamlit Native (hosted in Snowflake)
- **Backend:** Snowflake SQL + Snowpark Python
- **Storage:** TRAINING_DB.PUBLIC (14 tables)
- **Auth:** Snowflake roles (TRAINING_APP_ROLE, TRAINING_APP_ADMIN)

---

## Prerequisites

### Required
- ✅ Snowflake account with ACCOUNTADMIN access
- ✅ Database: TRAINING_DB (created by 00_master_deployment.sql)
- ✅ Schema: PUBLIC with all 14 tables
- ✅ Warehouse: TRAINING_WH (XSMALL or larger)
- ✅ Roles: TRAINING_APP_ROLE, TRAINING_APP_ADMIN

### Optional (for AI features)
- OpenAI API key (for suggested workout generation)
- Sentence Transformers (for exercise embeddings)

### Environment Variables Required
```bash
export SNOWFLAKE_ACCOUNT="your_account"           # e.g., xy12345.us-east-1
export SNOWFLAKE_USER="your_user"                 # e.g., trainer_admin
export SNOWFLAKE_PASSWORD="your_password"         # Your Snowflake password
export SNOWFLAKE_ROLE="TRAINING_APP_ROLE"         # or TRAINING_APP_ADMIN
export SNOWFLAKE_WAREHOUSE="TRAINING_WH"
export SNOWFLAKE_DATABASE="TRAINING_DB"
export SNOWFLAKE_SCHEMA="PUBLIC"
export OPENAI_API_KEY="sk-..."                    # Optional: for AI features
```

---

## Deployment Methods

### Method 1: Create Streamlit via SQL (Recommended for Snowflake Native)

**Step 1: Execute the SQL DDL**
```sql
-- Run this SQL in Snowflake:
-- File: sql/06_create_streamlit_app.sql

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

CREATE STAGE IF NOT EXISTS streamlit_app_stage
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Internal stage for Streamlit app files';

CREATE OR REPLACE STREAMLIT AI_PERSONAL_TRAINER
  STAGE = streamlit_app_stage
  MAIN_FILE = '/app.py'
  QUERY_WAREHOUSE = TRAINING_WH
  TITLE = 'AI Personal Trainer'
  COMMENT = 'AI-powered personal training app';

-- Grant permissions
GRANT EXECUTE ON STREAMLIT TRAINING_DB.PUBLIC.AI_PERSONAL_TRAINER 
  TO ROLE TRAINING_APP_ROLE;
```

**Step 2: Access the app**
1. Open Snowflake UI
2. Navigate to **Streamlit Apps**
3. Click **AI_PERSONAL_TRAINER**
4. App loads automatically

---

### Method 2: Local Development (for testing)

**Step 1: Clone repository**
```bash
cd /workspaces/ai-personal-trainer
```

**Step 2: Set environment variables**
```bash
# Create .env file
cat > .env << EOF
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=TRAINING_APP_ROLE
SNOWFLAKE_WAREHOUSE=TRAINING_WH
SNOWFLAKE_DATABASE=TRAINING_DB
SNOWFLAKE_SCHEMA=PUBLIC
OPENAI_API_KEY=sk-...
EOF
```

**Step 3: Install dependencies**
```bash
cd streamlit_app
pip install -r requirements.txt
```

**Step 4: Run locally**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

### Method 3: Deploy to Streamlit Cloud (Alternative)

**Step 1: Push to GitHub**
```bash
git push origin main
```

**Step 2: Connect to Streamlit Cloud**
- Visit https://share.streamlit.io
- Connect GitHub repo
- Select `/streamlit_app/app.py` as main file

**Step 3: Configure secrets**
In Streamlit Cloud, add these secrets:
```toml
SNOWFLAKE_ACCOUNT = "your_account"
SNOWFLAKE_USER = "your_user"
SNOWFLAKE_PASSWORD = "your_password"
SNOWFLAKE_ROLE = "TRAINING_APP_ROLE"
SNOWFLAKE_WAREHOUSE = "TRAINING_WH"
SNOWFLAKE_DATABASE = "TRAINING_DB"
SNOWFLAKE_SCHEMA = "PUBLIC"
OPENAI_API_KEY = "sk-..."
```

---

## Configuration

### Database Connection

The app connects using environment variables:

```python
from snowflake.snowpark.session import Session

connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE", "TRAINING_APP_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "TRAINING_WH"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "TRAINING_DB"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
}

session = Session.builder.configs(connection_params).create()
```

### Customization

**Change app title/theme:**
```python
st.set_page_config(
    page_title="My Custom Title",
    page_icon="🏋️",
    theme="dark"  # or "light"
)
```

**Add new pages:**
```python
# In main() navigation:
elif page == "📈 Reports":
    show_reports(session)

def show_reports(session):
    st.subheader("Custom Reports")
    # Add your code here
```

---

## Testing

### Verify Installation

**1. Check database objects:**
```sql
-- Run in Snowflake
SHOW STREAMLITS IN DATABASE TRAINING_DB;
SHOW STAGES IN SCHEMA TRAINING_DB.PUBLIC;
SHOW VIEWS IN SCHEMA TRAINING_DB.PUBLIC;
```

**2. Test connection:**
```bash
python -c "
from snowflake.snowpark.session import Session
import os

params = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
}
session = Session.builder.configs(params).create()
print('✅ Connection successful!')
print(session.sql('SELECT 1').collect())
"
```

**3. Test Streamlit locally:**
```bash
cd streamlit_app
streamlit run app.py
```

**4. Test form submissions:**
- Navigate to "⚖️ Weigh-In" page
- Fill form and submit
- Check WEIGH_INS table in Snowflake

---

## Troubleshooting

### Issue: "Failed to connect to Snowflake"

**Cause:** Missing or incorrect environment variables

**Solution:**
```bash
# Verify environment variables
echo $SNOWFLAKE_ACCOUNT
echo $SNOWFLAKE_USER
echo $SNOWFLAKE_ROLE

# Check credentials
snowsql -a $SNOWFLAKE_ACCOUNT -u $SNOWFLAKE_USER
```

---

### Issue: "Permission denied" when accessing tables

**Cause:** User/role doesn't have SELECT/INSERT permissions

**Solution:**
```sql
-- As ACCOUNTADMIN, grant permissions:
GRANT SELECT ON ALL TABLES IN SCHEMA TRAINING_DB.PUBLIC 
  TO ROLE TRAINING_APP_ROLE;

GRANT INSERT, UPDATE ON TABLE TRAINING_DB.PUBLIC.WEIGH_INS 
  TO ROLE TRAINING_APP_ROLE;
```

---

### Issue: "Module not found" (e.g., streamlit, snowflake)

**Cause:** Missing Python dependencies

**Solution:**
```bash
pip install -r streamlit_app/requirements.txt
```

---

### Issue: Slow query performance

**Cause:** Warehouse is suspended or too small

**Solution:**
```sql
-- Check warehouse status
SHOW WAREHOUSES;

-- Resume if suspended
ALTER WAREHOUSE TRAINING_WH RESUME;

-- Upgrade if needed (XSMALL → SMALL)
ALTER WAREHOUSE TRAINING_WH SET WAREHOUSE_SIZE = 'SMALL';
```

---

## Features

### Pages Overview

| Page | Description | Fields |
|------|---|---|
| **Dashboard** | Overview and recent activity | Metrics, recent workouts, recent weigh-ins |
| **📊 Progress** | Client progress tracking | Weight trend chart, performance metrics |
| **⚖️ Weigh-In** | Manual weight entry form | Weight, body fat %, muscle mass, date |
| **🏋️ Workouts** | Exercise tracking | Exercises, sets, reps, weight, RPE |
| **🏃 Running** | Running session logging | Distance, pace, duration, run type |
| **🍽️ Nutrition** | Nutrition logging | *Coming soon* |
| **⚙️ Settings** | Configuration and system info | Database info, cache management |

### Form Inputs

**Weigh-In Form:**
```
- Client (selectbox)
- Date (date picker)
- Weight (kg) - required
- Body Fat % - optional
- Muscle Mass (kg) - optional
- Entry Source (manual|device|import)
- Notes (text area)
```

**Workout Form:**
```
- Client (selectbox)
- Date (date picker)
- Type (gym|crossfit|yoga|other)
- Start Time
- Multiple Exercises:
  - Exercise (selectbox)
  - Suggested: sets, reps, weight
  - Actual: sets, reps, weight, RPE
  - Notes
```

**Running Form:**
```
- Client (selectbox)
- Date (date picker)
- Suggested: distance, pace, type
- Actual: distance, duration, type
- Calories (optional)
- Device (optional)
- Notes (text area)
```

---

## Database Queries Performed

The app runs these queries:

**Dashboard:**
```sql
SELECT COUNT(*) FROM CLIENTS;
SELECT COUNT(*) FROM TRAINERS;
SELECT COUNT(*) FROM WORKOUTS WHERE date >= CURRENT_DATE - 7;
SELECT COUNT(*) FROM RUNNING_SESSIONS WHERE date >= CURRENT_DATE - 7;
```

**Progress:**
```sql
SELECT * FROM CLIENT_PROGRESS_SUMMARY WHERE client_id = ?;
SELECT * FROM WEIGH_INS WHERE client_id = ? AND date >= CURRENT_DATE - 90;
```

**Insert Operations:**
```sql
INSERT INTO WEIGH_INS (...) VALUES (...);
INSERT INTO WORKOUTS (...) VALUES (...);
INSERT INTO WORKOUT_EXERCISES (...) VALUES (...);
INSERT INTO RUNNING_SESSIONS (...) VALUES (...);
```

---

## Performance Considerations

**Cache Strategy:**
- Database connection cached with `@st.cache_resource`
- Queries cached for 60 seconds
- Clear cache with "🔄 Refresh Cache" button

**Optimization Tips:**
1. Use indexes on CLIENT_ID and DATE columns
2. Limit queries to 30-90 day windows
3. Use materialized views for aggregations
4. Archive old data regularly

**Costs:**
- Compute: $2-4/hour (XSMALL warehouse)
- Storage: $23/month per TB
- Estimate: $100-300/month for active app

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tables created via `00_master_deployment.sql`
- [ ] Test data loaded via `05_validation_and_testing.sql`
- [ ] Database and roles verified
- [ ] Environment variables configured

### Deployment
- [ ] Run `06_create_streamlit_app.sql` in Snowflake
- [ ] App created successfully (verify in Streamlit Apps)
- [ ] Grant permissions to TRAINING_APP_ROLE

### Post-Deployment
- [ ] Access app from Snowflake UI
- [ ] Test each page (Dashboard, Weigh-In, Workouts, etc.)
- [ ] Test form submission (Weigh-In)
- [ ] Verify data appears in database
- [ ] Check query performance

### Production
- [ ] Set up alerts for failed tasks
- [ ] Monitor warehouse costs
- [ ] Plan backup strategy
- [ ] Document custom modifications
- [ ] Set up access control

---

## Quick Start (5 Minutes)

1. **Deploy SQL:**
   ```bash
   # In Snowflake, run:
   sql/06_create_streamlit_app.sql
   ```

2. **Access app:**
   - Open Snowflake UI
   - Go to Streamlit Apps
   - Click AI_PERSONAL_TRAINER

3. **Add test client:**
   ```sql
   INSERT INTO CLIENTS (client_id, first_name, last_name, email)
   VALUES ('CLIENT_001', 'John', 'Doe', 'john@example.com');
   ```

4. **Test Weigh-In:**
   - Navigate to ⚖️ Weigh-In
   - Select client
   - Enter weight
   - Click Save

5. **Check data:**
   ```sql
   SELECT * FROM WEIGH_INS ORDER BY created_at DESC;
   ```

---

## Support & Resources

- **Snowflake Docs:** https://docs.snowflake.com/en/user-guide/ui-snowsight-streamlit
- **Streamlit Docs:** https://docs.streamlit.io
- **Snowpark Python:** https://docs.snowflake.com/en/developer-guide/snowpark/python
- **GitHub:** https://github.com/ed-scott/ai-personal-trainer

---

## File Structure

```
ai-personal-trainer/
├── streamlit_app/
│   ├── app.py                 # Main Streamlit app
│   ├── requirements.txt        # Python dependencies
│   ├── config.py              # Configuration module
│   └── .streamlit/
│       └── config.toml        # Streamlit settings (optional)
│
├── sql/
│   ├── 00_master_deployment.sql
│   ├── 06_create_streamlit_app.sql  # ← Run this to create app
│   ├── 05_validation_and_testing.sql
│   └── ...
│
└── README.md
```

---

**Status:** ✅ Production Ready  
**Last Updated:** November 26, 2025  
**Version:** 1.0.0
