from apify_client import ApifyClient
import json
from typing import Dict, List, Any, Optional
from scraper_config import SCRAPER_CONFIGS, JOB_SEARCH_TEMPLATES


class UniversalJobScraper:
    """Universal job scraper that can handle multiple platforms using configuration"""
    
    def __init__(self, api_token: str):
        self.client = ApifyClient(api_token)
        self.configs = SCRAPER_CONFIGS
        self.templates = JOB_SEARCH_TEMPLATES
    
    def run_scraper(self, scraper_name: str, custom_params: Dict[str, Any] = None) -> List[Dict]:
        """Run a specific scraper with custom parameters"""
        if scraper_name not in self.configs:
            raise ValueError(f"Scraper '{scraper_name}' not found in configurations")
        
        config = self.configs[scraper_name]
        actor_id = config["actor_id"]
        
        # Merge default params with custom params
        params = config["default_params"].copy()
        
        # For LinkedIn URL-based scraper, handle query/location specially
        if custom_params and actor_id == "gdbRh93zn42kBYDyS":
            # Store custom query/location for URL building
            if "query" in custom_params:
                self._custom_query = custom_params["query"]
            if "location" in custom_params:
                self._custom_location = custom_params["location"]
            if "max_results" in custom_params:
                custom_params["count"] = custom_params["max_results"]
            
            # Remove parameters that don't apply to URL-based scraper
            url_incompatible = ["query", "location", "max_results", "delay", "proxyConfiguration"]
            custom_params_clean = {k: v for k, v in custom_params.items() if k not in url_incompatible}
            params.update(custom_params_clean)
        elif custom_params:
            params.update(custom_params)
        
        # LinkedIn-specific optimizations
        if "linkedin" in scraper_name.lower():
            params = self._optimize_linkedin_params(params)
        
        print(f"Starting scraper: {scraper_name} ({actor_id})")
        print(f"Input parameters: {json.dumps(params, indent=2)}")
        
        try:
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=params)
            
            # Get the results
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            print(f"✅ Scraped {len(items)} jobs successfully from {scraper_name}")
            return items
            
        except Exception as e:
            print(f"❌ Error running scraper {scraper_name}: {str(e)}")
            raise
    
    def _optimize_linkedin_params(self, params):
        """Optimize parameters specifically for LinkedIn scraping"""
        optimized = params.copy()
        
        # For URL-based LinkedIn scraper (gdbRh93zn42kBYDyS)
        if "searchUrl" in optimized:
            # If we have custom query/location, rebuild the URL
            if hasattr(self, '_custom_query') or hasattr(self, '_custom_location'):
                optimized["searchUrl"] = self._build_linkedin_search_url(
                    getattr(self, '_custom_query', 'software engineer'),
                    getattr(self, '_custom_location', 'United States'),
                    optimized.get('remote', []),
                    optimized.get('contract_type', [])
                )
            
            # Set reasonable defaults for URL-based scraper
            optimized["scrapeJobDetails"] = True
            optimized["scrapeCompany"] = True
            optimized["scrapeSkills"] = False
            
            if "count" in optimized:
                optimized["count"] = min(optimized["count"], 25)  # Limit to 25
            
            return optimized
        
        # For older parameter-based scrapers
        # Increase delays to avoid rate limiting
        if "delay" in optimized:
            optimized["delay"] = max(optimized["delay"], 2000)
        
        # Ensure proxy configuration for LinkedIn
        if "proxyConfiguration" not in optimized:
            optimized["proxyConfiguration"] = {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            }
        
        # Add stealth mode if supported
        optimized["stealth"] = True
        
        # Reduce max results to avoid detection
        if "max_results" in optimized:
            optimized["max_results"] = min(optimized["max_results"], 10)
        if "maxResults" in optimized:
            optimized["maxResults"] = min(optimized["maxResults"], 10)
        
        # Add longer wait times
        optimized["waitForResults"] = 30000
        
        return optimized
    
    def _build_linkedin_search_url(self, query, location, remote_types=None, contract_types=None):
        """Build LinkedIn search URL with parameters"""
        import urllib.parse
        
        base_url = "https://www.linkedin.com/jobs/search/?"
        
        # URL encode the query and location
        keywords = urllib.parse.quote(query)
        location_encoded = urllib.parse.quote(location)
        
        # Build URL parameters
        url_params = [
            f"keywords={keywords}",
            f"location={location_encoded}",
            "locationId=",
            "geoId=103644278",  # US geo ID
            "f_TPR=",  # Time posted
            "position=1",
            "pageNum=0"
        ]
        
        # Add job type filters
        if contract_types:
            # Convert our format to LinkedIn format
            linkedin_job_types = []
            type_mapping = {"F": "F", "P": "P", "T": "T", "C": "C"}
            for ct in contract_types:
                if ct in type_mapping:
                    linkedin_job_types.append(type_mapping[ct])
            
            if linkedin_job_types:
                url_params.append(f"f_JT={','.join(linkedin_job_types)}")
        else:
            url_params.append("f_JT=F")  # Default to Full-time
        
        # Add work type (remote) filters
        if remote_types:
            # Convert our format to LinkedIn format
            work_types = []
            remote_mapping = {"1": "1", "2": "2", "3": "3"}  # 1=On-site, 2=Remote, 3=Hybrid
            for rt in remote_types:
                if rt in remote_mapping:
                    work_types.append(remote_mapping[rt])
            
            if work_types:
                url_params.append(f"f_WT={','.join(work_types)}")
        else:
            url_params.append("f_WT=3,2")  # Default to Remote and Hybrid
        
        return base_url + "&".join(url_params)
    
    def batch_scrape(self, scraper_jobs: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Run multiple scrapers in batch"""
        all_results = {}
        
        for job in scraper_jobs:
            scraper_name = job.get("scraper")
            custom_params = job.get("params", {})
            filename = job.get("filename", f"{scraper_name}_results.json")
            
            print(f"\n📋 Running batch job: {scraper_name}")
            results = self.run_scraper(scraper_name, custom_params)
            
            if results:
                all_results[scraper_name] = results
                self.save_results(results, filename)
        
        return all_results
    
    def search_by_template(self, template_name: str, scraper_name: str = "linkedin_free") -> List[Dict]:
        """Use predefined search templates"""
        
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found. Available: {list(self.templates.keys())}")
        
        template = self.templates[template_name]
        
        # Convert template to scraper-specific parameters
        custom_params = self._convert_template_to_params(template, scraper_name)
        
        return self.run_scraper(scraper_name, custom_params)
    
    def _convert_template_to_params(self, template: Dict, scraper_name: str) -> Dict:
        """Convert template parameters to scraper-specific format"""
        params = {}
        
        # Handle different scraper parameter formats
        if scraper_name.startswith("linkedin"):
            if "queries" in template:
                params["query"] = template["queries"][0]  # Use first query
            if "locations" in template:
                params["location"] = template["locations"][0]  # Use first location
            if "companies" in template:
                params["companyName"] = template["companies"]
            if "remote_preference" in template:
                params["remote"] = template["remote_preference"]
        
        return params
    
    def save_results(self, results: List[Dict], filename: str = "results.json"):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scrapers"""
        return list(self.configs.keys())
    
    def get_available_templates(self) -> List[str]:
        """Get list of available search templates"""
        return list(self.templates.keys())
    
    def add_custom_scraper(self, name: str, actor_id: str, default_params: Dict):
        """Add a new scraper configuration at runtime"""
        self.configs[name] = {
            "actor_id": actor_id,
            "default_params": default_params
        }
        print(f"✅ Added custom scraper: {name}")


class JobScraperFactory:
    """Factory class to create different types of scrapers"""
    
    @staticmethod
    def create_linkedin_scraper(api_token: str) -> UniversalJobScraper:
        """Create a LinkedIn-focused scraper"""
        scraper = UniversalJobScraper(api_token)
        return scraper
    
    @staticmethod
    def create_multi_platform_scraper(api_token: str) -> UniversalJobScraper:
        """Create a multi-platform scraper"""
        return UniversalJobScraper(api_token)


# Example usage and demonstrations
if __name__ == "__main__":
    API_TOKEN = "apify_api_bjdtHFhEJDkUBt8PGSFK8iP7m4Ycae2dqQLX"
    
    # Create universal scraper
    scraper = UniversalJobScraper(API_TOKEN)
    
    print("🚀 Available scrapers:", scraper.get_available_scrapers())
    print("📋 Available templates:", scraper.get_available_templates())
    
    # Example 1: Simple single scraper
    print("\n=== Example 1: Single Scraper ===")
    results = scraper.run_scraper("linkedin_free", {
        "query": "Python Developer",
        "location": "San Francisco",
        "max_results": 10
    })
    scraper.save_results(results, "python_jobs_sf.json")
    
    # Example 2: Using templates
    print("\n=== Example 2: Using Template ===")
    tech_results = scraper.search_by_template("tech_jobs", "linkedin_free")
    scraper.save_results(tech_results, "tech_jobs_template.json")
    
    # Example 3: Batch scraping
    print("\n=== Example 3: Batch Scraping ===")
    batch_jobs = [
        {
            "scraper": "linkedin_free",
            "params": {"query": "Data Scientist", "location": "New York", "max_results": 15},
            "filename": "data_scientist_ny.json"
        },
        {
            "scraper": "linkedin_free", 
            "params": {"query": "DevOps Engineer", "location": "Austin", "max_results": 15},
            "filename": "devops_austin.json"
        }
    ]
    
    batch_results = scraper.batch_scrape(batch_jobs)
    
    # Example 4: Adding custom scraper at runtime
    print("\n=== Example 4: Custom Scraper ===")
    scraper.add_custom_scraper(
        name="custom_linkedin",
        actor_id="forward_dinosaur/linkedin-job-scraper",
        default_params={
            "query": "Machine Learning Engineer",
            "location": "Remote",
            "max_results": 20,
            "remote": ["2"],  # Remote only
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }
        }
    )
    
    custom_results = scraper.run_scraper("custom_linkedin")
    scraper.save_results(custom_results, "ml_engineer_remote.json")
    
    print("\n✅ All scraping tasks completed!") 