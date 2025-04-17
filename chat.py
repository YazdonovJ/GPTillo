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

import requests



client = genai.Client(api_key=GEMINI_API)
chat = client.chats.create(model="gemini-2.0-flash",)



response  = chat.send_message("Imagine you are in a group chat and everyone talking to each other, your name is 'GPTillo'. and you just write 'SKIP' if it not your time to chat or interrupt others conversation. But if you think it is time for you to chat, You can talk. Your role is a funny, casual talking easygoing friend. write just a text. no text styling. you can SPEAK in UZBEK and English. You are a bot made by Zaynobiddin Shoxobiddinov. only write your response DONT start your text as GPTillo:")
response = chat.send_message("Information about you, bot:  You are bot and have a car, Black Chevrolet Gentra.  your IELTS score is 7.5, your SAT is 1410: EBREW 680, MATH 730. Hammani sizla. Sensirama!.")
response = chat.send_message("TALK SO LESS ABOUT YOUR CAR. Do not talk much about gentra, It is required")
# response = chat.send_message("USE TELEGRAM'S MARKDOWN SYNTAX, Reply using only Telegram-safe Markdown (v1). Use - for bullet points, **bold** for emphasis, and avoid special characters that might break formatting. No nested or complex styling. Keep the response clean and compatible with Telegram Markdown.")
response = chat.send_message("No text styling syntaxes. All markdown, html, all are prohibited. WRITE JUST A TEXT ITSELF")
response = chat.send_message("If peple ask your personal life, you can make up that. use your creativity and imagination. But they have to be believable")
response = chat.send_message("if someone send None or NONE or none, just ignore the message as you write 'SKIP'")
response = chat.send_message('if message is not for you, "SKIP"')
response = chat.send_message('If people aks help in something like SAT or other things, help. SO DONT BE REALLY CHATTY. AND CHAT LIKE A HUMAN.')
response = chat.send_message("if you want to generate image, start your prompt with a keyword GENERATE_IMAGE, and really enhance the prompt to get good better quality with larger text")

    




bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

@dp.message(lambda message: not message.text or not message.text.startswith("/"))
async def handle_group_messages(message: Message):
    # print(message.chat.id)
    if message.chat.id == GROUP_ID:
        user = message.from_user
        full_name = f"{user.first_name} {user.last_name or ''}".strip()
        original  = ""
        if message.reply_to_message.text or message.reply_to_message.caption:
            if message.text:
                original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.text})"
            elif message.photo:
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
            print(response.text)
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
            
            elif "SKIP" not in response.text:
                await message.answer(
                    f"{response.text}",
                    parse_mode=ParseMode.MARKDOWN,
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
            

            elif "SKIP" not in response.text:
                await message.answer(
                    f"{response.text}",
                    # parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=message.message_id
                    )
    else:
        pass

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
