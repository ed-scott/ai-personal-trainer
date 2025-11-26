-- ============================================================================
-- AI Personal Trainer - Validation and Testing Script
-- Purpose: Validate schema integrity, FK relationships, and sample data loading
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: Verify All Objects Created Successfully
-- ============================================================================

SHOW TABLES;
SHOW VIEWS;
SHOW PROCEDURES;

-- Detailed table inventory
SELECT 
  TABLE_NAME,
  ROW_COUNT,
  BYTES,
  CREATED,
  LAST_ALTERED
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_CATALOG = 'TRAINING_DB' AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- ============================================================================
-- STEP 2: Verify Foreign Key Relationships
-- ============================================================================

SELECT 
  CONSTRAINT_NAME,
  TABLE_NAME,
  COLUMN_NAME,
  REFERENCED_TABLE_NAME,
  REFERENCED_COLUMN_NAME,
  CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'PUBLIC' 
  AND TABLE_CATALOG = 'TRAINING_DB' 
  AND CONSTRAINT_TYPE IN ('PRIMARY KEY', 'FOREIGN KEY')
ORDER BY TABLE_NAME, CONSTRAINT_NAME;

-- ============================================================================
-- STEP 3: Test Data Insertion (Sample Data)
-- ============================================================================

-- Insert sample trainer
INSERT INTO TRAINERS (trainer_id, name, email, phone, bio, certifications)
SELECT
  'trainer_001',
  'John Smith',
  'john.smith@example.com',
  '555-0001',
  'Certified personal trainer with 10 years of experience',
  PARSE_JSON('[\"NASM\", \"ACE\", \"ISSF\"]');

-- Insert sample client
INSERT INTO CLIENTS (client_id, first_name, last_name, email, phone, dob, gender, timezone)
VALUES (
  'client_001',
  'Jane',
  'Doe',
  'jane.doe@example.com',
  '555-0002',
  '1990-01-15'::DATE,
  'Female',
  'US/Eastern'
);

-- Insert sample exercises
INSERT INTO EXERCISES (exercise_id, name, category, primary_muscles, instructions, equipment)
SELECT 'exe_001', 'Barbell Squat', 'strength', PARSE_JSON('["quadriceps", "glutes", "hamstrings"]'), 'Stand with feet shoulder-width apart, lower body by bending knees and hips', 'Barbell'
UNION ALL
SELECT 'exe_002', 'Bench Press', 'strength', PARSE_JSON('["chest", "shoulders", "triceps"]'), 'Lie on flat bench, push weight away from chest', 'Barbell'
UNION ALL
SELECT 'exe_003', 'Running', 'cardio', PARSE_JSON('["legs", "cardiovascular"]'), 'Sustained aerobic running', 'None';

-- Insert sample workout
INSERT INTO WORKOUTS (workout_id, client_id, trainer_id, date, start_time, type, notes)
VALUES (
  'wo_001',
  'client_001',
  'trainer_001',
  CURRENT_DATE,
  CURRENT_TIMESTAMP,
  'gym',
  'Lower body strength day'
);

-- Insert workout exercises with suggested values
INSERT INTO WORKOUT_EXERCISES 
  (id, workout_id, exercise_id, order_index, suggested_sets, suggested_reps, suggested_weight_kg)
VALUES
  ('we_001', 'wo_001', 'exe_001', 1, 4, '8-10', 120.0),
  ('we_002', 'wo_001', 'exe_002', 2, 3, '10-12', 80.0);

-- Insert actual performance data
UPDATE WORKOUT_EXERCISES
SET actual_sets = 4, actual_reps = '8-10', actual_weight_kg = 120.0, rpe = 8.5
WHERE id = 'we_001';

UPDATE WORKOUT_EXERCISES
SET actual_sets = 3, actual_reps = '10', actual_weight_kg = 80.0, rpe = 7.0
WHERE id = 'we_002';

-- Insert sample running session
INSERT INTO RUNNING_SESSIONS 
  (run_id, client_id, trainer_id, date, suggested_distance_km, suggested_pace_sec_per_km, suggested_type,
   actual_distance_km, actual_duration_sec, actual_type, device)
VALUES (
  'run_001',
  'client_001',
  'trainer_001',
  CURRENT_DATE,
  5.0,
  360.0,
  'easy',
  5.2,
  1900,
  'easy',
  'Garmin Forerunner 945'
);

-- Calculate actual pace
UPDATE RUNNING_SESSIONS
SET actual_pace_sec_per_km = ROUND(actual_duration_sec / actual_distance_km, 2)
WHERE run_id = 'run_001';

