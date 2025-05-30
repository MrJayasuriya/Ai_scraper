#!/usr/bin/env python3

import os
import json
import time
from typing import Dict, List, Any, Optional, Callable
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

class GoogleMapsExtractor:
    """Google Maps business extractor using Apify Google Maps scraper"""
    
    def __init__(self, apify_token: str = None):
        self.apify_token = apify_token or os.getenv("APIFY_KEY")
        if not self.apify_token:
            raise ValueError("Apify API token is required. Set APIFY_KEY environment variable or pass token as parameter.")
        
        self.client = ApifyClient(self.apify_token)
        self.actor_id = "nwua9Gu5YrADL7ZDj"  # Google Maps scraper
    
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
                time.sleep(1)
                
            except Exception as e:
                if status_callback:
                    status_callback(f"❌ Error processing {business_name}: {str(e)}")
                continue
        
        if progress_callback:
            progress_callback(1.0)
        
        return all_results
    
    def extract_single_business(self, business_name: str, location: str) -> List[Dict[str, Any]]:
        """Extract data for a single business"""
        
        run_input = {
            "searchStringsArray": [business_name],
            "locationQuery": location,
            "maxCrawledPlacesPerSearch": 10,  # Get multiple locations
            "language": "en",
            "searchMatching": "all",
            "placeMinimumStars": "",
            "website": "allPlaces",
            "skipClosedPlaces": False,
            "scrapePlaceDetailPage": True,  # Get detailed contact info
            "scrapeTableReservationProvider": False,
            "includeWebResults": False,
            "scrapeDirectories": False,
            "maxQuestions": 0,
            "scrapeContacts": True,  # Enable contact scraping
            "maximumLeadsEnrichmentRecords": 0,
            "maxReviews": 5,  # Get some reviews for context
            "reviewsSort": "newest",
            "reviewsFilterString": "",
            "reviewsOrigin": "all",
            "scrapeReviewsPersonalData": True,
            "maxImages": 0,
            "scrapeImageAuthors": False,
            "allPlacesNoSearchAction": "",
        }
        
        try:
            # Run the actor
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            # Fetch results
            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                # Clean and structure the data
                cleaned_item = self.clean_business_data(item, business_name)
                results.append(cleaned_item)
            
            return results
            
        except Exception as e:
            print(f"Error extracting data for {business_name}: {str(e)}")
            return []
    
    def clean_business_data(self, raw_data: Dict, original_query: str) -> Dict[str, Any]:
        """Clean and structure the extracted business data"""
        
        return {
            # Basic info
            'business_name': raw_data.get('title', ''),
            'original_query': original_query,
            'place_id': raw_data.get('placeId', ''),
            
            # Contact information
            'phone': raw_data.get('phone', ''),
            'website': raw_data.get('website', ''),
            'email': self.extract_email_from_data(raw_data),
            
            # Location
            'address': raw_data.get('address', ''),
            'city': raw_data.get('city', ''),
            'state': raw_data.get('state', ''),
            'zip_code': raw_data.get('postalCode', ''),
            'country': raw_data.get('country', ''),
            'latitude': raw_data.get('location', {}).get('lat', ''),
            'longitude': raw_data.get('location', {}).get('lng', ''),
            
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
            
            # Metadata
            'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'Google Maps API',
            'raw_data': json.dumps(raw_data)  # Store full raw data for reference
        }
    
    def extract_email_from_data(self, data: Dict) -> str:
        """Try to extract email from various fields in the data"""
        # Check common fields where emails might be stored
        email_fields = ['email', 'contactEmail', 'ownerEmail']
        
        for field in email_fields:
            if field in data and data[field]:
                return data[field]
        
        # Check in website or other text fields
        text_fields = ['website', 'description', 'additionalInfo']
        for field in text_fields:
            if field in data and data[field]:
                text = str(data[field])
                # Simple email regex
                import re
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                if email_match:
                    return email_match.group()
        
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
            'phone_percentage': (with_phone / total_businesses) * 100,
            'website_percentage': (with_website / total_businesses) * 100,
            'email_percentage': (with_email / total_businesses) * 100,
            'address_percentage': (with_address / total_businesses) * 100,
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
        
        print("🗺️ Testing Google Maps extractor...")
        
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