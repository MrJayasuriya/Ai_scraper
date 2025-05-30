import streamlit as st
import re
from typing import Optional, Dict
from .database import db_manager

class AuthManager:
    """Authentication manager for Streamlit app"""
    
    def __init__(self):
        self.db = db_manager
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict[str, str]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def validate_username(self, username: str) -> Dict[str, str]:
        """Validate username"""
        errors = []
        
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        if len(username) > 30:
            errors.append("Username must be less than 30 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username can only contain letters, numbers, and underscores")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def show_login_form(self) -> bool:
        """Display premium login form with enhanced UX"""
        
        with st.form("login_form", clear_on_submit=False):
            # Enhanced input fields with custom styling
            st.markdown('<div class="auth-input-group">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                <span style="font-size: 1.2rem;">👤</span>
                <label style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    Username or Email Address
                </label>
            </div>
            """, unsafe_allow_html=True)
            username = st.text_input(
                "Username or Email", 
                placeholder="Enter your username or email address",
                label_visibility="collapsed",
                key="login_username"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input-group">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                <span style="font-size: 1.2rem;">🔐</span>
                <label style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    Password
                </label>
            </div>
            """, unsafe_allow_html=True)
            password = st.text_input(
                "Password", 
                type="password", 
                placeholder="Enter your secure password",
                label_visibility="collapsed",
                key="login_password"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Enhanced submit button
            st.markdown('<div class="auth-button-container">', unsafe_allow_html=True)
            submit_button = st.form_submit_button(
                "🚀 Sign In to Your Workspace", 
                use_container_width=True,
                type="primary"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_button:
                if username and password:
                    # Show loading state
                    with st.spinner("🔐 Authenticating your credentials..."):
                        result = self.db.authenticate_user(username, password)
                        
                        if result["success"]:
                            # Create session
                            session_token = self.db.create_session(result["user_id"])
                            
                            # Update session state
                            st.session_state.authenticated = True
                            st.session_state.user_info = {
                                "user_id": result["user_id"],
                                "username": result["username"],
                                "email": result["email"]
                            }
                            st.session_state.session_token = session_token
                            
                            # Enhanced success message
                            st.markdown(f"""
                            <div class="auth-form-message success">
                                <span style="font-size: 1.4rem;">🎉</span>
                                <div>
                                    <div style="font-weight: 700;">Welcome back, {result['username']}!</div>
                                    <div style="font-size: 0.9rem; opacity: 0.8;">Redirecting to your personal workspace...</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Small delay for better UX
                            import time
                            time.sleep(1)
                            st.rerun()
                            return True
                        else:
                            # Enhanced error message
                            st.markdown(f"""
                            <div class="auth-form-message error">
                                <span style="font-size: 1.4rem;">❌</span>
                                <div>
                                    <div style="font-weight: 700;">Authentication Failed</div>
                                    <div style="font-size: 0.9rem; opacity: 0.8;">{result['error']}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="auth-form-message error">
                        <span style="font-size: 1.4rem;">⚠️</span>
                        <div>
                            <div style="font-weight: 700;">Missing Information</div>
                            <div style="font-size: 0.9rem; opacity: 0.8;">Please fill in all fields to continue</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Additional help section
        st.markdown("""
        <div style="margin-top: 2rem; text-align: center; padding: 1.5rem; 
                    background: rgba(255, 255, 255, 0.03); border-radius: 16px; 
                    border: 1px solid rgba(255, 255, 255, 0.05);">
            <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem;">
                💡 <strong>Tip:</strong> You can use either your username or email address to sign in
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    def show_signup_form(self) -> bool:
        """Display premium signup form with enhanced UX and real-time validation"""
        
        with st.form("signup_form", clear_on_submit=False):
            # Enhanced input fields with icons and styling
            st.markdown('<div class="auth-input-group">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                <span style="font-size: 1.2rem;">👤</span>
                <label style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    Choose Your Username
                </label>
            </div>
            """, unsafe_allow_html=True)
            username = st.text_input(
                "Username", 
                placeholder="3-30 characters, letters, numbers, underscore",
                label_visibility="collapsed",
                key="signup_username"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input-group">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                <span style="font-size: 1.2rem;">📧</span>
                <label style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    Email Address
                </label>
            </div>
            """, unsafe_allow_html=True)
            email = st.text_input(
                "Email", 
                placeholder="your.email@example.com",
                label_visibility="collapsed",
                key="signup_email"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input-group">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                <span style="font-size: 1.2rem;">🔐</span>
                <label style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    Create Password
                </label>
            </div>
            """, unsafe_allow_html=True)
            password = st.text_input(
                "Password", 
                type="password", 
                placeholder="Minimum 8 characters with uppercase, lowercase, number",
                label_visibility="collapsed",
                key="signup_password"
            )
            
            # Real-time password strength indicator
            if password:
                strength_score = 0
                strength_text = "Weak"
                strength_class = "strength-weak"
                
                if len(password) >= 8:
                    strength_score += 1
                if re.search(r'[A-Z]', password):
                    strength_score += 1
                if re.search(r'[a-z]', password):
                    strength_score += 1
                if re.search(r'\d', password):
                    strength_score += 1
                
                if strength_score >= 4:
                    strength_text = "Strong"
                    strength_class = "strength-strong"
                elif strength_score >= 2:
                    strength_text = "Medium"
                    strength_class = "strength-medium"
                
                st.markdown(f"""
                <div class="password-strength {strength_class}">
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.8);">Password Strength:</span>
                        <span style="font-size: 0.9rem; font-weight: 600;">{strength_text}</span>
                    </div>
                    <div class="password-strength-bar">
                        <div class="password-strength-fill"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input-group">', unsafe_allow_html=True)
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                <span style="font-size: 1.2rem;">🔒</span>
                <label style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    Confirm Password
                </label>
            </div>
            """, unsafe_allow_html=True)
            confirm_password = st.text_input(
                "Confirm Password", 
                type="password", 
                placeholder="Re-enter your password to confirm",
                label_visibility="collapsed",
                key="signup_confirm_password"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Enhanced submit button
            st.markdown('<div class="auth-button-container">', unsafe_allow_html=True)
            submit_button = st.form_submit_button(
                "🎯 Create Your Pro Account", 
                use_container_width=True,
                type="primary"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_button:
                # Enhanced validation with better error display
                errors = []
                
                if not all([username, email, password, confirm_password]):
                    errors.append("All fields are required")
                
                # Validate username
                username_validation = self.validate_username(username)
                if not username_validation["valid"]:
                    errors.extend(username_validation["errors"])
                
                # Validate email
                if not self.validate_email(email):
                    errors.append("Please enter a valid email address")
                
                # Validate password
                password_validation = self.validate_password(password)
                if not password_validation["valid"]:
                    errors.extend(password_validation["errors"])
                
                # Check password confirmation
                if password != confirm_password:
                    errors.append("Passwords do not match")
                
                if errors:
                    # Display all errors in a nice format
                    error_list = "".join([f"<li>{error}</li>" for error in errors])
                    st.markdown(f"""
                    <div class="auth-form-message error">
                        <span style="font-size: 1.4rem;">❌</span>
                        <div>
                            <div style="font-weight: 700;">Please fix the following issues:</div>
                            <ul style="margin: 0.5rem 0 0 1rem; font-size: 0.9rem; opacity: 0.9;">
                                {error_list}
                            </ul>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    return False
                
                # Create user with loading state
                with st.spinner("🎯 Creating your premium account..."):
                    result = self.db.create_user(username, email, password)
                    
                    if result["success"]:
                        # Enhanced success message
                        st.markdown(f"""
                        <div class="auth-form-message success">
                            <span style="font-size: 1.4rem;">🎉</span>
                            <div>
                                <div style="font-weight: 700;">Account Created Successfully!</div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Welcome to AI Scraper Pro, {username}! Signing you in...</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Auto-login after signup
                        auth_result = self.db.authenticate_user(username, password)
                        if auth_result["success"]:
                            session_token = self.db.create_session(auth_result["user_id"])
                            
                            st.session_state.authenticated = True
                            st.session_state.user_info = {
                                "user_id": auth_result["user_id"],
                                "username": auth_result["username"],
                                "email": auth_result["email"]
                            }
                            st.session_state.session_token = session_token
                            
                            # Small delay for better UX
                            import time
                            time.sleep(1.5)
                            st.rerun()
                            return True
                    else:
                        # Enhanced error message
                        st.markdown(f"""
                        <div class="auth-form-message error">
                            <span style="font-size: 1.4rem;">❌</span>
                            <div>
                                <div style="font-weight: 700;">Account Creation Failed</div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">{result['error']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Enhanced requirements and help section
        st.markdown("""
        <div style="margin-top: 2rem; padding: 1.5rem; 
                    background: rgba(255, 255, 255, 0.03); border-radius: 16px; 
                    border: 1px solid rgba(255, 255, 255, 0.05);">
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="color: rgba(255, 255, 255, 0.9); font-weight: 600; font-size: 1rem;">
                    📋 Account Requirements
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                <div style="background: rgba(255, 255, 255, 0.02); padding: 1rem; border-radius: 12px;">
                    <div style="color: rgba(255, 255, 255, 0.8); font-weight: 600; margin-bottom: 0.5rem;">
                        👤 Username Guidelines
                    </div>
                    <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">
                        • 3-30 characters<br>
                        • Letters, numbers, underscore only<br>
                        • Must be unique
                    </div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.02); padding: 1rem; border-radius: 12px;">
                    <div style="color: rgba(255, 255, 255, 0.8); font-weight: 600; margin-bottom: 0.5rem;">
                        🔐 Password Security
                    </div>
                    <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">
                        • Minimum 8 characters<br>
                        • Uppercase & lowercase letters<br>
                        • At least one number
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated and session is valid"""
        # Initialize session state variables if they don't exist
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
            
        if not st.session_state.authenticated or not st.session_state.session_token:
            return False
        
        # Validate session token
        user_info = self.db.validate_session(st.session_state.session_token)
        if user_info:
            # Update user info in session state
            st.session_state.user_info = user_info
            return True
        else:
            # Session expired or invalid
            self.logout()
            return False
    
    def logout(self):
        """Logout user and clean up session"""
        # Initialize session state variables if they don't exist
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
            
        if st.session_state.session_token:
            self.db.logout_user(st.session_state.session_token)
        
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.session_token = None
        
        st.rerun()
    
    def get_current_user_id(self) -> Optional[int]:
        """Get current user ID if authenticated"""
        # Ensure session state is initialized
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
            
        if self.check_authentication() and st.session_state.user_info:
            return st.session_state.user_info["user_id"]
        return None
    
    def get_current_username(self) -> Optional[str]:
        """Get current username if authenticated"""
        # Ensure session state is initialized
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
            
        if self.check_authentication() and st.session_state.user_info:
            return st.session_state.user_info["username"]
        return None
    
    def show_user_info(self):
        """Display current user information in sidebar"""
        # Ensure session state is initialized
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
            
        if self.check_authentication() and st.session_state.user_info:
            st.markdown('<div class="section-header">👤 User Account</div>', unsafe_allow_html=True)
            
            user_info = st.session_state.user_info
            st.markdown(f"""
            <div class="status-success">
                <span style="font-size: 1.2rem;">👤</span>
                <span><strong>{user_info['username']}</strong><br>{user_info['email']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                self.logout()

# Create global auth manager instance
auth_manager = AuthManager() 