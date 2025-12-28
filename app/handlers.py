from datetime import date
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from texts import HELP_TEXT
from states import Registration, UpdateProfile, EditProfile, DescForProduct
from app import keyboards as kb
from database.sqlite_db import db
from app.formatters import format_kbju
from app.gemini_client import auto_set_kbju, get_product_kbju


#сделал обращение к геминай, нужно продлить чат акшн, +протестить добавление продукта и доделать его в целом


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(text=("Привет! Это бот - счетчик калорий. "
                               "Он поможет тебе следить за твоим рационом и набрать/похудеть.\n\n"
                               "Жми /go для начала работы!\n"
                               "Команда /cancel поможет отменить тебе любое текущее действие.\n\n"))
    
    
@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Действие отменено.", reply_markup=kb.main_kb)


@router.message(Command("go"))
async def reg_user(message: Message, state: FSMContext):
    check = await db.get_profile(telegram_id=message.from_user.id)
    if check: 
        await message.answer(text="Твой профиль уже существует, хочешь продолжить с ним или заполнить его заново?", reply_markup=kb.continue_or_again)
    else:
        await state.set_state(Registration.age)
        await message.answer(text="Отлично! Введи свой возраст:", reply_markup=ReplyKeyboardRemove())
    

@router.message(F.text == "Продолжить")
async def continue_with_profile(message: Message):
    await message.answer(text="Можешь пользоваться ботом дальше.", reply_markup=kb.main_kb)


@router.message(F.text == "Заново")
async def fill_again(message: Message, state: FSMContext):
    await state.set_state(Registration.age)
    await message.answer(text="Отлично! Введи свой возраст:", reply_markup=ReplyKeyboardRemove())


@router.message(Registration.age)
async def get_age(message: Message, state: FSMContext):
    age = int(message.text)
    await state.update_data(age=age)
    await state.set_state(Registration.height)
    await message.answer(text="Хорошо! Введи свой текущий рост:")
    
    
@router.message(Registration.height)
async def get_height(message: Message, state: FSMContext):
    height = float(message.text)
    await state.update_data(height=height)
    await state.set_state(Registration.weight)
    await message.answer(text="Прекрасно! Введи свой текущий вес:")
    

@router.message(Registration.weight)
async def get_weight(message: Message, state: FSMContext):
    weight = float(message.text)
    await state.update_data(weight=weight)
    await state.set_state(Registration.goal)
    await message.answer(text="Принято! Ты бы хотел(-а) набрать или похудеть?", reply_markup=kb.gain_lose_weight)
    
    
@router.message(Registration.goal)
async def get_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await message.answer(text=("Замечательно! Теперь выбери, установить"
                               " значения КБЖУ самостоятельно или автоматически?"), reply_markup=kb.auto_or_by_yrslf)
    await state.set_state(Registration.yourself_or_ai)
    
    
@router.message(Registration.yourself_or_ai)
async def auto_or_ai(message: Message, state: FSMContext):
    await state.update_data(yourself_or_ai=message.text)
    
    if message.text == "Самостоятельно":
        await state.set_state(Registration.kbju)
        await message.answer(text=("Введи значения КБЖУ:\n"
                               "Пример: 2500 120 60 370"), reply_markup=ReplyKeyboardRemove())
    elif message.text == "Автоматически":
        await state.set_state(Registration.gender)
        await message.answer(text=("Выбери свой пол:\n\n"
                                   "(этот и последующие выборы нужны для автоматического подсчета КБЖУ)"),
                             reply_markup=kb.genders)
    

