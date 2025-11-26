"""
AI Personal Trainer - Streamlit Native App
================================================

Main application entry point for the AI Personal Trainer app hosted in Snowflake.

This app provides:
- Client weigh-in tracking (manual entry)
- Workout logging with suggested vs actual performance
- Running session tracking
- Nutrition and meal planning
- Progress dashboards with AI insights

All data is stored in Snowflake tables (TRAINING_DB.PUBLIC).
Authentication and permissions are managed via Snowflake roles.

Usage:
    streamlit run app.py

Environment Requirements:
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SNOWFLAKE_ROLE
    - SNOWFLAKE_WAREHOUSE
    - SNOWFLAKE_DATABASE (default: TRAINING_DB)
    - SNOWFLAKE_SCHEMA (default: PUBLIC)
    - OPENAI_API_KEY (optional, for AI features)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from snowflake.snowpark.session import Session
from snowflake.snowpark import functions as F
import os
from typing import Optional, List, Dict
import logging

# ========================================================================
# CONFIGURATION & SETUP
# ========================================================================

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Personal Trainer",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
    }
    .header-title {
        color: #667eea;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ========================================================================
# SNOWFLAKE CONNECTION
# ========================================================================

@st.cache_resource
def get_snowflake_connection() -> Session:
    """
    Establish connection to Snowflake using environment variables.
    Connection is cached to avoid reconnecting on every script run.
    """
    try:
        connection_params = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "role": os.getenv("SNOWFLAKE_ROLE", "TRAINING_APP_ROLE"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "TRAINING_WH"),
            "database": os.getenv("SNOWFLAKE_DATABASE", "TRAINING_DB"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        }
        
        session = Session.builder.configs(connection_params).create()
        logger.info("✅ Connected to Snowflake")
        return session
    except Exception as e:
        logger.error(f"❌ Failed to connect to Snowflake: {str(e)}")
        st.error(f"Database connection failed: {str(e)}")
        st.stop()

# ========================================================================
# DATABASE HELPERS
# ========================================================================

def execute_query(session: Session, query: str) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame."""
    try:
        result = session.sql(query).to_pandas()
        return result
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        st.error(f"Query error: {str(e)}")
        return pd.DataFrame()

def execute_insert(session: Session, query: str) -> bool:
    """Execute an INSERT query."""
    try:
        session.sql(query).collect()
        return True
    except Exception as e:
        logger.error(f"Insert failed: {str(e)}")
        st.error(f"Insert error: {str(e)}")
        return False

def get_clients(session: Session) -> pd.DataFrame:
    """Get list of active clients."""
    query = """
    SELECT client_id, CONCAT(first_name, ' ', last_name) as client_name, email
    FROM CLIENTS
    ORDER BY first_name, last_name
    """
    return execute_query(session, query)

def get_trainers(session: Session) -> pd.DataFrame:
    """Get list of trainers."""
    query = """
    SELECT trainer_id, name, email
    FROM TRAINERS
    ORDER BY name
    """
    return execute_query(session, query)

def get_exercises(session: Session) -> pd.DataFrame:
    """Get list of exercises."""
    query = """
    SELECT exercise_id, name, category, equipment
    FROM EXERCISES
    ORDER BY name
    """
    return execute_query(session, query)

def get_client_recent_weighins(session: Session, client_id: str, days: int = 30) -> pd.DataFrame:
    """Get recent weigh-ins for a client."""
    query = f"""
    SELECT 
        date,
        weight_kg,
        body_fat_pct,
        muscle_mass_kg,
        notes
    FROM WEIGH_INS
    WHERE client_id = '{client_id}'
    AND date >= CURRENT_DATE - INTERVAL '{days} days'
    ORDER BY date DESC
    """
    return execute_query(session, query)

def get_client_progress(session: Session, client_id: str) -> pd.DataFrame:
    """Get client progress summary."""
    query = f"""
    SELECT *
    FROM CLIENT_PROGRESS_SUMMARY
    WHERE client_id = '{client_id}'
    """
    return execute_query(session, query)

# ========================================================================
# MAIN APPLICATION
# ========================================================================

