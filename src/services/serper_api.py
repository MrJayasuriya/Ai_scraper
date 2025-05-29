import requests
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class SerperAPI:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
        
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def search(self, query: str, location: str = "", num_results: int = 10) -> List[Dict]:
        """
        Perform a search using Serper API
        
        Args:
            query: Search query
            location: Location for search (optional)
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        payload = {
            "q": query,
            "num": num_results
        }
        
        if location:
            payload["location"] = location
        
        try:
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            organic_results = data.get("organic", [])
            
            # Process and flatten results
            processed_results = []
            for idx, result in enumerate(organic_results):
                processed_result = self._process_result(result, query, location, idx + 1)
                processed_results.append(processed_result)
            
            return processed_results
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Serper API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Serper API response: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during search: {str(e)}")
    
    def _process_result(self, result: Dict, query: str, location: str, position: int) -> Dict:
        """
        Process a single search result into standardized format
        
        Args:
            result: Raw result from Serper API
            query: Original search query
            location: Search location
            position: Result position
            
        Returns:
            Processed result dictionary
        """
        # Extract address information if available
        address_text = ""
        if "address" in result:
            if isinstance(result["address"], dict):
                address_text = result["address"].get("text", "")
            elif isinstance(result["address"], str):
                address_text = result["address"]
        
        # Extract attributes if available
        attributes = result.get("attributes", {})
        if attributes and isinstance(attributes, dict):
            attributes = json.dumps(attributes)
        else:
            attributes = None
        
        return {
            "original_query": query,
            "original_location": location,
            "position": position,
            "title": result.get("title", ""),
            "link": result.get("link", ""),
            "snippet": result.get("snippet", ""),
            "source": result.get("source", ""),
            "address_text": address_text,
            "phone_number_serper": result.get("phoneNumber", ""),
            "rating": result.get("rating"),
            "reviews_count": result.get("reviews"),
            "attributes": attributes
        }
    
    def search_local_businesses(self, business_type: str, location: str, num_results: int = 10) -> List[Dict]:
        """
        Search for local businesses
        
        Args:
            business_type: Type of business (e.g., "dental clinics", "restaurants")
            location: Location to search in
            num_results: Number of results to return
            
        Returns:
            List of business search results
        """
        query = f"{business_type} in {location}"
        return self.search(query, location, num_results)

# Create global Serper API instance
serper_api = SerperAPI() if os.getenv("SERPER_API_KEY") else None 