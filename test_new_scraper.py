#!/usr/bin/env python3

import os
from universal_job_scraper import UniversalJobScraper
from dotenv import load_dotenv

load_dotenv()
# Test the new LinkedIn scraper
def test_new_linkedin_scraper():
    """Test the new URL-based LinkedIn scraper"""
    
    # Get API token from environment
    api_token = os.getenv("APIFY_KEY")
    if not api_token:
        print("❌ APIFY_KEY environment variable not set!")
        return
    
    # Initialize scraper
    scraper = UniversalJobScraper(api_token)
    
    # Test with custom parameters
    print("🔍 Testing new LinkedIn scraper with custom parameters...")
    
    custom_params = {
        "query": "Python Developer",
        "location": "San Francisco, CA",
        "max_results": 5,  # Will be converted to "count"
        "remote": ["2", "3"],  # Remote and Hybrid
        "contract_type": ["F", "P"]  # Full-time and Part-time
    }
    
    try:
        results = scraper.run_scraper("linkedin_free", custom_params)
        
        if results:
            print(f"\n✅ SUCCESS! Found {len(results)} jobs")
            
            # Show first result structure
            first_job = results[0]
            print(f"\n📋 First job data structure:")
            print(f"Available fields: {list(first_job.keys())}")
            
            # Show sample values
            print(f"\n📝 Sample values:")
            for key, value in first_job.items():
                if value and str(value) != 'N/A':
                    display_value = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                    print(f"  {key}: {display_value}")
                    
        else:
            print("⚠️ No results returned")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_new_linkedin_scraper() 