def main():
    """Main application logic with multi-page navigation."""
    
    # Initialize session state
    if "session" not in st.session_state:
        st.session_state.session = get_snowflake_connection()
    
    session = st.session_state.session
    
    # ====================================================================
    # HEADER
    # ====================================================================
    
    st.markdown("# 💪 AI Personal Trainer")
    st.markdown("_AI-powered fitness tracking powered by Snowflake_")
    
    # ====================================================================
    # SIDEBAR NAVIGATION
    # ====================================================================
    
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            options=[
                "Dashboard",
                "📊 Progress",
                "⚖️ Weigh-In",
                "🏋️ Workouts",
                "🏃 Running",
                "🍽️ Nutrition",
                "⚙️ Settings"
            ]
        )
    
    # ====================================================================
    # PAGE ROUTING
    # ====================================================================
    
    if page == "Dashboard":
        show_dashboard(session)
    
    elif page == "📊 Progress":
        show_progress(session)
    
    elif page == "⚖️ Weigh-In":
        show_weighin(session)
    
    elif page == "🏋️ Workouts":
        show_workouts(session)
    
    elif page == "🏃 Running":
        show_running(session)
    
    elif page == "🍽️ Nutrition":
        show_nutrition(session)
    
    elif page == "⚙️ Settings":
        show_settings(session)

# ========================================================================
# PAGE: DASHBOARD
# ========================================================================

