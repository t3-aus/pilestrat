import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =====================================================================
# PAGE CONFIGURATION & STYLING
# =====================================================================
st.set_page_config(
    page_title="Stockpile Net-Flow & Operational Field Simulator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏗️ Stockpile Net-Flow & Operational Field Simulator")
st.caption(
    "Site-Level Decision Tool: Tracking Incoming/Outgoing Velocity, Pad Utilization, and 7-Day Surge Capacity"
)

# =====================================================================
# SIDEBAR: SITE OPERATIONAL CONTROLS & PARAMETERS
# =====================================================================
st.sidebar.header("🎛️ Site Facility & Pad Parameters")

pad_length = st.sidebar.number_input("Storage Pad Length (m)", value=100.0, step=10.0)
pad_width = st.sidebar.number_input("Storage Pad Width (m)", value=100.0, step=10.0)
total_pad_area = pad_length * pad_width

st.sidebar.divider()
st.sidebar.header("📐 Geometry & Footprint Mode")

# Expanded geometry selection matching all evaluated profiles
design_option = st.sidebar.radio(
    "Select Configuration Mode",
    [
        "Option C (Modular Ribbon + Walls - 96.0% Util)",
        "Option A (Mega-Pile Slopes - 86.4% Util)",
        "Windrow (Low Profile - 93.0% Util)",
        "Ribbon (Continuous - 92.0% Util)",
        "Hybrid (Balanced - 91.0% Util)",
        "Flat Deck (Wide Area - 86.0% Util)",
        "Rectangular (High Wall - 84.0% Util)",
        "Asymmetric Block (Transition - 91.0% Util)",
        "Dual-Tier Ribbon (Multi-Level - 89.0% Util)",
        "Conical (Legacy Peak - 68.0% Util)"
    ]
)

# Map selected option to specific parameters
if "Option C" in design_option:
    pad_util_pct = 96.0
    max_height = 2.5
    wall_contained = True
elif "Option A" in design_option:
    pad_util_pct = 86.4
    max_height = 12.0
    wall_contained = False
elif "Windrow" in design_option:
    pad_util_pct = 93.0
    max_height = 3.0
    wall_contained = False
elif "Ribbon" in design_option:
    pad_util_pct = 92.0
    max_height = 4.0
    wall_contained = True
elif "Hybrid" in design_option:
    pad_util_pct = 91.0
    max_height = 4.5
    wall_contained = True
elif "Flat Deck" in design_option:
    pad_util_pct = 86.0
    max_height = 3.5
    wall_contained = False
elif "Rectangular" in design_option:
    pad_util_pct = 84.0
    max_height = 6.0
    wall_contained = True
elif "Asymmetric Block" in design_option:
    pad_util_pct = 91.0
    max_height = 3.8
    wall_contained = True
elif "Dual-Tier Ribbon" in design_option:
    pad_util_pct = 89.0
    max_height = 4.2
    wall_contained = True
else:  # Conical
    pad_util_pct = 68.0
    max_height = 8.0
    wall_contained = False

max_capacity_tonnes = st.sidebar.number_input(
    "Total Maximum Safe Storage Capacity (Tonnes)", value=95000.0, step=5000.0
)

st.sidebar.divider()
st.sidebar.header("🚛 Shift Net-Flow & Velocity Settings")

daily_incoming = st.sidebar.number_input("Average Daily Incoming (Tonnes/Day)", value=2500.0, step=250.0)
daily_outgoing = st.sidebar.number_input("Average Daily Outgoing / Dispatch (Tonnes/Day)", value=2000.0, step=250.0)
current_starting_inventory = st.sidebar.number_input("Current Inventory on Pad (Tonnes)", value=65000.0, step=5000.0)

net_daily_delta = daily_incoming - daily_outgoing

# =====================================================================
# 7-DAY FORWARD SIMULATION ENGINE
# =====================================================================
def run_operational_simulation(start_inv, daily_in, daily_out, max_cap, util_pct):
    days = [f"Day {i}" for i in range(1, 8)]
    inventory_track = []
    utilization_track = []
    status_track = []
    
    running_inv = start_inv
    for day in range(7):
        running_inv += (daily_in - daily_out)
        running_inv = np.clip(running_inv, 0.0, max_cap * 1.15) # Allow slight overfill tracking
        
        util_ratio = (running_inv / max_cap) * 100.0
        
        inventory_track.append(round(running_inv, 1))
        utilization_track.append(round(util_ratio, 1))
        
        # Traffic light operational triggers
        if util_ratio < 75.0:
            status_track.append("🟢 Normal Ops")
        elif util_ratio <= 90.0:
            status_track.append("🟡 Surge Inflow Alert")
        else:
            status_track.append("🔴 Critical / Spill Risk")
            
    return days, inventory_track, utilization_track, status_track

