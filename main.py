import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv
from scrapegraph_py import Client
import time

# Load environment variables from .env file FIRST!
load_dotenv()

# --- Configuration ---
# It's highly recommended to use environment variables for API keys.
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "0da3cd5baeefef7360c8aa32bd50028cbd5d14c7") # Your Serper API Key
SCRAPEGRAPH_API_KEY = os.getenv("SCRAPEGRAPH_API_KEY") # Ensure this is in your .env
SERPER_SEARCH_URL = "https://google.serper.dev/search"
DEFAULT_EXCEL_OUTPUT_PATH = "serper_search_output_SG.xlsx" # Changed default name slightly
SCRAPEGRAPH_DELAY = 2 # Seconds to wait between ScrapeGraph API calls (if needed, good practice)

class SerperSearcher:
    def __init__(self, serper_api_key: str, scrapegraph_client_instance):
        if not serper_api_key or serper_api_key == "0da3cd5baeefef7360c8aa32bd50028cbd5d14c7":
            print("WARNING: Using a fallback API key for Serper. Please set the SERPER_API_KEY environment variable.")
        self.serper_api_key = serper_api_key
        self.serper_headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        self.scrapegraph_client = scrapegraph_client_instance
        if not self.scrapegraph_client:
             print("WARNING: ScrapeGraph client not initialized. Contact scraping will be skipped.")

    def _flatten_search_result(self, result_item: dict, query: str, location: str) -> dict:
        """Flattens a single organic search result item."""
        if not result_item or not isinstance(result_item, dict):
            return {}
        
        # Extract address components if available (common in local pack results within organic search)
        address_info = result_item.get("address", {})
        full_address = address_info.get("text", "")
        
        return {
            "original_query": query,
            "original_location": location,
            "position": result_item.get("position"),
            "title": result_item.get("title"),
            "link": result_item.get("link"),
            "snippet": result_item.get("snippet"),
            "source": result_item.get("source"), # Domain, if provided
            "rating": result_item.get("rating"), # Stars, if available
            "reviews_count": result_item.get("reviews"), # Number of reviews, if available
            "phone_number_serper": result_item.get("phoneNumber"), # Phone from Serper
            "scraped_name": None,
            "scraped_phone_number": None,
            "scraped_email_address": None,
            "address_text": full_address, # From address.text, if available
            "attributes": json.dumps(result_item.get("attributes")) if result_item.get("attributes") else None,
            # Add more fields if Serper provides them consistently, e.g., from "sitelinks" or other specific result types
        }

    def search(self, query: str, location: str, num_results: int = 10) -> list[dict] | None:
        """Performs a search using Serper API and returns flattened organic results."""
        payload = json.dumps({
                    "q": query,
                    "location": location,
                    "num": num_results # Number of results to return
                })
        
        print(f"Searching Serper for query='{query}', location='{location}'...")
        try:
            response = requests.post(SERPER_SEARCH_URL, headers=self.serper_headers, data=payload, timeout=20)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            api_data = response.json()
            
            # print(f"\nRaw API Response for debugging:")
            # print(json.dumps(api_data, indent=2))

            organic_results = api_data.get("organic", []) # Serper usually has results in 'organic'
            # Serper might also have 'places', 'localResults', 'knowledgeGraph' etc.
            # For this example, we are primarily focusing on 'organic' results.
            
            if not organic_results:
                print("No organic search results found in the API response.")
                if "Error" in api_data:
                    print(f"API Error: {api_data.get('Error')}")
                elif "error" in api_data:
                    print(f"API Error: {api_data.get('error')}")
                else:
                    print("API Response snippet:")
                    print(json.dumps(api_data, indent=2)[:1000])
                return None

            flattened_results = [self._flatten_search_result(item, query, location) for item in organic_results]
            
            print(f"Found {len(flattened_results)} organic results via Serper.")
            return flattened_results

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.text[:500]}") 
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        except json.JSONDecodeError as json_err:
            print(f"JSON decoding error: {json_err}")
            print(f"Response content: {response.text[:500]}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")
        return None

    def _scrape_contacts_with_scrapegraph(self, url: str) -> dict:
        """Uses ScrapeGraph to extract contacts from a URL."""
        if not self.scrapegraph_client:
            print("ScrapeGraph client not available, skipping scrape.")
            return {}
            
        print(f"  Scraping with ScrapeGraph: {url}")
        contacts_data = {}
        try:
            response = self.scrapegraph_client.smartscraper(
                website_url=url,
                user_prompt="Extract all contact details including names (of people or company), phone numbers, and email addresses from the source. Prioritize official contact information."
            )
            # Assuming response is a dictionary. Structure may vary.
            # Example: {'names': ['John Doe'], 'phone_numbers': ['555-1234'], 'emails': ['j.doe@example.com']}
            # We will take the first item from each list if available.
            if isinstance(response, dict):
                # Names: Look for a 'names' key, or potentially 'company_name', 'contact_persons' etc.
                # This part is speculative and depends on ScrapeGraph's typical output for such a prompt.
                names_list = response.get("names", response.get("name", response.get("company_name", [])))
                if isinstance(names_list, list) and names_list:
                    contacts_data["scraped_name"] = names_list[0]
                
                phone_list = response.get("phone_numbers", response.get("phones", []))
                if isinstance(phone_list, list) and phone_list:
                    contacts_data["scraped_phone_number"] = phone_list[0]
                
                email_list = response.get("emails", response.get("email_addresses", []))
                if isinstance(email_list, list) and email_list:
                    contacts_data["scraped_email_address"] = email_list[0]
                
                if not contacts_data:
                    print(f"    ScrapeGraph returned data, but no specific contacts extracted: {response}")
                else:
                    print(f"    ScrapeGraph extracted: Name: {contacts_data.get('scraped_name')}, Phone: {contacts_data.get('scraped_phone_number')}, Email: {contacts_data.get('scraped_email_address')}")
            else:
                print(f"    ScrapeGraph returned unexpected data type: {type(response)}. Response: {str(response)[:500]}")

        except Exception as e:
            print(f"    Error during ScrapeGraph call for {url}: {e}")
        return contacts_data

    def enrich_results_with_scraped_contacts(self, results: list[dict]) -> list[dict]:
        if not results or not self.scrapegraph_client:
            print("No results to enrich or ScrapeGraph client not available.")
            return results
        
        print(f"\nStarting contact scraping with ScrapeGraph for {len(results)} results...")
        enriched_results = []
        for i, result in enumerate(results):
            enriched_result = result.copy()
            url_to_scrape = enriched_result.get("link")

            if url_to_scrape:
                scraped_data = self._scrape_contacts_with_scrapegraph(url_to_scrape)
                enriched_result.update(scraped_data) # Update with any found contacts
                time.sleep(SCRAPEGRAPH_DELAY) # Be respectful with API calls
            else:
                print(f"  Skipping ScrapeGraph for '{enriched_result.get('title', 'N/A')}': No link.")
            
            enriched_results.append(enriched_result)
        print("ScrapeGraph contact enrichment finished.")
        return enriched_results

    def save_to_excel(self, search_results: list[dict], output_path: str):
        """Saves a list of flattened search results to an Excel file."""
        if not search_results:
            print("No search results to save.")
            return

        df = pd.DataFrame(search_results)
        
        # Define a preferred column order - adjust based on typical Serper response for your queries
        preferred_columns = [
            'original_query', 'original_location', 'position', 'title', 'link', 'snippet', 'source', 
            'address_text', 'phone_number_serper', 'scraped_name', 'scraped_phone_number', 'scraped_email_address',
            'rating', 'reviews_count', 'attributes'
        ]
        
        for col in preferred_columns:
            if col not in df.columns:
                df[col] = None 
        final_cols = [col for col in preferred_columns if col in df.columns] + \
                     [col for col in df.columns if col not in preferred_columns]
        df = df[list(dict.fromkeys(final_cols))] # Keep order and ensure unique columns

        try:
            df.to_excel(output_path, index=False)
            print(f"Search results successfully saved to {output_path} ({df.shape[0]} rows)")
        except Exception as e:
            print(f"Error saving to Excel: {e}")

