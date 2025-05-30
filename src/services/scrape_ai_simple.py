"""
Simple AI Scraper - Lightweight fallback for deployment environments
Uses only basic requests and OpenAI API without heavy dependencies
"""
import json
import os
import time
import requests
from typing import Dict, List, Optional, Callable
from dotenv import load_dotenv
from ..utils.database import db_manager

load_dotenv()

def simple_scrape_website(url: str) -> str:
    """Simple website content extraction using requests"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract text content (simple approach)
        content = response.text
        
        # Basic cleanup - remove scripts and styles
        import re
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<[^>]+>', ' ', content)  # Remove HTML tags
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        
        return content[:5000]  # Limit content length
        
    except Exception as e:
        return f"Error fetching content: {str(e)}"

def extract_with_openai(content: str, url: str) -> Dict:
    """Extract contact information using OpenAI API"""
    try:
        openai_key = os.getenv("OPENROUTER_API_KEY")
        if not openai_key:
            return {"error": "OpenAI API key not configured"}
        
        # Prepare the prompt
        prompt = f"""
        Extract contact information from the following website content. 
        Look for names, phone numbers, and email addresses.
        
        Website URL: {url}
        Content: {content}
        
        Return the information in this exact JSON format:
        {{
            "names": ["name1", "name2"],
            "phone_numbers": ["phone1", "phone2"],
            "email_addresses": ["email1", "email2"]
        }}
        
        If no information is found for a category, return an empty list.
        Only include actual contact information, not examples or placeholders.
        """
        
        # Call OpenAI API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Try to parse JSON
            try:
                # Remove markdown formatting if present
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                
                return json.loads(content)
            except:
                # Fallback: try to extract using regex
                import re
                names = re.findall(r'"names":\s*\[(.*?)\]', content)
                phones = re.findall(r'"phone_numbers":\s*\[(.*?)\]', content)
                emails = re.findall(r'"email_addresses":\s*\[(.*?)\]', content)
                
                return {
                    "names": [n.strip('"') for n in names[0].split(',')] if names else [],
                    "phone_numbers": [p.strip('"') for p in phones[0].split(',')] if phones else [],
                    "email_addresses": [e.strip('"') for e in emails[0].split(',')] if emails else []
                }
        else:
            return {"error": f"API call failed: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}

def process_single_link_simple(link: str, search_result_id: int) -> Dict:
    """Process a single link using simple scraping"""
    try:
        print(f"  Simple scraping: {link[:50]}...")
        
        # Get website content
        content = simple_scrape_website(link)
        
        if content.startswith("Error"):
            return {
                'success': False,
                'contact_data': {
                    'scraped_names': None,
                    'scraped_phones': None,
                    'scraped_emails': None,
                    'scraping_status': f"Content Error: {content}",
                    'raw_response': None
                }
            }
        
        # Extract contact info with AI
        extracted_data = extract_with_openai(content, link)
        
        if "error" in extracted_data:
            return {
                'success': False,
                'contact_data': {
                    'scraped_names': None,
                    'scraped_phones': None,
                    'scraped_emails': None,
                    'scraping_status': f"AI Error: {extracted_data['error']}",
                    'raw_response': None
                }
            }
        
        # Format results
        names = "; ".join(extracted_data.get("names", [])) if extracted_data.get("names") else None
        phones = "; ".join(extracted_data.get("phone_numbers", [])) if extracted_data.get("phone_numbers") else None
        emails = "; ".join(extracted_data.get("email_addresses", [])) if extracted_data.get("email_addresses") else None
        
        return {
            'success': True,
            'contact_data': {
                'scraped_names': names,
                'scraped_phones': phones,
                'scraped_emails': emails,
                'scraping_status': 'Success (Simple)',
                'raw_response': json.dumps(extracted_data)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'contact_data': {
                'scraped_names': None,
                'scraped_phones': None,
                'scraped_emails': None,
                'scraping_status': f"Simple Error: {str(e)}",
                'raw_response': None
            }
        }

def process_links_from_database(progress_callback=None, status_callback=None, user_id: int = None):
    """Simple version of link processing for deployment environments"""
    
    # Get unscraped links from database
    data = db_manager.get_unscraped_links(user_id)
    
    if data.empty:
        print("No unscraped links found in database")
        return 0
    
    print(f"Found {len(data)} unscraped links in database")
    print("Using simple scraper (deployment mode)")
    
    total_links = len(data)
    successful_extractions = 0
    
    for index, (_, row) in enumerate(data.iterrows()):
        link = row['link']
        search_result_id = row['id']
        
        if not link or link == 'nan':
            continue
        
        # Update progress
        progress = (index + 1) / total_links
        if progress_callback:
            progress_callback(progress)
        
        if status_callback:
            status_callback(f"Processing {index + 1}/{total_links}: {link[:50]}...")
        
        # Process the link
        result = process_single_link_simple(link, search_result_id)
        
        # Update database
        if result['success']:
            successful_extractions += 1
            
        db_manager.update_scraping_result(
            search_result_id=search_result_id,
            **result['contact_data']
        )
        
        # Small delay
        time.sleep(0.5)
    
    print(f"Simple scraping completed: {successful_extractions}/{total_links} successful")
    return successful_extractions

def get_results_for_download(user_id: int = None):
    """Get all scraped results for download - compatible with enhanced version"""
    return db_manager.get_all_search_results(user_id) 