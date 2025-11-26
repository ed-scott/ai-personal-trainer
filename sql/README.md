# AI Personal Trainer - Snowflake Deployment Guide

## Overview

This SQL package deploys a complete Snowflake application for an AI-powered personal training system. It includes:

- **14 core data tables** (clients, trainers, workouts, running_sessions, weigh_ins, meals, recipes, etc.)
- **5 analytical views** (progress summaries, performance analysis, trends)
- **3 Snowflake tasks** (daily metrics aggregation, data quality checks, archival)
- **2 helper procedures** (running pace calculation, workout logging)
- **Role-based access control** (TRAINING_APP_ROLE, TRAINING_APP_ADMIN)
- **Search optimization** on key tables
- **Comprehensive foreign key relationships** with CASCADE delete where appropriate

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `00_master_deployment.sql` | **START HERE** - Complete deployment script with all objects in correct order |
| `01_setup_database_and_roles.sql` | Database, warehouse, roles, and permissions setup |
| `02_create_core_tables.sql` | All 14 core tables with indexes and comments |
| `03_create_views.sql` | 5 analytical views for reporting and analysis |
| `04_create_tasks_and_procedures.sql` | Scheduled tasks and helper stored procedures |
| `05_validation_and_testing.sql` | Comprehensive validation, sample data, and testing queries |

---

## Quick Start (Recommended)

### Step 1: Connect to Snowflake

Open Snowflake WebUI or use SnowSQL:

```bash
snowsql -a <account_id> -u <username>
```

Or use VS Code extension, DBeaver, or your preferred Snowflake client.

### Step 2: Run Master Deployment

Copy and paste the entire contents of **`00_master_deployment.sql`** into your Snowflake worksheet and execute.

**Expected output:**
- Database `TRAINING_DB` created
- Schema `PUBLIC` created
- Warehouse `TRAINING_WH` created
- Roles `TRAINING_APP_ROLE` and `TRAINING_APP_ADMIN` created
- All 14 tables created successfully
- All indexes and foreign keys in place
- 0 rows in each table (empty, ready for data)

### Step 3: Validate Deployment

Run **`05_validation_and_testing.sql`** to:
- Verify all objects were created
- Insert sample data (trainer, client, workouts, runs, weigh-ins, etc.)
- Test views and aggregation queries
- Confirm foreign key integrity

**Expected output:**
- 14 tables with 0 initial rows (after setup)
- 5 views accessible and queryable
- Sample data inserted successfully
- All views return expected results
- No orphaned foreign key references

---

## Schema Overview

### Dimension/Reference Tables (No dependencies)
- **CLIENTS** - End users being trained
- **TRAINERS** - Personal trainers managing clients
- **EXERCISES** - Library of exercise definitions

### Fact/Transactional Tables
- **WORKOUTS** - Gym sessions (references CLIENTS, TRAINERS)
- **WORKOUT_EXERCISES** - Individual exercises within workouts (references WORKOUTS, EXERCISES)
- **RUNNING_SESSIONS** - Running/cardio sessions (references CLIENTS, TRAINERS)
- **WEIGH_INS** - Body weight and composition tracking (references CLIENTS)
- **BODY_MEASUREMENTS** - Detailed body measurements (references CLIENTS)

### Nutrition Tables
- **MEAL_PLANS** - Nutrition plans (references CLIENTS, TRAINERS)
- **RECIPES** - Recipe library
- **RECIPE_INGREDIENTS** - Ingredients within recipes (references RECIPES)
- **NUTRITION_LOGS** - Daily nutrition tracking (references CLIENTS, RECIPES)

### Program & Session Tables
- **TRAINING_PROGRAMS** - Multi-week training plans (references CLIENTS, TRAINERS)
- **SESSIONS** - 1:1 training sessions (references CLIENTS, TRAINERS)

### AI/Support Tables
- **AI_EMBEDDINGS** - Vector embeddings for similarity search
- **APP_LOGS** - Application logging and audit trail

---

## Key Design Decisions

### 1. Suggested vs. Actual Values
All workout and running data uses separate fields:
- **Suggested**: AI-generated recommendations (trainers populate)
- **Actual**: Client's actual performance (input via Streamlit)

