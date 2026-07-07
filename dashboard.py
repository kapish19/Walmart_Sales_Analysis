import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import datetime
import os

# --- Page Configurations & Premium Styling ---
st.set_page_config(
    page_title="Walmart SQL Insights Portal",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Slate Dark CSS with Glassmorphism, Neon Accents, and Hover Animations
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        /* General layout body */
        .stApp {
            background: linear-gradient(180deg, #0d1117 0%, #07090e 100%);
            color: #c9d1d9;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        }
        
        /* Clean sidebar layout */
        section[data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4);
        }
        section[data-testid="stSidebar"] .stMarkdown h3,
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] label {
            color: #8b949e !important;
            font-weight: 600;
        }
        
        /* Glassmorphism Card Aesthetics with Glow Borders */
        .kpi-card {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.7) 0%, rgba(13, 17, 23, 0.8) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px 16px;
            text-align: left;
            position: relative;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
            margin-bottom: 12px;
            height: 125px; /* Uniform card height */
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent-color, #58a6ff);
        }
        .kpi-card:hover {
            transform: translateY(-4px);
            border-color: var(--accent-color, #58a6ff);
            box-shadow: 0 12px 40px 0 rgba(0, 210, 255, 0.15);
        }
        
        .kpi-label {
            font-size: 0.78rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 2.1rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.1;
            margin-bottom: 4px;
        }
        .kpi-subtext {
            font-size: 0.8rem;
            color: #8b949e;
            font-weight: 500;
        }
        
        /* Vector SVG container inside cards */
        .card-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 46px;
            height: 46px;
            border-radius: 12px;
            flex-shrink: 0;
        }
        .card-icon svg {
            width: 22px;
            height: 22px;
        }
        
        /* Gradient Header Banner */
        .page-header {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.6) 0%, rgba(13, 17, 23, 0.7) 100%);
            padding: 24px 32px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            margin-bottom: 25px;
        }
        .page-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #58a6ff 0%, #bc8cff 50%, #ff7b72 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -0.5px;
        }
        .page-subtitle {
            font-size: 0.95rem;
            color: #8b949e;
            margin-top: 4px;
            font-weight: 500;
        }
        
        /* Tabs custom spacing & selection style */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(22, 27, 34, 0.8);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border: none;
            border-radius: 8px;
            padding: 10px 22px;
            color: #8b949e;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.25s ease;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            font-weight: 700;
        }
        
        hr {
            border: 0;
            height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0) 100%);
            margin: 25px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- Database Connection Setup ---
DB_URL = "postgresql+psycopg2://postgres:x0000@localhost:5432/walmart_db"

@st.cache_resource
def get_db_engine():
    return create_engine(DB_URL)

