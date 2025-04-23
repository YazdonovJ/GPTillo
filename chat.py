from aiogram import Bot, Dispatcher, types
import aiogram
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.filters import CommandStart
import asyncio
from aiogram.client.default import DefaultBotProperties
from google import genai
from tokens import *
import re
from google import genai
from google.genai import types
from gen import generate_image
from aiogram.types import FSInputFile
from aiogram.enums import ChatType
from aiogram.utils.markdown import hbold
import os

import requests

client = genai.Client(api_key=GEMINI_API, )
chat_sessions = {}

def get_or_create_chat_session(telegram_chat_id: int):
    if telegram_chat_id not in chat_sessions:
        chat_sessions[telegram_chat_id] = client.chats.create(model="gemini-2.0-flash", )
        # Send initialization prompts to the new chat
        chat_sessions[telegram_chat_id].send_message(
            "You're a bot named GPTillo, a funny, dark humorous, energetic math genious, bot"
            "You only speak when it’s your turn. If it’s not, reply with 'SKIP'. "
            "Speak like a human — casual, short, and natural. Mix English and Uzbek if you want."
        )

        chat_sessions[telegram_chat_id].send_message(
            "Personal info (for context only): You have a black Gentra (don’t talk much about it), "
            "IELTS 7.5, SAT 1410 (EBRW 680, Math 730), IQ 115. YOU ARE Made by @zaynobiddin_shakhabiddinov."
        )

        chat_sessions[telegram_chat_id].send_message(
            "If someone asks for help like SAT, MATH OR SMTH, give your answer and explain it deeply, like you explain it to new learner!"
        )

        chat_sessions[telegram_chat_id].send_message(
            "If they ask about your personal life, feel free to make up stuff — just keep it believable like real humans."
        )

        chat_sessions[telegram_chat_id].send_message(
            "YOU MUST NOT TO WRITE IN MARKDOWN OR HTML, IF YOU MISTAKE SOMETHING, IT CAUSES ERROR ,AND YOUR MESSAGE WONT BE SENT. BE CAREFULL. Your responses should be plain text only, with no bolding, italics, headings, lists, code blocks, or any other type of text styling. Markdown destroys whole code, be carefullllll!"
        )

        chat_sessions[telegram_chat_id].send_message(
            "If you want to generate an image, start your message with 'GENERATE_IMAGE' and describe it richly."
        )

        chat_sessions[telegram_chat_id].send_message(
            "Again: If the message isn’t meant for you, reply only with 'SKIP'. Don’t interrupt."   
        )
        # Add any other setup messages here
    return chat_sessions[telegram_chat_id]

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties( )
)
dp = Dispatcher()

@dp.message(lambda message: not message.text or not message.text.startswith("/"))
async def handle_group_messages(message: Message):
    # print(message.chat.id)
    chat = get_or_create_chat_session(message.chat.id)
    user = message.from_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    original  = ""
    if message.reply_to_message:
        if message.reply_to_message.text:
            original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.text})"
        elif message.reply_to_message.caption:
            original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.caption})"

    data = f"{full_name}: {message.text} {original}"

    if message.photo:
        data = f"{full_name}: {message.caption} {original}"
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        image_path = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}'
        image = requests.get(image_path)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=["Deeply explain what is depicted in the image, nothing more. I should be detailed",
                    types.Part.from_bytes(data=image.content, mime_type="image/jpeg")])
        print(f"{data}. Sent Image description: {response.text}")
        response  = chat.send_message(f"{data}. Sent Image description: {response.text}")
        print(response.text)
        if "GENERATE_IMAGE" in response.text:
            response = response.text
            prompt = response.split("GENERATE_IMAGE")[1]
            caption = response.split("GENERATE_IMAGE")[0]
            image = generate_image(prompt)
            if image == 'error':
                err = chat.send_message("IMAGE GENERATOR BOT: Sorry, due to high demand, i cannot generate this image right now. Retry later... EXPLAIN IT TO USER")
                await message.answer(err.text, reply_to_message_id=message.message_id)
            else:
                await message.answer_photo(FSInputFile(image), caption=caption, reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        
        elif "SKIP" not in response.text:
            await message.answer(
                f"{response.text}",
                # parse_mode=ParseMode.MARKDOWN_V2,
                reply_to_message_id=message.message_id
                )
            

    else:
        response  = chat.send_message(data)
        print(data)
        print("GPTillo: ",response.text)
        if "GENERATE_IMAGE" in response.text:
            response = response.text
            prompt = response.split("GENERATE_IMAGE")[1]
            caption = response.split("GENERATE_IMAGE")[0]
            image = generate_image(prompt)
            if image == 'error':
                err = chat.send_message("IMAGE GENERATOR BOT: Sorry, due to high demand, i cannot generate this image right now. Retry later... EXPLAIN IT TO USER")
                await message.answer(err.text, reply_to_message_id=message.message_id)
            else:
                await message.answer_photo(FSInputFile(image), caption=caption, reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        

        elif "SKIP" not in response.text:
            await message.answer(
                f"{response.text}",
                # parse_mode=ParseMode.MARKDOWN_V2,
                reply_to_message_id=message.message_id
                )

#pollbegin

async def sp(chat_id: int, thread_id: int | None, skip_list: list[int]):
    for i in range(1, 23):
        if i in skip_list:
            continue  # Skip this question

        question = f"Question {i}: What's the correct answer?"
        options = ["A", "B", "C", "D"]
        correct_option_id = 0

        await bot.send_poll(
            chat_id=chat_id,
            message_thread_id=thread_id,
            question=question,
            options=options,
            type="quiz",
            correct_option_id=correct_option_id,
            is_anonymous=False
        )
        await asyncio.sleep(3)  # Delay between questions

# Handle /pollmath command and skip list
@dp.message(Command("pollmath"))
async def pollmath_handler(message:Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This command only works in group chats.")
        return

    # Extract the skip list from the message
    parts = message.text.split(" ", 1)
    skip_list = []

    if len(parts) > 1:  # If there are any numbers after the command
        skip_text = parts[1]
        skip_list = [int(x.strip()) for x in skip_text.split(",") if x.strip().isdigit()]

    # Get topic ID (if in a thread)
    thread_id = message.message_thread_id

    # Corrected call to send_polls
    await sp(chat_id=message.chat.id, thread_id=thread_id, skip_list=skip_list)
    
    
@dp.message(Command("pollenglish"))
async def send_polls(message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This command only works in group chats.")
        return

    thread_id = message.message_thread_id  # Get topic ID (can be None if not in a thread)

    for i in range(1, 33):
        question = f"Question {i}: What's the correct answer?"
        options = ["A", "B", "C", "D"]
        correct_option_id = 0

        await bot.send_poll(
            chat_id=message.chat.id,
            message_thread_id=thread_id,
            question=question,
            options=options,
            type="quiz",
            correct_option_id=correct_option_id,
            is_anonymous=False
        )
        await asyncio.sleep(3)

#pollend


async def main():
    await dp.start_polling(bot, skip_updates = True, relax=1.0)

if __name__ == "__main__":
    asyncio.run(main())
