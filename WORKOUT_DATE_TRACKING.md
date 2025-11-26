# Workout Date Tracking Implementation

**Date:** November 26, 2025  
**Status:** ✅ Complete  
**Files Modified:**
- `sql/02_stage1_create_tables.sql` - Added workout_date column
- `streamlit_app/app.py` - Updated UI and save logic

---

## 📝 Changes Made

### 1. Database Schema Update

**File:** `sql/02_stage1_create_tables.sql`

Added new column to `generated_workouts` table:

```sql
CREATE TABLE IF NOT EXISTS generated_workouts (
  workout_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  workout_date DATE COMMENT 'Scheduled date for this workout',  -- NEW
  generation_date TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  workout_week NUMBER(2,0) NOT NULL,
  ...
)
```

**Purpose:** Track the scheduled date for each workout so clients can plan and keep track of their training schedule.

**Column Details:**
- `workout_date`: DATE type (nullable)
- Stores the scheduled/planned date for each workout
- Different from `generation_date` (when the workout was created by AI)
- Allows filtering and sorting by calendar date

---

### 2. Streamlit App Updates

#### A. Date Input in UI

**File:** `streamlit_app/app.py` (line ~655)

Added date picker to the "Generate Full Week" tab:

```python
col1, col2 = st.columns(2)
with col1:
    week = st.number_input("Week Number", min_value=1, max_value=52, value=1)
with col2:
    start_date = st.date_input(
        "Start Date (Monday of this week)", 
        value=datetime.now().date(), 
        help="First day of the workout week"
    )
```

**User Experience:**
- Two inputs side-by-side: Week number + Start date
- Date defaults to today
- Placeholder text: "Start Date (Monday of this week)"
- Tooltip explains this is the first day of the workout week

---

#### B. Updated `save_weekly_workouts()` Function

**File:** `streamlit_app/app.py` (line ~355)

Function now accepts and uses the start date:

```python
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
            
            # ... insert with workout_date
```

**Key Features:**
- Accepts optional `start_date` parameter
- Defaults to today if not provided
- Calculates individual dates for each day:
  - Day 1: start_date + 0 days
  - Day 2: start_date + 1 day
  - Day 3: start_date + 2 days
  - ... and so on through Day 7

---

#### C. Updated Database Inserts

**Rest Days:**
```python
INSERT INTO TRAINING_DB.PUBLIC.generated_workouts
(workout_id, client_id, workout_date, workout_week, workout_day, ...)
SELECT
'{workout_id}',
'{client_id}',
'{workout_date}',  -- NEW
{week},
{day_num},
...
```

**Training Days:**
```python
INSERT INTO TRAINING_DB.PUBLIC.generated_workouts
(workout_id, client_id, workout_date, workout_week, workout_day, ...)
SELECT
'{workout_id}',
'{client_id}',
'{workout_date}',  -- NEW
{week},
{day_num},
...
```

---

#### D. Updated Function Call

**File:** `streamlit_app/app.py` (line ~745)

Pass start_date when saving:

```python
saved_count = save_weekly_workouts(
    client_id, 
    st.session_state.weekly_data, 
    prompt, 
    start_date=start_date  # NEW
)
```

---

#### E. Updated History Display

**File:** `streamlit_app/app.py` (line ~757)

Added WORKOUT_DATE to the displayed columns:

```python
st.dataframe(
    workouts_df[['WORKOUT_ID', 'WORKOUT_DATE', 'GENERATION_DATE', 'WORKOUT_WEEK', 'WORKOUT_DAY', 'WORKOUT_FOCUS']],
    use_container_width=True,
    hide_index=True
)
```

**Columns Displayed (in order):**
1. WORKOUT_ID - Unique identifier
2. **WORKOUT_DATE** - Scheduled date (NEW)
3. GENERATION_DATE - When AI created it
4. WORKOUT_WEEK - Week number
5. WORKOUT_DAY - Day 1-7
6. WORKOUT_FOCUS - Muscle group/focus

---

## 🔄 Workflow

### User Generates a Week

1. **Input:**
   - Select client
   - Enter Week Number (e.g., 1)
   - Select Start Date (e.g., Monday Nov 27, 2025)

2. **AI Generation:**
   - AI reviews previous 4 weeks
   - Generates full 7-day program
   - User reviews and accepts

3. **Database Save:**
   - Day 1 (Monday): Monday Nov 27, 2025
   - Day 2 (Tuesday): Tuesday Nov 28, 2025
   - Day 3 (Wednesday): Wednesday Nov 29, 2025
   - Day 4 (Thursday): Thursday Nov 30, 2025
   - Day 5 (Friday): Friday Dec 1, 2025
   - Day 6 (Saturday): Saturday Dec 2, 2025
   - Day 7 (Sunday): Sunday Dec 3, 2025

4. **View History:**
   - All 7 workouts displayed with dates
   - Can see exact calendar dates for each workout
   - Easy to track and plan around schedule

---

## 📊 Example Data

| WORKOUT_ID | WORKOUT_DATE | GENERATION_DATE | WORKOUT_WEEK | WORKOUT_DAY | WORKOUT_FOCUS |
|---|---|---|---|---|---|
| uuid-1 | 2025-11-27 | 2025-11-26 14:32 | 1 | 1 | Upper Body Strength |
| uuid-2 | 2025-11-28 | 2025-11-26 14:32 | 1 | 2 | Rest Day |
| uuid-3 | 2025-11-29 | 2025-11-26 14:32 | 1 | 3 | Lower Body Power |
| uuid-4 | 2025-11-30 | 2025-11-26 14:32 | 1 | 4 | Pull Day |
| uuid-5 | 2025-12-01 | 2025-11-26 14:32 | 1 | 5 | Push Day |
| uuid-6 | 2025-12-02 | 2025-11-26 14:32 | 1 | 6 | Rest Day |
| uuid-7 | 2025-12-03 | 2025-11-26 14:32 | 1 | 7 | Full Body |

---

## ✅ Benefits

1. **Client Tracking**
   - Know exactly when to do each workout
   - Can see full week at a glance with calendar dates

2. **Schedule Planning**
   - Identify rest days
   - Plan around life events
   - Track multiple weeks visually

3. **Progress Logging** (future)
   - Can log workout completion on specific dates
   - Track actual vs. planned dates
   - Identify patterns

4. **Reporting** (future)
   - Filter workouts by date range
   - Generate workout calendars
   - Track adherence over time

---

## 🚀 Deployment

**No breaking changes** - the column is optional (nullable), so existing data isn't affected.

**Migration steps:**
1. Run updated `02_stage1_create_tables.sql`
2. Deploy updated `app.py`
3. New workouts will include dates
4. Old workouts (if any) will have NULL dates

---

## 📝 SQL Verification

To verify the date is being stored correctly:

```sql
SELECT 
  WORKOUT_ID,
  WORKOUT_DATE,
  GENERATION_DATE,
  WORKOUT_WEEK,
  WORKOUT_DAY,
  WORKOUT_FOCUS
FROM TRAINING_DB.PUBLIC.generated_workouts
WHERE client_id = 'YOUR_CLIENT_ID'
ORDER BY WORKOUT_DATE ASC;
```

---

**Status:** ✅ Production Ready  
**Test Date:** November 26, 2025  
**Version:** 1.1.1
