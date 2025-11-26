# AI Personal Trainer - Deployment Checklist

## Pre-Deployment Requirements

- [ ] Snowflake account with ACCOUNTADMIN access
- [ ] Snowflake credits available (minimum 2 for initial deployment)
- [ ] SQL editor (Snowflake WebUI, SnowSQL, DBeaver, VS Code, etc.)
- [ ] YAML configuration reviewed: `../prompts/streamlit_native_snowflake_app.yaml`

---

## Deployment Steps

### Phase 1: Preparation (5 min)

- [ ] Connect to Snowflake as ACCOUNTADMIN
- [ ] Verify account is active and has available credits
- [ ] Open a new worksheet/query editor
- [ ] Copy entire contents of `00_master_deployment.sql`
- [ ] Verify no errors in clipboard

### Phase 2: Execute Master Deployment (2-3 min)

- [ ] Paste `00_master_deployment.sql` into editor
- [ ] Review for any account-specific customizations (optional)
- [ ] Execute entire script
- [ ] **Wait for completion** (all queries must succeed)
- [ ] Check for any error messages in output
- [ ] Verify final output shows "SHOW TABLES;" results

**Expected Output:**
```
Database TRAINING_DB created
Schema PUBLIC created
Warehouse TRAINING_WH created
Roles created
All 14 tables created with 0 rows
All indexes created
All foreign keys validated
SHOW TABLES returns 16 objects (14 tables + 2 system)
```

### Phase 3: Validation (5-10 min)

- [ ] Open new worksheet
- [ ] Copy entire contents of `05_validation_and_testing.sql`
- [ ] Execute entire script
- [ ] **Review output carefully:**

**Expected Results:**
```
✅ STEP 1: All objects listed (SHOW TABLES output)
✅ STEP 2: Foreign keys displayed (all relationships shown)
✅ STEP 3: Sample data inserted (no errors)
✅ STEP 4: Sample data returned (rows visible in SELECT results)
✅ STEP 5: Views execute and return data
✅ STEP 6: Data quality checks return 0 orphaned records
✅ STEP 7: Performance test queries run under 1 second
```

### Phase 4: Smoke Testing (2 min)

Run these quick checks:

- [ ] Count tables: Should return `14` (or more with system tables)
  ```sql
  SELECT COUNT(*) AS table_count FROM INFORMATION_SCHEMA.TABLES 
  WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_CATALOG = 'TRAINING_DB' AND TABLE_TYPE = 'BASE TABLE';
  ```

- [ ] Verify sample data: Should return 1 row each
  ```sql
  SELECT COUNT(*) FROM CLIENTS;
  SELECT COUNT(*) FROM TRAINERS;
  SELECT COUNT(*) FROM EXERCISES;
  ```

- [ ] Test a view: Should return 1 row
  ```sql
  SELECT * FROM CLIENT_PROGRESS_SUMMARY;
  ```

- [ ] Check tasks exist: Should return 3 tasks
  ```sql
  SHOW TASKS;
  ```

### Phase 5: Post-Deployment (2 min)

- [ ] Warehouse running: `SHOW WAREHOUSES LIKE 'TRAINING_WH';`
- [ ] Roles created: `SHOW ROLES LIKE 'TRAINING_APP%';`
- [ ] Database ready: `USE TRAINING_DB; SELECT * FROM INFORMATION_SCHEMA.SCHEMATA;`
- [ ] Note warehouse name, database name for Streamlit config
- [ ] Document connection details for app team

---

## Connection Details (Save These)

After successful deployment, document:

```
Database:     TRAINING_DB
Schema:       PUBLIC
Warehouse:    TRAINING_WH
Role (App):   TRAINING_APP_ROLE
Role (Admin): TRAINING_APP_ADMIN

Snowflake Account ID: ________________
Connection String:   ________________
```

---

## Cleanup of Sample Data (Optional)

If you want to remove sample data and start fresh:

```sql
-- Run these in order
DELETE FROM WORKOUT_EXERCISES WHERE workout_id = 'wo_001';
DELETE FROM WORKOUTS WHERE workout_id = 'wo_001';
DELETE FROM RUNNING_SESSIONS WHERE run_id = 'run_001';
DELETE FROM WEIGH_INS WHERE weigh_in_id = 'wi_001';
DELETE FROM BODY_MEASUREMENTS WHERE measurement_id = 'bm_001';
DELETE FROM NUTRITION_LOGS WHERE log_id = 'nl_001';
DELETE FROM MEAL_PLANS WHERE meal_plan_id = 'mp_001';
DELETE FROM TRAINING_PROGRAMS WHERE program_id = 'tp_001';
DELETE FROM SESSIONS WHERE session_id = 'sess_001';
DELETE FROM RECIPE_INGREDIENTS WHERE recipe_id = 'recipe_001';
DELETE FROM RECIPES WHERE recipe_id = 'recipe_001';
DELETE FROM EXERCISES WHERE exercise_id IN ('exe_001', 'exe_002', 'exe_003');
DELETE FROM CLIENTS WHERE client_id = 'client_001';
DELETE FROM TRAINERS WHERE trainer_id = 'trainer_001';
```

---

## Common Issues & Fixes

### Issue: "Database TRAINING_DB already exists"
**Fix:** This is OK - scripts use `CREATE IF NOT EXISTS`. Continue.

### Issue: "Permission denied" errors
**Fix:** 
- Verify you're logged in as ACCOUNTADMIN
- Run: `GRANT ROLE TRAINING_APP_ROLE TO ROLE SYSADMIN;`

### Issue: Warehouse won't start
**Fix:**
- Verify sufficient credits available
- Check account status in Snowflake admin panel
- Resume manually: `ALTER WAREHOUSE TRAINING_WH RESUME;`

### Issue: Sample data insert fails
**Fix:**
- Ensure all master deployment completed successfully
- Check for duplicate UUIDs (very rare): run again with fresh UUIDs
- Verify foreign keys exist: `SELECT COUNT(*) FROM CLIENTS;` should be > 0

### Issue: Tasks show SUSPENDED status
**Fix:**
- Resume all: 
  ```sql
  ALTER TASK TASK_REFRESH_DAILY_METRICS RESUME;
  ALTER TASK TASK_ARCHIVE_OLD_RECORDS RESUME;
  ALTER TASK TASK_DATA_QUALITY_CHECK RESUME;
  ```

### Issue: Views return no data
**Fix:**
- This is normal before data is loaded
- Run `05_validation_and_testing.sql` to load sample data
- Then views will return results

---

## Success Criteria

✅ **Deployment is successful if:**

1. All SQL executes without errors
2. 14 core tables exist and are empty (0 rows after initial setup)
3. 5 views are created and queryable
4. 3 tasks appear in task list
5. 2 procedures are listed
6. Foreign keys validate (no orphaned records possible)
7. Sample data loads cleanly (if running validation)
8. All views return data after sample insert
9. Database and warehouse accessible
10. Roles configured with proper grants

---

## Performance Targets

After deployment, these queries should complete in < 1 second:

```sql
SELECT * FROM CLIENTS WHERE client_id = 'client_001';                    -- Should be instant
SELECT * FROM WORKOUTS WHERE client_id = 'client_001' AND date = CURRENT_DATE;  -- Should be fast
SELECT * FROM RUNNING_SESSIONS WHERE client_id = 'client_001' ORDER BY date DESC LIMIT 10;  -- Fast
SELECT * FROM CLIENT_PROGRESS_SUMMARY WHERE client_id = 'client_001';    -- View should be instant
```

If queries are slow:
- Check warehouse is running (not suspended)
- Verify indexes were created: `SHOW INDEXES;`
- Check warehouse size (XSMALL OK for < 1M rows)

---

## Cost Estimation

Snowflake charges for:
- **Compute:** Warehouse XSMALL = ~1 credit/hour (~$2-4/hour)
- **Storage:** 14 tables with 1M rows ≈ 100 MB = ~$0.01/month
- **Tasks:** Minimal cost, included in warehouse time

**Deployment Cost:** ~$0.50 for initial setup + testing

---

## Next Steps After Deployment

Once deployment succeeds:

1. **Build Streamlit App**
   - Use connection string from "Connection Details" above
   - Reference forms from: `../prompts/streamlit_native_snowflake_app.yaml`
   - Connect using `TRAINING_APP_ROLE`

2. **Load Production Data**
   - Create scripts to insert real trainers and clients
   - Use `QUICK_REFERENCE.sql` for INSERT examples
   - Validate data quality

3. **Configure AI Integration**
   - Generate suggested values via OpenAI API
   - Store in `suggested_*` columns
   - Let Streamlit form collect actual values

4. **Set Up Monitoring**
   - Query `APP_LOGS` table regularly
   - Monitor warehouse credit usage
   - Review data quality check results

5. **Tune Performance** (if needed)
   - Add clustering on high-volume tables
   - Create materialized views for dashboard queries
   - Implement query caching in Streamlit

---

## Documentation References

- **Full Guide:** `README.md`
- **Summary:** `DEPLOYMENT_SUMMARY.md`
- **Quick Queries:** `QUICK_REFERENCE.sql`
- **Navigation:** `INDEX.md`
- **Master Script:** `00_master_deployment.sql`
- **Validation:** `05_validation_and_testing.sql`

---

## Deployment Sign-Off

```
Deployed By:        ___________________________
Date:               ___________________________
Time:               ___________________________
Deployment Method:  [ ] Master Script  [ ] Step-by-Step  [ ] Other: _______
All Checks Passed:  [ ] YES  [ ] NO
Issues Found:       ___________________________
Notes:              ___________________________
```

---

**Total Estimated Time:** 15-20 minutes  
**Difficulty Level:** Beginner-Intermediate  
**Prerequisites:** ACCOUNTADMIN access  
**Rollback:** Drop TRAINING_DB (entire database)  

**Ready to deploy? Start with `00_master_deployment.sql`** ✅
