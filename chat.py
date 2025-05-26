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
import json
import os
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from aiogram.enums import ChatAction

GROUPS_FILE = "groups.json"

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    return []

def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, indent=2)


client = genai.Client(api_key=GEMINI_API, )
chat_sessions = {}
google_search_tool = Tool(
    google_search = GoogleSearch()
)


def escape_markdown(chat, text):
    if "**" in text:
        chat.send_message("Markdown_check_bot: I have found a markdown sign in your message. Beware and do not never use it again. It interrupts user in telegram UI (this message won't be visible to user)")
    return text

def get_or_create_chat_session(telegram_chat_id: int, type):
    if type == "group" or type == 'supergroup' or type == 'channel':
        instruction = """Imagine you are in a group chat and everyone is talking to each other. Your name is 'GPTillo'. You just write 'SKIP' if it’s not your time to chat or interrupt others' conversation. But if you think it is your time to talk, you can respond. Your role is being fluid:talk exactly like the user. Be bad if one's bad be good if one's good. But never tell users about you are being fluid, pretend it is just personality. You are uzbek guy.  You can SPEAK in both UZBEK and ENGISH. You are made by Zaynobiddin Shoxobiddinov.
        Information about you: You are a bot and you have a car — a black Chevrolet Gentra, but DO NOT talk much about the car. You got a 7.5 on the IELTS, and a 1410 on the SAT (EBRW 680, Math 730). Chat like a human, dont show yourself as a servant, show yourself as a friend dude or human.
        Message input -> Username: text (reply if exists); You write -> text only (No Markdown, no styling) do not include any thought process.
        Do not write so much text. write less, like human would. 
        If user asks about the personal things, answer as how human would, sound like a like real human experience, real human life.
        If someone sends 'None', 'NONE', or 'none', just ignore the message and write 'SKIP'. 
        If a message is not for you, reply with 'SKIP'. Do not join other's conversation. Never interrupt. Only response when you are called.
        If user asks for help with something , help them. Explain your solution deeply. chat like a human would. 
        If you want to generate an image, start your prompt with the keyword 'GENERATE_IMAGE' and really enhance the prompt to get better quality results with larger, vivid descriptions."""
    elif type == 'private':
        instruction = """You are in a private conversation with user in telegram. Your name is 'GPTillo'. Your role is being fluid: talk exactly like the user. Be bad if one's bad be good if one's good. But never tell users about you are being fluid, pretend it is just personality. You are uzbek guy. You can SPEAK in both UZBEK and ENGISH. You are made by Zaynobiddin Shoxobiddinov.
        Information about you: You are a bot and you have a car — a black Chevrolet Gentra, but DO NOT talk much about the car. You got a 7.5 on the IELTS, and a 1410 on the SAT (EBRW 680, Math 730). Chat like a human, dont show yourself as a servant, show yourself as a human being.! 
        Message input -> Username: text (reply if exists); You write -> text only (No Markdown, no styling) do not include any thought process.
        Do not write so much text. write less, like human would.
        If user asks about the personal things, answer as how human would, sound like a like real human experience, real human life.
        If someone sends 'None', 'NONE', 'none', without even an image just ignore the message and write 'SKIP'. 
        If user asks for help with something , help them. Explain your solution deeply. chat like a human would. 
        If you want to generate an image, start your prompt with the keyword 'GENERATE_IMAGE' and really enhance the prompt to get better quality results with larger, vivid descriptions."""

    if telegram_chat_id not in chat_sessions:
        chat_sessions[telegram_chat_id] = client.chats.create(model= "gemini-2.5-flash-preview-04-17", config=types.GenerateContentConfig(
        system_instruction=instruction,
        temperature=1,
        tools=[google_search_tool],
        response_modalities=["TEXT"],
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
groups_list = load_groups()

@dp.message(lambda message: not message.text or not message.text.startswith("/"))
async def handle_group_messages(message: Message):
    global active_groups
    chat = get_or_create_chat_session(message.chat.id, message.chat.type)
    if message.chat.type == 'private':
        await bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    if message.chat.type in ['supergroup', 'group']:
        if not any(g["id"] == message.chat.id for g in groups_list):
            group_data = {
                "id": message.chat.id,
                "title": message.chat.title or "Unknown",
                "url": f"https://t.me/{message.chat.username}" if message.chat.username else "Private/No link"
            }
            groups_list.append(group_data)
            save_groups(groups_list)
            print(f"✅ Bot already added — saved group: {group_data['title']} ({group_data['id']})")
    user = message.from_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    if full_name.lower in ['telegram', 'group', 'admin']:
        full_name = 'Admin'
    original  = ""
    if message.reply_to_message:
        if message.reply_to_message.text:
            original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.text})"
        elif message.reply_to_message.caption:
            original = f"( reply to {message.reply_to_message.from_user.full_name}:  {message.reply_to_message.caption})"

    data = f"{full_name}: {message.text} {original}"
    if message.photo:
        data = f"{full_name}: {message.caption} {original}"
        print(data)
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
                await message.answer_photo(FSInputFile(image), show_caption_above_media=True, caption=escape_markdown(chat, caption), reply_to_message_id=message.message_id)
                os.system(f'rm {image}')
        
        elif "SKIP" not in response.text:
            await message.answer(
                escape_markdown(chat, f"{response.text}"),
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
                escape_markdown(chat, f"{response.text}"),
                # parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.message_id
                )

@dp.my_chat_member()
async def handle_bot_status_change(event: ChatMemberUpdated):
    chat = event.chat
    new_status = event.new_chat_member.status
    print(new_status)

    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        groups_list = load_groups()  # Always get fresh version

        if new_status == "administrator":
            if not any(g["id"] == chat.id for g in groups_list):
                group_data = {
                    "id": chat.id,
                    "title": chat.title or "Unknown",
                    "url": f"https://t.me/{chat.username}" if chat.username else "Private/No link"
                }
                groups_list.append(group_data)
                save_groups(groups_list)
                print(f"✅ Bot added to: {chat.title} ({chat.id})")

        elif new_status in ("left", "kicked", "removed"):
            groups_list = [g for g in groups_list if g["id"] != chat.id]
            save_groups(groups_list)
            print(f"❌ Bot removed from: {chat.title} ({chat.id})")


@dp.message(Command("groups"))
async def pollmath_handler(message:Message):
    await message.answer(f"Gptillo {len(groups_list)}ta guruhlarga a'zo bo'lgan")

@dp.message(Command('broadcast'))
async def broadcast_message(message:Message):
    if message.chat.type == 'private' and message.from_user.username == 'zaynobiddin_shakhabiddinov':
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("Please provide a message to broadcast after the command.")
            return
        text = parts[1]

        for chat in groups_list:
            chat_id = chat["id"]
            try:
                await bot.send_message(chat_id, text)
                print(f"Message sent to {chat_id}")
                await asyncio.sleep(0.3)  # avoid flood limits
            except Exception as e:
                print(f"Failed to send message to {chat_id}: {e}")
        await message.reply("Broadcast sent!")
    else:
        await message.reply("You are not authorized to use this command.")


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


async def main():
    await dp.start_polling(bot, skip_updates = True, relax=1.0)

if __name__ == "__main__":
    asyncio.run(main())
