#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from jsearch_job_scraper import JSearchJobScraper
import json

load_dotenv()

def test_jsearch_api():
    """Test the JSearch API with platform-specific searches"""
    
    # Use the API key from your test.py file
    api_key = "0597028da3mshba0adfb0a4deeafp136104jsn630c8f1a47e0"
    
    try:
        # Initialize scraper
        scraper = JSearchJobScraper(api_key)
        print("✅ JSearch scraper initialized successfully")
        
        # Test 1: General search
        print("\n🔍 Test 1: General job search...")
        results = scraper.search_jobs(
            query="python developer",
            location="San Francisco, CA",
            num_pages=1,
            date_posted="week"
        )
        
        if "data" in results:
            jobs = results["data"]
            print(f"✅ Found {len(jobs)} jobs (all platforms)!")
            
            if jobs:
                # Show first job details
                first_job = jobs[0]
                print(f"\n📋 Sample job:")
                print(f"Title: {first_job.get('job_title', 'N/A')}")
                print(f"Company: {first_job.get('employer_name', 'N/A')}")
                print(f"Location: {first_job.get('job_city', 'N/A')}, {first_job.get('job_state', 'N/A')}")
                print(f"Salary: ${first_job.get('job_salary_min', 'N/A')}-${first_job.get('job_salary_max', 'N/A')}")
                print(f"Remote: {first_job.get('job_is_remote', 'N/A')}")
                print(f"Apply: {first_job.get('job_apply_link', 'N/A')}")
        
        # Test 2: LinkedIn-specific search
        print("\n🔍 Test 2: LinkedIn-specific search...")
        linkedin_results = scraper.search_jobs(
            query="data scientist",
            location="New York, NY", 
            num_pages=1,
            platform="linkedin"
        )
        
        if "data" in linkedin_results:
            linkedin_jobs = linkedin_results["data"]
            print(f"✅ Found {len(linkedin_jobs)} LinkedIn jobs!")
            
            if linkedin_jobs:
                first_linkedin_job = linkedin_jobs[0]
                print(f"\n📋 LinkedIn job sample:")
                print(f"Title: {first_linkedin_job.get('job_title', 'N/A')}")
                print(f"Company: {first_linkedin_job.get('employer_name', 'N/A')}")
                print(f"Apply URL: {first_linkedin_job.get('job_apply_link', 'N/A')}")
        
        # Test 3: Indeed-specific search
        print("\n🔍 Test 3: Indeed-specific search...")
        indeed_results = scraper.search_jobs(
            query="software engineer",
            location="Austin, TX",
            num_pages=1,
            platform="indeed"
        )
        
        if "data" in indeed_results:
            indeed_jobs = indeed_results["data"]
            print(f"✅ Found {len(indeed_jobs)} Indeed jobs!")
        
        # Test 4: Available platforms
        print(f"\n🌐 Available platforms: {scraper.get_available_platforms()}")
        
        # Save all results
        all_results = {
            "general_search": results.get("data", []),
            "linkedin_search": linkedin_results.get("data", []),
            "indeed_search": indeed_results.get("data", [])
        }
        
        with open("platform_test_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
        
        print("\n💾 Results saved to platform_test_results.json")
        print("✅ All platform tests completed successfully!")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_jsearch_api() 