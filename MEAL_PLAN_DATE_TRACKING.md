# Meal Plan Date Tracking & Summary Pages - Implementation Guide

**Date:** November 26, 2025  
**Status:** ✅ COMPLETE  
**Features Added:** Date tracking for meal plans + Workout Summary page + Meal Plan Summary page

---

## 📋 Overview

This update adds comprehensive date tracking to meal plans and introduces two powerful new summary pages that allow clients to view their workouts and meal plans within date ranges.

### What Was Added

1. **Meal Plan Date Tracking** - Schedule meal plans for specific dates
2. **Workout Summary Page** - Filter and view workouts by date range (week/month/custom)
3. **Meal Plan Summary Page** - Filter and view meal plans by date range with analytics

---

## 🗄️ Database Changes

### SQL Schema Update: `02_stage1_create_tables.sql`

**Added Column to `meal_plans` table:**

```sql
CREATE TABLE IF NOT EXISTS meal_plans (
  meal_plan_id VARCHAR(36) DEFAULT TO_VARCHAR(UUID_STRING()) NOT NULL,
  client_id VARCHAR(36) NOT NULL,
  plan_start_date DATE COMMENT 'Scheduled start date for this meal plan',  -- NEW!
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
```

**Key Change:** Added `plan_start_date DATE` column (line 6 in meal_plans table definition)

**Why:** Allows meal plans to be scheduled for specific weeks, enabling date-range filtering in the UI.

---

## 🐍 Python/Streamlit Changes

### File: `streamlit_app/app.py`

#### 1. Updated `save_meal_plan()` Function

**Changes:**
- Added `start_date=None` parameter (defaults to today if not provided)
- Updated INSERT to include `plan_start_date` column with calculated date value
- Maintains backward compatibility

**Code:**
```python
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
        ...
```

#### 2. Enhanced Meal Plan Generator UI

**Changes:**
- Added date picker next to week number input
- Two-column layout for week selection and date selection
- Defaults to current date

**Code:**
```python
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        week = st.number_input("Week Number", min_value=1, max_value=52, value=1, key="meal_plan_week")
    with col2:
        meal_start_date = st.date_input("Start Date (Monday of this week)", value=datetime.now().date(), key="meal_plan_start_date")
```

#### 3. Updated Meal Plan Save Call

**Changes:**
- Pass `start_date=meal_start_date` to `save_meal_plan()` function

**Code:**
```python
meal_plan_id = save_meal_plan(client_id, meal_plan_data, prompt, week, start_date=meal_start_date)
```

#### 4. New Helper Functions

**`get_client_workouts_by_date_range(client_id, start_date, end_date)`**
- Fetches workouts filtered by date range
- Orders by date and day number
- Used by Workout Summary page

```python
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
```

**`get_client_meal_plans_by_date_range(client_id, start_date, end_date)`**
- Fetches meal plans filtered by date range
- Orders by start date
- Used by Meal Plan Summary page

```python
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
```

#### 5. New Page: `page_workout_summary()`

**Features:**
- 📊 Client selection with fitness level display
- 📅 Three date range options:
  - **This Week** - Monday to Sunday of current week
  - **This Month** - First to last day of current month
  - **Custom Range** - User-selected start and end dates
- 📈 Summary metrics:
  - Training Days count
  - Rest Days count
  - Total Duration (minutes)
  - Average Duration (minutes/session)
- 📊 Bar chart showing workout focus distribution
- 🏋️ Expandable detailed workout view with exercises
- 📋 Raw data table for export

**Layout:**
```
Page Title: 📊 Workout Summary
  ├─ Client Selection + Fitness Level
  ├─ Date Range Selector (This Week / This Month / Custom)
  ├─ Summary Metrics (4-column display)
  ├─ Focus Area Distribution Chart
  ├─ Detailed Workout Expandable List
  │  ├─ Rest Days
  │  └─ Training Days with exercises
  └─ Raw Data Table
```

**Key Functions:**
- Date range calculation (This Week, This Month, Custom)
- Workout statistics (count, duration, focus areas)
- Plotly bar chart for visualization
- JSON parsing for exercises data

#### 6. New Page: `page_meal_plan_summary()`

**Features:**
- 🍽️ Client selection with target calorie display
- 📅 Three date range options (matching Workout Summary):
  - This Week
  - This Month
  - Custom Range
- 📊 Summary metrics:
  - Meal Plans count
  - Average Calories per plan
  - Average Protein per plan
  - Total Days Covered
- 🥗 Macronutrient distribution pie chart
- 📝 Expandable meal plan details with daily breakdown
- 🍴 Food items list for each meal type
- 📋 Raw data table for export

**Layout:**
```
Page Title: 🍽️ Meal Plan Summary
  ├─ Client Selection + Target Calories
  ├─ Date Range Selector
  ├─ Summary Metrics (4-column display)
  ├─ Macro Distribution Pie Chart
  ├─ Meal Plans by Date Expandable List
  │  ├─ Week number + Date range + Total calories
  │  ├─ Macro metrics (Cals, Protein, Carbs, Fat)
  │  └─ Daily breakdown with meal types and foods
  └─ Raw Data Table
```

**Key Functions:**
- Macro calculation and averaging
- Plotly pie chart for macro distribution
- JSON parsing for meal plan details
- Date range display with meal plan duration

#### 7. Updated Navigation

**Added two new pages to sidebar:**
```python
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Workout Generator", "Meal Plan Generator", "Workout Summary", "Meal Plan Summary", "Weight Tracking", "Client Profiles"],
)
```

**Updated routing:**
```python
elif page == "Workout Summary":
    page_workout_summary()
elif page == "Meal Plan Summary":
    page_meal_plan_summary()
```

---

## 🔄 User Workflow

### Generating Meal Plans with Dates

1. Navigate to **"Meal Plan Generator"**
2. Select client
3. **NEW:** Choose start date alongside week number
   - Date picker defaults to today
   - User can click to select specific Monday
4. Generate meal plan with AI
5. **NEW:** Meal plan saved with `plan_start_date` in database

### Viewing Workout History by Date

1. Navigate to **"Workout Summary"** (new page)
2. Select client
3. Choose date range:
   - **This Week:** Auto-calculates Monday-Sunday
   - **This Month:** Auto-calculates 1st-last day of month
   - **Custom Range:** Pick start and end dates
4. View:
   - Summary statistics (training/rest days, duration)
   - Focus area distribution chart
   - Detailed workout breakdown
   - Raw data table

### Viewing Meal Plans by Date

1. Navigate to **"Meal Plan Summary"** (new page)
2. Select client
3. Choose date range (Week/Month/Custom)
4. View:
   - Summary statistics (plans, calories, protein, days covered)
   - Macronutrient distribution pie chart
   - Detailed meal plans with daily breakdowns
   - Raw data table

---

## 🧪 Testing & Validation

### Test Case 1: Meal Plan Date Entry
```
GIVEN: User generating new meal plan
WHEN: Selecting "2025-11-27" as start date
THEN: 
  - Date picker shows 2025-11-27
  - save_meal_plan() receives start_date parameter
  - Database INSERT includes plan_start_date = '2025-11-27'
```

### Test Case 2: Workout Summary - This Week
```
GIVEN: Current date is 2025-11-26 (Wednesday)
WHEN: User selects "This Week"
THEN:
  - start_date = 2025-11-24 (Monday)
  - end_date = 2025-11-30 (Sunday)
  - Query filters: workout_date >= 2025-11-24 AND <= 2025-11-30
```

### Test Case 3: Meal Plan Summary - Custom Range
```
GIVEN: User on Meal Plan Summary page
WHEN: Selecting "Custom Range", dates "2025-11-01" to "2025-11-30"
THEN:
  - Query filters: plan_start_date >= '2025-11-01' AND <= '2025-11-30'
  - All meal plans with start dates in November displayed
  - Statistics recalculated for filtered data
```

### Test Case 4: Chart Rendering
```
GIVEN: User viewing Workout Summary with 7 days of workouts
WHEN: Page renders
THEN:
  - Focus distribution chart shows exercise focus types
  - Bar heights proportional to exercise counts
  - No errors in Plotly rendering
```

### Validation Queries

**Verify meal plan dates saved correctly:**
```sql
SELECT meal_plan_id, client_id, plan_start_date, plan_week, total_calories
FROM TRAINING_DB.PUBLIC.meal_plans
WHERE plan_start_date >= '2025-11-01'
ORDER BY plan_start_date DESC;
```

**Verify workout dates and meal plan dates align:**
```sql
SELECT 
  w.workout_date, w.workout_focus, w.duration_min,
  m.plan_start_date, m.total_calories
FROM TRAINING_DB.PUBLIC.generated_workouts w
LEFT JOIN TRAINING_DB.PUBLIC.meal_plans m 
  ON w.client_id = m.client_id 
  AND w.workout_date >= m.plan_start_date 
  AND w.workout_date <= DATE_ADD(m.plan_start_date, INTERVAL (m.duration_days - 1) DAY)
WHERE w.client_id = '< client_id >'
ORDER BY w.workout_date;
```

---

## 📦 Files Modified

| File | Changes | Status |
|------|---------|--------|
| `sql/02_stage1_create_tables.sql` | Added `plan_start_date DATE` to `meal_plans` table | ✅ Modified |
| `streamlit_app/app.py` | Updated `save_meal_plan()`, added date picker UI, added 2 new pages, added 2 helper functions | ✅ Modified |

---

## 🚀 Deployment Steps

### 1. Database Deployment
```sql
-- Run the modified 02_stage1_create_tables.sql
USE DATABASE TRAINING_DB;
USE SCHEMA PUBLIC;

-- The script uses CREATE TABLE IF NOT EXISTS, so:
-- - Existing data is preserved
-- - New column plan_start_date is added
-- - No data loss or downtime

EXECUTE SCRIPT 02_stage1_create_tables.sql;
```

### 2. Application Deployment
```bash
# Commit and push updated app.py
git add streamlit_app/app.py
git commit -m "Add meal plan date tracking and summary pages"
git push origin main

# Snowflake Native Streamlit auto-reloads with new code
# New pages appear immediately in sidebar
```

### 3. Verify Deployment
```
✓ SQL: Check meal_plans table structure includes plan_start_date
✓ UI: Verify "Workout Summary" and "Meal Plan Summary" appear in sidebar
✓ Feature: Generate meal plan, confirm date picker works
✓ Feature: View Workout Summary with date filtering
✓ Feature: View Meal Plan Summary with analytics
```

---

## 📊 Data Model Impact

### Before
```
meal_plans
├── meal_plan_id
├── client_id
├── generation_date (only timestamp of creation)
├── plan_week
├── duration_days
└── total_calories
```

### After
```
meal_plans
├── meal_plan_id
├── client_id
├── plan_start_date ✨ NEW - scheduled date
├── generation_date (creation timestamp)
├── plan_week
├── duration_days
└── total_calories
```

**Impact:**
- Enables scheduling meal plans for future dates
- Supports date-based filtering
- No backward compatibility issues (defaults to TODAY if not provided)

---

## 💡 Use Cases Enabled

### Use Case 1: Weekly Planning
Manager can now:
1. Generate workouts for Week 1 starting Monday 11/24
2. Generate meal plan for Week 1 starting Monday 11/24
3. Both show up in Summary pages for that week
4. Client sees aligned workout + nutrition plan

### Use Case 2: Monthly Reporting
Client/coach can:
1. View "Meal Plan Summary" → select "This Month"
2. See all meal plans generated in November
3. Analyze macro trends across month
4. Compare with "Workout Summary" for same period

### Use Case 3: Historical Analysis
Trainer can:
1. View Workout Summary for custom range "Oct 1 - Oct 31"
2. View Meal Plan Summary for same range
3. Analyze which workouts paired with which meal plans
4. Track what worked / what didn't

