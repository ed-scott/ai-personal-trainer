-- ========================================================================
-- UPLOADING STREAMLIT APP FILES TO SNOWFLAKE STAGE
-- ========================================================================
-- Purpose: Upload your local Streamlit app files to the streamlit_app_stage
-- Location: TRAINING_DB.PUBLIC.streamlit_app_stage
-- ========================================================================

-- ========================================================================
-- OPTION 1: Using SnowSQL (Command Line) - RECOMMENDED FOR INITIAL SETUP
-- ========================================================================
-- This is the easiest method for uploading multiple files at once

/*
STEPS:

1. Open Terminal/Command Prompt
   cd /workspaces/ai-personal-trainer/streamlit_app

2. Connect to Snowflake using SnowSQL
   snowsql -a <account_id> -u <username> -w TRAINING_WH -d TRAINING_DB -s PUBLIC

3. Upload all Python files to the stage:
   PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py \
       @streamlit_app_stage/app.py auto_compress=false;
   
   PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py \
       @streamlit_app_stage/config.py auto_compress=false;

4. Upload requirements.txt:
   PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt \
       @streamlit_app_stage/requirements.txt auto_compress=false;

5. Verify uploads:
   LIST @streamlit_app_stage;

NOTES:
- Use 'auto_compress=false' to prevent compression (Streamlit needs raw files)
- The stage path is: @streamlit_app_stage/
- Files will be accessible as: /app.py, /config.py, etc.
*/

-- ========================================================================
-- OPTION 2: Using Snowflake WebUI - MOST USER-FRIENDLY
-- ========================================================================

/*
STEPS:

1. In Snowflake WebUI:
   - Click "Data" in the left sidebar
   - Click "Databases"
   - Select "TRAINING_DB"
   - Select "PUBLIC" schema
   - Click "Stages"
   - Click on "streamlit_app_stage"

2. Click the "Upload Files" button

3. Select files to upload:
   - app.py
   - config.py
   - requirements.txt
   - Any other supporting files

4. Click "Upload"

5. Verify files appear in the stage browser

NOTES:
- WebUI automatically handles compression settings
- You can see files as you upload them
- Drag-and-drop is supported
- Max file size: 100 MB per file (default)
*/

-- ========================================================================
-- OPTION 3: Using SQL PUT Command (Advanced)
-- ========================================================================

-- First, verify the stage exists:
SHOW STAGES IN SCHEMA TRAINING_DB.PUBLIC;

-- Check stage details:
DESC STAGE streamlit_app_stage;

-- List current stage contents:
LIST @streamlit_app_stage;

-- Upload a single file (using local file path):
-- Note: Execute this from directory containing your files
-- PUT file:///absolute/path/to/app.py @streamlit_app_stage/app.py auto_compress=false;

-- Upload with overwrite (replace if exists):
-- PUT file:///absolute/path/to/app.py @streamlit_app_stage/app.py auto_compress=false overwrite=true;

-- ========================================================================
-- OPTION 4: Using Python/Snowpark (Programmatic)
-- ========================================================================

/*
from snowflake.snowpark.session import Session

# Create session
session = Session.builder.configs({
    "account": "your_account",
    "user": "your_user",
    "password": "your_password",
    "role": "ACCOUNTADMIN",
    "warehouse": "TRAINING_WH",
    "database": "TRAINING_DB",
    "schema": "PUBLIC"
}).create()

# Upload file
session.file.put(
    local_file_path="/workspaces/ai-personal-trainer/streamlit_app/app.py",
    stage_location="@streamlit_app_stage",
    auto_compress=False,
    overwrite=True
)

# Upload multiple files
import os
app_dir = "/workspaces/ai-personal-trainer/streamlit_app"
for file in ["app.py", "config.py", "requirements.txt"]:
    session.file.put(
        local_file_path=os.path.join(app_dir, file),
        stage_location="@streamlit_app_stage",
        auto_compress=False,
        overwrite=True
    )

session.close()
*/

-- ========================================================================
-- STEP-BY-STEP: RECOMMENDED WORKFLOW
-- ========================================================================

