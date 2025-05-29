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
from Ai_scraper.src.utils.database import db_manager
from Ai_scraper.src.services.serper_api import serper_api
# Use enhanced scraper with retry mechanism and concurrent processing
try:
    from Ai_scraper.src.services.scrape_ai_enhanced import process_links_from_database, get_results_for_download
    ENHANCED_SCRAPER_AVAILABLE = True
    print("✓ Using enhanced scraper with retry mechanism and concurrent processing")
except ImportError:
    from scrape_ai import process_links_from_database, get_results_for_download
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

def main():
    # Premium Header
    st.markdown("""
    <div class="premium-header floating-card">
        <h1>🤖 AI Contact Scraper Pro</h1>
        <p>Advanced Intelligence • Premium Performance • Enterprise Grade</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration with premium styling
    with st.sidebar:
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
        stats = db_manager.get_statistics()
        
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
        if st.button("🗑️ Clear Database", type="secondary", use_container_width=True):
            db_manager.clear_all_data()
            display_status_card("success", "Database cleared successfully!", "✨")
            st.rerun()
    
    # Main content tabs with premium styling
    tab1, tab2, tab3 = st.tabs(["🔍 Intelligent Search", "🎯 AI Extraction", "📊 Analytics Center"])
    
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
                                inserted_count = db_manager.insert_search_results(results)
                                
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
        recent_results = db_manager.get_all_search_results().head(20)
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
        unscraped_df = db_manager.get_unscraped_links()
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
                            status_callback=update_status
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
        all_results_df = db_manager.get_all_search_results()
        
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

if __name__ == "__main__":
    main() 