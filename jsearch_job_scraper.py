#!/usr/bin/env python3

import requests
import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class JSearchJobScraper:
    """Job scraper using JSearch RapidAPI - Much more reliable than LinkedIn scraping"""
    
    def __init__(self, rapidapi_key: str = None):
        self.rapidapi_key = rapidapi_key or os.getenv("RAPIDAPI_KEY")
        if not self.rapidapi_key:
            raise ValueError("RapidAPI key is required. Set RAPIDAPI_KEY environment variable.")
        
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
    
    def search_jobs(self, 
                   query: str = "software engineer",
                   location: str = "United States", 
                   page: int = 1,
                   num_pages: int = 1,
                   country: str = "us",
                   date_posted: str = "all",
                   employment_types: str = "FULLTIME,PARTTIME",
                   job_requirements: str = "under_3_years_experience,more_than_3_years_experience",
                   remote_jobs_only: bool = False,
                   platform: str = None,
                   company_types: str = None,
                   employer_website: bool = None) -> Dict[str, Any]:
        """
        Search for jobs using JSearch API
        
        Args:
            query: Job search query (e.g., "python developer", "data scientist")
            location: Location to search in (e.g., "New York, NY", "San Francisco")
            page: Page number to retrieve (starts from 1)
            num_pages: Number of pages to retrieve (max 20)
            country: Country code (us, uk, ca, etc.)
            date_posted: Filter by date (all, today, 3days, week, month)
            employment_types: FULLTIME, PARTTIME, CONTRACTOR, INTERN
            job_requirements: under_3_years_experience, more_than_3_years_experience, no_experience, no_degree
            remote_jobs_only: True to only return remote jobs
            platform: Specific platform to search (linkedin, indeed, glassdoor, ziprecruiter, etc.)
            company_types: Company size types to include
            employer_website: Filter for employers with websites
        """
        
        # Build query string with platform specification
        if location.lower() != "remote" and not remote_jobs_only:
            if platform:
                search_query = f"{query} in {location} via {platform}"
            else:
                search_query = f"{query} in {location}"
        else:
            if platform:
                search_query = f"remote {query} via {platform}"
            else:
                search_query = f"remote {query}"
        
        querystring = {
            "query": search_query,
            "page": str(page),
            "num_pages": str(min(num_pages, 20)),  # API limit
            "country": country,
            "date_posted": date_posted
        }
        
        # Add optional filters
        if employment_types:
            querystring["employment_types"] = employment_types
        if job_requirements:
            querystring["job_requirements"] = job_requirements
        if remote_jobs_only:
            querystring["remote_jobs_only"] = "true"
        if company_types:
            querystring["company_types"] = company_types
        if employer_website is not None:
            querystring["employer_website"] = "true" if employer_website else "false"
        
        try:
            print(f"🔍 Searching jobs: {search_query}")
            print(f"📋 Parameters: {querystring}")
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=self.headers,
                params=querystring,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs_found = len(data.get('data', []))
                print(f"✅ Found {jobs_found} jobs successfully")
                return data
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return {"error": str(e)}
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific job"""
        querystring = {"job_id": job_id}
        
        try:
            response = requests.get(
                f"{self.base_url}/job-details",
                headers=self.headers,
                params=querystring,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned status code {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def search_multiple_locations(self, 
                                 query: str,
                                 locations: List[str],
                                 max_results_per_location: int = 10) -> List[Dict]:
        """Search jobs across multiple locations"""
        all_jobs = []
        
        for location in locations:
            print(f"\n🌍 Searching in {location}...")
            results = self.search_jobs(
                query=query,
                location=location,
                num_pages=max(1, max_results_per_location // 10)
            )
            
            if "data" in results:
                jobs = results["data"][:max_results_per_location]
                for job in jobs:
                    job["search_location"] = location  # Add metadata
                all_jobs.extend(jobs)
        
        return all_jobs
    
    def search_multiple_queries(self,
                               queries: List[str],
                               location: str = "United States",
                               max_results_per_query: int = 10) -> List[Dict]:
        """Search multiple job types in one location"""
        all_jobs = []
        
        for query in queries:
            print(f"\n🔍 Searching for {query}...")
            results = self.search_jobs(
                query=query,
                location=location,
                num_pages=max(1, max_results_per_query // 10)
            )
            
            if "data" in results:
                jobs = results["data"][:max_results_per_query]
                for job in jobs:
                    job["search_query"] = query  # Add metadata
                all_jobs.extend(jobs)
        
        return all_jobs
    
    def filter_jobs(self, jobs: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """
        Apply custom filters to job results including employee count and review filters
        
        Args:
            jobs: List of job dictionaries
            filters: Dictionary containing filter criteria:
                - min_salary: Minimum salary threshold
                - max_salary: Maximum salary threshold
                - excluded_companies: List of company names to exclude
                - required_keywords: List of keywords that must be present
                - min_employees: Minimum number of employees
                - max_employees: Maximum number of employees
                - min_reviews: Minimum Google review count
                - min_rating: Minimum company rating
                - company_types: List of preferred company types
        """
        filtered_jobs = []
        
        for job in jobs:
            include_job = True
            
            # Salary filters
            if filters.get("min_salary"):
                salary = job.get("job_salary_max", 0) or job.get("job_salary_min", 0)
                if salary and salary < filters["min_salary"]:
                    include_job = False
            
            if filters.get("max_salary"):
                salary = job.get("job_salary_min", float('inf')) or job.get("job_salary_max", float('inf'))
                if salary and salary > filters["max_salary"]:
                    include_job = False
            
            # Company filter
            if filters.get("excluded_companies"):
                company = job.get("employer_name", "").lower()
                if any(excluded.lower() in company for excluded in filters["excluded_companies"]):
                    include_job = False
            
            # Keywords filter
            if filters.get("required_keywords"):
                job_text = f"{job.get('job_title', '')} {job.get('job_description', '')}".lower()
                if not any(keyword.lower() in job_text for keyword in filters["required_keywords"]):
                    include_job = False
            
            # Employee count filters
            if filters.get("min_employees") or filters.get("max_employees"):
                # Check various fields that might contain employee info
                employee_count = self._extract_employee_count(job)
                
                if filters.get("min_employees") and employee_count:
                    if employee_count < filters["min_employees"]:
                        include_job = False
                
                if filters.get("max_employees") and employee_count:
                    if employee_count > filters["max_employees"]:
                        include_job = False
            
            # Review count filter
            if filters.get("min_reviews"):
                review_count = self._extract_review_count(job)
                if review_count is not None and review_count < filters["min_reviews"]:
                    include_job = False
            
            # Company rating filter
            if filters.get("min_rating"):
                rating = self._extract_company_rating(job)
                if rating is not None and rating < filters["min_rating"]:
                    include_job = False
            
            # Company type filter
            if filters.get("company_types"):
                company_type = job.get("employer_company_type", "").lower()
                if company_type and not any(ct.lower() in company_type for ct in filters["company_types"]):
                    include_job = False
            
            if include_job:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _extract_employee_count(self, job: Dict) -> Optional[int]:
        """
        Extract employee count from job data
        Looks in various fields that might contain company size information
        """
        # Direct fields that might contain employee count
        employee_fields = [
            "employer_employees",
            "employer_employee_count", 
            "employer_size",
            "company_size",
            "employees"
        ]
        
        for field in employee_fields:
            if field in job and job[field]:
                try:
                    # Handle different formats
                    value = job[field]
                    if isinstance(value, int):
                        return value
                    elif isinstance(value, str):
                        # Parse strings like "100-500", "1000+", "50-100 employees"
                        return self._parse_employee_range(value)
                except:
                    continue
        
        # Check company description for size indicators
        description = job.get("employer_description", "") or ""
        if description:
            return self._parse_employee_range(description)
        
        return None
    
    def _parse_employee_range(self, text: str) -> Optional[int]:
        """Parse employee count from text like '100-500', '1000+', 'small company'"""
        import re
        
        text = text.lower()
        
        # Handle specific patterns
        if "startup" in text or "small" in text:
            return 50  # Assume small company
        elif "enterprise" in text or "large" in text:
            return 5000  # Assume large company
        elif "medium" in text or "mid-size" in text:
            return 500  # Assume medium company
        
        # Extract numbers from ranges like "100-500" or "1000+"
        numbers = re.findall(r'\d+', text)
        if numbers:
            nums = [int(n) for n in numbers]
            if len(nums) >= 2:
                # Take average of range
                return sum(nums) // len(nums)
            elif len(nums) == 1:
                return nums[0]
        
        return None
    
    def _extract_review_count(self, job: Dict) -> Optional[int]:
        """Extract Google review count from job data"""
        # Fields that might contain review information
        review_fields = [
            "employer_reviews",
            "employer_review_count",
            "employer_google_reviews",
            "company_reviews",
            "google_reviews"
        ]
        
        for field in review_fields:
            if field in job and job[field]:
                try:
                    value = job[field]
                    if isinstance(value, int):
                        return value
                    elif isinstance(value, str):
                        # Extract number from strings like "150 reviews"
                        import re
                        numbers = re.findall(r'\d+', value)
                        if numbers:
                            return int(numbers[0])
                except:
                    continue
        
        return None
    
    def _extract_company_rating(self, job: Dict) -> Optional[float]:
        """Extract company rating from job data"""
        # Fields that might contain rating information
        rating_fields = [
            "employer_rating",
            "employer_glassdoor_rating", 
            "company_rating",
            "glassdoor_rating"
        ]
        
        for field in rating_fields:
            if field in job and job[field]:
                try:
                    return float(job[field])
                except:
                    continue
        
        return None
    
    def get_company_size_ranges(self) -> List[Dict[str, Any]]:
        """Get predefined company size ranges for filtering"""
        return [
            {"label": "Startup (1-50)", "min": 1, "max": 50},
            {"label": "Small (51-200)", "min": 51, "max": 200},
            {"label": "Medium (201-1000)", "min": 201, "max": 1000},
            {"label": "Large (1001-5000)", "min": 1001, "max": 5000},
            {"label": "Enterprise (5000+)", "min": 5001, "max": None}
        ]
    
    def save_results(self, jobs: List[Dict], filename: str = "jsearch_jobs.json"):
        """Save job results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def get_available_platforms(self) -> List[str]:
        """Get list of supported job platforms"""
        return [
            "linkedin",
            "indeed", 
            "glassdoor",
            "ziprecruiter",
            "monster",
            "careerbuilder",
            "dice",
            "simplyhired",
            "jobscom",
            "flexjobs"
        ]
    
    def get_available_countries(self) -> List[str]:
        """Get list of supported countries"""
        return ["us", "uk", "ca", "au", "de", "fr", "in", "sg", "ae"]
    
    def get_employment_types(self) -> List[str]:
        """Get available employment types"""
        return ["FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"]
    
    def get_date_filters(self) -> List[str]:
        """Get available date filters"""
        return ["all", "today", "3days", "week", "month"]
    
    def get_company_types(self) -> List[str]:
        """Get available company types"""
        return ["startup", "public", "private", "nonprofit", "government"]
    
    def extract_companies_from_jobs(self, jobs_data: List[Dict], include_duplicates: bool = False) -> List[Dict]:
        """
        Extract unique company information from job search results
        
        Args:
            jobs_data: List of job dictionaries from JSearch API
            include_duplicates: Whether to include duplicate companies (default: False)
            
        Returns:
            List of company dictionaries with structured data
        """
        companies = {}
        company_jobs = {}
        
        for job in jobs_data:
            company_name = job.get('employer_name', '').strip()
            
            if not company_name or company_name.lower() in ['unknown', 'not specified', 'n/a']:
                continue
                
            # Use company name as key for deduplication
            company_key = company_name.lower()
            
            if company_key not in companies:
                # Extract company information
                companies[company_key] = {
                    'company_name': company_name,
                    'company_website': job.get('employer_website', ''),
                    'company_logo': job.get('employer_logo', ''),
                    'company_type': job.get('employer_company_type', ''),
                    'company_reviews': job.get('employer_reviews', ''),
                    'company_rating': job.get('employer_rating', ''),
                    'glassdoor_rating': job.get('employer_glassdoor_rating', ''),
                    'company_size': job.get('employer_employees', '') or job.get('employer_size', ''),
                    'headquarters': job.get('employer_headquarters', ''),
                    'industry': job.get('employer_industry', ''),
                    'founded_year': job.get('employer_founded', ''),
                    'description': job.get('employer_description', ''),
                    'job_count': 0,
                    'job_titles': [],
                    'job_locations': set(),
                    'salary_ranges': [],
                    'job_links': [],
                    'first_seen_date': job.get('job_posted_at_datetime_utc', ''),
                    'last_seen_date': job.get('job_posted_at_datetime_utc', ''),
                    'employment_types': set(),
                    'experience_levels': set()
                }
                company_jobs[company_key] = []
            
            # Update company statistics
            companies[company_key]['job_count'] += 1
            company_jobs[company_key].append(job)
            
            # Collect job information
            if job.get('job_title'):
                companies[company_key]['job_titles'].append(job['job_title'])
            
            # Location information
            location_parts = []
            if job.get('job_city'): location_parts.append(job['job_city'])
            if job.get('job_state'): location_parts.append(job['job_state'])
            if job.get('job_country'): location_parts.append(job['job_country'])
            if location_parts:
                companies[company_key]['job_locations'].add(', '.join(location_parts))
            
            # Salary information
            salary_min = job.get('job_salary_min')
            salary_max = job.get('job_salary_max')
            salary_currency = job.get('job_salary_currency', 'USD')
            
            if salary_min or salary_max:
                salary_range = f"{salary_min or 'N/A'} - {salary_max or 'N/A'} {salary_currency}"
                companies[company_key]['salary_ranges'].append(salary_range)
            
            # Job links
            if job.get('job_apply_link'):
                companies[company_key]['job_links'].append(job['job_apply_link'])
            
            # Employment types and experience
            if job.get('job_employment_type'):
                companies[company_key]['employment_types'].add(job['job_employment_type'])
            
            if job.get('job_required_experience'):
                companies[company_key]['experience_levels'].add(job['job_required_experience'])
            
            # Update last seen date
            job_date = job.get('job_posted_at_datetime_utc', '')
            if job_date and job_date > companies[company_key]['last_seen_date']:
                companies[company_key]['last_seen_date'] = job_date
        
        # Convert sets to strings and finalize data
        final_companies = []
        for company_key, company_data in companies.items():
            # Convert sets to comma-separated strings
            company_data['job_locations'] = '; '.join(sorted(company_data['job_locations']))
            company_data['employment_types'] = '; '.join(sorted(company_data['employment_types']))
            company_data['experience_levels'] = '; '.join(sorted(company_data['experience_levels']))
            
            # Limit job titles to avoid overflow
            unique_titles = list(set(company_data['job_titles']))[:10]
            company_data['job_titles'] = '; '.join(unique_titles)
            
            # Salary ranges - get unique values
            unique_salaries = list(set(company_data['salary_ranges']))[:5]
            company_data['salary_ranges'] = '; '.join(unique_salaries)
            
            # Job links - limit to avoid overflow
            company_data['job_links'] = '; '.join(company_data['job_links'][:5])
            
            # Add company search status for next phase
            company_data['contact_extraction_status'] = 'Pending'
            company_data['contact_extraction_priority'] = 'High' if company_data['job_count'] > 1 else 'Normal'
            
            final_companies.append(company_data)
        
        # Sort by job count (companies with more jobs first)
        final_companies.sort(key=lambda x: x['job_count'], reverse=True)
        
        return final_companies
    
    def create_companies_excel(self, companies_data: List[Dict], search_query: str = "", search_location: str = "") -> bytes:
        """
        Create a professionally formatted Excel file for company data
        
        Args:
            companies_data: List of company dictionaries
            search_query: Original job search query
            search_location: Original search location
            
        Returns:
            Excel file as bytes
        """
        import pandas as pd
        from io import BytesIO
        
        if not companies_data:
            return None
        
        # Create DataFrame with organized columns
        companies_df = pd.DataFrame(companies_data)
        
        # Define column order and formatting
        excel_columns = {
            # Company Identification
            'Company Name': 'company_name',
            'Company Website': 'company_website',
            'Company Type': 'company_type',
            'Industry': 'industry',
            
            # Company Details
            'Company Size': 'company_size',
            'Founded Year': 'founded_year',
            'Headquarters': 'headquarters',
            'Description': 'description',
            
            # Ratings & Reviews
            'Company Rating': 'company_rating',
            'Glassdoor Rating': 'glassdoor_rating',
            'Review Count': 'company_reviews',
            
            # Job Information
            'Total Jobs Found': 'job_count',
            'Job Titles': 'job_titles',
            'Job Locations': 'job_locations',
            'Salary Ranges': 'salary_ranges',
            'Employment Types': 'employment_types',
            'Experience Levels': 'experience_levels',
            
            # Tracking Information
            'First Job Posted': 'first_seen_date',
            'Latest Job Posted': 'last_seen_date',
            'Contact Extraction Status': 'contact_extraction_status',
            'Priority': 'contact_extraction_priority',
            
            # Reference Links
            'Sample Job Links': 'job_links',
            'Company Logo URL': 'company_logo'
        }
        
        # Create organized DataFrame
        organized_data = {}
        for excel_col, data_col in excel_columns.items():
            if data_col in companies_df.columns:
                column_data = companies_df[data_col].copy()
                
                # Clean and format specific columns
                if data_col in ['first_seen_date', 'last_seen_date']:
                    column_data = pd.to_datetime(column_data, errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                elif data_col == 'description':
                    # Limit description length
                    column_data = column_data.astype(str).apply(lambda x: x[:300] + '...' if len(str(x)) > 300 else x)
                elif data_col in ['company_rating', 'glassdoor_rating']:
                    # Format ratings
                    column_data = column_data.apply(lambda x: f"{float(x):.1f}" if x and str(x) != 'nan' else '')
                
                organized_data[excel_col] = column_data
            else:
                organized_data[excel_col] = [''] * len(companies_df)
        
        excel_df = pd.DataFrame(organized_data)
        
        # Create metadata
        metadata = {
            'Search Query': [search_query],
            'Search Location': [search_location],
            'Companies Found': [len(companies_df)],
            'Total Jobs Analyzed': [companies_df['job_count'].sum()],
            'Export Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Data Source': ['JSearch API - Company Analysis'],
            'With Websites': [len(excel_df[excel_df['Company Website'] != ''])],
            'High Priority (Multiple Jobs)': [len(excel_df[excel_df['Priority'] == 'High'])],
            'Average Jobs per Company': [companies_df['job_count'].mean()],
            'Companies with Ratings': [len(excel_df[(excel_df['Company Rating'] != '') | (excel_df['Glassdoor Rating'] != '')])]
        }
        metadata_df = pd.DataFrame(metadata)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main company data
            excel_df.to_excel(writer, sheet_name='Companies_Data', index=False)
            
            # Write metadata
            metadata_df.to_excel(writer, sheet_name='Search_Summary', index=False)
            
            # Write company statistics
            stats_data = {
                'Company Size Distribution': companies_df['company_size'].value_counts().head(10).to_dict(),
                'Industry Distribution': companies_df['industry'].value_counts().head(10).to_dict(),
                'Employment Types': companies_df['employment_types'].str.split('; ').explode().value_counts().head(10).to_dict()
            }
            
            # Convert stats to DataFrame format
            stats_rows = []
            for category, data in stats_data.items():
                for item, count in data.items():
                    if item and str(item) != 'nan':
                        stats_rows.append({'Category': category, 'Item': item, 'Count': count})
            
            if stats_rows:
                stats_df = pd.DataFrame(stats_rows)
                stats_df.to_excel(writer, sheet_name='Company_Statistics', index=False)
            
            # Format the main sheet
            workbook = writer.book
            worksheet = writer.sheets['Companies_Data']
            
            # Auto-adjust column widths
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells if cell.value)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
            
            # Add header formatting
            from openpyxl.styles import Font, PatternFill, Alignment
            
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Freeze the header row
            worksheet.freeze_panes = 'A2'
        
        return output.getvalue()


