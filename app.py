import streamlit as st
import subprocess
import os
import sys

# 1. Page Configuration & Professional Styling
st.set_page_config(
    page_title="SwingTradeAI Pro Dashboard", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional modern tech interface
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { font-size: 2.5rem; font-weight: 800; color: #1E293B; letter-spacing: -0.5px; }
    h2 { font-size: 1.75rem; font-weight: 700; color: #334155; margin-top: 1.5rem; }
    h3 { font-size: 1.25rem; font-weight: 600; color: #334155; margin-top: 1rem; }
    
    /* Subheader styling for consistency */
    [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
    }
    
    /* KPI Card styling */
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val { font-size: 2rem; font-weight: 700; color: #0F172A; }
    .metric-lbl { font-size: 0.9rem; font-weight: 500; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* Terminal output styling */
    pre {
        background-color: #0F172A !important;
        border-left: 4px solid #0EA5E9 !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
        color: #38BDF8 !important;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        letter-spacing: 0 !important;
        overflow-x: auto !important;
        max-height: 600px !important;
        white-space: pre !important;
        word-wrap: normal !important;
    }
    
    pre::-webkit-scrollbar {
        height: 10px;
    }
    pre::-webkit-scrollbar-track {
        background: #1E293B;
    }
    pre::-webkit-scrollbar-thumb {
        background: #0EA5E9;
        border-radius: 4px;
    }
    pre::-webkit-scrollbar-thumb:hover {
        background: #0284C7;
    }
    
    /* Caption and info text */
    [data-testid="stMarkdownContainer"] p {
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    
    /* Button text */
    button {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Tab labels */
    [data-testid="stTabs"] button {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Info and Warning boxes */
    [data-testid="stAlert"] {
        font-size: 0.95rem !important;
    }
    
    </style>
""", unsafe_allow_html=True)

# 🛠️ DYNAMIC PATH RESOLUTION
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(current_dir, "..", "main.py")):
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
else:
    project_root = current_dir

# Title Header
st.title("⚡ SwingTradeAI Platform")
st.caption("Professional Algorithmic Scanning & Analysis Control Center")
st.markdown("---")

# 2. Top-Level Executive Metrics Grid
col_m1, col_m2, col_m3 = st.columns(3)

data_dir_path = os.path.join(project_root, "data")
data_exists = os.path.exists(data_dir_path)

with col_m1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Data Directory Status</div>
            <div class="metric-val" style="color: {'#10B981' if data_exists else '#EF4444'};">
                {'Active' if data_exists else 'Offline'}
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Target Universe</div>
            <div class="metric-val" style="color: #0EA5E9;">Mid-Cap Stocks</div>
        </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">System Mode</div>
            <div class="metric-val" style="color: #64748B;">Ad-Hoc Execution</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Helper function to run commands safely and format output beautifully
def execute_engine_command(command_args):
    with st.spinner("Processing execution pool..."):
        try:
            result = subprocess.run(
                [sys.executable, "main.py"] + command_args, 
                capture_output=True, 
                text=True, 
                check=True,
                cwd=project_root
            )
            st.toast("Command executed successfully!", icon="✅")
            st.subheader("🖥️ Execution Terminal Output")
            
            # Display using st.text with monospace - no wrapping
            st.text(result.stdout)
            
        except subprocess.CalledProcessError as e:
            st.toast("Execution error detected", icon="❌")
            st.error("Engine Halt: Process returned a non-zero exit code.")
            
            # Display error output
            output_err = f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
            st.text(output_err)

# 3. Clean Tabbed Navigation Layout
tab_ops, tab_diag, tab_maint = st.tabs(["🚀 Core Operations", "🔍 Strategy Diagnostics", "🛠️ System Maintenance"])

with tab_ops:
    st.markdown("### Market Processing & Live Signals")
    st.info("Execute scans or pull the real-time pipeline status below.")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔥 Run Ad-hoc Market Scan", use_container_width=True, type="primary"):
            execute_engine_command(["scan"])
            
    with col_btn2:
        if st.button("📊 Query Current System Status", use_container_width=True):
            execute_engine_command(["status"])

with tab_diag:
    st.markdown("### Deep Strategy Analysis & Validation")
    st.info("Deconstruct why individual symbols pass or fail your algorithmic technical rules.")
    
    col_diag1, col_diag2 = st.columns(2)
    with col_diag1:
        if st.button("🔎 Run Full Rule Diagnosis Breakdown", use_container_width=True):
            execute_engine_command(["diagnose"])
            
    with col_diag2:
        if st.button("🧪 Trigger 60-Day Historic Backtest", use_container_width=True):
            execute_engine_command(["backtest"])

with tab_maint:
    st.markdown("### Infrastructure & Initialization")
    st.warning("Running maintenance re-initializes underlying data states. Ensure market is closed or steady.")
    
    if st.button("📥 Re-download & Sync Mid-Cap Universe Data", use_container_width=True):
        execute_engine_command(["setup"])
