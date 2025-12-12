"""
AI Personal Trainer - Stage 1
Snowflake Native Streamlit Application
Personalized Workout and Meal Plan Generation using Cortex Prompt Complete
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
from snowflake.snowpark import Session
from snowflake.snowpark.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType
from snowflake.snowpark.functions import current_timestamp, col, to_date, to_timestamp
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# Configuration and Setup
# ============================================================================

st.set_page_config(
    page_title="AI Personal Trainer - Stage 1",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_snowpark_session():
    """Initialize and cache Snowpark session"""
    return Session.builder.getOrCreate()

session = get_snowpark_session()

# ============================================================================
# Utility Functions
# ============================================================================

def generate_uuid():
    """Generate a UUID for database records"""
    return str(uuid.uuid4())

def log_event(event_type: str, client_id: str = None, message: str = None, context: dict = None):
    """Log events to the app_logs table"""
    try:
        log_id = generate_uuid()
        context_json = json.dumps(context) if context else None
        
        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.app_logs 
        (log_id, event_type, severity, client_id, message, context)
        SELECT '{log_id}', '{event_type}', 'INFO', {f"'{client_id}'" if client_id else 'NULL'}, 
                {f"'{message}'" if message else 'NULL'}, TRY_PARSE_JSON('{context_json}')
        """
        session.sql(insert_sql).collect()
    except Exception as e:
        st.error(f"Logging error: {str(e)}")

def get_clients():
    """Fetch all clients from database"""
    try:
        df = session.sql("SELECT * FROM TRAINING_DB.PUBLIC.clients ORDER BY created_at DESC").to_pandas()
        return df
    except Exception as e:
        st.error(f"Error fetching clients: {str(e)}")
        return pd.DataFrame()

def insert_client(client_data: dict):
    """Insert a new client into the database"""
    try:
        client_id = generate_uuid()
        
        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.clients
        (client_id, client_name, age, gender, current_weight_kg, height_cm, 
         fitness_level, fitness_goals, available_equipment, days_per_week, 
         workout_duration_min, dietary_preferences, allergies, target_calories, target_protein_g)
        SELECT
        '{client_id}',
        '{client_data['client_name']}',
        {client_data['AGE']},
        '{client_data['gender']}',
        {client_data['CURRENT_WEIGHT_KG']},
        {client_data['HEIGHT_CM']},
        '{client_data['FITNESS_LEVEL']}',
        TRY_PARSE_JSON('{json.dumps(client_data['FITNESS_GOALS'])}'),
        TRY_PARSE_JSON('{json.dumps(client_data['AVAILABLE_EQUIPMENT'])}'),
        {client_data['DAYS_PER_WEEK']},
        {client_data['WORKOUT_DURATION_MIN']},
        PARSE_JSON('{json.dumps(client_data['DIETARY_PREFERENCES'])}'),
        {f"'{client_data['allergies']}'" if client_data['allergies'] else 'NULL'},
        {client_data['target_calories'] if client_data['target_calories'] else 'NULL'},
        {client_data['target_protein_g'] if client_data['target_protein_g'] else 'NULL'}
        """
        
        session.sql(insert_sql).collect()
        st.stop()
        log_event("client_created", client_id=client_id, message=f"Client {client_data['client_name']} created")
        return client_id
    except Exception as e:
        st.error(f"Error creating client: {str(e)}")
        return None

def get_previous_workouts_context(client_id: str, weeks: int = 4):
    """Get previous workouts to provide context for AI generation"""
    try:
        df = session.sql(f"""
        SELECT workout_week, workout_day, workout_focus, exercises, duration_min
        FROM TRAINING_DB.PUBLIC.generated_workouts
        WHERE client_id = '{client_id}'
        ORDER BY generation_date DESC
        LIMIT {weeks * 7}
        """).to_pandas()
        
        if df.empty:
            return "No previous workouts found. This will be the first training program."
        
        # Summarize previous workouts
        context_lines = ["Previous Workouts (Last 4 Weeks):"]
        workout_dict = {}
        
        for _, row in df.iterrows():
            week = row['WORKOUT_WEEK']
            day = row['WORKOUT_DAY']
            key = f"Week {week}, Day {day}"
            if key not in workout_dict:
                workout_dict[key] = {
                    'focus': row['WORKOUT_FOCUS'],
                    'duration': row['DURATION_MIN'],
                    'exercises': row['EXERCISES']
                }
        
        for key in sorted(workout_dict.keys(), reverse=True)[:16]:  # Last 4 weeks
            workout = workout_dict[key]
            context_lines.append(f"- {key}: {workout['focus']} ({workout['duration']}min)")
        
        return "\n".join(context_lines)
    except Exception as e:
        st.warning(f"Could not retrieve previous workouts: {str(e)}")
        return "No previous workouts available."

def generate_full_week_workouts_cortex(client_id: str, client_data: dict, week: int = 1):
    """Generate a full week of workouts (7 days including rest days) using Cortex Prompt Complete"""
    try:
        # Get context from previous workouts
        previous_context = get_previous_workouts_context(client_id, weeks=4)
        
        # Build prompt from client data
        fitness_goals = ', '.join(client_data['FITNESS_GOALS']) if isinstance(client_data['FITNESS_GOALS'], list) else client_data['FITNESS_GOALS']
        equipment = ', '.join(client_data['AVAILABLE_EQUIPMENT']) if isinstance(client_data['AVAILABLE_EQUIPMENT'], list) else client_data['AVAILABLE_EQUIPMENT']
        
        prompt = f"""You are an expert personal trainer creating a complete 7-day training program.

=== CLIENT PROFILE ===
- Fitness Level: {client_data['FITNESS_LEVEL']}
- Goals: {fitness_goals}
- Available Equipment: {equipment}
- Training Days per Week: {client_data['DAYS_PER_WEEK']}
- Workout Duration: {client_data['WORKOUT_DURATION_MIN']} minutes per session

=== CONTEXT FROM PREVIOUS TRAINING ===
{previous_context}

=== IMPORTANT INSTRUCTIONS ===
1. Create a diverse training program where each training day focuses on different muscle groups
2. Include {client_data['DAYS_PER_WEEK']} training days and {7 - client_data['DAYS_PER_WEEK']} rest days
3. ENSURE THE WORKOUTS ARE SIGNIFICANTLY DIFFERENT from the previous weeks shown above
4. Vary the exercises, rep ranges, and training focus across the week
5. Include at least 1 running day within the {client_data['DAYS_PER_WEEK']} training days
6. On gym days, ensure to include at least 5 exercises
7. Include proper warm-up and cool-down for each training day
8. Space out muscle groups to allow for recovery (e.g., no back-to-back same muscle groups)
9. Rest days should be labeled with recovery recommendations

Format EXACTLY as this JSON (no extra text):
{{
  "week": {week},
  "days": [
    {{"day": 1, "day_name": "Monday", "is_rest_day": false, "focus": "Upper Body", "warm_up": "5 min", "exercises": [{{"name": "Ex1", "sets": 3, "reps": "8-10", "rest_sec": 90, "notes": "notes"}}], "cool_down": "stretch"}},
    {{"day": 2, "day_name": "Tuesday", "is_rest_day": true, "recovery_tips": "Light activity"}}
  ]
}}"""
        
        # Call Cortex
        cortex_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-7b',
            '{prompt}'
        ) AS response
        """
        
        result = session.sql(cortex_sql).collect()
        response_text = result[0][0]
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            workout_json = json.loads(json_match.group())
        else:
            workout_json = json.loads(response_text)
        
        return workout_json, prompt
    except Exception as e:
        st.error(f"Error generating weekly workout with Cortex: {str(e)}")
        return None, None

