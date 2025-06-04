import streamlit as st
import pandas as pd
import json
import os
from dotenv import load_dotenv
import time
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import platform

# Import custom modules
from src.utils.database import db_manager
from src.utils.auth import auth_manager
from src.services.serper_api import serper_api
# Import the JSearch Job Scraper instead of Universal Job Scraper
from jsearch_job_scraper import JSearchJobScraper, JOB_TEMPLATES
# Use enhanced scraper with retry mechanism and concurrent processing for AI extraction tab
try:
    from src.services.scrape_ai_enhanced import process_links_from_database, get_results_for_download
    ENHANCED_SCRAPER_AVAILABLE = True
    print("✓ Using enhanced scraper with retry mechanism and concurrent processing")
except ImportError as e:
    print(f"! Enhanced scraper not available ({e}), falling back to simple scraper")
    try:
        from src.services.scrape_ai_simple import process_links_from_database, get_results_for_download
        ENHANCED_SCRAPER_AVAILABLE = False
        print("✓ Using simple scraper (deployment mode)")
    except ImportError as e2:
        print(f"❌ No scraper available: {e2}")
        # Create dummy functions as last resort
        def process_links_from_database(progress_callback=None, status_callback=None, user_id=None):
            if status_callback:
                status_callback("❌ No scraper available - please check dependencies")
            return 0
        def get_results_for_download(user_id=None):
            return []
        ENHANCED_SCRAPER_AVAILABLE = False
# Import Google Maps Extractor
from google_maps_extractor import GoogleMapsExtractor