@router.message(Registration.kbju)
async def get_kbju(message: Message, state: FSMContext):
    kbju = format_kbju(message.text)
    
    await state.update_data(kbju=kbju)
    
    data = await state.get_data()
    
    goal = data["goal"]
    height = data["height"]
    weight = data["weight"]
    calories_goal = float(data["kbju"][0])
    belki = float(data["kbju"][1])
    jiri = float(data["kbju"][2])
    uglevodi = float(data["kbju"][3])
    
    await db.save_data_in_db(telegram_id=message.from_user.id,
                                   full_name=message.from_user.full_name,
                                   goal=goal,
                                   height=height,
                                   weight=weight,
                                   calories_goal=float(calories_goal),
                                   belki=float(belki),
                                   jiri=float(jiri),
                                   uglevodi=float(uglevodi)
                                   )
    
    await message.answer(text=("Круто! Теперь можешь пользоваться кнопками на месте твоей клавиатуры,"
                               " чтобы пользоваться функциями бота."), reply_markup=kb.main_kb)
    await state.clear()
    

@router.message(Registration.gender)
async def get_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await state.set_state(Registration.activity)
    await message.answer(text="Выбери уровень твоей активности:", reply_markup=kb.activity)


@router.message(Registration.activity)
async def get_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await state.set_state(Registration.description)
    await message.answer(text="Теперь дай описание своей активности, к примеру:\n\n"
                         "'3 силовые тренировки в неделю', 'особо нет активности,"
                         " максимум по дому похожу', 'легкие прогулки каждый день'", reply_markup=ReplyKeyboardRemove())
    
    
@router.message(Registration.description)
async def get_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()

    temp_message = await message.answer(text="Идет вычисление...")
    
    result = await auto_set_kbju(age=data["age"], 
                                 height=data["height"],
                                 weight=data["weight"],
                                 goal=data["goal"],
                                 gender=data["gender"],
                                 activity=data["activity"],
                                 activity_desc=data["description"])
    
    k, b, j, u = result.split()
    
    await message.answer(text=(f"Автоматически для тебя была выбрана норма в {k} {b} {j} {u}!"
                               " Теперь можешь пользоваться кнопками на месте твоей клавиатуры,"
                               " чтобы пользоваться функциями бота."), reply_markup=kb.main_kb)
    
    await temp_message.delete()
    
    await db.save_data_in_db(telegram_id=message.from_user.id,
                                   full_name=message.from_user.full_name,
                                   goal=data["goal"],
                                   height=data["height"],
                                   weight=data["weight"],
                                   calories_goal=float(k),
                                   belki=float(b),
                                   jiri=float(j),
                                   uglevodi=float(u))
    
    await state.clear()



@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(text=HELP_TEXT)
    

@router.message(F.text == "🥗 Добавить продукт")
async def add_product(message: Message, state: FSMContext):
    await state.set_state(DescForProduct.desc)
    
    await message.answer(text="Введите описание того, что хотите добавить:\n\n"
                         "Пример: 150г куриной грудки и 200г риса")
    
    
@router.message(DescForProduct.desc)
async def get_desc_product(message: Message, state: FSMContext):
    product_kbju = await get_product_kbju(message.text)
    
    #валидировать
    #если что то пойдет не так попросить еще раз, либо нажать /cancel
    print(product_kbju)
    k, b, j, u = product_kbju.split()
    
    today = date.today().isoformat()
    progress_for_check = await db.show_daily_progress_from_db(user_id=message.from_user.id,
                                                    today_date=today)
    
    if progress_for_check:
        await db.add_product_to_progress(user_id=message.from_user.id,
                                         calories=float(k),
                                         belki=float(b),
                                         jiri=float(j),
                                         uglevodi=float(u),
                                         date=today)
    else:
        await db.create_day_by_product_in_db(user_id=message.from_user.id,
                                             calories=float(k),
                                             belki=float(b),
                                             jiri=float(j),
                                             uglevodi=float(u),
                                             date=today)
        
    await message.answer(text="КБЖУ продукта добавлены к прогрессу за сегодня!")
    
    await state.clear()
        
        

