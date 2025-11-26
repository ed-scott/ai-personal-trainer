-- ============================================================================
-- AI Personal Trainer Stage 1 - Create Core Tables
-- Snowflake Native Streamlit Application
-- Purpose: Create all core data model tables in dependency order
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- ============================================================================
-- Table 1: CLIENTS - Client Profiles
-- ============================================================================

CREATE TABLE IF NOT EXISTS clients (
  client_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_name VARCHAR(100) NOT NULL,
  age NUMBER(3,0) NOT NULL,
  gender VARCHAR(20) NOT NULL COMMENT 'Male, Female, Other',
  current_weight_kg NUMBER(7,2) NOT NULL,
  height_cm NUMBER(5,0) NOT NULL,
  fitness_level VARCHAR(50) NOT NULL COMMENT 'Beginner, Intermediate, Advanced',
  fitness_goals VARIANT NOT NULL COMMENT 'JSON array of fitness goals',
  available_equipment VARIANT NOT NULL COMMENT 'JSON array of available equipment',
  days_per_week NUMBER(1,0) NOT NULL COMMENT '1-7 days per week',
  workout_duration_min NUMBER(3,0) NOT NULL COMMENT 'Minutes per workout session',
  dietary_preferences VARIANT COMMENT 'JSON array of dietary preferences',
  allergies VARCHAR(1000) COMMENT 'Free-form text for allergies and restrictions',
  target_calories NUMBER(5,0) COMMENT 'Daily caloric target',
  target_protein_g NUMBER(5,0) COMMENT 'Daily protein target in grams',
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (client_id)
)
COMMENT = 'Client profiles with fitness goals and preferences for AI-generated workouts and meal plans';