def generate_workout_cortex(client_id: str, client_data: dict):
    """Generate workout using Cortex Prompt Complete (Legacy - single day)"""
    try:
        # Build prompt from client data
        fitness_goals = ', '.join(client_data['FITNESS_GOALS']) if isinstance(client_data['FITNESS_GOALS'], list) else client_data['FITNESS_GOALS']
        equipment = ', '.join(client_data['AVAILABLE_EQUIPMENT']) if isinstance(client_data['AVAILABLE_EQUIPMENT'], list) else client_data['AVAILABLE_EQUIPMENT']
        
        prompt = f"""You are an expert personal trainer. Generate a detailed workout plan for a client.

Client Profile:
- Fitness Level: {client_data['FITNESS_LEVEL']}
- Goals: {fitness_goals}
- Available Equipment: {equipment}
- Days Available per Week: {client_data['DAYS_PER_WEEK']}
- Preferred Duration: {client_data['WORKOUT_DURATION_MIN']} minutes

Generate a complete {client_data['WORKOUT_DURATION_MIN']}-minute workout including:
1. Warm-up (5 minutes)
2. Main exercises with sets, reps, and rest periods (appropriate to their fitness level)
3. Cool-down (5-10 minutes)

Format EXACTLY as this JSON structure (no extra text before or after):
{{
  "warm_up": "description here",
  "exercises": [
    {{"name": "Exercise Name", "sets": 3, "reps": "8-10", "rest_sec": 60, "notes": "form cues"}},
    {{"name": "Exercise Name", "sets": 3, "reps": "8-10", "rest_sec": 60, "notes": "form cues"}}
  ],
  "cool_down": "description here"
}}"""
        
        # Call Cortex
        cortex_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-7b',
            '{prompt}'
        ) AS response
        """
        
        result = session.sql(cortex_sql).collect()
        response_text = result[0][0]
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            workout_json = json.loads(json_match.group())
        else:
            workout_json = json.loads(response_text)
        
        return workout_json, prompt
    except Exception as e:
        st.error(f"Error generating workout with Cortex: {str(e)}")
        return None, None

def generate_meal_plan_cortex(client_data: dict):
    """Generate meal plan using Cortex Prompt Complete"""
    try:
        fitness_goals = ', '.join(client_data['FITNESS_GOALS']) if isinstance(client_data['FITNESS_GOALS'], list) else client_data['FITNESS_GOALS']
        dietary_prefs = ', '.join(client_data['DIETARY_PREFERENCES']) if isinstance(client_data['DIETARY_PREFERENCES'], list) else client_data['DIETARY_PREFERENCES']
        
        target_calories = client_data.get('target_calories', 2000)
        target_protein = client_data.get('target_protein_g', 150)
        
        prompt = f"""You are a sports nutritionist. Create a detailed 7-day meal plan for a client.

Client Profile:
- Target Daily Calories: {target_calories}
- Target Protein: {target_protein}g
- Dietary Preferences: {dietary_prefs}
- Allergies/Restrictions: {client_data.get('allergies', 'None')}
- Fitness Goals: {fitness_goals}

Generate a complete 7-day meal plan with:
1. Daily meals (breakfast, lunch, dinner, snacks)
2. Macronutrient targets per day
3. Specific recipes or foods

Format EXACTLY as this JSON structure (no extra text before or after):
{{
  "weekly_totals": {{"calories": {target_calories}, "protein": {target_protein}, "carbs": 200, "fat": 70}},
  "days": [
    {{
      "day": 1,
      "meals": [
        {{"meal_type": "breakfast", "foods": ["food 1", "food 2"], "calories": 500, "protein": 30}},
        {{"meal_type": "lunch", "foods": ["food 1", "food 2"], "calories": 600, "protein": 40}},
        {{"meal_type": "dinner", "foods": ["food 1", "food 2"], "calories": 650, "protein": 45}},
        {{"meal_type": "snacks", "foods": ["snack"], "calories": 250, "protein": 35}}
      ]
    }}
  ]
}}"""
        
        cortex_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-7b',
            '{prompt}'
        ) AS response
        """
        
        result = session.sql(cortex_sql).collect()
        response_text = result[0][0]
        
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            meal_plan_json = json.loads(json_match.group())
        else:
            meal_plan_json = json.loads(response_text)
        
        return meal_plan_json, prompt
    except Exception as e:
        st.error(f"Error generating meal plan with Cortex: {str(e)}")
        return None, None

def save_workout(client_id: str, workout_data: dict, prompt: str, week: int = 1, day: int = 1):
    """Save a single day's workout to database"""
    try:
        workout_id = generate_uuid()
        
        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.generated_workouts
        (workout_id, client_id, workout_week, workout_day, workout_focus, duration_min,
         warm_up, exercises, cool_down, cortex_prompt, cortex_model)
        SELECT
        '{workout_id}',
        '{client_id}',
        {week},
        {day},
        '{workout_data.get('focus', 'Generated Workout').replace("'", "''")}',
        60,
        '{workout_data.get('warm_up', '').replace("'", "''")}',
        PARSE_JSON('{json.dumps(workout_data.get('exercises', []))}'),
        '{workout_data.get('cool_down', '').replace("'", "''")}',
        '{prompt.replace("'", "''")}',
        'mistral-7b'
        """
        
        session.sql(insert_sql).collect()
        log_event("workout_generated", client_id=client_id, message=f"Workout Day {day} Week {week} saved")
        return workout_id
    except Exception as e:
        st.error(f"Error saving workout: {str(e)}")
        return None

def save_weekly_workouts(client_id: str, weekly_data: dict, prompt: str, start_date=None):
    """Save all workouts from a full week to database"""
    try:
        week = weekly_data.get('week', 1)
        saved_count = 0
        
        # If no start date provided, use today
        if start_date is None:
            start_date = datetime.now().date()
        
        for day_data in weekly_data.get('days', []):
            day_num = day_data.get('day', 1)
            # Calculate workout date based on start date and day number
            workout_date = start_date + timedelta(days=day_num - 1)
            
            if day_data.get('is_rest_day', False):
                # Save rest day as a special entry
                workout_id = generate_uuid()
                recovery_tips = day_data.get('recovery_tips', 'Rest day')
                
                insert_sql = f"""
                INSERT INTO TRAINING_DB.PUBLIC.generated_workouts
                (workout_id, client_id, workout_date, workout_week, workout_day, workout_focus, duration_min,
                 warm_up, exercises, cool_down, cortex_prompt, cortex_model)
                SELECT
                '{workout_id}',
                '{client_id}',
                '{workout_date}',
                {week},
                {day_num},
                'Rest Day',
                0,
                '{recovery_tips.replace("'", "''")}',
                PARSE_JSON('[]'),
                'Focus on recovery',
                '{prompt.replace("'", "''")}',
                'mistral-7b'
                """
            else:
                # Save training day
                workout_id = generate_uuid()
                focus = day_data.get('focus', 'Generated Workout')
                warm_up = day_data.get('warm_up', '')
                exercises = day_data.get('exercises', [])
                cool_down = day_data.get('cool_down', '')
                
                insert_sql = f"""
                INSERT INTO TRAINING_DB.PUBLIC.generated_workouts
                (workout_id, client_id, workout_date, workout_week, workout_day, workout_focus, duration_min,
                 warm_up, exercises, cool_down, cortex_prompt, cortex_model)
                SELECT
                '{workout_id}',
                '{client_id}',
                '{workout_date}',
                {week},
                {day_num},
                '{focus.replace("'", "''")}',
                60,
                '{warm_up.replace("'", "''")}',
                PARSE_JSON('{json.dumps(exercises)}'),
                '{cool_down.replace("'", "''")}',
                '{prompt.replace("'", "''")}',
                'mistral-7b'
                """
            
            session.sql(insert_sql).collect()
            saved_count += 1
        
        log_event("weekly_workouts_generated", client_id=client_id, 
                 message=f"Week {week} with {saved_count} days saved")
        return saved_count
    except Exception as e:
        st.error(f"Error saving weekly workouts: {str(e)}")
        return 0

def save_meal_plan(client_id: str, meal_plan_data: dict, prompt: str, week: int = 1, start_date=None):
    """Save generated meal plan to database"""
    try:
        meal_plan_id = generate_uuid()
        totals = meal_plan_data['weekly_totals']
        
        # If no start date provided, use today
        if start_date is None:
            start_date = datetime.now().date()
        
        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.meal_plans
        (meal_plan_id, client_id, plan_start_date, plan_week, duration_days, total_calories, protein_g, 
         carbs_g, fat_g, meal_plan_json, cortex_prompt, cortex_model)
        SELECT
        '{meal_plan_id}',
        '{client_id}',
        '{start_date}',
        {week},
        7,
        {totals['calories']},
        {totals['protein']},
        {totals['carbs']},
        {totals['fat']},
        PARSE_JSON('{json.dumps(meal_plan_data)}'),
        '{prompt.replace("'", "''")}',
        'mistral-7b'
        """
        
        session.sql(insert_sql).collect()
        log_event("meal_plan_generated", client_id=client_id, message="Meal plan generated and saved")
        return meal_plan_id
    except Exception as e:
        st.error(f"Error saving meal plan: {str(e)}")
        return None

