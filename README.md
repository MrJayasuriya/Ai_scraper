# AI Contact Scraper Pro

An advanced web scraping tool that uses artificial intelligence to extract contact information from websites. The application features a two-stage workflow: web search using Serper API and AI-powered contact extraction.

## Features

🔍 **Web Search**: Find businesses using Serper API Search API  
🗄️ **Database Storage**: Store search results in SQLite database  
🎯 **AI Contact Extraction**: Extract names, phone numbers, and emails using AI  
📊 **Analytics Dashboard**: Comprehensive insights and statistics  
📥 **Excel Export**: Download results in Excel format  
🚀 **Real-time Processing**: Live progress updates during extraction  

## Workflow

1. **Web Search Tab**: Search for businesses using Serper API and store results in SQLite database
2. **Contact Scraping Tab**: Process stored links to extract contact details using AI
3. **Results & Analytics Tab**: View, filter, and download extracted data

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# OpenRouter API Key (Required for AI-powered contact extraction)
# Get your key from: https://openrouter.ai/
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Serper API Key (Required for web search functionality) 
# Get your key from: https://serper.dev/
SERPER_API_KEY=your_serper_api_key_here

# Optional OpenRouter Configuration
OPENROUTER_MODEL=openai/gpt-3.5-turbo-0613
OPENROUTER_TEMPERATURE=0.0
OPENROUTER_SITE_URL=https://your-site.com
OPENROUTER_SITE_NAME=AI Contact Scraper Pro
```

### 3. Run the Application

```bash
streamlit run streamlit_app.py
```

## Usage

### Web Search Tab

1. Enter a search query (e.g., "dental clinics", "restaurants")
2. Specify a location (e.g., "New York, NY")
3. Set the number of results to fetch
4. Click "Search" to find businesses and store them in the database

### Contact Scraping Tab

1. View the count of unscraped links from your previous searches
2. Click "Start Scraping" to begin AI-powered contact extraction
3. Monitor real-time progress as contacts are extracted
4. Results are automatically stored in the database

### Results & Analytics Tab

1. View comprehensive analytics and statistics
2. Filter results by status, contact type, or search query
3. Download complete results in Excel format
4. Analyze extraction success rates and contact distribution

## Database Schema

The application uses SQLite with two main tables:

### search_results
- Stores business information from web searches
- Tracks which links have been processed for contact extraction

### scraped_contacts
- Stores extracted contact information
- Links to search results via foreign key relationship

## API Requirements

### OpenRouter API
- Used for AI-powered contact extraction
- Supports multiple LLM models
- Sign up at: https://openrouter.ai/

### Serper API
- Used for Google search functionality
- Provides business listings and contact information
- Sign up at: https://serper.dev/

## Architecture

```
streamlit_app.py     # Main Streamlit interface
├── database.py      # SQLite database operations
├── serper_api.py    # Serper Google Search API integration
├── scrape_ai.py     # AI-powered contact extraction
└── llm_services.py  # OpenRouter LLM service management
```

## Technology Stack

- **Frontend**: Streamlit with custom CSS
- **Database**: SQLite3
- **AI/LLM**: OpenRouter GPT-3.5-turbo
- **Web Search**: Serper Google Search API
- **Web Scraping**: ScrapeGraphAI with Playwright
- **Data Processing**: Pandas
- **Visualization**: Plotly

## Troubleshooting

### Common Issues

1. **API Keys Not Working**
   - Verify your API keys are correct in the `.env` file
   - Check API key permissions and quotas

2. **No Search Results**
   - Try different search queries or locations
   - Check Serper API quota and status

3. **Contact Extraction Failing**
   - Verify OpenRouter API key and model availability
   - Some websites may block automated access

4. **Database Issues**
   - Delete `scraper_data.db` to reset the database
   - Use the "Clear All Data" button in the sidebar

### Windows Users

The application includes fixes for Windows asyncio issues. If you encounter problems:

```python
import asyncio
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Create an issue on GitHub 