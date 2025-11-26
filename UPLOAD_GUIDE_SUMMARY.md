# 📤 UPLOAD YOUR STREAMLIT FILES TO STAGE - COMPLETE GUIDE

**Your Question:** "Can you show me how I can put my files into the streamlit_app_stage?"

**ANSWER:** I've created 4 comprehensive guides for you! Choose your preferred method below.

---

## 🎯 Choose Your Path

### ⭐ **Path 1: Visual/Easiest (WebUI) - RECOMMENDED FOR BEGINNERS**

**File:** `UPLOAD_VISUAL_GUIDE.md`

```
✓ Step-by-step visual guide
✓ No command line required
✓ 10 easy steps with ASCII diagrams
✓ Perfect for first-time users
✓ Most intuitive method

Time: ~3 minutes
Difficulty: Easy ⭐
```

**What to do:**
1. Open `UPLOAD_VISUAL_GUIDE.md`
2. Follow Steps 1-10
3. Files uploaded! ✅

---

### ⚡ **Path 2: Quick Reference (Text) - RECOMMENDED FOR EXPERIENCED USERS**

**File:** `STAGE_UPLOAD_QUICKREF.md`

```
✓ Condensed cheat sheet
✓ All methods on 1 page
✓ Copy-paste commands
✓ Troubleshooting table
✓ Perfect for quick lookup

Time: ~1 minute to read
Difficulty: Medium ⭐⭐
```

**What to do:**
1. Open `STAGE_UPLOAD_QUICKREF.md`
2. Pick your preferred method (A, B, or C)
3. Copy-paste the commands
4. Done! ✅

---

### 🖥️ **Path 3: Command Line (SnowSQL) - RECOMMENDED FOR CLI LOVERS**

**File:** `HOW_TO_UPLOAD_TO_STAGE.md`

```
✓ Detailed command-line instructions
✓ Step-by-step SnowSQL guide
✓ Troubleshooting for each method
✓ Comparison table
✓ Perfect for automation

Time: ~2 minutes
Difficulty: Medium ⭐⭐
```

**What to do:**
1. Open terminal
2. Run the SnowSQL commands from the guide
3. Files uploaded! ✅

---

### 📚 **Path 4: Complete Reference (SQL) - RECOMMENDED FOR DEEP LEARNING**

**File:** `UPLOAD_FILES_TO_STAGE.md`

```
✓ Comprehensive SQL documentation
✓ 4 different upload methods
✓ Python/Snowpark code examples
✓ Bash script for automation
✓ Complete troubleshooting section
✓ Best practices & security tips

Time: ~10 minutes to read
Difficulty: Advanced ⭐⭐⭐
```

**What to do:**
1. Open `UPLOAD_FILES_TO_STAGE.md`
2. Explore all options (SQL, Python, Bash)
3. Choose your method
4. Execute! ✅

---

## 🚀 Quick Start (Right Now)

### Fastest Method (30 seconds)

```bash
# Option A: WebUI (Recommended - no typing!)
1. Snowflake UI → Data → TRAINING_DB → PUBLIC → Stages
2. Click: streamlit_app_stage
3. Click: "Upload Files"
4. Select: app.py, config.py, requirements.txt
5. Upload!
```

### Alternative: SnowSQL (1 minute)

```bash
# Option B: Command line
snowsql -a <your_account> -u <your_user>

# Copy & paste all 3:
PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;

# Then verify:
LIST @streamlit_app_stage;
```

---

## 📊 Files to Upload

You need to upload **exactly 3 files** from `/workspaces/ai-personal-trainer/streamlit_app/`:

```
✓ app.py ....................... Main Streamlit application (850 lines)
✓ config.py .................... Configuration module (50 lines)
✓ requirements.txt ............. Dependencies list (25 lines)

✗ Don't upload:
  .env.template ................ (Local secrets only)
  README.md ..................... (Documentation)
  DEPLOYMENT_GUIDE.md ........... (Documentation)
  .streamlit/config.toml ........ (Snowflake has its own config)
```

---

## 🎯 The 3 Files Explained

| File | Size | Purpose | Must Upload? |
|------|------|---------|--------------|
| **app.py** | 850 KB | Main Streamlit app code | ✅ YES |
| **config.py** | 2 KB | Configuration module | ✅ YES |
| **requirements.txt** | 1 KB | Python package list | ✅ YES |

---

## ✅ After Upload - Verification

Run this SQL to verify your files are in the stage:

```sql
-- In Snowflake WebUI, run:
LIST @streamlit_app_stage;

-- Expected output:
-- name              file_size  uploaded
-- app.py            870400     ...
-- config.py         2048       ...
-- requirements.txt  1024       ...
```

If you see these 3 files, you're all set! ✅

---

## 🔄 Full Workflow

