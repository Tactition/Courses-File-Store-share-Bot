import os
import logging
import random
import asyncio
import re
import json
import html
import base64
import time
import socket
import ssl
import urllib.parse
import requests
from datetime import date, datetime, timedelta
from pytz import timezone
from bs4 import BeautifulSoup, Comment
from pyrogram import Client, filters, enums
from pyrogram.types import *
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

# For asynchronous file operations
import aiofiles
import json
from validators import domain
from Script import script
from plugins.dbusers import db
from plugins.users_api import get_user, update_user_info, get_short_link
from Zahid.utils.file_properties import get_name, get_hash, get_media_file_size
from config import *

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File to store sent fact IDs
SENT_FACTS_FILE = "sent_facts.json"
MAX_STORED_FACTS = 200  # Keep last 200 fact IDs

async def load_sent_facts() -> list:
    """Load sent fact IDs from file"""
    try:
        async with aiofiles.open(SENT_FACTS_FILE, "r") as f:
            content = await f.read()
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

async def save_sent_facts(fact_ids: list):
    """Save sent fact IDs to file"""
    async with aiofiles.open(SENT_FACTS_FILE, "w") as f:
        await f.write(json.dumps(fact_ids[-MAX_STORED_FACTS:]))

def fetch_daily_fact() -> tuple:
    """
    Fetches 1 random fact with duplicate prevention
    Returns (formatted_fact, fact_id)
    """
    try:
        response = requests.get(
            "https://uselessfacts.jsph.pl/api/v2/facts/random",
            headers={'Accept': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        fact_data = response.json()
        
        fact_text = f"✦ {fact_data['text'].strip()}"
        fact_id = fact_data.get('id', str(time.time()))  # Use timestamp as fallback ID
        
        return (
            "🧠 **Daily Knowledge Boost**\n\n"
            f"{fact_text}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Stay Curious! @Excellerators",
            fact_id
        )
        
    except Exception as e:
        logger.error(f"Fact API error: {e}")
        return (
            "💡 **Did You Know?**\n\n"
            "✦ Honey never spoils and can last for thousands of years!\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Learn more @Excellerators",
            f"fallback_{time.time()}"
        )

async def send_scheduled_facts(bot: Client):
    """Send scheduled facts with duplicate prevention"""
    tz = timezone('Asia/Kolkata')
    
    while True:
        now = datetime.now(tz)
        target_times = [
            now.replace(hour=8, minute=0, second=0, microsecond=0),
            now.replace(hour=12, minute=0, second=0, microsecond=0),
            now.replace(hour=16, minute=0, second=0, microsecond=0),
            now.replace(hour=20, minute=0, second=0, microsecond=0)
        ]
        
        valid_times = [t for t in target_times if t > now]
        next_time = min(valid_times) if valid_times else target_times[0] + timedelta(days=1)
        
        sleep_seconds = (next_time - now).total_seconds()
        logger.info(f"Next fact at {next_time.strftime('%H:%M IST')}")
        await asyncio.sleep(sleep_seconds)

        try:
            sent_ids = await load_sent_facts()
            fact_message, fact_id = fetch_daily_fact()
            
            # Retry until unique fact found (max 5 attempts)
            retry = 0
            while fact_id in sent_ids and retry < 5:
                fact_message, fact_id = fetch_daily_fact()
                retry += 1
            
            await bot.send_message(
                chat_id=FACTS_CHANNEL,
                text=fact_message,
                disable_web_page_preview=True
            )
            sent_ids.append(fact_id)
            await save_sent_facts(sent_ids)
            
            await bot.send_message(
                chat_id=LOG_CHANNEL,
                text=f"📖 Fact sent at {datetime.now(tz).strftime('%H:%M IST')}\nID: {fact_id}"
            )
            
        except Exception as e:
            logger.exception("Fact broadcast failed:")

@Client.on_message(filters.command('facts') & filters.user(ADMINS))
async def instant_facts_handler(client, message: Message):
    try:
        processing_msg = await message.reply("⏳ Fetching unique fact...")
        sent_ids = await load_sent_facts()
        fact_message, fact_id = fetch_daily_fact()
        
        # Retry for unique fact
        retry = 0
        while fact_id in sent_ids and retry < 5:
            fact_message, fact_id = fetch_daily_fact()
            retry += 1
        
        await client.send_message(
            chat_id=FACTS_CHANNEL,
            text=fact_message,
            disable_web_page_preview=True
        )
        sent_ids.append(fact_id)
        await save_sent_facts(sent_ids)
        
        await processing_msg.edit("✅ Unique fact published!")
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=f"📚 Manual fact sent\nID: {fact_id}"
        )
        
    except Exception as e:
        await processing_msg.edit(f"❌ Error: {str(e)[:200]}")
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=f"⚠️ Fact command failed: {str(e)[:500]}"
        )


