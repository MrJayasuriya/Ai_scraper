from apify_client import ApifyClient
import json
from typing import Dict, List, Any, Optional


class JobScraper:
    """Base class for job scraping with Apify actors"""
    
    def __init__(self, api_token: str):
        self.client = ApifyClient(api_token)
    
    def run_scraper(self, actor_id: str, input_data: Dict[str, Any]) -> List[Dict]:
        """Run the scraper and return results"""
        try:
            print(f"Starting scraper: {actor_id}")
            run = self.client.actor(actor_id).call(run_input=input_data)
            
            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)
            
            print(f"Scraped {len(results)} items successfully")
            return results
            
        except Exception as e:
            print(f"Error running scraper {actor_id}: {str(e)}")
            return []
    
    def save_results(self, results: List[Dict], filename: str = "results.json"):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")


class LinkedInScraper(JobScraper):
    """LinkedIn-specific scraper configurations"""
    
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.proxy_config = {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        }
    
    def scrape_premium_jobs(self, companies: List[str] = None, company_ids: List[str] = None, 
                           location: str = "United States", title: str = "", rows: int = 50) -> List[Dict]:
        """Scrape jobs using premium LinkedIn actor (paid)"""
        
        input_data = {
            "title": title,
            "location": location,
            "companyName": companies or ["Google", "Microsoft"],
            "companyId": company_ids or ["76987811", "1815218"],
            "publishedAt": "",
            "rows": rows,
            "proxy": self.proxy_config,
        }
        
        return self.run_scraper("BHzefUZlZRKWxkTck", input_data)
    
    def scrape_free_jobs(self, query: str = "Software Engineer", location: str = "United States",
                        max_results: int = 50, remote_types: List[str] = None, 
                        contract_types: List[str] = None, time_interval: str = "WEEK") -> List[Dict]:
        """Scrape jobs using free LinkedIn actor"""
        
        input_data = {
            "query": query,
            "location": location,
            "delay": 1000,
            "max_results": max_results,
            "remote": remote_types or ["1", "2", "3"],  # 1=On site, 2=Remote, 3=Hybrid
            "contract_type": contract_types or ["1", "2"],  # 1=Full time, 2=Part-time
            "time_interval": time_interval,
            "proxyConfiguration": self.proxy_config,
        }
        
        return self.run_scraper("forward_dinosaur/linkedin-job-scraper", input_data)
    
    def scrape_alternative_jobs(self, search_url: str, max_results: int = 100) -> List[Dict]:
        """Scrape jobs using alternative LinkedIn actor"""
        
        input_data = {
            "include_company_details": True,
            "max_results": max_results,
            "search_url": search_url,
            "proxy_group": "DATACENTER"
        }
        
        return self.run_scraper("fetchclub/linkedin-jobs-scraper", input_data)


class IndeedScraper(JobScraper):
    """Indeed job scraper (example of extending the base class)"""
    
    def scrape_jobs(self, query: str = "Software Engineer", location: str = "United States",
                   max_results: int = 50) -> List[Dict]:
        """Scrape jobs from Indeed"""
        
        input_data = {
            "queries": [query],
            "locations": [location],
            "maxResults": max_results,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }
        }
        
        # Replace with actual Indeed actor ID when available
        return self.run_scraper("some-indeed-actor-id", input_data)


# Example usage
if __name__ == "__main__":
    # Initialize the LinkedIn scraper
    API_TOKEN = "apify_api_bjdtHFhEJDkUBt8PGSFK8iP7m4Ycae2dqQLX"
    linkedin_scraper = LinkedInScraper(API_TOKEN)
    
    # Option 1: Use free scraper
    print("=== Using Free LinkedIn Scraper ===")
    free_results = linkedin_scraper.scrape_free_jobs(
        query="Python Developer",
        location="San Francisco",
        max_results=25
    )
    linkedin_scraper.save_results(free_results, "free_linkedin_jobs.json")
    
    # Option 2: Use premium scraper (if you have subscription)
    # print("=== Using Premium LinkedIn Scraper ===")
    # premium_results = linkedin_scraper.scrape_premium_jobs(
    #     companies=["Google", "Apple", "Microsoft"],
    #     location="United States",
    #     rows=30
    # )
    # linkedin_scraper.save_results(premium_results, "premium_linkedin_jobs.json")
    
    # Option 3: Use alternative scraper with URL
    # print("=== Using Alternative LinkedIn Scraper ===")
    # search_url = "https://www.linkedin.com/jobs/search?keywords=Data%20Engineer&location=London"
    # alt_results = linkedin_scraper.scrape_alternative_jobs(search_url, max_results=50)
    # linkedin_scraper.save_results(alt_results, "alternative_linkedin_jobs.json")
    
    # Example of extending for other platforms
    # indeed_scraper = IndeedScraper(API_TOKEN)
    # indeed_results = indeed_scraper.scrape_jobs("Data Scientist", "New York")
    # indeed_scraper.save_results(indeed_results, "indeed_jobs.json")