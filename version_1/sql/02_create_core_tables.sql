-- ============================================================================
-- AI Personal Trainer - Core Data Model DDL
-- Purpose: Create all core tables in the correct dependency order
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ============================================================================
-- DIMENSION/REFERENCE TABLES (No external dependencies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS CLIENTS (
  client_id VARCHAR(36) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255),
  phone VARCHAR(50),
  dob DATE,
  gender VARCHAR(32),
  timezone VARCHAR(64) DEFAULT 'UTC',
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  metadata VARIANT,
  PRIMARY KEY (client_id),
  UNIQUE (email)
);

COMMENT ON TABLE CLIENTS IS 'Clients / members managed by personal trainers';
GRANT SELECT, INSERT, UPDATE, DELETE ON CLIENTS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS TRAINERS (
  trainer_id VARCHAR(36) NOT NULL,
  name VARCHAR(200),
  email VARCHAR(255),
  phone VARCHAR(50),
  bio VARCHAR(2000),
  certifications VARIANT,
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (trainer_id),
  UNIQUE (email)
);

COMMENT ON TABLE TRAINERS IS 'Personal trainers managing clients and programs';
GRANT SELECT, INSERT, UPDATE, DELETE ON TRAINERS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS EXERCISES (
  exercise_id VARCHAR(36) NOT NULL,
  name VARCHAR(200),
  category VARCHAR(100) DEFAULT 'strength' COMMENT 'strength|cardio|mobility',
  primary_muscles VARIANT,
  instructions VARCHAR(4000),
  equipment VARCHAR(200),
  video_url VARCHAR(2000),
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (exercise_id),
  UNIQUE (name)
);

