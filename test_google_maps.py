#!/usr/bin/env python3

from google_maps_extractor import GoogleMapsExtractor

def test_google_maps_extractor():
    """Test the Google Maps extractor with the Apify API key"""
    
    # Use the same API key from test.py
    api_key = "apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq"
    
    try:
        # Initialize extractor
        extractor = GoogleMapsExtractor(api_key)
        print("✅ Google Maps extractor initialized successfully")
        
        # Test with Inspira Health Network
        test_companies = ["Inspira Health Network"]
        
        print(f"\n🗺️ Testing Google Maps extractor with: {test_companies}")
        
        def progress_update(progress):
            print(f"Progress: {progress*100:.1f}%")
        
        def status_update(status):
            print(f"Status: {status}")
        
        results = extractor.extract_business_data(
            business_names=test_companies,
            location="New Jersey, USA",
            progress_callback=progress_update,
            status_callback=status_update
        )
        
        print(f"\n✅ Extraction complete! Found {len(results)} business locations")
        
        # Show first result details
        if results:
            first_result = results[0]
            print(f"\n📋 Sample business data:")
            print(f"Name: {first_result.get('business_name', 'N/A')}")
            print(f"Phone: {first_result.get('phone', 'N/A')}")
            print(f"Website: {first_result.get('website', 'N/A')}")
            print(f"Email: {first_result.get('email', 'N/A')}")
            print(f"Address: {first_result.get('address', 'N/A')}")
            print(f"Category: {first_result.get('category', 'N/A')}")
            print(f"Rating: {first_result.get('rating', 'N/A')}")
            
            # Show all available fields
            print(f"\n🔧 Available fields: {list(first_result.keys())}")
        
        # Show summary
        summary = extractor.get_business_summary(results)
        if summary:
            print(f"\n📊 Summary:")
            print(f"- Total businesses: {summary['total_businesses']}")
            print(f"- With phone: {summary['with_phone']} ({summary['phone_percentage']:.1f}%)")
            print(f"- With website: {summary['with_website']} ({summary['website_percentage']:.1f}%)")
            print(f"- With email: {summary['with_email']} ({summary['email_percentage']:.1f}%)")
        
        # Save results
        extractor.save_results_to_file(results, "test_inspira_results.json")
        print("💾 Results saved to test_inspira_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None

if __name__ == "__main__":
    test_google_maps_extractor() 