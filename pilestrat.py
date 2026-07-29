import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =====================================================================
# PAGE CONFIGURATION & STYLING
# =====================================================================
st.set_page_config(
    page_title="Carina West: Advanced Stockpile Simulator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏗️ Carina West Facility: Multi-Variable Stockpile Dynamics Simulator")
st.caption(
    "Analyzing Net-Flow, Seasonal Takt Times, Geometry Performance, and Pad Shape Constraints Across All Configurations"
)

# =====================================================================
# GEOMETRY DATABASE & DEFINITIONS (ALL 5 PROFILES)
# =====================================================================
GEOMETRY_PROFILES = {
    "Option C (Modular Ribbon + Walls)": {"util": 0.96, "wall": True, "takt_eff": 0.98},
    "Windrow (Low Profile)": {"util": 0.93, "wall": False, "takt_eff": 0.90},
    "Option A (Mega-Pile Slopes)": {"util": 0.864, "wall": False, "takt_eff": 0.75},
    "Conical (Legacy Peak)": {"util": 0.68, "wall": False, "takt_eff": 0.60},
    "Rectangular (High Wall)": {"util": 0.84, "wall": True, "takt_eff": 0.80}
}

# =====================================================================
# SIDEBAR: SIMULATION CONTROLS
# =====================================================================
st.sidebar.header("🎛️ Facility & Operations Parameters")

# 1. Facility Baseline
rated_capacity = st.sidebar.number_input("Rated Stockpile Capacity (Tonnes)", value=95000.0, step=5000.0)

# 2. Seasonal Takt Flow Regime
season_mode = st.sidebar.selectbox(
    "Select Seasonal Operating Regime",
    [
        "Peak Harvest Surge (Inflow > Processing)",
        "Winter Wet / High Humidity (Balanced / Managed)",
        "Transition Period (Moderate Inflow)",
        "Summer Steady-State (Outflow / Drawdown)"
    ]
)

# Preset velocities based on operational reality
if "Peak Harvest" in season_mode:
    default_in = 4500.0
    default_out = 2500.0
    default_inv = 65000.0
elif "Winter Wet" in season_mode:
    default_in = 1500.0
    default_out = 2000.0
    default_inv = 40000.0
elif "Transition" in season_mode:
    default_in = 2200.0
    default_out = 2200.0
    default_inv = 50000.0
else:  # Summer
    default_in = 1000.0
    default_out = 2800.0
    default_inv = 70000.0

daily_incoming = st.sidebar.number_input("Intake Velocity (Tonnes/Day)", value=default_in, step=250.0)
daily_outgoing = st.sidebar.number_input("Processing Plant Takt Outflow (Tonnes/Day)", value=default_out, step=250.0)
current_starting_inventory = st.sidebar.number_input("Starting Pad Inventory (Tonnes)", value=default_inv, step=5000.0)

net_daily_delta = daily_incoming - daily_outgoing

# 3. Pad Footprint & Shape Constraints (Fully Adjustable Dimensions)
st.sidebar.divider()
st.sidebar.header("📐 Pad Constraint Analysis")

pad_length = st.sidebar.number_input("Pad Length (m)", value=150.0, step=5.0)
pad_width = st.sidebar.number_input("Pad Width (m)", value=66.66, step=2.0)
pad_area_sqm = pad_length * pad_width

st.sidebar.markdown(f"**Total Available Pad Area:** `{pad_area_sqm:,.0f}` sq meters")

selected_pad = {"l": pad_length, "w": pad_width}
selected_pad_name = f"Custom Pad ({pad_length:g}m x {pad_width:g}m)"

# =====================================================================
# SIMULATION ENGINE
# =====================================================================

def run_net_flow_simulation(start_inv, daily_in, daily_out, rated_cap):
    days = [f"Day {i}" for i in range(1, 8)]
    inventory_track = []
    status_track = []
    
    running_inv = start_inv
    for day in range(7):
        running_inv += (daily_in - daily_out)
        running_inv = np.clip(running_inv, 0.0, rated_cap * 1.15) 
        util_ratio = (running_inv / rated_cap) * 100.0
        
        inventory_track.append(round(running_inv, 1))
        
        if util_ratio < 75.0:
            status_track.append("🟢 Normal Ops")
        elif util_ratio <= 90.0:
            status_track.append("🟡 Surge Alert")
        else:
            status_track.append("🔴 Overfill Risk")
            
    return days, inventory_track, status_track