def insert_weigh_in(client_id: str, weigh_in_date: datetime, weight_kg: float, body_fat_pct: float = None, notes: str = None):
    """Insert weigh-in record"""
    try:
        weigh_in_id = generate_uuid()
        
        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.weigh_ins
        (weigh_in_id, client_id, weigh_in_date, weight_kg, body_fat_pct, notes)
        SELECT
        '{weigh_in_id}',
        '{client_id}',
        '{weigh_in_date.strftime("%Y-%m-%d")}',
        {weight_kg},
        {body_fat_pct if body_fat_pct else 'NULL'},
        {f"'{notes}'" if notes else 'NULL'}
        """
        
        session.sql(insert_sql).collect()
        log_event("weigh_in_recorded", client_id=client_id, message=f"Weigh-in recorded: {weight_kg}kg")
        return weigh_in_id
    except Exception as e:
        st.error(f"Error saving weigh-in: {str(e)}")
        return None

def insert_exercise_result(client_id: str, workout_id: str, exercise_id: str, performed_date: datetime,
                           set_number: int, reps: int, weight_kg: float = None, rpe: float = None,
                           rest_seconds: int = None, duration_seconds: int = None, notes: str = None):
    """Insert a single exercise set result into the exercise_results table"""
    try:
        result_id = generate_uuid()

        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.exercise_results
        (result_id, client_id, workout_id, exercise_id, performed_date, set_number, reps, weight_kg, rpe, rest_seconds, duration_seconds, notes)
        SELECT
        '{result_id}',
        '{client_id}',
        '{workout_id}',
        '{exercise_id}',
        '{performed_date.strftime('%Y-%m-%d')}',
        {set_number},
        {reps},
        {weight_kg if weight_kg is not None else 'NULL'},
        {rpe if rpe is not None else 'NULL'},
        {rest_seconds if rest_seconds is not None else 'NULL'},
        {duration_seconds if duration_seconds is not None else 'NULL'},
        {f"'{notes.replace("'", "''")}'" if notes else 'NULL'}
        """

        session.sql(insert_sql).collect()
        log_event('exercise_result_recorded', client_id=client_id,
                  message=f'Result recorded for workout {workout_id}, exercise {exercise_id}, set {set_number}')
        return result_id
    except Exception as e:
        st.error(f"Error saving exercise result: {str(e)}")
        return None

def get_exercise_progress(client_id: str, exercise_id: str):
    """Fetch aggregated exercise progress for a client and exercise from the exercise_progress view.

    Returns a dict with keys: client_id, exercise_id, max_weight_kg, avg_reps, avg_rpe,
    sessions_recorded, estimated_1rm, recent_sets (list of JSON objects)
    """
    try:
        sql = f"SELECT * FROM TRAINING_DB.PUBLIC.exercise_progress WHERE client_id = '{client_id}' AND exercise_id = '{exercise_id}'"
        df = session.sql(sql).to_pandas()
        if df.empty:
            return None

        row = df.iloc[0].to_dict()

        # Parse the recent_sets Variant/ARRAY into Python list if it's a string
        recent_sets = row.get('RECENT_SETS')
        if isinstance(recent_sets, str):
            try:
                recent_sets = json.loads(recent_sets)
            except Exception:
                # Leave as-is if parsing fails
                pass

        return {
            'client_id': row.get('CLIENT_ID'),
            'exercise_id': row.get('EXERCISE_ID'),
            'max_weight_kg': row.get('MAX_WEIGHT_KG'),
            'avg_reps': row.get('AVG_REPS'),
            'avg_rpe': row.get('AVG_RPE'),
            'sessions_recorded': int(row.get('SESSIONS_RECORDED')) if row.get('SESSIONS_RECORDED') is not None else 0,
            'estimated_1rm': row.get('ESTIMATED_1RM'),
            'recent_sets': recent_sets
        }
    except Exception as e:
        st.warning(f"Could not fetch exercise progress: {str(e)}")
        return None

def get_exercise_1rm_trend(client_id: str, exercise_id: str, weeks: int = 12):
    """Return a pandas DataFrame with weekly estimated 1RM (Epley) for the last `weeks` weeks.

    Columns: week_start (date), estimated_1rm_max, avg_reps, total_sets, weekly_volume
    """
    try:
        sql = f"""
        SELECT
          DATE_TRUNC('week', performed_date) AS week_start,
          MAX(CASE WHEN weight_kg IS NOT NULL THEN weight_kg * (1 + reps / 30.0) ELSE NULL END) AS estimated_1rm_max,
          AVG(reps) AS avg_reps,
          COUNT(*) AS total_sets,
          SUM(CASE WHEN weight_kg IS NOT NULL THEN weight_kg * reps ELSE 0 END) AS weekly_volume
        FROM TRAINING_DB.PUBLIC.exercise_results
        WHERE client_id = '{client_id}'
          AND exercise_id = '{exercise_id}'
          AND performed_date >= DATEADD(week, -{weeks}, CURRENT_DATE())
        GROUP BY week_start
        ORDER BY week_start ASC
        """

        df = session.sql(sql).to_pandas()
        if df.empty:
            return pd.DataFrame(columns=['week_start', 'estimated_1rm_max', 'avg_reps', 'total_sets', 'weekly_volume'])

        # Ensure proper dtypes
        df['WEEK_START'] = pd.to_datetime(df['WEEK_START']).dt.date
        df = df.rename(columns={
            'WEEK_START': 'week_start',
            'ESTIMATED_1RM_MAX': 'estimated_1rm_max',
            'AVG_REPS': 'avg_reps',
            'TOTAL_SETS': 'total_sets',
            'WEEKLY_VOLUME': 'weekly_volume'
        })

        return df
    except Exception as e:
        st.warning(f"Could not fetch 1RM trend: {str(e)}")
        return pd.DataFrame(columns=['week_start', 'estimated_1rm_max', 'avg_reps', 'total_sets', 'weekly_volume'])

