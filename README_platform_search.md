# 🌐 Platform-Specific Job Search Guide

## 🎯 **New Feature: Target Specific Job Platforms**

Now you can search for jobs on specific platforms like LinkedIn, Indeed, Glassdoor, and more through the JSearch API!

## 🚀 **Supported Platforms**

### **Major Platforms:**
- **LinkedIn** - Best for tech jobs and professional networking
- **Indeed** - Largest job database with millions of listings  
- **Glassdoor** - Best for salary data and company reviews
- **ZipRecruiter** - Fast applications and AI matching
- **Monster** - Diverse industries and career resources
- **CareerBuilder** - Enterprise jobs and advanced search

### **Specialized Platforms:**
- **Dice** - Tech and IT specialization
- **SimplyHired** - Aggregated job listings
- **Jobs.com** - Professional opportunities
- **FlexJobs** - Remote and flexible work

## 🎛️ **How to Use in Streamlit**

### **1. Platform Selection Interface**
In the "🌐 Platform Selection" section:

1. **Choose Target Platform**: Select from dropdown
   - "All Platforms" - Search across all job sites
   - "LinkedIn" - LinkedIn jobs only
   - "Indeed" - Indeed jobs only
   - etc.

2. **Query Preview**: See exactly what query will be sent
   - All platforms: `python developer in San Francisco, CA`
   - LinkedIn only: `python developer in San Francisco, CA via linkedin`

3. **Platform Stats**: Get insights about each platform's strengths

### **2. Template Examples**
Pre-configured platform-specific templates:

- **`linkedin_tech`** - LinkedIn tech jobs in the US
- **`indeed_jobs`** - Indeed data science roles
- **`glassdoor_salary`** - Glassdoor senior positions with salary data
- **`tech_remote`** - Remote jobs across all platforms

## 💻 **Code Examples**

### **Basic Platform Search**
```python
from jsearch_job_scraper import JSearchJobScraper

scraper = JSearchJobScraper("your_rapidapi_key")

# LinkedIn-specific search
linkedin_jobs = scraper.search_jobs(
    query="data scientist",
    location="New York, NY",
    platform="linkedin",
    num_pages=2
)

# Indeed-specific search  
indeed_jobs = scraper.search_jobs(
    query="software engineer", 
    location="San Francisco, CA",
    platform="indeed",
    employment_types="FULLTIME"
)

# All platforms (default)
all_jobs = scraper.search_jobs(
    query="python developer",
    location="Austin, TX"
    # platform=None (default)
)
```

### **Platform-Specific Remote Jobs**
```python
# Remote LinkedIn jobs
remote_linkedin = scraper.search_jobs(
    query="frontend developer",
    location="remote",
    platform="linkedin",
    remote_jobs_only=True
)

# Remote jobs across all platforms
remote_all = scraper.search_jobs(
    query="backend engineer",
    location="remote", 
    remote_jobs_only=True
    # platform=None searches all platforms
)
```

### **Using Templates**
```python
from jsearch_job_scraper import JOB_TEMPLATES

# Use LinkedIn tech template
linkedin_template = JOB_TEMPLATES["linkedin_tech"]
results = scraper.search_jobs(**linkedin_template)

# Use Glassdoor salary template  
glassdoor_template = JOB_TEMPLATES["glassdoor_salary"]
results = scraper.search_jobs(**glassdoor_template)
```

## 🎯 **Query Format Examples**

The JSearch API accepts these query formats:

### **General Searches:**
```
web development jobs in chicago
marketing manager in new york
remote python developer
```

### **Platform-Specific Searches:**
```
marketing manager in new york via linkedin
software engineer in seattle via indeed
data scientist in boston via glassdoor
remote developer via ziprecruiter
```

### **What Gets Generated:**
- **All Platforms**: `"python developer in San Francisco, CA"`
- **LinkedIn Only**: `"python developer in San Francisco, CA via linkedin"`
- **Indeed Only**: `"python developer in San Francisco, CA via indeed"`
- **Remote + Platform**: `"remote python developer via linkedin"`

## 📊 **Platform Comparison**