@st.cache_data
def load_dataset():
    engine = get_db_engine()
    df = pd.read_sql("SELECT * FROM walmart", engine)
    
    # Parse dates natively
    df['parsed_date'] = pd.to_datetime(df['date'], format='%d/%m/%y')
    df['parsed_time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
    df['hour'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
    
    # Calculate Profit
    df['profit'] = df['total'] * df['profit_margin']
    return df

try:
    df_raw = load_dataset()
except Exception as e:
    st.error(f"⚠️ Connection error: Failed to fetch transactional data from local PostgreSQL database. Details: {e}")
    st.stop()

# --- Sidebar Controls ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/Walmart_logo.svg", width=180)
st.sidebar.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
st.sidebar.subheader("🎛️ Control Panel")

# Date Range Slicer in Sidebar
min_date = df_raw['parsed_date'].min().date()
max_date = df_raw['parsed_date'].max().date()
date_range = st.sidebar.date_input(
    "Date Filter",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Slicer selectors with search
all_cities = sorted(df_raw['city'].unique())
selected_cities = st.sidebar.multiselect("Select Cities", all_cities, default=all_cities)

# Dynamically link City Selection to Branch dropdown
filtered_branches = sorted(df_raw[df_raw['city'].isin(selected_cities)]['branch'].unique())
selected_branches = st.sidebar.multiselect("Select Branches", filtered_branches, default=filtered_branches)

# Apply filters
df_filtered = df_raw[
    (df_raw['branch'].isin(selected_branches)) &
    (df_raw['city'].isin(selected_cities))
]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered['parsed_date'].dt.date >= start_date) &
        (df_filtered['parsed_date'].dt.date <= end_date)
    ]

# Reset Filters Button
if st.sidebar.button("🔄 Reset All Filters"):
    st.rerun()

# --- Main Dashboard Header Banner ---
st.markdown('<div class="page-header"><h1 class="page-title">Walmart SQL Query Results</h1><div class="page-subtitle">Interactive visual charts generated exclusively for the 9 key business problems</div></div>', unsafe_allow_html=True)

# ==========================================
# ROW 1: METRIC KPI CARDS WITH INLINE SVGs
# ==========================================
kpi_cols = st.columns(6)
total_sales = df_filtered['total'].sum()
total_profit = df_filtered['profit'].sum()
avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
total_units = df_filtered['quantity'].sum()
avg_rating = df_filtered['rating'].mean()
aov = (total_sales / len(df_filtered)) if len(df_filtered) > 0 else 0

# SVGs for Metrics
svg_revenue = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>"""
svg_profit = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>"""
svg_margin = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 7h.01M15 17h.01M9 17l6-10m-3 14c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" /></svg>"""
svg_aov = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>"""
svg_units = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>"""
svg_rating = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.907c.961 0 1.36 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.77-.57-.371-1.81.588-1.81h4.907a1 1 0 00.95-.69l1.519-4.674z" /></svg>"""

with kpi_cols[0]:
    st.markdown(f"""
        <div class="kpi-card" style="--accent-color: #58a6ff;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-label">Sales Revenue</div>
                    <div class="kpi-value">${total_sales:,.0f}</div>
                    <div class="kpi-subtext">Total Gross Volume</div>
                </div>
                <div class="card-icon" style="background-color: rgba(88, 166, 255, 0.1); color: #58a6ff;">
                    {svg_revenue}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown(f"""
        <div class="kpi-card" style="--accent-color: #3fb950;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-label">Net Profit</div>
                    <div class="kpi-value" style="color: #3fb950;">${total_profit:,.0f}</div>
                    <div class="kpi-subtext">Net Earnings</div>
                </div>
                <div class="card-icon" style="background-color: rgba(63, 185, 80, 0.1); color: #3fb950;">
                    {svg_profit}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with kpi_cols[2]:
    st.markdown(f"""
        <div class="kpi-card" style="--accent-color: #d299ff;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-label">Profit Margin</div>
                    <div class="kpi-value" style="color: #d299ff;">{avg_margin:.1f}%</div>
                    <div class="kpi-subtext">Avg Product Markup</div>
                </div>
                <div class="card-icon" style="background-color: rgba(210, 153, 255, 0.1); color: #d299ff;">
                    {svg_margin}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown(f"""
        <div class="kpi-card" style="--accent-color: #f2e05a;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-label">AOV</div>
                    <div class="kpi-value" style="color: #f2e05a;">${aov:.2f}</div>
                    <div class="kpi-subtext">Average Order Value</div>
                </div>
                <div class="card-icon" style="background-color: rgba(242, 224, 90, 0.1); color: #f2e05a;">
                    {svg_aov}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with kpi_cols[4]:
    st.markdown(f"""
        <div class="kpi-card" style="--accent-color: #f7786b;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-label">Quantity Sold</div>
                    <div class="kpi-value" style="color: #f7786b;">{total_units:,}</div>
                    <div class="kpi-subtext">Units Dispatched</div>
                </div>
                <div class="card-icon" style="background-color: rgba(247, 120, 107, 0.1); color: #f7786b;">
                    {svg_units}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with kpi_cols[5]:
    st.markdown(f"""
        <div class="kpi-card" style="--accent-color: #ff9f43;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-label">Customer Rating</div>
                    <div class="kpi-value" style="color: #ff9f43;">{avg_rating:.2f} ★</div>
                    <div class="kpi-subtext">Satisfaction Score</div>
                </div>
                <div class="card-icon" style="background-color: rgba(255, 159, 67, 0.1); color: #ff9f43;">
                    {svg_rating}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Tabs for the 9 SQL Queries ---
tab_cat, tab_pay, tab_branch_shift, tab_sandbox = st.tabs([
    "📦 Product Category Analytics (Q2, Q5, Q6)",
    "💳 Payment & Transaction Patterns (Q1, Q4, Q7)",
    "🏢 Branch & Shift Operations (Q3, Q8, Q9)",
    "💻 Live SQL Sandbox"
])

# =================================================================
# 📦 TAB: PRODUCT CATEGORY ANALYTICS (Q2, Q5, Q6)
# =================================================================
with tab_cat:
    st.markdown("## 📦 Product Category Performance & Rating Dynamics")
    
    # --- QUERY 6: Total Profit per Category ---
    st.markdown("### 1. Total Profit per Category (Query 6)")
    df_q6 = df_filtered.groupby('category').agg(
        revenue=('total', 'sum'),
        profit=('profit', 'sum')
    ).reset_index().sort_values(by='profit', ascending=False)
    
    fig_q6 = go.Figure()
    fig_q6.add_trace(go.Bar(
        x=df_q6['category'], y=df_q6['revenue'], name='Revenue ($)', marker_color='#58a6ff'
    ))
    fig_q6.add_trace(go.Bar(
        x=df_q6['category'], y=df_q6['profit'], name='Net Profit ($)', marker_color='#3fb950'
    ))
    fig_q6.update_layout(
        barmode='group',
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=10, b=20),
        height=320,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig_q6, use_container_width=True)
    st.markdown("> **💡 Decision Impact**: *Product Mix Optimization*. Identifies low profit margins relative to high revenue. Guides category pricing policies.")
    
    st.markdown("---")
    
    col_q2, col_q5 = st.columns(2)
    
    # --- QUERY 2: Highest Rated Category per Branch ---
    with col_q2:
        st.markdown("### 2. Highest-Rated Category per Branch (Query 2)")
        
        # Branch Selector Dropdown
        all_branches_q2 = sorted(df_filtered['branch'].unique().tolist())
        selected_branch_q2 = st.selectbox("Select Branch to View Rating", all_branches_q2)
        
        df_br_cat = df_filtered[df_filtered['branch'] == selected_branch_q2].groupby('category')['rating'].mean().reset_index().sort_values(by='rating', ascending=True)
        
        if len(df_br_cat) > 0:
            top_cat_row = df_br_cat.sort_values(by='rating', ascending=False).iloc[0]
            top_category = top_cat_row['category']
            top_rating = top_cat_row['rating']
            
            # Subtitle showing top rated category
            st.markdown(f"🏆 **Top-Rated Category**: `{top_category}` with Average Rating of **{top_rating:.2f} ★**")
            
            fig_q2 = px.bar(
                df_br_cat, y='category', x='rating', orientation='h',
                color='rating', color_continuous_scale=px.colors.sequential.Teal,
                labels={'rating': 'Avg Rating ⭐', 'category': 'Product Category'}
            )
            fig_q2.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=10, b=20),
                height=260,
                coloraxis_showscale=False,
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_q2, use_container_width=True)
        else:
            st.info("No ratings found for the selected branch.")
        st.markdown("> **💡 Decision Impact**: *Regional Assortment Planning*. Highlights which product lines are driving local satisfaction. Guides localized inventory allocation.")
        
    # --- QUERY 5: Category Rating Statistics per City ---
    with col_q5:
        st.markdown("### 3. Category Rating Statistics per City (Query 5)")
        # City selector dropdown
        all_cities_q5 = sorted(df_filtered['city'].unique().tolist())
        selected_city_q5 = st.selectbox("Select City", all_cities_q5)
        
        df_q5 = df_filtered[df_filtered['city'] == selected_city_q5].groupby('category')['rating'].agg(
            min_rating='min', max_rating='max', avg_rating='mean'
        ).reset_index()
        
        fig_q5 = go.Figure()
        fig_q5.add_trace(go.Bar(
            x=df_q5['category'], y=df_q5['max_rating'], name='Max Rating', marker_color='#58a6ff'
        ))
        fig_q5.add_trace(go.Bar(
            x=df_q5['category'], y=df_q5['avg_rating'], name='Avg Rating', marker_color='#bc8cff'
        ))
        fig_q5.add_trace(go.Bar(
            x=df_q5['category'], y=df_q5['min_rating'], name='Min Rating', marker_color='#ff7b72'
        ))
        fig_q5.update_layout(
            barmode='group',
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=10, b=20),
            height=320,
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig_q5, use_container_width=True)
        st.markdown("> **💡 Decision Impact**: *Customer Feedback Audits*. Visualizes the rating span of local categories. Tells store managers where service quality is volatile.")