# Fix for Windows asyncio subprocess issue
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Contact Scraper Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS with glassmorphism and modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default Streamlit styling */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95%;
    }
    
    /* Premium header */
    .premium-header {
        background: linear-gradient(135deg, rgba(29, 78, 216, 0.8), rgba(147, 51, 234, 0.8), rgba(236, 72, 153, 0.8));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 3rem 2rem;
        margin-bottom: 3rem;
        color: white;
        text-align: center;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        position: relative;
        overflow: hidden;
    }
    
    .premium-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .premium-header h1 {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #ffffff, #e0e7ff, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
    }
    
    .premium-header p {
        font-size: 1.25rem;
        font-weight: 400;
        margin: 1rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Glass card styling */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Status indicators */
    .status-success {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(59, 130, 246, 0.2));
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        color: #10b981;
        font-weight: 600;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .status-error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(245, 101, 101, 0.2));
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        color: #ef4444;
        font-weight: 600;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .status-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(251, 191, 36, 0.2));
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        color: #f59e0b;
        font-weight: 600;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .status-info {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(147, 197, 253, 0.2));
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        color: #3b82f6;
        font-weight: 600;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
    }
    
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-weight: 500;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb, #7c3aed);
    }
    
    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        border-radius: 10px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(15, 15, 35, 0.95), rgba(26, 26, 46, 0.95));
        backdrop-filter: blur(20px);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 0.5rem;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: rgba(255, 255, 255, 0.7);
        font-weight: 600;
        padding: 1rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
    }
    
    /* DataFrame styling */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem;
        border-radius: 16px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    }
    
    /* Text color */
    .css-10trblm, .css-1ec4kjn, .css-1cpxqw2, .css-16huue1 {
        color: white;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Upload area */
    .uploadedFile {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #2563eb, #7c3aed);
    }
    
    /* Floating elements */
    .floating-card {
        animation: floating 3s ease-in-out infinite;
    }
    
    @keyframes floating {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* Glow effects */
    .glow-blue {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    
    .glow-purple {
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
    }
    
    .glow-pink {
        box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
    }

    /* Authentication styling */
    .auth-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 3rem 2rem;
        position: relative;
    }
    
    .auth-glass-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(25px);
        border: 2px solid rgba(255, 255, 255, 0.15);
        border-radius: 28px;
        padding: 3rem 2.5rem;
        box-shadow: 
            0 25px 50px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            0 0 80px rgba(59, 130, 246, 0.3);
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .auth-glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, 
            transparent 30%, 
            rgba(255, 255, 255, 0.1) 50%, 
            transparent 70%);
        animation: shimmer 4s infinite;
        pointer-events: none;
    }
    
    .auth-glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 
            0 35px 70px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3),
            0 0 120px rgba(59, 130, 246, 0.4);
        border-color: rgba(255, 255, 255, 0.25);
    }
    
    .auth-tabs-container {
        margin-bottom: 3rem;
        position: relative;
    }
    
    .auth-tabs {
        display: flex;
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.1));
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 0.5rem;
        position: relative;
        overflow: hidden;
    }
    
    .auth-tabs::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, 
            rgba(59, 130, 246, 0.1) 0%, 
            rgba(139, 92, 246, 0.1) 50%, 
            rgba(236, 72, 153, 0.1) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .auth-tabs:hover::before {
        opacity: 1;
    }
    
    .auth-tab {
        flex: 1;
        padding: 1.2rem 2rem;
        text-align: center;
        border-radius: 16px;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        color: rgba(255, 255, 255, 0.6);
        font-weight: 600;
        font-size: 1.1rem;
        position: relative;
        z-index: 2;
        overflow: hidden;
    }
    
    .auth-tab::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
        opacity: 0;
        transition: opacity 0.3s ease;
        border-radius: 16px;
        z-index: -1;
    }
    
    .auth-tab.active {
        color: white;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(59, 130, 246, 0.4);
    }
    
    .auth-tab.active::before {
        opacity: 1;
    }
    
    .auth-tab:hover:not(.active) {
        color: rgba(255, 255, 255, 0.9);
        transform: translateY(-1px);
        background: rgba(255, 255, 255, 0.1);
    }
    
    /* Enhanced form styling */
    .auth-form-container {
        position: relative;
    }
    
    .auth-input-group {
        position: relative;
        margin-bottom: 2rem;
    }
    
    .auth-input-label {
        display: block;
        margin-bottom: 0.8rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.5px;
    }
    
    .auth-input-wrapper {
        position: relative;
        overflow: hidden;
        border-radius: 16px;
    }
    
    .auth-input-wrapper::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, 
            rgba(59, 130, 246, 0.3) 0%,
            rgba(139, 92, 246, 0.3) 50%,
            rgba(236, 72, 153, 0.3) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
        border-radius: 16px;
    }
    
    .auth-input-wrapper:focus-within::before {
        opacity: 1;
    }
    
    /* Enhanced input field styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.08)) !important;
        backdrop-filter: blur(15px) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        color: white !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
        padding: 1.2rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 8px 25px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #3b82f6 !important;
        box-shadow: 
            0 0 0 4px rgba(59, 130, 246, 0.3),
            0 12px 35px rgba(59, 130, 246, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px) !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.12)) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
        font-style: italic !important;
    }
    
    /* Enhanced button styling */
    .auth-button-container {
        margin-top: 3rem;
        position: relative;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899) !important;
        border: none !important;
        border-radius: 18px !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        padding: 1.2rem 3rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 15px 35px rgba(59, 130, 246, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        position: relative !important;
        overflow: hidden !important;
        width: 100% !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3), 
            transparent);
        transition: left 0.6s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px) !important;
        box-shadow: 
            0 25px 50px rgba(59, 130, 246, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        background: linear-gradient(135deg, #2563eb, #7c3aed, #db2777) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-2px) !important;
        box-shadow: 
            0 15px 30px rgba(59, 130, 246, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Form messages styling */
    .auth-form-message {
        padding: 1.2rem 1.8rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .auth-form-message.success {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(59, 130, 246, 0.2));
        border-color: rgba(34, 197, 94, 0.4);
        color: #10b981;
        box-shadow: 0 8px 25px rgba(34, 197, 94, 0.2);
    }
    
    .auth-form-message.error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(245, 101, 101, 0.2));
        border-color: rgba(239, 68, 68, 0.4);
        color: #ef4444;
        box-shadow: 0 8px 25px rgba(239, 68, 68, 0.2);
    }
    
    /* Loading animation */
    .auth-loading {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin: 2rem 0;
    }
    
    .auth-loading-spinner {
        width: 24px;
        height: 24px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-top: 3px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Floating particles effect */
    .auth-particles {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
        overflow: hidden;
        border-radius: 28px;
    }
    
    .auth-particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border-radius: 50%;
        animation: float 6s infinite ease-in-out;
        opacity: 0.6;
    }
    
    .auth-particle:nth-child(1) { left: 10%; animation-delay: 0s; }
    .auth-particle:nth-child(2) { left: 20%; animation-delay: 1s; }
    .auth-particle:nth-child(3) { left: 30%; animation-delay: 2s; }
    .auth-particle:nth-child(4) { left: 40%; animation-delay: 3s; }
    .auth-particle:nth-child(5) { left: 50%; animation-delay: 4s; }
    .auth-particle:nth-child(6) { left: 60%; animation-delay: 5s; }
    
    @keyframes float {
        0%, 100% { 
            transform: translateY(100vh) scale(0);
            opacity: 0;
        }
        10% {
            opacity: 0.6;
            transform: scale(1);
        }
        90% {
            opacity: 0.6;
            transform: scale(1);
        }
        100% {
            transform: translateY(-100px) scale(0);
            opacity: 0;
        }
    }
    
    /* Password strength indicator */
    .password-strength {
        margin-top: 0.8rem;
        padding: 0.8rem 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .password-strength-bar {
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }
    
    .password-strength-fill {
        height: 100%;
        transition: all 0.3s ease;
        border-radius: 2px;
    }
    
    .strength-weak .password-strength-fill {
        width: 33%;
        background: linear-gradient(90deg, #ef4444, #f97316);
    }
    
    .strength-medium .password-strength-fill {
        width: 66%;
        background: linear-gradient(90deg, #f59e0b, #eab308);
    }
    
    .strength-strong .password-strength-fill {
        width: 100%;
        background: linear-gradient(90deg, #10b981, #059669);
    }
    
    /* Social login placeholder (for future enhancement) */
    .social-login-divider {
        position: relative;
        text-align: center;
        margin: 2.5rem 0;
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.9rem;
    }
    
    .social-login-divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3), 
            transparent);
    }
    
    .social-login-divider span {
        background: rgba(0, 0, 0, 0.5);
        padding: 0 1.5rem;
        backdrop-filter: blur(10px);
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = None

def create_download_link(df, filename):
    """Create a download link for the DataFrame"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Scraped_Data')
    
    excel_data = output.getvalue()
    return excel_data

def create_jobs_excel_download(jobs_data, filename, job_query="", job_location=""):
    """Create a properly formatted Excel file for JSearch job data with organized columns"""
    if not jobs_data:
        return None
    
    # Convert to DataFrame
    jobs_df = pd.DataFrame(jobs_data)
    
    # Define the column mapping and order for clean Excel export
    excel_columns = {
        # Basic Job Information
        'Job Title': 'job_title',
        'Company': 'employer_name', 
        'Company Logo': 'employer_logo',
        'Employment Type': 'job_employment_type',
        'Job Category': 'job_category',
        
        # Location Information
        'Location (City)': 'job_city',
        'Location (State)': 'job_state', 
        'Location (Country)': 'job_country',
        'Is Remote': 'job_is_remote',
        
        # Salary Information
        'Min Salary (USD)': 'job_salary_min',
        'Max Salary (USD)': 'job_salary_max',
        'Salary Period': 'job_salary_period',
        'Salary Currency': 'job_salary_currency',
        
        # Job Details
        'Job Description': 'job_description',
        'Experience Required': 'job_required_experience',
        'Education Required': 'job_required_education',
        'Skills Required': 'job_required_skills',
        
        # Application Information
        'Apply Link': 'job_apply_link',
        'Application Deadline': 'job_offer_expiration_datetime_utc',
        'Posted Date': 'job_posted_at_datetime_utc',
        'Posted Date (Human)': 'job_posted_at_human',
        
        # Company Information
        'Company Website': 'employer_website',
        'Company Type': 'employer_company_type',
        'Company Reviews': 'employer_reviews',
        
        # Additional Information
        'Job ID': 'job_id',
        'Job Publisher': 'job_publisher',
        'Job Benefits': 'job_benefits',
        'Job Highlights': 'job_highlights'
    }
    
    # Create organized DataFrame with proper column names
    organized_data = {}
    
    for excel_col, api_col in excel_columns.items():
        if api_col in jobs_df.columns:
            # Clean and format the data
            column_data = jobs_df[api_col].copy()
            
            # Special formatting for specific columns
            if api_col == 'job_is_remote':
                column_data = column_data.map({True: 'Yes', False: 'No', None: 'Unknown'})
            elif api_col in ['job_salary_min', 'job_salary_max']:
                column_data = column_data.fillna('Not specified')
            elif api_col == 'job_description':
                # Limit description length for Excel readability
                column_data = column_data.astype(str).apply(lambda x: x[:500] + '...' if len(str(x)) > 500 else x)
            elif api_col in ['job_posted_at_datetime_utc', 'job_offer_expiration_datetime_utc']:
                # Format dates properly
                column_data = pd.to_datetime(column_data, errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
            elif api_col in ['job_benefits', 'job_highlights', 'job_required_skills']:
                # Handle lists/arrays
                column_data = column_data.apply(lambda x: '; '.join(x) if isinstance(x, list) else str(x) if x else '')
            
            organized_data[excel_col] = column_data
        else:
            # Add empty column if data not available
            organized_data[excel_col] = [''] * len(jobs_df)
    
    # Create final DataFrame
    excel_df = pd.DataFrame(organized_data)
    
    # Add metadata sheet information
    metadata = {
        'Search Query': [job_query],
        'Search Location': [job_location], 
        'Total Jobs Found': [len(jobs_df)],
        'Export Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
        'Data Source': ['JSearch API'],
        'Companies Found': [excel_df['Company'].nunique()],
        'Remote Jobs': [len(excel_df[excel_df['Is Remote'] == 'Yes'])],
        'With Salary Info': [len(excel_df[(excel_df['Min Salary (USD)'] != 'Not specified') | 
                                        (excel_df['Max Salary (USD)'] != 'Not specified')])]
    }
    metadata_df = pd.DataFrame(metadata)
    
    # Create Excel file with multiple sheets
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write main jobs data
        excel_df.to_excel(writer, sheet_name='Jobs_Data', index=False)
        
        # Write metadata
        metadata_df.to_excel(writer, sheet_name='Search_Info', index=False)
        
        # Format the main sheet
        workbook = writer.book
        worksheet = writer.sheets['Jobs_Data']
        
        # Auto-adjust column widths
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
        
        # Add header formatting
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Freeze the header row
        worksheet.freeze_panes = 'A2'
    
    return output.getvalue()

def display_status_card(status_type, message, icon=""):
    """Display a premium status card"""
    st.markdown(f"""
    <div class="status-{status_type}">
        <span style="font-size: 1.2rem;">{icon}</span>
        <span>{message}</span>
    </div>
    """, unsafe_allow_html=True)

def show_authentication_page():
    """Show the premium authentication page with advanced UI/UX"""
    st.markdown("""
    <div class="premium-header floating-card">
        <h1>🤖 AI Contact Scraper Pro</h1>
        <p>Advanced Intelligence • Premium Performance • Enterprise Grade</p>
        <p style="font-size: 1rem; margin-top: 1rem; opacity: 0.8;">🔐 Secure Portal • Personal Data Spaces • Advanced Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the authentication form with enhanced layout
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-glass-card">', unsafe_allow_html=True)
        
        # Add floating particles effect
        st.markdown("""
        <div class="auth-particles">
            <div class="auth-particle"></div>
            <div class="auth-particle"></div>
            <div class="auth-particle"></div>
            <div class="auth-particle"></div>
            <div class="auth-particle"></div>
            <div class="auth-particle"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced authentication tabs
        st.markdown('<div class="auth-tabs-container">', unsafe_allow_html=True)
        
        # Create custom tab selector with premium styling
        tab_col1, tab_col2 = st.columns(2)
        
        # Initialize session state for tab
        if 'auth_tab' not in st.session_state:
            st.session_state.auth_tab = "Login"
        
        with tab_col1:
            if st.button("🔐 Sign In", key="login_tab", use_container_width=True):
                st.session_state.auth_tab = "Login"
        
        with tab_col2:
            if st.button("📝 Create Account", key="signup_tab", use_container_width=True):
                st.session_state.auth_tab = "Sign Up"
        
        # Custom CSS for active tab styling
        if st.session_state.auth_tab == "Login":
            st.markdown("""
            <style>
            div[data-testid="column"]:first-child button {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 15px 35px rgba(59, 130, 246, 0.4) !important;
            }
            </style>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <style>
            div[data-testid="column"]:last-child button {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 15px 35px rgba(59, 130, 246, 0.4) !important;
            }
            </style>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Form container with enhanced styling
        st.markdown('<div class="auth-form-container">', unsafe_allow_html=True)
        
        if st.session_state.auth_tab == "Login":
            # Enhanced Login Form
            st.markdown("""
            <div style="text-align: center; margin: 2rem 0;">
                <h2 style="background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                           background-clip: text; font-size: 2rem; font-weight: 700; margin: 0;">
                    Welcome Back! 👋
                </h2>
                <p style="color: rgba(255, 255, 255, 0.7); margin-top: 0.5rem; font-size: 1.1rem;">
                    Sign in to access your personal workspace
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            auth_manager.show_login_form()
            
        else:
            # Enhanced Signup Form  
            st.markdown("""
            <div style="text-align: center; margin: 2rem 0;">
                <h2 style="background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899); 
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                           background-clip: text; font-size: 2rem; font-weight: 700; margin: 0;">
                    Join the Pro Experience! ✨
                </h2>
                <p style="color: rgba(255, 255, 255, 0.7); margin-top: 0.5rem; font-size: 1.1rem;">
                    Create your account and start scraping with AI power
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            auth_manager.show_signup_form()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced footer with features
        st.markdown("""
        <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid rgba(255, 255, 255, 0.1);">
            <div style="text-align: center; margin-bottom: 2rem;">
                <h3 style="color: rgba(255, 255, 255, 0.9); font-size: 1.2rem; font-weight: 600; margin-bottom: 1.5rem;">
                    🚀 What You Get with AI Scraper Pro
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
                    <div style="text-align: center; padding: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                        <div style="color: rgba(255, 255, 255, 0.8); font-weight: 600;">AI-Powered Extraction</div>
                        <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">Advanced GPT models</div>
                    </div>
                    <div style="text-align: center; padding: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔒</div>
                        <div style="color: rgba(255, 255, 255, 0.8); font-weight: 600;">Personal Data Space</div>
                        <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">Secure & private</div>
                    </div>
                    <div style="text-align: center; padding: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                        <div style="color: rgba(255, 255, 255, 0.8); font-weight: 600;">Advanced Analytics</div>
                        <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">Real-time insights</div>
                    </div>
                    <div style="text-align: center; padding: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                        <div style="color: rgba(255, 255, 255, 0.8); font-weight: 600;">Enhanced Performance</div>
                        <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">Concurrent processing</div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; padding: 1.5rem; background: rgba(255, 255, 255, 0.05); 
                        border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1);">
                <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">
                    🔐 <strong>Enterprise-Grade Security</strong> • 
                    💾 <strong>Personal Data Isolation</strong> • 
                    📈 <strong>Real-Time Analytics</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Check authentication first
    if not auth_manager.check_authentication():
        show_authentication_page()
        return
    
    # Get current user ID for database operations
    current_user_id = auth_manager.get_current_user_id()
    
    # Premium Header
    st.markdown("""
    <div class="premium-header floating-card">
        <h1>🤖 AI Contact Scraper Pro</h1>
        <p>Advanced Intelligence • Premium Performance • Enterprise Grade</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration with premium styling
    with st.sidebar:
        # Show user info
        auth_manager.show_user_info()
        
        st.markdown('<div class="section-header">⚙️ System Configuration</div>', unsafe_allow_html=True)
        
        # API Status checks with premium cards
        serper_key = os.getenv("SERPER_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        if serper_key:
            display_status_card("success", "Serper API Connected", "🟢")
        else:
            display_status_card("error", "Serper API Not Configured", "🔴")
            
        if openrouter_key:
            display_status_card("success", "OpenRouter API Connected", "🟢")
        else:
            display_status_card("error", "OpenRouter API Not Configured", "🔴")
        
        if ENHANCED_SCRAPER_AVAILABLE:
            display_status_card("info", "Enhanced Scraper Active", "⚡")
        
        st.markdown('<div class="section-header">📊 Real-time Analytics</div>', unsafe_allow_html=True)
        stats = db_manager.get_statistics(current_user_id)
        
        # Premium metrics display
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎯 Total Links", stats['total_results'])
            st.metric("📋 Unscraped", stats['unscraped_results'])
            st.metric("✅ Success Rate", f"{(stats['successful_extractions']/max(stats['total_results'], 1)*100):.1f}%")
        
        with col2:
            st.metric("👥 Names Found", stats['names_found'])
            st.metric("📞 Phone Numbers", stats['phones_found'])
            st.metric("📧 Email Addresses", stats['emails_found'])
        
        # Database management with premium styling
        st.markdown('<div class="section-header">🗄️ Data Management</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear My Data", type="secondary", use_container_width=True, key="sidebar_clear_data"):
            db_manager.clear_all_data(current_user_id)
            display_status_card("success", "Your data cleared successfully!", "✨")
            st.rerun()
    
    # Main content tabs with premium styling
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Intelligent Search", "🎯 AI Extraction", "📊 Analytics Center", "💼 JSearch Job Scraper", "🗺️ Google Maps Extractor"])
    
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔍 Web Intelligence Search</div>', unsafe_allow_html=True)
        
        if not serper_api:
            display_status_card("error", "Serper API configuration required. Please add SERPER_API_KEY to your environment.", "⚠️")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Premium search interface
        col1, col2 = st.columns(2, gap="large")
        with col1:
            search_query = st.text_input(
                "🎯 Search Query",
                placeholder="e.g., dental clinics, restaurants, law firms",
                help="Enter the type of businesses you want to discover"
            )
        with col2:
            location = st.text_input(
                "📍 Target Location",
                placeholder="e.g., New York, NY or California, USA",
                help="Specify the geographical area for your search"
            )
        
        col1, col2, col3 = st.columns([1, 1, 2], gap="large")
        with col1:
            num_results = st.number_input(
                "📊 Results Count",
                min_value=1,
                max_value=100,
                value=10,
                help="Number of search results to retrieve"
            )
        
        with col2:
            if st.button("🚀 Launch Search", type="primary", use_container_width=True, key="search_launch_btn"):
                if search_query and location:
                    with st.spinner("🔍 Conducting intelligent search..."):
                        try:
                            results = serper_api.search_local_businesses(
                                business_type=search_query,
                                location=location,
                                num_results=num_results
                            )
                            
                            if results:
                                inserted_count = db_manager.insert_search_results(results, current_user_id)
                                
                                display_status_card("success", f"Discovered {len(results)} results • {inserted_count} new entries added to database", "🎉")
                                st.session_state.search_results = results
                                
                                # Premium results preview
                                st.markdown('<div class="section-header">👀 Search Results Preview</div>', unsafe_allow_html=True)
                                df = pd.DataFrame(results)
                                preview_cols = ['title', 'link', 'snippet', 'rating', 'reviews_count']
                                available_cols = [col for col in preview_cols if col in df.columns]
                                st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
                            else:
                                display_status_card("warning", "No results found for your search criteria. Try different keywords or location.", "🔍")
                                
                        except Exception as e:
                            display_status_card("error", f"Search error: {str(e)}", "❌")
                else:
                    display_status_card("warning", "Please provide both search query and location to proceed.", "⚠️")
        
        # Recent database entries with premium styling
        st.markdown('<div class="section-header">📋 Recent Database Entries</div>', unsafe_allow_html=True)
        recent_results = db_manager.get_all_search_results(current_user_id).head(20)
        if not recent_results.empty:
            display_cols = ['title', 'link', 'original_query', 'original_location', 'scraped']
            available_cols = [col for col in display_cols if col in recent_results.columns]
            st.dataframe(recent_results[available_cols], use_container_width=True, hide_index=True)
        else:
            display_status_card("info", "No search results in database yet. Use the search interface above to get started.", "💡")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🎯 AI-Powered Contact Extraction</div>', unsafe_allow_html=True)
        
        if not openrouter_key:
            display_status_card("error", "OpenRouter API configuration required. Please add OPENROUTER_API_KEY to your environment.", "⚠️")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Get unscraped links count
        unscraped_df = db_manager.get_unscraped_links(current_user_id)
        unscraped_count = len(unscraped_df)
        
        # Premium status display
        col1, col2, col3 = st.columns([2, 2, 1], gap="large")
        with col1:
            st.metric("🎯 Ready for Processing", unscraped_count)
            if unscraped_count > 0:
                display_status_card("info", "AI extraction system ready to process stored links", "🤖")
            else:
                display_status_card("warning", "No unscraped links available. Please conduct a search first.", "⚠️")
        
        with col2:
            if ENHANCED_SCRAPER_AVAILABLE:
                display_status_card("success", "Enhanced AI Engine Active", "⚡")
                st.markdown("**Features:** Retry mechanism • Concurrent processing • Smart error handling")
            else:
                display_status_card("info", "Standard AI Engine Active", "🤖")
        
        with col3:
            if st.button("🚀 Start AI Extraction", type="primary", use_container_width=True, disabled=unscraped_count == 0, key="ai_extraction_btn"):
                # Premium progress interface
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(progress):
                        progress_bar.progress(progress)
                    
                    def update_status(status):
                        status_text.text(f"🤖 {status}")
                    
                    with st.spinner("🧠 AI processing in progress..."):
                        successful_extractions = process_links_from_database(
                            progress_callback=update_progress,
                            status_callback=update_status,
                            user_id=current_user_id
                        )
                        
                        progress_bar.progress(1.0)
                        status_text.text("✅ AI extraction completed successfully!")
                        
                        display_status_card("success", f"Extraction complete! {successful_extractions}/{unscraped_count} contacts successfully processed", "🎉")
                        st.rerun()
        
        # Preview of unscraped links with premium styling
        if not unscraped_df.empty:
            st.markdown('<div class="section-header">📋 Queued for Processing</div>', unsafe_allow_html=True)
            preview_cols = ['title', 'link', 'original_query', 'original_location']
            st.dataframe(unscraped_df[preview_cols].head(10), use_container_width=True, hide_index=True)
            
            if len(unscraped_df) > 10:
                display_status_card("info", f"Displaying 10 of {len(unscraped_df)} pending links", "📊")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 Advanced Analytics Center</div>', unsafe_allow_html=True)
        
        # Get all results for display
        all_results_df = db_manager.get_all_search_results(current_user_id)
        
        if all_results_df.empty:
            display_status_card("info", "No analytics data available. Please search for businesses and run AI extraction first.", "📊")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Premium download section
        col1, col2, col3 = st.columns([3, 1, 1], gap="large")
        with col1:
            st.markdown('<div class="section-header">💾 Export Center</div>', unsafe_allow_html=True)
        with col2:
            excel_data = create_download_link(all_results_df, "AI_Contact_Scraper_Results.xlsx")
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name="AI_Contact_Scraper_Results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # Premium analytics dashboard
        st.markdown('<div class="section-header">📈 Performance Dashboard</div>', unsafe_allow_html=True)
        
        # Key metrics with premium styling
        col1, col2, col3, col4 = st.columns(4, gap="large")
        
        total_records = len(all_results_df)
        scraped_records = len(all_results_df[all_results_df['scraped_names'].notna() | 
                                          all_results_df['scraped_phones'].notna() | 
                                          all_results_df['scraped_emails'].notna()])
        success_count = len(all_results_df[all_results_df['scraping_status'] == 'Success'])
        phone_count = len(all_results_df[all_results_df['scraped_phones'].notna()])
        email_count = len(all_results_df[all_results_df['scraped_emails'].notna()])
        
        with col1:
            st.metric("📊 Total Records", total_records)
        with col2:
            success_rate = (success_count / total_records) * 100 if total_records > 0 else 0
            st.metric("✅ Success Rate", f"{success_rate:.1f}%")
        with col3:
            phone_rate = (phone_count / total_records) * 100 if total_records > 0 else 0
            st.metric("📞 Phone Found", f"{phone_rate:.1f}%")
        with col4:
            email_rate = (email_count / total_records) * 100 if total_records > 0 else 0
            st.metric("📧 Email Found", f"{email_rate:.1f}%")
        
        # Premium charts
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            # Enhanced status distribution chart
            status_counts = all_results_df['scraping_status'].fillna('Not Processed').value_counts()
            fig1 = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="🎯 Processing Status Distribution",
                color_discrete_sequence=['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#ef4444']
            )
            fig1.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_size=16,
                title_font_color='white'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Enhanced contact extraction chart
            contact_data = {
                'Phone Numbers': phone_count,
                'Email Addresses': email_count,
                'Both Phone & Email': len(all_results_df[all_results_df['scraped_phones'].notna() & 
                                                      all_results_df['scraped_emails'].notna()]),
                'No Contacts': len(all_results_df[all_results_df['scraped_phones'].isna() & 
                                                all_results_df['scraped_emails'].isna()])
            }
            
            fig2 = px.bar(
                x=list(contact_data.keys()),
                y=list(contact_data.values()),
                title="📊 Contact Information Extracted",
                color=list(contact_data.keys()),
                color_discrete_sequence=['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b']
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_font_size=16,
                title_font_color='white',
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Premium filter interface
        st.markdown('<div class="section-header">🔍 Advanced Filtering</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            status_filter = st.selectbox(
                "📊 Filter by Status",
                ["All", "Success", "Error", "Not Processed"],
                help="Filter results by processing status"
            )
        with col2:
            contact_filter = st.selectbox(
                "📱 Filter by Contact Type",
                ["All", "Has Phone", "Has Email", "Has Both", "Has Neither"]
            )
        with col3:
            query_filter = st.selectbox(
                "🔍 Filter by Query",
                ["All"] + list(all_results_df['original_query'].dropna().unique()),
                help="Filter by original search query"
            )
        
        # Apply filters
        filtered_df = all_results_df.copy()
        
        if status_filter != "All":
            if status_filter == "Success":
                filtered_df = filtered_df[filtered_df['scraping_status'] == 'Success']
            elif status_filter == "Error":
                filtered_df = filtered_df[filtered_df['scraping_status'].str.contains('Error', na=False)]
            elif status_filter == "Not Processed":
                filtered_df = filtered_df[filtered_df['scraping_status'].isna()]
        
        if contact_filter != "All":
            if contact_filter == "Has Phone":
                filtered_df = filtered_df[filtered_df['scraped_phones'].notna()]
            elif contact_filter == "Has Email":
                filtered_df = filtered_df[filtered_df['scraped_emails'].notna()]
            elif contact_filter == "Has Both":
                filtered_df = filtered_df[filtered_df['scraped_phones'].notna() & filtered_df['scraped_emails'].notna()]
            elif contact_filter == "Has Neither":
                filtered_df = filtered_df[filtered_df['scraped_phones'].isna() & filtered_df['scraped_emails'].isna()]
        
        if query_filter != "All":
            filtered_df = filtered_df[filtered_df['original_query'] == query_filter]
        
        # Display filtered results with premium styling
        st.markdown(f'<div class="section-header">📋 Filtered Results ({len(filtered_df)} of {len(all_results_df)} records)</div>', unsafe_allow_html=True)
        
        # Key columns display
        display_columns = ['title', 'link', 'scraped_names', 'scraped_phones', 'scraped_emails', 'scraping_status', 'original_query']
        available_display_columns = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed view expander with premium styling
        with st.expander("🔍 Complete Data View"):
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">💼 JSearch Job Scraper</div>', unsafe_allow_html=True)
        
        # Initialize session state for job scraper results
        if 'job_scraper_results' not in st.session_state:
            st.session_state.job_scraper_results = None
        if 'job_scraper_running' not in st.session_state:
            st.session_state.job_scraper_running = False
        
        # Check if RapidAPI token is available
        rapidapi_key = os.getenv("RAPIDAPI_KEY")
        if not rapidapi_key:
            display_status_card("error", "RapidAPI key configuration required. Please add RAPIDAPI_KEY to your environment.", "⚠️")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Premium job scraper interface
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1)); 
                    border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 16px; padding: 2rem; margin: 1rem 0;">
            <h3 style="color: #3b82f6; margin: 0 0 1rem 0;">🚀 Advanced Job Search with JSearch API</h3>
            <p style="color: rgba(255, 255, 255, 0.8); margin: 0;">
                Search millions of jobs from multiple platforms including LinkedIn, Indeed, Glassdoor, and more. 
                Get real job data with salaries, company details, and apply links - no more N/A values!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize JSearch scraper
        try:
            job_scraper = JSearchJobScraper(rapidapi_key)
            display_status_card("success", "JSearch API connected successfully • Access to millions of jobs", "✅")
        except Exception as e:
            display_status_card("error", f"Failed to initialize JSearch scraper: {str(e)}", "❌")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Job search parameters
        st.markdown('<div class="section-header">🎯 Search Parameters</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            # Template selector
            template_options = ["Custom Search"] + list(JOB_TEMPLATES.keys())
            selected_template = st.selectbox(
                "📋 Search Template",
                template_options,
                help="Use predefined templates or create custom search"
            )
            
            if selected_template != "Custom Search":
                template = JOB_TEMPLATES[selected_template]
                st.info(f"Template: {selected_template}")
                for key, value in template.items():
                    if key == "platform" and value:
                        st.text(f"🎯 Platform: {value.title()}")
                    elif key != "platform":
                        st.text(f"{key}: {value}")
        
        with col2:
            job_query = st.text_input(
                "💼 Job Title/Keywords",
                value="software engineer" if selected_template == "Custom Search" else "",
                placeholder="e.g., Python Developer, Data Scientist, Marketing Manager",
                help="Enter the job title or keywords to search for"
            )
        
        with col3:
            job_location = st.text_input(
                "📍 Location",
                value="United States" if selected_template == "Custom Search" else "",
                placeholder="e.g., San Francisco, CA or Remote",
                help="Specify the job location or 'Remote' for remote jobs"
            )
        
        # Platform selection row
        st.markdown('<div class="section-header">🌐 Platform Selection</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            # Platform selector
            available_platforms = job_scraper.get_available_platforms()
            platform_options = ["All Platforms"] + [platform.title() for platform in available_platforms]
            
            selected_platform = st.selectbox(
                "🎯 Target Platform",
                platform_options,
                help="Choose specific job platform or search all platforms"
            )
            
            # Convert back to lowercase for API
            if selected_platform == "All Platforms":
                target_platform = None
            else:
                target_platform = selected_platform.lower()
        
        with col2:
            # Platform info
            if target_platform:
                st.info(f"🎯 Searching on {selected_platform} only")
                st.markdown(f"""
                **Query will be:** `{job_query} in {job_location} via {target_platform}`
                """)
            else:
                st.info("🌐 Searching across all job platforms")
                st.markdown(f"""
                **Query will be:** `{job_query} in {job_location}`
                """)
        
        with col3:
            # Platform statistics (placeholder)
            if target_platform:
                platform_stats = {
                    "linkedin": "📊 Best for tech jobs",
                    "indeed": "📊 Largest job database", 
                    "glassdoor": "💰 Best for salary data",
                    "ziprecruiter": "⚡ Fast applications",
                    "monster": "🎯 Diverse industries",
                    "dice": "💻 Tech specialization"
                }
                if target_platform in platform_stats:
                    st.success(platform_stats[target_platform])
        
        # Advanced options
        with st.expander("🔧 Advanced Search Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                num_pages = st.number_input(
                    "📄 Number of Pages",
                    min_value=1,
                    max_value=20,
                    value=2,
                    help="Each page contains ~10 jobs. Max 20 pages per search."
                )
                
                date_posted = st.selectbox(
                    "📅 Date Posted",
                    options=["all", "today", "3days", "week", "month"],
                    index=3,
                    help="Filter jobs by posting date"
                )
                
                country = st.selectbox(
                    "🌍 Country",
                    options=["us", "uk", "ca", "au", "de", "fr", "in", "sg", "ae"],
                    index=0,
                    help="Select target country"
                )
            
            with col2:
                employment_types = st.multiselect(
                    "💼 Employment Types",
                    options=["FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"],
                    default=["FULLTIME", "PARTTIME"],
                    help="Select employment types"
                )
                
                job_requirements = st.multiselect(
                    "🎓 Experience Level",
                    options=["under_3_years_experience", "more_than_3_years_experience", "no_experience", "no_degree"],
                    default=["under_3_years_experience", "more_than_3_years_experience"],
                    help="Filter by experience requirements"
                )
                
                remote_only = st.checkbox(
                    "🏠 Remote Jobs Only",
                    value=False,
                    help="Only return remote job opportunities"
                )
                
                save_to_db = st.checkbox(
                    "💾 Save to Database",
                    value=True,
                    help="Store results in your personal database"
                )
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1], gap="large")
        
        with col1:
            if st.button("🚀 Search Jobs", type="primary", use_container_width=True, 
                        disabled=st.session_state.job_scraper_running, key="job_search_btn"):
                if not job_query.strip():
                    display_status_card("warning", "Please enter a job title or keywords", "⚠️")
                elif not job_location.strip():
                    display_status_card("warning", "Please enter a location", "⚠️")
                else:
                    st.session_state.job_scraper_running = True
                    
                    # Progress tracking
                    progress_container = st.container()
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("🚀 Initializing JSearch API...")
                        progress_bar.progress(0.1)
                        
                        try:
                            # Prepare search parameters
                            if selected_template != "Custom Search":
                                template_config = JOB_TEMPLATES[selected_template]
                                search_params = {
                                    "query": template_config.get("queries", [job_query])[0] if isinstance(template_config.get("queries"), list) else job_query,
                                    "location": template_config.get("location", job_location),
                                    "employment_types": template_config.get("employment_types", ",".join(employment_types)),
                                    "remote_jobs_only": template_config.get("remote_jobs_only", remote_only),
                                    "job_requirements": template_config.get("job_requirements", ",".join(job_requirements)),
                                    "platform": template_config.get("platform", target_platform),
                                    "num_pages": num_pages,
                                    "date_posted": date_posted,
                                    "country": country
                                }
                            else:
                                search_params = {
                                    "query": job_query,
                                    "location": job_location,
                                    "employment_types": ",".join(employment_types),
                                    "job_requirements": ",".join(job_requirements),
                                    "remote_jobs_only": remote_only,
                                    "platform": target_platform,
                                    "num_pages": num_pages,
                                    "date_posted": date_posted,
                                    "country": country
                                }
                            
                            with st.spinner("🔍 Searching jobs across multiple platforms..."):
                                status_text.text("📡 Connecting to job search engines...")
                                progress_bar.progress(0.3)
                                
                                # Search jobs using JSearch API
                                results = job_scraper.search_jobs(**search_params)
                                progress_bar.progress(0.8)
                                
                                if "data" in results and results["data"]:
                                    jobs = results["data"]
                                    st.session_state.job_scraper_results = jobs
                                    
                                    # Debug information
                                    st.write("🔍 **Debug Info:**")
                                    st.write(f"- Found {len(jobs)} jobs")
                                    if jobs:
                                        first_job = jobs[0]
                                        st.write(f"- First job fields: {list(first_job.keys())}")
                                        
                                        # Show sample of actual values
                                        sample_data = {}
                                        for key, value in first_job.items():
                                            if value and str(value).lower() not in ['none', 'null', '']:
                                                sample_data[key] = str(value)[:100] + ('...' if len(str(value)) > 100 else '')
                                        if sample_data:
                                            st.write("- Sample data:")
                                            st.json(sample_data)
                                    
                                    # Save to database if requested
                                    if save_to_db:
                                        status_text.text("💾 Saving results to database...")
                                        
                                        # Convert job results to format compatible with existing database
                                        job_data_for_db = []
                                        for job in jobs:
                                            job_entry = {
                                                'title': job.get('job_title', 'N/A'),
                                                'link': job.get('job_apply_link', job.get('job_offer_expiration_datetime_utc', '')),
                                                'snippet': (job.get('job_description', '') or '')[:500] + '...' if job.get('job_description') else '',
                                                'original_query': f"JSearch: {job_query}",
                                                'original_location': job_location,
                                                'source': 'JSearch API',
                                                'scraped_names': job.get('employer_name', ''),
                                                'scraped_phones': '',  # JSearch doesn't provide phone numbers
                                                'scraped_emails': '',  # JSearch doesn't provide email addresses
                                                'scraping_status': 'Job Found',
                                                'additional_data': json.dumps(job)
                                            }
                                            job_data_for_db.append(job_entry)
                                        
                                        # Insert into database
                                        inserted_count = db_manager.insert_search_results(job_data_for_db, current_user_id)
                                        
                                    progress_bar.progress(1.0)
                                    status_text.text(f"✅ Successfully found {len(jobs)} jobs!")
                                    
                                    display_status_card("success", 
                                        f"🎉 Job search completed! Found {len(jobs)} jobs" + 
                                        (f" • {inserted_count} saved to database" if save_to_db else ""), "🚀")
                                    
                                elif "error" in results:
                                    display_status_card("error", f"API Error: {results['error']}", "❌")
                                else:
                                    display_status_card("warning", "No jobs found for your search criteria. Try different keywords or location.", "🔍")
                                
                        except Exception as e:
                            display_status_card("error", f"Search error: {str(e)}", "❌")
                        
                        finally:
                            st.session_state.job_scraper_running = False
                            st.rerun()
        
        with col2:
            if st.session_state.job_scraper_results:
                # Create Excel download with enhanced formatting
                excel_data = create_jobs_excel_download(
                    st.session_state.job_scraper_results, 
                    f"JSearch_Jobs_{job_query.replace(' ', '_')}.xlsx", 
                    job_query, 
                    job_location
                )
                
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"JSearch_Jobs_{job_query.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Download professionally formatted Excel with organized columns and metadata"
                )
        
        with col3:
            if st.session_state.job_scraper_results:
                if st.button("🔄 Clear Results", use_container_width=True, key="job_clear_results_btn"):
                    st.session_state.job_scraper_results = None
                    st.rerun()
        
        # Display results
        if st.session_state.job_scraper_results:
            st.markdown('<div class="section-header">📋 Job Search Results</div>', unsafe_allow_html=True)
            
            jobs_df = pd.DataFrame(st.session_state.job_scraper_results)
            
            # Excel Format Info
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(59, 130, 246, 0.1)); 
                        border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                <h4 style="color: #22c55e; margin: 0 0 0.5rem 0;">📊 Excel Export Features</h4>
                <p style="color: rgba(255, 255, 255, 0.8); margin: 0;">
                    <strong>✅ Professional formatting</strong> with organized columns<br>
                    <strong>✅ Two sheets:</strong> Jobs_Data + Search_Info metadata<br>
                    <strong>✅ Clean column names:</strong> Job Title, Company, Salary, Location, etc.<br>
                    <strong>✅ Auto-sized columns</strong> and formatted headers
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Results summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Jobs", len(jobs_df))
            with col2:
                unique_companies = len(jobs_df['employer_name'].dropna().unique()) if 'employer_name' in jobs_df.columns else 0
                st.metric("🏢 Companies", unique_companies)
            with col3:
                with_salary = len(jobs_df[(jobs_df.get('job_salary_max', pd.Series()).notna()) | 
                                        (jobs_df.get('job_salary_min', pd.Series()).notna())]) if any(col in jobs_df.columns for col in ['job_salary_max', 'job_salary_min']) else 0
                st.metric("💰 With Salary", with_salary)
            with col4:
                remote_jobs = len(jobs_df[jobs_df.get('job_is_remote', pd.Series()) == True]) if 'job_is_remote' in jobs_df.columns else 0
                st.metric("🏠 Remote Jobs", remote_jobs)
            
            # Platform breakdown
            if not target_platform:  # If searching all platforms
                st.markdown("### 🌐 Platform Breakdown")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Try to identify platforms from job URLs or other indicators
                    platform_counts = {}
                    for _, job in jobs_df.iterrows():
                        job_url = job.get('job_apply_link', '') or job.get('job_offer_expiration_datetime_utc', '')
                        if 'linkedin' in str(job_url).lower():
                            platform_counts['LinkedIn'] = platform_counts.get('LinkedIn', 0) + 1
                        elif 'indeed' in str(job_url).lower():
                            platform_counts['Indeed'] = platform_counts.get('Indeed', 0) + 1
                        elif 'glassdoor' in str(job_url).lower():
                            platform_counts['Glassdoor'] = platform_counts.get('Glassdoor', 0) + 1
                        else:
                            platform_counts['Other'] = platform_counts.get('Other', 0) + 1
                    
                    if platform_counts:
                        for platform, count in platform_counts.items():
                            st.metric(f"🎯 {platform}", count)
                
                with col2:
                    if len(platform_counts) > 1:
                        st.info("📊 Jobs found across multiple platforms - great diversity!")
                    else:
                        st.info("🎯 Jobs concentrated on one main platform")
            else:
                st.info(f"🎯 All results from {selected_platform}")
            
            # Display table with key columns
            display_columns = []
            
            # JSearch API field mapping
            column_mappings = {
                'title': ['job_title'],
                'company': ['employer_name'],
                'location': ['job_city', 'job_state', 'job_country'],
                'salary': ['job_salary_min', 'job_salary_max'],
                'posted': ['job_posted_at_datetime_utc'],
                'type': ['job_employment_type'],
                'remote': ['job_is_remote'],
                'link': ['job_apply_link']
            }
            
            # Find the best available columns
            for col_type, possible_names in column_mappings.items():
                for col_name in possible_names:
                    if col_name in jobs_df.columns:
                        display_columns.append(col_name)
                        break
            
            if display_columns:
                # Show main table
                st.dataframe(
                    jobs_df[display_columns[:6]],  # Show first 6 relevant columns
                    use_container_width=True,
                    hide_index=True
                )
            else:
                # Fallback
                available_cols = jobs_df.columns.tolist()[:6]
                st.dataframe(jobs_df[available_cols], use_container_width=True, hide_index=True)
            
            # Detailed view
            with st.expander("🔍 Complete Job Data"):
                st.dataframe(jobs_df, use_container_width=True, hide_index=True)
            
            # Excel Preview
            with st.expander("📊 Excel Export Preview - Column Structure"):
                excel_columns_info = {
                    'Section': ['Basic Info', 'Basic Info', 'Basic Info', 'Basic Info', 'Location', 'Location', 'Location', 'Location', 
                               'Salary', 'Salary', 'Salary', 'Application', 'Application', 'Application', 'Company', 'Company'],
                    'Excel Column Name': ['Job Title', 'Company', 'Employment Type', 'Job Category', 'Location (City)', 'Location (State)', 
                                         'Location (Country)', 'Is Remote', 'Min Salary (USD)', 'Max Salary (USD)', 'Salary Period', 
                                         'Apply Link', 'Posted Date', 'Application Deadline', 'Company Website', 'Company Type'],
                    'Description': ['Job position title', 'Employer company name', 'Full-time/Part-time/Contract', 'Job category/industry',
                                   'City where job is located', 'State/province location', 'Country location', 'Remote work availability',
                                   'Minimum salary range', 'Maximum salary range', 'Annual/Monthly/Hourly', 'Direct application URL',
                                   'When job was posted', 'Application deadline', 'Company official website', 'Company size/type']
                }
                excel_preview_df = pd.DataFrame(excel_columns_info)
                st.dataframe(excel_preview_df, use_container_width=True, hide_index=True)
                
                st.info(f"""
                **📋 Your Excel file will contain:**
                - **Jobs_Data sheet**: {len(jobs_df)} jobs with {len(excel_columns_info['Excel Column Name'])}+ organized columns
                - **Search_Info sheet**: Search metadata (query: "{job_query}", location: "{job_location}")
                - **Professional formatting**: Headers, auto-sized columns, frozen header row
                """)
            
            # JSON view for debugging (separate expander, not nested)
            with st.expander("🔧 Raw JSON Data (for debugging)"):
                st.json(st.session_state.job_scraper_results[:3])  # Show first 3 jobs
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🗺️ Google Maps Business Extractor</div>', unsafe_allow_html=True)
        
        # Initialize session state for Google Maps results
        if 'google_maps_results' not in st.session_state:
            st.session_state.google_maps_results = None
        if 'google_maps_running' not in st.session_state:
            st.session_state.google_maps_running = False
        if 'google_maps_extractor' not in st.session_state:
            st.session_state.google_maps_extractor = None
        if 'apify_key_status' not in st.session_state:
            st.session_state.apify_key_status = None
        
        # API Key Configuration Section
        st.markdown('<div class="section-header">🔑 API Configuration</div>', unsafe_allow_html=True)
        
        # Check if Apify API key is available
        apify_key = os.getenv("APIFY_KEY")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
        if not apify_key:
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(251, 191, 36, 0.1)); 
                            border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 1.5rem; margin: 1rem 0;">
                    <h4 style="color: #f59e0b; margin: 0 0 1rem 0;">⚠️ Apify API Key Required</h4>
                    <p style="color: rgba(255, 255, 255, 0.8); margin: 0;">
                        To use Google Maps business extraction, you need an Apify API key.<br>
                        <strong>Steps:</strong><br>
                        1. Go to <a href="https://console.apify.com/account/integrations" target="_blank" style="color: #3b82f6;">Apify Console</a><br>
                        2. Sign up for a free account (includes free credits)<br>
                        3. Copy your API key<br>
                        4. Add it to your environment variables as APIFY_KEY
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Manual API key input
                manual_key = st.text_input(
                    "🔑 Or Enter API Key Manually",
                    type="password",
                    placeholder="apify_api_xxxxxxxxxxxxxxxxxxxxxxx",
                    help="Enter your Apify API key for this session"
                )
                
                if manual_key:
                    apify_key = manual_key
            else:
                display_status_card("success", f"Apify API key loaded from environment • {apify_key[:15]}...", "✅")
        
        with col2:
            if apify_key:
                if st.button("🧪 Test API Key", use_container_width=True, key="gmaps_test_api_btn"):
                    with st.spinner("Testing API key..."):
                        from google_maps_extractor import GoogleMapsExtractor
                        is_valid, message = GoogleMapsExtractor.test_api_key(apify_key)
                        
                        if is_valid:
                            display_status_card("success", f"API key is valid! {message}", "✅")
                            st.session_state.apify_key_status = "valid"
                        else:
                            display_status_card("error", f"API key test failed: {message}", "❌")
                            st.session_state.apify_key_status = "invalid"
            
            # Reset extractor button
            if st.session_state.google_maps_extractor is not None:
                if st.button("🔄 Reset Extractor", use_container_width=True, help="Clear current extractor instance", key="gmaps_reset_extractor_btn"):
                    st.session_state.google_maps_extractor = None
                    st.session_state.apify_key_status = None
                    st.rerun()
        
        # Only proceed if we have an API key
        if not apify_key:
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Premium Google Maps extractor interface
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(59, 130, 246, 0.1)); 
                    border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 16px; padding: 2rem; margin: 1rem 0;">
            <h3 style="color: #22c55e; margin: 0 0 1rem 0;">🗺️ Extract Business Contact Data from Google Maps</h3>
            <p style="color: rgba(255, 255, 255, 0.8); margin: 0;">
                Extract comprehensive business information including phone numbers, addresses, websites, and more from Google Maps.
                Perfect for getting contact details from job posting companies!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize Google Maps extractor with better error handling
        try:
            if st.session_state.google_maps_extractor is None:
                with st.spinner("Initializing Google Maps extractor..."):
                    st.session_state.google_maps_extractor = GoogleMapsExtractor(apify_key)
            display_status_card("success", "Google Maps extractor ready • Access to comprehensive business data", "✅")
            google_extractor = st.session_state.google_maps_extractor
        except Exception as e:
            error_message = str(e)
            if "authentication" in error_message.lower() or "invalid api key" in error_message.lower():
                display_status_card("error", 
                    f"Authentication failed: {error_message}", "❌")
                st.markdown("""
                <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); 
                            border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                    <p style="color: #ef4444; margin: 0;">
                        <strong>🔧 Troubleshooting Steps:</strong><br>
                        1. Check your API key format (should start with 'apify_api_')<br>
                        2. Verify your account has sufficient credits<br>
                        3. Ensure your account can access the Google Maps scraper<br>
                        4. Try generating a new API key
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                display_status_card("error", f"Failed to initialize extractor: {error_message}", "❌")
            
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Business extraction parameters
        st.markdown('<div class="section-header">🏢 Business Search Parameters</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            # Company input methods
            input_method = st.radio(
                "📥 Input Method",
                ["Manual Entry", "From Job Results", "Upload List"],
                help="Choose how to provide company names"
            )
        
        with col2:
            location = st.text_input(
                "📍 Search Location",
                value="United States",
                placeholder="e.g., New York, NY or California, USA",
                help="Geographic area to search for businesses"
            )
        
        with col3:
            save_to_db = st.checkbox(
                "💾 Save to Database",
                value=True,
                help="Store extracted business data in your personal database"
            )
        
        # Company names input
        companies_to_search = []
        
        if input_method == "Manual Entry":
            st.markdown("### 📝 Enter Company Names")
            company_text = st.text_area(
                "Company Names (one per line)",
                placeholder="Inspira Health Network\nTesla\nStarbucks\nMicrosoft",
                help="Enter each company name on a separate line",
                height=150
            )
            if company_text.strip():
                companies_to_search = [line.strip() for line in company_text.split('\n') if line.strip()]
        
        elif input_method == "From Job Results":
            st.markdown("### 💼 Extract from Job Search Results")
            
            # Get unique company names from job results if available
            if 'job_scraper_results' in st.session_state and st.session_state.job_scraper_results:
                jobs_df = pd.DataFrame(st.session_state.job_scraper_results)
                if 'employer_name' in jobs_df.columns:
                    unique_companies = jobs_df['employer_name'].dropna().unique().tolist()
                    
                    if unique_companies:
                        st.info(f"📊 Found {len(unique_companies)} unique companies from job search results")
                        
                        # Allow user to select companies
                        selected_companies = st.multiselect(
                            "Select Companies to Extract",
                            unique_companies,
                            default=unique_companies[:10],  # Pre-select first 10
                            help="Choose which companies to extract business data for"
                        )
                        companies_to_search = selected_companies
                    else:
                        st.warning("No company names found in job search results")
                else:
                    st.warning("No employer information available in job search results")
            else:
                st.warning("No job search results available. Run a job search first in the JSearch tab.")
        
        elif input_method == "Upload List":
            st.markdown("### 📄 Upload Company List")
            uploaded_file = st.file_uploader(
                "Upload CSV/TXT file",
                type=['csv', 'txt'],
                help="Upload a file with company names"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                        if 'company' in df.columns:
                            companies_to_search = df['company'].dropna().tolist()
                        elif 'name' in df.columns:
                            companies_to_search = df['name'].dropna().tolist()
                        else:
                            companies_to_search = df.iloc[:, 0].dropna().tolist()
                    else:
                        content = uploaded_file.read().decode('utf-8')
                        companies_to_search = [line.strip() for line in content.split('\n') if line.strip()]
                    
                    st.success(f"📄 Loaded {len(companies_to_search)} companies from file")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        # Display companies to be processed
        if companies_to_search:
            st.markdown(f"### 🎯 Companies to Process ({len(companies_to_search)})")
            
            with st.expander("📋 Company List Preview"):
                for i, company in enumerate(companies_to_search[:20], 1):
                    st.text(f"{i}. {company}")
                if len(companies_to_search) > 20:
                    st.text(f"... and {len(companies_to_search) - 20} more")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1], gap="large")
        
        with col1:
            if st.button("🚀 Extract Business Data", type="primary", use_container_width=True, 
                        disabled=st.session_state.google_maps_running or not companies_to_search, key="gmaps_extract_btn"):
                if not companies_to_search:
                    display_status_card("warning", "Please provide company names to extract", "⚠️")
                else:
                    st.session_state.google_maps_running = True
                    
                    # Progress tracking
                    progress_container = st.container()
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            def progress_update(progress):
                                progress_bar.progress(progress)
                            
                            def status_update(status):
                                status_text.text(f"🗺️ {status}")
                            
                            with st.spinner("🗺️ Extracting business data from Google Maps..."):
                                results = google_extractor.extract_business_data(
                                    business_names=companies_to_search,
                                    location=location,
                                    progress_callback=progress_update,
                                    status_callback=status_update
                                )
                                
                                progress_bar.progress(1.0)
                                status_text.text("✅ Business data extraction completed!")
                                
                                if results:
                                    st.session_state.google_maps_results = results
                                    
                                    # Save to database if requested
                                    if save_to_db:
                                        inserted_count = db_manager.insert_google_maps_businesses(results, current_user_id)
                                        display_status_card("success", 
                                            f"🎉 Extraction complete! Found {len(results)} business locations" + 
                                            f" • {inserted_count} saved to database", "🚀")
                                    else:
                                        display_status_card("success", 
                                            f"🎉 Extraction complete! Found {len(results)} business locations", "🚀")
                                else:
                                    display_status_card("warning", "No business data found for the provided companies", "⚠️")
                        
                        except Exception as e:
                            display_status_card("error", f"Extraction error: {str(e)}", "❌")
                        
                        finally:
                            st.session_state.google_maps_running = False
                            st.rerun()
        
        with col2:
            if st.session_state.google_maps_results:
                # Create Excel download
                businesses_df = pd.DataFrame(st.session_state.google_maps_results)
                excel_data = create_download_link(businesses_df, "Google_Maps_Business_Data.xlsx")
                
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name="Google_Maps_Business_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col3:
            if st.session_state.google_maps_results:
                if st.button("🔄 Clear Results", use_container_width=True, key="gmaps_clear_results_btn"):
                    st.session_state.google_maps_results = None
                    st.rerun()
        
        # Display results
        if st.session_state.google_maps_results:
            st.markdown('<div class="section-header">📋 Business Extraction Results</div>', unsafe_allow_html=True)
            
            businesses_df = pd.DataFrame(st.session_state.google_maps_results)
            
            # Results summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏢 Total Businesses", len(businesses_df))
            with col2:
                with_phone = len(businesses_df[businesses_df['phone'] != '']) if 'phone' in businesses_df.columns else 0
                st.metric("📞 With Phone", with_phone)
            with col3:
                with_website = len(businesses_df[businesses_df['website'] != '']) if 'website' in businesses_df.columns else 0
                st.metric("🌐 With Website", with_website)
            with col4:
                with_email = len(businesses_df[businesses_df['email'] != '']) if 'email' in businesses_df.columns else 0
                st.metric("📧 With Email", with_email)
            
            # Category breakdown
            if 'category' in businesses_df.columns:
                st.markdown("### 📊 Business Categories")
                category_counts = businesses_df['category'].value_counts().head(10)
                if not category_counts.empty:
                    st.bar_chart(category_counts)
            
            # Display main data table
            display_columns = ['business_name', 'phone', 'website', 'email', 'address', 'city', 'state', 'rating']
            available_columns = [col for col in display_columns if col in businesses_df.columns]
            
            if available_columns:
                st.dataframe(
                    businesses_df[available_columns],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(businesses_df, use_container_width=True, hide_index=True)
            
            # Detailed view
            with st.expander("🔍 Complete Business Data"):
                st.dataframe(businesses_df, use_container_width=True, hide_index=True)
        
        # Show database statistics
        st.markdown('<div class="section-header">📊 Database Statistics</div>', unsafe_allow_html=True)
        
        try:
            gmaps_stats = db_manager.get_google_maps_statistics(current_user_id)
            
            if gmaps_stats['total_businesses'] > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total in DB", gmaps_stats['total_businesses'])
                with col2:
                    st.metric("📞 Phone %", f"{gmaps_stats['phone_percentage']:.1f}%")
                with col3:
                    st.metric("🌐 Website %", f"{gmaps_stats['website_percentage']:.1f}%")
                with col4:
                    st.metric("📧 Email %", f"{gmaps_stats['email_percentage']:.1f}%")
                
                # Clear database button
                if st.button("🗑️ Clear Google Maps Data", type="secondary", key="gmaps_clear_db_btn"):
                    db_manager.clear_google_maps_data(current_user_id)
                    display_status_card("success", "Google Maps data cleared successfully!", "✨")
                    st.rerun()
            else:
                st.info("No Google Maps business data in database yet. Extract some businesses to see statistics!")
        
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 