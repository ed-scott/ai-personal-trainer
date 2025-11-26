-- ============================================================================
-- QUICK REFERENCE: Common Queries for AI Personal Trainer App
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ============================================================================
-- CLIENT MANAGEMENT
-- ============================================================================

-- Get all clients
SELECT client_id, first_name, last_name, email, timezone FROM CLIENTS ORDER BY last_name;

-- Get client progress
SELECT * FROM CLIENT_PROGRESS_SUMMARY WHERE client_id = 'client_001';

-- Get client's latest weigh-in
SELECT * FROM WEIGH_INS 
WHERE client_id = 'client_001' 
ORDER BY date DESC LIMIT 1;

-- ============================================================================
-- WORKOUT TRACKING
-- ============================================================================

-- Get all workouts for a client this month
SELECT * FROM WORKOUTS 
WHERE client_id = 'client_001' 
  AND date >= DATE_TRUNC(MONTH, CURRENT_DATE)
ORDER BY date DESC;

-- Get workout with exercises and performance
SELECT 
  w.workout_id,
  w.date,
  e.name AS exercise,
  we.suggested_sets, we.suggested_reps, we.suggested_weight_kg,
  we.actual_sets, we.actual_reps, we.actual_weight_kg,
  we.rpe
FROM WORKOUTS w
JOIN WORKOUT_EXERCISES we ON w.workout_id = we.workout_id
JOIN EXERCISES e ON we.exercise_id = e.exercise_id
WHERE w.client_id = 'client_001'
  AND w.date >= DATE_TRUNC(MONTH, CURRENT_DATE)
ORDER BY w.date DESC, we.order_index;

-- Exercise completion analysis
SELECT * FROM EXERCISE_PERFORMANCE_ANALYSIS 
WHERE times_prescribed > 0
ORDER BY completion_rate_pct DESC;

-- ============================================================================
-- RUNNING TRACKING
-- ============================================================================

-- Get all running sessions for a client
SELECT 
  run_id,
  date,
  suggested_distance_km,
  actual_distance_km,
  ROUND((actual_distance_km - suggested_distance_km), 3) AS distance_variance_km,
  ROUND(actual_duration_sec / 60, 1) AS duration_min,
  ROUND(actual_pace_sec_per_km, 1) AS pace_sec_per_km,
  device
FROM RUNNING_SESSIONS
WHERE client_id = 'client_001'
ORDER BY date DESC;

-- Running performance comparison
SELECT * FROM RUNNING_PERFORMANCE_COMPARISON
WHERE client_id = 'client_001'
ORDER BY date DESC;

-- ============================================================================
-- WEIGHT TRACKING
-- ============================================================================

-- Get weigh-in history with trends
SELECT * FROM RECENT_WEIGHIN_TRENDS
WHERE client_id = 'client_001'
ORDER BY date DESC;

-- Weight change over time
SELECT 
  DATEADD(WEEK, -ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date DESC) / 1, CURRENT_DATE) AS week,
  client_id,
  AVG(weight_kg) AS avg_weight,
  MIN(weight_kg) AS min_weight,
  MAX(weight_kg) AS max_weight
FROM WEIGH_INS
WHERE date >= DATEADD(MONTH, -3, CURRENT_DATE)
GROUP BY week, client_id
ORDER BY client_id, week;

-- ============================================================================
-- NUTRITION TRACKING
-- ============================================================================

-- Get client's meals for today
SELECT 
  meal_time,
  r.name AS recipe,
  calories,
  macros
FROM NUTRITION_LOGS nl
LEFT JOIN RECIPES r ON nl.recipe_id = r.recipe_id
WHERE client_id = 'client_001' AND date = CURRENT_DATE
ORDER BY meal_time;

-- Daily calorie total
SELECT 
  DATE(meal_time) AS date,
  client_id,
  SUM(calories) AS total_calories,
  COUNT(*) AS meal_count
FROM NUTRITION_LOGS
GROUP BY DATE(meal_time), client_id
HAVING DATE(meal_time) >= DATE_TRUNC(MONTH, CURRENT_DATE)
ORDER BY date DESC;

-- ============================================================================
-- TRAINER MANAGEMENT
-- ============================================================================

-- Get trainer's workload
SELECT * FROM TRAINER_WORKLOAD_SUMMARY;

-- Get trainer's clients and activity
SELECT 
  t.trainer_id,
  t.name AS trainer,
  c.client_id,
  c.first_name || ' ' || c.last_name AS client_name,
  COUNT(DISTINCT w.workout_id) AS total_workouts,
  COUNT(DISTINCT rs.run_id) AS total_runs,
  MAX(w.date) AS last_workout,
  MAX(rs.date) AS last_run
FROM TRAINERS t
LEFT JOIN WORKOUTS w ON t.trainer_id = w.trainer_id
LEFT JOIN RUNNING_SESSIONS rs ON t.trainer_id = rs.trainer_id
LEFT JOIN CLIENTS c ON w.client_id = c.client_id OR rs.client_id = c.client_id
WHERE t.trainer_id = 'trainer_001'
GROUP BY t.trainer_id, t.name, c.client_id, c.first_name, c.last_name
ORDER BY trainer, client_name;

-- ============================================================================
-- DATA QUALITY
-- ============================================================================

-- Check for missing actual values (incomplete workouts)
SELECT 
  w.workout_id,
  w.client_id,
  w.date,
  COUNT(*) AS total_exercises,
  SUM(CASE WHEN we.actual_sets IS NULL THEN 1 ELSE 0 END) AS incomplete_exercises