# =================================================================
# 💳 TAB: PAYMENT & TRANSACTION PATTERNS (Q1, Q4, Q7)
# =================================================================
with tab_pay:
    st.markdown("## 💳 Payment Method Share & Branch Preferences")
    
    col_q1_bar, col_q4_donut = st.columns([3, 2])
    
    # --- QUERY 1: Payment Method Transaction Analysis ---
    with col_q1_bar:
        st.markdown("### 1. Transactions per Payment Method (Query 1)")
        df_q1 = df_filtered.groupby('payment_method').size().reset_index(name='no_payments')
        fig_q1 = px.bar(
            df_q1, x='payment_method', y='no_payments', text='no_payments',
            color_discrete_sequence=['#58a6ff']
        )
        fig_q1.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=10, b=20),
            height=320,
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig_q1, use_container_width=True)
        st.markdown("> **💡 Decision Impact**: *Merchant Fee Audits*. Cashless share indicates processing merchant overheads. Helps cashiers predict terminal queues.")
        
    # --- QUERY 4: Total Quantity Sold per Payment Method ---
    with col_q4_donut:
        st.markdown("### 2. Qty Sold per Payment Method (Query 4)")
        df_q4 = df_filtered.groupby('payment_method')['quantity'].sum().reset_index()
        fig_q4 = px.pie(
            df_q4, values='quantity', names='payment_method', hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_q4.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig_q4, use_container_width=True)
        st.markdown("> **💡 Decision Impact**: *Transaction Cost Control*. Highlights if larger cart sizes are purchased using higher fee processors.")
        
    st.markdown("---")
    
    # --- QUERY 7: Most Common Payment Method per Branch ---
    st.markdown("### 3. Preferred Payment Method Count by Branch (Query 7)")
    df_q7_raw = df_filtered.groupby(['branch', 'payment_method']).size().reset_index(name='count')
    idx_q7 = df_q7_raw.groupby('branch')['count'].idxmax()
    df_q7 = df_q7_raw.loc[idx_q7]
    df_q7_summary = df_q7.groupby('payment_method').size().reset_index(name='branch_count')
    
    fig_q7 = px.bar(
        df_q7_summary, x='payment_method', y='branch_count', text='branch_count',
        color='payment_method', color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_q7.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=10, b=20),
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig_q7, use_container_width=True)
    st.markdown("> **💡 Decision Impact**: *Regional Bank Deposits & Security*. Tracks payment channel infrastructure needs by region.")

