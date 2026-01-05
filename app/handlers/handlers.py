from datetime import date
from pydantic import ValidationError
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from app.texts.texts import HELP_TEXT
from app.states.states import Registration, UpdateProfile, EditProfile, DescForProduct
from app.keyboards import keyboards as kb
from app.validators import validators
from app.fomatters.formatters import (
    format_kbju,
    format_errors,
    format_daily_progress,
    format_week_history,
)
from app.gemini_api.gemini_client import auto_set_kbju, get_product_kbju
from database.sqlite_db import db


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        text=(
            "Привет! Это бот - счетчик калорий. "
            "Он поможет тебе следить за твоим рационом и набрать/похудеть.\n\n"
            "Жми /go для начала работы!\n"
        )
    )


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Действие отменено.", reply_markup=kb.main_kb)


@router.message(Command("go"))
async def reg_user(message: Message, state: FSMContext):
    check = await db.get_profile(telegram_id=message.from_user.id)
    if check:
        await message.answer(
            text="Твой профиль уже существует, хочешь продолжить с ним или заполнить его заново?",
            reply_markup=kb.continue_or_again,
        )
    else:
        await state.set_state(Registration.age)
        await message.answer(
            text="Отлично! Введи свой возраст:", reply_markup=ReplyKeyboardRemove()
        )


@router.message(F.text == "Продолжить")
async def continue_with_profile(message: Message):
    await message.answer(
        text="Можешь пользоваться ботом дальше.", reply_markup=kb.main_kb
    )


@router.message(F.text == "Заново")
async def fill_again(message: Message, state: FSMContext):
    await state.set_state(Registration.age)
    await message.answer(
        text="Отлично! Введи свой возраст:", reply_markup=ReplyKeyboardRemove()
    )


@router.message(Registration.age)
async def get_age(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        age = int(message.text)
        validators.Registration(age=age)

        await state.update_data(age=age)
        await state.set_state(Registration.height)
        await message.answer(text="Хорошо! Введи свой текущий рост:")

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)

    except ValueError:
        await message.answer(text="Возраст должен быть целым числом.")


@router.message(Registration.height)
async def get_height(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    msg = message.text
    if "," in msg:
        msg = msg.replace(",", ".")

    try:
        height = float(msg)
        validators.Registration(height=height)

        await state.update_data(height=height)
        await state.set_state(Registration.weight)
        await message.answer(text="Прекрасно! Введи свой текущий вес:")

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)

    except ValueError:
        await message.answer(text="Рост должен быть целым/вещественным числом.")


@router.message(Registration.weight)
async def get_weight(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    height = float((await state.get_data())["height"])
    try:
        msg = message.text
        if "," in msg:
            msg = msg.replace(",", ".")

        weight = float(msg)
        validators.Registration(weight=weight)
        validators.Registration(height=height, weight=weight)

        await state.update_data(weight=weight)
        await state.set_state(Registration.goal)
        await message.answer(
            text="Принято! Ты бы хотел(-а) набрать или похудеть?",
            reply_markup=kb.gain_lose_weight,
        )

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)

    except ValueError:
        await message.answer(text="Вес должен быть целым/вещественным числом.")


@router.message(Registration.goal)
async def get_goal(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        validators.Registration(goal=message.text)

        await state.update_data(goal=message.text)
        await message.answer(
            text=(
                "Замечательно! Теперь выбери, установить"
                " значения КБЖУ самостоятельно или автоматически?"
            ),
            reply_markup=kb.auto_or_yourself,
        )
        await state.set_state(Registration.yourself_or_ai)

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)


@router.message(Registration.yourself_or_ai)
async def auto_or_ai(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        validators.Registration(kbju_setting=message.text)

        await state.update_data(yourself_or_ai=message.text)

        if message.text == "Самостоятельно":
            await state.set_state(Registration.kbju)
            await message.answer(
                text=("Введи значения КБЖУ:\nПример: 2500 120 60 370"),
                reply_markup=ReplyKeyboardRemove(),
            )
        elif message.text == "Автоматически":
            await state.set_state(Registration.gender)
            await message.answer(
                text=(
                    "Выбери свой пол:\n\n"
                    "(этот и последующие выборы нужны для автоматического подсчета КБЖУ)"
                ),
                reply_markup=kb.genders,
            )

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)


