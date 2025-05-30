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
except ImportError:
    from src.services.scrape_ai_enhanced import process_links_from_database, get_results_for_download
    ENHANCED_SCRAPER_AVAILABLE = False
    print("! Using original scraper (enhanced version not available)")

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
        if st.button("🗑️ Clear My Data", type="secondary", use_container_width=True):
            db_manager.clear_all_data(current_user_id)
            display_status_card("success", "Your data cleared successfully!", "✨")
            st.rerun()
    
    # Main content tabs with premium styling
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Intelligent Search", "🎯 AI Extraction", "📊 Analytics Center", "💼 JSearch Job Scraper"])
    
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
            if st.button("🚀 Launch Search", type="primary", use_container_width=True):
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
            if st.button("🚀 Start AI Extraction", type="primary", use_container_width=True, disabled=unscraped_count == 0):
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
                        disabled=st.session_state.job_scraper_running):
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
                # Create Excel download
                jobs_df = pd.DataFrame(st.session_state.job_scraper_results)
                excel_data = create_download_link(jobs_df, f"JSearch_Jobs_{job_query.replace(' ', '_')}.xlsx")
                
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"JSearch_Jobs_{job_query.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col3:
            if st.session_state.job_scraper_results:
                if st.button("🔄 Clear Results", use_container_width=True):
                    st.session_state.job_scraper_results = None
                    st.rerun()
        
        # Display results
        if st.session_state.job_scraper_results:
            st.markdown('<div class="section-header">📋 Job Search Results</div>', unsafe_allow_html=True)
            
            jobs_df = pd.DataFrame(st.session_state.job_scraper_results)
            
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
            
            # JSON view for debugging (separate expander, not nested)
            with st.expander("🔧 Raw JSON Data (for debugging)"):
                st.json(st.session_state.job_scraper_results[:3])  # Show first 3 jobs
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 