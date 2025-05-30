import sqlite3
import pandas as pd
import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "scraper_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table for authentication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create user sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create search_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    original_query TEXT,
                    original_location TEXT,
                    title TEXT,
                    link TEXT,
                    snippet TEXT,
                    source TEXT,
                    address_text TEXT,
                    phone_number_serper TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    attributes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scraped BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
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
            
            # Add user_id column to existing search_results if it doesn't exist
            try:
                cursor.execute("SELECT user_id FROM search_results LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE search_results ADD COLUMN user_id INTEGER REFERENCES users(id)")
            
            conn.commit()
    
    # Authentication methods
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Generate a random salt"""
        return secrets.token_hex(32)
    
    def create_user(self, username: str, email: str, password: str) -> Dict:
        """Create a new user account"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return {"success": False, "error": "Username or email already exists"}
            
            # Generate salt and hash password
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt)
                    VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, salt))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return {
                    "success": True, 
                    "user_id": user_id,
                    "message": "User created successfully"
                }
            except Exception as e:
                return {"success": False, "error": f"Error creating user: {str(e)}"}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user credentials"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, password_hash, salt, is_active 
                FROM users 
                WHERE username = ? OR email = ?
            """, (username, username))
            
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": "Invalid username or password"}
            
            user_id, username, email, stored_hash, salt, is_active = user
            
            if not is_active:
                return {"success": False, "error": "Account is deactivated"}
            
            # Verify password
            password_hash = self._hash_password(password, salt)
            if password_hash != stored_hash:
                return {"success": False, "error": "Invalid username or password"}
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                         (datetime.now(), user_id))
            conn.commit()
            
            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "email": email
            }
    
    def create_session(self, user_id: int) -> str:
        """Create a new session for the user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate session token
            session_token = secrets.token_urlsafe(64)
            expires_at = datetime.now() + timedelta(days=30)  # 30 days expiry
            
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, expires_at))
            
            conn.commit()
            return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user info"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.username, u.email, s.expires_at
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.is_active = TRUE AND s.expires_at > ?
            """, (session_token, datetime.now()))
            
            result = cursor.fetchone()
            if result:
                user_id, username, email, expires_at = result
                return {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "expires_at": expires_at
                }
            return None
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user by deactivating session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE session_token = ?
            """, (session_token,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE expires_at < ?
            """, (datetime.now(),))
            
            conn.commit()

    # Modified existing methods to support user isolation
    def insert_search_results(self, results: List[Dict], user_id: int = None) -> int:
        """Insert search results into the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            inserted_count = 0
            
            for result in results:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO search_results 
                        (user_id, original_query, original_location, title, link, snippet, source, 
                         address_text, phone_number_serper, rating, reviews_count, attributes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
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
    
    def get_unscraped_links(self, user_id: int = None) -> pd.DataFrame:
        """Get all links that haven't been scraped yet"""
        with sqlite3.connect(self.db_path) as conn:
            if user_id:
                query = """
                    SELECT id, original_query, original_location, title, link, snippet, 
                           source, address_text, phone_number_serper, rating, reviews_count, attributes
                    FROM search_results 
                    WHERE scraped = FALSE AND (user_id = ? OR user_id IS NULL)
                    ORDER BY created_at DESC
                """
                return pd.read_sql_query(query, conn, params=[user_id])
            else:
                query = """
                    SELECT id, original_query, original_location, title, link, snippet, 
                           source, address_text, phone_number_serper, rating, reviews_count, attributes
                    FROM search_results 
                    WHERE scraped = FALSE
                    ORDER BY created_at DESC
                """
                return pd.read_sql_query(query, conn)
    
    def get_all_search_results(self, user_id: int = None) -> pd.DataFrame:
        """Get all search results"""
        with sqlite3.connect(self.db_path) as conn:
            if user_id:
                query = """
                    SELECT sr.*, sc.scraped_names, sc.scraped_phones, sc.scraped_emails, 
                           sc.scraping_status, sc.raw_response, sc.scraped_at
                    FROM search_results sr
                    LEFT JOIN scraped_contacts sc ON sr.id = sc.search_result_id
                    WHERE sr.user_id = ? OR sr.user_id IS NULL
                    ORDER BY sr.created_at DESC
                """
                return pd.read_sql_query(query, conn, params=[user_id])
            else:
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
    
    def get_statistics(self, user_id: int = None) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if user_id:
                # User-specific statistics
                cursor.execute("SELECT COUNT(*) FROM search_results WHERE user_id = ? OR user_id IS NULL", [user_id])
                total_results = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM search_results WHERE scraped = TRUE AND (user_id = ? OR user_id IS NULL)", [user_id])
                scraped_results = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM scraped_contacts sc
                    JOIN search_results sr ON sc.search_result_id = sr.id
                    WHERE sc.scraping_status = 'Success' AND (sr.user_id = ? OR sr.user_id IS NULL)
                """, [user_id])
                successful_extractions = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM scraped_contacts sc
                    JOIN search_results sr ON sc.search_result_id = sr.id
                    WHERE sc.scraped_names IS NOT NULL AND (sr.user_id = ? OR sr.user_id IS NULL)
                """, [user_id])
                names_found = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM scraped_contacts sc
                    JOIN search_results sr ON sc.search_result_id = sr.id
                    WHERE sc.scraped_phones IS NOT NULL AND (sr.user_id = ? OR sr.user_id IS NULL)
                """, [user_id])
                phones_found = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM scraped_contacts sc
                    JOIN search_results sr ON sc.search_result_id = sr.id
                    WHERE sc.scraped_emails IS NOT NULL AND (sr.user_id = ? OR sr.user_id IS NULL)
                """, [user_id])
                emails_found = cursor.fetchone()[0]
            else:
                # Global statistics (backward compatibility)
                cursor.execute("SELECT COUNT(*) FROM search_results")
                total_results = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM search_results WHERE scraped = TRUE")
                scraped_results = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM scraped_contacts 
                    WHERE scraping_status = 'Success'
                """)
                successful_extractions = cursor.fetchone()[0]
                
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
    
    def clear_all_data(self, user_id: int = None):
        """Clear all data from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if user_id:
                # Clear only user's data
                cursor.execute("""
                    DELETE FROM scraped_contacts 
                    WHERE search_result_id IN (
                        SELECT id FROM search_results WHERE user_id = ?
                    )
                """, [user_id])
                cursor.execute("DELETE FROM search_results WHERE user_id = ?", [user_id])
            else:
                # Clear all data (backward compatibility)
                cursor.execute("DELETE FROM scraped_contacts")
                cursor.execute("DELETE FROM search_results")
            conn.commit()

# Create global database manager instance
db_manager = DatabaseManager() 