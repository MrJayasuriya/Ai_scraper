# LinkedIn Job Scraper Integration

## 🚀 Overview

The Universal Job Scraper has been integrated into the Streamlit dashboard as a new tab called **"💼 LinkedIn Job Scraper"**. This provides a user-friendly interface to scrape LinkedIn jobs directly from the web app.

## 🔧 Setup Requirements

### Environment Variables

Add the following to your `.env` file:

```bash
# Existing variables
SERPER_API_KEY=your_serper_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# New variable for job scraping (note: use APIFY_KEY, not APIFY_API_KEY)
APIFY_KEY=your_apify_api_key_here
```

### Get Your Apify API Key

1. Go to [apify.com](https://apify.com)
2. Create a free account
3. Navigate to Settings → Integrations → API keys
4. Copy your API key and add it to your `.env` file

## 💼 Features

### 🎯 Smart Job Search
- **Multiple LinkedIn Scrapers**: Choose from different scraper types
- **Flexible Parameters**: Job title, location, remote preferences
- **Advanced Filters**: Contract types, time intervals, company filters
- **Rate Limiting**: Configurable delays to avoid blocks

### 📊 Rich Results Display
- **Summary Metrics**: Total jobs, companies, salary info, remote jobs
- **Interactive Table**: Key job information in a clean table
- **Complete Data View**: Access to all scraped fields
- **JSON Debug View**: Raw data for troubleshooting

### 💾 Data Integration
- **Database Storage**: Automatically saves to your personal database
- **Excel Export**: Download results as Excel files
- **Format Compatibility**: Integrates with existing analytics

## 🎮 How to Use

1. **Navigate to the Job Scraper Tab**
   - Open the Streamlit app
   - Click on "💼 LinkedIn Job Scraper" tab

2. **Configure Your Search**
   - Select a LinkedIn scraper type
   - Enter job title/keywords (e.g., "Python Developer")
   - Specify location (e.g., "San Francisco, CA")
   - Set maximum results (1-100)

3. **Set Preferences**
   - Choose remote work preferences (On-site, Remote, Hybrid)
   - Select contract types (Full-time, Part-time, etc.)
   - Expand "Advanced Options" for more settings

4. **Start Scraping**
   - Click "🚀 Start Job Scraping"
   - Watch the progress bar
   - View results in the table below

5. **Download & Analyze**
   - Click "📥 Download Excel" to export
   - Results automatically saved to database
   - Use Analytics tab for deeper insights

## 🤖 Available Scrapers

- **linkedin_free**: Free LinkedIn scraper (recommended)
- **linkedin_premium**: Premium features (requires subscription)
- **linkedin_alternative**: Alternative scraper with different features
- **linkedin_no_cookies**: Cookie-free scraper

## 📋 Scraped Data Fields

The system extracts comprehensive job information:

### Core Job Data
- Job title and description
- Company name and details
- Location and remote options
- Salary information (when available)
- Application links

### Additional Fields
- Posted date and time
- Number of applicants
- Job functions and industries
- Seniority levels
- Employment types

## 🔒 Privacy & Security

- **Personal Data Spaces**: Each user has isolated data
- **Secure Storage**: All data encrypted in database
- **Rate Limiting**: Respects LinkedIn's terms of service
- **No Account Required**: Scrapes public data only

## ⚡ Performance Features

- **Progress Tracking**: Real-time scraping progress
- **Error Handling**: Graceful failure recovery
- **Result Caching**: Session-based result storage
- **Concurrent Processing**: Fast data extraction

## 🛠️ Troubleshooting

### Common Issues

1. **"Apify API configuration required"**
   - Add `APIFY_KEY` to your `.env` file (note: use `APIFY_KEY`, not `APIFY_API_KEY`)
   - Restart the Streamlit app

2. **Contract type validation error: "Field input.0 must be equal to one of the allowed values"**
   - This has been fixed in the latest version
   - The system now uses correct contract type codes: F=Full-time, P=Part-time, T=Temporary, C=Contract
   - If you still see this error, make sure you're using the updated scraper configuration

3. **"You must rent a paid Actor" error**
   - Some scrapers require paid subscriptions
   - Use the "Show paid scrapers" checkbox to see which ones require payment
   - Stick to free scrapers like `linkedin_free` for no-cost usage
   - The system now clearly marks paid vs free scrapers

4. **No results found**
   - Try different keywords or locations
   - Check scraper availability
   - Reduce result count if rate limited

5. **Scraping errors**
   - LinkedIn may temporarily block requests
   - Try again with longer delays
   - Switch to a different scraper type

### Debug Information

- Use the "🔧 Raw JSON Data" expander to see complete scraper output
- Check browser console for any JavaScript errors
- Monitor progress messages for specific error details

## 🔄 Integration Benefits

- **Seamless Workflow**: No need to switch between tools
- **Unified Analytics**: Job data appears in existing dashboards
- **Database Continuity**: Uses same storage as other features
- **Consistent UI**: Matches the app's premium design

## 📈 Future Enhancements

- Additional job boards (Indeed, Glassdoor, etc.)
- AI-powered job matching
- Automated job alerts
- Advanced filtering and search
- Bulk company analysis 