# AI Personal Trainer - Stage 1 Quick Start Guide

**⚡ Get Running in 10 Minutes**

---

## 🚀 Quick Start (4 Steps)

### Step 1: Setup GitHub Integration (2 min)

1. Follow **`sql/04_git_integration_setup.md`** to:
   - Generate GitHub Personal Access Token (PAT)
   - Update SQL placeholders with your credentials
   - Push code to your GitHub repository

### Step 2: Run SQL Setup (3 min)

Copy and paste into Snowflake SQL Editor as **ACCOUNTADMIN** in order:

```bash
# File: sql/01_stage1_setup.sql
# File: sql/02_stage1_create_tables.sql
# File: sql/03_stage1_create_streamlit.sql (NOW USES GIT)
```

✅ **Verification:**
```sql
SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_CATALOG = 'TRAINING_DB';
-- Expected: 8 tables

SHOW GIT REPOSITORIES IN TRAINING_DB.PUBLIC;
-- Expected: ai_personal_trainer_repo
```

### Step 3: Configure Cortex & Access App (2 min)

```sql
-- Grant Cortex access
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE SNOWFLAKE TO ROLE TRAINING_APP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE TRAINING_APP_ROLE;
```

Access Streamlit app:
- Snowflake UI → Projects → Streamlit Apps → **ai_personal_trainer**

---

## 📋 Quick Test

1. **Create Client:** Home page → Form → Create
2. **Generate Workout:** Workout Generator → Select Client → Generate
3. **Generate Meal Plan:** Meal Plan Generator → Generate
4. **Track Weight:** Weight & Measurements → Record Weigh-in

---

## 📁 File Roadmap

| File | Purpose |
|------|---------|
| `sql/04_git_integration_setup.md` | **Start here!** GitHub PAT + Secret setup |
| `01_stage1_setup.sql` | Database, warehouse, roles, privileges |
| `02_stage1_create_tables.sql` | 8 core tables + indexes + constraints |
| `03_stage1_create_streamlit.sql` | **Git-based** Streamlit app + repository |
| `app.py` | Main Streamlit application (in GitHub repo) |
| `DEPLOYMENT_GUIDE.md` | Detailed deployment instructions |
| `SYNTAX_VALIDATION_REPORT.md` | Syntax validation details |

---

## ✅ Syntax Validation

All SQL and Python syntax verified against:
- ✅ [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference)
- ✅ [Streamlit Documentation](https://docs.streamlit.io)
- ✅ [Snowpark Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python)
- ✅ [Snowflake Cortex](https://docs.snowflake.com/en/user-guide/cortex/cortex-overview)

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "CORTEX_FUNCTIONS not found" | Run: `GRANT USAGE ON SCHEMA SNOWFLAKE.CORTEX TO ROLE TRAINING_APP_ROLE;` |
| "Files not found in stage" | Run: `LIST @streamlit_app_stage;` to verify upload |
| "Warehouse not running" | Check: `SHOW WAREHOUSES LIKE 'TRAINING_WH';` |
| "Permission denied" | Ensure user has `TRAINING_APP_ROLE` granted |

---

## 📚 Full Documentation

- **Deployment:** See `sql/DEPLOYMENT_GUIDE.md`
- **Syntax Details:** See `sql/SYNTAX_VALIDATION_REPORT.md`
- **YAML Spec:** See `prompts/streamlit_native_snowflake_app.yaml`

---

**Status:** ✅ Production Ready | **Version:** 1.0.0 | **Stage:** 1