-- Insert sample weigh-in
INSERT INTO WEIGH_INS 
  (weigh_in_id, client_id, date, weight_kg, body_fat_pct, muscle_mass_kg, entry_source, entered_by)
VALUES (
  'wi_001',
  'client_001',
  CURRENT_DATE,
  68.5,
  22.5,
  50.2,
  'manual',
  'trainer_001'
);

-- Insert sample body measurements
INSERT INTO BODY_MEASUREMENTS 
  (measurement_id, client_id, date, neck_cm, chest_cm, waist_cm, hip_cm, thigh_cm, calf_cm)
VALUES (
  'bm_001',
  'client_001',
  CURRENT_DATE,
  38.0,
  95.0,
  75.0,
  92.0,
  58.0,
  38.0
);

-- Insert sample recipe
INSERT INTO RECIPES 
  (recipe_id, name, servings, total_calories, macronutrients, ingredients, steps, tags, prep_time_min, cook_time_min, created_by)
SELECT
  'recipe_001',
  'Grilled Chicken Breast with Vegetables',
  1,
  450,
  PARSE_JSON('{"protein": 45, "carbs": 30, "fat": 12}'),
  PARSE_JSON('[{"name": "chicken breast", "quantity": "200g"}, {"name": "broccoli", "quantity": "150g"}, {"name": "olive oil", "quantity": "1 tbsp"}]'),
  PARSE_JSON('["Preheat grill to 400F", "Season chicken with salt and pepper", "Grill for 6-8 minutes per side", "Grill vegetables until tender"]'),
  PARSE_JSON('["high_protein", "low_carb", "healthy"]'),
  5,
  15,
  'trainer_001';

-- Insert nutrition log
INSERT INTO NUTRITION_LOGS 
  (log_id, client_id, date, meal_time, recipe_id, calories, macros, raw_entry)
SELECT
  'nl_001',
  'client_001',
  CURRENT_DATE,
  CURRENT_TIMESTAMP,
  'recipe_001',
  450,
  PARSE_JSON('{"protein": 45, "carbs": 30, "fat": 12}'),
  'Lunch: Grilled chicken with broccoli';

-- Insert meal plan
INSERT INTO MEAL_PLANS 
  (meal_plan_id, client_id, trainer_id, name, start_date, end_date, goals, metadata)
SELECT
  'mp_001',
  'client_001',
  'trainer_001',
  'Weight Loss - Week 1',
  CURRENT_DATE,
  DATEADD(WEEK, 1, CURRENT_DATE),
  PARSE_JSON('{"target_daily_calories": 1800, "target_protein_g": 150}'),
  PARSE_JSON('{"priority": "weight_loss", "restrictions": ["gluten_free"]}');

-- Insert training program
INSERT INTO TRAINING_PROGRAMS 
  (program_id, name, client_id, trainer_id, duration_weeks, description, structure)
SELECT
  'tp_001',
  'Full Body Strength - 8 Weeks',
  'client_001',
  'trainer_001',
  8,
  'Progressive strength training program focused on compound movements',
  PARSE_JSON('{"weeks": [{"week": 1, "focus": "technique"}, {"week": 2, "focus": "hypertrophy"}]}');

-- Insert training session
INSERT INTO SESSIONS 
  (session_id, client_id, trainer_id, start_time, end_time, session_type, notes)
VALUES (
  'sess_001',
  'client_001',
  'trainer_001',
  CURRENT_TIMESTAMP,
  DATEADD(HOUR, 1, CURRENT_TIMESTAMP),
  'In-Person',
  'Initial assessment and goal setting'
);

-- ============================================================================
-- STEP 4: Verify Sample Data
-- ============================================================================

SELECT * FROM TRAINERS;
SELECT * FROM CLIENTS;
SELECT * FROM EXERCISES LIMIT 5;
SELECT * FROM WORKOUTS;
SELECT * FROM WORKOUT_EXERCISES;
SELECT * FROM RUNNING_SESSIONS;
SELECT * FROM WEIGH_INS;
SELECT * FROM BODY_MEASUREMENTS;
SELECT * FROM RECIPES;
SELECT * FROM NUTRITION_LOGS;
SELECT * FROM MEAL_PLANS;
SELECT * FROM TRAINING_PROGRAMS;
SELECT * FROM SESSIONS;

-- ============================================================================
-- STEP 5: Test View Queries
-- ============================================================================

SELECT * FROM CLIENT_PROGRESS_SUMMARY;
SELECT * FROM TRAINER_WORKLOAD_SUMMARY;
SELECT * FROM EXERCISE_PERFORMANCE_ANALYSIS;
SELECT * FROM RUNNING_PERFORMANCE_COMPARISON;
SELECT * FROM RECENT_WEIGHIN_TRENDS;

