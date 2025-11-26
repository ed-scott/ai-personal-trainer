# 📤 HOW TO UPLOAD FILES TO STREAMLIT_APP_STAGE

**Quick Answer:** Use **WebUI upload** (easiest) or **SnowSQL PUT command** (fastest for CLI)

---

## 🚀 QUICK START (3 Minutes)

### Method 1: Snowflake WebUI (Easiest) ⭐

```
1. Open: snowflakecomputing.com
2. Go to: Data → Databases → TRAINING_DB → PUBLIC → Stages
3. Click: streamlit_app_stage
4. Click: "Upload Files" button
5. Select: 
   □ app.py
   □ config.py
   □ requirements.txt
6. Click: Upload
7. Done! ✅
```

### Method 2: SnowSQL Command Line (Fastest)

```bash
# Connect to Snowflake
snowsql -a <account> -u <username> -w TRAINING_WH -d TRAINING_DB -s PUBLIC

# Upload files (copy & paste all 3 at once)
PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;

# Verify
LIST @streamlit_app_stage;
```

---

## 📊 Comparison of Methods

| Method | Time | Ease | Command Line | Best For |
|--------|------|------|--------------|----------|
| **WebUI** | 2 min | ⭐⭐⭐ Easy | No | First time, visual |
| **SnowSQL** | 1 min | ⭐⭐ Medium | Yes | Scripting, batch |
| **SQL Query** | 3 min | ⭐ Hard | No | Advanced users |
| **Python** | 2 min | ⭐⭐ Medium | Yes | Automation |

---

## ✅ Verification

After uploading, verify files are in the stage:

```sql
-- In Snowflake WebUI, run:
LIST @streamlit_app_stage;

-- Should show:
-- app.py (850 KB)
-- config.py (2 KB)
-- requirements.txt (1 KB)
```

---

## 📁 File Structure

Files should be uploaded to **stage root** (not subdirectories):

```
streamlit_app_stage/
├── app.py ........................ Your main app (850 lines)
├── config.py ..................... Configuration module
└── requirements.txt .............. Dependencies list
```

NOT like this (wrong):
```
streamlit_app_stage/
└── streamlit_app/
    ├── app.py ..................... ✗ Too deep
    ├── config.py
    └── requirements.txt
```

---

## 🔧 SnowSQL Put Command Explained

```bash
PUT file:///local/path/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
    ↑                         ↑                       ↑                    ↑
    |                         |                       |                    |
  Upload               Where is the file?      Stage name            Options:
                                                              -false = don't compress
                                                              -true = replace if exists
```

### Options Breakdown:
- `auto_compress=false` - Keep files uncompressed (Streamlit needs raw Python)
- `overwrite=true` - Replace if file already exists
- `@streamlit_app_stage/` - Stage name with trailing slash

---

## 🎯 Step-by-Step WebUI Upload

### Step 1: Navigate to Stage
```
1. Snowflake UI (top left)
2. Click: Data
3. Click: Databases
4. Click: TRAINING_DB
5. Click: Schemas
6. Click: PUBLIC
7. Click: Stages
8. Click: streamlit_app_stage
```

### Step 2: Upload Files
```
1. Look for "Upload Files" button (top right area)
2. Click it
3. A file browser opens
4. Navigate to: /workspaces/ai-personal-trainer/streamlit_app/
5. Select: app.py (then Ctrl+click to select multiple)
6. Select: config.py
7. Select: requirements.txt
8. Click "Open"
9. Files upload automatically
```

### Step 3: Verify
```
You'll see the files listed:
✓ app.py
✓ config.py  
✓ requirements.txt
```

---

## 🖥️ Step-by-Step SnowSQL Upload

### Step 1: Open Terminal
```bash
# Open your terminal/command prompt
# Navigate to your app directory
cd /workspaces/ai-personal-trainer/streamlit_app
```

### Step 2: Connect to Snowflake
```bash
snowsql -a xy12345 -u youruser
# (It will prompt for password)
# Then you're connected!
```

