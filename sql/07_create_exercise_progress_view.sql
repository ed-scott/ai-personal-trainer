-- ============================================================================
-- Exercise Progress View
-- Purpose: Provide aggregated exercise performance metrics for each client/exercise
-- Includes: max weight, avg reps, avg RPE, sessions recorded, estimated 1RM (Epley),
-- and a JSON array of recent sets for quick consumption by AI or app logic
-- ============================================================================

USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

CREATE OR REPLACE VIEW exercise_progress AS
SELECT
  er.client_id,
  er.exercise_id,
  MAX(er.weight_kg) AS max_weight_kg,
  AVG(er.reps) AS avg_reps,
  AVG(er.rpe) AS avg_rpe,
  COUNT(DISTINCT er.performed_date) AS sessions_recorded,
  -- Epley 1RM estimate per set: weight * (1 + reps/30). We take the max observed per-client/exercise
  MAX(CASE WHEN er.weight_kg IS NOT NULL THEN er.weight_kg * (1 + er.reps / 30.0) ELSE NULL END) AS estimated_1rm,
  -- Recent sets as JSON array (most recent first). Limit applied in client queries if needed.
  ARRAY_AGG(
    OBJECT_CONSTRUCT(
      'performed_date', TO_VARCHAR(er.performed_date),
      'set_number', er.set_number,
      'reps', er.reps,
      'weight_kg', er.weight_kg,
      'rpe', er.rpe,
      'rest_seconds', er.rest_seconds,
      'duration_seconds', er.duration_seconds,
      'notes', er.notes
    ) ORDER BY er.recorded_at DESC
  ) AS recent_sets
FROM TRAINING_DB.PUBLIC.exercise_results er
GROUP BY er.client_id, er.exercise_id
;

-- Example: To get the progress for a single client/exercise:
-- SELECT * FROM exercise_progress WHERE client_id = '<client-id>' AND exercise_id = '<exercise-id>';

-- Optional: Create a secure view or materialized view if you expect heavy reads.



