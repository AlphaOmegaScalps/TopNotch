import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import gspread
from google.oauth2.service_account import Credentials
import os
import base64

# 1. PAGE SETUP & THEME CONFIGS
st.set_page_config(page_title="Top Notch Lawn & Tree", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS to override standard Streamlit boxes and match the target dark UI
st.markdown("""
    <style>
    /* Main background color override */
    .stApp {
        background-color: #0b111e;
        color: #e2e8f0;
    }
    
    /* Styled container mimicking dashboard cards */
    .metric-card {
        background-color: #111928;
        border: 1px solid #1f2a37;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Typography adjustments */
    .metric-title {
        color: #9ca3af;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .metric-delta-pos {
        color: #10b981;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    /* Hide standard Streamlit block padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom app tables styling */
    table { 
        color: white; 
        width: 100%; 
        background-color: #111928; 
        border-collapse: collapse; 
        border-radius: 8px; 
        overflow: hidden; 
        margin-top: 10px;
    }
    th { 
        background-color: #1f2a37; 
        padding: 10px; 
        text-align: left; 
        font-size: 0.8rem; 
        color: #9ca3af;
    }
    td { 
        padding: 12px 10px; 
        border-bottom: 1px solid #1f2a37; 
        font-size: 0.85rem;
    }
    
    /* Make the navigation radio mix cleanly into our dark design */
    div.row-widget.stRadio > div {
        background-color: transparent;
    }
    div.row-widget.stRadio label {
        color: #9ca3af !important;
        font-size: 0.95rem;
        padding: 6px 10px;
        border-radius: 6px;
    }
    div.row-widget.stRadio label:hover {
        color: #ffffff !important;
        background-color: #1f2a37;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to safely read image file to HTML string bypassing PIL/Streamlit errors
def get_image_html(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f'<img src="data:image/jpeg;base64,{encoded}" style="width:100%; border-radius:8px; margin-bottom:15px;">'
    return None

# ==========================================
# 🔌 DATABASE CONNECTION (GOOGLE SHEETS)
# ==========================================
@st.cache_data(ttl=60)
def load_sheet_data():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("creds.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open("TopNotch_Operations").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), None
    except Exception as e:
        fallback_jobs = pd.DataFrame([
            {"Time": "9:00 AM", "Customer": "Johnson Residence (Demo)", "Crew": "Crew 1", "Status": "In Progress"},
            {"Time": "9:30 AM", "Customer": "Williams Residence (Demo)", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "10:00 AM", "Customer": "Brown Residence (Demo)", "Crew": "Crew 2", "Status": "Pending"}
        ])
        return fallback_jobs, str(e)

jobs_df, connection_error = load_sheet_data()

# ==========================================
# SIDEBAR NAVIGATION & PAGE SELECTION
# ==========================================
with st.sidebar:
    logo_html = get_image_html("logo.jpg") or get_image_html("logo.png")
    if logo_html:
        st.markdown(logo_html, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color:#ffffff; margin-top:0;'>Top Notch</h2>", unsafe_allow_html=True)
        st.caption("LAWN & TREE SERVICES")
    
    if connection_error:
        st.info("ℹ️ **Demo Mode Active**\nPlace 'creds.json' in your folder to link Google Sheets.")
    
    st.markdown("---")
    
    page = st.radio(
        label="Navigation Links",
        options=[
            "🟢 Dashboard", 
            "📡 Live Radar",  # Brand new zero-dependency weather deck module
            "📋 Jobs", 
            "👥 Customers", 
            "🗺️ Routes", 
            "📅 Schedule", 
            "💳 Invoices", 
            "🚜 Equipment"
        ],
        label_visibility="collapsed",
        key="main_navigation_menu"
    )
    
    st.markdown("---")
    st.markdown("🌐 **County Weather Overview**")
    st.caption("All crews tracking clear of precipitation cells across Brevard.")

# ==========================================
# PAGE ROUTING CONTROL BLOCK
# ==========================================

if page == "🟢 Dashboard":
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("<h2 style='margin:0;'>Dashboard</h2>", unsafe_allow_html=True)
    with header_col2:
        st.markdown(f"<p style='text-align:right; color:#9ca3af; margin-top:10px;'>📍 Brevard County Core</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ROW 1: TOP KPI METRICS CARDS
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.markdown('<div class="metric-card"><div class="metric-title">Today\'s Revenue</div><div class="metric-value">$1,385</div><div class="metric-delta-pos">↗ 12.5% <span style="color:#6b7280;">vs yesterday</span></div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown('<div class="metric-card"><div class="metric-title">Yards Completed</div><div class="metric-value">21 / 38</div><div class="metric-delta-pos"><span style="color:#6b7280;">55% of today\'s route</span></div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown('<div class="metric-card"><div class="metric-title">Current Efficiency</div><div class="metric-value">94%</div><div class="metric-delta-pos">↗ 5% <span style="color:#6b7280;">vs last week</span></div></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown('<div class="metric-card"><div class="metric-title">Avg Time Per Yard</div><div class="metric-value">16.2 min</div><div class="metric-delta-pos" style="color:#10b981;">↘ 1.3 min <span style="color:#6b7280;">vs last week</span></div></div>', unsafe_allow_html=True)
    with kpi5:
        st.markdown('<div class="metric-card"><div class="metric-title">Estimated Finish</div><div class="metric-value">4:17 PM</div><div class="metric-delta-pos" style="color:#3b82f6;">On track</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ROW 2: ALL-CITIES MATRIX MAP & FEED
    map_col, feed_col = st.columns([3, 1])
    with map_col:
        st.markdown("<div style='background-color:#111928; border:1px solid #1f2a37; border-radius:12px; padding:15px; margin-bottom:15px;'><h4 style='margin:0 0 10px 0;'>Active Operational Footprint Matrix</h4></div>", unsafe_allow_html=True)
        
        # Center the map regionally over central Brevard County
        brevard_center = [28.3200, -80.6826]
        m = folium.Map(location=brevard_center, zoom_start=10, tiles="CartoDB dark_matter")
        
        # Plotting ALL 5 cities on the map simultaneously as requested
        all_hubs = [
            {"name": "Titusville Hub", "coords": [28.6122, -80.8076], "details": "Crew 1 assigned · 8 yards scheduled"},
            {"name": "Merritt Island Hub", "coords": [28.3553, -80.6826], "details": "Crew 2 assigned · 12 yards scheduled"},
            {"name": "Cocoa Beach Hub", "coords": [28.3200, -80.6076], "details": "Crew 3 assigned · Canopy lift priority"},
            {"name": "Viera Hub", "coords": [28.2346, -80.7287], "details": "Crew 4 assigned · Commercial accounts clear"},
            {"name": "Palm Bay Hub", "coords": [28.0331, -80.6431], "details": "Crew 5 assigned · Stumping operations pending"}
        ]
        
        for hub in all_hubs:
            tooltip_content = f"""
                <div style='font-size: 13px; line-height: 1.4;'>
                    <strong style='color:#10b981;'>{hub['name']}</strong><br/>
                    <b>Status:</b> {hub['details']}
                </div>
            """
            folium.CircleMarker(
                location=hub["coords"],
                radius=8,
                color="#10b981",
                fill=True,
                fill_color="#111928",
                fill_opacity=1.0,
                tooltip=folium.Tooltip(tooltip_content, sticky=True)
            ).add_to(m)
            
        folium_static(m, width=910, height=375)

    with feed_col:
        st.markdown("<h4 style='margin:0;'>Activity Feed</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color:#111928; border:1px solid #1f2a37; border-radius:12px; padding:15px; height:375px; overflow-y:auto; font-size:0.85rem;'><p>🟢 <b>8:40 AM</b> - All 5 regional sectors synched matrix outputs safely.<br><span style='color:#9ca3af;'>Dispatch check-in clear.</span></p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ROW 3: CHARTS & TABLE
    chart1_col, chart2_col, table_col = st.columns([1.5, 1.2, 1.8])
    with chart1_col:
        st.markdown("<h4 style='margin:0;'>Revenue Overview</h4>", unsafe_allow_html=True)
        rev_data = pd.DataFrame({'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], 'Revenue': [600, 900, 800, 1100, 1385]})
        fig_line = px.line(rev_data, x='Day', y='Revenue', template="plotly_dark")
        fig_line.update_traces(line_color="#10b981", line_width=3)
        fig_line.update_layout(paper_bgcolor='rgba(17,25,40,1)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20), height=220, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1f2a37"))
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    with chart2_col:
        st.markdown("<h4 style='margin:0;'>Jobs by Status</h4>", unsafe_allow_html=True)
        status_data = pd.DataFrame({'Status': ['Completed', 'Remaining'], 'Count': [21, 10]})
        fig_pie = px.pie(status_data, values='Count', names='Status', hole=0.6, template="plotly_dark", color_discrete_sequence=['#10b981', '#3b82f6'])
        fig_pie.update_layout(paper_bgcolor='rgba(17,25,40,1)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=220, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    with table_col:
        st.markdown("<h4 style='margin:0;'>Upcoming Jobs</h4>", unsafe_allow_html=True)
        st.markdown(jobs_df.to_html(classes='table', index=False, escape=False), unsafe_allow_html=True)

# ------------------------------------------
# NEW PAGE: 📡 LIVE RADAR MODULE (ZERO DEPENDENCIES)
# ------------------------------------------
elif page == "📡 Live Radar":
    st.markdown("<h2>Brevard County Live Precipitation Radar</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Real-time weather tracking loop centered over your exact Florida operations footprint.</p>", unsafe_allow_html=True)
    
    # Embedded interactive RainViewer element configured to target Brevard County coordinates
    radar_html = """
    <iframe src="https://www.rainviewer.com/map.html?loc=28.3200,-80.6826,9&oFa=1&oC=1&oU=0&oCS=1&oF=0&oAP=1&c=3&o=80&lm=1&layer=radar&sm=1&sn=1" 
            width="100%" 
            height="650" 
            frameborder="0" 
            style="border:1px solid #1f2a37; border-radius:12px; background-color:#111928;" 
            allowfullscreen>
    </iframe>
    """
    st.components.v1.html(radar_html, height=660)

elif page == "📋 Jobs":
    st.markdown("<h2>Operations & Work Orders</h2>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#111928; border:1px dashed #374151; border-radius:12px; padding:40px; text-align:center;'><h4 style='color:#9ca3af; margin:0;'>🗃️ Master Work Orders Database Block</h4></div>", unsafe_allow_html=True)

elif page == "👥 Customers":
    st.markdown("<h2>Customer Profiles & Direct CRM</h2>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#111928; border:1px dashed #374151; border-radius:12px; padding:40px; text-align:center;'><h4 style='color:#9ca3af; margin:0;'>👥 Active Customer CRM Data Hub</h4></div>", unsafe_allow_html=True)

else:
    st.markdown(f"<h2>{page[2:]} Module</h2>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#111928; border:1px solid #1f2a37; border-radius:12px; padding:30px;'><p style='color:#9ca3af; margin:0;'>📦 Container frame configured.</p></div>", unsafe_allow_html=True)