--CREATE INDEX IF NOT EXISTS idx_clients_created ON clients (created_at DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON clients TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Table 2: WEIGH_INS - Weight Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS weigh_ins (
  weigh_in_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  weigh_in_date DATE NOT NULL,
  weight_kg NUMBER(7,3) NOT NULL,
  body_fat_pct NUMBER(5,2) COMMENT 'Optional body fat percentage',
  notes VARCHAR(500) COMMENT 'Optional user notes',
  recorded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (weigh_in_id),
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
  CONSTRAINT unique_weighin_per_date UNIQUE (client_id, weigh_in_date)
)
COMMENT = 'Weight tracking and body composition history for clients';

--CREATE INDEX IF NOT EXISTS idx_weighins_client_date ON weigh_ins (client_id, weigh_in_date DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON weigh_ins TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Table 3: BODY_MEASUREMENTS - Body Measurements Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS body_measurements (
  measurement_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  measurement_date DATE NOT NULL,
  neck_cm NUMBER(6,2) COMMENT 'Neck circumference in cm',
  chest_cm NUMBER(6,2) COMMENT 'Chest circumference in cm',
  waist_cm NUMBER(6,2) COMMENT 'Waist circumference in cm',
  hip_cm NUMBER(6,2) COMMENT 'Hip circumference in cm',
  thigh_cm NUMBER(6,2) COMMENT 'Thigh circumference in cm',
  calf_cm NUMBER(6,2) COMMENT 'Calf circumference in cm',
  recorded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (measurement_id),
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
)
COMMENT = 'Detailed body measurements tracked over time';

--CREATE INDEX IF NOT EXISTS idx_body_meas_client_date ON body_measurements (client_id, measurement_date DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON body_measurements TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Table 4: EXERCISES_LIBRARY - Exercise Reference Library
-- ============================================================================

CREATE TABLE IF NOT EXISTS exercises_library (
  exercise_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  exercise_name VARCHAR(200) NOT NULL,
  category VARCHAR(100) NOT NULL COMMENT 'strength, cardio, flexibility',
  target_muscles VARIANT COMMENT 'JSON array of target muscle groups',
  equipment_required VARIANT COMMENT 'JSON array of required equipment',
  difficulty_level VARCHAR(20) COMMENT 'Beginner, Intermediate, Advanced',
  instructions VARCHAR(2000) COMMENT 'Exercise instructions and form cues',
  variations VARIANT COMMENT 'JSON array of exercise variations',
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (exercise_id),
  CONSTRAINT unique_exercise_name UNIQUE (exercise_name)
)
COMMENT = 'Reference library of exercises for AI workout generation';

--CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises_library (category);
GRANT SELECT ON exercises_library TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Table 5: GENERATED_WORKOUTS - AI-Generated Workouts
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_workouts (
  workout_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  generation_date TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  workout_week NUMBER(2,0) NOT NULL COMMENT 'Week number in the plan',
  workout_day NUMBER(1,0) NOT NULL COMMENT 'Day of week (1-7)',
  workout_focus VARCHAR(200) NOT NULL COMMENT 'e.g., Chest & Triceps, Leg Day',
  duration_min NUMBER(3,0) NOT NULL COMMENT 'Workout duration in minutes',
  warm_up VARCHAR(1000) NOT NULL COMMENT 'Warm-up description',
  exercises VARIANT NOT NULL COMMENT 'JSON array of exercises with sets/reps/rest',
  cool_down VARCHAR(1000) NOT NULL COMMENT 'Cool-down description',
  notes VARCHAR(2000) COMMENT 'Additional notes about the workout',
  cortex_prompt VARCHAR(4000) COMMENT 'Prompt used for Cortex generation',
  cortex_model VARCHAR(100) DEFAULT 'mistral-7b' COMMENT 'Cortex model used',
  PRIMARY KEY (workout_id),
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
)
COMMENT = 'AI-generated workouts using Snowflake Cortex Prompt Complete';

--CREATE INDEX IF NOT EXISTS idx_workouts_client_week ON generated_workouts (client_id, workout_week);
GRANT SELECT, INSERT, UPDATE, DELETE ON generated_workouts TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Table 6: RECIPES - Recipe Library
-- ============================================================================

CREATE TABLE IF NOT EXISTS recipes (
  recipe_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  recipe_name VARCHAR(300) NOT NULL,
  servings NUMBER(2,0) NOT NULL,
  total_calories NUMBER(5,0) NOT NULL,
  protein_g NUMBER(5,1) NOT NULL,
  carbs_g NUMBER(5,1) NOT NULL,
  fat_g NUMBER(5,1) NOT NULL,
  ingredients VARIANT NOT NULL COMMENT 'JSON array of ingredients',
  instructions VARCHAR(4000) NOT NULL COMMENT 'Recipe instructions',
  prep_time_min NUMBER(3,0) COMMENT 'Prep time in minutes',
  cook_time_min NUMBER(3,0) COMMENT 'Cook time in minutes',
  tags VARIANT COMMENT 'JSON array of tags (vegetarian, vegan, etc.)',
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (recipe_id),
  CONSTRAINT unique_recipe_name UNIQUE (recipe_name)
)
COMMENT = 'Recipe library for meal plan generation and suggestions';

--CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes (recipe_name);
GRANT SELECT, INSERT ON recipes TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Table 7: MEAL_PLANS - AI-Generated Meal Plans
-- ============================================================================

CREATE TABLE IF NOT EXISTS meal_plans (
  meal_plan_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  generation_date TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  plan_week NUMBER(2,0) NOT NULL COMMENT 'Week number of the meal plan',
  duration_days NUMBER(2,0) DEFAULT 7 COMMENT 'Number of days in the plan',
  total_calories NUMBER(5,0) NOT NULL,
  protein_g NUMBER(5,0) NOT NULL,
  carbs_g NUMBER(5,0) NOT NULL,
  fat_g NUMBER(5,0) NOT NULL,
  meal_plan_json VARIANT NOT NULL COMMENT 'Complete meal plan as JSON with daily breakdowns',
  cortex_prompt VARCHAR(4000) COMMENT 'Prompt used for Cortex generation',
  cortex_model VARCHAR(100) DEFAULT 'mistral-7b' COMMENT 'Cortex model used',
  PRIMARY KEY (meal_plan_id),
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
)
COMMENT = 'AI-generated meal plans using Snowflake Cortex Prompt Complete';

--CREATE INDEX IF NOT EXISTS idx_meal_plans_client_week ON meal_plans (client_id, plan_week);
GRANT SELECT, INSERT, UPDATE, DELETE ON meal_plans TO ROLE TRAINING_APP_ROLE;

-- ============================================================================
-- Verification
-- ============================================================================

SHOW TABLES IN TRAINING_DB.PUBLIC;

SELECT
  TABLE_NAME,
  ROW_COUNT,
  CREATED,
  LAST_ALTERED
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
  AND TABLE_CATALOG = 'TRAINING_DB'
  AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;