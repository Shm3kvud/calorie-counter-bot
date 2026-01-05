from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# main_kb
add_product = KeyboardButton(text="🥗 Добавить продукт")
my_profile = KeyboardButton(text="🙂 Мой профиль")
show_daily_progress = KeyboardButton(text="🕰️ Прогресс за сегодня")
show_week_history = KeyboardButton(text="🗓️ Отобразить историю недели")
get_help = KeyboardButton(text="❓ Помощь")


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [add_product],
        [show_daily_progress],
        [show_week_history],
        [my_profile],
        [get_help],
    ],
    resize_keyboard=True,
)

# gain/lose weight
gain_lose_weight = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Набрать")], [KeyboardButton(text="Похудеть")]],
    resize_keyboard=True,
)

# set kbju by AI
activity = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Низкая")],
        [KeyboardButton(text="Умеренная")],
        [KeyboardButton(text="Высокая")],
    ],
    resize_keyboard=True,
)

# question about set kbju
auto_or_yourself = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Самостоятельно")],
        [KeyboardButton(text="Автоматически")],
    ],
    resize_keyboard=True,
)

# continue or again
continue_or_again = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Заново")], [KeyboardButton(text="Продолжить")]],
    resize_keyboard=True,
)

# edit profile
edit_height = KeyboardButton(text="Рост")
edit_weight = KeyboardButton(text="Вес")
edit_goal = KeyboardButton(text="Цель")
edit_calories_goal = KeyboardButton(text="Значения КБЖУ")

edit_profile = ReplyKeyboardMarkup(
    keyboard=[[edit_calories_goal], [edit_weight], [edit_goal], [edit_height]],
    resize_keyboard=True,
)


# pick gender
genders = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Мужской")], [KeyboardButton(text="Женский")]],
    resize_keyboard=True,
)
