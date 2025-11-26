# ⚡ UPLOAD TO STAGE - QUICK REFERENCE

## 🎯 TL;DR (30 seconds)

**Choose ONE method:**

### Option A: WebUI (Easiest) ⭐
```
Snowflake UI → Data → Databases → TRAINING_DB → PUBLIC → Stages
→ streamlit_app_stage → Upload Files button
→ Select: app.py, config.py, requirements.txt → Upload
```

### Option B: SnowSQL (Fastest)
```bash
snowsql -a <account> -u <user>
PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;
LIST @streamlit_app_stage;
```

### Option C: Snowflake WebUI SQL
```sql
-- Run in Snowflake WebUI (but PUT might not work in WebUI)
-- Better to use SnowSQL (Option B)
LIST @streamlit_app_stage;  -- Check what's there
```

---

## 📍 Location Map

```
Your Computer:
  /workspaces/ai-personal-trainer/streamlit_app/
  ├── app.py ...................... UPLOAD THIS
  ├── config.py ................... UPLOAD THIS
  └── requirements.txt ............ UPLOAD THIS

↓↓↓ (Upload to) ↓↓↓

Snowflake Stage:
  TRAINING_DB.PUBLIC.streamlit_app_stage
  ├── app.py ...................... Stored here
  ├── config.py ................... Stored here
  └── requirements.txt ............ Stored here
```

---

## ✅ Verify Upload

```sql
-- Run in Snowflake WebUI:
LIST @streamlit_app_stage;

-- Should output:
-- name                 size    created
-- app.py               850000  2025-11-26 ...
-- config.py            2000    2025-11-26 ...
-- requirements.txt     1000    2025-11-26 ...
```

---

## 🔑 Key Points

| Point | Detail |
|-------|--------|
| **Files** | 3 files: app.py, config.py, requirements.txt |
| **Location** | @streamlit_app_stage/ (stage root, not subdirs) |
| **Compression** | auto_compress=false (keep uncompressed) |
| **Overwrite** | overwrite=true (replace if exists) |
| **Stage** | Created by 06_create_streamlit_app.sql |
| **Access** | Files automatically used by Streamlit app |

---

## 🚀 Full Commands (Copy & Paste)

### SnowSQL
```bash
# 1. Connect
snowsql -a xy12345 -u youruser -w TRAINING_WH -d TRAINING_DB -s PUBLIC

# 2. Upload all three
PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;

# 3. Verify
LIST @streamlit_app_stage;
```

---

## 🛠️ Troubleshoot

| Error | Fix |
|-------|-----|
| "Stage does not exist" | Run: `CREATE STAGE IF NOT EXISTS streamlit_app_stage DIRECTORY = (ENABLE = TRUE);` |
| "Permission denied" | Use ACCOUNTADMIN role or grant: `GRANT ALL ON STAGE streamlit_app_stage TO ROLE TRAINING_APP_ROLE;` |
| "File not found" | Check path is correct: `/workspaces/ai-personal-trainer/streamlit_app/app.py` |
| "Overwrite failed" | Add: `overwrite=true` to PUT command |
| "Files won't upload" | Check: auto_compress=false, no spaces in path, file exists locally |

---

## 📚 Full Docs

- **Detailed Guide:** `UPLOAD_FILES_TO_STAGE.md`
- **Visual Guide:** `HOW_TO_UPLOAD_TO_STAGE.md`
- **App Files:** `/workspaces/ai-personal-trainer/streamlit_app/`

---

**Done?** Run `LIST @streamlit_app_stage;` to confirm ✓