# Job search templates for common use cases
JOB_TEMPLATES = {
    "tech_remote": {
        "queries": ["software engineer", "python developer", "data scientist", "frontend developer"],
        "location": "remote",
        "employment_types": "FULLTIME",
        "remote_jobs_only": True,
        "platform": None  # Search all platforms
    },
    
    "linkedin_tech": {
        "queries": ["software engineer", "backend developer", "full stack developer"],
        "location": "United States",
        "employment_types": "FULLTIME,PARTTIME",
        "date_posted": "week",
        "platform": "linkedin"  # LinkedIn specific
    },
    
    "indeed_jobs": {
        "queries": ["data scientist", "data engineer", "machine learning engineer"],
        "location": "United States", 
        "employment_types": "FULLTIME",
        "date_posted": "week",
        "platform": "indeed"  # Indeed specific
    },
    
    "glassdoor_salary": {
        "queries": ["senior software engineer", "staff engineer", "principal engineer"],
        "location": "San Francisco, CA",
        "employment_types": "FULLTIME",
        "job_requirements": "more_than_3_years_experience",
        "platform": "glassdoor"  # Glassdoor for salary data
    },
    
    "entry_level": {
        "queries": ["junior developer", "entry level engineer", "software engineer intern"],
        "location": "United States",
        "employment_types": "FULLTIME,INTERN",
        "job_requirements": "under_3_years_experience,no_experience",
        "platform": None  # Search all platforms
    }
}


