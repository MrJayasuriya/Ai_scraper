#!/usr/bin/env python3

import os
import json
import time
import requests
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from io import BytesIO
from urllib.parse import quote_plus

class ApifyJobScraper:
    """Simplified and reliable job scraper using proven Apify actors"""
    
    def __init__(self, api_key: str, debug: bool = False):
        self.api_key = api_key
        self.base_url = "https://api.apify.com/v2"
        self.debug = debug
        
        # Proven working actors (tested and verified)
        self.actors = {
            "indeed": {
                "primary": "dtrungtin~indeed-scraper",  # Simple and reliable
                "fallback": "misceres~indeed-scraper",
                "legacy": "nwua9Gu5YrADL7ZDj"
            },
            "linkedin": {
                "primary": "bebity~linkedin-jobs-scraper",
                "fallback": "misceres~linkedin-jobs-scraper"
            }
        }
        
        self.available_platforms = ["indeed", "linkedin"]
        
        # Setup session for reliability
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ApifyJobScraper/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_available_platforms(self) -> List[str]:
        return self.available_platforms
    
    def test_actor(self, actor_id: str) -> bool:
        """Test if actor is available"""
        try:
            response = self.session.get(
                f"{self.base_url}/acts/{actor_id}",
                params={"token": self.api_key},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_working_actor(self, platform: str) -> str:
        """Get first working actor for platform"""
        actors = self.actors.get(platform.lower(), {})
        
        for actor_type in ["primary", "fallback", "legacy"]:
            actor_id = actors.get(actor_type)
            if actor_id:
                if self.debug:
                    print(f"🔍 Testing {platform} actor: {actor_id}")
                
                if self.test_actor(actor_id):
                    if self.debug:
                        print(f"✅ Using working actor: {actor_id}")
                    return actor_id
                elif self.debug:
                    print(f"❌ Actor not available: {actor_id}")
        
        raise Exception(f"No working actors found for {platform}")
    
    def format_query(self, query: str, exact_match: bool = True) -> str:
        """Format search query for better results"""
        query = query.strip()
        
        if exact_match and ' ' in query:
            # Use quotes for exact matching of multi-word job titles
            return f'"{query}"'
        
        return query
    
    def scrape_jobs(self, 
                   platform: str,
                   query: str, 
                   location: str = "United States",
                   max_items: int = 50,
                   exact_match: bool = True,
                   progress_callback: Optional[Callable] = None,
                   status_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Main scraping method"""
        
        platform = platform.lower()
        if platform not in self.available_platforms:
            raise ValueError(f"Platform '{platform}' not supported")
        
        if status_callback:
            status_callback(f"🔍 Starting {platform.title()} job search...")
        
        try:
            # Get working actor
            actor_id = self.get_working_actor(platform)
            
            if progress_callback:
                progress_callback(0.1)
            
            # Format query
            formatted_query = self.format_query(query, exact_match)
            
            # Create input based on platform
            if platform == "indeed":
                run_input = {
                    "position": formatted_query,  # Simpler input format
                    "location": location,
                    "country": "US",
                    "maxItems": max_items,
                    "parseJobDescription": True,
                    "saveOnlyUniqueItems": True
                }
            elif platform == "linkedin":
                # Create LinkedIn search URL
                query_encoded = quote_plus(formatted_query.replace('"', ''))
                location_encoded = quote_plus(location)
                search_url = f"https://www.linkedin.com/jobs/search?keywords={query_encoded}&location={location_encoded}"
                
                run_input = {
                    "startUrls": [{"url": search_url}],
                    "maxItems": max_items,
                    "proxyConfiguration": {"useApifyProxy": True}
                }
            
            if self.debug:
                print(f"📝 Input: {json.dumps(run_input, indent=2)}")
            
            if status_callback:
                status_callback(f"🚀 Starting scraper...")
            
            # Start actor run
            response = self.session.post(
                f"{self.base_url}/acts/{actor_id}/runs",
                params={"token": self.api_key},
                json=run_input,
                timeout=30
            )
            
            if response.status_code != 201:
                raise Exception(f"Failed to start actor: HTTP {response.status_code}")
            
            run_data = response.json()
            run_id = run_data["data"]["id"]
            
            if progress_callback:
                progress_callback(0.2)
            
            if status_callback:
                status_callback(f"⏳ Waiting for results... (Run ID: {run_id})")
            
            # Wait for completion
            max_wait = 300  # 5 minutes
            waited = 0
            
            while waited < max_wait:
                status_response = self.session.get(
                    f"{self.base_url}/acts/{actor_id}/runs/{run_id}",
                    params={"token": self.api_key},
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    run_info = status_response.json()["data"]
                    status = run_info["status"]
                    
                    if status == "SUCCEEDED":
                        break
                    elif status in ["FAILED", "ABORTED"]:
                        error_msg = run_info.get("statusMessage", f"Run {status.lower()}")
                        raise Exception(f"Scraping {status.lower()}: {error_msg}")
                    
                    # Update progress
                    if progress_callback:
                        progress = 0.2 + (waited / max_wait) * 0.6
                        progress_callback(min(progress, 0.8))
                
                time.sleep(10)
                waited += 10
            
            if waited >= max_wait:
                raise TimeoutError("Scraping timed out")
            
            if progress_callback:
                progress_callback(0.9)
            
            if status_callback:
                status_callback("📥 Fetching results...")
            
            # Get results with multiple fallback methods
            raw_results = []
            
            # Method 1: Standard dataset fetch
            try:
                results_response = self.session.get(
                    f"{self.base_url}/acts/{actor_id}/runs/{run_id}/dataset/items",
                    params={"token": self.api_key, "format": "json"},
                    timeout=30
                )
                
                if results_response.status_code == 200:
                    raw_results = results_response.json()
                    if self.debug:
                        print(f"✅ Method 1 successful: {len(raw_results)} results")
                elif self.debug:
                    print(f"⚠️ Method 1 failed: HTTP {results_response.status_code}")
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Method 1 error: {e}")
            
            # Method 2: Get dataset ID from run info and try that
            if not raw_results:
                try:
                    run_info_response = self.session.get(
                        f"{self.base_url}/acts/{actor_id}/runs/{run_id}",
                        params={"token": self.api_key},
                        timeout=10
                    )
                    
                    if run_info_response.status_code == 200:
                        run_info = run_info_response.json()["data"]
                        dataset_id = run_info.get("defaultDatasetId")
                        
                        if dataset_id:
                            dataset_response = self.session.get(
                                f"{self.base_url}/datasets/{dataset_id}/items",
                                params={"token": self.api_key, "format": "json"},
                                timeout=30
                            )
                            
                            if dataset_response.status_code == 200:
                                raw_results = dataset_response.json()
                                if self.debug:
                                    print(f"✅ Method 2 successful with dataset {dataset_id}: {len(raw_results)} results")
                            elif self.debug:
                                print(f"⚠️ Method 2 dataset failed: HTTP {dataset_response.status_code}")
                    elif self.debug:
                        print(f"⚠️ Method 2 run info failed: HTTP {run_info_response.status_code}")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Method 2 error: {e}")
            
            # Method 3: Try key-value store
            if not raw_results:
                try:
                    kv_response = self.session.get(
                        f"{self.base_url}/key-value-stores/default/records/OUTPUT",
                        params={"token": self.api_key},
                        timeout=30
                    )
                    
                    if kv_response.status_code == 200:
                        kv_data = kv_response.json()
                        if isinstance(kv_data, list):
                            raw_results = kv_data
                        elif isinstance(kv_data, dict) and "items" in kv_data:
                            raw_results = kv_data["items"]
                        
                        if raw_results and self.debug:
                            print(f"✅ Method 3 successful: {len(raw_results)} results")
                    elif self.debug:
                        print(f"⚠️ Method 3 failed: HTTP {kv_response.status_code}")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Method 3 error: {e}")
            
            if not raw_results:
                raise Exception("Failed to fetch results using all available methods")
            
            if not raw_results:
                if status_callback:
                    status_callback("⚠️ No jobs found")
                return []
            
            if self.debug:
                print(f"📊 Raw results: {len(raw_results)}")
                if raw_results:
                    sample = raw_results[0]
                    print(f"📋 Sample fields: {list(sample.keys())[:10]}")
                    # Check for error responses
                    if "error" in sample:
                        print(f"⚠️ Error in results: {sample.get('error', 'Unknown error')}")
                    elif sample:
                        print(f"📄 Sample data: {sample}")
            
            # Filter out error results
            raw_results = [result for result in raw_results if not result.get("error")]
            
            # Process results
            processed_jobs = self.process_results(raw_results, platform)
            
            # Filter for relevance
            relevant_jobs = self.filter_relevant_jobs(processed_jobs, query)
            
            if progress_callback:
                progress_callback(1.0)
            
            if status_callback:
                status_callback(f"✅ Found {len(relevant_jobs)} relevant jobs!")
            
            if self.debug:
                print(f"📈 Processing: {len(raw_results)} → {len(processed_jobs)} → {len(relevant_jobs)}")
            
            return relevant_jobs
            
        except Exception as e:
            error_msg = f"{platform.title()} error: {str(e)}"
            if status_callback:
                status_callback(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def process_results(self, raw_results: List[Dict], platform: str) -> List[Dict[str, Any]]:
        """Process raw results into standardized format"""
        processed_jobs = []
        
        # Field mappings for different platforms
        if platform == "indeed":
            field_map = {
                "job_title": ["positionName", "title", "jobTitle", "displayTitle"],
                "company_name": ["company", "companyName"],
                "job_location": ["location", "formattedLocation"],
                "apply_url": ["url", "jobUrl", "applyUrl", "externalApplyLink"],
                "job_description": ["description", "jobDescription", "snippet"],
                "posted_date": ["postedAt", "pubDate", "formattedRelativeTime"],
                "salary_info": ["salary", "salarySnippet.text", "extractedSalary"],
                "company_rating": ["rating", "companyRating"],
                "job_type": ["jobType"]
            }
        else:  # linkedin
            field_map = {
                "job_title": ["title", "jobTitle"],
                "company_name": ["companyName", "company"],
                "job_location": ["location", "jobLocation"],
                "apply_url": ["applyUrl", "jobUrl"],
                "job_description": ["description", "jobDescription"],
                "posted_date": ["postedAt", "publishedAt"],
                "salary_info": ["salary"]
            }
        
        for job_data in raw_results:
            try:
                processed_job = {"platform": platform}
                
                # Extract fields
                for field, possible_keys in field_map.items():
                    value = self.extract_field(job_data, possible_keys)
                    processed_job[field] = value
                
                # Process salary for Indeed
                if platform == "indeed" and not processed_job["salary_info"]:
                    salary_data = job_data.get("extractedSalary", {})
                    if salary_data and isinstance(salary_data, dict):
                        min_sal = salary_data.get("min")
                        max_sal = salary_data.get("max")
                        if min_sal or max_sal:
                            if min_sal and max_sal:
                                processed_job["salary_info"] = f"${min_sal} - ${max_sal}"
                            elif min_sal:
                                processed_job["salary_info"] = f"${min_sal}+"
                            elif max_sal:
                                processed_job["salary_info"] = f"Up to ${max_sal}"
                
                # Clean description
                if processed_job["job_description"] and len(processed_job["job_description"]) > 500:
                    processed_job["job_description"] = processed_job["job_description"][:500] + "..."
                
                # Only keep jobs with basic info
                if processed_job.get("job_title") or processed_job.get("company_name"):
                    processed_jobs.append(processed_job)
                    
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Error processing job: {e}")
                continue
        
        return processed_jobs
    
    def extract_field(self, data: Dict, possible_keys: List[str]) -> str:
        """Extract field value from job data"""
        for key in possible_keys:
            try:
                if '.' in key:
                    # Handle nested keys like "salarySnippet.text"
                    parts = key.split('.')
                    value = data
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                    
                    if value is not None:
                        return str(value).strip()
                else:
                    # Direct key access
                    if key in data and data[key] is not None:
                        value = data[key]
                        if isinstance(value, (str, int, float)):
                            return str(value).strip()
                        elif isinstance(value, list) and value:
                            # Handle job types as comma-separated string
                            if key == "jobType":
                                return ", ".join(str(v) for v in value)
                            return str(value[0]).strip()
                        elif isinstance(value, dict) and "text" in value:
                            return str(value["text"]).strip()
            except:
                continue
        
        return ""
    
    def filter_relevant_jobs(self, jobs: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """Filter jobs for relevance to search query"""
        if not jobs or not original_query:
            return jobs
        
        query_words = [word.lower().strip() for word in original_query.split() if len(word.strip()) > 2]
        
        relevant_jobs = []
        
        for job in jobs:
            relevance_score = 0
            
            job_title = job.get('job_title', '').lower()
            job_description = job.get('job_description', '').lower()
            
            # Score based on title matches (highest weight)
            for word in query_words:
                if word in job_title:
                    relevance_score += 3
            
            # Score based on description matches
            for word in query_words:
                if word in job_description:
                    relevance_score += 1
            
            # Bonus for exact query match
            if original_query.lower() in job_title:
                relevance_score += 5
            
            # Keep jobs with minimum relevance
            min_threshold = 1 if len(query_words) == 1 else 2
            if relevance_score >= min_threshold:
                job['relevance_score'] = relevance_score
                relevant_jobs.append(job)
        
        # Sort by relevance
        relevant_jobs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return relevant_jobs
    
    def get_job_summary(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate job summary statistics"""
        if not jobs:
            return {"total_jobs": 0}
        
        df = pd.DataFrame(jobs)
        
        return {
            "total_jobs": len(jobs),
            "unique_companies": len(df['company_name'].dropna().unique()) if 'company_name' in df.columns else 0,
            "platforms": list(df['platform'].unique()) if 'platform' in df.columns else [],
            "with_salary": len(df[df['salary_info'] != '']) if 'salary_info' in df.columns else 0
        }
    
    def create_jobs_excel(self, jobs_data: List[Dict], search_query: str, search_location: str, platform: str) -> Optional[bytes]:
        """Create Excel file with job data"""
        if not jobs_data:
            return None
        
        try:
            df = pd.DataFrame(jobs_data)
            
            # Clean column mapping
            columns = {
                'Job Title': 'job_title',
                'Company': 'company_name',
                'Location': 'job_location',
                'Salary': 'salary_info',
                'Posted Date': 'posted_date',
                'Apply URL': 'apply_url',
                'Description': 'job_description',
                'Platform': 'platform',
                'Relevance Score': 'relevance_score'
            }
            
            excel_data = {}
            for excel_col, data_col in columns.items():
                if data_col in df.columns:
                    excel_data[excel_col] = df[data_col]
                else:
                    excel_data[excel_col] = [''] * len(df)
            
            excel_df = pd.DataFrame(excel_data)
            
            # Create metadata
            metadata = pd.DataFrame({
                'Search Query': [search_query],
                'Location': [search_location],
                'Platform': [platform.title()],
                'Total Jobs': [len(df)],
                'Export Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
            
            # Write to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                excel_df.to_excel(writer, sheet_name='Jobs', index=False)
                metadata.to_excel(writer, sheet_name='Info', index=False)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Excel creation error: {e}")
            return None

# Test function
def test_scraper():
    """Test the scraper"""
    api_key = os.getenv("APIFY_KEY")
    if not api_key:
        print("❌ Set APIFY_KEY environment variable")
        return []
    
    scraper = ApifyJobScraper(api_key, debug=True)
    
    def progress(p):
        print(f"📊 {p*100:.0f}%")
    
    def status(s):
        print(f"📢 {s}")
    
    try:
        print("🧪 Testing Indeed scraper...")
        jobs = scraper.scrape_jobs(
            platform="indeed",
            query="medical biller",
            location="United States",
            max_items=10,
            progress_callback=progress,
            status_callback=status
        )
        
        print(f"\n✅ Success! Found {len(jobs)} jobs")
        
        if jobs:
            print("\n📋 Sample jobs:")
            for i, job in enumerate(jobs[:3]):
                print(f"{i+1}. {job.get('job_title', 'No title')}")
                print(f"   Company: {job.get('company_name', 'Unknown')}")
                print(f"   Location: {job.get('job_location', 'Unknown')}")
                print(f"   Salary: {job.get('salary_info', 'Not specified')}")
        
        return jobs
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return []

if __name__ == "__main__":
    test_scraper() 