def main():
    print("Serper Google Search & ScrapeGraph Contact Extractor")
    print("-----------------------------------------------------")

    # Initialize ScrapeGraph Client
    scrapegraph_api_key_env = os.getenv("SCRAPEGRAPH_API_KEY")
    sg_client = None
    if scrapegraph_api_key_env:
        try:
            sg_client = Client(api_key=scrapegraph_api_key_env)
            # balance = sg_client.get_balance() # You can uncomment this to check balance
            # print(f"ScrapeGraph client initialized. Balance: {balance}")
        except Exception as e:
            print(f"Failed to initialize ScrapeGraph client: {e}. Scraping will be skipped.")
    else:
        print("SCRAPEGRAPH_API_KEY not found in environment variables. Scraping will be skipped.")

    serper_api_key_env = SERPER_API_KEY # Already fetched with fallback
    searcher = SerperSearcher(serper_api_key=serper_api_key_env, scrapegraph_client_instance=sg_client)
    
    query = input("Enter search query (e.g., 'Dental clinics'): ")
    location = input("Enter location (e.g., 'Texas, United States'): ")
    num_results_str = input("Enter number of results (default 10): ")
    num_results = int(num_results_str) if num_results_str.strip() else 10

    if not query.strip() or not location.strip():
        print("Query and location cannot be empty.")
        return

    results = searcher.search(query=query, location=location, num_results=num_results)
    if results:
        if sg_client: # Only enrich if client is available
            enriched_data = searcher.enrich_results_with_scraped_contacts(results)
        else:
            enriched_data = results # Proceed without enrichment
            print("Proceeding without ScrapeGraph enrichment.")
            
        output_fn = input(f"Save to Excel (default: {DEFAULT_EXCEL_OUTPUT_PATH}): ") or DEFAULT_EXCEL_OUTPUT_PATH
        searcher.save_to_excel(enriched_data, output_fn)
    else:
        print("No results from Serper to process.")

if __name__ == "__main__":
    main()

print("Test")