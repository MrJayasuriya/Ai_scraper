import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "scraper_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create search_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_query TEXT,
                    original_location TEXT,
                    title TEXT,
                    link TEXT UNIQUE,
                    snippet TEXT,
                    source TEXT,
                    address_text TEXT,
                    phone_number_serper TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    attributes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scraped BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create scraped_contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraped_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_result_id INTEGER,
                    scraped_names TEXT,
                    scraped_phones TEXT,
                    scraped_emails TEXT,
                    scraping_status TEXT,
                    raw_response TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (search_result_id) REFERENCES search_results (id)
                )
            """)
            
            conn.commit()
    
    def insert_search_results(self, results: List[Dict]) -> int:
        """Insert search results into the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            inserted_count = 0
            
            for result in results:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO search_results 
                        (original_query, original_location, title, link, snippet, source, 
                         address_text, phone_number_serper, rating, reviews_count, attributes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.get('original_query'),
                        result.get('original_location'),
                        result.get('title'),
                        result.get('link'),
                        result.get('snippet'),
                        result.get('source'),
                        result.get('address_text'),
                        result.get('phone_number_serper'),
                        result.get('rating'),
                        result.get('reviews_count'),
                        json.dumps(result.get('attributes')) if result.get('attributes') else None
                    ))
                    if cursor.rowcount > 0:
                        inserted_count += 1
                except Exception as e:
                    print(f"Error inserting result: {e}")
            
            conn.commit()
            return inserted_count
    
    def get_unscraped_links(self) -> pd.DataFrame:
        """Get all links that haven't been scraped yet"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT id, original_query, original_location, title, link, snippet, 
                       source, address_text, phone_number_serper, rating, reviews_count, attributes
                FROM search_results 
                WHERE scraped = FALSE
                ORDER BY created_at DESC
            """
            return pd.read_sql_query(query, conn)
    
    def get_all_search_results(self) -> pd.DataFrame:
        """Get all search results"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT sr.*, sc.scraped_names, sc.scraped_phones, sc.scraped_emails, 
                       sc.scraping_status, sc.raw_response, sc.scraped_at
                FROM search_results sr
                LEFT JOIN scraped_contacts sc ON sr.id = sc.search_result_id
                ORDER BY sr.created_at DESC
            """
            return pd.read_sql_query(query, conn)
    
    def insert_scraped_contact(self, search_result_id: int, contact_data: Dict):
        """Insert scraped contact data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraped_contacts 
                (search_result_id, scraped_names, scraped_phones, scraped_emails, 
                 scraping_status, raw_response)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                search_result_id,
                contact_data.get('scraped_names'),
                contact_data.get('scraped_phones'),
                contact_data.get('scraped_emails'),
                contact_data.get('scraping_status'),
                contact_data.get('raw_response')
            ))
            
            # Mark search result as scraped
            cursor.execute("""
                UPDATE search_results SET scraped = TRUE WHERE id = ?
            """, (search_result_id,))
            
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total search results
            cursor.execute("SELECT COUNT(*) FROM search_results")
            total_results = cursor.fetchone()[0]
            
            # Scraped results
            cursor.execute("SELECT COUNT(*) FROM search_results WHERE scraped = TRUE")
            scraped_results = cursor.fetchone()[0]
            
            # Successful extractions
            cursor.execute("""
                SELECT COUNT(*) FROM scraped_contacts 
                WHERE scraping_status = 'Success'
            """)
            successful_extractions = cursor.fetchone()[0]
            
            # Contact counts
            cursor.execute("SELECT COUNT(*) FROM scraped_contacts WHERE scraped_names IS NOT NULL")
            names_found = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scraped_contacts WHERE scraped_phones IS NOT NULL")
            phones_found = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scraped_contacts WHERE scraped_emails IS NOT NULL")
            emails_found = cursor.fetchone()[0]
            
            return {
                'total_results': total_results,
                'scraped_results': scraped_results,
                'unscraped_results': total_results - scraped_results,
                'successful_extractions': successful_extractions,
                'names_found': names_found,
                'phones_found': phones_found,
                'emails_found': emails_found
            }
    
    def clear_all_data(self):
        """Clear all data from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scraped_contacts")
            cursor.execute("DELETE FROM search_results")
            conn.commit()

# Create global database manager instance
db_manager = DatabaseManager() 