def show_dashboard(session: Session):
    """Dashboard overview page."""
    st.subheader("Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        stats = execute_query(session, "SELECT COUNT(*) as count FROM CLIENTS")
        if not stats.empty:
            st.metric("Total Clients", stats.iloc[0]['COUNT'])
    
    with col2:
        stats = execute_query(session, "SELECT COUNT(*) as count FROM TRAINERS")
        if not stats.empty:
            st.metric("Trainers", stats.iloc[0]['COUNT'])
    
    with col3:
        stats = execute_query(session, "SELECT COUNT(*) as count FROM WORKOUTS WHERE date >= CURRENT_DATE - 7")
        if not stats.empty:
            st.metric("Workouts (7d)", stats.iloc[0]['COUNT'])
    
    with col4:
        stats = execute_query(session, "SELECT COUNT(*) as count FROM RUNNING_SESSIONS WHERE date >= CURRENT_DATE - 7")
        if not stats.empty:
            st.metric("Running (7d)", stats.iloc[0]['COUNT'])
    
    st.divider()
    
    # Recent activity
    st.subheader("Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recent Weigh-Ins**")
        weighins = execute_query(session, """
        SELECT 
            c.first_name || ' ' || c.last_name as client,
            w.date,
            w.weight_kg
        FROM WEIGH_INS w
        JOIN CLIENTS c ON w.client_id = c.client_id
        ORDER BY w.date DESC
        LIMIT 10
        """)
        st.dataframe(weighins, use_container_width=True)
    
    with col2:
        st.write("**Recent Workouts**")
        workouts = execute_query(session, """
        SELECT 
            c.first_name || ' ' || c.last_name as client,
            w.date,
            w.type
        FROM WORKOUTS w
        JOIN CLIENTS c ON w.client_id = c.client_id
        ORDER BY w.date DESC
        LIMIT 10
        """)
        st.dataframe(workouts, use_container_width=True)

# ========================================================================
# PAGE: PROGRESS
# ========================================================================

def show_progress(session: Session):
    """Client progress tracking page."""
    st.subheader("Client Progress")
    
    clients = get_clients(session)
    if clients.empty:
        st.warning("No clients found")
        return
    
    selected_client = st.selectbox(
        "Select Client",
        options=clients['CLIENT_ID'].tolist(),
        format_func=lambda x: clients[clients['CLIENT_ID'] == x]['CLIENT_NAME'].values[0]
    )
    
    # Get progress data
    progress = get_client_progress(session, selected_client)
    
    if not progress.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Workouts", int(progress.iloc[0].get('TOTAL_WORKOUTS', 0)))
        with col2:
            st.metric("Total Running", f"{progress.iloc[0].get('TOTAL_RUNNING_DISTANCE', 0):.1f} km")
        with col3:
            st.metric("Latest Weight", f"{progress.iloc[0].get('LATEST_WEIGHT', 0):.1f} kg")
    
    # Weight trend
    st.subheader("Weight Trend")
    weighins = get_client_recent_weighins(session, selected_client, days=90)
    
    if not weighins.empty:
        weighins['DATE'] = pd.to_datetime(weighins['DATE'])
        weighins = weighins.sort_values('DATE')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=weighins['DATE'],
            y=weighins['WEIGHT_KG'],
            mode='lines+markers',
            name='Weight',
            line=dict(color='#667eea', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Weight Trend (90 days)",
            xaxis_title="Date",
            yaxis_title="Weight (kg)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# ========================================================================
# PAGE: WEIGH-IN
# ========================================================================

def show_weighin(session: Session):
    """Weigh-in entry page."""
    st.subheader("Log Weigh-In")
    
    clients = get_clients(session)
    if clients.empty:
        st.warning("No clients found. Please add clients first.")
        return
    
    with st.form("weighin_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_id = st.selectbox(
                "Client",
                options=clients['CLIENT_ID'].tolist(),
                format_func=lambda x: clients[clients['CLIENT_ID'] == x]['CLIENT_NAME'].values[0]
            )
            weighin_date = st.date_input("Date", value=datetime.now().date())
        
        with col2:
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, step=0.1)
            body_fat_pct = st.number_input("Body Fat %", min_value=0.0, max_value=100.0, step=0.1, value=0.0)
        
        muscle_mass_kg = st.number_input("Muscle Mass (kg)", min_value=0.0, max_value=300.0, step=0.1, value=0.0)
        entry_source = st.selectbox("Entry Source", options=["manual", "device", "import"])
        notes = st.text_area("Notes", max_chars=500)
        
        if st.form_submit_button("💾 Save Weigh-In"):
            # Generate ID
            weighin_id = f"WEIGHIN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{np.random.randint(10000)}"
            
            # Insert into database
            insert_query = f"""
            INSERT INTO WEIGH_INS 
            (weighin_id, client_id, date, weight_kg, body_fat_pct, muscle_mass_kg, 
             entry_source, entered_by, notes, created_at)
            VALUES (
                '{weighin_id}',
                '{client_id}',
                '{weighin_date}',
                {weight_kg},
                {body_fat_pct if body_fat_pct > 0 else 'NULL'},
                {muscle_mass_kg if muscle_mass_kg > 0 else 'NULL'},
                '{entry_source}',
                CURRENT_USER(),
                '{notes.replace("'", "''")}',
                CURRENT_TIMESTAMP()
            )
            """
            
            if execute_insert(session, insert_query):
                st.success("✅ Weigh-in saved!")
            else:
                st.error("❌ Failed to save weigh-in")

# ========================================================================
# PAGE: WORKOUTS
# ========================================================================

def show_workouts(session: Session):
    """Workout logging page."""
    st.subheader("Log Workout")
    
    clients = get_clients(session)
    exercises = get_exercises(session)
    
    if clients.empty or exercises.empty:
        st.warning("Missing clients or exercises. Please set up data first.")
        return
    
    with st.form("workout_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_id = st.selectbox(
                "Client",
                options=clients['CLIENT_ID'].tolist(),
                format_func=lambda x: clients[clients['CLIENT_ID'] == x]['CLIENT_NAME'].values[0]
            )
            workout_date = st.date_input("Date", value=datetime.now().date())
        
        with col2:
            workout_type = st.selectbox("Workout Type", options=["gym", "crossfit", "yoga", "other"])
            start_time = st.time_input("Start Time")
        
        # Exercises
        st.write("**Add Exercises**")
        num_exercises = st.number_input("Number of exercises", min_value=1, max_value=10, value=1)
        
        exercises_data = []
        for i in range(num_exercises):
            with st.expander(f"Exercise {i+1}"):
                exercise_id = st.selectbox(
                    "Exercise",
                    options=exercises['EXERCISE_ID'].tolist(),
                    format_func=lambda x: exercises[exercises['EXERCISE_ID'] == x]['NAME'].values[0],
                    key=f"exercise_{i}"
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    suggested_sets = st.number_input("Suggested Sets", min_value=1, value=3, key=f"sug_sets_{i}")
                with col2:
                    suggested_reps = st.text_input("Suggested Reps", value="8-12", key=f"sug_reps_{i}")
                with col3:
                    suggested_weight = st.number_input("Suggested Weight (kg)", value=0.0, key=f"sug_weight_{i}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    actual_sets = st.number_input("Actual Sets", min_value=1, value=3, key=f"act_sets_{i}")
                with col2:
                    actual_reps = st.text_input("Actual Reps", value="8-12", key=f"act_reps_{i}")
                with col3:
                    actual_weight = st.number_input("Actual Weight (kg)", value=0.0, key=f"act_weight_{i}")
                
                rpe = st.slider("RPE (Perceived Exertion)", 1, 10, 5, key=f"rpe_{i}")
                
                exercises_data.append({
                    'exercise_id': exercise_id,
                    'suggested_sets': suggested_sets,
                    'suggested_reps': suggested_reps,
                    'suggested_weight_kg': suggested_weight,
                    'actual_sets': actual_sets,
                    'actual_reps': actual_reps,
                    'actual_weight_kg': actual_weight,
                    'rpe': rpe
                })
        
        notes = st.text_area("Workout Notes", max_chars=1000)
        
        if st.form_submit_button("💾 Save Workout"):
            # Generate workout ID
            workout_id = f"WO_{datetime.now().strftime('%Y%m%d%H%M%S')}_{np.random.randint(10000)}"
            
            # Insert workout
            insert_query = f"""
            INSERT INTO WORKOUTS 
            (workout_id, client_id, date, start_time, type, notes, created_at)
            VALUES (
                '{workout_id}',
                '{client_id}',
                '{workout_date}',
                '{start_time}',
                '{workout_type}',
                '{notes.replace("'", "''")}',
                CURRENT_TIMESTAMP()
            )
            """
            
            if execute_insert(session, insert_query):
                st.success("✅ Workout saved!")
            else:
                st.error("❌ Failed to save workout")

# ========================================================================
# PAGE: RUNNING
# ========================================================================

def show_running(session: Session):
    """Running session logging page."""
    st.subheader("Log Running Session")
    
    clients = get_clients(session)
    if clients.empty:
        st.warning("No clients found")
        return
    
    with st.form("running_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_id = st.selectbox(
                "Client",
                options=clients['CLIENT_ID'].tolist(),
                format_func=lambda x: clients[clients['CLIENT_ID'] == x]['CLIENT_NAME'].values[0]
            )
            session_date = st.date_input("Date", value=datetime.now().date())
        
        with col2:
            suggested_type = st.selectbox("Run Type", options=["easy", "tempo", "intervals", "long", "recovery", "speed_work"])
            suggested_distance = st.number_input("Suggested Distance (km)", value=5.0, step=0.1)
        
        suggested_pace_sec = st.number_input("Suggested Pace (sec/km)", value=300, step=10)
        
        st.divider()
        st.write("**Actual Performance**")
        
        col1, col2 = st.columns(2)
        with col1:
            actual_distance = st.number_input("Actual Distance (km)", value=5.0, step=0.1)
            actual_type = st.selectbox("Actual Run Type", options=["easy", "tempo", "intervals", "long", "recovery", "speed_work"])
        
        with col2:
            actual_duration = st.number_input("Actual Duration (seconds)", value=1500, step=10)
            calories = st.number_input("Calories (optional)", value=0, step=10)
        
        device = st.text_input("Device/App", placeholder="e.g., Strava, Apple Watch")
        notes = st.text_area("Notes", max_chars=500)
        
        if st.form_submit_button("💾 Save Running Session"):
            # Calculate actual pace
            if actual_distance > 0:
                actual_pace_sec = actual_duration / actual_distance
            else:
                actual_pace_sec = 0
            
            run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{np.random.randint(10000)}"
            
            insert_query = f"""
            INSERT INTO RUNNING_SESSIONS
            (run_id, client_id, date, suggested_distance_km, suggested_pace_sec_per_km, 
             suggested_type, actual_distance_km, actual_duration_sec, actual_pace_sec_per_km, 
             actual_type, calories, device, notes, created_at)
            VALUES (
                '{run_id}',
                '{client_id}',
                '{session_date}',
                {suggested_distance},
                {suggested_pace_sec},
                '{suggested_type}',
                {actual_distance},
                {actual_duration},
                {actual_pace_sec:.2f},
                '{actual_type}',
                {calories if calories > 0 else 'NULL'},
                '{device.replace("'", "''")}',
                '{notes.replace("'", "''")}',
                CURRENT_TIMESTAMP()
            )
            """
            
            if execute_insert(session, insert_query):
                st.success("✅ Running session saved!")
            else:
                st.error("❌ Failed to save running session")

# ========================================================================
# PAGE: NUTRITION
# ========================================================================

def show_nutrition(session: Session):
    """Nutrition logging page."""
    st.subheader("Nutrition Tracking")
    
    clients = get_clients(session)
    if clients.empty:
        st.warning("No clients found")
        return
    
    st.info("Nutrition tracking features coming soon!")

# ========================================================================
# PAGE: SETTINGS
# ========================================================================

def show_settings(session: Session):
    """Settings and configuration page."""
    st.subheader("Settings")
    
    # Database info
    st.write("**Database Configuration**")
    db_info = execute_query(session, "SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_USER(), CURRENT_ROLE()")
    
    if not db_info.empty:
        row = db_info.iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Database", row[0])
            st.metric("User", row[2])
        with col2:
            st.metric("Schema", row[1])
            st.metric("Role", row[3])
    
    st.divider()
    
    # Data management
    st.write("**Data Management**")
    if st.button("🔄 Refresh Cache"):
        st.cache_resource.clear()
        st.success("Cache refreshed!")
    
    st.divider()
    
    # System info
    st.write("**System Information**")
    sys_info = execute_query(session, """
    SELECT 
        COUNT(*) as total_tables,
        CURRENT_TIMESTAMP() as server_time
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'PUBLIC'
    """)
    
    if not sys_info.empty:
        st.write(sys_info)

# ========================================================================
# RUN APPLICATION
# ========================================================================

if __name__ == "__main__":
    main()