FROM WORKOUTS w
LEFT JOIN WORKOUT_EXERCISES we ON w.workout_id = we.workout_id
GROUP BY w.workout_id, w.client_id, w.date
HAVING incomplete_exercises > 0
ORDER BY w.date DESC;

-- Check for incomplete running sessions
SELECT 
  run_id,
  client_id,
  date,
  CASE 
    WHEN actual_distance_km IS NULL THEN 'Missing distance'
    WHEN actual_duration_sec IS NULL THEN 'Missing duration'
    WHEN actual_type IS NULL THEN 'Missing type'
    ELSE 'Complete'
  END AS completion_status
FROM RUNNING_SESSIONS
WHERE date >= DATEADD(DAY, -30, CURRENT_DATE)
  AND (actual_distance_km IS NULL OR actual_duration_sec IS NULL OR actual_type IS NULL);

-- Recent application logs
SELECT 
  timestamp,
  level,
  source,
  message,
  context
FROM APP_LOGS
WHERE level IN ('ERROR', 'WARNING')
ORDER BY timestamp DESC
LIMIT 20;

-- ============================================================================
-- ANALYTICS & REPORTING
-- ============================================================================

-- Weekly activity summary by client
SELECT 
  DATE_TRUNC(WEEK, date) AS week,
  COUNT(DISTINCT workout_id) AS gym_workouts,
  COUNT(DISTINCT run_id) AS running_sessions,
  ROUND(SUM(DATEDIFF(MINUTE, start_time, DATEADD(SECOND, DATEDIFF(SECOND, 0, start_time + INTERVAL '1 HOUR'), 0))), 1) AS total_gym_minutes,
  ROUND(SUM(actual_duration_sec) / 60, 1) AS total_running_minutes
FROM (
  SELECT workout_id, NULL AS run_id, date, start_time FROM WORKOUTS WHERE start_time IS NOT NULL
  UNION ALL
  SELECT NULL, run_id, date, NULL FROM RUNNING_SESSIONS
)
WHERE date >= DATEADD(MONTH, -3, CURRENT_DATE)
GROUP BY DATE_TRUNC(WEEK, date)
ORDER BY week DESC;

-- Most prescribed exercises
SELECT 
  e.name,
  COUNT(*) AS times_prescribed,
  ROUND(AVG(we.suggested_weight_kg), 2) AS avg_suggested_weight,
  ROUND(AVG(we.actual_weight_kg), 2) AS avg_actual_weight,
  ROUND(AVG(we.rpe), 1) AS avg_rpe
FROM WORKOUT_EXERCISES we
JOIN EXERCISES e ON we.exercise_id = e.exercise_id
WHERE we.workout_id IN (
  SELECT workout_id FROM WORKOUTS 
  WHERE date >= DATEADD(MONTH, -1, CURRENT_DATE)
)
GROUP BY e.name
ORDER BY times_prescribed DESC
LIMIT 10;

-- ============================================================================
-- INSERT EXAMPLES
-- ============================================================================

-- Create new client
-- INSERT INTO CLIENTS (client_id, first_name, last_name, email, phone, dob, gender, timezone)
-- VALUES (UUID_STRING(), 'John', 'Doe', 'john@example.com', '555-1234', '1990-01-01'::DATE, 'Male', 'US/Eastern');

-- Create new trainer
-- INSERT INTO TRAINERS (trainer_id, name, email, phone, bio, certifications)
-- VALUES (UUID_STRING(), 'Jane Smith', 'jane@example.com', '555-5678', 'Expert trainer', PARSE_JSON('["NASM", "ACE"]'));

-- Log workout with exercises
-- DECLARE
--   v_workout_id VARCHAR(36) := UUID_STRING();
-- BEGIN
--   INSERT INTO WORKOUTS (workout_id, client_id, trainer_id, date, start_time, type)
--   VALUES (v_workout_id, 'client_001', 'trainer_001', CURRENT_DATE, CURRENT_TIMESTAMP, 'gym');
--   
--   INSERT INTO WORKOUT_EXERCISES 
--     (id, workout_id, exercise_id, order_index, suggested_sets, suggested_reps, suggested_weight_kg)
--   VALUES 
--     (UUID_STRING(), v_workout_id, 'exe_001', 1, 4, '8-10', 100.0),
--     (UUID_STRING(), v_workout_id, 'exe_002', 2, 3, '10-12', 80.0);
-- END;

-- Log running session
-- INSERT INTO RUNNING_SESSIONS 
--   (run_id, client_id, trainer_id, date, 
--    suggested_distance_km, suggested_pace_sec_per_km, suggested_type,
--    actual_distance_km, actual_duration_sec, actual_type, device)
-- VALUES (UUID_STRING(), 'client_001', 'trainer_001', CURRENT_DATE,
--         5.0, 360, 'easy', 5.1, 1840, 'easy', 'Garmin');

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Show task status
SELECT TASK_NAME, STATE, SCHEDULE_TYPE, LAST_COMPLETED_TIME 
FROM INFORMATION_SCHEMA.TASK_EXECUTIONS
WHERE DATABASE_NAME = 'TRAINING_DB'
ORDER BY LAST_COMPLETED_TIME DESC;

-- Resume all tasks
-- ALTER TASK TASK_REFRESH_DAILY_METRICS RESUME;
-- ALTER TASK TASK_ARCHIVE_OLD_RECORDS RESUME;
-- ALTER TASK TASK_DATA_QUALITY_CHECK RESUME;

-- Clear old logs (keep 90 days)
-- DELETE FROM APP_LOGS WHERE timestamp < DATEADD(DAY, -90, CURRENT_TIMESTAMP);

-- Vacuum and analyze
-- ALTER WAREHOUSE TRAINING_WH REFRESH;

-- ============================================================================
