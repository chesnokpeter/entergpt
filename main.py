from openai import OpenAI
import base64

ZIP = 2

client = OpenAI(
    api_key="",
    base_url="",
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


import logging, asyncio, sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery
import mss
from PIL import Image
import base64
from io import BytesIO

API_TOKEN = '7934869499:AAE0-tYXc5Ho7U0KWY2AbjinJaePJqpF-wA'

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

keyboard = [
    [InlineKeyboardButton(text="*** ЭКРАН ***", callback_data="main")],
]
reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer('помочь?', reply_markup=reply_markup)


@dp.callback_query()
async def create_team(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    if callback_query.data == 'main':
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])  # Делаем скриншот первого монитора

            # Преобразуем скриншот в изображение PIL
            img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)

            new_size = (img.width // ZIP, img.height // ZIP)
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)  # Уменьшаем изображение

            # Сохраняем уменьшенное изображение в буфер в формате JPEG
            buffer = BytesIO()
            img_resized.save(buffer, format="JPEG")
            buffer.seek(0)

            # Конвертируем изображение в base64
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        await callback_query.message.answer_photo(BufferedInputFile(buffer.getvalue(), filename="screenshot.jpg"), reply_markup=reply_markup)

        response = client.chat.completions.create(
        model="vis-openai/gpt-4o-2024-08-06",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Если это картина, то напиши название картины, автора картины, эпоху и год картины. А если это фильм, то напиши оператора, режиссёра, название, год"},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{img_base64}",
                    },
                ],
            }
            ],
            max_tokens=400,
        )
        await callback_query.message.answer(response.choices[0].message.content, reply_markup=reply_markup)


async def main() -> None:
    global bot
    bot = Bot(token=API_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