-- ============================================================================
-- STEP 6: Data Quality Checks
-- ============================================================================

-- Check for NULL primary keys (should be 0)
SELECT 'CLIENTS - NULL PKs' AS check_name, COUNT(*) AS count 
FROM CLIENTS WHERE client_id IS NULL
UNION ALL
SELECT 'TRAINERS - NULL PKs', COUNT(*) FROM TRAINERS WHERE trainer_id IS NULL
UNION ALL
SELECT 'EXERCISES - NULL PKs', COUNT(*) FROM EXERCISES WHERE exercise_id IS NULL
UNION ALL
SELECT 'WORKOUTS - NULL PKs', COUNT(*) FROM WORKOUTS WHERE workout_id IS NULL
UNION ALL
SELECT 'RUNNING_SESSIONS - NULL PKs', COUNT(*) FROM RUNNING_SESSIONS WHERE run_id IS NULL
UNION ALL
SELECT 'WEIGH_INS - NULL PKs', COUNT(*) FROM WEIGH_INS WHERE weigh_in_id IS NULL;

-- Check for orphaned foreign keys in WORKOUTS
SELECT COUNT(*) AS orphaned_client_refs
FROM WORKOUTS w
WHERE NOT EXISTS (SELECT 1 FROM CLIENTS c WHERE c.client_id = w.client_id);

-- Check for orphaned foreign keys in WORKOUT_EXERCISES
SELECT COUNT(*) AS orphaned_workout_refs
FROM WORKOUT_EXERCISES we
WHERE NOT EXISTS (SELECT 1 FROM WORKOUTS w WHERE w.workout_id = we.workout_id);

-- ============================================================================
-- STEP 7: Performance Test Queries
-- ============================================================================

-- Fast index query by client and date
SELECT COUNT(*) FROM WORKOUTS WHERE client_id = 'client_001' AND date = CURRENT_DATE;

-- Running performance comparison
SELECT 
  suggested_distance_km,
  actual_distance_km,
  ROUND((actual_distance_km - suggested_distance_km), 3) AS variance_km
FROM RUNNING_SESSIONS
WHERE actual_distance_km IS NOT NULL;

-- Aggregation query
SELECT 
  client_id,
  COUNT(DISTINCT workout_id) AS total_workouts,
  COUNT(DISTINCT run_id) AS total_runs,
  MAX(weight_kg) AS max_weight,
  MIN(weight_kg) AS min_weight
FROM (
  SELECT client_id, workout_id, NULL::VARCHAR AS run_id, NULL::NUMBER AS weight_kg FROM WORKOUTS
  UNION ALL
  SELECT client_id, NULL::VARCHAR, run_id, NULL::NUMBER FROM RUNNING_SESSIONS
  UNION ALL
  SELECT client_id, NULL::VARCHAR, NULL::VARCHAR, weight_kg FROM WEIGH_INS
)
GROUP BY client_id;

-- ============================================================================
-- CLEANUP (Comment out to keep test data)
-- ============================================================================

-- DELETE FROM WORKOUT_EXERCISES WHERE workout_id = 'wo_001';
-- DELETE FROM WORKOUTS WHERE workout_id = 'wo_001';
-- DELETE FROM RUNNING_SESSIONS WHERE run_id = 'run_001';
-- DELETE FROM WEIGH_INS WHERE weigh_in_id = 'wi_001';
-- DELETE FROM BODY_MEASUREMENTS WHERE measurement_id = 'bm_001';
-- DELETE FROM NUTRITION_LOGS WHERE log_id = 'nl_001';
-- DELETE FROM MEAL_PLANS WHERE meal_plan_id = 'mp_001';
-- DELETE FROM TRAINING_PROGRAMS WHERE program_id = 'tp_001';
-- DELETE FROM SESSIONS WHERE session_id = 'sess_001';
-- DELETE FROM RECIPES WHERE recipe_id = 'recipe_001';
-- DELETE FROM EXERCISES WHERE exercise_id IN ('exe_001', 'exe_002', 'exe_003');
-- DELETE FROM CLIENTS WHERE client_id = 'client_001';
-- DELETE FROM TRAINERS WHERE trainer_id = 'trainer_001';

-- ============================================================================
-- FINAL SUMMARY
-- ============================================================================

SHOW TABLES;
SELECT COUNT(*) AS table_count FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_CATALOG = 'TRAINING_DB' AND TABLE_TYPE = 'BASE TABLE';
