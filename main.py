import os
import io
import logging
from datetime import datetime
import PIL.Image
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.enums import ParseMode
from pymongo import MongoClient
import google.generativeai as genai
import requests
import fitz  # PyMuPDF for PDF handling
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize MongoDB
client = MongoClient(MONGODB_URI)
db = client.telegram_bot
users_collection = db.users
chats_collection = db.chats
files_collection = db.files

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
vision_model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Pyrogram client
app = Client(
    "gemini_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.MARKDOWN
)

# Define custom filter for non-command messages
def non_command(_, __, message):
    return bool(message.text and not message.text.startswith('/'))

non_cmd = filters.create(non_command)

# User registration handler
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    
    # Check if user exists
    existing_user = users_collection.find_one({"chat_id": chat_id})
    if not existing_user:
        # Save new user
        users_collection.insert_one({
            "chat_id": chat_id,
            "username": user.username,
            "first_name": user.first_name,
            "registered_at": datetime.utcnow()
        })
    
    # Create contact button
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("📱 Share Contact", request_contact=True)]
    ], resize_keyboard=True)
    
    welcome_message = (
        "👋 Welcome to AI Assistant!\n\n"
        "To get started, please share your contact information using the button below.\n\n"
        "I can help you with:\n"
        "1️⃣ Answering questions\n"
        "2️⃣ Analyzing images and files\n"
        "3️⃣ Web searches (/websearch)\n"
        "4️⃣ Document analysis\n\n"
        "Just send me a message or file to begin!"
    )
    
    await message.reply_text(welcome_message, reply_markup=keyboard)

# Contact handler
@app.on_message(filters.contact)
async def contact_handler(client: Client, message: Message):
    chat_id = message.chat.id
    contact = message.contact
    
    # Update user with phone number
    users_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "phone_number": contact.phone_number,
            "contact_shared_at": datetime.utcnow()
        }}
    )
    
    # Remove contact keyboard and show regular interface
    keyboard = ReplyKeyboardMarkup([
        ["💭 Chat", "🔍 Web Search"],
        ["📁 Send Files", "❓ Help"]
    ], resize_keyboard=True)
    
    await message.reply_text(
        "✅ Thank you for registering! You now have full access to all features.",
        reply_markup=keyboard
    )

# Chat handler for text messages
@app.on_message(non_cmd & filters.private)
async def chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user_input = message.text
    loading_message = await message.reply_text("💭 Thinking...")

    try:
        # Generate response using Gemini
        response = model.generate_content(user_input)
        bot_response = response.text

        # Store chat history
        chats_collection.insert_one({
            "chat_id": chat_id,
            "user_input": user_input,
            "bot_response": bot_response,
            "timestamp": datetime.utcnow()
        })

        # Handle long responses
        if len(bot_response) > 4096:
            parts = [bot_response[i:i+4096] for i in range(0, len(bot_response), 4096)]
            for part in parts:
                await message.reply_text(part)
        else:
            await message.reply_text(bot_response)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")
    finally:
        await loading_message.delete()

# Image Analysis Handler
@app.on_message(filters.command("img"))
async def generate_from_image(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("**Please reply to a photo for a response.**")
        return

    prompt = message.command[1] if len(message.command) > 1 else message.reply_to_message.caption or "Describe this image."

    processing_message = await message.reply_text("**Generating response, please wait...**")

    try:
        img_data = await client.download_media(message.reply_to_message, in_memory=True)
        img = PIL.Image.open(io.BytesIO(img_data.getbuffer()))

        response = model.generate_content([prompt, img])
        response_text = response.text

        await message.reply_text(response_text, parse_mode=None)
    except Exception as e:
        logging.error(f"Error during image analysis: {e}")
        await message.reply_text("**An error occurred. Please try again.**")
    finally:
        await processing_message.delete()

# File handler for PDF documents
@app.on_message(filters.document)
async def pdf_handler(client: Client, message: Message):
    chat_id = message.chat.id
    loading_message = await message.reply_text("📄 Processing PDF...")

    try:
        file_id = message.document.file_id
        content_type = message.document.mime_type
        file_path = await client.download_media(message.document)

        if content_type == "application/pdf":
            # Process PDF using PyMuPDF
            with fitz.open(file_path) as pdf_document:
                text_content = "\n".join(page.get_text() for page in pdf_document)

            # Analyze text with Gemini
            response = model.generate_content(f"Analyze this PDF content: {text_content[:1500]}")
            analysis = response.text

            # Store PDF metadata in MongoDB
            files_collection.insert_one({
                "chat_id": chat_id,
                "file_id": file_id,
                "content_type": "pdf",
                "analysis": analysis,
                "timestamp": datetime.utcnow()
            })

            await message.reply_text(f"📊 PDF Analysis:\n\n{analysis}")

        else:
            await message.reply_text(f"📁 File received: {message.document.file_name} (unsupported format)")

    except Exception as e:
        logger.error(f"PDF analysis error: {e}")
        await message.reply_text("❌ Error analyzing the PDF. Please try again.")

    finally:
        await loading_message.delete()

# Web search handler
@app.on_message(filters.command("websearch"))
async def websearch_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("ℹ️ Please provide a search query.\nExample: /websearch artificial intelligence")
        return
    
    query = " ".join(message.command[1:])
    loading_message = await message.reply_text("🔍 Searching...")

    try:
        # Perform web search using SerpAPI
        search_url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 5
        }
        
        response = requests.get(search_url, params=params)
        search_data = response.json()
        
        if "organic_results" in search_data:
            # Format search results
            results = []
            for result in search_data["organic_results"][:5]:
                title = result.get("title", "No title")
                snippet = result.get("snippet", "No description")
                link = result.get("link", "")
                results.append(f"**{title}**\n{snippet}\n{link}\n")
            
            search_results = "\n".join(results)
            
            # Generate AI summary
            summary_prompt = f"Summarize these search results:\n{search_results}"
            summary = model.generate_content(summary_prompt).text
            
            # Send response
            response_text = (
                f"🤖 **AI Summary:**\n{summary}\n\n"
                f"🔍 **Top Results:**\n{search_results}"
            )
            
            # Handle long responses
            if len(response_text) > 4096:
                parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
                for part in parts:
                    await message.reply_text(part)
            else:
                await message.reply_text(response_text)
        
        else:
            await message.reply_text("❌ No results found.")

    except Exception as e:
        logger.error(f"Web search error: {e}")
        await message.reply_text("❌ Error performing search. Please try again.")
    finally:
        await loading_message.delete()

if __name__ == "__main__":
    logger.info("🚀 Starting Telegram bot...")
    app.run()