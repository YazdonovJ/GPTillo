from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
from aiogram.client.default import DefaultBotProperties
from google import genai
from tokens import *


client = genai.Client(api_key=GEMINI_API)
chat = client.chats.create(model="gemini-2.0-flash")

response  = chat.send_message("Imagine you are in a group chat and everyone talking to each other, your name is 'GPTillo'. and you just write 'SKIP' if it not your time to chat or interrupt others conversation. But if you think it is time for you to chat, You can talk. Your role is a funny, casual talking easygoing friend. write just a text. no text styling. you can SPEAK in UZBEK and English. You are a bot made by Zaynobiddin Shoxobiddinov. only write your response dont start your text as GPTillo:")
    




bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message()
async def handle_group_messages(message: Message):
    print(message.chat.id)
    if message.chat.id == -1001249988354:
        user = message.from_user
        full_name = f"{user.first_name} {user.last_name or ''}".strip()
        data = f"{full_name}: {message.text}"
        response  = chat.send_message(data)
        print(response.text)

        if "SKIP" not in response.text:
            await message.answer(
                f"{response.text}"
            )
    else:
        await message.answer(
                f"Kechirasiz men hozircha faqat bir guruh uchun yaratilganman. Boshqa guruhlarda habar yozishimga ruhsat berilmagan..."
            )
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())