def get_client_workouts(client_id: str):
    """Get all workouts for a client"""
    try:
        df = session.sql(f"""
        SELECT * FROM TRAINING_DB.PUBLIC.generated_workouts 
        WHERE client_id = '{client_id}'
        ORDER BY generation_date DESC
        """).to_pandas()
        return df
    except Exception as e:
        st.error(f"Error fetching workouts: {str(e)}")
        return pd.DataFrame()

def get_client_meal_plans(client_id: str):
    """Get all meal plans for a client"""
    try:
        df = session.sql(f"""
        SELECT * FROM TRAINING_DB.PUBLIC.meal_plans 
        WHERE client_id = '{client_id}'
        ORDER BY generation_date DESC
        """).to_pandas()
        return df
    except Exception as e:
        st.error(f"Error fetching meal plans: {str(e)}")
        return pd.DataFrame()

def get_client_weight_history(client_id: str):
    """Get weight history for a client"""
    try:
        df = session.sql(f"""
        SELECT weigh_in_date, weight_kg, body_fat_pct
        FROM TRAINING_DB.PUBLIC.weigh_ins 
        WHERE client_id = '{client_id}'
        ORDER BY weigh_in_date ASC
        """).to_pandas()
        return df
    except Exception as e:
        st.error(f"Error fetching weight history: {str(e)}")
        return pd.DataFrame()

def get_client_workouts_by_date_range(client_id: str, start_date, end_date):
    """Get workouts for a client within a date range"""
    try:
        df = session.sql(f"""
        SELECT * FROM TRAINING_DB.PUBLIC.generated_workouts 
        WHERE client_id = '{client_id}'
        AND workout_date >= '{start_date}'
        AND workout_date <= '{end_date}'
        ORDER BY workout_date ASC, workout_day ASC
        """).to_pandas()
        return df
    except Exception as e:
        st.error(f"Error fetching workouts by date range: {str(e)}")
        return pd.DataFrame()

