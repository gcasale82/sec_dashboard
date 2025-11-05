import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Mission Security Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .title {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.75rem;
        color: #34495e;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #f0f0f0;
    }
    .info-box {
        background-color: #f8f9fa;
        border-left: 3px solid #3498db;
        padding: 15px;
        margin: 10px 0;
        border-radius: 3px;
    }
    .high-risk {
        color: #e74c3c;
        font-weight: bold;
    }
    .medium-risk {
        color: #f39c12;
        font-weight: bold;
    }
    .low-risk {
        color: #2ecc71;
        font-weight: bold;
    }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# --- Data Loading and Caching ---
@st.cache_data
def load_data(csv_path="mission_security_reports.csv"):
    """
    Loads and cleans the mission security report data with proper CSV parsing.
    """
    try:
        # Read the file content first
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the CSV by properly quoting fields that contain commas
        lines = content.strip().split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            if i == 0:
                # Keep header as-is
                fixed_lines.append(line)
            else:
                # Split by comma but be careful with embedded commas
                parts = []
                current_part = []
                in_quotes = False

                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                        current_part.append(char)
                    elif char == ',' and not in_quotes:
                        parts.append(''.join(current_part))
                        current_part = []
                    else:
                        current_part.append(char)

                # Add last part
                if current_part:
                    parts.append(''.join(current_part))

                # Now quote any part that contains commas or colons and isn't already quoted
                fixed_parts = []
                for part in parts:
                    part = part.strip()
                    if part and not part.startswith('"') and (',' in part or ':' in part):
                        fixed_parts.append(f'"{part}"')
                    else:
                        fixed_parts.append(part)

                fixed_lines.append(','.join(fixed_parts))

        # Read from the fixed content
        fixed_content = '\n'.join(fixed_lines)
        df = pd.read_csv(StringIO(fixed_content), quotechar='"')

    except FileNotFoundError:
        st.error(f"Error: The data file '{csv_path}' was not found.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        # Try alternative method - skip bad lines
        try:
            df = pd.read_csv(
                csv_path,
                on_bad_lines='skip',
                engine='python'
            )
            st.warning("Loaded with some lines skipped due to parsing errors.")
        except Exception as e2:
            st.error(f"Critical error: {e2}")
            st.stop()

    # Data Cleaning and Transformation
    df['date'] = pd.to_datetime(df['date'])
    df['time_to_fix_hours'] = pd.to_numeric(df['time_to_fix_hours'], errors='coerce')

    # Fill N/A in key categorical fields
    str_cols_to_fill = ['risk_level', 'status', 'attack_type']
    for col in str_cols_to_fill:
        if col in df.columns:
            df[col] = df[col].fillna('N/A')

    return df

# Load the data
df = load_data()


# --- Header Section ---
st.markdown("🌎EO Missions -🛡️ Security & Compliance Demo Dashboard</h1>", unsafe_allow_html=True)
st.markdown("""
<div class='info-box'>
    <p>This dashboard provides a high-level overview of security and compliance status across all missions (FLEX, BIOMASS, EARTHCARE).
    Use the filters in the sidebar to select missions, report types, and date ranges for a detailed analysis.</p>
</div>
""", unsafe_allow_html=True)


# --- Sidebar for Filters ---
with st.sidebar:
    st.title("Filters")

    st.subheader("Mission")
    all_missions = sorted(df['mission'].unique().tolist())
    selected_missions = st.multiselect(
        'Select Mission(s)',
        options=all_missions,
        default=all_missions
    )

    st.subheader("Report Type")
    all_report_types = sorted(df['report_type'].unique().tolist())
    selected_report_types = st.multiselect(
        'Select Report Type(s)',
        options=all_report_types,
        default=all_report_types
    )

    st.subheader("Date Range")
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    selected_dates = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.subheader("Risk Level")
    all_risks = sorted([r for r in df['risk_level'].unique() if r != 'N/A'])
    selected_risk = st.multiselect(
        'Select Risk Level',
        options=all_risks,
        default=all_risks
    )

    st.markdown("""
    <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-top:20px;">
        <h4>Need Help?</h4>
        <p>This dashboard visualizes data from 5 report types:</p>
        <ul>
            <li><b>Security Incidents</b>: Active threats and attacks.</li>
            <li><b>Compliance Reports</b>: Audits against standards.</li>
            <li><b>Verification Reports</b>: Technical control checks.</li>
            <li><b>Risk Assessments</b>: Identified business risks.</li>
            <li><b>Regular Reports</b>: Weekly/monthly status.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Apply Filters to Data ---
filtered_df = df

start_date, end_date = selected_dates
filtered_df = filtered_df[
    (filtered_df['date'].dt.date >= start_date) &
    (filtered_df['date'].dt.date <= end_date)
]

filtered_df = filtered_df[
    (filtered_df['mission'].isin(selected_missions)) &
    (filtered_df['report_type'].isin(selected_report_types))
]

if len(selected_risk) < len(all_risks):
     filtered_df = filtered_df[filtered_df['risk_level'].isin(selected_risk)]


# --- Main Content Area ---
st.markdown("<h2 class='subtitle'>Mission Overview (Filtered)</h2>", unsafe_allow_html=True)

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
else:
    incidents_df = filtered_df[filtered_df['report_type'] == 'Security Incident Report']
    compliance_df = filtered_df[filtered_df['report_type'] == 'Compliance Report']
    risk_df = filtered_df[filtered_df['report_type'] == 'Security Risk Assessment Report']

    total_reports = len(filtered_df)
    open_incidents = len(incidents_df[incidents_df['status'] == 'Investigating'])
    high_risk_items = len(filtered_df[filtered_df['risk_level'] == 'High'])
    avg_fix_time = incidents_df['time_to_fix_hours'].mean()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Reports Logged", f"{total_reports}")
    kpi2.metric("Open Incidents (Investigating)", f"{open_incidents}")
    kpi3.metric("High-Risk Findings", f"{high_risk_items}", delta_color="inverse")
    kpi4.metric("Avg. Incident Fix Time (Hours)", f"{avg_fix_time:.1f}h" if not pd.isna(avg_fix_time) else "N/A")

    st.markdown("<h2 class='subtitle'>Graphical Analysis</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Security Incidents by Attack Type")
        if not incidents_df.empty:
            attack_counts = incidents_df['attack_type'].value_counts().reset_index()
            attack_counts.columns = ['Attack Type', 'Count']

            fig_bar = px.bar(
                attack_counts,
                x='Attack Type',
                y='Count',
                color='Attack Type',
                title='Frequency of Attack Types'
            )
            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("No Security Incident data to display.")

    with col2:
        st.markdown("### Risk Level Distribution (All Reports)")
        risk_data = filtered_df[filtered_df['risk_level'] != 'N/A']
        if not risk_data.empty:
            risk_counts = risk_data['risk_level'].value_counts().reset_index()
            risk_counts.columns = ['Risk Level', 'Count']

            fig_pie = px.pie(
                risk_counts,
                names='Risk Level',
                values='Count',
                color='Risk Level',
                color_discrete_map={
                    'High': '#e74c3c',
                    'Medium': '#f39c12',
                    'Low': '#2ecc71'
                },
                title='Incidents by Risk Level'
            )
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, width='stretch')
        else:
            st.info("No Risk Level data to display.")

    st.markdown("<h2 class='subtitle'>Report Timeline</h2>", unsafe_allow_html=True)
    timeline_data = filtered_df.groupby([filtered_df['date'].dt.date, 'mission']).size().reset_index(name='count')
    timeline_data.columns = ['Date', 'Mission', 'Count']

    fig_line = px.line(
        timeline_data,
        x='Date',
        y='Count',
        color='Mission',
        title='Daily Report Submissions by Mission'
    )
    st.plotly_chart(fig_line, width='stretch')

    st.markdown("<h2 class='subtitle'>Detailed Findings & Action Items</h2>", unsafe_allow_html=True)

    tab_inc, tab_comp, tab_ver, tab_risk, tab_reg = st.tabs([
        "🚨 Incidents",
        "📜 Compliance Findings",
        "🔬 Verification Gaps",
        "📈 Risk Treatment",
        "📓 Regular Summaries"
    ])

    # Helper function to safely select columns
    def safe_select_columns(dataframe, columns):
        """Select only columns that exist in the dataframe"""
        existing_cols = [col for col in columns if col in dataframe.columns]
        if not existing_cols:
            return pd.DataFrame()
        return dataframe[existing_cols]

    with tab_inc:
        st.subheader("Security Incident Details")
        incident_cols = ['mission', 'date', 'attack_type', 'risk_level', 'status',
                        'root_cause', 'remediation_measures', 'time_to_fix_hours']
        display_df = safe_select_columns(incidents_df, incident_cols)
        if not display_df.empty:
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No incident data available.")

    with tab_comp:
        st.subheader("Compliance Non-Conformities")
        compliance_cols = ['mission', 'date', 'compliance_evaluation_results',
                          'identified_non_conformities_and_recommendations',
                          'follow_up_actions_and_deadlines']
        display_df = safe_select_columns(compliance_df, compliance_cols)
        if not display_df.empty:
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No compliance data available.")

    with tab_ver:
        st.subheader("Security Verification Gaps")
        verification_df = filtered_df[filtered_df['report_type'] == 'Security Verification Report']
        verification_cols = ['mission', 'date', 'security_control_checks',
                            'findings_from_technical_verifications',
                            'identified_gaps_and_proposed_corrective_actions']
        display_df = safe_select_columns(verification_df, verification_cols)
        if not display_df.empty:
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No verification data available.")

    with tab_risk:
        st.subheader("Risk Assessment Treatment Plans")
        risk_cols = ['mission', 'date', 'identified_risks_and_threat_scenarios', 'risk_level',
                    'likelihood_and_impact_assessments', 'existing_mitigations_and_residual_risks',
                    'risk_treatment_plan_and_responsible_entities']
        display_df = safe_select_columns(risk_df, risk_cols)
        if not display_df.empty:
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No risk assessment data available.")

    with tab_reg:
        st.subheader("Regular Report Summaries")
        regular_df = filtered_df[filtered_df['report_type'] == 'Security Regular Report']
        regular_cols = ['mission', 'date', 'summary_of_ongoing_security_operations',
                       'notable_security_events', 'progress_on_mitigation_actions']
        display_df = safe_select_columns(regular_df, regular_cols)
        if not display_df.empty:
            st.dataframe(display_df, width='stretch')
        else:
            st.info("No regular report data available.")

st.markdown("""
<div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-top:20px; text-align:center;">
    <p>Mission Security Dashboard | Data as of: """ + str(df['date'].max().date()) + """</p>
</div>
""", unsafe_allow_html=True)
