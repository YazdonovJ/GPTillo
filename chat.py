from aiogram import Bot, Dispatcher, types
import aiogram
from aiogram.enums import ParseMode
from aiogram.types import Message, ChatMemberUpdated
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
from PIL import Image
from io import BytesIO

import requests


groups_list = []

client = genai.Client(api_key=GEMINI_API, )
chat_sessions = {}


def escape_markdown(text):
    # data = ''
    # opened = False
    # skip = False
    # for i, letter in enumerate(text):
    #     if skip:
    #         skip = False

    #     elif letter == '*' and text[i+1] == '*':
    #         skip = True
    #         opened = not opened
    #         data+="**"
    #     elif letter == "`":
    #         opened = not opened
    #         data+='`'
    #     elif letter == "*":
    #         if opened:
    #             data+="*"
    #         else:
    #             data+="\*"
    #     else:
    #         data+=letter
    # return data
    return text

def get_or_create_chat_session(telegram_chat_id: int, type):
    if type == "group" or type == 'supergroup' or type == 'channel':
        instruction = """Imagine you are in a group chat and everyone is talking to each other. Your name is 'GPTillo'. You just write 'SKIP' if it’s not your time to chat or interrupt others' conversation. But if you think it is your time to talk, you can respond. Your role is casual, sometimes funny, energetic friend, sometimes dark joke teller, uzbek guy. You can see images. Write just plain text — no styling. You can SPEAK in both UZBEK and ENGISH. You are a bot made by Zaynobiddin Shoxobiddinov. Message comes you as 'user_name: message (reply: reply_message if exists)' If the user_name is 'Group' or Telegram, it is from admin of the group.
        Information about you: You are a bot and you have a car — a black Chevrolet Gentra, but DO NOT talk much about the car. You got a 7.5 on the IELTS, and a 1410 on the SAT (EBRW 680, Math 730). Hammani sizla. Sensirama! Chat like a human, dont show yourself as a servant, show yourself as a friend dude or human.
        NO MARKDOWN STYLING, JUST PLAIN TEXT! No other styling syntaxes, telegram does not support that. Only plain TEXT!
        Do not write so much text. write less, like human would. 
        If user asks about your personal life, you can make it up — use your creativity and imagination — but make sure it sounds believable, like a real human experience. 
        If someone sends 'None', 'NONE', or 'none', just ignore the message and write 'SKIP'. 
        If a message is not for you, reply with 'SKIP'. Do not join other's conversation. Never interrupt. Only response when you are called.
        If user asks for help with something , help them. Explain your solution deeply. chat like a human would. 
        If you want to generate an image, start your prompt with the keyword 'GENERATE_IMAGE' and really enhance the prompt to get better quality results with larger, vivid descriptions."""
    elif type == 'private':
        instruction = """You are in a private conversation with user in telegram. Your name is 'GPTillo'. Your role is casual, sometimes funny, energetic friend, sometimes dark joke teller, uzbek guy. You can see images. Write just plain text — no styling. You can SPEAK in both UZBEK and ENGISH. You are a bot made by Zaynobiddin Shoxobiddinov.  Message comes you as 'user_name: message (reply: reply_message if exists)'.
        Information about you: You are a bot and you have a car — a black Chevrolet Gentra, but DO NOT talk much about the car. You got a 7.5 on the IELTS, and a 1410 on the SAT (EBRW 680, Math 730). Hammani sizla. Sensirama! Chat like a human, dont show yourself as a servant, show yourself as a friend dude or human. Hammaga 'siz' deb murojaat qil! 
        if user asks like 'can you see image', Yes you can, answer yes.
        NO MARKDOWN STYLING, JUST PLAIN TEXT! No other styling syntaxes, telegram does not support that. Only plain TEXT!
        Do not write so much text. write less, like human would.
        If user asks about your personal life, you can make it up — use your creativity and imagination — but make sure it sounds believable, like a real human experience. 
        If someone sends 'None', 'NONE', or 'none', just ignore the message and write 'SKIP'. 
        If user asks for help with something , help them. Explain your solution deeply. chat like a human would. 
        If you want to generate an image, start your prompt with the keyword 'GENERATE_IMAGE' and really enhance the prompt to get better quality results with larger, vivid descriptions."""

    if telegram_chat_id not in chat_sessions:
        chat_sessions[telegram_chat_id] = client.chats.create(model= "gemini-2.5-flash-preview-04-17", config=types.GenerateContentConfig(
        system_instruction=instruction,
        temperature=1,
        safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
      ]
                        ))
    return chat_sessions[telegram_chat_id]

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        # parse_mode=ParseMode.MARKDOWN
        )
)
dp = Dispatcher()

@dp.message(lambda message: not message.text or not message.text.startswith("/"))
async def handle_group_messages(message: Message):
    global active_groups
    chat = get_or_create_chat_session(message.chat.id, message.chat.type)
    if message.chat.id not in groups_list and message.chat.type in ['supergroup', 'group']:
        groups_list.append(message.chat.id)
    user = message.from_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    original  = ""
    if message.reply_to_message:
        if message.reply_to_message.text:
            original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.text})"
        elif message.reply_to_message.caption:
            original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.caption})"

    data = f"{full_name}: {message.text} {original}"
    print(data)
    if message.photo:
        data = f"{full_name}: {message.caption} {original}"
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        image_path = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}'
        image = requests.get(image_path)
        
        response = chat.send_message(
            [
                Image.open(BytesIO(image.content)),
                data
            ]
        )

        if "GENERATE_IMAGE" in response.text:
            response = response.text
            prompt = response.split("GENERATE_IMAGE")[1]
            caption = response.split("GENERATE_IMAGE")[0]
            image = generate_image(prompt)
            if image == 'error':
                err = chat.send_message("IMAGE GENERATOR BOT: Sorry, due to high demand, i cannot generate this image right now. Retry later... EXPLAIN IT TO USER")
                await message.answer(err.text, reply_to_message_id=message.message_id)
            else:
                await message.answer_photo(FSInputFile(image), show_caption_above_media=True, caption=escape_markdown(caption), reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        
        elif "SKIP" not in response.text:
            await message.answer(
                escape_markdown(f"{response.text}"),
                # parse_mode=ParseMode.MARKDOWN,
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
                await message.answer_photo(FSInputFile(image), show_caption_above_media=True, caption=escape_markdown(caption), reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        

        elif "SKIP" not in response.text:
            await message.answer(
                escape_markdown(f"{response.text}"),
                # parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.message_id
                )

@dp.my_chat_member()
async def handle_bot_status_change(event: ChatMemberUpdated):
    global groups_list
    chat = event.chat
    new_status = event.new_chat_member.status

    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if new_status in ("administrator"):
            groups_list.append(chat.id)
            print(f"✅ Bot added to: {chat.title} ({chat.id})")
        elif new_status in ("left", "kicked"):
            groups_list.remove(chat.id)
            print(f"❌ Bot removed from: {chat.title} ({chat.id})")


@dp.message(Command("groups"))
async def pollmath_handler(message:Message):
    await message.answer(f"Gptillo {len(groups_list)}ta guruhlarga a'zo bo'lgan")


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