/*
STEP 1: Verify Stage Exists
   Run: SHOW STAGES;
   Expected: streamlit_app_stage appears in list

STEP 2: Check Current Contents
   Run: LIST @streamlit_app_stage;
   Expected: Empty (or previous files)

STEP 3: Upload Files (Choose one method above)
   Option A: SnowSQL PUT (recommended for first time)
   Option B: WebUI Upload (most user-friendly)
   Option C: Python Script (programmatic)

STEP 4: Verify Upload
   Run: LIST @streamlit_app_stage;
   Expected: Your files appear with sizes

STEP 5: Check File Contents (Optional)
   SELECT GET_PRESIGNED_URL(@streamlit_app_stage, 'app.py', 3600) as download_url;

STEP 6: Update Streamlit App
   The app will automatically use files from the stage
   No additional configuration needed
*/

-- ========================================================================
-- COMPLETE SNOWSQL SCRIPT (Copy & Paste Ready)
-- ========================================================================

/*
Save this as: upload_streamlit_files.sql

Then run: snowsql -a <account> -u <username> -f upload_streamlit_files.sql

-- Connect to database
USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- Verify stage
SHOW STAGES;
LIST @streamlit_app_stage;

-- Upload files
PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;

-- Verify upload
LIST @streamlit_app_stage;

-- Success!
SELECT 'Files uploaded successfully!' as status;
*/

-- ========================================================================
-- VERIFICATION QUERIES
-- ========================================================================

-- Check if stage was created:
SELECT 
  STAGE_NAME,
  STAGE_TYPE,
  STAGE_URL,
  COMMENT
FROM INFORMATION_SCHEMA.STAGES
WHERE STAGE_SCHEMA = 'PUBLIC'
  AND STAGE_NAME = 'STREAMLIT_APP_STAGE';

-- List all files in stage:
LIST @streamlit_app_stage;

-- Get file details:
SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

-- Check stage size:
SELECT 
  COUNT(*) as file_count,
  SUM(FILE_SIZE) as total_size_bytes
FROM TABLE(LIST(BUILD_SCOPED_FILE_URL(@streamlit_app_stage, '*')));

-- ========================================================================
-- TROUBLESHOOTING
-- ========================================================================

/*
ISSUE: "Stage does not exist"
SOLUTION: Run sql/06_create_streamlit_app.sql first
          It creates the stage if it doesn't exist

ISSUE: "Permission denied"
SOLUTION: Use ACCOUNTADMIN or TRAINING_APP_ADMIN role
          Or grant permissions: GRANT ALL ON STAGE streamlit_app_stage TO ROLE <role>;

ISSUE: "File already exists"
SOLUTION: Use OVERWRITE=TRUE in PUT command
          Or delete first: REMOVE @streamlit_app_stage/filename;

ISSUE: "Files not showing in Streamlit app"
SOLUTION: Make sure MAIN_FILE = '/app.py' (with leading slash)
          Verify files are in stage root, not subdirectory
          Check CREATE STREAMLIT command uses correct stage

ISSUE: "Import errors in Streamlit"
SOLUTION: Check requirements.txt is uploaded
          Verify app.py and config.py are in same directory
          Use relative imports: from config import ...

ISSUE: "Stage shows but files won't upload"
SOLUTION: Check file permissions (should be readable)
          Try smaller test file first
          Use auto_compress=false
          Check available storage quota
*/

-- ========================================================================
-- BEST PRACTICES
-- ========================================================================

/*
1. FILE ORGANIZATION
   ✓ Keep all files in stage root (/app.py, /config.py, etc.)
   ✗ Don't use subdirectories
   
2. FILE NAMING
   ✓ Use lowercase with underscores (app.py, config.py)
   ✓ No spaces in filenames
   
3. COMPRESSION
   ✓ Use auto_compress=false for Python/text files
   ✗ Don't use gzip compression for Streamlit
   
4. UPDATES
   ✓ Always use overwrite=true when updating
   ✓ Test locally before uploading
   ✓ Keep version backups
   
5. SECURITY
   ✓ Don't upload secrets or API keys
   ✓ Use environment variables instead
   ✓ Keep .env files local, not in stage
   
6. PERMISSIONS
   ✓ Grant stage access to TRAINING_APP_ROLE
   ✓ Use least privilege principle
   ✓ Review permissions regularly
*/

-- ========================================================================
-- AUTOMATION: BATCH UPLOAD SCRIPT (Bash)
-- ========================================================================

