# Scraper Configuration File
# Add new scrapers here without changing the main code

SCRAPER_CONFIGS = {
    "linkedin_free": {
        "actor_id": "gdbRh93zn42kBYDyS",
        "description": "Direct LinkedIn URL scraper - Higher success rate",
        "requires_payment": False,
        "monthly_cost": "Free",
        "default_params": {
            "searchUrl": "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=United%20States&locationId=&geoId=103644278&f_TPR=&f_JT=F&f_WT=3%2C2&position=1&pageNum=0",
            "scrapeJobDetails": True,
            "scrapeSkills": False,
            "scrapeCompany": True,
            "count": 25,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyCountry": "US"
            }
        }
    },
    
    "linkedin_premium": {
        "actor_id": "BHzefUZlZRKWxkTck",
        "default_params": {
            "title": "",
            "location": "United States",
            "companyName": ["Google", "Microsoft"],
            "companyId": ["76987811", "1815218"],
            "publishedAt": "",
            "rows": 50,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }
        },
        "requires_payment": True
    },
    
    "linkedin_alternative": {
        "actor_id": "misceres/linkedin-jobs-scraper",
        "description": "Alternative LinkedIn job scraper - May have better success rate",
        "requires_payment": False,
        "monthly_cost": "Free (limited runs)",
        "default_params": {
            "queries": ["software engineer"],
            "locations": ["United States"],
            "maxResults": 10,
            "delay": 3000,
            "stealth": True
        }
    },
    
    "linkedin_basic": {
        "actor_id": "jakubdrobnik/linkedin-job-scraper",
        "description": "Basic LinkedIn scraper - Simple and reliable",
        "requires_payment": False,
        "monthly_cost": "Free (limited)",
        "default_params": {
            "search": "software engineer",
            "location": "United States",
            "count": 10,
            "delay": 2500
        }
    },
    
    "linkedin_no_cookies": {
        "actor_id": "apimaestro/linkedin-jobs-scraper-api",
        "default_params": {
            "keywords": "Software Engineer",
            "location": "United States",
            "datePosted": "week",
            "experienceLevel": ["entry", "associate", "mid"],
            "jobType": ["full-time", "part-time"],
            "remote": ["on-site", "remote", "hybrid"],
            "maxResults": 50
        },
        "requires_payment": True
    },
    
    # Add more scrapers here
    "indeed": {
        "actor_id": "some-indeed-actor-id",
        "default_params": {
            "queries": ["Software Engineer"],
            "locations": ["United States"],
            "maxResults": 50,
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }
        }
    },
    
    "glassdoor": {
        "actor_id": "some-glassdoor-actor-id", 
        "default_params": {
            "keyword": "Software Engineer",
            "location": "United States",
            "maxJobs": 50
        }
    },
    
    "indeed_jobs": {
        "actor_id": "misceres/indeed-scraper",
        "description": "Indeed job scraper - Reliable alternative to LinkedIn",
        "requires_payment": False,
        "monthly_cost": "Free",
        "default_params": {
            "position": "software engineer",
            "location": "United States",
            "maxResults": 20,
            "parseCompanyDetails": True
        }
    },
    
    "glassdoor_jobs": {
        "actor_id": "drobnikj/glassdoor-scraper",
        "description": "Glassdoor job scraper - Good for salary data",
        "requires_payment": False,
        "monthly_cost": "Free (limited)",
        "default_params": {
            "search": "software engineer",
            "location": "United States",
            "maxResults": 15
        }
    }
}

# Job search templates
JOB_SEARCH_TEMPLATES = {
    "tech_jobs": {
        "queries": ["Software Engineer", "Data Engineer", "DevOps Engineer", "Frontend Developer"],
        "locations": ["San Francisco", "New York", "Seattle", "Austin"],
        "companies": ["Google", "Microsoft", "Apple", "Amazon", "Meta"]
    },
    
    "remote_tech": {
        "queries": ["Remote Software Engineer", "Remote Python Developer"],
        "locations": ["United States", "Remote"],
        "remote_preference": ["2", "3"]  # Remote and Hybrid
    },
    
    "senior_roles": {
        "queries": ["Senior Software Engineer", "Staff Engineer", "Principal Engineer"],
        "experience_levels": ["senior", "director", "executive"]
    }
} 