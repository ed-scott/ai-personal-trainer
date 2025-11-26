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
    return Session.builder.configs(st.secrets["snowflake"]).create()

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
        VALUES ('{log_id}', '{event_type}', 'INFO', {f"'{client_id}'" if client_id else 'NULL'}, 
                {f"'{message}'" if message else 'NULL'}, PARSE_JSON('{context_json}'))
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
        {client_data['age']},
        '{client_data['gender']}',
        {client_data['current_weight_kg']},
        {client_data['height_cm']},
        '{client_data['fitness_level']}',
        PARSE_JSON('{json.dumps(client_data['fitness_goals'])}'),
        PARSE_JSON('{json.dumps(client_data['available_equipment'])}'),
        {client_data['days_per_week']},
        {client_data['workout_duration_min']},
        PARSE_JSON('{json.dumps(client_data['dietary_preferences'])}'),
        {f"'{client_data['allergies']}'" if client_data['allergies'] else 'NULL'},
        {client_data['target_calories'] if client_data['target_calories'] else 'NULL'},
        {client_data['target_protein_g'] if client_data['target_protein_g'] else 'NULL'}
        """
        
        session.sql(insert_sql).collect()
        log_event("client_created", client_id=client_id, message=f"Client {client_data['client_name']} created")
        return client_id
    except Exception as e:
        st.error(f"Error creating client: {str(e)}")
        return None

def generate_workout_cortex(client_id: str, client_data: dict):
    """Generate workout using Cortex Prompt Complete"""
    try:
        # Build prompt from client data
        fitness_goals = ', '.join(client_data['fitness_goals']) if isinstance(client_data['fitness_goals'], list) else client_data['fitness_goals']
        equipment = ', '.join(client_data['available_equipment']) if isinstance(client_data['available_equipment'], list) else client_data['available_equipment']
        
        prompt = f"""You are an expert personal trainer. Generate a detailed workout plan for a client.

Client Profile:
- Fitness Level: {client_data['fitness_level']}
- Goals: {fitness_goals}
- Available Equipment: {equipment}
- Days Available per Week: {client_data['days_per_week']}
- Preferred Duration: {client_data['workout_duration_min']} minutes