@router.message(Registration.kbju)
async def get_kbju(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        validators.ValuesKBJU(KBJU=message.text)

        kbju = format_kbju(message.text)

        await state.update_data(kbju=kbju)

        data = await state.get_data()

        goal = data.get("goal")
        height = data.get("height")
        weight = data.get("weight")
        kbju = data.get("kbju")
        calories_goal = float(kbju[0])
        belki = float(kbju[1])
        jiri = float(kbju[2])
        uglevodi = float(kbju[3])

        await db.save_data(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            goal=goal,
            height=height,
            weight=weight,
            calories_goal=float(calories_goal),
            belki=float(belki),
            jiri=float(jiri),
            uglevodi=float(uglevodi),
        )

        await message.answer(
            text=(
                "Круто! Теперь можешь пользоваться кнопками на месте твоей клавиатуры,"
                " чтобы пользоваться функциями бота."
            ),
            reply_markup=kb.main_kb,
        )
        await state.clear()

    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        await message.answer(text=msg)


@router.message(Registration.gender)
async def get_gender(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        validators.Registration(gender=message.text)
        await state.update_data(gender=message.text)
        await state.set_state(Registration.activity)
        await message.answer(
            text="Выбери уровень твоей активности:", reply_markup=kb.activity
        )

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)


@router.message(Registration.activity)
async def get_activity(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        validators.Registration(activity_level=message.text)

        await state.update_data(activity=message.text)
        await state.set_state(Registration.description)
        await message.answer(
            text="Теперь дай описание своей активности, к примеру:\n\n"
            "'3 силовые тренировки в неделю', 'особо нет активности,"
            " максимум по дому похожу', 'легкие прогулки каждый день'",
            reply_markup=ReplyKeyboardRemove(),
        )

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)


@router.message(Registration.description)
async def get_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()

    temp_message = await message.answer(text="Идет вычисление...")

    result = await auto_set_kbju(
        age=data.get("age"),
        height=data.get("height"),
        weight=data.get("weight"),
        goal=data.get("goal"),
        gender=data.get("gender"),
        activity=data.get("activity"),
        activity_desc=data.get("description"),
    )

    k, b, j, u = result.split()

    await message.answer(
        text=(
            f"Автоматически для тебя была выбрана норма:\n"
            f"К - {k}\n"
            f"Б - {b}\n"
            f"Ж - {j}\n"
            f"У - {u}\n"
            "Теперь можешь пользоваться кнопками на месте твоей клавиатуры, "
            "чтобы пользоваться функциями бота."
        ),
        reply_markup=kb.main_kb,
    )

    await temp_message.delete()

    await db.save_data(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        goal=data.get("goal"),
        height=data.get("height"),
        weight=data.get("weight"),
        calories_goal=float(k),
        belki=float(b),
        jiri=float(j),
        uglevodi=float(u),
    )

    await state.clear()


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(text=HELP_TEXT)


@router.message(F.text == "🥗 Добавить продукт")
async def add_product(message: Message, state: FSMContext):
    await state.set_state(DescForProduct.desc)

    await message.answer(
        text="Введите описание того, что хотите добавить:\n\n"
        "Пример: 150г куриной грудки и 200г риса"
    )


@router.message(DescForProduct.desc)
async def get_desc_product(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    product_kbju = await get_product_kbju(message.text)

    try:
        validators.ValuesKBJU(KBJU=product_kbju)

        k, b, j, u = product_kbju.split()

        today = date.today().isoformat()
        progress_for_check = await db.show_daily_progress(
            user_id=message.from_user.id, today_date=today
        )

        if progress_for_check:
            await db.add_product_to_progress(
                user_id=message.from_user.id,
                calories=float(k),
                belki=float(b),
                jiri=float(j),
                uglevodi=float(u),
                date=today,
            )
        else:
            await db.create_day_by_product(
                user_id=message.from_user.id,
                calories=float(k),
                belki=float(b),
                jiri=float(j),
                uglevodi=float(u),
                date=today,
            )

        await message.answer(text="КБЖУ продукта добавлены к прогрессу за сегодня!")

        await state.clear()

    except ValidationError as e:
        msg = format_errors(e.errors()[0]["msg"])
        await message.answer(text=msg)


@router.message(F.text == "🕰️ Прогресс за сегодня")
async def show_daily_progress(message: Message):
    today = date.today().isoformat()

    progress = await db.show_daily_progress(
        user_id=message.from_user.id, today_date=today
    )
    progress_goal = await db.get_progress_goal(telegram_id=message.from_user.id)

    if progress:
        text = format_daily_progress(progress=progress, progress_goal=progress_goal)
        await message.answer(text=text)
    else:
        await message.answer(
            text="Сегодня ты еще ничего не ел. Не забудь поесть сегодня!"
        )


@router.message(F.text == "🗓️ Отобразить историю недели")
async def show_week_history(message: Message):
    history = await db.show_week_history(user_id=message.from_user.id)
    progress_goal = await db.get_progress_goal(telegram_id=message.from_user.id)
    
    text = format_week_history(history=history, progress_goal=progress_goal)

    await message.answer(text=text)


@router.message(F.text == "🙂 Мой профиль")
@router.message(Command("profile"))
async def show_profile(message: Message):
    data = await db.get_profile(message.from_user.id)

    name, goal, height, weight, calories_goal, belki, jiri, uglevodi = data

    if height == int(height):
        height = int(height)

    if weight == int(weight):
        weight = int(weight)

    if calories_goal == int(calories_goal):
        calories_goal = int(calories_goal)

    if belki == int(belki):
        belki = int(belki)

    if jiri == int(jiri):
        jiri = int(jiri)

    if uglevodi == int(uglevodi):
        uglevodi = int(uglevodi)

    await message.answer(
        text=f"Вот мини версия твоего профиля:\n\n"
        f"Имя: {name}\n"
        f"Рост: {height}\n"
        f"Вес: {weight}\n"
        f"Текущая цель: {goal}\n\n"
        f"Текущие значения КБЖУ:\n"
        f"К - {calories_goal}\n"
        f"Б - {belki}\n"
        f"Ж - {jiri}\n"
        f"У - {uglevodi}\n\n"
        "(/edit - изменить профиль)"
    )


@router.message(Command("edit"))
async def edit_profile(message: Message, state: FSMContext):
    await state.set_state(EditProfile.object)
    await message.answer(
        text="Какую вещь хочешь изменить?\n\n"
        "(если хочешь изменить несколько значений, "
        "проще будет использовать /go, "
        "чтобы заполнить профиль заново)",
        reply_markup=kb.edit_profile,
    )


@router.message(EditProfile.object, F.text == "Значения КБЖУ")
async def get_new_kbju(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_kbju)
    await message.answer(
        text=("Введи новые значения КБЖУ:\nПример: 2500 120 60 370"),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(UpdateProfile.new_kbju)
async def update_kbju(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        validators.ValuesKBJU(KBJU=message.text)

        kbju_value = format_kbju(message.text)

        calories_goal = kbju_value[0]
        belki = kbju_value[1]
        jiri = kbju_value[2]
        uglevodi = kbju_value[3]

        await db.update_data(
            user_id=message.from_user.id,
            calories_goal=calories_goal,
            belki=belki,
            jiri=jiri,
            uglevodi=uglevodi,
        )

        await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)
        await state.clear()

    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        await message.answer(text=msg)


@router.message(EditProfile.object, F.text == "Рост")
async def get_new_height(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_height)
    await message.answer(
        text="Введи новое значение роста:", reply_markup=ReplyKeyboardRemove()
    )


@router.message(UpdateProfile.new_height)
async def update_height(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        height_value = float(message.text)
        validators.Registration(height=height_value)

        await db.update_data(user_id=message.from_user.id, height=height_value)
        await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)

        await state.clear()

    except ValueError:
        await message.answer(text="Рост должен быть целым/вещественным числом.")

    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        await message.answer(text=msg)


@router.message(EditProfile.object, F.text == "Вес")
async def get_new_weight(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_weight)
    await message.answer(
        text="Введи новое значение веса:", reply_markup=ReplyKeyboardRemove()
    )


@router.message(UpdateProfile.new_weight)
async def update_weight(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        weight_value = float(message.text)
        validators.Registration(weight=weight_value)

        await db.update_data(user_id=message.from_user.id, weight=weight_value)
        await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)

        await state.clear()

    except ValueError:
        await message.answer(text="Вес должен быть целым/вещественным числом.")

    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        await message.answer(text=msg)


@router.message(EditProfile.object, F.text == "Цель")
async def get_new_goal(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_goal)
    await message.answer(
        text="Какая твоя новая цель?", reply_markup=kb.gain_lose_weight
    )


@router.message(UpdateProfile.new_goal)
async def update_goal(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
        return

    try:
        goal = message.text
        validators.Registration(goal=goal)

        await db.update_data(user_id=message.from_user.id, goal=goal)
        await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)

        await state.clear()

    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        await message.answer(text=msg)