days_list, inv_track, util_track, status_list = run_operational_simulation(
    current_starting_inventory, daily_incoming, daily_outgoing, max_capacity_tonnes, pad_util_pct
)

# =====================================================================
# MAIN DASHBOARD: OPERATOR VIEW (CLEAR, SCANNABLE, ACTIONABLE)
# =====================================================================

col1, col2, col3, col4 = st.columns(4)

current_util = util_track[0]
current_status = status_list[0]

col1.metric("Current Pad Inventory", f"{inv_track[0]:,.0f} t", f"{net_daily_delta:+,.0f} t/day Net Delta")
col2.metric("Pad Footprint Utilization", f"{pad_util_pct:.1f}%", "Modular Wall Contained" if wall_contained else "Sloping Edge Margins")
col3.metric("Current Capacity Load", f"{current_util:.1f}%", current_status)
col4.metric("7-Day Projecting Status", status_list[-1], f"End Inv: {inv_track[-1]:,.0f} t")

st.divider()

col_left, col_right = st.columns([1.2, 1.0])

with col_left:
    st.subheader("📊 7-Day Rolling Inventory & Surge Trajectory")
    st.markdown("Tracking how net volume fluctuations (incoming vs. outgoing) impact pad capacity limits over the coming week.")
    
    fig_surge = go.Figure()
    
    fig_surge.add_trace(
        go.Scatter(
            x=days_list,
            y=inv_track,
            mode='lines+markers+text',
            name='Projected Inventory',
            line=dict(color='teal' if wall_contained else 'crimson', width=4),
            text=[f"{v:,.0f}t" for v in inv_track],
            textposition="top center"
        )
    )
    
    fig_surge.add_hline(
        y=max_capacity_tonnes,
        line_dash="dash",
        line_color="black",
        annotation_text="Max Safe Pad Capacity (100%)",
        annotation_position="bottom right"
    )
    
    fig_surge.add_hline(
        y=max_capacity_tonnes * 0.90,
        line_dash="dot",
        line_color="orange",
        annotation_text="Amber Surge Threshold (90%)",
        annotation_position="top right"
    )

    fig_surge.update_layout(
        yaxis_title="Stockpile Tonnage (Tonnes)",
        xaxis_title="Lookahead Horizon",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_surge, use_container_width=True)

with col_right:
    st.subheader("📋 Shift Supervisor 7-Day Action Plan")
    st.markdown("Operational status and loader/truck staging recommendations based on net volume momentum.")
    
    shift_df = pd.DataFrame({
        "Day": days_list,
        "Projected Tonnage": [f"{v:,.0f} t" for v in inv_track],
        "Capacity (%)": [f"{u:.1f}%" for u in util_track],
        "Field Status": status_list
    })
    
    st.dataframe(shift_df, use_container_width=True, hide_index=True)
    
    if net_daily_delta > 0:
        st.info(f"💡 **Inflow Surge Active:** Net addition of **+{net_daily_delta:,.0f} tonnes/day**. {'Modular walls are containing side spread safely.' if wall_contained else 'Monitor pile angle stability and edge spillage.'}")
    elif net_daily_delta < 0:
        st.success(f"💡 **Outflow Drawdown Active:** Net reduction of **{net_daily_delta:,.0f} tonnes/day**. {'Bounded lanes are clearing systematically with minimal loader scraping.' if wall_contained else 'Perimeter scrape-up required for sloping margins.'}")
    else:
         st.warning("⚖️ **Balanced Flow:** Incoming tonnage equals outgoing dispatches. Pad footprint is steady.")

st.divider()

# =====================================================================
# FIELD OPERATOR BRIEFING: HOW TO READ THIS ON SITE
# =====================================================================
st.subheader("🚜 On-Site Field Execution Guide")

op_col1, op_col2 = st.columns(2)

with op_col1:
    st.markdown("#### 🟢 Green / Amber / Red Zone Rules")
    st.markdown("""
    *   **< 75% Capacity (Green):** Normal operations. Full loader maneuverability and clear truck turn-around lanes.
    *   **75% – 90% Capacity (Amber):** Surge Inflow Alert. Supervisor reviews incoming truck delivery schedules against dispatch rates to prevent edge spillage.
    *   **> 90% Capacity (Red):** Critical Threshold. Trigger priority outloading or halt secondary intake until clear lanes are established.
    """)

with op_col2:
    st.markdown("#### 📐 Selected Footprint Impact")
    st.markdown(f"**Current Configuration:** `{design_option}`")
    if wall_contained:
        st.markdown("""
        *   *Field Benefit:* Rigid boundaries or low profiles provide high volume utilization. Material packs uniformly against hard limits, ensuring predictable clearing cycles and zero edge spillage during surge inflows.
        """)
    else:
        st.markdown("""
        *   *Field Benefit:* Sloping perimeter edges consume more pad footprint. Requires extra front-end loader hours to scrape scattered material from dead-zone margins as inventory shrinks.
        """)
