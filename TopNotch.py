import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import gspread
from google.oauth2.service_account import Credentials
import os
import base64
import requests
import time
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# 1. PAGE SETUP & THEME CONFIGS
st.set_page_config(page_title="Top Notch Lawn & Tree", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS to enforce typography, large bold headings, larger sidebar navigation, and checkbox layouts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global typography and background color override */
    .stApp {
        background-color: #0b111e;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Make Main Page Titles massive, bold, and easily readable */
    h2 {
        font-family: 'Inter', sans-serif !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        color: #ffffff !important;
        margin-top: 0px !important;
        margin-bottom: 5px !important;
    }
    
    h4 {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    
    /* -------------------------------------------------------------------------
       SIDEBAR NAVIGATION FORCED OVERRIDES
       ------------------------------------------------------------------------- */
    div[data-testid="stSidebar"] div[role="radiogroup"] p,
    div[data-testid="stSidebar"] .stRadio p,
    div.row-widget.stRadio label p,
    label[data-testid="stWidgetLabel"] p {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        color: #9ca3af !important;
        line-height: 1.4 !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover p,
    div.row-widget.stRadio label:hover p {
        color: #ffffff !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label,
    div.row-widget.stRadio label {
        padding: 10px 14px !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover,
    div.row-widget.stRadio label:hover {
        background-color: #1f2a37 !important;
    }
    
    div[data-testid="stCheckbox"] label p {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }
    /* ------------------------------------------------------------------------- */
    
    .metric-card {
        background-color: #111928;
        border: 1px solid #1f2a37;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
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
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
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
        font-weight: 600;
    }
    td { 
        padding: 12px 10px; 
        border-bottom: 1px solid #1f2a37; 
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

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
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("creds.json", scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("TopNotch_Operations").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), None
    except Exception as e:
        # LARGER EXPANDED DEMO SAMPLE SIZE ACROSS BREVARD COUNTY
        fallback_jobs = pd.DataFrame([
            {"Time": "7:00 AM", "Customer": "C1-Stop1", "Address": "400 S Washington Ave, Titusville, FL", "Crew": "Crew 1", "Status": "Completed"},
            {"Time": "7:45 AM", "Customer": "C1-Stop2", "Address": "840 Century Medical Dr, Titusville, FL", "Crew": "Crew 1", "Status": "Completed"},
            {"Time": "8:30 AM", "Customer": "C1-Stop3", "Address": "225 King St, Cocoa, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "9:15 AM", "Customer": "C1-Stop4", "Address": "1450 N Courtenay Pkwy, Merritt Island, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "10:00 AM", "Customer": "C1-Stop5", "Address": "2201 Ivey Lane, Cocoa Beach, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "10:45 AM", "Customer": "C1-Stop6", "Address": "220 Marine Harbor Dr, Merritt Island, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "11:30 AM", "Customer": "C1-Stop7", "Address": "1500 N Banana River Dr, Merritt Island, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "12:15 PM", "Customer": "C1-Stop8", "Address": "500 Florida Ave, Cocoa, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "1:00 PM", "Customer": "C1-Stop9", "Address": "300 Cheney Hwy, Titusville, FL", "Crew": "Crew 1", "Status": "Pending"},
            {"Time": "1:45 PM", "Customer": "C1-Stop10", "Address": "100 Riveredge Blvd, Cocoa, FL", "Crew": "Crew 1", "Status": "Pending"},
            
            # Crew 2 - South Focus
            {"Time": "7:00 AM", "Customer": "C2-Stop1", "Address": "1500 Viera Blvd, Viera, FL", "Crew": "Crew 2", "Status": "Completed"},
            {"Time": "7:45 AM", "Customer": "C2-Stop2", "Address": "1 Country Club Dr, Melbourne, FL", "Crew": "Crew 2", "Status": "Completed"},
            {"Time": "8:30 AM", "Customer": "C2-Stop3", "Address": "4700 Malabar Rd, Palm Bay, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "9:15 AM", "Customer": "C2-Stop4", "Address": "1901 Degroodt Rd SW, Palm Bay, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "10:00 AM", "Customer": "C2-Stop5", "Address": "2210 Front St, Melbourne, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "10:45 AM", "Customer": "C2-Stop6", "Address": "7000 Babcock St SE, Palm Bay, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "11:30 AM", "Customer": "C2-Stop7", "Address": "5000 Wickham Rd, Melbourne, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "12:15 PM", "Customer": "C2-Stop8", "Address": "2500 Post Rd, Melbourne, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "1:00 PM", "Customer": "C2-Stop9", "Address": "3500 Jupiter Blvd SE, Palm Bay, FL", "Crew": "Crew 2", "Status": "Pending"},
            {"Time": "1:45 PM", "Customer": "C2-Stop10", "Address": "800 Palm Bay Rd NE, Palm Bay, FL", "Crew": "Crew 2", "Status": "Pending"}
        ])
        return fallback_jobs, str(e)

jobs_df, connection_error = load_sheet_data()

# ==========================================
# 🗺️ BACKGROUND ROUTING & MAP MATCHING ENGINES
# ==========================================

@st.cache_data(ttl=86400) 
def geocode_address(address_str):
    """Quietly finds map pins behind the scenes."""
    headers = {"User-Agent": "TopNotchOperationalMatrixApp/1.0"}
    url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(address_str)}&format=json&limit=1"
    try:
        response = requests.get(url, headers=headers, timeout=5).json()
        if response:
            return [float(response[0]["lat"]), float(response[0]["lon"])]
    except Exception as e:
        pass
    return None

def get_osrm_route_and_matrix(coords):
    n = len(coords)
    coord_string = ";".join([f"{lon},{lat}" for lat, lon in coords])
    
    route_url = f"http://router.project-osrm.org/route/v1/driving/{coord_string}?overview=full&geometries=geojson"
    total_meters = 0
    total_seconds = 0
    try:
        r = requests.get(route_url, timeout=5).json()
        geometry = r['routes'][0]['geometry']['coordinates']
        total_meters = r['routes'][0]['distance']
        total_seconds = r['routes'][0]['duration']
        road_path = [[lat, lon] for lon, lat in geometry]
    except:
        road_path = coords

    matrix_url = f"http://router.project-osrm.org/table/v1/driving/{coord_string}?annotations=distance"
    try:
        rm = requests.get(matrix_url, timeout=5).json()
        distance_matrix = [[int(val) for val in row] for row in rm['distances']]
    except:
        distance_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                dist = int((abs(coords[i][0]-coords[j][0]) + abs(coords[i][1]-coords[j][1])) * 111000)
                row.append(dist)
            distance_matrix.append(row)
            
    return distance_matrix, road_path, total_meters, total_seconds

def solve_or_tools_tsp(distance_matrix):
    if not distance_matrix or len(distance_matrix) <= 1:
        return list(range(len(distance_matrix))) if distance_matrix else []
        
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        return route
    return list(range(len(distance_matrix)))

# ==========================================
# SIDEBAR NAVIGATION
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
        options=["🟢 Dashboard", "📡 Live Radar", "📋 Jobs", "👥 Customers", "🗺️ Smart Routes", "📅 Schedule"],
        label_visibility="collapsed",
        key="main_navigation_menu"
    )
    
    st.markdown("---")
    st.markdown("🌐 **County Weather Overview**")
    st.caption("All crews tracking clear of precipitation cells across Brevard.")

# ==========================================
# PAGE ROUTING CONTROL BLOCK
# ==========================================
clean_page_name = page.strip()

if clean_page_name == "🟢 Dashboard":
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("<h2>Dashboard</h2>", unsafe_allow_html=True)
    with header_col2:
        st.markdown(f"<p style='text-align:right; color:#9ca3af; margin-top:15px;'>📍 Brevard County Core</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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

    map_col, feed_col = st.columns([3, 1])
    with map_col:
        st.markdown("<div style='background-color:#111928; border:1px solid #1f2a37; border-radius:12px; padding:15px; margin-bottom:15px;'><h4 style='margin:0 0 10px 0;'>Active Operational Footprint Matrix</h4></div>", unsafe_allow_html=True)
        brevard_center = [28.3200, -80.6826]
        m = folium.Map(location=brevard_center, zoom_start=10, tiles="CartoDB dark_matter")
        all_hubs = [
            {"name": "Titusville Hub", "coords": [28.6122, -80.8076], "details": "Crew 1 assigned · 8 yards scheduled"},
            {"name": "Merritt Island Hub", "coords": [28.3553, -80.6826], "details": "Crew 2 assigned · 12 yards scheduled"},
            {"name": "Cocoa Beach Hub", "coords": [28.3200, -80.6076], "details": "Crew 3 assigned · Canopy lift priority"},
            {"name": "Viera Hub", "coords": [28.2346, -80.7287], "details": "Crew 4 assigned · Commercial accounts clear"},
            {"name": "Palm Bay Hub", "coords": [28.0331, -80.6431], "details": "Crew 5 assigned · Stumping operations pending"}
        ]
        for hub in all_hubs:
            tooltip_content = f"<div style='font-size: 13px; line-height: 1.4;'><strong style='color:#10b981;'>{hub['name']}</strong><br/><b>Status:</b> {hub['details']}</div>"
            folium.CircleMarker(location=hub["coords"], radius=8, color="#10b981", fill=True, fill_color="#111928", fill_opacity=1.0, tooltip=folium.Tooltip(tooltip_content, sticky=True)).add_to(m)
        folium_static(m, width=910, height=375)

    with feed_col:
        st.markdown("<h4 style='margin:0;'>Activity Feed</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color:#111928; border:1px solid #1f2a37; border-radius:12px; padding:15px; height:375px; overflow-y:auto; font-size:0.85rem;'><p>🟢 <b>8:40 AM</b> - All 5 regional sectors synched matrix outputs safely.<br><span style='color:#9ca3af;'>Dispatch check-in clear.</span></p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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
        display_df = jobs_df[["Time", "Customer", "Crew", "Status"]].head(3)
        st.markdown(display_df.to_html(classes='table', index=False, escape=False), unsafe_allow_html=True)

elif clean_page_name == "📡 Live Radar":
    st.markdown("<h2>Brevard County Live Radar</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Real-time weather tracking loop centered over your exact Florida operations footprint.</p>", unsafe_allow_html=True)
    radar_html = '<iframe src="https://www.rainviewer.com/map.html?loc=28.3200,-80.6826,9&oFa=1&oC=1&oU=0&oCS=1&oF=0&oAP=1&c=3&o=80&lm=1&layer=radar&sm=1&sn=1" width="100%" height="650" frameborder="0" style="border:1px solid #1f2a37; border-radius:12px; background-color:#111928;" allowfullscreen></iframe>'
    st.components.v1.html(radar_html, height=660)

elif clean_page_name == "🗺️ Smart Routes":
    st.markdown("<h2>Smart Route Fixer</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Select a crew below and click the green button to automatically shuffle their job list into the absolute fastest driving order.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    control_col, display_col, key_col = st.columns([1.1, 3.1, 0.8])

    with control_col:
        st.markdown("<h4 style='margin-top:0;'>1. Choose Trucks</h4>", unsafe_allow_html=True)
        show_crew1 = st.checkbox("Crew 1 (North/Central Jobs)", value=True)
        show_crew2 = st.checkbox("Crew 2 (South Jobs)", value=True)
        
        st.markdown("---")
        st.markdown("<h4>2. Fix Driving Order</h4>", unsafe_allow_html=True)
        optimize_trigger = st.button("Fix Route Order Now", type="primary", use_container_width=True)

    selected_crews = []
    if show_crew1: selected_crews.append("Crew 1")
    if show_crew2: selected_crews.append("Crew 2")

    # Tracking metrics to show on screen
    total_miles_all_crews = 0.0
    total_hours_all_crews = 0.0

    with display_col:
        brevard_center = [28.3200, -80.6826]
        m_routes = folium.Map(location=brevard_center, zoom_start=10, tiles="CartoDB dark_matter")
        
        # Simple crew line styling colors
        crew_colors = {"Crew 1": "#3b82f6", "Crew 2": "#a855f7"}
        # Stop status colors
        status_colors = {"In Progress": "#f59e0b", "Completed": "#10b981", "Pending": "#4b5563"}

        for crew in selected_crews:
            crew_jobs = jobs_df[jobs_df["Crew"] == crew].to_dict(orient="records")
            
            # Silently process address locations background matrix
            valid_stops = []
            for job in crew_jobs:
                coords = geocode_address(job["Address"])
                if coords:
                    job["coords"] = coords
                    valid_stops.append(job)
                    time.sleep(0.05) # Prevent blasting the server too fast
            
            if len(valid_stops) > 1:
                base_coords = [stop["coords"] for stop in valid_stops]
                dist_matrix, _, raw_meters, raw_seconds = get_osrm_route_and_matrix(base_coords)
                
                # Run the math solver only if they clicked the button
                if optimize_trigger:
                    optimal_order = solve_or_tools_tsp(dist_matrix)
                    stops = [valid_stops[i] for i in optimal_order]
                else:
                    stops = valid_stops
                
                # Fetch route geometry paths and driving lengths
                ordered_coords = [stop["coords"] for stop in stops]
                _, road_path, final_meters, final_seconds = get_osrm_route_and_matrix(ordered_coords)
                
                # Accumulate map stats (Convert meters to miles, seconds to hours)
                total_miles_all_crews += (final_meters * 0.000621371)
                total_hours_all_crews += (final_seconds / 3600.0)
                
                # Draw true street lines
                folium.PolyLine(
                    locations=road_path,
                    color=crew_colors[crew],
                    weight=4,
                    opacity=0.85,
                    tooltip=f"{crew} Drive Track"
                ).add_to(m_routes)
            else:
                stops = valid_stops

            # Drop easy numbered pins onto the map interface
            for index, stop in enumerate(stops, start=1):
                marker_color = crew_colors[stop["Crew"]]
                tooltip_html = f"""
                    <div style='font-size: 13px; line-height: 1.4; font-family: "Inter", sans-serif;'>
                        <strong style='color:{marker_color};'>{stop['Crew']} — Stop #{index}</strong><br/>
                        <b>Customer:</b> {stop['Customer']}<br/>
                        <b>Address:</b> {stop['Address']}<br/>
                        <b>Current Status:</b> {stop['Status']}
                    </div>
                """
                
                # Give a small colored dot center matching their job completion status
                inner_status_color = status_colors.get(stop["Status"], "#4b5563")
                
                folium.CircleMarker(
                    location=stop["coords"],
                    radius=10,
                    color=marker_color,
                    fill=True,
                    fill_color=inner_status_color,
                    fill_opacity=0.9,
                    weight=3,
                    tooltip=folium.Tooltip(tooltip_html, sticky=True)
                ).add_to(m_routes)

        folium_static(m_routes, width=720, height=520)

    with key_col:
        st.markdown("<h4 style='margin-top:0;'>Route Stats</h4>", unsafe_allow_html=True)
        
        # Calculate pretty numbers for the employee overview card
        display_miles = round(total_miles_all_crews, 1)
        display_hours = round(total_hours_all_crews, 1)
        
        # Display simplified statistical performance box cards
        stats_html = f"""
        <div style="background-color: #111928; border: 1px solid #1f2a37; border-radius: 12px; padding: 15px; font-family: 'Inter', sans-serif;">
            <div style="margin-bottom: 15px;">
                <span style="font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; font-weight:600;">Total Drive Distance</span>
                <div style="font-size: 1.6rem; color: #ffffff; font-weight: 700; margin-top: 2px;">{display_miles} Miles</div>
            </div>
            <div style="margin-bottom: 5px;">
                <span style="font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; font-weight:600;">Total Time on Road</span>
                <div style="font-size: 1.6rem; color: #ffffff; font-weight: 700; margin-top: 2px;">{display_hours} Hours</div>
            </div>
            {"<hr style='border-color:#1f2a37;'/><span style='color:#10b981; font-size:0.8rem; font-weight:600;'>✅ Order is Fully Optimized</span>" if optimize_trigger else "<hr style='border-color:#1f2a37;'/><span style='color:#9ca3af; font-size:0.8rem;'>❌ Showing un-optimized sheet order</span>"}
        </div>
        """
        st.markdown(stats_html, unsafe_allow_html=True)
        
        st.markdown("<br><h4>Map Helper</h4>", unsafe_allow_html=True)
        # Ensure the string is defined clearly and not interrupted
        legend_html = """
        <div style="background-color: #111928; border: 1px solid #1f2a37; border-radius: 12px; padding: 15px; font-family: 'Inter', sans-serif; font-size: 0.85rem;">
            <b style="color: #9ca3af; font-size: 0.7rem; text-transform: uppercase;">Line Paths</b>
            <div style="display: flex; align-items: center; margin-top: 6px; margin-bottom: 10px;">
                <div style="width: 20px; height: 3px; background-color: #3b82f6; margin-right: 8px;"></div>
                <span style="color: #ffffff;">Crew 1 Route</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="width: 20px; height: 3px; background-color: #a855f7; margin-right: 8px;"></div>
                <span style="color: #ffffff;">Crew 2 Route</span>
            </div>
            
            <b style="color: #9ca3af; font-size: 0.7rem; text-transform: uppercase;">Job Status (Center Dot)</b>
            <div style="display: flex; align-items: center; margin-top: 6px; margin-bottom: 6px;">
                <div style="width: 10px; height: 10px; background-color: #10b981; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: #ffffff;">Done</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <div style="width: 10px; height: 10px; background-color: #f59e0b; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: #ffffff;">At Site Now</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 10px; height: 10px; background-color: #4b5563; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: #ffffff;">Waiting</span>
            </div>
        </div>
        """
        
        # Use components.v1.html to ensure the browser treats it as a rendered block
        st.components.v1.html(legend_html, height=300)

elif clean_page_name == "📅 Schedule":
    st.markdown("<h2>Crew Matrix & Dispatch Schedule</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Real-time operational dashboard synchronized with live Google Calendar deployments.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
    with c_kpi1:
        st.markdown('<div class="metric-card"><div class="metric-title">Total Scheduled (Week)</div><div class="metric-value">48 Jobs</div><div class="metric-delta-pos" style="color:#3b82f6;">100% capacity locked</div></div>', unsafe_allow_html=True)
    with c_kpi2:
        st.markdown('<div class="metric-card"><div class="metric-title">Tree Removals Pending</div><div class="metric-value">6 Open</div><div class="metric-delta-pos" style="color:#f59e0b;">Requires heavy rigging</div></div>', unsafe_allow_html=True)
    with c_kpi3:
        st.markdown('<div class="metric-card"><div class="metric-title">Crew Allocation</div><div class="metric-value">5 / 5 Active</div><div class="metric-delta-pos">↗ All teams dispatched</div></div>', unsafe_allow_html=True)
    with c_kpi4:
        st.markdown('<div class="metric-card"><div class="metric-title">Open Time Blocks</div><div class="metric-value">2 Available</div><div class="metric-delta-pos" style="color:#10b981;">Next target open Thursday</div></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    google_calendar_embed_url = "https://calendar.google.com/calendar/embed?src=en.usa%23holiday%40group.v.calendar.google.com&ctz=America%2FNew_York&mode=MONTH&showTitle=0&showNav=1&showDate=1&showPrint=0&showTabs=1&showCalendars=0&showTz=0"
    calendar_html = f'<iframe src="{google_calendar_embed_url}" style="border: 1px solid #1f2a37; border-radius: 12px; filter: invert(0.9) hue-rotate(180deg);" width="100%" height="700" frameborder="0" scrolling="no"></iframe>'
    st.components.v1.html(calendar_html, height=710)

else:
    st.markdown(f"<h2>{clean_page_name[2:]} Management Panel</h2>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#111928; border:1px solid #1f2a37; border-radius:12px; padding:30px;'><p style='color:#9ca3af; margin:0;'>📦 Container module frame configured and ready.</p></div>", unsafe_allow_html=True)