# =================================================================
# 🏢 TAB: BRANCH & SHIFT OPERATIONS (Q3, Q8, Q9)
# =================================================================
with tab_branch_shift:
    st.markdown("## 🏢 Operational Shifts, Busiest Days, and YoY Decline Ratios")
    
    col_q8, col_q3 = st.columns(2)
    
    # --- QUERY 8: Transactions by Hourly Shifts ---
    with col_q8:
        st.markdown("### 1. Invoices by Branch and Shift (Query 8)")
        def get_shift_label(h):
            if h < 12: return 'Morning'
            elif 12 <= h <= 17: return 'Afternoon'
            else: return 'Evening'
            
        df_filtered['shift'] = df_filtered['hour'].apply(get_shift_label)
        df_q8 = df_filtered.groupby(['branch', 'shift']).size().reset_index(name='num_invoices')
        
        # Sort branches by volume to keep charts clean
        top_branches_q8 = df_filtered.groupby('branch').size().nlargest(10).index.tolist()
        df_q8_filtered = df_q8[df_q8['branch'].isin(top_branches_q8)]
        
        fig_q8 = px.bar(
            df_q8_filtered, x='branch', y='num_invoices', color='shift', barmode='stack',
            color_discrete_map={'Morning': '#f2e05a', 'Afternoon': '#58a6ff', 'Evening': '#bc8cff'}
        )
        fig_q8.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=10, b=20),
            height=340
        )
        st.plotly_chart(fig_q8, use_container_width=True)
        st.markdown("> **💡 Decision Impact**: *Workforce Scheduling*. Shifts cashiers from low-volume mornings to busy afternoons/evenings, reducing wait time.")
        
    # --- QUERY 3: Busiest Day of the Week per Branch ---
    with col_q3:
        st.markdown("### 2. Busiest Day of the Week per Branch (Query 3)")
        df_filtered['day_name'] = df_filtered['parsed_date'].dt.day_name()
        df_q3_raw = df_filtered.groupby(['branch', 'day_name']).size().reset_index(name='no_transactions')
        idx_q3 = df_q3_raw.groupby('branch')['no_transactions'].idxmax()
        df_q3 = df_q3_raw.loc[idx_q3]
        
        # Sort branches by volume to keep charts clean
        df_q3_filtered = df_q3[df_q3['branch'].isin(top_branches_q8)].sort_values(by='no_transactions', ascending=True)
        
        fig_q3 = px.bar(
            df_q3_filtered, y='branch', x='no_transactions', text='day_name', color='no_transactions',
            color_continuous_scale=px.colors.sequential.Teal
        )
        fig_q3.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=10, b=20),
            height=340,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_q3, use_container_width=True)
        st.markdown("> **💡 Decision Impact**: *Supply Chain Logistics*. Aligns store restocking schedule with busiest weekly sale peaks.")

    st.markdown("---")
    
    # --- QUERY 9: YoY Revenue Decrease Ratio (2022 vs 2023) ---
    st.markdown("### 3. Top 5 Branches with Highest Revenue Decrease Ratio (Query 9)")
    df_yoy_base = df_filtered[df_filtered['parsed_date'].dt.year.isin([2022, 2023])]
    if len(df_yoy_base) > 0:
        df_yoy = df_yoy_base.groupby([df_yoy_base['parsed_date'].dt.year, 'branch'])['total'].sum().reset_index()
        df_yoy_pivot = df_yoy.pivot(index='branch', columns='parsed_date', values='total').reset_index()
        
        # Check if both years are present
        if 2022 in df_yoy_pivot.columns and 2023 in df_yoy_pivot.columns:
            df_yoy_pivot['rev_change'] = df_yoy_pivot[2022] - df_yoy_pivot[2023]
            df_yoy_pivot['change_ratio'] = (df_yoy_pivot['rev_change'] / df_yoy_pivot[2022]) * 100
            
            # Sort to find highest decrease
            df_q9 = df_yoy_pivot[df_yoy_pivot['rev_change'] > 0].sort_values(by='change_ratio', ascending=False).head(5)
            
            if len(df_q9) > 0:
                col_q9_chart, col_q9_tbl = st.columns([3, 2])
                with col_q9_chart:
                    fig_q9 = px.bar(
                        df_q9, x='branch', y='change_ratio', text='change_ratio',
                        color='change_ratio', color_continuous_scale=px.colors.sequential.Reds,
                        labels={'change_ratio': 'Decline Ratio (%)'}
                    )
                    fig_q9.update_layout(
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=10, b=20),
                        height=300,
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_q9, use_container_width=True)
                with col_q9_tbl:
                    st.dataframe(df_q9.style.format({
                        2022: '${:,.2f}',
                        2023: '${:,.2f}',
                        'rev_change': '${:,.2f}',
                        'change_ratio': '{:.2f}%'
                    }), use_container_width=True)
            else:
                st.info("No branches recorded a revenue decrease YoY (2022 vs 2023) in the current selection.")
        else:
            st.warning("Date filters must contain records for both 2022 and 2023 to generate YoY Decrease ratios.")
    else:
        st.warning("No records found for comparison in 2022/2023.")
    st.markdown("> **💡 Decision Impact**: *Regional Underperformance Audits*. Identifies branches suffering from revenue contraction. Triggers strategic recovery campaigns or branch consolidation decisions.")