@router.message(F.text == "🕰️ Прогресс за сегодня")
async def show_daily_progress(message: Message):
    today = date.today().isoformat()
    
    progress = await db.show_daily_progress_from_db(user_id=message.from_user.id,
                                                    today_date=today)
    
    calories, belki, jiri, uglevodi = progress

    if progress:
        format_progress = f'Текущие значения кбжу: {calories} | {belki} | {jiri} | {uglevodi}'
        await message.answer(text=format_progress)
    else:
        await message.answer(text="Сегодня ты еще ничего не ел. Не забудь поесть сегодня!")


@router.message(F.text == "🗓️ Отобразить историю недели")
async def show_week_history(message: Message):
    history = await db.show_week_history_from_db(user_id=message.from_user.id)
    
    await message.answer(text=f'{history}')


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
        
    await message.answer(text=f"Вот мини версия твоего профиля:\n\n"
                         f"Имя: {name}\n"
                         f"Рост: {height}\n"
                         f"Вес: {weight}\n"
                         f"Текущая цель: {goal}\n\n"
                         f"Текущие значения КБЖУ:\n {calories_goal}к | {belki}б | {jiri}ж | {uglevodi}у\n\n"
                          "(/edit - изменить профиль)")
    
    
@router.message(Command("edit"))
async def edit_profile(message: Message, state: FSMContext):
    await state.set_state(EditProfile.object)
    await message.answer(text="Какую вещь хочешь изменить?\n\n"
                         "(если хочешь изменить несколько значений, "
                         "проще будет использовать /go, "
                         "чтобы заполнить профиль заново)", reply_markup=kb.edit_profile)


@router.message(EditProfile.object, F.text == "Значения КБЖУ")
async def input_new_kbju(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_kbju)
    await message.answer(text=("Введи новые значения КБЖУ:\n"
                               "Пример: 2500 120 60 370"), reply_markup=ReplyKeyboardRemove())


@router.message(UpdateProfile.new_kbju)
async def update_kbju(message: Message, state: FSMContext):
    kbju_value = format_kbju(message.text)
    
    calories_goal = kbju_value[0]
    belki = kbju_value[1]
    jiri = kbju_value[2]
    uglevodi = kbju_value[3]
    
    await db.update_data_in_db(user_id=message.from_user.id,
                               calories_goal=calories_goal,
                               belki=belki,
                               jiri=jiri,
                               uglevodi=uglevodi)
    
    await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)
    await state.clear()
    
    
@router.message(EditProfile.object, F.text == "Рост")
async def input_new_height(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_height)
    await message.answer(text="Введи новое значение роста:", reply_markup=ReplyKeyboardRemove())
    
    
@router.message(UpdateProfile.new_height)
async def update_height(message: Message, state: FSMContext):
    height_value =  message.text
    
    await db.update_data_in_db(user_id=message.from_user.id, height=height_value)
    await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)
    
    await state.clear()
    
    
@router.message(EditProfile.object, F.text == "Вес")
async def input_new_weight(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_weight)
    await message.answer(text="Введи новое значение веса:", reply_markup=ReplyKeyboardRemove())
    
    
@router.message(UpdateProfile.new_weight)
async def update_weight(message: Message, state: FSMContext):
    weight_value =  message.text
    
    await db.update_data_in_db(user_id=message.from_user.id, weight=weight_value)
    await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)
    
    await state.clear()
    
    
@router.message(EditProfile.object, F.text == "Цель")
async def input_new_goal(message: Message, state: FSMContext):
    await state.set_state(UpdateProfile.new_goal)
    await message.answer(text="Какая твоя новая цель?", reply_markup=kb.gain_lose_weight) 
    
    
@router.message(UpdateProfile.new_goal)
async def update_goal(message: Message, state: FSMContext):
    goal =  message.text
    
    await db.update_data_in_db(user_id=message.from_user.id, goal=goal)
    await message.answer(text="Данные успешно обновлены!", reply_markup=kb.main_kb)
    
    await state.clear()