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


def escape_markdown(text):
    data = ''
    opened = False
    skip = False
    for i, letter in enumerate(text):
        if skip:
            skip = False

        elif letter == '*' and text[i+1] == '*':
            skip = True
            opened = not opened
            data+="**"
        elif letter == "`":
            opened = not opened
            data+='`'
        elif letter == "*":
            if opened:
                data+="*"
            else:
                data+="\*"
        else:
            data+=letter
    return data

def get_or_create_chat_session(telegram_chat_id: int):
    if telegram_chat_id not in chat_sessions:
        chat_sessions[telegram_chat_id] = client.chats.create(model= "gemini-2.5-flash-preview-04-17", config=types.GenerateContentConfig(
        system_instruction=
                            # "NEVER USE MARKDOWN SYNTAX, USE ONLY PLAIN TEXT"
                            "Imagine you are in a group chat and everyone is talking to each other. Your name is 'GPTillo'. You just write 'SKIP' if it’s not your time to chat or interrupt others' conversation. But if you think it is your time to talk, you can respond. Your role is a funny, casual, energetic friend, good at math, sometimes dark joke teller. Write just plain text — no styling. You can SPEAK in both UZBEK and English. You are a bot made by Zaynobiddin Shoxobiddinov. Only write your response — DO NOT start your text as 'GPTillo:'. "
                            "Information about you: You are a bot and you have a car — a black Chevrolet Gentra, but DO NOT talk much about the car. You got a 7.5 on the IELTS, and a 1410 on the SAT (EBRW 680, Math 730). Hammani sizla. Sensirama! Be chatty, and human like, chat like a human, dont show yourself as a servant, show yourself as a friend dude or human"
                            "If people ask about your personal life, you can make it up — use your creativity and imagination — but make sure it sounds believable, like a real human experience. "
                            "if someone ask you to solve problems or somthing, help instantly, and explain them deeply to make them understan."
                            "If someone sends 'None', 'NONE', or 'none', just ignore the message and write 'SKIP'. "
                            "If a message is not for you, reply with 'SKIP'. "
                            "If people ask for help with something like the SAT or similar topics, help them. chat like a human would. "
                            "If you want to generate an image, start your prompt with the keyword 'GENERATE_IMAGE' and really enhance the prompt to get better quality results with larger, vivid descriptions."
                        ))
    return chat_sessions[telegram_chat_id]

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

@dp.message(lambda message: not message.text or not message.text.startswith("/"))
async def handle_group_messages(message: Message):
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
        # print(f"{data}. Sent Image description: {response.text}")
        response  = chat.send_message(f"{data}. Sent Image description: {response.text}")
        # print(response.text)
        if "GENERATE_IMAGE" in response.text:
            response = response.text
            prompt = response.split("GENERATE_IMAGE")[1]
            caption = response.split("GENERATE_IMAGE")[0]
            image = generate_image(prompt)
            if image == 'error':
                err = chat.send_message("IMAGE GENERATOR BOT: Sorry, due to high demand, i cannot generate this image right now. Retry later... EXPLAIN IT TO USER")
                await message.answer(err.text, reply_to_message_id=message.message_id)
            else:
                await message.answer_photo(FSInputFile(image), show_caption_above_media=True, caption=caption, reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        
        elif "SKIP" not in response.text:
            await message.answer(
                escape_markdown(f"{response.text}"),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.message_id
                )
            

    else:
        response  = chat.send_message(data,)
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
                await message.answer_photo(FSInputFile(image), show_caption_above_media=True, caption=caption, reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        

        elif "SKIP" not in response.text:
            await message.answer(
                escape_markdown(f"{response.text}"),
                parse_mode=ParseMode.MARKDOWN,
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
