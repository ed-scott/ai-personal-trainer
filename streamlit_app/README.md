# Streamlit App Directory
## AI Personal Trainer - Snowflake Native Application

**Status:** ✅ Ready to Deploy  
**Type:** Streamlit Native (Snowflake Hosted)  
**Version:** 1.0.0  

---

## Quick Start

### Option 1: Deploy to Snowflake (Recommended)

```bash
# 1. In Snowflake, run the SQL DDL:
# File: ../sql/06_create_streamlit_app.sql

# 2. The app will appear in Snowflake UI → Streamlit Apps

# 3. Click "AI_PERSONAL_TRAINER" to launch
```

### Option 2: Run Locally for Testing

```bash
# 1. Set up environment
cp .env.template .env
# Edit .env with your Snowflake credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py

# 4. Open browser to http://localhost:8501
```

---

## Files in This Directory

### Application Files
- **app.py** (850 lines)
  - Main Streamlit application
  - Multi-page navigation (Dashboard, Progress, Weigh-In, Workouts, Running, Nutrition, Settings)
  - Snowflake connection management
  - Form submission logic
  - Chart generation

### Configuration Files
- **requirements.txt**
  - Python dependencies (streamlit, snowflake-connector, pandas, plotly, etc.)

- **config.py**
  - Application configuration module
  - Snowflake connection parameters
  - Feature flags
  - AI configuration

- **.env.template**
  - Environment variable template
  - Copy to `.env` and fill in your credentials

- **.streamlit/config.toml**
  - Streamlit UI configuration
  - Theme settings
  - Server parameters

### Documentation
- **DEPLOYMENT_GUIDE.md** (500+ lines)
  - Complete deployment instructions
  - Configuration details
  - Troubleshooting guide
  - Testing procedures

---

## App Architecture

### Frontend (Streamlit Native)
```
┌─────────────────────────────────────┐
│  Streamlit Native (Hosted in SF)   │
├─────────────────────────────────────┤
│  Navigation                         │
│  ├── Dashboard                      │
│  ├── Progress (Charts)              │
│  ├── Weigh-In (Form)                │
│  ├── Workouts (Form)                │
│  ├── Running (Form)                 │
│  ├── Nutrition (Form)               │
│  └── Settings                       │
└─────────────────────────────────────┘
         ↓ (Snowpark)
┌─────────────────────────────────────┐
│  Snowflake Database Layer           │
├─────────────────────────────────────┤
│  TRAINING_DB.PUBLIC                 │
│  ├── CLIENTS                        │
│  ├── TRAINERS                       │
│  ├── WEIGH_INS                      │
│  ├── WORKOUTS                       │
│  ├── WORKOUT_EXERCISES              │
│  ├── RUNNING_SESSIONS               │
│  ├── MEAL_PLANS                     │
│  ├── NUTRITION_LOGS                 │
│  └── ... (14 total)                │
└─────────────────────────────────────┘
```

### Pages Overview

| Page | Purpose | Features |
|------|---------|----------|
| **Dashboard** | System overview | Metrics, recent activity, statistics |
| **📊 Progress** | Client tracking | Weight trends, performance charts |
| **⚖️ Weigh-In** | Weight entry | Manual input form, body composition |
| **🏋️ Workouts** | Exercise logging | Suggested vs actual, RPE tracking |
| **🏃 Running** | Running sessions | Distance, pace, performance |
| **🍽️ Nutrition** | Meal tracking | *Coming soon* |
| **⚙️ Settings** | Configuration | DB info, cache management |

---

## Features

### ✅ Implemented
- [x] Snowflake connection via Snowpark
- [x] Multi-page navigation
- [x] Dashboard with metrics
- [x] Weigh-in form with manual entry
- [x] Workout logging with suggested vs actual
- [x] Running session tracking
- [x] Progress charts (Plotly)
- [x] Client/trainer/exercise selection
- [x] Form validation
- [x] Database insertion
- [x] Role-based access
- [x] Settings/configuration page
- [x] Caching for performance

### 🚀 Future Enhancements
- [ ] Nutrition logging complete
- [ ] AI-generated workout suggestions
- [ ] Performance analytics
- [ ] Data export (CSV/Excel)
- [ ] Mobile responsiveness
- [ ] Push notifications
- [ ] Social features (sharing)
- [ ] Advanced filtering/search

---

## Data Flow

### Weigh-In Form Submission
```
User fills form
     ↓
Streamlit validates
     ↓
Generate ID (WEIGHIN_20231126_123456)
     ↓
Execute INSERT via Snowpark
     ↓
INSERT INTO WEIGH_INS (...)
     ↓
Success → Update views automatically
```

### Dashboard Queries
```
Page loads
     ↓
Execute SELECT from CLIENTS, TRAINERS, etc.
     ↓
Load into Pandas DataFrame
     ↓
Display as st.metric() cards
     ↓
Show recent activity tables
```

### Progress Chart
```
Select client
     ↓
Query WEIGH_INS (last 90 days)
     ↓
Convert dates to datetime
     ↓
Create Plotly Figure
     ↓
Display interactive chart
```

