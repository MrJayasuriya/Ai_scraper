"""
Enhanced AI Scraper with retry mechanism, concurrent processing, and better error handling
"""
import json
import os
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable
from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
from llm_services import get_service
from database import db_manager

load_dotenv()

# Configuration
MAX_CONCURRENT_SCRAPES = int(os.getenv("MAX_CONCURRENT_SCRAPES", "3"))
SCRAPE_DELAY_SECONDS = float(os.getenv("SCRAPE_DELAY_SECONDS", "1.0"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# Get LLM service
llm_service = get_service()

# Enhanced configuration for the scraping pipeline
graph_config = {
    "llm": {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo-0613"),
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    },
    "verbose": False,  # Reduced verbosity for cleaner output
    "headless": True,
    "browser_type": "chromium",
    "playwright_config": {
        "headless": True,
        "timeout": 30000,  # 30 second timeout
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor"
        ]
    }
}

def extract_contact_details(scraped_result: Dict) -> Dict[str, Optional[str]]:
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
                content.get('people', []) or
                content.get('owners', []) or
                content.get('staff', []))
        
        # Try different possible keys for phones
        phones = (content.get('phone_numbers', []) or 
                 content.get('phones', []) or 
                 content.get('contact_phones', []) or
                 content.get('telephone', []) or
                 content.get('phone', []) or
                 content.get('tel', []))
        
        # Try different possible keys for emails
        emails = (content.get('email_addresses', []) or 
                 content.get('emails', []) or 
                 content.get('contact_emails', []) or
                 content.get('email', []) or
                 content.get('mail', []))
        
        # Ensure we have lists and clean data
        names = _clean_contact_list(names)
        phones = _clean_contact_list(phones)
        emails = _clean_contact_list(emails)
        
        return {
            "scraped_names": "; ".join(names) if names else None,
            "scraped_phones": "; ".join(phones) if phones else None,
            "scraped_emails": "; ".join(emails) if emails else None
        }
    except Exception as e:
        print(f"  Warning: Could not parse contact details: {e}")
        return {"scraped_names": None, "scraped_phones": None, "scraped_emails": None}

def _clean_contact_list(items) -> List[str]:
    """Clean and validate contact list items"""
    if not items:
        return []
    
    if not isinstance(items, list):
        items = [items] if items else []
    
    # Clean and filter items
    cleaned = []
    for item in items:
        if item and str(item).strip() and str(item).lower() not in ['none', 'null', 'n/a', '']:
            cleaned.append(str(item).strip())
    
    return list(set(cleaned))  # Remove duplicates

