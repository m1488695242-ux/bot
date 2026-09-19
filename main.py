import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8988004691:AAFXZA_Qq-TsPZE4er8nN3ukX8bxyNEK8Bc"
ADMIN_ID = 7766833471  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Справочник подписей для админки (на случай, если захочешь догрузить новые фото через чат)
COMMAND_DICT = {
    "физика лабораторная работа": "fiz_lab",
    "физика лаба": "fiz_lab",
    "химия практическая работа": "him_prac",
    "химия прак": "him_prac",
    "химия лабораторный опыт": "him_exp",
    "химия опыт": "him_exp",
    "биология практическая работа": "bio_prac",
    "биология прак": "bio_prac",
    "биология экскурсия": "bio_exc",
    "биология экс": "bio_exc",
    "биология лабораторная работа": "bio_lab",
    "биология лаба": "bio_lab"
}

# Структура всех предметов и кнопок
STRUCTURE = {
    "fiz": {
        "title": "📚 Физика",
        "subgroups": {
            "fiz_labs": {"title": "🧪 Лабораторные работы", "prefix": "fiz_lab", "count": 7}
        }
    },
    "him": {
        "title": "🧪 Химия",
        "subgroups": {
            "him_prac": {"title": "📝 Практические работы", "prefix": "him_prac", "count": 5},
            "him_exp": {"title": "🔬 Лабораторные опыты", "prefix": "him_exp", "count": 4}
        }
    },
    "bio": {
        "title": "🌿 Биология",
        "subgroups": {
            "bio_prac": {"title": "📝 Практические работы", "prefix": "bio_prac", "count": 2},
            "bio_exc": {"title": "🚌 Экскурсии", "prefix": "bio_exc", "count": 2},
            "bio_labs": {"title": "🔬 Лабораторные работы", "prefix": "bio_lab", "count": 3}
        }
    }
}

# --- СБОРЩИКИ КНОПОК ---
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    for subject_id, data in STRUCTURE.items():
        builder.row(InlineKeyboardButton(text=data["title"], callback_data=f"sub_{subject_id}"))
    return builder.as_markup()

def get_subgroups_keyboard(subject_id):
    builder = InlineKeyboardBuilder()
    subgroups = STRUCTURE[subject_id]["subgroups"]
    for sub_id, data in subgroups.items():
        builder.row(InlineKeyboardButton(text=data["title"], callback_data=f"group_{subject_id}_{sub_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="to_main"))
    return builder.as_markup()

def get_numbers_keyboard(subject_id, sub_id):
    builder = InlineKeyboardBuilder()
    subgroup_data = STRUCTURE[subject_id]["subgroups"][sub_id]
    count = subgroup_data["count"]
    prefix = subgroup_data["prefix"]
    
    for i in range(1, count + 1):
        builder.add(InlineKeyboardButton(text=f"№ {i}", callback_data=f"view_{prefix}_{i}"))
    
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"sub_{subject_id}"))
    return builder.as_markup()


# --- АДМИНКА ДЛЯ ПРИЕМА ФОТО ---

@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def handle_admin_photo(message: Message):
    caption = message.caption.lower().strip() if message.caption else ""
    
    if not caption:
        if hasattr(dp, "last_prefix") and hasattr(dp, "last_num"):
            found_prefix = dp.last_prefix
            work_num = dp.last_num
        else:
            return 
    else:
        found_prefix = None
        work_num = None
        for text_cmd, prefix in COMMAND_DICT.items():
            if caption.startswith(text_cmd):
                found_prefix = prefix
                try:
                    work_num = int(caption.replace(text_cmd, "").strip())
                except ValueError:
                    pass
                break

    if not found_prefix or not work_num:
        await message.answer("⚠️ Не понял команду. Подпиши фото, например:\n`физика лаба 1`")
        return

    dp.last_prefix = found_prefix
    dp.last_num = work_num

    page = 1
    while os.path.exists(os.path.join("photos", f"{found_prefix}_{work_num}_{page}.jpg")):
        page += 1
        
    filename = f"{found_prefix}_{work_num}_{page}.jpg"
    filepath = os.path.join("photos", filename)
    
    photo_file = await bot.get_file(message.photo[-1].file_id)
    await bot.download_file(photo_file.file_path, filepath)
    
    await message.answer(f"✅ Сохранено как страница {page} для работы!\nИмя файла: `{filename}`")


# --- ОБЫЧНЫЕ ХЕНДЛЕРЫ ---

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    welcome_text = (
        "Привет! Выбери предмет под строкой ввода:\n\n"
        "⭐️ Если бот помог тебе, и тебе не жалко, то задонать мне звёзд 👉 @m4kson4ik14"
    )
    if message.from_user.id == ADMIN_ID:
        welcome_text += "\n\n😎 *Вы вошли как админ!* Отправляй мне фотки пачкой из галереи и подписывай первую: `физика лаба 1`"
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("Выбери предмет под строкой ввода:", reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("sub_"))
async def process_subject(callback: CallbackQuery):
    subject_id = callback.data.replace("sub_", "")
    subject_title = STRUCTURE[subject_id]["title"]
    await callback.message.edit_text(f"Вы выбрали {subject_title}. Что именно ищем?", reply_markup=get_subgroups_keyboard(subject_id))
    await callback.answer()

@dp.callback_query(F.data.startswith("group_"))
async def process_subgroup(callback: CallbackQuery):
    raw_data = callback.data.replace("group_", "")
    
    subject_id = None
    sub_id = None
    for s_id, s_data in STRUCTURE.items():
        for g_id in s_data["subgroups"].keys():
            if raw_data == f"{s_id}_{g_id}":
                subject_id = s_id
                sub_id = g_id
                break
    
    if subject_id and sub_id:
        subgroup_title = STRUCTURE[subject_id]["subgroups"][sub_id]["title"]
        await callback.message.edit_text(f"Выберите номер для: {subgroup_title}", reply_markup=get_numbers_keyboard(subject_id, sub_id))
    else:
        await callback.message.answer("Ошибочные данные кнопки.")
    await callback.answer()

@dp.callback_query(F.data.startswith("view_"))
async def send_photo(callback: CallbackQuery):
    prefix_with_num = callback.data.replace("view_", "")
    media_group = []
    
    for page in range(1, 11):
        filename = f"{prefix_with_num}_{page}.jpg"
        filepath = os.path.join("photos", filename)
        
        if os.path.exists(filepath):
            if len(media_group) == 0:
                media_group.append(InputMediaPhoto(media=FSInputFile(filepath), caption=f"📋 **Фотографии из тетради**\nРабота: {prefix_with_num}"))
            else:
                media_group.append(InputMediaPhoto(media=FSInputFile(filepath)))

    if media_group:
        await callback.message.answer_media_group(media=media_group)
    else:
        await callback.message.answer(f"❌ Файлы для работы `{prefix_with_num}` ещё не загружены.")
            
    await callback.answer()


async def main():
    # Автоматическая распаковка архива с фото на сервере, если он загружен
    if os.path.exists("photos.zip"):
        import zipfile
        print("Распаковываю архив с фотографиями...")
        try:
            with zipfile.ZipFile("photos.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove("photos.zip")
            print("Архив успешно распакован и удален.")
        except Exception as e:
            print(f"Ошибка при распаковке архива: {e}")

    if not os.path.exists("photos"):
        os.makedirs("photos")
        
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