| Platform | Best For | Typical Response Time | Job Volume |
|----------|----------|---------------------|------------|
| LinkedIn | Tech, Professional | Fast | High |
| Indeed | All Industries | Fast | Very High |
| Glassdoor | Salary Research | Medium | Medium |
| ZipRecruiter | Quick Apply | Fast | High |
| Monster | Career Growth | Medium | Medium |
| Dice | Tech/IT Specialized | Fast | Medium |

## 🔍 **Search Strategy Tips**

### **For Tech Jobs:**
1. **LinkedIn** - Best for senior roles and startups
2. **Dice** - Specialized tech roles and contracts
3. **Indeed** - Broad coverage, all levels

### **For Salary Research:**
1. **Glassdoor** - Detailed salary data and reviews
2. **LinkedIn** - Professional context and networking
3. **Indeed** - Market rates across companies

### **For Remote Work:**
1. **FlexJobs** - Curated remote opportunities
2. **LinkedIn** - Professional remote roles
3. **Indeed** - Largest remote job database

### **For Fast Applications:**
1. **ZipRecruiter** - One-click apply features
2. **Indeed** - Simple application process
3. **SimplyHired** - Aggregated easy-apply jobs

## 🎛️ **UI Features**

### **Platform Breakdown:**
When searching all platforms, see job distribution:
```
🎯 LinkedIn: 15 jobs
🎯 Indeed: 23 jobs  
🎯 Glassdoor: 8 jobs
🎯 Other: 4 jobs
```

### **Platform Insights:**
Get platform-specific guidance:
- **LinkedIn**: "📊 Best for tech jobs"
- **Indeed**: "📊 Largest job database"  
- **Glassdoor**: "💰 Best for salary data"
- **ZipRecruiter**: "⚡ Fast applications"

### **Query Preview:**
See exactly what will be searched:
```
Query will be: python developer in San Francisco, CA via linkedin
```

## 🧪 **Testing**

### **Test Platform-Specific Searches:**
```bash
# Run the enhanced test script
python test_jsearch.py

# This will test:
# 1. General search (all platforms)
# 2. LinkedIn-specific search  
# 3. Indeed-specific search
# 4. Platform availability check
```

### **Test in Streamlit:**
1. Go to "JSearch Job Scraper" tab
2. Select a specific platform
3. Enter job details
4. See platform-specific results

## 🎉 **Benefits**

### **Targeted Search:**
- Find platform-specific opportunities
- Leverage each platform's strengths
- Reduce noise from irrelevant sources

### **Better Data Quality:**
- Platform-specific job formats
- More accurate salary data (Glassdoor)
- Professional context (LinkedIn)

### **Strategic Job Hunting:**
- Research salaries on Glassdoor
- Network on LinkedIn  
- Apply quickly on ZipRecruiter
- Find specialized roles on Dice

## 🔧 **Advanced Usage**

### **Platform Strategy Workflow:**
```python
# 1. Research salaries on Glassdoor
glassdoor_research = scraper.search_jobs(
    query="senior python developer",
    location="San Francisco, CA", 
    platform="glassdoor"
)

# 2. Find networking opportunities on LinkedIn
linkedin_networking = scraper.search_jobs(
    query="python developer",
    location="San Francisco, CA",
    platform="linkedin" 
)

# 3. Apply quickly on Indeed/ZipRecruiter
quick_apply = scraper.search_jobs(
    query="python developer", 
    location="San Francisco, CA",
    platform="ziprecruiter"
)
```

### **Multi-Platform Comparison:**
```python
platforms = ["linkedin", "indeed", "glassdoor"]
all_results = {}

for platform in platforms:
    results = scraper.search_jobs(
        query="data scientist",
        location="New York, NY",
        platform=platform,
        num_pages=1
    )
    all_results[platform] = results.get("data", [])

# Compare results across platforms
```

## 🎯 **Get Started**

1. **Update your code** - The new platform parameter is available
2. **Test it out** - Run `python test_jsearch.py`  
3. **Use Streamlit** - Try the new platform selector
4. **Strategic search** - Target specific platforms for different goals

**Now you can search exactly where you want to find jobs!** 🚀 