COMMENT ON TABLE EXERCISES IS 'Exercise library with metadata and instructions';
GRANT SELECT, INSERT, UPDATE, DELETE ON EXERCISES TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- FACT/TRANSACTIONAL TABLES (May have dependencies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS WORKOUTS (
  workout_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  trainer_id VARCHAR(36),
  program_id VARCHAR(36),
  date DATE NOT NULL,
  start_time TIMESTAMP_LTZ,
  type VARCHAR(50) DEFAULT 'gym' COMMENT 'gym|run|cycling|swim|other',
  notes VARCHAR(2000),
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  metadata VARIANT,
  PRIMARY KEY (workout_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
  FOREIGN KEY (trainer_id) REFERENCES TRAINERS(trainer_id)
);

COMMENT ON TABLE WORKOUTS IS 'Top-level workout sessions. Suggested/actual exercise data stored in workout_exercises table.';
CREATE INDEX IF NOT EXISTS IDX_WORKOUTS_CLIENT_DATE ON WORKOUTS(client_id, date);
GRANT SELECT, INSERT, UPDATE, DELETE ON WORKOUTS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS WORKOUT_EXERCISES (
  id VARCHAR(36) NOT NULL,
  workout_id VARCHAR(36) NOT NULL,
  exercise_id VARCHAR(36) NOT NULL,
  order_index NUMBER,
  suggested_sets NUMBER,
  suggested_reps VARCHAR(50) COMMENT 'AI-suggested reps (e.g., 8-12 or AMRAP)',
  suggested_weight_kg NUMBER(8,2),
  actual_sets NUMBER COMMENT 'Actual completed sets (input via Streamlit)',
  actual_reps VARCHAR(50) COMMENT 'Actual completed reps',
  actual_weight_kg NUMBER(8,2) COMMENT 'Actual used weight in kg',
  rpe NUMBER(3,1) COMMENT 'Rate of Perceived Exertion for the exercise',
  notes VARCHAR(1000),
  PRIMARY KEY (id),
  FOREIGN KEY (workout_id) REFERENCES WORKOUTS(workout_id) ON DELETE CASCADE,
  FOREIGN KEY (exercise_id) REFERENCES EXERCISES(exercise_id)
);

COMMENT ON TABLE WORKOUT_EXERCISES IS 'Exercise records within workouts, tracking suggested vs actual performance';
CREATE INDEX IF NOT EXISTS IDX_WKT_EXE_WORKOUT ON WORKOUT_EXERCISES(workout_id);
CREATE INDEX IF NOT EXISTS IDX_WKT_EXE_EXERCISE ON WORKOUT_EXERCISES(exercise_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON WORKOUT_EXERCISES TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS RUNNING_SESSIONS (
  run_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  trainer_id VARCHAR(36),
  date DATE NOT NULL,
  suggested_distance_km NUMBER(8,3) COMMENT 'AI-suggested target distance',
  suggested_pace_sec_per_km NUMBER(8,2) COMMENT 'AI-suggested target pace',
  suggested_type VARCHAR(100) COMMENT 'AI-suggested run type (easy, tempo, intervals, long, etc.)',
  actual_distance_km NUMBER(8,3) COMMENT 'Actual completed distance (input via Streamlit)',
  actual_duration_sec NUMBER COMMENT 'Actual completed duration in seconds',
  actual_pace_sec_per_km NUMBER(8,2) COMMENT 'Actual average pace',
  actual_type VARCHAR(100) COMMENT 'Actual run type as performed',
  calories NUMBER(8,2),
  route_geojson VARIANT COMMENT 'Store GeoJSON points if available',
  device VARCHAR(200),
  notes VARCHAR(2000),
  PRIMARY KEY (run_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
  FOREIGN KEY (trainer_id) REFERENCES TRAINERS(trainer_id)
);

COMMENT ON TABLE RUNNING_SESSIONS IS 'Running session tracking with suggested vs actual metrics';
CREATE INDEX IF NOT EXISTS IDX_RUNNING_CLIENT_DATE ON RUNNING_SESSIONS(client_id, date);
GRANT SELECT, INSERT, UPDATE, DELETE ON RUNNING_SESSIONS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS WEIGH_INS (
  weigh_in_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  date DATE NOT NULL,
  weight_kg NUMBER(7,3),
  body_fat_pct NUMBER(5,2),
  muscle_mass_kg NUMBER(7,3),
  notes VARCHAR(1000),
  recorded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  entry_source VARCHAR(50) DEFAULT 'manual' COMMENT 'manual|device|import',
  entered_by VARCHAR(36) COMMENT 'who entered the weigh-in (client_id or trainer_id)',
  PRIMARY KEY (weigh_in_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id)
);

COMMENT ON TABLE WEIGH_INS IS 'Client weigh-in tracking with body composition metrics';
CREATE INDEX IF NOT EXISTS IDX_WEIGHINS_CLIENT_DATE ON WEIGH_INS(client_id, date DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON WEIGH_INS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS BODY_MEASUREMENTS (
  measurement_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  date DATE NOT NULL,
  neck_cm NUMBER(6,2),
  chest_cm NUMBER(6,2),
  waist_cm NUMBER(6,2),
  hip_cm NUMBER(6,2),
  thigh_cm NUMBER(6,2),
  calf_cm NUMBER(6,2),
  recorded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (measurement_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id)
);

COMMENT ON TABLE BODY_MEASUREMENTS IS 'Detailed body measurement tracking over time';
CREATE INDEX IF NOT EXISTS IDX_BODY_MEAS_CLIENT_DATE ON BODY_MEASUREMENTS(client_id, date DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON BODY_MEASUREMENTS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS TRAINING_PROGRAMS (
  program_id VARCHAR(36) NOT NULL,
  name VARCHAR(300),
  client_id VARCHAR(36),
  trainer_id VARCHAR(36),
  duration_weeks NUMBER,
  description VARCHAR(2000),
  structure VARIANT COMMENT 'hierarchical program JSON',
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (program_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
  FOREIGN KEY (trainer_id) REFERENCES TRAINERS(trainer_id)
);

COMMENT ON TABLE TRAINING_PROGRAMS IS 'Training programs assigned to clients';
CREATE INDEX IF NOT EXISTS IDX_PROGRAMS_CLIENT ON TRAINING_PROGRAMS(client_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON TRAINING_PROGRAMS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS SESSIONS (
  session_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  trainer_id VARCHAR(36) NOT NULL,
  start_time TIMESTAMP_LTZ,
  end_time TIMESTAMP_LTZ,
  session_type VARCHAR(100),
  notes VARCHAR(4000),
  PRIMARY KEY (session_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
  FOREIGN KEY (trainer_id) REFERENCES TRAINERS(trainer_id)
);

COMMENT ON TABLE SESSIONS IS 'Training sessions between trainers and clients';
CREATE INDEX IF NOT EXISTS IDX_SESSIONS_CLIENT_DATE ON SESSIONS(client_id, DATE(start_time));
GRANT SELECT, INSERT, UPDATE, DELETE ON SESSIONS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS MEAL_PLANS (
  meal_plan_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  trainer_id VARCHAR(36),
  name VARCHAR(200),
  start_date DATE,
  end_date DATE,
  goals VARIANT,
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  metadata VARIANT,
  PRIMARY KEY (meal_plan_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
  FOREIGN KEY (trainer_id) REFERENCES TRAINERS(trainer_id)
);

COMMENT ON TABLE MEAL_PLANS IS 'Nutritional meal plans assigned to clients';
CREATE INDEX IF NOT EXISTS IDX_MEALPLANS_CLIENT ON MEAL_PLANS(client_id, start_date);
GRANT SELECT, INSERT, UPDATE, DELETE ON MEAL_PLANS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS RECIPES (
  recipe_id VARCHAR(36) NOT NULL,
  name VARCHAR(300),
  servings NUMBER,
  total_calories NUMBER,
  macronutrients VARIANT COMMENT '{protein:.., carbs:.., fat:..}',
  ingredients VARIANT COMMENT 'array of ingredient objects',
  steps VARIANT,
  tags VARIANT,
  prep_time_min NUMBER,
  cook_time_min NUMBER,
  created_by VARCHAR(36),
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (recipe_id),
  UNIQUE (name)
);

COMMENT ON TABLE RECIPES IS 'Recipe library with nutritional information';
GRANT SELECT, INSERT, UPDATE, DELETE ON RECIPES TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS RECIPE_INGREDIENTS (
  id VARCHAR(36) NOT NULL,
  recipe_id VARCHAR(36) NOT NULL,
  name VARCHAR(300),
  quantity VARCHAR(100),
  calories NUMBER,
  PRIMARY KEY (id),
  FOREIGN KEY (recipe_id) REFERENCES RECIPES(recipe_id) ON DELETE CASCADE
);

COMMENT ON TABLE RECIPE_INGREDIENTS IS 'Ingredient details for each recipe';
CREATE INDEX IF NOT EXISTS IDX_RECIPE_ING_RECIPE ON RECIPE_INGREDIENTS(recipe_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON RECIPE_INGREDIENTS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS NUTRITION_LOGS (
  log_id VARCHAR(36) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  date DATE NOT NULL,
  meal_time TIMESTAMP_LTZ,
  recipe_id VARCHAR(36),
  calories NUMBER,
  macros VARIANT,
  raw_entry VARCHAR(4000),
  PRIMARY KEY (log_id),
  FOREIGN KEY (client_id) REFERENCES CLIENTS(client_id),
  FOREIGN KEY (recipe_id) REFERENCES RECIPES(recipe_id)
);

COMMENT ON TABLE NUTRITION_LOGS IS 'Daily nutrition and meal tracking';
CREATE INDEX IF NOT EXISTS IDX_NUTRITION_CLIENT_DATE ON NUTRITION_LOGS(client_id, date DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON NUTRITION_LOGS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================

CREATE TABLE IF NOT EXISTS AI_EMBEDDINGS (
  id VARCHAR(36) NOT NULL,
  source_table VARCHAR(200),
  source_id VARCHAR(36),
  embedding VARIANT COMMENT 'vector or array stored as VARIANT',
  model VARCHAR(200),
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

COMMENT ON TABLE AI_EMBEDDINGS IS 'Store embeddings used for similarity search and AI features';
CREATE INDEX IF NOT EXISTS IDX_EMBEDDINGS_SOURCE ON AI_EMBEDDINGS(source_table, source_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON AI_EMBEDDINGS TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- List all created tables
SHOW TABLES IN SCHEMA TRAINING_DB.PUBLIC;

-- Verify table structure (sample)
DESCRIBE TABLE CLIENTS;
DESCRIBE TABLE WORKOUTS;
DESCRIBE TABLE WORKOUT_EXERCISES;
DESCRIBE TABLE RUNNING_SESSIONS;
DESCRIBE TABLE WEIGH_INS;

-- Check row counts (should all be 0)
SELECT TABLE_NAME, ROW_COUNT FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'PUBLIC' AND TABLE_CATALOG = 'TRAINING_DB'
ORDER BY TABLE_NAME;
