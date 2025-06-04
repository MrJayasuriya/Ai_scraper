#!/usr/bin/env python3

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Callable
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

class GoogleMapsExtractor:
    """Enhanced Google Maps business extractor using Apify Google Maps scraper"""
    
    def __init__(self, apify_token: str = None):
        self.apify_token = apify_token or os.getenv("APIFY_KEY")
        if not self.apify_token:
            raise ValueError("Apify API token is required. Set APIFY_KEY environment variable or pass token as parameter.")
        
        # Set base URL first
        self.base_url = "https://api.apify.com/v2"
        
        # Validate API key format (make it more flexible)
        if not self.apify_token.startswith("apify_api_") and len(self.apify_token) < 10:
            raise ValueError(f"Invalid Apify API key format. Please check your API key from https://console.apify.com/account/integrations")
        
        # Test authentication before proceeding (make it optional for better UX)
        try:
            self._test_authentication()
        except Exception as e:
            print(f"⚠️ Warning: Could not verify API authentication: {str(e)}")
            print("Proceeding anyway - authentication will be tested during extraction.")
        
        try:
            self.client = ApifyClient(self.apify_token)
            self.actor_id = "nwua9Gu5YrADL7ZDj"  # Google Maps scraper
            
            # Test actor access (make it optional)
            try:
                self._test_actor_access()
            except Exception as e:
                print(f"⚠️ Warning: Could not verify actor access: {str(e)}")
                print("Proceeding anyway - actor access will be tested during extraction.")
        except Exception as e:
            raise ValueError(f"Failed to initialize Apify client: {str(e)}")
    
    def _test_authentication(self):
        """Test if the API key is valid"""
        try:
            auth_url = f"{self.base_url}/users/me"
            headers = {"Authorization": f"Bearer {self.apify_token}"}
            
            response = requests.get(auth_url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                raise ValueError(
                    f"Authentication failed - Invalid API key. "
                    f"Please check your Apify API key. "
                    f"Get a new one at: https://console.apify.com/account/integrations"
                )
            elif response.status_code != 200:
                raise ValueError(f"API authentication error: {response.status_code} - {response.text}")
                
            print(f"✅ Apify authentication successful")
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Connection error while testing authentication: {str(e)}")
    
    def _test_actor_access(self):
        """Test if we can access the Google Maps actor"""
        try:
            actor_info = self.client.actor(self.actor_id).get()
            print(f"✅ Google Maps actor accessible: {actor_info.get('name', 'N/A')}")
        except Exception as e:
            if "401" in str(e):
                raise ValueError(
                    f"Cannot access Google Maps actor - Authentication issue. "
                    f"Please verify your Apify API key has proper permissions."
                )
            elif "404" in str(e):
                raise ValueError(
                    f"Google Maps actor not found. Actor ID: {self.actor_id}. "
                    f"Please check if this actor is available in your Apify account."
                )
            else:
                print(f"⚠️ Warning: Could not verify actor access: {str(e)}")
    
    @classmethod
    def test_api_key(cls, api_key: str) -> tuple[bool, str]:
        """Test if an API key is valid without creating a full instance"""
        if not api_key:
            return False, "API key is required"
        
        if not api_key.startswith("apify_api_") and len(api_key) < 10:
            return False, "Invalid API key format"
        
        try:
            base_url = "https://api.apify.com/v2"
            auth_url = f"{base_url}/users/me"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response = requests.get(auth_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "API key is valid"
            elif response.status_code == 401:
                return False, "Invalid API key"
            else:
                return False, f"API error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def extract_business_data(self, 
                             business_names: List[str],
                             location: str = "United States",
                             progress_callback: Callable = None,
                             status_callback: Callable = None) -> List[Dict[str, Any]]:
        """
        Extract business contact data for multiple companies
        
        Args:
            business_names: List of company names to search for
            location: Geographic location for search
            progress_callback: Function to call with progress updates (0.0 to 1.0)
            status_callback: Function to call with status updates
        
        Returns:
            List of extracted business data dictionaries
        """
        
        all_results = []
        total_companies = len(business_names)
        
        for i, business_name in enumerate(business_names):
            try:
                if status_callback:
                    status_callback(f"Processing {business_name} ({i+1}/{total_companies})")
                
                if progress_callback:
                    progress_callback(i / total_companies)
                
                # Extract data for single business
                business_data = self.extract_single_business(business_name, location)
                
                if business_data:
                    all_results.extend(business_data)
                    if status_callback:
                        status_callback(f"✅ Found {len(business_data)} locations for {business_name}")
                else:
                    if status_callback:
                        status_callback(f"⚠️ No data found for {business_name}")
                
                # Small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg:
                    if status_callback:
                        status_callback(f"❌ Authentication error - Please check your Apify API key")
                    print(f"Authentication error for {business_name}: {error_msg}")
                    # Don't continue if authentication fails
                    break
                else:
                    if status_callback:
                        status_callback(f"❌ Error processing {business_name}: {error_msg}")
                    print(f"Error extracting data for {business_name}: {error_msg}")
                continue
        
        if progress_callback:
            progress_callback(1.0)
        
        return all_results
    
    def extract_single_business(self, business_name: str, location: str) -> List[Dict[str, Any]]:
        """Extract data for a single business using enhanced API approach"""
        
        run_input = {
            "searchStringsArray": [business_name],
            "locationQuery": location,
            "maxCrawledPlacesPerSearch": 15,  # Increased for better coverage
            "language": "en",
            "searchMatching": "all", 
            "placeMinimumStars": "",
            "website": "allPlaces",
            "skipClosedPlaces": False,
            "scrapePlaceDetailPage": True,  # Critical for detailed contact info
            "scrapeTableReservationProvider": False,
            "includeWebResults": False,
            "scrapeDirectories": False,
            "maxQuestions": 0,
            "scrapeContacts": True,  # Enable contact scraping
            "maximumLeadsEnrichmentRecords": 0,
            "maxReviews": 3,  # Keep minimal for faster processing
            "reviewsSort": "newest",
            "reviewsFilterString": "",
            "reviewsOrigin": "all",
            "scrapeReviewsPersonalData": False,  # Privacy conscious
            "maxImages": 0,
            "scrapeImageAuthors": False,
            "allPlacesNoSearchAction": "",
            "scrapeAllPhotos": False,
            "additionalInfo": True,  # Get additional business info
        }
        
        try:
            print(f"🔍 Starting extraction for: {business_name}")
            
            # Run the actor with timeout
            run = self.client.actor(self.actor_id).call(
                run_input=run_input,
                timeout_secs=300,  # 5 minute timeout
                memory_mbytes=4096  # Increased memory for better performance
            )
            
            if not run:
                print(f"❌ Failed to start run for {business_name}")
                return []
            
            run_id = run.get("id")
            dataset_id = run.get("defaultDatasetId")
            
            if not dataset_id:
                print(f"❌ No dataset ID found for {business_name}")
                return []
            
            print(f"✅ Run completed for {business_name}. Dataset ID: {dataset_id}")
            
            # Use direct API call to get dataset items (more reliable)
            results = self._get_dataset_items_direct(dataset_id, business_name)
            
            if not results:
                # Fallback to client method
                print(f"🔄 Trying fallback method for {business_name}")
                results = self._get_dataset_items_fallback(dataset_id, business_name)
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                raise ValueError(f"Authentication error: {error_msg}")
            elif "timeout" in error_msg.lower():
                print(f"⏱️ Timeout extracting data for {business_name}: {error_msg}")
                return []
            else:
                print(f"❌ Error extracting data for {business_name}: {error_msg}")
                return []
    
    def _get_dataset_items_direct(self, dataset_id: str, business_name: str) -> List[Dict[str, Any]]:
        """Get dataset items using direct API call (more reliable)"""
        try:
            url = f"{self.base_url}/datasets/{dataset_id}/items"
            headers = {"Authorization": f"Bearer {self.apify_token}"}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            raw_items = response.json()
            
            if not raw_items:
                print(f"⚠️ No items found in dataset for {business_name}")
                return []
            
            print(f"📦 Found {len(raw_items)} raw items for {business_name}")
            
            # Clean and structure the data
            results = []
            for item in raw_items:
                cleaned_item = self.clean_business_data(item, business_name)
                if cleaned_item['business_name']:  # Only add if we have a business name
                    results.append(cleaned_item)
            
            print(f"✨ Processed {len(results)} valid items for {business_name}")
            return results
            
        except Exception as e:
            print(f"❌ Direct API call failed for {business_name}: {str(e)}")
            return []
    
    def _get_dataset_items_fallback(self, dataset_id: str, business_name: str) -> List[Dict[str, Any]]:
        """Fallback method using Apify client"""
        try:
            results = []
            items_found = 0
            
            for item in self.client.dataset(dataset_id).iterate_items():
                items_found += 1
                cleaned_item = self.clean_business_data(item, business_name)
                if cleaned_item['business_name']:  # Only add if we have a business name
                    results.append(cleaned_item)
            
            print(f"📦 Fallback found {items_found} raw items, {len(results)} valid for {business_name}")
            return results
            
        except Exception as e:
            print(f"❌ Fallback method failed for {business_name}: {str(e)}")
            return []
    
    def clean_business_data(self, raw_data: Dict, original_query: str) -> Dict[str, Any]:
        """Clean and structure the extracted business data"""
        
        # Handle nested location data
        location = raw_data.get('location', {})
        if isinstance(location, dict):
            latitude = location.get('lat', '')
            longitude = location.get('lng', '')
        else:
            latitude = longitude = ''
        
        # Extract contact information more thoroughly
        phone = raw_data.get('phone') or raw_data.get('phoneNumber') or ''
        website = raw_data.get('website') or raw_data.get('url') or ''
        
        # More comprehensive email extraction
        email = self.extract_email_from_data(raw_data)
        
        return {
            # Basic info
            'business_name': raw_data.get('title', ''),
            'original_query': original_query,
            'place_id': raw_data.get('placeId', ''),
            
            # Contact information
            'phone': phone,
            'website': website,
            'email': email,
            
            # Location
            'address': raw_data.get('address', ''),
            'city': raw_data.get('city', ''),
            'state': raw_data.get('state', ''),
            'zip_code': raw_data.get('postalCode', ''),
            'country': raw_data.get('country', ''),
            'latitude': latitude,
            'longitude': longitude,
            
            # Business details
            'category': raw_data.get('categoryName', ''),
            'rating': raw_data.get('totalScore', ''),
            'review_count': raw_data.get('reviewsCount', ''),
            'price_level': raw_data.get('priceLevel', ''),
            'business_status': raw_data.get('businessStatus', ''),
            
            # Hours
            'hours': json.dumps(raw_data.get('openingHours', [])),
            'permanently_closed': raw_data.get('permanentlyClosed', False),
            
            # Additional data
            'google_maps_url': raw_data.get('url', ''),
            'plus_code': raw_data.get('plusCode', ''),
            'claimed': raw_data.get('claimed', False),
            'description': raw_data.get('description', ''),
            
            # Metadata
            'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'Google Maps API via Apify',
            'raw_data': json.dumps(raw_data, default=str)  # Store full raw data for reference
        }
    
    def extract_email_from_data(self, data: Dict) -> str:
        """Enhanced email extraction from various fields in the data"""
        import re
        
        # Check common fields where emails might be stored
        email_fields = ['email', 'contactEmail', 'ownerEmail', 'businessEmail']
        
        for field in email_fields:
            if field in data and data[field]:
                return str(data[field]).strip()
        
        # Check in website or other text fields
        text_fields = ['website', 'description', 'additionalInfo', 'about', 'contact']
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        for field in text_fields:
            if field in data and data[field]:
                text = str(data[field])
                email_match = re.search(email_pattern, text)
                if email_match:
                    return email_match.group().strip()
        
        # Check in nested contact information
        if 'contactInfo' in data and isinstance(data['contactInfo'], dict):
            for key, value in data['contactInfo'].items():
                if 'email' in key.lower() and value:
                    return str(value).strip()
        
        return ''
    
    def save_results_to_file(self, results: List[Dict], filename: str = "google_maps_extraction.json"):
        """Save results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(results)} business records to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def get_business_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from extracted data"""
        if not results:
            return {}
        
        total_businesses = len(results)
        with_phone = len([r for r in results if r['phone']])
        with_website = len([r for r in results if r['website']])
        with_email = len([r for r in results if r['email']])
        with_address = len([r for r in results if r['address']])
        
        # Category breakdown
        categories = {}
        for result in results:
            category = result.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_businesses': total_businesses,
            'with_phone': with_phone,
            'with_website': with_website,
            'with_email': with_email,
            'with_address': with_address,
            'phone_percentage': (with_phone / total_businesses) * 100 if total_businesses > 0 else 0,
            'website_percentage': (with_website / total_businesses) * 100 if total_businesses > 0 else 0,
            'email_percentage': (with_email / total_businesses) * 100 if total_businesses > 0 else 0,
            'address_percentage': (with_address / total_businesses) * 100 if total_businesses > 0 else 0,
            'categories': categories
        }


