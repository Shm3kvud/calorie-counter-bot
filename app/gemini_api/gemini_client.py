from configs.config import GEMINI_API_KEY
from google import genai


client = genai.Client(api_key=GEMINI_API_KEY).aio
model = "gemini-2.5-flash"


async def auto_set_kbju(age, height, weight, goal, gender, activity, activity_desc):
    text = f"""Ты — нутрициолог. Составь норму КБЖУ:
    Возраст: {age}, Рост: {height}см, Вес: {weight}кг
    Пол: {gender}, Цель: {goal}, Активность: {activity}
    Описание активности: {activity_desc} (если введен бред — проигнорировать)
    Ответ в формате: К Б Ж У
    Пример: 2500 120 60 370
    СТРОГО через пробел, без лишних слов"""

    response = await client.models.generate_content(model=model, contents=text)

    response_text = response.text.strip()

    return response_text


async def get_product_kbju(description):
    text = f"""Задача: посчитать суммарное КБЖУ блюда по описанию.
    Описание: {description}
    Для сложных или редких продуктов используй МАКСИМАЛЬНО средние значения,
    даже если посчитать нельзя, или значения будут неверные, 
    все равно считай.
    Формат вывода СТРОГО: К Б Ж У
    Пример: 525 66 7.5 44
    Если ввод — бред (напр. "съел 200г камазов") — вывести ровно: ПЛОХИЕ ДАННЫЕ
    Только эти слова, через пробел, заглавными."""

    response = await client.models.generate_content(model=model, contents=text)

    response_text = response.text.strip()

    return response_text
