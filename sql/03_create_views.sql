-- ============================================================================
-- AI Personal Trainer - Views and Materialized Objects
-- Purpose: Create views for analytics and reporting
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ============================================================================
-- MATERIALIZED VIEW: Daily Client Activity Metrics
-- ============================================================================

CREATE OR REPLACE TABLE DAILY_CLIENT_METRICS AS
SELECT 
  client_id,
  CAST(CURRENT_DATE AS DATE) AS day,
  COUNT(DISTINCT workout_id) AS workouts_count,
  SUM(CAST(DATEDIFF(SECOND, start_time, CURRENT_TIMESTAMP) / 60.0 AS NUMBER(6,2))) AS total_minutes,
  COUNT(DISTINCT CASE WHEN type = 'gym' THEN workout_id END) AS gym_workouts,
  COUNT(DISTINCT CASE WHEN type != 'gym' THEN workout_id END) AS other_workouts
FROM WORKOUTS
WHERE DATE(start_time) = CURRENT_DATE
GROUP BY client_id;

COMMENT ON TABLE DAILY_CLIENT_METRICS IS 'Aggregated daily activity metrics per client (gym vs other workouts, duration)';
GRANT SELECT ON DAILY_CLIENT_METRICS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- VIEW: Client Progress Summary
-- ============================================================================

CREATE OR REPLACE VIEW CLIENT_PROGRESS_SUMMARY AS
SELECT 
  c.client_id,
  c.first_name,
  c.last_name,
  c.email,
  (SELECT weight_kg FROM WEIGH_INS WHERE client_id = c.client_id ORDER BY date DESC LIMIT 1) AS latest_weight_kg,
  (SELECT date FROM WEIGH_INS WHERE client_id = c.client_id ORDER BY date DESC LIMIT 1) AS latest_weigh_in_date,
  (SELECT 
    COALESCE(weight_kg, 0) - 
    COALESCE((SELECT weight_kg FROM WEIGH_INS WHERE client_id = c.client_id ORDER BY date ASC LIMIT 1), 0)
   FROM WEIGH_INS WHERE client_id = c.client_id ORDER BY date DESC LIMIT 1) AS total_weight_change_kg,
  COUNT(DISTINCT w.workout_id) AS total_workouts,
  COUNT(DISTINCT rs.run_id) AS total_runs,
  MAX(w.date) AS last_workout_date,
  MAX(rs.date) AS last_run_date
FROM CLIENTS c
LEFT JOIN WORKOUTS w ON c.client_id = w.client_id
LEFT JOIN RUNNING_SESSIONS rs ON c.client_id = rs.client_id
GROUP BY c.client_id, c.first_name, c.last_name, c.email;

COMMENT ON VIEW CLIENT_PROGRESS_SUMMARY IS 'Client overview with latest weight, activity counts, and progress trends';
GRANT SELECT ON CLIENT_PROGRESS_SUMMARY TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- VIEW: Trainer Workload Summary
-- ============================================================================

CREATE OR REPLACE VIEW TRAINER_WORKLOAD_SUMMARY AS
SELECT 
  t.trainer_id,
  t.name,
  t.email,
  COUNT(DISTINCT t1.client_id) AS active_clients,
  COUNT(DISTINCT t1.workout_id) AS total_workouts,
  COUNT(DISTINCT s.session_id) AS total_sessions,
  MAX(s.start_time) AS last_session
FROM TRAINERS t
LEFT JOIN WORKOUTS t1 ON t.trainer_id = t1.trainer_id
LEFT JOIN SESSIONS s ON t.trainer_id = s.trainer_id
GROUP BY t.trainer_id, t.name, t.email;

COMMENT ON VIEW TRAINER_WORKLOAD_SUMMARY IS 'Trainer overview showing client count, workout count, and session activity';
GRANT SELECT ON TRAINER_WORKLOAD_SUMMARY TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- VIEW: Exercise Performance Analysis
-- ============================================================================

CREATE OR REPLACE VIEW EXERCISE_PERFORMANCE_ANALYSIS AS
SELECT 
  e.exercise_id,
  e.name,
  e.category,
  COUNT(DISTINCT we.workout_id) AS times_prescribed,
  COUNT(DISTINCT CASE WHEN we.actual_sets IS NOT NULL THEN we.workout_id END) AS times_completed,
  ROUND(
    COUNT(DISTINCT CASE WHEN we.actual_sets IS NOT NULL THEN we.workout_id END) * 100.0 / 
    NULLIF(COUNT(DISTINCT we.workout_id), 0), 2
  ) AS completion_rate_pct,
  ROUND(AVG(we.actual_weight_kg), 2) AS avg_actual_weight_kg,
  ROUND(AVG(we.suggested_weight_kg), 2) AS avg_suggested_weight_kg,
  ROUND(AVG(we.rpe), 2) AS avg_rpe
FROM EXERCISES e
LEFT JOIN WORKOUT_EXERCISES we ON e.exercise_id = we.exercise_id
GROUP BY e.exercise_id, e.name, e.category;

COMMENT ON VIEW EXERCISE_PERFORMANCE_ANALYSIS IS 'Exercise analytics showing completion rates and performance metrics';
GRANT SELECT ON EXERCISE_PERFORMANCE_ANALYSIS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- VIEW: Running Performance Comparison (Suggested vs Actual)
-- ============================================================================

CREATE OR REPLACE VIEW RUNNING_PERFORMANCE_COMPARISON AS
SELECT 
  client_id,
  date,
  suggested_distance_km,
  actual_distance_km,
  ROUND((actual_distance_km - suggested_distance_km), 3) AS distance_variance_km,
  suggested_pace_sec_per_km,
  actual_pace_sec_per_km,
  ROUND((actual_pace_sec_per_km - suggested_pace_sec_per_km), 2) AS pace_variance_sec_per_km,
  suggested_type,
  actual_type,
  calories,
  device,
  CASE 
    WHEN actual_distance_km >= suggested_distance_km THEN 'Exceeded'
    WHEN actual_distance_km >= (suggested_distance_km * 0.9) THEN 'Met'
    ELSE 'Below Target'
  END AS performance_status
FROM RUNNING_SESSIONS
WHERE actual_distance_km IS NOT NULL
ORDER BY client_id, date DESC;

COMMENT ON VIEW RUNNING_PERFORMANCE_COMPARISON IS 'Running session analysis comparing suggested vs actual performance';
GRANT SELECT ON RUNNING_PERFORMANCE_COMPARISON TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- VIEW: Recent Client Weigh-In Trends
-- ============================================================================

CREATE OR REPLACE VIEW RECENT_WEIGHIN_TRENDS AS
SELECT 
  c.client_id,
  c.first_name || ' ' || c.last_name AS full_name,
  wi.date,
  wi.weight_kg,
  wi.body_fat_pct,
  wi.muscle_mass_kg,
  wi.notes,
  wi.entry_source,
  LAG(wi.weight_kg) OVER (PARTITION BY c.client_id ORDER BY wi.date) AS prev_weight_kg,
  ROUND(wi.weight_kg - LAG(wi.weight_kg) OVER (PARTITION BY c.client_id ORDER BY wi.date), 3) AS weight_change_kg,
  DATEDIFF(DAY, LAG(wi.date) OVER (PARTITION BY c.client_id ORDER BY wi.date), wi.date) AS days_since_last_weigh_in
FROM CLIENTS c
INNER JOIN WEIGH_INS wi ON c.client_id = wi.client_id
WHERE wi.date >= DATEADD(DAY, -90, CURRENT_DATE)
ORDER BY c.client_id, wi.date DESC;

COMMENT ON VIEW RECENT_WEIGHIN_TRENDS IS 'Recent weigh-in data with weight change tracking (last 90 days)';
GRANT SELECT ON RECENT_WEIGHIN_TRENDS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Verification
-- ============================================================================

SHOW TABLES IN SCHEMA TRAINING_DB.PUBLIC;
SHOW VIEWS IN SCHEMA TRAINING_DB.PUBLIC;

-- Test view queries (should return empty initially)
SELECT * FROM CLIENT_PROGRESS_SUMMARY LIMIT 5;
SELECT * FROM TRAINER_WORKLOAD_SUMMARY LIMIT 5;
SELECT * FROM EXERCISE_PERFORMANCE_ANALYSIS LIMIT 5;