# Example usage and testing
if __name__ == "__main__":
    # Test the scraper
    try:
        scraper = JSearchJobScraper()
        
        # Test 1: Basic search
        print("=== Test 1: Basic Job Search ===")
        results = scraper.search_jobs(
            query="python developer",
            location="San Francisco, CA",
            num_pages=1,
            date_posted="week"
        )
        
        if "data" in results:
            jobs = results["data"]
            print(f"Found {len(jobs)} jobs")
            
            # Show first job details
            if jobs:
                first_job = jobs[0]
                print(f"Sample job: {first_job.get('job_title')} at {first_job.get('employer_name')}")
                print(f"Location: {first_job.get('job_city')}, {first_job.get('job_state')}")
                print(f"Salary: ${first_job.get('job_salary_min', 'N/A')}-${first_job.get('job_salary_max', 'N/A')}")
            
            scraper.save_results(jobs, "test_python_jobs.json")
        
        # Test 2: Remote jobs
        print("\n=== Test 2: Remote Jobs ===")
        remote_results = scraper.search_jobs(
            query="data scientist",
            location="remote",
            remote_jobs_only=True,
            num_pages=1
        )
        
        if "data" in remote_results:
            remote_jobs = remote_results["data"]
            print(f"Found {len(remote_jobs)} remote jobs")
            scraper.save_results(remote_jobs, "test_remote_jobs.json")
        
        # Test 3: Multiple locations
        print("\n=== Test 3: Multiple Locations ===")
        multi_location_jobs = scraper.search_multiple_locations(
            query="software engineer",
            locations=["New York, NY", "Austin, TX", "Seattle, WA"],
            max_results_per_location=5
        )
        print(f"Found {len(multi_location_jobs)} jobs across multiple locations")
        scraper.save_results(multi_location_jobs, "test_multi_location_jobs.json")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("Make sure to set RAPIDAPI_KEY environment variable") 