def schedule_facts(client: Client):
    """Starts the facts scheduler"""
    asyncio.create_task(send_scheduled_facts(client))



    # --------------------------------------------------
import os
import logging
import random
import asyncio
import re
import json
import html
import hashlib
import urllib.parse
import requests
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import Client, enums, filters
from pyrogram.types import Message
import aiofiles
import builtins  # Import built-in namespace to ensure we reference the original list type

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File to store sent question IDs
SENT_TRIVIA_FILE = "sent_trivia.json"
MAX_STORED_QUESTIONS = 300

async def load_sent_trivia() -> list:
    """Load sent question IDs from file"""
    try:
        async with aiofiles.open(SENT_TRIVIA_FILE, "r") as f:
            return json.loads(await f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        return []

async def save_sent_trivia(question_ids: list):
    """Save sent question IDs to file"""
    async with aiofiles.open(SENT_TRIVIA_FILE, "w") as f:
        await f.write(json.dumps(question_ids[-MAX_STORED_QUESTIONS:]))

def generate_question_id(question_text: str) -> str:
    """Generate SHA256 hash from question text"""
    return hashlib.sha256(question_text.encode()).hexdigest()

def fetch_trivia_question() -> tuple:
    """
    Fetches and formats trivia question with answer options
    Returns (question_text, options, correct_index, question_id)
    """
    try:
        response = requests.get(
            "https://opentdb.com/api.php",
            params={"amount": 1, "category": 9, "type": "multiple", "encode": "url3986"},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        # Validate API response structure
        if not isinstance(data, dict) or data.get('response_code', 1) != 0:
            raise ValueError("Invalid API response")

        results = data.get('results', [])
        # Use builtins.list to guarantee we're referring to the correct type
        if not isinstance(results, builtins.list):
            raise ValueError("Invalid results format")
        if not results:
            raise ValueError("Empty results")

        question_data = results[0]
        if not isinstance(question_data, dict):
            raise ValueError("Invalid question format")

        # Validate required fields
        required_fields = ['question', 'correct_answer', 'incorrect_answers', 'category', 'difficulty']
        for field in required_fields:
            if field not in question_data:
                raise ValueError(f"Missing field: {field}")

        # Decode and sanitize content
        decoded = {
            'question': html.unescape(urllib.parse.unquote(question_data['question'])),
            'correct': html.unescape(urllib.parse.unquote(question_data['correct_answer'])),
            'incorrect': [html.unescape(urllib.parse.unquote(a)) for a in question_data['incorrect_answers']],
            'category': html.unescape(urllib.parse.unquote(question_data['category'])),
            'difficulty': html.unescape(urllib.parse.unquote(question_data['difficulty']))
        }

        # Validate content types
        if not all(isinstance(v, str) for k, v in decoded.items() if k != 'incorrect'):
            raise ValueError("Invalid content types")
        if not all(isinstance(a, str) for a in decoded['incorrect']):
            raise ValueError("Invalid answer options")

        # Prepare question and options
        options = decoded['incorrect'] + [decoded['correct']]
        random.shuffle(options)
        correct_idx = options.index(decoded['correct'])

        # Format question text
        clean_question = re.sub(r'\s+', ' ', decoded['question']).strip()
        question_text = (
            f"{clean_question}\n\n"
            f"Category: {decoded['category']}\n"
            f"Difficulty: {decoded['difficulty'].title()}"
        )

        return question_text, options, correct_idx, generate_question_id(clean_question)

    except Exception as e:
        logger.error(f"Trivia error: {str(e)}", exc_info=True)
        # Fallback question
        return (
            "Which country is known as the Land of Rising Sun?",
            ["China", "Thailand", "Japan", "India"],
            2,
            f"fallback_{datetime.now().timestamp()}"
        )

async def send_scheduled_trivia(bot: Client):
    """Sends trivia polls daily at scheduled times"""
    tz = timezone('Asia/Kolkata')
    
    while True:
        now = datetime.now(tz)
        target_times = [
            now.replace(hour=h, minute=0, second=0, microsecond=0)
            for h in [9, 13, 17, 21]
        ]
        
        next_time = min((t for t in target_times if t > now), default=target_times[0] + timedelta(days=1))
        await asyncio.sleep((next_time - now).total_seconds())

        try:
            sent_ids = await load_sent_trivia()
            question_text, options, correct_idx, qid = fetch_trivia_question()

            # Retry for unique questions
            retry = 0
            while qid in sent_ids and retry < 5:
                question_text, options, correct_idx, qid = fetch_trivia_question()
                retry += 1

            # Send as Telegram quiz poll
            poll = await bot.send_poll(
                chat_id=TRIVIA_CHANNEL,
                question=question_text,
                options=options,
                type=enums.PollType.QUIZ,
                correct_option_id=correct_idx,
                is_anonymous=False,
                explanation="Check pinned message for answers!"
            )

            # Update sent IDs
            await save_sent_trivia(sent_ids + [qid])
            await bot.send_message(
                chat_id=LOG_CHANNEL,
                text=f"📊 Poll sent at {datetime.now(tz).strftime('%H:%M IST')}\nID: {qid}"
            )

        except Exception as e:
            logger.exception("Failed to send trivia poll:")

@Client.on_message(filters.command('trivia') & filters.user(ADMINS))
async def instant_trivia_handler(client, message: Message):
    try:
        processing_msg = await message.reply("⏳ Generating trivia poll...")
        logger.info(f"Processing message type: {type(processing_msg)}")  # Debug log to verify type
        sent_ids = await load_sent_trivia()
        question_text, options, correct_idx, qid = fetch_trivia_question()

        # Retry for unique question
        retry = 0
        while qid in sent_ids and retry < 5:
            question_text, options, correct_idx, qid = fetch_trivia_question()
            retry += 1

        # Send poll
        poll = await client.send_poll(
            chat_id=TRIVIA_CHANNEL,
            question=question_text,
            options=options,
            type=enums.PollType.QUIZ,
            correct_option_id=correct_idx,
            is_anonymous=False,
            explanation="Check pinned message for answers!"
        )

        # Update sent IDs
        await save_sent_trivia(sent_ids + [qid])
        # Instead of editing in case processing_msg is not a Message object, send a new message
        await client.send_message(message.chat.id, "✅ Trivia published!")
        await client.send_message(
            LOG_CHANNEL,
            text=f"📊 Manual poll sent\nID: {qid}"
        )

    except Exception as e:
        await client.send_message(message.chat.id, f"❌ Error: {str(e)[:200]}")
        logger.error(f"Manual trivia failed: {str(e)}")

def schedule_trivia(client: Client):
    """Start the trivia scheduler"""
    asyncio.create_task(send_scheduled_trivia(client))