/*
Save as: upload_stage.sh

#!/bin/bash

# Configuration
SNOWFLAKE_ACCOUNT="your_account"
SNOWFLAKE_USER="your_user"
SNOWFLAKE_PASSWORD="your_password"
SNOWFLAKE_DATABASE="TRAINING_DB"
SNOWFLAKE_SCHEMA="PUBLIC"
STAGE_NAME="streamlit_app_stage"
APP_DIR="/workspaces/ai-personal-trainer/streamlit_app"

# Files to upload
FILES=("app.py" "config.py" "requirements.txt")

echo "Uploading files to $STAGE_NAME..."

for file in "${FILES[@]}"; do
    echo "Uploading $file..."
    
    snowsql -a "$SNOWFLAKE_ACCOUNT" \
            -u "$SNOWFLAKE_USER" \
            -d "$SNOWFLAKE_DATABASE" \
            -s "$SNOWFLAKE_SCHEMA" \
            -q "PUT file://$APP_DIR/$file @$STAGE_NAME/ auto_compress=false overwrite=true;"
    
    if [ $? -eq 0 ]; then
        echo "✓ $file uploaded successfully"
    else
        echo "✗ Failed to upload $file"
    fi
done

echo "Upload complete!"
echo ""
echo "Verifying files..."
snowsql -a "$SNOWFLAKE_ACCOUNT" \
        -u "$SNOWFLAKE_USER" \
        -d "$SNOWFLAKE_DATABASE" \
        -s "$SNOWFLAKE_SCHEMA" \
        -q "LIST @$STAGE_NAME;"

# Run: chmod +x upload_stage.sh
# Run: ./upload_stage.sh
*/

-- ========================================================================
-- QUICK REFERENCE
-- ========================================================================

-- Create stage (if not already created):
CREATE STAGE IF NOT EXISTS streamlit_app_stage 
  DIRECTORY = (ENABLE = TRUE);

-- List files:
LIST @streamlit_app_stage;

-- Upload single file:
PUT file:///path/to/file.py @streamlit_app_stage/ auto_compress=false overwrite=true;

-- Remove file:
REMOVE @streamlit_app_stage/filename.py;

-- Clear entire stage:
REMOVE @streamlit_app_stage/;

-- Download file:
GET @streamlit_app_stage/app.py file:///local/path/;

-- Check stage properties:
DESC STAGE streamlit_app_stage;

-- Grant permissions:
GRANT READ, WRITE ON STAGE streamlit_app_stage TO ROLE TRAINING_APP_ROLE;

-- ========================================================================
-- SUMMARY
-- ========================================================================

/*
TO UPLOAD YOUR STREAMLIT FILES:

1. EASIEST METHOD (WebUI):
   - Snowflake UI → Data → Databases → TRAINING_DB → Stages → streamlit_app_stage
   - Click "Upload Files"
   - Select: app.py, config.py, requirements.txt
   - Done! ✓

2. COMMAND LINE (SnowSQL):
   snowsql -a <account> -u <user> -w TRAINING_WH -d TRAINING_DB -s PUBLIC
   PUT file:///workspaces/ai-personal-trainer/streamlit_app/app.py @streamlit_app_stage/ auto_compress=false overwrite=true;
   PUT file:///workspaces/ai-personal-trainer/streamlit_app/config.py @streamlit_app_stage/ auto_compress=false overwrite=true;
   PUT file:///workspaces/ai-personal-trainer/streamlit_app/requirements.txt @streamlit_app_stage/ auto_compress=false overwrite=true;
   LIST @streamlit_app_stage;

3. SQL QUERY:
   -- Run in Snowflake WebUI
   -- PUT command (but WebUI doesn't support PUT directly, use SnowSQL)

VERIFY:
   LIST @streamlit_app_stage;
   -- Should show your 3 files with sizes

NEXT STEPS:
   1. Upload files to stage
   2. Run sql/06_create_streamlit_app.sql
   3. App automatically uses files from stage
   4. Test in Snowflake UI
*/

-- ========================================================================
-- FINAL VERIFICATION
-- ========================================================================

-- After uploading files, verify they're accessible:
SELECT 
  RELATIVE_PATH,
  FILE_SIZE,
  LAST_MODIFIED
FROM TABLE(LIST(BUILD_SCOPED_FILE_URL(@streamlit_app_stage, '')))
ORDER BY LAST_MODIFIED DESC;

-- If you see your files here, you're all set! ✓
