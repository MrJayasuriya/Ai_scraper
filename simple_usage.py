#!/usr/bin/env python3
"""
Simple usage examples for the Universal Job Scraper

This demonstrates how easy it is to add new scrapers without changing existing code.
"""

from universal_job_scraper import UniversalJobScraper

def main():
    # Your API token
    API_TOKEN = "apify_api_bjdtHFhEJDkUBt8PGSFK8iP7m4Ycae2dqQLX"
    
    # Create the scraper
    scraper = UniversalJobScraper(API_TOKEN)
    
    print("🎯 Simple Job Scraper Usage Examples\n")
    
    # Example 1: Quick job search
    print("1️⃣ Quick Python job search in San Francisco")
    python_jobs = scraper.run_scraper("linkedin_free", {
        "query": "Python Developer",
        "location": "San Francisco, CA",
        "max_results": 5
    })
    
    if python_jobs:
        print(f"   Found {len(python_jobs)} Python jobs!")
        scraper.save_results(python_jobs, "python_sf_jobs.json")
    
    # Example 2: Remote jobs only
    print("\n2️⃣ Remote JavaScript jobs")
    js_remote_jobs = scraper.run_scraper("linkedin_free", {
        "query": "JavaScript Developer",
        "location": "United States",
        "remote": ["2"],  # Remote only
        "max_results": 5
    })
    
    if js_remote_jobs:
        print(f"   Found {len(js_remote_jobs)} remote JavaScript jobs!")
        scraper.save_results(js_remote_jobs, "js_remote_jobs.json")
    
    # Example 3: Multiple searches at once
    print("\n3️⃣ Batch searching multiple roles")
    batch_searches = [
        {
            "scraper": "linkedin_free",
            "params": {
                "query": "Data Engineer", 
                "location": "New York",
                "max_results": 5
            },
            "filename": "data_engineer_ny.json"
        },
        {
            "scraper": "linkedin_free",
            "params": {
                "query": "DevOps Engineer",
                "location": "Seattle", 
                "max_results": 5
            },
            "filename": "devops_seattle.json"
        }
    ]
    
    all_results = scraper.batch_scrape(batch_searches)
    total_jobs = sum(len(jobs) for jobs in all_results.values())
    print(f"   Total jobs found across all searches: {total_jobs}")


def add_new_scraper_example():
    """Example of how to add a new scraper without changing existing code"""
    
    API_TOKEN = "apify_api_bjdtHFhEJDkUBt8PGSFK8iP7m4Ycae2dqQLX"
    scraper = UniversalJobScraper(API_TOKEN)
    
    print("\n🔧 Adding a new Indeed scraper (example)")
    
    # Add Indeed scraper configuration
    scraper.add_custom_scraper(
        name="indeed_jobs",
        actor_id="some-indeed-actor-id",  # Replace with real actor ID
        default_params={
            "queries": ["Software Engineer"],
            "locations": ["United States"],
            "maxResults": 5,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }
        }
    )
    
    print("✅ Indeed scraper added! You can now use:")
    print('   scraper.run_scraper("indeed_jobs", {"queries": ["Python Developer"]})')


def company_specific_search():
    """Search for jobs at specific companies"""
    
    API_TOKEN = "apify_api_bjdtHFhEJDkUBt8PGSFK8iP7m4Ycae2dqQLX"
    scraper = UniversalJobScraper(API_TOKEN)
    
    print("\n🏢 Company-specific search")
    
    # Search for Google jobs specifically
    google_jobs = scraper.run_scraper("linkedin_free", {
        "query": "Software Engineer Google",
        "location": "Mountain View, CA",
        "max_results": 5
    })
    
    if google_jobs:
        print(f"   Found {len(google_jobs)} Google jobs!")
        scraper.save_results(google_jobs, "google_jobs.json")


if __name__ == "__main__":
    # Run main examples
    main()
    
    # Show how to add new scrapers
    add_new_scraper_example()
    
    # Company-specific search
    company_specific_search()
    
    print("\n🎉 All examples completed!") 