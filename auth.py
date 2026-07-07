"""
Authentication Module for SwingTradeAI
Handles login/logout and session management
"""

import streamlit as st
import hashlib

# Define valid users here to avoid circular imports
VALID_USERS = {
    "admin": "admin123",
    "trader": "trader456",
    # Add more users as needed
}


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    """Verify username and password against VALID_USERS"""
    if username in VALID_USERS:
        # In this simple version, we compare plain text
        # For production, store hashed passwords in config
        return VALID_USERS[username] == password
    return False


def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None


def login_page():
    """Display login page"""
    st.set_page_config(
        page_title="SwingTradeAI Pro - Login",
        page_icon="⚡",
        layout="centered"
    )
    
    # Custom styling for login page
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            color: #1E293B;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .login-header p {
            color: #64748B;
            font-size: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div class="login-header">
                <h1>⚡ SwingTradeAI</h1>
                <p>Professional Trading Dashboard</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter your username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            
            submit_button = st.form_submit_button(
                "🔓 Login",
                use_container_width=True,
                type="primary"
            )
        
        if submit_button:
            if not username or not password:
                st.error("⚠️ Please enter both username and password")
            elif authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid username or password. Please try again.")


def logout():
    """Logout the user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


def require_login(func):
    """Decorator to require login before accessing function"""
    def wrapper(*args, **kwargs):
        init_session_state()
        if not st.session_state.authenticated:
            login_page()
            return
        return func(*args, **kwargs)
    return wrapper
