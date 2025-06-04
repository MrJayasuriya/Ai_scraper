# AI Contact Scraper Pro 🤖

Advanced AI-powered contact scraping tool with beautiful Streamlit interface and comprehensive authentication system.

## ✨ Features

### 🔐 User Authentication
- **Secure Signup/Login**: Create personal accounts with encrypted passwords
- **Session Management**: 30-day secure sessions with automatic cleanup
- **Data Isolation**: Each user has their own private data space
- **Input Validation**: Real-time validation for usernames, emails, and passwords

### 🎯 Intelligent Contact Extraction
- AI-powered contact extraction using OpenRouter GPT models
- Retry mechanism with exponential backoff
- Concurrent processing for better performance
- Comprehensive contact details extraction (names, phones, emails)

### 🔍 Smart Business Search
- Google Search integration via Serper API
- Local business discovery
- Comprehensive business information collection
- Rating and review data extraction

### 📊 Advanced Analytics
- Real-time statistics dashboard
- Performance metrics and success rates
- Interactive charts and visualizations
- User-specific analytics

### 💾 Data Management
- SQLite database with automatic migrations
- Excel export functionality
- Advanced filtering and search
- Secure data isolation per user

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **API Keys** (create `.env` file in the `Ai_scraper` directory):
   ```env
   SERPER_API_KEY=your_serper_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_MODEL=openai/gpt-3.5-turbo-0613
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   ```

### Installation

1. **Clone or Download** the project
2. **Navigate** to the `Ai_scraper` directory:
   ```bash
   cd Ai_scraper
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: Easy Start (Recommended)
**Windows:** Double-click `start_app.bat`
**All Systems:** 
```bash
python start_app.py
```

#### Option 2: Manual Start
```bash
cd Ai_scraper
streamlit run streamlit_app.py
```

#### Option 3: Direct Streamlit
```bash
streamlit run streamlit_app.py
```

### First Time Setup

1. **Open your browser** to `http://localhost:8501`
2. **Create an account** using the signup form
3. **Login** with your credentials
4. **Start searching** for businesses!

## 📱 User Interface

### Authentication Screen
- **Modern Design**: Glassmorphism UI with premium styling
- **Login/Signup Toggle**: Easy switching between forms
- **Real-time Validation**: Instant feedback on form inputs
- **Auto-login**: Automatic login after successful signup

### Main Dashboard
- **User Info Sidebar**: Shows current user and logout option
- **API Status Cards**: Real-time API connection status
- **Analytics Overview**: Personal statistics and metrics
- **Data Management**: Clear personal data functionality

### Three Main Tabs

#### 🔍 Intelligent Search
- Business type and location input
- Configurable result count
- Real-time search progress
- Results preview and database storage

#### 🎯 AI Extraction
- View queued links for processing
- Start AI-powered contact extraction
- Real-time progress tracking
- Enhanced vs standard scraper options

#### 📊 Analytics Center
- Comprehensive data visualization
- Advanced filtering options
- Excel export functionality
- Performance metrics and charts

## 🔐 Authentication System

### Security Features
- **Password Hashing**: SHA-256 with salt
- **Session Tokens**: Cryptographically secure 64-character tokens
- **Automatic Cleanup**: Expired sessions are cleaned automatically
- **Input Validation**: Comprehensive validation for all user inputs

### User Requirements
**Username:**
- 3-30 characters
- Letters, numbers, and underscores only

**Password:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

**Email:**
- Valid email format
- Used for login (alternative to username)

### Data Isolation
- Each user sees only their own data
- Search results are user-specific
- Analytics are calculated per user
- Data export includes only user's data

## 🛠️ Technical Details

### Architecture
```
Ai_scraper/
├── streamlit_app.py         # Main Streamlit application
├── start_app.py            # Easy start script
├── start_app.bat           # Windows batch file
├── src/
│   ├── utils/
│   │   ├── database.py     # Database management + auth
│   │   ├── auth.py         # Authentication manager
│   │   └── llm_services.py # LLM service management
│   └── services/
│       ├── serper_api.py   # Google Search API
│       └── scrape_ai_enhanced.py # AI-powered scraper
├── requirements.txt        # Python dependencies
├── .env                   # API keys (create this)
└── scraper_data.db       # SQLite database (auto-created)
```

