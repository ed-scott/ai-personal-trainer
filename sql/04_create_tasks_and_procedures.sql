-- ============================================================================
-- AI Personal Trainer - Snowflake Tasks and Automation
-- Purpose: Schedule data aggregations and transformations
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;
USE WAREHOUSE TRAINING_WH;

-- ============================================================================
-- TASK 1: Refresh Daily Metrics (runs daily at 2 AM UTC)
-- ============================================================================

CREATE OR REPLACE TASK TASK_REFRESH_DAILY_METRICS
  WAREHOUSE = TRAINING_WH
  SCHEDULE = 'USING CRON 0 2 * * * UTC'
  COMMENT = 'Aggregate daily client activity metrics'
AS
INSERT INTO DAILY_CLIENT_METRICS
SELECT 
  client_id,
  DATEADD(DAY, -1, CURRENT_DATE) AS day,
  COUNT(DISTINCT workout_id) AS workouts_count,
  SUM(CAST(DATEDIFF(SECOND, start_time, CURRENT_TIMESTAMP) / 60.0 AS NUMBER(6,2))) AS total_minutes,
  COUNT(DISTINCT CASE WHEN type = 'gym' THEN workout_id END) AS gym_workouts,
  COUNT(DISTINCT CASE WHEN type != 'gym' THEN workout_id END) AS other_workouts
FROM WORKOUTS
WHERE DATE(start_time) = DATEADD(DAY, -1, CURRENT_DATE)
GROUP BY client_id
ON CONFLICT DO NOTHING;

-- Alter task to enable it
ALTER TASK TASK_REFRESH_DAILY_METRICS RESUME;

-- ============================================================================
-- TASK 2: Archive old activity records (runs weekly on Monday at 3 AM UTC)
-- ============================================================================

CREATE OR REPLACE TASK TASK_ARCHIVE_OLD_RECORDS
  WAREHOUSE = TRAINING_WH
  SCHEDULE = 'USING CRON 0 3 * * MON UTC'
  COMMENT = 'Archive workout/run records older than 2 years'
AS
DELETE FROM WORKOUTS
WHERE date < DATEADD(YEAR, -2, CURRENT_DATE)
  AND created_at < DATEADD(YEAR, -2, CURRENT_TIMESTAMP);

ALTER TASK TASK_ARCHIVE_OLD_RECORDS RESUME;

-- ============================================================================
-- TASK 3: Data Quality Check (runs daily at 1 AM UTC)
-- ============================================================================

CREATE OR REPLACE TASK TASK_DATA_QUALITY_CHECK
  WAREHOUSE = TRAINING_WH
  SCHEDULE = 'USING CRON 0 1 * * * UTC'
  COMMENT = 'Check for data quality issues and log anomalies'
AS
BEGIN
  -- Check for orphaned workout_exercises (no corresponding workout)
  INSERT INTO APP_LOGS (log_id, level, source, message, context)
  SELECT 
    UUID_STRING(),
    'WARNING',
    'DATA_QUALITY',
    'Orphaned workout_exercises detected',
    OBJECT_CONSTRUCT('count', COUNT(*))
  FROM WORKOUT_EXERCISES we
  WHERE NOT EXISTS (SELECT 1 FROM WORKOUTS w WHERE w.workout_id = we.workout_id)
  HAVING COUNT(*) > 0;

  -- Check for missing trainer references in active workouts
  INSERT INTO APP_LOGS (log_id, level, source, message, context)
  SELECT 
    UUID_STRING(),
    'WARNING',
    'DATA_QUALITY',
    'Workouts without trainer assigned (recent)',
    OBJECT_CONSTRUCT('count', COUNT(*))
  FROM WORKOUTS w
  WHERE trainer_id IS NULL 
    AND date >= DATEADD(DAY, -7, CURRENT_DATE)
  HAVING COUNT(*) > 0;
END;

ALTER TASK TASK_DATA_QUALITY_CHECK RESUME;

-- ============================================================================
-- HELPER PROCEDURE: Calculate Running Session Pace
-- ============================================================================

CREATE OR REPLACE PROCEDURE CALCULATE_RUNNING_PACE(
  p_run_id VARCHAR(36)
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  UPDATE RUNNING_SESSIONS
  SET actual_pace_sec_per_km = ROUND(
    CASE 
      WHEN actual_distance_km > 0 THEN actual_duration_sec / actual_distance_km
      ELSE NULL 
    END, 2)
  WHERE run_id = p_run_id;
  
  RETURN 'Pace calculated for run ' || p_run_id;
$$;

COMMENT ON PROCEDURE CALCULATE_RUNNING_PACE(VARCHAR) IS 'Calculate average pace for a running session from distance and duration';

GRANT EXECUTE ON PROCEDURE CALCULATE_RUNNING_PACE(VARCHAR) TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- HELPER PROCEDURE: Log Workout Completion
-- ============================================================================

CREATE OR REPLACE PROCEDURE LOG_WORKOUT_COMPLETION(
  p_workout_id VARCHAR(36),
  p_actual_duration_min NUMBER
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  DECLARE
    v_count INT;
  BEGIN
    SELECT COUNT(*) INTO v_count FROM WORKOUTS WHERE workout_id = p_workout_id;
    
    IF v_count = 0 THEN
      RETURN 'Error: Workout ' || p_workout_id || ' not found';
    END IF;
    
    -- Update workout timestamp (if not already set)
    UPDATE WORKOUTS
    SET start_time = COALESCE(start_time, CURRENT_TIMESTAMP)
    WHERE workout_id = p_workout_id;
    
    INSERT INTO APP_LOGS (log_id, level, source, message, context)
    VALUES (
      UUID_STRING(),
      'INFO',
      'WORKOUT_LOGGING',
      'Workout completed',
      OBJECT_CONSTRUCT('workout_id', p_workout_id, 'duration_min', p_actual_duration_min)
    );
    
    RETURN 'Logged completion for workout ' || p_workout_id;
  END;
$$;

COMMENT ON PROCEDURE LOG_WORKOUT_COMPLETION(VARCHAR, NUMBER) IS 'Log workout completion with duration and create audit log entry';

GRANT EXECUTE ON PROCEDURE LOG_WORKOUT_COMPLETION(VARCHAR, NUMBER) TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Verification
-- ============================================================================

SHOW TASKS IN SCHEMA TRAINING_DB.PUBLIC;

-- Check task status
SELECT TASK_NAME, STATE, SCHEDULE_TYPE, LAST_COMPLETED_TIME FROM INFORMATION_SCHEMA.TASK_EXECUTIONS
WHERE DATABASE_NAME = 'TRAINING_DB' AND SCHEMA_NAME = 'PUBLIC'
LIMIT 10;

-- Show procedures
SHOW PROCEDURES IN SCHEMA TRAINING_DB.PUBLIC;
