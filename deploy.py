#!/usr/bin/env python3
"""
Deployment Helper Script for AI Contact Scraper Pro
Checks dependencies and guides deployment process
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filename):
    """Check if a required file exists"""
    return Path(filename).exists()

def check_env_vars():
    """Check if required environment variables are set"""
    required_vars = [
        "SERPER_API_KEY",
        "OPENROUTER_API_KEY", 
        "RAPIDAPI_KEY",
        "APIFY_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars

def test_imports():
    """Test if imports work correctly"""
    try:
        print("🔍 Testing imports...")
        
        # Test basic imports
        import streamlit
        import pandas
        import plotly
        print("✅ Basic dependencies OK")
        
        # Test scraper fallback system
        try:
            from src.services.scrape_ai_enhanced import process_links_from_database
            print("✅ Enhanced scraper available")
            scraper_type = "Enhanced"
        except ImportError:
            try:
                from src.services.scrape_ai_simple import process_links_from_database
                print("✅ Simple scraper available")
                scraper_type = "Simple"
            except ImportError:
                print("❌ No scraper available")
                return False, "No scraper"
        
        # Test other components
        from src.utils.database import db_manager
        from src.utils.auth import auth_manager
        print("✅ Database and auth OK")
        
        from jsearch_job_scraper import JSearchJobScraper
        from google_maps_extractor import GoogleMapsExtractor
        print("✅ Job and Maps scrapers OK")
        
        return True, scraper_type
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False, str(e)

def main():
    print("🚀 AI Contact Scraper Pro - Deployment Checker")
    print("=" * 50)
    
    # Check required files
    print("\n📁 Checking required files...")
    required_files = [
        "requirements.txt",
        "streamlit_app.py", 
        ".streamlit/config.toml",
        "src/utils/database.py",
        "src/utils/auth.py"
    ]
    
    missing_files = []
    for file in required_files:
        if check_file_exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        print("Please ensure all required files are present.")
        return False
    
    # Test imports
    print("\n🔍 Testing imports...")
    imports_ok, scraper_info = test_imports()
    
    if not imports_ok:
        print(f"\n❌ Import issues detected: {scraper_info}")
        print("Try installing dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    print(f"✅ All imports working (Scraper: {scraper_info})")
    
    # Check environment variables
    print("\n🔐 Checking environment variables...")
    missing_vars = check_env_vars()
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print("These will need to be configured in your deployment platform.")
    else:
        print("✅ All environment variables configured locally")
    
    # Deployment recommendations
    print("\n🎯 Deployment Recommendations:")
    print("1. 🥇 Streamlit Community Cloud (FREE)")
    print("   - Go to share.streamlit.io")
    print("   - Connect your GitHub repo")
    print("   - Add API keys as secrets")
    print("   - Deploy!")
    
    print("\n2. 🥈 Railway ($5/month)")
    print("   - Go to railway.app") 
    print("   - Deploy from GitHub")
    print("   - Auto-detects Python/Streamlit")
    
    print("\n3. 🥉 Heroku ($7/month)")
    print("   - Requires Procfile and runtime.txt")
    print("   - More setup but very reliable")
    
    print("\n📋 Next Steps:")
    print("1. Push code to GitHub (public repo for free Streamlit Cloud)")
    print("2. Choose deployment platform above")
    print("3. Add environment variables in platform dashboard")
    print("4. Deploy and test!")
    
    print(f"\n✅ Your app is ready for deployment!")
    print(f"📊 Scraper mode: {scraper_info}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Deployment check failed: {e}")
        sys.exit(1) 