### Database Schema
```sql
-- Authentication tables
users (id, username, email, password_hash, salt, created_at, last_login, is_active)
user_sessions (id, user_id, session_token, created_at, expires_at, is_active)

-- Data tables (with user isolation)
search_results (id, user_id, original_query, original_location, title, link, ...)
scraped_contacts (id, search_result_id, scraped_names, scraped_phones, ...)
```

### API Integration
- **Serper API**: Google Search functionality
- **OpenRouter API**: GPT models for contact extraction
- **ScrapeGraphAI**: Web scraping with Playwright

## 🔧 Configuration

### Environment Variables
```env
# Required APIs
SERPER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here

# Optional Configuration
OPENROUTER_MODEL=openai/gpt-3.5-turbo-0613
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MAX_CONCURRENT_SCRAPES=3
SCRAPE_DELAY_SECONDS=1.0
MAX_RETRIES=2
```

### Customization
- Modify CSS in `streamlit_app.py` for UI changes
- Adjust scraper settings in `scrape_ai_enhanced.py`
- Update database schema in `database.py`

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the Ai_scraper directory
   cd Ai_scraper
   streamlit run streamlit_app.py
   ```

2. **API Key Issues**
   - Check `.env` file exists in `Ai_scraper` directory
   - Verify API keys are correct and active
   - Check API quotas and limits

3. **Database Issues**
   - Delete `scraper_data.db` to reset
   - Use "Clear My Data" in the sidebar
   - Check file permissions

4. **Authentication Problems**
   - Try clearing browser cache
   - Use different browser/incognito mode
   - Check session expiration (30 days)

### Windows Specific
- Use `start_app.bat` for easiest startup
- Ensure Python is in PATH
- May need to run as administrator

### Error Messages
- **"No module named 'src'"**: Run from `Ai_scraper` directory
- **"API not configured"**: Check `.env` file
- **"Session expired"**: Login again

## 📊 Performance

### Optimization Features
- **Concurrent Processing**: Multiple links processed simultaneously
- **Retry Mechanism**: Automatic retry with exponential backoff
- **Rate Limiting**: Respectful delays between requests
- **Caching**: Session-based caching for better performance

### Recommended Settings
- Max Concurrent Scrapes: 3-5
- Delay Between Requests: 1-2 seconds
- Max Retries: 2-3

## 🆕 What's New in This Version

### Authentication System
- Complete user management with signup/login
- Secure password hashing and session management
- Personal data spaces for each user
- Beautiful authentication UI

### Enhanced Security
- SQL injection protection
- Session token validation
- Input sanitization
- Automatic session cleanup

### Improved User Experience
- Modern glassmorphism design
- Real-time validation feedback
- User-specific analytics
- Simplified startup process

### Backward Compatibility
- All existing functionality preserved
- Existing data remains accessible
- No breaking changes to core features

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the authentication documentation in `AUTHENTICATION.md`
3. Verify API keys and configuration
4. Create an issue on GitHub

## 🎯 Future Enhancements

Planned features for future releases:
- Password reset functionality
- Email verification
- User roles and permissions
- Advanced user settings
- Two-factor authentication
- API rate limit dashboard 


Get run
View API reference
Returns an object containing all details of this run.

https://api.apify.com/v2/actor-runs/OSYBwxHDbYZu6dkot?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq


Get input
View API reference
Returns the input of this run from its key-value store.

https://api.apify.com/v2/key-value-stores/Kd5EfNogsC0j5jYyd/records/INPUT?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq


Get output
View API reference
Returns the output of this run from its default key-value store.

https://api.apify.com/v2/key-value-stores/Kd5EfNogsC0j5jYyd/records/OUTPUT?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq



Get dataset items
View API reference
Returns items stored in default dataset of this run.
https://api.apify.com/v2/datasets/IgiXerOCg2dCEVz3D/items?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq


Get request queue head
View API reference
Returns 100 first requests from a default request queue of this run.

https://api.apify.com/v2/request-queues/HMvlZSxtqF3trFIVL/head?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq

Get log
View API reference
Returns the log of this run.

https://api.apify.com/v2/logs/OSYBwxHDbYZu6dkot?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq


Abort run
View API reference
Aborts the current run.

https://api.apify.com/v2/actor-runs/OSYBwxHDbYZu6dkot/abort?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq


Resurrect run
View API reference
Resurrects the current run.

https://api.apify.com/v2/actor-runs/OSYBwxHDbYZu6dkot/resurrect?token=apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq