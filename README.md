# Astrobot - Telegram AI Assistant Bot

## Overview
This is a sophisticated Telegram bot that leverages Google's Gemini AI model to provide various AI-powered features. The bot can process text queries, analyze images, handle PDF documents, and perform web searches with AI-enhanced summaries.

## Features
- 🤖 Natural language conversation using Gemini AI
- 📸 Image analysis and description
- 📄 PDF document processing and analysis
- 🔍 Web search with AI-powered summaries
- 👤 User registration and contact management
- 📊 MongoDB integration for data persistence

## Prerequisites
- Python 3.8 or higher
- MongoDB database
- Telegram Bot Token
- Google API Key (Gemini)
- SerpAPI Key
- MongoDB URI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-ai-assistant.git
cd telegram-ai-assistant
```

2. Create and activate a virtual environment:
```bash
conda create --name <yourenv> python==3.8
conda activate <yourenv>
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_gemini_api_key
SERPAPI_KEY=your_serpapi_key
MONGODB_URI=your_mongodb_uri
```

## Usage

1. Start the bot:
```bash
python bot.py
```

2. Open Telegram and search for your bot using its username


## 📖 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot & register | `/start` |
| `/img` | Analyze image with AI | `/img [photo]` |
| `/websearch` | Perform web search | `/websearch AI trends` |



## Features in Detail

### Chat
- Send any text message to get AI-powered responses
- Supports markdown formatting
- Handles long responses automatically

### Image Analysis
- Send any image to get AI-powered analysis
- Supports high-resolution images
- Stores analysis results in database

### PDF Processing
- Send PDF documents for analysis
- Extracts text content
- Provides AI-generated summary

### Web Search
- Uses SerpAPI for web searches
- Provides AI-generated summaries of search results
- Returns top 5 relevant results

## Architecture
- Built with Pyrogram for Telegram API interaction
- Uses MongoDB for data persistence
- Integrates Google's Gemini AI model
- Implements SerpAPI for web searches
- Uses PyMuPDF for PDF processing

## Error Handling
- Comprehensive error logging
- User-friendly error messages
- Automatic cleanup of loading messages

## Data Storage
The bot stores the following information in MongoDB:
- User registration details
- Chat history
- File analysis results
- Document processing results

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

<Feel free to contribute🤝>

## License

This project is licensed under the MIT License - see the LICENSE file for details

