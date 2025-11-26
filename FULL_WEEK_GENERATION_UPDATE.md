# Full Week Workout Generation Update

**Date:** November 26, 2025  
**Status:** ✅ Complete  
**File Updated:** `streamlit_app/app.py`

---

## 📋 Overview

The Streamlit app has been updated to generate **full weeks of training** (7 days) instead of individual workouts. The AI now reviews previous training history to create **varied, progressive programs** that prevent plateaus.

---

## 🎯 Key Changes

### 1. New Function: `get_previous_workouts_context()`

**Purpose:** Retrieves and summarizes the client's last 4 weeks of training

**Key Features:**
- Queries the database for previous 28 workouts
- Summarizes workout focus and duration for context
- Returns formatted string showing historical training patterns
- Graceful fallback if no previous workouts exist

**Usage:**
```python
context = get_previous_workouts_context(client_id, weeks=4)
# Returns: "Week 1, Day 1: Upper Body Strength (60min)\n..."
```

---

### 2. New Function: `generate_full_week_workouts_cortex()`

**Purpose:** Generates an entire 7-day training program with AI awareness of previous workouts

**Key Features:**
- Includes previous workout context in the prompt
- AI generates all 7 days (training + rest days)
- Ensures significant variety from previous weeks
- Includes instructions to:
  - Alternate muscle groups
  - Space recovery appropriately
  - Prevent plateaus
  - Vary rep ranges and exercises

**Prompt Structure:**
```
=== CLIENT PROFILE ===
- Fitness Level, Goals, Equipment, etc.

=== CONTEXT FROM PREVIOUS TRAINING ===
- Last 4 weeks workout summary

=== IMPORTANT INSTRUCTIONS ===
1. Diverse program with different muscle groups each day
2. {DAYS_PER_WEEK} training days + {7-DAYS_PER_WEEK} rest days
3. ENSURE WORKOUTS ARE SIGNIFICANTLY DIFFERENT from previous weeks
4. Vary exercises, rep ranges, training focus
5. Include warm-up and cool-down
6. Space muscle groups appropriately
7. Include recovery tips on rest days
```

**Output Format:** Full week as JSON with all 7 days

---

### 3. New Function: `save_weekly_workouts()`

**Purpose:** Saves an entire week of workouts to the database

**Key Features:**
- Iterates through all 7 days
- Handles both training days and rest days
- Rest days stored with duration_min = 0 and workout_focus = 'Rest Day'
- Training days store complete exercise data
- Single database operation per day for efficiency

**Database Storage:**
- Each day = separate row in `generated_workouts` table
- Week number and day number preserved for tracking
- Cortex model and prompt stored for reproducibility

---

### 4. Updated Function: `generate_workout_cortex()` (Legacy)

**Purpose:** Kept for backward compatibility but marked as "Legacy - single day"

**Note:** Users should now use `generate_full_week_workouts_cortex()` for better results

---

### 5. Updated Page: `page_workout_generator()`

**UI Changes:**
- ✅ Title updated: "💪 Workout Generator - Full Week Planning"
- ✅ Shows both "Fitness Level" and "Training Days/Week" metrics
- ✅ Changed tab names: "Generate Full Week" → "View History"
- ✅ Removed individual day/week inputs, now just week number
- ✅ Added info banner explaining the process

**Generation Workflow:**
```
1. User selects client and week number
2. Click "Generate Full Week with AI"
3. Status 1: "Reviewing previous 4 weeks..." → shows context
4. Status 2: "Generating full week..." → calls Cortex
5. Display: Summary table (7 days with Type/Focus/Exercises)
6. Display: Detailed expandable sections for each day
7. Option: "Save Full Week to Database"
```

**Display Features:**
- Summary table showing all 7 days at a glance
  - Day name (Monday-Sunday)
  - Type (💪 Training or 🔄 Rest)
  - Focus (muscle group/recovery)
  - Exercise count
- Expandable sections for detailed view
  - Warm-up details
  - Exercise breakdown (sets, reps, rest, notes)
  - Cool-down details