---

## Security

### Authentication
- Snowflake role-based access
- User credentials in environment variables
- Connection parameters in `.env` (not committed)

### Authorization
- `TRAINING_APP_ROLE` for normal users
- `TRAINING_APP_ADMIN` for administrators
- Permissions managed via Snowflake GRANT

### Data Protection
- All SQL executed under role identity
- Timestamps track data source
- Audit logging in APP_LOGS table
- No credentials logged

---

## Performance Optimization

### Caching Strategy
```python
@st.cache_resource
def get_snowflake_connection() -> Session:
    # Connection cached for entire session
    # Reconnects only when app restarted
```

### Query Optimization
- Queries limited to 30-90 day windows
- Indexes on CLIENT_ID and DATE
- Materialized views for aggregations
- Avoid N+1 queries

### Cost Management
- XSMALL warehouse adequate
- Queries auto-suspend after 10 minutes
- Monitor warehouse time usage
- Archive old data regularly

---

## Troubleshooting

### "Failed to connect to Snowflake"
```bash
# Check environment variables
env | grep SNOWFLAKE

# Verify .env file exists
cat .env

# Test connection manually
python -c "from snowflake.snowpark.session import Session; ..."
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check Python version (3.8+)
python --version
```

### "Permission denied" on INSERT
```sql
-- As ACCOUNTADMIN:
GRANT INSERT ON TABLE TRAINING_DB.PUBLIC.WEIGH_INS 
  TO ROLE TRAINING_APP_ROLE;
```

### Slow performance
```sql
-- Check warehouse
ALTER WAREHOUSE TRAINING_WH RESUME;

-- Upgrade size if needed
ALTER WAREHOUSE TRAINING_WH SET WAREHOUSE_SIZE = 'SMALL';
```

---

## Development

### Adding a New Page

1. Create function in `app.py`:
```python
def show_new_page(session: Session):
    st.subheader("New Page")
    # Add your code here
```

2. Add to navigation:
```python
elif page == "📋 New Page":
    show_new_page(session)
```

3. Add selectbox option:
```python
page = st.radio("Select Page", options=[
    "Dashboard",
    "📋 New Page",  # Add here
    ...
])
```

### Adding a Form

```python
with st.form("my_form"):
    field1 = st.text_input("Field 1")
    field2 = st.number_input("Field 2")
    
    if st.form_submit_button("Submit"):
        query = f"INSERT INTO TABLE (...) VALUES (...)"
        if execute_insert(session, query):
            st.success("✅ Saved!")
        else:
            st.error("❌ Failed!")
```

### Adding a Chart

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=data['DATE'],
    y=data['VALUE'],
    mode='lines+markers'
))
fig.update_layout(title="Chart Title")
st.plotly_chart(fig, use_container_width=True)
```

---

## Testing

### Manual Testing Checklist
- [ ] Dashboard loads without errors
- [ ] Weigh-In form submits successfully
- [ ] Data appears in WEIGH_INS table
- [ ] Progress chart displays
- [ ] Settings page shows correct DB info
- [ ] Page navigation works
- [ ] Forms validate input

### Automated Testing (TODO)
```bash
# Future: Add pytest tests
pytest tests/
```

---

## Deployment Checklist

- [ ] `.env.template` copied to `.env`
- [ ] Snowflake credentials configured
- [ ] `requirements.txt` dependencies installed
- [ ] Local test run successful
- [ ] `06_create_streamlit_app.sql` executed in Snowflake
- [ ] App visible in Snowflake UI
- [ ] Permissions granted to TRAINING_APP_ROLE
- [ ] Test form submission
- [ ] Data verified in database
- [ ] Production URLs tested

---

## Cost Estimation

**Compute:**
- XSMALL warehouse: $2-4/hour
- Average usage: 2-4 hours/day
- Monthly: $50-150

**Storage:**
- 14 tables, 100k rows: ~100 MB
- Monthly: $2-5

**Total:** ~$100-200/month

---

## Support

- **Snowflake Docs:** https://docs.snowflake.com/en/user-guide/ui-snowsight-streamlit
- **Streamlit Docs:** https://docs.streamlit.io
- **Snowpark Python:** https://docs.snowflake.com/developer-guide/snowpark/python
- **GitHub Issues:** https://github.com/ed-scott/ai-personal-trainer/issues

---

## File Manifest

```
streamlit_app/
├── app.py ........................... Main application (850 lines)
├── config.py ........................ Configuration module
├── requirements.txt ................. Python dependencies
├── .env.template .................... Environment template
├── .streamlit/
│   └── config.toml .................. Streamlit UI config
├── DEPLOYMENT_GUIDE.md .............. Detailed deployment guide
└── README.md (this file)
```

---

**Status:** ✅ Production Ready  
**Last Updated:** November 26, 2025  
**Version:** 1.0.0  

Next Step: Run `../sql/06_create_streamlit_app.sql` in Snowflake!
