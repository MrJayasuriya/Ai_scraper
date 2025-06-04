# 🔐 API Keys Setup Guide

## Security First! 

**⚠️ NEVER commit real API keys to version control!**

This project includes placeholder API keys in the configuration files. You must replace them with your actual keys.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .streamlit/secrets.example.toml .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml` with your real API keys**

3. **The `secrets.toml` file is already in `.gitignore` - it won't be committed**

## Required API Keys

### Core Services (Essential)

#### 1. RapidAPI Key
- **Service**: JSearch Job Scraper
- **Get from**: https://rapidapi.com/
- **Plans**: Free tier available
- **Usage**: Job search functionality

#### 2. Apify API Key  
- **Service**: Google Maps business extraction
- **Get from**: https://console.apify.com/account/integrations
- **Plans**: Free tier with credits
- **Usage**: Google Maps data extraction

#### 3. OpenAI API Key
- **Service**: AI-powered contact extraction
- **Get from**: https://platform.openai.com/api-keys
- **Plans**: Pay-per-use
- **Usage**: AI text processing for contact extraction

#### 4. Serper API Key
- **Service**: Web search functionality
- **Get from**: https://serper.dev/
- **Plans**: Free tier available
- **Usage**: Business search and discovery

#### 5. OpenRouter API Key
- **Service**: Alternative AI models
- **Get from**: https://openrouter.ai/
- **Plans**: Pay-per-use
- **Usage**: AI processing with multiple model options

#### 6. Supabase Credentials
- **Service**: Database and authentication
- **Get from**: https://supabase.com/
- **Plans**: Free tier available
- **Usage**: User accounts and data storage

## Optional API Keys

### Google API Key
- **Service**: Google services integration
- **Get from**: https://console.cloud.google.com/
- **Usage**: Optional Google integrations

### Email Configuration (Gmail)
- **Service**: Email notifications
- **Setup**: Use Gmail App Password
- **Usage**: Optional email features

### Twitter API (Optional)
- **Service**: Twitter integration features
- **Get from**: https://developer.twitter.com/
- **Usage**: Optional Twitter functionality

## Environment Setup Options

### Option 1: Local Development (.streamlit/secrets.toml)
```toml
RAPIDAPI_KEY = "your_actual_key_here"
APIFY_KEY = "apify_api_your_actual_key"
# ... etc
```

### Option 2: Environment Variables
```bash
export RAPIDAPI_KEY="your_actual_key_here"
export APIFY_KEY="apify_api_your_actual_key"
# ... etc
```

### Option 3: Streamlit Cloud Deployment
1. Go to your Streamlit Cloud app settings
2. Navigate to "Secrets" tab
3. Paste your secrets.toml content there

## Security Best Practices

1. **Never commit secrets.toml to git**
2. **Use environment variables in production**
3. **Rotate API keys regularly**
4. **Use read-only/limited scope keys when possible**
5. **Monitor API usage for suspicious activity**

## Troubleshooting

### GitHub Push Blocked?
If GitHub blocks your push due to detected secrets:
1. Remove real API keys from committed files
2. Replace with placeholders
3. Add files to .gitignore
4. Commit the changes

### API Key Not Working?
1. Check key format (e.g., OpenAI keys start with "sk-")
2. Verify account has credits/quota
3. Check API key permissions
4. Test with API provider's documentation

### Missing API Functionality?
The app will gracefully handle missing API keys:
- Features requiring that API will be disabled
- Error messages will guide you to get the required keys
- Core functionality may still work with partial API setup

## Cost Considerations

Most APIs offer free tiers suitable for testing:
- **RapidAPI**: 100-1000 free requests/month
- **Apify**: $5 free credits monthly
- **OpenAI**: $5 free credit for new accounts
- **Serper**: 2,500 free searches/month
- **Supabase**: 50,000 monthly active users free

## Support

If you need help with API setup:
1. Check the official documentation for each service
2. Refer to the individual API provider's support
3. Check this project's issues on GitHub

---

🔒 **Remember: Keep your API keys secure and never share them publicly!** 