**Running Sessions:**
```
suggested_distance_km, suggested_pace_sec_per_km, suggested_type
actual_distance_km, actual_duration_sec, actual_pace_sec_per_km, actual_type
```

**Workout Exercises:**
```
suggested_sets, suggested_reps, suggested_weight_kg
actual_sets, actual_reps, actual_weight_kg
```

### 2. Standard Data Types (No VARIANT for Suggested/Actual)
All suggested/actual values use `NUMBER` or `VARCHAR` for:
- Better query performance
- Easier aggregation and analytics
- Schema clarity
- Reduced storage footprint

Complex structures (program hierarchies, instructions, etc.) still use `VARIANT` where appropriate.

### 3. Cascading Deletes
```
WORKOUT_EXERCISES → WORKOUTS (CASCADE)
RECIPE_INGREDIENTS → RECIPES (CASCADE)
```
Deleting a workout automatically removes all associated exercises; deleting a recipe removes ingredients.

### 4. Indexes for Query Performance
Key indexes on:
- `WORKOUTS(client_id, date)` - Fast workout history lookups
- `RUNNING_SESSIONS(client_id, date)` - Fast running history
- `WEIGH_INS(client_id, date DESC)` - Latest weigh-in first
- `NUTRITION_LOGS(client_id, date DESC)` - Latest nutrition first
- Exercise and recipe lookups

---

## Roles and Permissions

### TRAINING_APP_ADMIN
- Full ownership of database and schema
- Can create/alter/drop objects
- Can grant privileges to others
- Can execute tasks

### TRAINING_APP_ROLE
- `SELECT, INSERT, UPDATE, DELETE` on all tables
- `SELECT` on all views
- Cannot modify schema
- Can execute helper procedures
- Suitable for Streamlit app user

---

## Scheduled Tasks

### 1. TASK_REFRESH_DAILY_METRICS
- **Schedule:** Daily at 2 AM UTC
- **Purpose:** Aggregate yesterday's workouts into daily metrics table
- **Status:** Auto-resumes

### 2. TASK_ARCHIVE_OLD_RECORDS
- **Schedule:** Weekly (Monday 3 AM UTC)
- **Purpose:** Archive workouts older than 2 years
- **Status:** Auto-resumes

### 3. TASK_DATA_QUALITY_CHECK
- **Schedule:** Daily at 1 AM UTC
- **Purpose:** Detect orphaned records and log anomalies
- **Status:** Auto-resumes

---

## Helper Procedures

### CALCULATE_RUNNING_PACE(p_run_id)
Auto-calculates average pace from distance and duration:
```sql
CALL CALCULATE_RUNNING_PACE('run_001');
```

### LOG_WORKOUT_COMPLETION(p_workout_id, p_actual_duration_min)
Logs workout completion and creates audit entry:
```sql
CALL LOG_WORKOUT_COMPLETION('wo_001', 60.0);
```

---

## Views for Analytics

### CLIENT_PROGRESS_SUMMARY
Latest weight, weight change, workout/run counts, last activity dates

### TRAINER_WORKLOAD_SUMMARY
Active client count, total workouts, session count per trainer

### EXERCISE_PERFORMANCE_ANALYSIS
Exercise completion rates, avg weights, RPE trends

### RUNNING_PERFORMANCE_COMPARISON
Suggested vs actual running metrics with performance status

### RECENT_WEIGHIN_TRENDS
Last 90 days of weigh-ins with weight changes and time between measurements

---

## Data Loading Examples

### Insert a New Client
```sql
INSERT INTO CLIENTS (client_id, first_name, last_name, email, phone, dob, gender, timezone)
VALUES (
  UUID_STRING(),
  'John',
  'Athlete',
  'john@example.com',
  '555-1234',
  '1995-05-10'::DATE,
  'Male',
  'US/Pacific'
);
```