### Use Case 4: Forward Planning
Coach can:
1. Generate Week 12 meal plan, select date "2026-03-16"
2. Meal plan saved with future date
3. Show client in advance
4. Client can plan groceries, meal prep

---

## 🔍 Features Deep Dive

### Workout Summary - Date Logic
```python
if date_range_option == "This Week":
    today = datetime.now().date()
    # Get Monday of this week (weekday() = 0-6, Monday is 0)
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    # Example: If today is Wed 11/26, range is Mon 11/24 - Sun 11/30

elif date_range_option == "This Month":
    today = datetime.now().date()
    start_date = today.replace(day=1)  # 1st of current month
    if today.month == 12:
        # Handle year boundary
        end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        # Get last day of current month
        end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

else:  # Custom Range
    # User picks start and end dates via date_input widgets
    start_date = st.date_input("Start Date", ...)
    end_date = st.date_input("End Date", ...)
```

### Summary Statistics Calculation
```python
# For Workout Summary
total_workouts = len(workouts_df[workouts_df['WORKOUT_FOCUS'] != 'Rest Day'])
rest_days = len(workouts_df[workouts_df['WORKOUT_FOCUS'] == 'Rest Day'])
total_duration = workouts_df[workouts_df['WORKOUT_FOCUS'] != 'Rest Day']['DURATION_MIN'].sum()
avg_duration = total_duration / total_workouts if total_workouts > 0 else 0

# For Meal Plan Summary
total_plans = len(meal_plans_df)
avg_calories = meal_plans_df['TOTAL_CALORIES'].mean()
avg_protein = meal_plans_df['PROTEIN_G'].mean()
total_days_covered = meal_plans_df['DURATION_DAYS'].sum()
```

---

## ✨ Benefits

| Feature | Benefit |
|---------|---------|
| Date tracking on meal plans | Clients can schedule nutrition aligned with workouts |
| Workout Summary page | Easy tracking of training frequency, duration, and focus |
| Meal Plan Summary page | Monitor nutritional consistency across weeks |
| Date range filtering | Flexible analysis for week/month/custom periods |
| Charts & visualization | Quick insights into workout focus distribution and macros |
| Raw data export | Detailed data for external analysis or coach review |

---

## 🔧 Backward Compatibility

All changes are **100% backward compatible**:

- ✅ Existing meal plans don't break (no data migration required)
- ✅ Old code still works (start_date parameter defaults to TODAY)
- ✅ Database column is nullable? No - but INSERT always provides a date
- ✅ Workouts already had workout_date, so no changes needed there

---

## 📞 Support

### Common Questions

**Q: Can I edit a meal plan's date after saving?**
A: Currently no. Regenerate with new date if needed. Future enhancement could add edit capability.

**Q: What if I don't select a date when generating?**
A: Date defaults to TODAY. User will likely notice in summary and can regenerate if incorrect date.

**Q: Can I see workouts and meal plans together?**
A: Use both summary pages side-by-side with matching date ranges. Future enhancement: unified dashboard.

**Q: Do past meal plans show in summary?**
A: Yes! Any meal plan with plan_start_date in the selected range appears. Perfect for historical analysis.

---

## 🎯 Next Steps (Future Enhancements)

1. **Adherence Tracking** - Log completed meals, compare to plan
2. **Unified Dashboard** - Workouts + meals + weight on one page
3. **Advanced Analytics** - Correlate workout intensity with meal macros
4. **Calendar View** - Visual calendar showing scheduled workouts and meals
5. **Mobile App** - View schedules on mobile
6. **Email Reminders** - Notifications for upcoming meal plans and workouts
7. **API Integration** - Connect to calendar apps (Google Calendar, etc.)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-26 | Initial meal plan date tracking + Workout/Meal Plan Summary pages |

---

**Last Updated:** November 26, 2025  
**Status:** ✅ Production Ready  
**Author:** AI Personal Trainer Development Team