### Step 3: Select Database
```bash
USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;
```

### Step 4: Upload Files
```bash
# Copy & paste all three lines:
PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;
```

### Step 5: Verify Upload
```bash
LIST @streamlit_app_stage;
```

---

## ❓ Troubleshooting

### Problem: "Stage does not exist"
```sql
-- Solution: Create the stage first
CREATE STAGE IF NOT EXISTS streamlit_app_stage 
  DIRECTORY = (ENABLE = TRUE);
```

### Problem: "Permission denied"
```sql
-- Solution: Use ACCOUNTADMIN role or grant permissions
GRANT ALL ON STAGE streamlit_app_stage TO ROLE TRAINING_APP_ROLE;
```

### Problem: "File already exists"
```bash
# Solution: Use overwrite=true (already in commands above)
# Or delete first:
REMOVE @streamlit_app_stage/app.py;
```

### Problem: "Cannot find file"
```bash
# Check the path is correct:
# Should be: /workspaces/ai-personal-trainer/streamlit_app/app.py
# Not: ~/streamlit_app/app.py (~ doesn't work, use full path)
ls -la /workspaces/ai-personal-trainer/streamlit_app/
```

---

## 🎓 What Each File Does

### `app.py` (Main Application)
- 850+ lines of Streamlit code
- 7 pages (Dashboard, Progress, Forms, etc.)
- Database operations
- Chart generation
- This is the main file Streamlit will run

### `config.py` (Configuration)
- Snowflake connection settings
- Database credentials handling
- Feature flags
- AI configuration
- Imported by app.py

### `requirements.txt` (Dependencies)
- List of Python packages needed
- Streamlit, Snowpark, Plotly, etc.
- Snowflake will install these automatically

---

## 📋 Before & After

### Before Upload
```
Your Computer:
  /workspaces/ai-personal-trainer/streamlit_app/
  ├── app.py
  ├── config.py
  └── requirements.txt

Snowflake:
  streamlit_app_stage/ (empty)
```

### After Upload
```
Your Computer:
  (files still here)

Snowflake:
  streamlit_app_stage/
  ├── app.py (copied)
  ├── config.py (copied)
  └── requirements.txt (copied)
  
Streamlit uses these files automatically! ✓
```

---

## 🚀 Full Workflow

```
1. Create stage (already done by sql/06_create_streamlit_app.sql)
   ↓
2. Upload files (you do this now)
   webui: drag & drop or button
   cli: PUT commands
   ↓
3. Create Streamlit app (already done by sql/06_create_streamlit_app.sql)
   CREATE STREAMLIT ... STAGE = streamlit_app_stage ...
   ↓
4. Access app in Snowflake UI
   ↓
5. App automatically loads files from stage
   ↓
✓ Done!
```

---

## 📝 Summary Table

| What | Where | How |
|-----|-------|-----|
| **app.py** | `/workspaces/ai-personal-trainer/streamlit_app/app.py` | Upload to `@streamlit_app_stage/` |
| **config.py** | `/workspaces/ai-personal-trainer/streamlit_app/config.py` | Upload to `@streamlit_app_stage/` |
| **requirements.txt** | `/workspaces/ai-personal-trainer/streamlit_app/requirements.txt` | Upload to `@streamlit_app_stage/` |
| **Stage** | `TRAINING_DB.PUBLIC.streamlit_app_stage` | Created by 06_create_streamlit_app.sql |
| **Verification** | Run `LIST @streamlit_app_stage;` | Should show 3 files |

---

## 🎯 Next Steps After Upload

```
1. ✓ Upload files to stage (DO THIS NOW)
2. ✓ Run sql/06_create_streamlit_app.sql (if not done)
3. ✓ Open Snowflake UI → Streamlit Apps
4. ✓ Click "AI_PERSONAL_TRAINER"
5. ✓ App loads with your files!
```

---

**Recommendation:** Use **WebUI upload** - it's easiest and most intuitive! 🎯

See `UPLOAD_FILES_TO_STAGE.md` for detailed SQL reference.