volume_steps = np.linspace(0, rated_capacity * 1.15, 50)

def calculate_loader_efficiency_kpi(vol_array, profile_data, rated_cap, pad_config):
    util_pct = profile_data["util"]
    takt_eff = profile_data["takt_eff"]
    is_wall = profile_data["wall"]
    
    pad_l = pad_config["l"]
    pad_w = pad_config["w"]
    pad_aspect_ratio = max(pad_l, pad_w) / min(pad_l, pad_w)
    
    travel_penalty = 1.0 if pad_aspect_ratio == 1.0 else (0.95 if is_wall else 0.85)
    
    loader_scores = []
    for v in vol_array:
        load_ratio = v / rated_cap
        base_score = takt_eff * 100.0 * travel_penalty
        
        if load_ratio <= 0.75:
            score = base_score
        elif load_ratio <= 1.0:
            decay_rate = 0.2 if is_wall else 0.4
            score = base_score * (1.0 - (load_ratio - 0.75) * decay_rate)
        else:
            overfill_penalty = 0.3 if is_wall else 0.6
            score = max(30.0, base_score * (0.8 - (load_ratio - 1.0) * overfill_penalty))
            
        loader_scores.append(round(score, 1))
        
    return loader_scores

days_list, inv_track, status_list = run_net_flow_simulation(
    current_starting_inventory, daily_incoming, daily_outgoing, rated_capacity
)

# =====================================================================
# MAIN DASHBOARD LAYOUT
# =====================================================================
st.subheader(f"Operational Overview: {season_mode} | Active Pad: {selected_pad_name}")
col1, col2, col3, col4 = st.columns(4)

current_util_pct = (inv_track[0] / rated_capacity) * 100.0
current_status = status_list[0]

col1.metric("Current Inventory", f"{inv_track[0]:,.0f} t", f"{net_daily_delta:+,.0f} t/day Net Takt")
col2.metric("Current Capacity Load", f"{current_util_pct:.1f}%", current_status)
col3.metric("7-Day Status Projection", status_list[-1], f"End Inv: {inv_track[-1]:,.0f} t")
col4.metric("Max Facility Takt", f"{rated_capacity:,.0f} t", "Rated Capacity Baseline")

st.divider()

# =====================================================================
# GRAPHIC 1: 7-DAY INVENTORY SURGE TRAJECTORY
# =====================================================================
st.subheader("📊 7-Day Rolling Inventory Surge Trajectory vs. Capacity Limits")

fig_surge = go.Figure()

fig_surge.add_trace(
    go.Scatter(
        x=days_list,
        y=inv_track,
        mode='lines+markers+text',
        name='Projected Inventory',
        line=dict(color='teal', width=4),
        text=[f"{v:,.0f}t" for v in inv_track],
        textposition="top center"
    )
)

fig_surge.add_hline(
    y=rated_capacity,
    line_dash="dash",
    line_color="black",
    annotation_text=f"Rated Capacity ({rated_capacity:,.0f} t)",
    annotation_position="bottom right"
)

fig_surge.add_hline(
    y=rated_capacity * 0.90,
    line_dash="dot",
    line_color="orange",
    annotation_text="Surge Threshold (90%)",
    annotation_position="top right"
)

fig_surge.update_layout(
    yaxis_title="Stockpile Tonnage (Tonnes)",
    xaxis_title="Lookahead Horizon",
    height=400,
    margin=dict(l=20, r=20, t=30, b=20)
)
st.plotly_chart(fig_surge, use_container_width=True)

st.divider()

# =====================================================================
# GRAPHIC 2 & 3: MULTI-GEOMETRY COMPARISON ACROSS PAD DIMENSIONS
# =====================================================================
st.subheader(f"📈 Comprehensive Geometry Performance Analysis on {selected_pad_name}")
st.markdown(f"Comparing all 5 stockpile geometries simultaneously as volume scales from 0 to rated capacity ({rated_capacity:,.0f}t) and into overfill, governed by your custom pad dimensions and aspect ratios.")

kpi_col1, kpi_col2 = st.columns(2)

