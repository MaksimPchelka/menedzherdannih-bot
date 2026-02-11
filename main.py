import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or "8532055151:AAF0-Qp9z_141FCdMht17SDggNfYfURGIg4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class SafeStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_search = State()
    setting_pin = State()
    entering_pin = State()

vault = {}
user_pins = {} # {user_id:"1234"}

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔒 Сохранить"), KeyboardButton(text="📂 Посмотреть всё")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="🔑 Установить/Сменить Пин")],
        [KeyboardButton(text="🗑 Очистить сейф")]
    ], resize_keyboard=True)

def delete_kb(index: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{index}"))
    return builder.as_markup()

# хендлеры

@dp.message(F.text == "🔑 Установить/Сменить Пин")
async def set_pin_start(message: Message, state: FSMContext):
    await message.answer("Придумайте и пришлите 4 цифры Пин-кода:")
    await state.set_state(SafeStates.setting_pin)

@dp.message(SafeStates.setting_pin)
async def set_pin_process(message: Message, state: FSMContext):
    if message.text.isdigit() and len(message.text) == 4:
        user_pins[message.from_user.id] = message.text
        await message.answer(f"✅ Пин-код установлен: `{message.text}`", parse_mode="Markdown", reply_markup=main_kb())
        await state.clear()
    else:
        await message.answer("⚠️ Пин должен состоять ровно из 4 цифр")
        

@dp.message(F.text == "📂 Посмотреть всё")
async def check_pin_before_show(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id in user_pins:
        await message.answer("🔒 Введите ваш Пин-код для доступа к сейфу:")
        await state.set_state(SafeStates.entering_pin)
    else:
        await show_all_logic(message)

@dp.message(SafeStates.entering_pin)
async def verify_pin_process(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == user_pins.get(user_id):
        await message.answer("🔓 Доступ разрешен!")
        await state.clear()
        await show_all_logic(message)
    else:
        await message.answer("❌ Неверный Пин! Попробуйте еще раз или отмените действие")

async def show_all_logic(message: Message):
    user_id = message.from_user.id
    items = vault.get(user_id, [])
    
    if not items:
        await message.answer("В сейфе пусто.")
        return

    for idx, item in enumerate(items):
        kb = delete_kb(idx)
        content = item["content"]

        if item["type"] == "text":
            await message.answer(f"📝 Запись №{idx+1}:\n`{content}`", parse_mode="Markdown", reply_markup=kb)
        elif item["type"] == "photo":
            await message.answer_photo(content, caption=f"🖼 Фото №{idx+1}", reply_markup=kb)
        elif item["type"] == "video":
            await message.answer_video(content, caption=f"🎥 Видео №{idx+1}", reply_markup=kb)
        elif item["type"] == "audio":
            await message.answer_audio(content, caption=f"🎵 Аудио №{idx+1}", reply_markup=kb)
        elif item["type"] == "voice":
            await message.answer_voice(content, caption=f"🎙 Голос №{idx+1}", reply_markup=kb)
        elif item["type"] == "document":
            await message.answer_document(content, caption=f"📄 Документ №{idx+1}", reply_markup=kb)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🔐 Бот активирован. Используйте меню ниже", reply_markup=main_kb())

@dp.message(F.text == "🔒 Сохранить")
async def add_start(message: Message, state: FSMContext):
    await message.answer("Пришлите контент любого формата")
    await state.set_state(SafeStates.waiting_for_content)

@dp.message(SafeStates.waiting_for_content)
@dp.message(SafeStates.waiting_for_content)
async def process_save(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in vault: 
        vault[user_id] = []
        
    if message.text:
        vault[user_id].append({"type": "text", "content": message.text})
    elif message.photo:
        vault[user_id].append({"type": "photo", "content": message.photo[-1].file_id})
    elif message.video:
        vault[user_id].append({"type": "video", "content": message.video.file_id})
    elif message.audio:
        vault[user_id].append({"type": "audio", "content": message.audio.file_id})
    elif message.voice:
        vault[user_id].append({"type": "voice", "content": message.voice.file_id})
    elif message.document:
        vault[user_id].append({"type": "document", "content": message.document.file_id})
    else:
        await message.answer("❌ Этот тип файла я не умею хранить.")
        return
    
    await message.answer("✅ Сохранено в сейф!", reply_markup=main_kb())
    await state.clear()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[1])
    if user_id in vault:
        vault[user_id].pop(index)
        await callback.message.delete()
        await callback.answer("Удалено!")

@dp.message(F.text == "🗑 Очистить сейф")
async def clear_all(message: Message):
    vault[message.from_user.id] = []
    await message.answer("Сейф пуст.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