# =================================================================
# 💻 TAB: LIVE SQL SANDBOX
# =================================================================
with tab_sandbox:
    st.markdown("### 💻 PostgreSQL Live SQL Editor")
    st.markdown("Type any PostgreSQL queries directly against the `walmart` database table and retrieve metrics instantly.")
    
    # Query Templates Selectbox
    templates = {
        "Select Template Query": "",
        "Busiest Day per Branch (Q3)": """SELECT branch, day_name, no_transactions
FROM (
    SELECT 
        branch,
        TO_CHAR(TO_DATE(date, 'DD/MM/YY'), 'Day') as day_name,
        COUNT(*) as no_transactions,
        RANK() OVER(PARTITION BY branch ORDER BY COUNT(*) DESC) as rank
    FROM walmart
    GROUP BY 1, 2
) AS subquery
WHERE rank = 1;""",
        "Highest Profit Categories (Q6)": """SELECT 
    category,
    ROUND(SUM(total)::numeric, 2) as total_revenue,
    ROUND(SUM(total * profit_margin)::numeric, 2) as profit
FROM walmart
GROUP BY 1
ORDER BY profit DESC;""",
        "Most Common Payment per Branch (Q7)": """WITH cte AS (
    SELECT 
        branch,
        payment_method,
        COUNT(*) as total_trans,
        RANK() OVER(PARTITION BY branch ORDER BY COUNT(*) DESC) as rank
    FROM walmart
    GROUP BY 1, 2
)
SELECT branch, payment_method AS preferred_payment_method
FROM cte
WHERE rank = 1;"""
    }
    
    selected_template = st.selectbox("Load SQL Template", list(templates.keys()))
    
    default_sql = templates[selected_template] if templates[selected_template] else "SELECT * FROM walmart LIMIT 5;"
    user_sql = st.text_area("SQL Editor Workspace", value=default_sql, height=150)
    
    col_run, col_dl_sql = st.columns([1, 4])
    
    with col_run:
        run_btn = st.button("Run SQL Query ⚡")
        
    if run_btn:
        try:
            engine = get_db_engine()
            res_df = pd.read_sql_query(user_sql, engine)
            st.success("🎉 Query Executed Successfully!")
            st.dataframe(res_df, use_container_width=True)
            
            # Download query result CSV
            csv = res_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download SQL Query Results (CSV)",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"❌ SQL Execution Error: {e}")
            
    st.markdown("---")
    
    # Export full filtered dataset
    st.markdown("### Export Current Filtered Dataset")
    st.markdown(f"The filters applied generated **{len(df_filtered):,}** transaction records.")
    
    filtered_csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Current Filtered Data (CSV)",
        data=filtered_csv,
        file_name="walmart_filtered_data.csv",
        mime="text/csv"
    )