def get_client_meal_plans_by_date_range(client_id: str, start_date, end_date):
    """Get meal plans for a client within a date range"""
    try:
        df = session.sql(f"""
        SELECT * FROM TRAINING_DB.PUBLIC.meal_plans 
        WHERE client_id = '{client_id}'
        AND plan_start_date >= '{start_date}'
        AND plan_start_date <= '{end_date}'
        ORDER BY plan_start_date ASC
        """).to_pandas()
        return df
    except Exception as e:
        st.error(f"Error fetching meal plans by date range: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# Page: Home / Client Management
# ============================================================================

def page_home():
    st.title("🏋️ AI Personal Trainer - Stage 1")
    st.markdown("**Personalized Workout and Meal Plan Generation with Cortex Prompt Complete**")
    
    tab1, tab2 = st.tabs(["Create New Client", "View Clients"])
    
    with tab1:
        st.header("Create New Client Profile")
        
        with st.form("client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                client_name = st.text_input("Client Name", placeholder="John Doe")
                age = st.number_input("Age", min_value=18, max_value=100, value=30)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                current_weight_kg = st.number_input("Current Weight (kg)", min_value=30.0, max_value=300.0, value=75.0, format="%.2f")
                height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=180)
            
            with col2:
                fitness_level = st.selectbox("Fitness Level", ["Beginner", "Intermediate", "Advanced"])
                fitness_goals = st.multiselect(
                    "Fitness Goals",
                    ["Weight Loss", "Muscle Gain", "Endurance", "Strength", "General Fitness", "Flexibility"],
                    default=["Muscle Gain"]
                )
                available_equipment = st.multiselect(
                    "Available Equipment",
                    ["Dumbbells", "Barbell", "Gym Machine", "Cardio Equipment", "Bodyweight Only", "Resistance Bands"],
                    default=["Dumbbells"]
                )
                days_per_week = st.number_input("Days Available per Week", min_value=1, max_value=7, value=4)
                workout_duration_min = st.number_input("Workout Duration (minutes)", min_value=15, max_value=180, value=60)
            
            st.divider()
            
            col3, col4 = st.columns(2)
            
            with col3:
                dietary_preferences = st.multiselect(
                    "Dietary Preferences",
                    ["Vegetarian", "Vegan", "Keto", "Paleo", "Mediterranean", "None"],
                    default=["None"]
                )
                allergies = st.text_area("Allergies / Restrictions", placeholder="e.g., nuts, dairy, gluten")
            
            with col4:
                target_calories = st.number_input("Caloric Target (kcal/day)", min_value=1200, max_value=5000, value=2000)
                target_protein_g = st.number_input("Protein Target (g/day)", min_value=50, max_value=300, value=150)
            
            if st.form_submit_button("✅ Create Client", use_container_width=True):
                if not client_name:
                    st.error("Please enter a client name")
                else:
                    client_data = {
                        'CLIENT_NAME': client_name,
                        'AGE': age,
                        'GENDER': gender,
                        'CURRENT_WEIGHT_KG': current_weight_kg,
                        'HEIGHT_CM': height_cm,
                        'FITNESS_LEVEL': fitness_level,
                        'FITNESS_GOALS': fitness_goals,
                        'AVAILABLE_EQUIPMENT': available_equipment,
                        'DAYS_PER_WEEK': days_per_week,
                        'WORKOUT_DURATION_MIN': workout_duration_min,
                        'DIETARY_PREFERENCES': dietary_preferences,
                        'allergies': allergies,
                        'target_calories': target_calories,
                        'target_protein_g': target_protein_g
                    }
                    
                    client_id = insert_client(client_data)
                    if client_id:
                        st.success(f"✅ Client created successfully! ID: {client_id}")
                        st.balloons()
    
    with tab2:
        st.header("All Clients")
        clients_df = get_clients()
        
        if not clients_df.empty:
            st.dataframe(
                clients_df[['CLIENT_ID', 'CLIENT_NAME', 'AGE', 'FITNESS_LEVEL', 'CURRENT_WEIGHT_KG', 'CREATED_AT']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No clients found. Create a new client to get started!")

# ============================================================================
# Page: Workout Generator
# ============================================================================

def page_workout_generator():
    st.title("💪 Workout Generator - Full Week Planning")
    st.markdown("Generate a complete 7-day training program with AI (Cortex Prompt Complete)")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_client_name = st.selectbox(
            "Select Client",
            clients_df['CLIENT_NAME'].tolist()
        )
        selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
        client_id = selected_client['CLIENT_ID']
    
    with col2:
        st.metric("Fitness Level", selected_client['FITNESS_LEVEL'])
    
    with col3:
        st.metric("Training Days/Week", selected_client['DAYS_PER_WEEK'])
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Generate Full Week", "View History"])
    
    with tab1:
        st.markdown("### Generate a Full 7-Day Training Program")
        st.info("💡 The AI will review your last 4 weeks of training and create a NEW program with varied exercises and focuses to prevent plateaus.")
        
        col1, col2 = st.columns(2)
        with col1:
            week = st.number_input("Week Number", min_value=1, max_value=52, value=1, help="Which week of the program is this?")
        with col2:
            start_date = st.date_input("Start Date (Monday of this week)", value=datetime.now().date(), help="First day of the workout week")
        
        if st.button("🤖 Generate Full Week with AI", use_container_width=True, type="primary"):
            with st.spinner("Analyzing previous workouts and generating new full-week program..."):
                # First show context
                with st.status("Reviewing previous 4 weeks of training...", expanded=False) as status:
                    context = get_previous_workouts_context(client_id, weeks=4)
                    st.write(context)
                    status.update(label="✅ Context reviewed", state="complete")
                
                # Generate full week
                with st.status("Generating full week with AI...", expanded=True) as status:
                    st.session_state.weekly_data, prompt = generate_full_week_workouts_cortex(
                        client_id, 
                        selected_client.to_dict(),
                        week=week
                    )
                    status.update(label="✅ Week generated", state="complete")
                
                if st.session_state.weekly_data:
                    st.success("✅ Full week program generated successfully!")
                    
                    # Display full week overview
                    st.markdown(f"### 📅 Week {week} Training Program")
                    
                    # Create a summary table
                    week_summary = []
                    for day_data in st.session_state.weekly_data.get('days', []):
                        day_name = day_data.get('day_name', f"Day {day_data.get('day')}")
                        if day_data.get('is_rest_day', False):
                            week_summary.append({
                                'Day': day_name,
                                'Type': '🔄 Rest',
                                'Focus': 'Recovery',
                                'Exercises': '-'
                            })
                        else:
                            focus = day_data.get('focus', 'Training')
                            exercises = day_data.get('exercises', [])
                            week_summary.append({
                                'Day': day_name,
                                'Type': '💪 Training',
                                'Focus': focus,
                                'Exercises': len(exercises)
                            })
                    
                    summary_df = pd.DataFrame(week_summary)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Display each day
                    st.markdown("### Detailed Daily Workouts")
                    
                    for day_data in st.session_state.weekly_data.get('days', []):
                        day_num = day_data.get('day', 1)
                        day_name = day_data.get('day_name', f"Day {day_num}")
                        
                        if day_data.get('is_rest_day', False):
                            with st.expander(f"📅 {day_name} - 🔄 Rest Day", expanded=False):
                                st.info(f"Recovery Tips: {day_data.get('recovery_tips', 'Take a well-deserved break!')}")
                        else:
                            focus = day_data.get('focus', 'Training')
                            with st.expander(f"📅 {day_name} - 💪 {focus}", expanded=day_num==1):
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Warm-up", "5 min")
                                col2.metric("Main Workout", "~45 min")
                                col3.metric("Cool-down", "10 min")
                                
                                st.markdown("**Warm-up:**")
                                st.write(day_data.get('warm_up', 'N/A'))
                                
                                st.markdown("**Main Exercises:**")
                                exercises = day_data.get('exercises', [])
                                for i, exercise in enumerate(exercises, 1):
                                    with st.expander(f"Exercise {i}: {exercise.get('name', 'N/A')}"):
                                        col1, col2, col3, col4 = st.columns(4)
                                        col1.metric("Sets", exercise.get('sets', 3))
                                        col2.metric("Reps", exercise.get('reps', '8-10'))
                                        col3.metric("Rest (sec)", exercise.get('rest_sec', 60))
                                        col4.metric("Notes", "See below")
                                        st.write(exercise.get('notes', 'Form cues TBD'))
                                
                                st.markdown("**Cool-down:**")
                                st.write(day_data.get('cool_down', 'N/A'))
                    
                    saved_count = save_weekly_workouts(client_id, st.session_state.weekly_data, prompt, start_date=start_date)
                    if saved_count > 0:
                        st.success(f"✅ Full week saved! {saved_count} workout days stored in database.")
                        if 'weekly_data' in st.session_state:
                            del st.session_state.weekly_data
    
    with tab2:
        st.markdown("### Workout History")
        workouts_df = get_client_workouts(client_id)
        
        if not workouts_df.empty:
            st.dataframe(
                workouts_df[['WORKOUT_ID', 'WORKOUT_DATE', 'GENERATION_DATE', 'WORKOUT_WEEK', 'WORKOUT_DAY', 'WORKOUT_FOCUS']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No workouts generated yet. Create a full week program using the generator above!")

# ============================================================================
# Page: Meal Plan Generator
# ============================================================================

def page_meal_plan_generator():
    st.title("🍽️ Meal Plan Generator")
    st.markdown("Generate personalized meal plans using AI (Cortex Prompt Complete)")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_client_name = st.selectbox(
            "Select Client",
            clients_df['CLIENT_NAME'].tolist(),
            key="meal_plan_client_select"
        )
        selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
        client_id = selected_client['CLIENT_ID']
    
    with col2:
        st.metric("Target Calories", f"{selected_client.get('target_calories', 2000)} kcal")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Generate New Meal Plan", "View History"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            week = st.number_input("Week Number", min_value=1, max_value=52, value=1, key="meal_plan_week")
        with col2:
            meal_start_date = st.date_input("Start Date (Monday of this week)", value=datetime.now().date(), key="meal_plan_start_date")
        
        if st.button("🤖 Generate Meal Plan with AI", use_container_width=True, type="primary"):
            with st.spinner("Generating meal plan using Cortex Prompt Complete..."):
                meal_plan_data, prompt = generate_meal_plan_cortex(selected_client.to_dict())
                
                if meal_plan_data:
                    st.success("✅ Meal plan generated successfully!")
                    
                    # Display meal plan
                    st.markdown("### 7-Day Meal Plan")
                    
                    totals = meal_plan_data['weekly_totals']
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Calories", f"{totals['calories']} kcal")
                    col2.metric("Protein", f"{totals['protein']}g")
                    col3.metric("Carbs", f"{totals['carbs']}g")
                    col4.metric("Fat", f"{totals['fat']}g")
                    
                    st.divider()
                    
                    for day_plan in meal_plan_data['days']:
                        day_num = day_plan['day']
                        st.markdown(f"#### Day {day_num}")
                        
                        meals = day_plan.get('meals', [])
                        for meal in meals:
                            meal_type = meal['meal_type'].title()
                            with st.expander(f"{meal_type} - {meal['calories']} kcal, {meal['protein']}g protein"):
                                for food in meal['foods']:
                                    st.write(f"• {food}")
                
                meal_plan_id = save_meal_plan(client_id, meal_plan_data, prompt, week, start_date=meal_start_date)
                if meal_plan_id:
                    st.success(f"✅ Meal plan saved! ID: {meal_plan_id}")
    
    with tab2:
        st.markdown("### Meal Plan History")
        meal_plans_df = get_client_meal_plans(client_id)
        
        if not meal_plans_df.empty:
            st.dataframe(
                meal_plans_df[['MEAL_PLAN_ID', 'GENERATION_DATE', 'PLAN_WEEK', 'TOTAL_CALORIES', 'PROTEIN_G']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No meal plans generated yet. Create one using the generator above!")

# ============================================================================
# Page: Weight Tracking
# ============================================================================

def page_weight_tracking():
    st.title("⚖️ Weight & Measurements Tracking")
    st.markdown("Track client weight and body measurements over time")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return
    
    selected_client_name = st.selectbox(
        "Select Client",
        clients_df['CLIENT_NAME'].tolist(),
        key="weight_tracking_client"
    )
    selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
    client_id = selected_client['CLIENT_ID']
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["Record Weigh-in", "Weight History", "Body Measurements"])
    
    with tab1:
        st.markdown("### Record Weight Entry")
        
        col1, col2 = st.columns(2)
        
        with col1:
            weigh_in_date = st.date_input("Date", value=datetime.now())
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=75.0, format="%.2f")
        
        with col2:
            body_fat_pct = st.number_input("Body Fat %", min_value=5.0, max_value=50.0, value=20.0, format="%.1f", help="Optional")
            notes = st.text_area("Notes (optional)", placeholder="e.g., After workout, morning weigh-in, etc.")
        
        if st.button("✅ Record Weigh-in", use_container_width=True, type="primary"):
            weigh_in_id = insert_weigh_in(client_id, weigh_in_date, weight_kg, body_fat_pct, notes)
            if weigh_in_id:
                st.success(f"✅ Weigh-in recorded! ID: {weigh_in_id}")
    
    with tab2:
        st.markdown("### Weight History")
        weight_history = get_client_weight_history(client_id)
        
        if not weight_history.empty:
            # Chart
            fig = px.line(
                weight_history,
                x='weigh_in_date',
                y='weight_kg',
                title="Weight Trend",
                labels={'weigh_in_date': 'Date', 'weight_kg': 'Weight (kg)'},
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.dataframe(weight_history, use_container_width=True, hide_index=True)
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            col1.metric("Latest Weight", f"{weight_history['weight_kg'].iloc[-1]:.2f} kg")
            col2.metric("Starting Weight", f"{weight_history['weight_kg'].iloc[0]:.2f} kg")
            col3.metric("Total Change", f"{weight_history['weight_kg'].iloc[-1] - weight_history['weight_kg'].iloc[0]:+.2f} kg")
        else:
            st.info("No weight history recorded yet. Start tracking by recording a weigh-in!")
    
    with tab3:
        st.markdown("### Record Body Measurements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            measurement_date = st.date_input("Date", value=datetime.now(), key="measurement_date")
            neck_cm = st.number_input("Neck (cm)", min_value=20.0, max_value=50.0, value=38.0, format="%.1f")
            chest_cm = st.number_input("Chest (cm)", min_value=70.0, max_value=150.0, value=95.0, format="%.1f")
        
        with col2:
            waist_cm = st.number_input("Waist (cm)", min_value=50.0, max_value=150.0, value=75.0, format="%.1f")
            hip_cm = st.number_input("Hip (cm)", min_value=70.0, max_value=150.0, value=92.0, format="%.1f")
            thigh_cm = st.number_input("Thigh (cm)", min_value=35.0, max_value=80.0, value=58.0, format="%.1f")
            calf_cm = st.number_input("Calf (cm)", min_value=25.0, max_value=50.0, value=38.0, format="%.1f")
        
        if st.button("✅ Record Measurements", use_container_width=True, type="primary", key="save_measurements"):
            try:
                measurement_id = str(uuid.uuid4())
                insert_sql = f"""
                INSERT INTO TRAINING_DB.PUBLIC.body_measurements
                (measurement_id, client_id, measurement_date, neck_cm, chest_cm, waist_cm, hip_cm, thigh_cm, calf_cm)
                SELECT
                '{measurement_id}',
                '{client_id}',
                '{measurement_date}',
                {neck_cm},
                {chest_cm},
                {waist_cm},
                {hip_cm},
                {thigh_cm},
                {calf_cm}
                """
                
                session.sql(insert_sql).collect()
                st.success(f"✅ Measurements recorded! ID: {measurement_id}")
            except Exception as e:
                st.error(f"Error saving measurements: {str(e)}")

# ============================================================================
# Page: Workout Summary
# ============================================================================

def page_workout_summary():
    st.title("📊 Workout Summary")
    st.markdown("View workouts for a selected date range")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_client_name = st.selectbox(
            "Select Client",
            clients_df['CLIENT_NAME'].tolist(),
            key="workout_summary_client"
        )
        selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
        client_id = selected_client['CLIENT_ID']
    
    with col2:
        st.metric("Fitness Level", selected_client['FITNESS_LEVEL'])
    
    st.divider()
    
    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        date_range_option = st.radio("Select Date Range", ["This Week", "Next Week", "This Month", "Custom Range"])
    
    with col2:
        if date_range_option == "This Week":
            today = datetime.now().date()
            # Get Monday of this week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            st.write(f"**Start:** {start_date}")
        if date_range_option == "Next Week":
            today = datetime.now().date()
            # Get Monday of this week
            start_date = today - timedelta(days=today.weekday()) + timedelta(days=7)
            end_date = start_date + timedelta(days=13)
            st.write(f"**Start:** {start_date}")
        elif date_range_option == "This Month":
            today = datetime.now().date()
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            st.write(f"**Start:** {start_date}")
        else:
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=7), key="workout_range_start")
            with col_end:
                end_date = st.date_input("End Date", value=datetime.now().date(), key="workout_range_end")
            st.write(f"**Range:** {start_date} to {end_date}")
    
    with col3:
        if date_range_option != "Custom Range":
            if date_range_option == "This Month":
                st.write(f"**End:** {end_date}")
            else:
                st.write(f"**End:** {end_date}")
    
    st.divider()
    
    # Fetch workouts for the date range
    workouts_df = get_client_workouts_by_date_range(client_id, start_date, end_date)
    
    if workouts_df.empty:
        st.info(f"No workouts found for {selected_client_name} in the selected date range.")
    else:
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_workouts = len(workouts_df[workouts_df['WORKOUT_FOCUS'] != 'Rest Day'])
        rest_days = len(workouts_df[workouts_df['WORKOUT_FOCUS'] == 'Rest Day'])
        total_duration = workouts_df[workouts_df['WORKOUT_FOCUS'] != 'Rest Day']['DURATION_MIN'].sum()
        avg_duration = total_duration / total_workouts if total_workouts > 0 else 0
        
        col1.metric("Training Days", total_workouts)
        col2.metric("Rest Days", rest_days)
        col3.metric("Total Duration", f"{int(total_duration)} min")
        col4.metric("Avg Duration", f"{int(avg_duration)} min")
        
        st.divider()
        
        # Display by focus
        st.markdown("### Workouts by Focus Area")
        focus_counts = workouts_df[workouts_df['WORKOUT_FOCUS'] != 'Rest Day']['WORKOUT_FOCUS'].value_counts()
        if not focus_counts.empty:
            fig = px.bar(focus_counts, title="Workout Focus Distribution", labels={'index': 'Focus Area', 'value': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Detailed workout list
        st.markdown("### Detailed Workouts")
        
        for _, workout in workouts_df.iterrows():
            workout_date = workout.get('WORKOUT_DATE', 'N/A')
            focus = workout['WORKOUT_FOCUS']
            
            if focus == 'Rest Day':
                with st.expander(f"📅 {workout_date} - 🔄 Rest Day"):
                    st.info(workout.get('WARM_UP', 'Rest day - focus on recovery'))
            else:
                with st.expander(f"📅 {workout_date} - 💪 {focus} ({workout['DURATION_MIN']} min)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Warm-up:**")
                        st.write(workout.get('WARM_UP', 'N/A'))
                    with col2:
                        st.markdown("**Cool-down:**")
                        st.write(workout.get('COOL_DOWN', 'N/A'))
                    
                    st.markdown("**Exercises:**")
                    exercises = workout.get('EXERCISES')
                    if exercises:
                        if isinstance(exercises, str):
                            exercises = json.loads(exercises)
                        for i, exercise in enumerate(exercises, 1):
                            ex_col1, ex_col2, ex_col3 = st.columns([2, 1, 2])
                            with ex_col1:
                                st.write(f"**{exercise.get('name', 'N/A')}**")
                            with ex_col2:
                                st.write(f"{exercise.get('sets', 0)}x{exercise.get('reps', '0')}")
                            with ex_col3:
                                st.write(f"Rest: {exercise.get('rest_sec', 0)}s")
        
        st.divider()
        
        # Raw data table
        st.markdown("### Raw Data")
        st.dataframe(
            workouts_df[['WORKOUT_ID', 'WORKOUT_DATE', 'GENERATION_DATE', 'WORKOUT_WEEK', 'WORKOUT_DAY', 'WORKOUT_FOCUS', 'DURATION_MIN']],
            use_container_width=True,
            hide_index=True
        )


def page_exercise_results():
    st.title("🏋️ Record Exercise Results")
    st.markdown("Record per-set exercise results (weight, reps, RPE, rest, notes)")

    clients_df = get_clients()
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return

    selected_client_name = st.selectbox("Select Client", clients_df['CLIENT_NAME'].tolist(), key="er_client_select")
    selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
    client_id = selected_client['CLIENT_ID']

    st.divider()

    # Choose a workout for this client
    workouts_df = get_client_workouts(client_id)
    if workouts_df.empty:
        st.info("No workouts found for this client. Generate a workout first.")
        return

    # format workout display
    workouts_df['DISPLAY'] = workouts_df.apply(lambda r: f"{r['WORKOUT_DATE']} | Week {r['WORKOUT_WEEK']} Day {r['WORKOUT_DAY']} | {r['WORKOUT_FOCUS']}", axis=1)
    workout_choice = st.selectbox("Select Workout", workouts_df['DISPLAY'].tolist(), key="er_workout_select")
    workout_row = workouts_df[workouts_df['DISPLAY'] == workout_choice].iloc[0]
    workout_id = workout_row['WORKOUT_ID']
    workout_date = workout_row.get('WORKOUT_DATE')

    # Parse exercises JSON stored in the workout
    exercises = workout_row.get('EXERCISES', [])
    if isinstance(exercises, str):
        exercises = json.loads(exercises)

    if not exercises:
        st.info("No exercises found in the selected workout.")
        return

    st.markdown(f"**Workout:** {workout_choice}")

    # Select exercise
    exercise_names = [f"{i+1}. {ex.get('name','Unnamed')}" for i, ex in enumerate(exercises)]
    ex_choice = st.selectbox("Select Exercise", exercise_names, key="er_ex_select")
    ex_index = exercise_names.index(ex_choice)
    exercise = exercises[ex_index]
    exercise_name = exercise.get('name')

    st.markdown(f"**Exercise:** {exercise_name}")

    # --- Progress panel: show aggregated metrics and weekly 1RM trend ---
    ex_id_for_progress = exercise.get('id') or exercise.get('exercise_id') or exercise_name
    progress = get_exercise_progress(client_id, ex_id_for_progress)
    trend_df = get_exercise_1rm_trend(client_id, ex_id_for_progress, weeks=12)

    with st.expander("Progress & Trend", expanded=True):
        if progress:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Estimated 1RM", f"{progress.get('estimated_1rm', 'N/A'):.1f}" if progress.get('estimated_1rm') else "N/A")
            c2.metric("Max Weight", f"{progress.get('max_weight_kg', 'N/A'):.1f} kg" if progress.get('max_weight_kg') else "N/A")
            c3.metric("Avg Reps", f"{progress.get('avg_reps', 'N/A'):.1f}" if progress.get('avg_reps') else "N/A")
            c4.metric("Sessions", f"{progress.get('sessions_recorded', 0)}")

            # Recent sets table (limit 8)
            recent = progress.get('recent_sets') or []
            if isinstance(recent, str):
                try:
                    recent = json.loads(recent)
                except Exception:
                    recent = []

            if recent:
                recent_tbl = pd.DataFrame(recent)
                if not recent_tbl.empty:
                    st.markdown("**Recent Sets (most recent first)**")
                    # show only a few columns for compact view
                    cols_to_show = [c for c in ['performed_date', 'set_number', 'reps', 'weight_kg', 'rpe', 'rest_seconds'] if c in recent_tbl.columns]
                    st.dataframe(recent_tbl[cols_to_show].head(8), use_container_width=True)
        else:
            st.info("No progress data available for this exercise yet.")

        # Trend chart (weekly estimated 1RM)
        if not trend_df.empty and 'estimated_1rm_max' in trend_df.columns:
            fig = px.line(trend_df, x='week_start', y='estimated_1rm_max', markers=True, title='Weekly Estimated 1RM (Epley)')
            fig.update_layout(xaxis_title='Week Start', yaxis_title='Estimated 1RM (kg)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough historical data to plot a weekly 1RM trend. Record some sets to see trends.")

    # Input performed date and sets
    col1, col2 = st.columns(2)
    with col1:
        performed_date = st.date_input("Performed Date", value=workout_date if workout_date else datetime.now().date(), key="er_date")
    with col2:
        default_sets = exercise.get('sets', 3)
        sets_to_record = st.number_input("Number of Sets to Record", min_value=1, max_value=20, value=default_sets, key="er_sets")

    # Dynamic inputs for each set
    set_entries = []
    for s in range(1, sets_to_record + 1):
        with st.expander(f"Set {s}", expanded=(s == 1)):
            c1, c2, c3, c4 = st.columns(4)
            reps = c1.number_input(f"Reps (Set {s})", min_value=0, max_value=100, value=exercise.get('reps', 0) if isinstance(exercise.get('reps'), int) else 10, key=f"er_{s}_reps")
            weight = c2.number_input(f"Weight (kg) (Set {s})", min_value=0.0, max_value=1000.0, value=0.0, format="%.2f", key=f"er_{s}_weight")
            rpe = c3.number_input(f"RPE (Set {s})", min_value=0.0, max_value=10.0, value=0.0, format="%.1f", key=f"er_{s}_rpe")
            rest = c4.number_input(f"Rest sec (Set {s})", min_value=0, max_value=600, value=exercise.get('rest_sec', 60), key=f"er_{s}_rest")
            duration = st.number_input(f"Duration sec (Set {s})", min_value=0, max_value=3600, value=0, key=f"er_{s}_dur")
            note = st.text_input(f"Notes (Set {s})", value="", key=f"er_{s}_notes")
            set_entries.append({
                'set_number': s,
                'reps': int(reps),
                'weight_kg': float(weight) if weight != 0.0 else None,
                'rpe': float(rpe) if rpe != 0.0 else None,
                'rest_seconds': int(rest) if rest != 0 else None,
                'duration_seconds': int(duration) if duration != 0 else None,
                'notes': note if note else None
            })

    if st.button("✅ Save Exercise Results", use_container_width=True, type="primary"):
        saved = 0
        for entry in set_entries:
            rid = insert_exercise_result(
                client_id=client_id,
                workout_id=workout_id,
                exercise_id=exercise.get('id') or exercise.get('exercise_id') or exercise_name,
                performed_date=performed_date,
                set_number=entry['set_number'],
                reps=entry['reps'],
                weight_kg=entry['weight_kg'],
                rpe=entry['rpe'],
                rest_seconds=entry['rest_seconds'],
                duration_seconds=entry['duration_seconds'],
                notes=entry['notes']
            )
            if rid:
                saved += 1

        if saved > 0:
            st.success(f"✅ Saved {saved} set result(s) for {exercise_name}")
        else:
            st.error("No results were saved. Check for errors above.")

# ============================================================================
# Page: Meal Plan Summary
# ============================================================================

def page_meal_plan_summary():
    st.title("🍽️ Meal Plan Summary")
    st.markdown("View meal plans for a selected date range")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_client_name = st.selectbox(
            "Select Client",
            clients_df['CLIENT_NAME'].tolist(),
            key="meal_summary_client"
        )
        selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
        client_id = selected_client['CLIENT_ID']
    
    with col2:
        st.metric("Target Calories", f"{selected_client.get('target_calories', 2000)} kcal")
    
    st.divider()
    
    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        date_range_option = st.radio("Select Date Range", ["This Week", "Next Week", "This Month", "Custom Range"], key="meal_date_range")
    
    with col2:
        if date_range_option == "This Week":
            today = datetime.now().date()
            # Get Monday of this week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            st.write(f"**Start:** {start_date}")
        if date_range_option == "Next Week":
            today = datetime.now().date()
            # Get Monday of this week
            start_date = today - timedelta(days=today.weekday()) + timedelta(days=7)
            end_date = start_date + timedelta(days=13)
            st.write(f"**Start:** {start_date}")
        elif date_range_option == "This Month":
            today = datetime.now().date()
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            st.write(f"**Start:** {start_date}")
        else:
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=7), key="meal_range_start")
            with col_end:
                end_date = st.date_input("End Date", value=datetime.now().date(), key="meal_range_end")
            st.write(f"**Range:** {start_date} to {end_date}")
    
    with col3:
        if date_range_option != "Custom Range":
            if date_range_option == "This Month":
                st.write(f"**End:** {end_date}")
            else:
                st.write(f"**End:** {end_date}")
    
    st.divider()
    
    # Fetch meal plans for the date range
    meal_plans_df = get_client_meal_plans_by_date_range(client_id, start_date, end_date)
    
    if meal_plans_df.empty:
        st.info(f"No meal plans found for {selected_client_name} in the selected date range.")
    else:
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_plans = len(meal_plans_df)
        avg_calories = meal_plans_df['TOTAL_CALORIES'].mean()
        avg_protein = meal_plans_df['PROTEIN_G'].mean()
        total_days_covered = meal_plans_df['DURATION_DAYS'].sum()
        
        col1.metric("Meal Plans", total_plans)
        col2.metric("Avg Calories", f"{int(avg_calories)} kcal")
        col3.metric("Avg Protein", f"{int(avg_protein)}g")
        col4.metric("Total Days Covered", int(total_days_covered))
        
        st.divider()
        
        # Display macro distribution
        st.markdown("### Macronutrient Distribution")
        macro_data = {
            'Nutrient': ['Protein', 'Carbs', 'Fat'],
            'Grams': [
                meal_plans_df['PROTEIN_G'].mean(),
                meal_plans_df['CARBS_G'].mean(),
                meal_plans_df['FAT_G'].mean()
            ]
        }
        macro_df = pd.DataFrame(macro_data)
        fig = px.pie(macro_df, values='Grams', names='Nutrient', title="Average Macro Split")
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Detailed meal plans
        st.markdown("### Meal Plans by Date")
        
        for _, meal_plan in meal_plans_df.iterrows():
            plan_start = meal_plan.get('PLAN_START_DATE', 'N/A')
            plan_end = plan_start + timedelta(days=meal_plan['DURATION_DAYS'] - 1) if plan_start != 'N/A' else 'N/A'
            week_num = meal_plan['PLAN_WEEK']
            
            with st.expander(f"📅 Week {week_num} ({plan_start} - {plan_end}) | {meal_plan['TOTAL_CALORIES']} kcal", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Calories", meal_plan['TOTAL_CALORIES'])
                col2.metric("Protein", f"{meal_plan['PROTEIN_G']}g")
                col3.metric("Carbs", f"{meal_plan['CARBS_G']}g")
                col4.metric("Fat", f"{meal_plan['FAT_G']}g")
                
                st.divider()
                
                # Parse meal plan JSON
                meal_plan_json = meal_plan.get('MEAL_PLAN_JSON')
                if meal_plan_json:
                    if isinstance(meal_plan_json, str):
                        meal_plan_json = json.loads(meal_plan_json)
                    
                    days = meal_plan_json.get('days', [])
                    for day in days:
                        day_num = day.get('day', 0)
                        st.markdown(f"**Day {day_num}**")
                        
                        meals = day.get('meals', [])
                        for meal in meals:
                            meal_type = meal.get('meal_type', 'meal').title()
                            meal_cal = meal.get('calories', 0)
                            meal_protein = meal.get('protein', 0)
                            
                            with st.expander(f"{meal_type} - {meal_cal} kcal, {meal_protein}g protein"):
                                foods = meal.get('foods', [])
                                for food in foods:
                                    st.write(f"• {food}")
        
        st.divider()
        
        # Raw data table
        st.markdown("### Raw Data")
        st.dataframe(
            meal_plans_df[['MEAL_PLAN_ID', 'GENERATION_DATE', 'PLAN_START_DATE', 'PLAN_WEEK', 'TOTAL_CALORIES', 'PROTEIN_G', 'CARBS_G', 'FAT_G']],
            use_container_width=True,
            hide_index=True
        )

# ============================================================================
# Page: Client Profiles
# ============================================================================

def page_client_profiles():
    st.title("👥 Client Profiles")
    st.markdown("View and manage client profiles")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.info("No clients found. Create a new client to get started!")
        return
    
    selected_client_name = st.selectbox(
        "Select Client to View",
        clients_df['CLIENT_NAME'].tolist(),
        key="profile_client_select"
    )
    
    selected_client = clients_df[clients_df['CLIENT_NAME'] == selected_client_name].iloc[0]
    
    st.markdown(f"## {selected_client['CLIENT_NAME']}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Age", f"{selected_client['AGE']} years")
    col2.metric("Height", f"{selected_client['HEIGHT_CM']} cm")
    col3.metric("Weight", f"{selected_client['CURRENT_WEIGHT_KG']:.2f} kg")
    col4.metric("Fitness Level", selected_client['FITNESS_LEVEL'])
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Goals & Preferences")
        st.write(f"**Fitness Goals:**")
        goals = selected_client['FITNESS_GOALS']
        if isinstance(goals, str):
            import json
            goals = json.loads(goals)
        for goal in goals:
            st.write(f"• {goal}")
        
        st.write(f"**Equipment Available:**")
        equipment = selected_client['AVAILABLE_EQUIPMENT']
        if isinstance(equipment, str):
            import json
            equipment = json.loads(equipment)
        for eq in equipment:
            st.write(f"• {eq}")
    
    with col2:
        st.markdown("### Training & Nutrition Targets")
        st.write(f"**Training Schedule:**")
        st.write(f"• {selected_client['DAYS_PER_WEEK']} days per week")
        st.write(f"• {selected_client['WORKOUT_DURATION_MIN']} minutes per session")
        
        st.write(f"**Nutrition Targets:**")
        if selected_client.get('target_calories'):
            st.write(f"• {selected_client['target_calories']} kcal/day")
        if selected_client.get('target_protein_g'):
            st.write(f"• {selected_client['target_protein_g']}g protein/day")
        
        if selected_client.get('allergies'):
            st.write(f"**Allergies/Restrictions:**")
            st.write(f"• {selected_client['allergies']}")

# ============================================================================
# Main Navigation
# ============================================================================

def main():
    # Sidebar Navigation
    st.sidebar.markdown("# 🏋️ AI Personal Trainer")
    st.sidebar.markdown("*Stage 1: Workout & Meal Plan Generation*")
    st.sidebar.divider()
    
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Workout Generator", "Record Exercise Results", "Meal Plan Generator", "Workout Summary", "Meal Plan Summary", "Weight Tracking", "Client Profiles"],
        # icons=["🏠", "💪", "📝", "🍽️", "📊", "📊", "⚖️", "👥"]
    )
    
    st.sidebar.divider()
    st.sidebar.markdown("### About Stage 1")
    st.sidebar.write("""
    This application uses **Snowflake Cortex Prompt Complete** to:
    - Generate personalized workouts
    - Create meal plans
    - Track client progress
    
    All data is stored securely in Snowflake.
    """)
    
    # Route to pages
    if page == "Home":
        page_home()
    elif page == "Workout Generator":
        page_workout_generator()
    elif page == "Record Exercise Results":
        page_exercise_results()
    elif page == "Meal Plan Generator":
        page_meal_plan_generator()
    elif page == "Workout Summary":
        page_workout_summary()
    elif page == "Meal Plan Summary":
        page_meal_plan_summary()
    elif page == "Weight Tracking":
        page_weight_tracking()
    elif page == "Client Profiles":
        page_client_profiles()

if __name__ == "__main__":
    main()