# Example usage
if __name__ == "__main__":
    # Test the extractor
    try:
        extractor = GoogleMapsExtractor()
        
        # Test with a few companies
        test_companies = [
            "Inspira Health Network",
            "Tesla",
            "Starbucks"
        ]
        
        print("🗺️ Testing Enhanced Google Maps extractor...")
        
        def progress_update(progress):
            print(f"Progress: {progress*100:.1f}%")
        
        def status_update(status):
            print(f"Status: {status}")
        
        results = extractor.extract_business_data(
            business_names=test_companies,
            location="United States",
            progress_callback=progress_update,
            status_callback=status_update
        )
        
        print(f"\n✅ Extraction complete! Found {len(results)} business locations")
        
        # Show summary
        summary = extractor.get_business_summary(results)
        print(f"\n📊 Summary:")
        print(f"- Total businesses: {summary['total_businesses']}")
        print(f"- With phone: {summary['with_phone']} ({summary['phone_percentage']:.1f}%)")
        print(f"- With website: {summary['with_website']} ({summary['website_percentage']:.1f}%)")
        print(f"- With email: {summary['with_email']} ({summary['email_percentage']:.1f}%)")
        
        # Save results
        extractor.save_results_to_file(results, "test_google_maps_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("Make sure to set APIFY_KEY environment variable or pass the API key as parameter")
        
        # Provide troubleshooting info
        print("\n🔧 Troubleshooting:")
        print("1. Check your Apify API key at: https://console.apify.com/account/integrations")
        print("2. Ensure your API key has the correct format: apify_api_...")
        print("3. Verify your account has sufficient credits")
        print("4. Make sure you can access the Google Maps scraper actor")
        print("5. Try running with debug output enabled") 