### Log a Workout
```sql
INSERT INTO WORKOUTS (workout_id, client_id, trainer_id, date, start_time, type)
VALUES (UUID_STRING(), 'client_001', 'trainer_001', CURRENT_DATE, CURRENT_TIMESTAMP, 'gym');

-- Add exercises
INSERT INTO WORKOUT_EXERCISES 
  (id, workout_id, exercise_id, order_index, suggested_sets, suggested_reps, suggested_weight_kg)
VALUES (UUID_STRING(), 'wo_001', 'exe_001', 1, 4, '8-10', 100.0);

-- Update with actual performance
UPDATE WORKOUT_EXERCISES
SET actual_sets = 4, actual_reps = '8-10', actual_weight_kg = 100.0, rpe = 8.0
WHERE workout_id = 'wo_001';
```

### Log a Running Session
```sql
INSERT INTO RUNNING_SESSIONS 
  (run_id, client_id, date, suggested_distance_km, suggested_pace_sec_per_km, suggested_type,
   actual_distance_km, actual_duration_sec, actual_type, device)
VALUES (UUID_STRING(), 'client_001', CURRENT_DATE, 5.0, 360, 'easy', 5.1, 1830, 'easy', 'Garmin');

-- Calculate pace
CALL CALCULATE_RUNNING_PACE('run_001');
```

### Log a Weigh-In
```sql
INSERT INTO WEIGH_INS 
  (weigh_in_id, client_id, date, weight_kg, body_fat_pct, muscle_mass_kg, entry_source, entered_by)
VALUES (UUID_STRING(), 'client_001', CURRENT_DATE, 75.5, 20.0, 55.0, 'manual', 'trainer_001');
```

---

## Snowflake Streamlit App Integration

This schema is designed for **Snowflake Streamlit Native** apps. The `deployment.streamlit_input_forms` section of the YAML defines form fields for:

- **Weigh-in form** - Manual daily/weekly entries
- **Running session form** - Separate suggested/actual sections
- **Workout exercise form** - Track prescribed vs performed

Key integrations:
1. Use `client_id`, `trainer_id` as foreign keys in your Streamlit app
2. Populate `suggested_*` fields from AI service (OpenAI)
3. Collect `actual_*` fields from Streamlit form inputs
4. Timestamps auto-populate with `CURRENT_TIMESTAMP`

---

## Performance Tuning

All tables include search optimization on key lookups:
```sql
ALTER TABLE APP_LOGS ADD SEARCH OPTIMIZATION ON EQUALITY(log_id), SUBSTRING(message);
```

For production, consider:
1. **Materialized views** on high-traffic queries
2. **Clustering** on `client_id` and date columns if > 100M rows
3. **Query results caching** for Streamlit app
4. **Partitioning by date** for very large fact tables

---

## Troubleshooting

### All tables return 0 rows after setup
✓ **Normal** - Start with the testing script to insert sample data.

### Foreign key constraint error during insert
✓ Verify the referenced table has the record. Example:
```sql
INSERT INTO WORKOUTS (client_id, ...) VALUES ('client_001', ...);
-- Will fail if 'client_001' doesn't exist in CLIENTS table
```

### View returns no results
✓ Ensure sample data has been inserted via `05_validation_and_testing.sql`.

### Roles don't have access
✓ Run the master deployment with `ACCOUNTADMIN` role to ensure grants are applied.

### Tasks show SUSPENDED status
✓ Resume with:
```sql
ALTER TASK TASK_NAME RESUME;
```

---

## Cleanup

To remove all objects (use cautiously):

```sql
DROP DATABASE IF EXISTS TRAINING_DB;
DROP ROLE IF EXISTS TRAINING_APP_ROLE;
DROP ROLE IF EXISTS TRAINING_APP_ADMIN;
DROP WAREHOUSE IF EXISTS TRAINING_WH;
```

---

## Next Steps

1. ✅ Run `00_master_deployment.sql`
2. ✅ Run `05_validation_and_testing.sql`
3. ✅ Review sample data in views
4. → Build Streamlit app using forms from YAML
5. → Load production client/trainer data
6. → Set up AI service integration for suggested workouts/runs
7. → Configure email alerts for key metrics

---

## Support

For issues or questions:
1. Check the validation script output for specific errors
2. Verify all foreign keys reference existing records
3. Review Snowflake documentation on roles, tasks, and views
4. Check `APP_LOGS` table for application errors

---

**Version:** 1.0  
**Last Updated:** November 26, 2025  
**Created by:** Snowflake Data Engineering Expert