Generate a complete {client_data['workout_duration_min']}-minute workout including:
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
        # Try to extract JSON from response text
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
        fitness_goals = ', '.join(client_data['fitness_goals']) if isinstance(client_data['fitness_goals'], list) else client_data['fitness_goals']
        dietary_prefs = ', '.join(client_data['dietary_preferences']) if isinstance(client_data['dietary_preferences'], list) else client_data['dietary_preferences']
        
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
    """Save generated workout to database"""
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
        'Generated Workout',
        60,
        '{workout_data['warm_up'].replace("'", "''")}',
        PARSE_JSON('{json.dumps(workout_data['exercises'])}'),
        '{workout_data['cool_down'].replace("'", "''")}',
        '{prompt.replace("'", "''")}',
        'mistral-7b'
        """
        
        session.sql(insert_sql).collect()
        log_event("workout_generated", client_id=client_id, message="Workout generated and saved")
        return workout_id
    except Exception as e:
        st.error(f"Error saving workout: {str(e)}")
        return None

def save_meal_plan(client_id: str, meal_plan_data: dict, prompt: str, week: int = 1):
    """Save generated meal plan to database"""
    try:
        meal_plan_id = generate_uuid()
        totals = meal_plan_data['weekly_totals']
        
        insert_sql = f"""
        INSERT INTO TRAINING_DB.PUBLIC.meal_plans
        (meal_plan_id, client_id, plan_week, duration_days, total_calories, protein_g, 
         carbs_g, fat_g, meal_plan_json, cortex_prompt, cortex_model)
        SELECT
        '{meal_plan_id}',
        '{client_id}',
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
                        'client_name': client_name,
                        'age': age,
                        'gender': gender,
                        'current_weight_kg': current_weight_kg,
                        'height_cm': height_cm,
                        'fitness_level': fitness_level,
                        'fitness_goals': fitness_goals,
                        'available_equipment': available_equipment,
                        'days_per_week': days_per_week,
                        'workout_duration_min': workout_duration_min,
                        'dietary_preferences': dietary_preferences,
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
                clients_df[['client_id', 'client_name', 'age', 'fitness_level', 'current_weight_kg', 'created_at']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No clients found. Create a new client to get started!")

# ============================================================================
# Page: Workout Generator
# ============================================================================

def page_workout_generator():
    st.title("💪 Workout Generator")
    st.markdown("Generate personalized workouts using AI (Cortex Prompt Complete)")
    
    clients_df = get_clients()
    
    if clients_df.empty:
        st.warning("No clients found. Please create a client first in the Home page.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_client_name = st.selectbox(
            "Select Client",
            clients_df['client_name'].tolist()
        )
        selected_client = clients_df[clients_df['client_name'] == selected_client_name].iloc[0]
        client_id = selected_client['client_id']
    
    with col2:
        st.metric("Fitness Level", selected_client['fitness_level'])
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Generate New Workout", "View History"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            week = st.number_input("Week Number", min_value=1, max_value=52, value=1)
        
        with col2:
            day = st.number_input("Day of Week", min_value=1, max_value=7, value=1)
        
        if st.button("🤖 Generate Workout with AI", use_container_width=True, type="primary"):
            with st.spinner("Generating workout using Cortex Prompt Complete..."):
                workout_data, prompt = generate_workout_cortex(client_id, selected_client.to_dict())
                
                if workout_data:
                    st.success("✅ Workout generated successfully!")
                    
                    # Display workout
                    st.markdown("### Generated Workout")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Warm-up Duration", "5 min")
                    col2.metric("Main Workout", f"{selected_client['workout_duration_min']-10} min")
                    col3.metric("Cool-down", "5-10 min")
                    
                    st.markdown("#### Warm-up")
                    st.write(workout_data.get('warm_up', 'N/A'))
                    
                    st.markdown("#### Main Exercises")
                    exercises = workout_data.get('exercises', [])
                    for i, exercise in enumerate(exercises, 1):
                        with st.expander(f"Exercise {i}: {exercise['name']}", expanded=i==1):
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("Sets", exercise['sets'])
                            col2.metric("Reps", exercise['reps'])
                            col3.metric("Rest (sec)", exercise.get('rest_sec', 60))
                            st.write(f"**Notes:** {exercise.get('notes', 'N/A')}")
                    
                    st.markdown("#### Cool-down")
                    st.write(workout_data.get('cool_down', 'N/A'))
                    
                    st.divider()
                    
                    if st.button("💾 Save Workout to Database", use_container_width=True):
                        workout_id = save_workout(client_id, workout_data, prompt, week, day)
                        if workout_id:
                            st.success(f"✅ Workout saved! ID: {workout_id}")
    
    with tab2:
        st.markdown("### Workout History")
        workouts_df = get_client_workouts(client_id)
        
        if not workouts_df.empty:
            st.dataframe(
                workouts_df[['workout_id', 'generation_date', 'workout_week', 'workout_day', 'workout_focus']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No workouts generated yet. Create one using the generator above!")

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
            clients_df['client_name'].tolist(),
            key="meal_plan_client_select"
        )
        selected_client = clients_df[clients_df['client_name'] == selected_client_name].iloc[0]
        client_id = selected_client['client_id']
    
    with col2:
        st.metric("Target Calories", f"{selected_client.get('target_calories', 2000)} kcal")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Generate New Meal Plan", "View History"])
    
    with tab1:
        week = st.number_input("Week Number", min_value=1, max_value=52, value=1, key="meal_plan_week")
        
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
                    
                    st.divider()
                    
                    if st.button("💾 Save Meal Plan to Database", use_container_width=True, key="save_meal_plan"):
                        meal_plan_id = save_meal_plan(client_id, meal_plan_data, prompt, week)
                        if meal_plan_id:
                            st.success(f"✅ Meal plan saved! ID: {meal_plan_id}")
    
    with tab2:
        st.markdown("### Meal Plan History")
        meal_plans_df = get_client_meal_plans(client_id)
        
        if not meal_plans_df.empty:
            st.dataframe(
                meal_plans_df[['meal_plan_id', 'generation_date', 'plan_week', 'total_calories', 'protein_g']],
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
        clients_df['client_name'].tolist(),
        key="weight_tracking_client"
    )
    selected_client = clients_df[clients_df['client_name'] == selected_client_name].iloc[0]
    client_id = selected_client['client_id']
    
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
        clients_df['client_name'].tolist(),
        key="profile_client_select"
    )
    
    selected_client = clients_df[clients_df['client_name'] == selected_client_name].iloc[0]
    
    st.markdown(f"## {selected_client['client_name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Age", f"{selected_client['age']} years")
    col2.metric("Height", f"{selected_client['height_cm']} cm")
    col3.metric("Weight", f"{selected_client['current_weight_kg']:.2f} kg")
    col4.metric("Fitness Level", selected_client['fitness_level'])
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Goals & Preferences")
        st.write(f"**Fitness Goals:**")
        goals = selected_client['fitness_goals']
        if isinstance(goals, str):
            import json
            goals = json.loads(goals)
        for goal in goals:
            st.write(f"• {goal}")
        
        st.write(f"**Equipment Available:**")
        equipment = selected_client['available_equipment']
        if isinstance(equipment, str):
            import json
            equipment = json.loads(equipment)
        for eq in equipment:
            st.write(f"• {eq}")
    
    with col2:
        st.markdown("### Training & Nutrition Targets")
        st.write(f"**Training Schedule:**")
        st.write(f"• {selected_client['days_per_week']} days per week")
        st.write(f"• {selected_client['workout_duration_min']} minutes per session")
        
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
        ["Home", "Workout Generator", "Meal Plan Generator", "Weight Tracking", "Client Profiles"],
        icons=["🏠", "💪", "🍽️", "⚖️", "👥"]
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
    elif page == "Meal Plan Generator":
        page_meal_plan_generator()
    elif page == "Weight Tracking":
        page_weight_tracking()
    elif page == "Client Profiles":
        page_client_profiles()

if __name__ == "__main__":
    main()
