#!/usr/bin/env python3

import requests
import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class JSearchJobScraper:
    """Job scraper using JSearch RapidAPI - Much more reliable than LinkedIn scraping"""
    
    def __init__(self, rapidapi_key: str = None):
        self.rapidapi_key = rapidapi_key or os.getenv("RAPIDAPI_KEY")
        if not self.rapidapi_key:
            raise ValueError("RapidAPI key is required. Set RAPIDAPI_KEY environment variable.")
        
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
    
    def search_jobs(self, 
                   query: str = "software engineer",
                   location: str = "United States", 
                   page: int = 1,
                   num_pages: int = 1,
                   country: str = "us",
                   date_posted: str = "all",
                   employment_types: str = "FULLTIME,PARTTIME",
                   job_requirements: str = "under_3_years_experience,more_than_3_years_experience",
                   remote_jobs_only: bool = False,
                   platform: str = None) -> Dict[str, Any]:
        """
        Search for jobs using JSearch API
        
        Args:
            query: Job search query (e.g., "python developer", "data scientist")
            location: Location to search in (e.g., "New York, NY", "San Francisco")
            page: Page number to retrieve (starts from 1)
            num_pages: Number of pages to retrieve (max 20)
            country: Country code (us, uk, ca, etc.)
            date_posted: Filter by date (all, today, 3days, week, month)
            employment_types: FULLTIME, PARTTIME, CONTRACTOR, INTERN
            job_requirements: under_3_years_experience, more_than_3_years_experience, no_experience, no_degree
            remote_jobs_only: True to only return remote jobs
            platform: Specific platform to search (linkedin, indeed, glassdoor, ziprecruiter, etc.)
        """
        
        # Build query string with platform specification
        if location.lower() != "remote" and not remote_jobs_only:
            if platform:
                search_query = f"{query} in {location} via {platform}"
            else:
                search_query = f"{query} in {location}"
        else:
            if platform:
                search_query = f"remote {query} via {platform}"
            else:
                search_query = f"remote {query}"
        
        querystring = {
            "query": search_query,
            "page": str(page),
            "num_pages": str(min(num_pages, 20)),  # API limit
            "country": country,
            "date_posted": date_posted
        }
        
        # Add optional filters
        if employment_types:
            querystring["employment_types"] = employment_types
        if job_requirements:
            querystring["job_requirements"] = job_requirements
        if remote_jobs_only:
            querystring["remote_jobs_only"] = "true"
        
        try:
            print(f"🔍 Searching jobs: {search_query}")
            print(f"📋 Parameters: {querystring}")
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=querystring,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs_found = len(data.get('data', []))
                print(f"✅ Found {jobs_found} jobs successfully")
                return data
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return {"error": str(e)}
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific job"""
        querystring = {"job_id": job_id}
        
        try:
            response = requests.get(
                f"{self.base_url}/job-details",
                headers=self.headers,
                params=querystring,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def search_multiple_locations(self, 
                                 query: str,
                                 locations: List[str],
                                 max_results_per_location: int = 10) -> List[Dict]:
        """Search jobs across multiple locations"""
        all_jobs = []
        
        for location in locations:
            print(f"\n🌍 Searching in {location}...")
            results = self.search_jobs(
                query=query,
                location=location,
                num_pages=max(1, max_results_per_location // 10)
            )
            
            if "data" in results:
                jobs = results["data"][:max_results_per_location]
                for job in jobs:
                    job["search_location"] = location  # Add metadata
                all_jobs.extend(jobs)
        
        return all_jobs
    
    def search_multiple_queries(self,
                               queries: List[str],
                               location: str = "United States",
                               max_results_per_query: int = 10) -> List[Dict]:
        """Search multiple job types in one location"""
        all_jobs = []
        
        for query in queries:
            print(f"\n🔍 Searching for {query}...")
            results = self.search_jobs(
                query=query,
                location=location,
                num_pages=max(1, max_results_per_query // 10)
            )
            
            if "data" in results:
                jobs = results["data"][:max_results_per_query]
                for job in jobs:
                    job["search_query"] = query  # Add metadata
                all_jobs.extend(jobs)
        
        return all_jobs
    
    def filter_jobs(self, jobs: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply custom filters to job results"""
        filtered_jobs = []
        
        for job in jobs:
            include_job = True
            
            # Salary filter
            if filters.get("min_salary"):
                salary = job.get("job_salary_max", 0) or job.get("job_salary_min", 0)
                if salary and salary < filters["min_salary"]:
                    include_job = False
            
            # Company filter
            if filters.get("excluded_companies"):
                company = job.get("employer_name", "").lower()
                if any(excluded.lower() in company for excluded in filters["excluded_companies"]):
                    include_job = False
            
            # Keywords filter
            if filters.get("required_keywords"):
                job_text = f"{job.get('job_title', '')} {job.get('job_description', '')}".lower()
                if not any(keyword.lower() in job_text for keyword in filters["required_keywords"]):
                    include_job = False
            
            if include_job:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def save_results(self, jobs: List[Dict], filename: str = "jsearch_jobs.json"):
        """Save job results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def get_available_platforms(self) -> List[str]:
        """Get list of supported job platforms"""
        return [
            "linkedin",
            "indeed", 
            "glassdoor",
            "ziprecruiter",
            "monster",
            "careerbuilder",
            "dice",
            "simplyhired",
            "jobscom",
            "flexjobs"
        ]
    
    def get_available_countries(self) -> List[str]:
        """Get list of supported countries"""
        return ["us", "uk", "ca", "au", "de", "fr", "in", "sg", "ae"]
    
    def get_employment_types(self) -> List[str]:
        """Get available employment types"""
        return ["FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"]
    
    def get_date_filters(self) -> List[str]:
        """Get available date filters"""
        return ["all", "today", "3days", "week", "month"]


# Job search templates for common use cases
JOB_TEMPLATES = {
    "tech_remote": {
        "queries": ["software engineer", "python developer", "data scientist", "frontend developer"],
        "location": "remote",
        "employment_types": "FULLTIME",
        "remote_jobs_only": True,
        "platform": None  # Search all platforms
    },
    
    "linkedin_tech": {
        "queries": ["software engineer", "backend developer", "full stack developer"],
        "location": "United States",
        "employment_types": "FULLTIME,PARTTIME",
        "date_posted": "week",
        "platform": "linkedin"  # LinkedIn specific
    },
    
    "indeed_jobs": {
        "queries": ["data scientist", "data engineer", "machine learning engineer"],
        "location": "United States", 
        "employment_types": "FULLTIME",
        "date_posted": "week",
        "platform": "indeed"  # Indeed specific
    },
    
    "glassdoor_salary": {
        "queries": ["senior software engineer", "staff engineer", "principal engineer"],
        "location": "San Francisco, CA",
        "employment_types": "FULLTIME",
        "job_requirements": "more_than_3_years_experience",
        "platform": "glassdoor"  # Glassdoor for salary data
    },
    
    "entry_level": {
        "queries": ["junior developer", "entry level engineer", "software engineer intern"],
        "location": "United States",
        "employment_types": "FULLTIME,INTERN",
        "job_requirements": "under_3_years_experience,no_experience",
        "platform": None  # Search all platforms
    }
}


# Example usage and testing
if __name__ == "__main__":
    # Test the scraper
    try:
        scraper = JSearchJobScraper()
        
        # Test 1: Basic search
        print("=== Test 1: Basic Job Search ===")
        results = scraper.search_jobs(
            query="python developer",
            location="San Francisco, CA",
            num_pages=1,
            date_posted="week"
        )
        
        if "data" in results:
            jobs = results["data"]
            print(f"Found {len(jobs)} jobs")
            
            # Show first job details
            if jobs:
                first_job = jobs[0]
                print(f"Sample job: {first_job.get('job_title')} at {first_job.get('employer_name')}")
                print(f"Location: {first_job.get('job_city')}, {first_job.get('job_state')}")
                print(f"Salary: ${first_job.get('job_salary_min', 'N/A')}-${first_job.get('job_salary_max', 'N/A')}")
            
            scraper.save_results(jobs, "test_python_jobs.json")
        
        # Test 2: Remote jobs
        print("\n=== Test 2: Remote Jobs ===")
        remote_results = scraper.search_jobs(
            query="data scientist",
            location="remote",
            remote_jobs_only=True,
            num_pages=1
        )
        
        if "data" in remote_results:
            remote_jobs = remote_results["data"]
            print(f"Found {len(remote_jobs)} remote jobs")
            scraper.save_results(remote_jobs, "test_remote_jobs.json")
        
        # Test 3: Multiple locations
        print("\n=== Test 3: Multiple Locations ===")
        multi_location_jobs = scraper.search_multiple_locations(
            query="software engineer",
            locations=["New York, NY", "Austin, TX", "Seattle, WA"],
            max_results_per_location=5
        )
        print(f"Found {len(multi_location_jobs)} jobs across multiple locations")
        scraper.save_results(multi_location_jobs, "test_multi_location_jobs.json")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("Make sure to set RAPIDAPI_KEY environment variable") 