def scrape_single_link_with_retry(link: str, search_result_id: int, max_retries: int = MAX_RETRIES) -> Dict:
    """Scrape a single link with retry mechanism"""
    for attempt in range(max_retries + 1):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries + 1} for: {link[:50]}...")
            
            smart_scraper_graph = SmartScraperGraph(
                prompt="""Extract all contact details, including names, phone numbers, and email addresses, from all pages of the provided website, such as the homepage, About page, Contact Us page, footer, header, team pages, or any other relevant sections. Search for contact information in text, HTML attributes (e.g., 'mailto:' links, 'tel:' links), meta tags, and structured data (e.g., schema.org markup). Include contact details for individuals, organizations, or departments when available. Handle variations in formatting (e.g., phone numbers with or without country codes, emails in plain text or linked). Return the data in a structured JSON format with the following keys: `names`, `phone_numbers`, `email_addresses`, each containing a list of unique values. If no contact information is found for a category, return an empty list for that key. Exclude any irrelevant or duplicate entries, and ensure the data is clean and properly formatted.
                Example output:
                {
                "names": ["John Doe", "Jane Smith"],
                "phone_numbers": ["+1-555-123-4567", "800-555-7890"],
                "email_addresses": ["contact@example.com", "support@website.org"]
                }""",
                source=link,
                config=graph_config
            )
            
            result = smart_scraper_graph.run()
            
            # Store raw response
            raw_response = json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
            
            # Extract structured contact details
            contact_details = extract_contact_details(result)
            
            return {
                'success': True,
                'contact_data': {
                    'scraped_names': contact_details['scraped_names'],
                    'scraped_phones': contact_details['scraped_phones'],
                    'scraped_emails': contact_details['scraped_emails'],
                    'scraping_status': 'Success',
                    'raw_response': raw_response
                },
                'contact_details': contact_details
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt < max_retries:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                return {
                    'success': False,
                    'contact_data': {
                        'scraped_names': None,
                        'scraped_phones': None,
                        'scraped_emails': None,
                        'scraping_status': f"Error after {max_retries + 1} attempts: {error_msg}",
                        'raw_response': None
                    },
                    'error': error_msg
                }

def process_links_concurrent(progress_callback=None, status_callback=None, max_workers: int = MAX_CONCURRENT_SCRAPES):
    """Process links with concurrent execution for better performance"""
    
    # Get unscraped links from database
    data = db_manager.get_unscraped_links()
    
    if data.empty:
        print("No unscraped links found in database")
        return 0
    
    print(f"Found {len(data)} unscraped links in database")
    print(f"Processing with {max_workers} concurrent workers")
    
    total_links = len(data)
    successful_extractions = 0
    processed = 0
    
    # Convert to list of tuples for easier processing
    links_to_process = [(row['link'], row['id']) for _, row in data.iterrows() 
                       if row['link'] and row['link'] != 'nan']
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_link = {
            executor.submit(scrape_single_link_with_retry, link, search_id): (link, search_id)
            for link, search_id in links_to_process
        }
        
        # Process completed tasks
        for future in as_completed(future_to_link):
            link, search_result_id = future_to_link[future]
            processed += 1
            
            progress = processed / total_links
            if progress_callback:
                progress_callback(progress)
            if status_callback:
                status_callback(f"Processing link {processed}/{total_links}: {link[:50]}...")
            
            try:
                result = future.result()
                
                # Insert into database
                db_manager.insert_scraped_contact(search_result_id, result['contact_data'])
                
                if result['success']:
                    successful_extractions += 1
                    contact_details = result['contact_details']
                    print(f"  ✓ Extracted from {link[:50]}:")
                    print(f"    Names: {contact_details['scraped_names']}")
                    print(f"    Phones: {contact_details['scraped_phones']}")
                    print(f"    Emails: {contact_details['scraped_emails']}")
                else:
                    print(f"  ✗ Failed to extract from {link[:50]}: {result.get('error', 'Unknown error')}")
                
                # Add delay between requests to respect rate limits
                time.sleep(SCRAPE_DELAY_SECONDS)
                
            except Exception as e:
                print(f"  ✗ Unexpected error processing {link}: {e}")
                # Still insert error record
                error_data = {
                    'scraped_names': None,
                    'scraped_phones': None,
                    'scraped_emails': None,
                    'scraping_status': f"Unexpected error: {str(e)}",
                    'raw_response': None
                }
                db_manager.insert_scraped_contact(search_result_id, error_data)
    
    print(f"\n✓ Concurrent processing complete!")
    print(f"Processed {total_links} links total")
    print(f"Successful extractions: {successful_extractions}/{total_links}")
    print(f"Success rate: {(successful_extractions/total_links)*100:.1f}%")
    
    return successful_extractions

def process_links_from_database(progress_callback=None, status_callback=None, use_concurrent=True):
    """Process all unscraped links from the database with enhanced features"""
    
    if use_concurrent and MAX_CONCURRENT_SCRAPES > 1:
        return process_links_concurrent(progress_callback, status_callback)
    else:
        # Fallback to sequential processing
        return _process_links_sequential(progress_callback, status_callback)

def _process_links_sequential(progress_callback=None, status_callback=None):
    """Sequential processing fallback"""
    data = db_manager.get_unscraped_links()
    
    if data.empty:
        print("No unscraped links found in database")
        return 0
    
    total_links = len(data)
    successful_extractions = 0
    
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
            
            result = scrape_single_link_with_retry(link, search_result_id)
            db_manager.insert_scraped_contact(search_result_id, result['contact_data'])
            
            if result['success']:
                successful_extractions += 1
                contact_details = result['contact_details']
                print(f"  ✓ Extracted:")
                print(f"    Names: {contact_details['scraped_names']}")
                print(f"    Phones: {contact_details['scraped_phones']}")
                print(f"    Emails: {contact_details['scraped_emails']}")
    
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
    print("🚀 Starting Enhanced AI Scraper")
    print(f"Configuration:")
    print(f"  - Max concurrent scrapes: {MAX_CONCURRENT_SCRAPES}")
    print(f"  - Delay between requests: {SCRAPE_DELAY_SECONDS}s")
    print(f"  - Max retries per link: {MAX_RETRIES}")
    
    # Process links from database
    successful_count = process_links_from_database()
    
    # Get results and save to Excel for local testing
    results_df = get_results_for_download()
    
    if not results_df.empty:
        output_file = "Enhanced_AI_Scrape_Results.xlsx"
        results_df.to_excel(output_file, index=False)
        print(f"\n✓ Results saved to {output_file}")
        
        # Show summary
        stats = db_manager.get_statistics()
        print(f"\nDatabase Summary:")
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    else:
        print("No results found in database") 