# Compute curves for ALL geometries in GEOMETRY_PROFILES
all_geo_names = list(GEOMETRY_PROFILES.keys())
chart_data_frames = []

for geo_name in all_geo_names:
    p_data = GEOMETRY_PROFILES[geo_name]
    scores = calculate_loader_efficiency_kpi(volume_steps, p_data, rated_capacity, selected_pad)
    
    df_temp = pd.DataFrame({
        "Stockpile Volume (t)": volume_steps,
        "Loader Productivity Index (%)": scores,
        "Geometry": geo_name,
        "Pad Shape": selected_pad_name
    })
    chart_data_frames.append(df_temp)

df_kpi_chart = pd.concat(chart_data_frames)

# Plotly Multi-Geometry Efficiency Lines
fig_eff = go.Figure()
for geo_name in all_geo_names:
    df_geo = df_kpi_chart[df_kpi_chart["Geometry"] == geo_name]
    fig_eff.add_trace(
        go.Scatter(
            x=df_geo["Stockpile Volume (t)"],
            y=df_geo["Loader Productivity Index (%)"],
            mode='lines',
            name=geo_name,
            line=dict(width=3)
        )
    )

fig_eff.add_vline(x=rated_capacity, line_dash="dash", line_color="black")
fig_eff.add_vline(x=rated_capacity * 0.90, line_dash="dot", line_color="orange")

fig_eff.update_layout(
    xaxis_title="Stockpile Volume / Tonnage on Pad (Tonnes)",
    yaxis_title="Loader Productivity & Takt Efficiency Index (%)",
    yaxis=dict(range=[20, 105]),
    height=380,
    margin=dict(l=20, r=20, t=10, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="right", x=1)
)
kpi_col1.plotly_chart(fig_eff, use_container_width=True)

# Plotly Multi-Geometry Footprint Utilization Bar Chart
fig_util = go.Figure()
fig_util.add_trace(go.Bar(
    y=all_geo_names,
    x=[GEOMETRY_PROFILES[g]["util"] * 100 for g in all_geo_names],
    orientation='h',
    name='Active Storage Zone',
    marker=dict(color=['teal', 'skyblue', 'orange', 'crimson', 'purple']),
    text=[f"Active: {GEOMETRY_PROFILES[g]['util']*100:.1f}%" for g in all_geo_names],
    textposition='inside'
))

fig_util.update_layout(
    barmode='stack',
    title=f"Footprint Utilization Efficiency Across All Profiles ({rated_capacity:,.0f}t)",
    xaxis=dict(range=[0, 100], title="Pad Area Breakdown (%)"),
    height=380,
    margin=dict(l=20, r=20, t=30, b=20),
    showlegend=False
)
kpi_col2.plotly_chart(fig_util, use_container_width=True)

st.divider()

# =====================================================================
# OPERATIONAL SUMMARY & LIMITS EXPLANATION
# =====================================================================
st.subheader("📖 Operational Summary: Multi-Geometry Benchmark & Limits")
st.markdown(
    f"""Running the simulator under the **{season_mode}** scenario with pad dimensions set to **{pad_length:g}m × {pad_width:g}m** highlights how every geometric profile performs side-by-side:

1. **Peak Harvest Surge Impact:** With net addition of **+{net_daily_delta:,.0f} tonnes/day**, inventory pushes toward the **{rated_capacity:,.0f}t Rated Capacity**, testing boundary limits across all profiles.
2. **Custom Pad Aspect Ratio & Boundary Collision:**
   - **Wall-Contained Configurations (Option C & Rectangular High Wall):** Restrict lateral spread rigidly, maintaining high active storage footprint efficiencies ($84\%$ to $96\%$) and stable loader productivity indices under surge conditions.
   - **Sloping Configurations (Conical, Mega-Pile Slopes, & Windrow):** Subject to natural angle-of-repose degradation. As volume passes **0.75C ({rated_capacity * 0.75:,.0f} tonnes)**, perimeter spread collides with your custom **{pad_width:g}m** width boundary, driving up loader idle travel penalties and clean-up labor.
3. **Interactive Control:** Changing any parameter in the sidebar instantly recalculates all 5 geometry curves and utilization bars simultaneously, keeping the model fully integrated and interactive."""
)