- Color-coded emojis for quick visual scanning

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────┐
│ User: Select Client & Week Number           │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ get_previous_workouts_context()             │
│ • Query last 28 workouts                    │
│ • Build context string                      │
│ • Return to user for review                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ generate_full_week_workouts_cortex()        │
│ • Include client profile                    │
│ • Include previous context                  │
│ • Call Cortex with full prompt              │
│ • Parse JSON response (7 days)              │
│ • Return structured week data               │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Display in Streamlit                        │
│ • Summary table (all 7 days)                │
│ • Detailed expandables (each day)           │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ User: Click "Save Full Week"                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ save_weekly_workouts()                      │
│ • Iterate through 7 days                    │
│ • Insert each day to database               │
│ • Log event: "Week X with 7 days saved"     │
│ • Return: count of saved days               │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Database: generated_workouts table          │
│ • 7 new rows (one per day)                  │
│ • Same week number, different day numbers   │
│ • Training days: exercises data + prompts   │
│ • Rest days: recovery tips + empty arrays   │
└─────────────────────────────────────────────┘
```

---

## 🔄 Weekly Variety Mechanism

The AI ensures variety through:

1. **Historical Context**
   - Receives summary of last 4 weeks
   - "ENSURE WORKOUTS ARE SIGNIFICANTLY DIFFERENT"
   - Explicit instruction to avoid repetition

2. **Muscle Group Spacing**
   - "Space out muscle groups (e.g., no back-to-back same groups)"
   - Rest days placed strategically
   - Different focuses each day

3. **Exercise Rotation**
   - "Vary the exercises, rep ranges, and training focus"
   - Can use different variations of same muscle group
   - Example: Week 1 chest could be incline, Week 2 could be decline/dumbbell

4. **Rep Range Variation**
   - Instructions include varying rep ranges
   - Example: Week 1 might use 8-10 reps (hypertrophy), Week 2 uses 4-6 reps (strength)

---

## 💾 Database Schema (No Changes Required)

The existing `generated_workouts` table handles both single days and full weeks:

```sql
-- Training Day (from new full week generation):
INSERT INTO generated_workouts (
  workout_id, client_id, workout_week, workout_day,
  workout_focus, duration_min, warm_up, exercises, cool_down,
  cortex_prompt, cortex_model
) VALUES (
  'uuid', 'client_id', 1, 1,
  'Upper Body Strength', 60,
  '5 min cardio', [...exercises_json...], 'stretching',
  '[full_prompt_text]', 'mistral-7b'
);

-- Rest Day (from new full week generation):
INSERT INTO generated_workouts (
  workout_id, client_id, workout_week, workout_day,
  workout_focus, duration_min, warm_up, exercises, cool_down,
  cortex_prompt, cortex_model
) VALUES (
  'uuid', 'client_id', 1, 2,
  'Rest Day', 0,
  'Recovery tips here', '[]', 'Focus on recovery',
  '[full_prompt_text]', 'mistral-7b'
);
```

---

## 🧪 Testing Workflow

1. **Create a Client**
   - Home page → "Create New Client"
   - Set fitness level, goals, equipment, etc.

2. **Generate Week 1**
   - Workout Generator → Week 1
   - Click "Generate Full Week"
   - Review previous context (should show none for first week)
   - Review generated week
   - Save to database

3. **Generate Week 2**
   - Workout Generator → Week 2
   - Click "Generate Full Week"
   - Review previous context (should show Week 1 summary)
   - Verify exercises are different from Week 1
   - Save to database

4. **View History**
   - Workout Generator → "View History" tab
   - Should show 14 rows (7 days × 2 weeks)
   - Filter by week to verify variety

---

## 📈 Future Enhancements

Possible improvements:
1. Add progress tracking (RPE, actual performance vs. target)
2. Auto-adjust intensity based on previous week feedback
3. Add periodization (linear, undulating, block)
4. Include deload weeks (lower intensity recovery weeks)
5. Add exercise swaps/alternatives for injury management
6. Store workout completion data and adjust next week based on actual performance

---

## ✅ What Changed vs. What Stayed the Same

### ✅ Changed:
- Generation: Single day → Full week
- UI: Week/Day selectors → Just week selector
- Page title: "Workout Generator" → "Workout Generator - Full Week Planning"
- Generation functions: Added context awareness
- Database: Now stores 7 rows per generation (vs. 1 before)
- Display: Added summary table + expandable detail sections

### ✅ Stayed the Same:
- Database schema (no migrations needed)
- Other pages (Meal Plans, Weight Tracking, etc.)
- Client creation workflow
- All existing data remains intact
- Cortex integration and model selection
- Logging and audit trail

---

## 🚀 Deployment Notes

**No database migrations needed** - the existing schema supports full week generation.

**Backward compatible** - the `generate_workout_cortex()` function still exists if needed for single-day generation.

**No new dependencies** - uses same libraries (pandas, json, streamlit, etc.)

---

## 📝 Code Structure

```
app.py
├── get_previous_workouts_context()      [NEW]
├── generate_full_week_workouts_cortex() [NEW]
├── save_weekly_workouts()               [NEW]
├── generate_workout_cortex()            [LEGACY - still works]
├── save_workout()                       [UPDATED - handles single days]
└── page_workout_generator()             [UPDATED - full week UI]
```

---

**Status:** ✅ Production Ready  
**Test Date:** November 26, 2025  
**Version:** 1.1.0
