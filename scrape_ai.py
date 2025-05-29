import os
from dotenv import load_dotenv
import pandas as pd
import json
import asyncio
import platform
from database import db_manager

# Fix for Windows asyncio subprocess issue
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()
from scrapegraphai.graphs import SmartScraperGraph
from llm_services import get_service

# Get LLM service
llm_service = get_service()

# Define the configuration for the scraping pipeline using OpenRouter
graph_config = {
    "llm": {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": "openai/gpt-3.5-turbo-0613",
        "base_url": "https://openrouter.ai/api/v1"
    },
    "verbose": True,
    "headless": True,
    "browser_type": "chromium",
    "playwright_config": {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions"
        ]
    }
}

def extract_contact_details(scraped_result):
    """Extract contact details from scraped result into structured format"""
    if not scraped_result:
        return {"scraped_names": None, "scraped_phones": None, "scraped_emails": None}
    
    try:
        # Handle both dict and JSON string formats
        if isinstance(scraped_result, str):
            data = json.loads(scraped_result)
        else:
            data = scraped_result
            
        # Extract from nested structure - try multiple possible keys
        content = data.get('content', data)
        
        # Try different possible keys for names
        names = (content.get('names', []) or 
                content.get('name', []) or 
                content.get('contact_names', []) or
                content.get('people', []))
        
        # Try different possible keys for phones
        phones = (content.get('phone_numbers', []) or 
                 content.get('phones', []) or 
                 content.get('contact_phones', []) or
                 content.get('telephone', []))
        
        # Try different possible keys for emails
        emails = (content.get('email_addresses', []) or 
                 content.get('emails', []) or 
                 content.get('contact_emails', []) or
                 content.get('email', []))
        
        # Ensure we have lists
        if not isinstance(names, list):
            names = [names] if names else []
        if not isinstance(phones, list):
            phones = [phones] if phones else []
        if not isinstance(emails, list):
            emails = [emails] if emails else []
        
        return {
            "scraped_names": "; ".join(str(name) for name in names if name) if names else None,
            "scraped_phones": "; ".join(str(phone) for phone in phones if phone) if phones else None,
            "scraped_emails": "; ".join(str(email) for email in emails if email) if emails else None
        }
    except Exception as e:
        print(f"  Warning: Could not parse contact details: {e}")
        return {"scraped_names": None, "scraped_phones": None, "scraped_emails": None}

def process_links_from_database(progress_callback=None, status_callback=None):
    """Process all unscraped links from the database"""
    
    # Get unscraped links from database
    data = db_manager.get_unscraped_links()
    
    if data.empty:
        print("No unscraped links found in database")
        return 0
    
    print(f"Found {len(data)} unscraped links in database")
    
    total_links = len(data)
    successful_extractions = 0
    
    # Process each link
    for index, row in data.iterrows():
        link = row['link']
        search_result_id = row['id']
        
        if link and link != 'nan':
            progress = (index + 1) / total_links
            if progress_callback:
                progress_callback(progress)
            if status_callback:
                status_callback(f"Processing link {index + 1}/{total_links}: {link[:50]}...")
            
            print(f"\nProcessing link {index + 1}/{total_links}: {link}")
            
            try:
                smart_scraper_graph = SmartScraperGraph(
                    prompt="Extract all contact details including names, phone numbers, and email addresses from the source. Return the data in a structured format with keys: names, phone_numbers, email_addresses",
                    source=link,
                    config=graph_config
                )
                result = smart_scraper_graph.run()
                
                # Store raw response
                raw_response = json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
                
                # Extract structured contact details
                contact_details = extract_contact_details(result)
                
                # Prepare contact data for database
                contact_data = {
                    'scraped_names': contact_details['scraped_names'],
                    'scraped_phones': contact_details['scraped_phones'],
                    'scraped_emails': contact_details['scraped_emails'],
                    'scraping_status': 'Success',
                    'raw_response': raw_response
                }
                
                # Insert into database
                db_manager.insert_scraped_contact(search_result_id, contact_data)
                successful_extractions += 1
                
                print(f"  ✓ Extracted:")
                print(f"    Names: {contact_details['scraped_names']}")
                print(f"    Phones: {contact_details['scraped_phones']}")
                print(f"    Emails: {contact_details['scraped_emails']}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ Error processing {link}: {e}")
                
                # Store error in database
                contact_data = {
                    'scraped_names': None,
                    'scraped_phones': None,
                    'scraped_emails': None,
                    'scraping_status': f"Error: {error_msg}",
                    'raw_response': None
                }
                db_manager.insert_scraped_contact(search_result_id, contact_data)
    
    print(f"\n✓ Processing complete!")
    print(f"Processed {total_links} links total")
    print(f"Successful extractions: {successful_extractions}/{total_links}")
    
    return successful_extractions

def get_results_for_download():
    """Get all results formatted for Excel download"""
    results_df = db_manager.get_all_search_results()
    
    # Reorder columns for better readability
    column_order = ['original_query', 'original_location', 'title', 'link', 
                    'scraped_names', 'scraped_phones', 'scraped_emails', 'scraping_status',
                    'snippet', 'source', 'address_text', 'phone_number_serper',
                    'rating', 'reviews_count', 'attributes', 'raw_response', 'scraped_at']

    # Only include columns that exist in the dataframe
    existing_columns = [col for col in column_order if col in results_df.columns]
    remaining_columns = [col for col in results_df.columns if col not in existing_columns]
    final_columns = existing_columns + remaining_columns
    results_df = results_df[final_columns]
    
    return results_df

if __name__ == "__main__":
    # Process links from database
    successful_count = process_links_from_database()
    
    # Get results and save to Excel for local testing
    results_df = get_results_for_download()
    
    if not results_df.empty:
        output_file = "Final_Results_AI_scrape_data.xlsx"
        results_df.to_excel(output_file, index=False)
        print(f"\n✓ Results saved to {output_file}")
        
        # Show summary
        stats = db_manager.get_statistics()
        print(f"\nDatabase Summary:")
        print(f"  Total results in database: {stats['total_results']}")
        print(f"  Scraped results: {stats['scraped_results']}")
        print(f"  Successful extractions: {stats['successful_extractions']}")
        print(f"  Names found: {stats['names_found']}")
        print(f"  Phone numbers found: {stats['phones_found']}")
        print(f"  Email addresses found: {stats['emails_found']}")
    else:
        print("No results found in database")