```
Step 1: Upload files to stage ← YOU ARE HERE
   ├─ Choose method: WebUI, SnowSQL, or SQL
   ├─ Upload 3 files: app.py, config.py, requirements.txt
   └─ Verify: LIST @streamlit_app_stage;
   
Step 2: Create Streamlit app (already done)
   └─ Ran: sql/06_create_streamlit_app.sql
   
Step 3: Access app
   ├─ Snowflake UI → Streamlit Apps
   └─ Click: AI_PERSONAL_TRAINER
   
Step 4: Test app
   ├─ Dashboard loads
   ├─ Try Weigh-In form
   └─ Verify data in database ✓
```

---

## 📁 Where Everything Is

```
Your Computer:
  /workspaces/ai-personal-trainer/
  ├── UPLOAD_VISUAL_GUIDE.md ........... Step-by-step with pictures
  ├── STAGE_UPLOAD_QUICKREF.md ........ One-page cheat sheet
  ├── HOW_TO_UPLOAD_TO_STAGE.md ....... Detailed command guide
  ├── UPLOAD_FILES_TO_STAGE.md ........ Complete reference (this guide!)
  │
  └── streamlit_app/ (the files to upload)
      ├── app.py ...................... UPLOAD THIS
      ├── config.py ................... UPLOAD THIS
      └── requirements.txt ............ UPLOAD THIS

Snowflake (after upload):
  TRAINING_DB.PUBLIC.streamlit_app_stage/
  ├── app.py .......................... Copied here
  ├── config.py ....................... Copied here
  └── requirements.txt ................ Copied here
```

---

## 🎓 Which Guide to Read?

| Your Situation | Read This Guide |
|---|---|
| "I'm new to Snowflake" | **UPLOAD_VISUAL_GUIDE.md** |
| "Just show me the commands" | **STAGE_UPLOAD_QUICKREF.md** |
| "I prefer command line" | **HOW_TO_UPLOAD_TO_STAGE.md** |
| "I want all the details" | **UPLOAD_FILES_TO_STAGE.md** |
| "I'm automating this" | **UPLOAD_FILES_TO_STAGE.md** (Python/Bash sections) |
| "Something went wrong" | **UPLOAD_FILES_TO_STAGE.md** (Troubleshooting) |

---

## ⚡ TL;DR (Too Long; Didn't Read)

### WebUI (Easiest):
```
Data → TRAINING_DB → PUBLIC → Stages → streamlit_app_stage 
→ Upload Files → Select 3 files → Upload → Done! ✅
```

### SnowSQL (Fastest):
```bash
snowsql -a account -u user
PUT file:///path/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///path/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///path/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;
LIST @streamlit_app_stage;
```

---

## 🚀 Next Steps

1. **Upload files** (choose method above) ← DO THIS NOW
2. **Verify upload** (run: `LIST @streamlit_app_stage;`)
3. **Create app** (run: `sql/06_create_streamlit_app.sql`)
4. **Access app** (Snowflake UI → Streamlit Apps → AI_PERSONAL_TRAINER)
5. **Test forms** (try Weigh-In, Workout, Running)

---

## 💡 Pro Tips

✓ Use **WebUI** if you're comfortable with UI navigation  
✓ Use **SnowSQL** if you want to automate  
✓ Use **SQL** if you're already in a SQL editor  
✓ Don't forget **auto_compress=false** (important!)  
✓ Always use **overwrite=true** (in case of re-upload)  
✓ Only upload the **3 Python files** (not docs or config)  

---

## ❓ Common Questions

**Q: Which method is fastest?**  
A: SnowSQL is fastest, but WebUI is easiest

**Q: Can I upload via drag-and-drop?**  
A: Yes! Drag files onto the stage in WebUI

**Q: What if upload fails?**  
A: Check permissions, file path, and try again. See troubleshooting guide.

**Q: Do I upload every time I change the code?**  
A: Yes, upload again with `overwrite=true`

**Q: What happens after I upload?**  
A: Snowflake automatically uses the files for your Streamlit app

---

## 📞 Need Help?

- **Visual learner?** → Read `UPLOAD_VISUAL_GUIDE.md`
- **Prefer text?** → Read `STAGE_UPLOAD_QUICKREF.md`
- **Need details?** → Read `UPLOAD_FILES_TO_STAGE.md`
- **Command line?** → Read `HOW_TO_UPLOAD_TO_STAGE.md`

---

## ✅ Checklist

Before you start:
- [ ] Have Snowflake account access
- [ ] Know your Snowflake account ID
- [ ] Have your username/password
- [ ] Know your warehouse name (TRAINING_WH)
- [ ] Have files ready to upload:
  - [ ] /workspaces/ai-personal-trainer/streamlit_app/app.py
  - [ ] /workspaces/ai-personal-trainer/streamlit_app/config.py
  - [ ] /workspaces/ai-personal-trainer/streamlit_app/requirements.txt

After you upload:
- [ ] Run `LIST @streamlit_app_stage;` to verify
- [ ] See 3 files? ✓ Success!
- [ ] Don't see files? Check troubleshooting section

---

**Summary:** Pick one of the 4 guides above and follow the steps. All methods work equally well - choose based on your preference!

**Recommended:** Start with `UPLOAD_VISUAL_GUIDE.md` or `STAGE_UPLOAD_QUICKREF.md` ✅
