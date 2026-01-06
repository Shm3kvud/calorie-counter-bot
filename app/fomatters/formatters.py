from datetime import date, timedelta


def format_kbju(string: str):
    result = string.split()
    return result


def format_errors(string: str):
    result = string[string.find(",") + 2 :]
    return result


def format_daily_progress(progress: tuple, progress_goal: tuple):
    result_text = ""
    try:
        calories, belki, jiri, uglevodi = progress
        calories_goal, belki_goal, jiri_goal, uglevodi_goal = progress_goal

        result_text = f"""Текущие значения:
К - {int(calories)}/{int(calories_goal)}
Б - {int(belki)}/{int(belki_goal)}
Ж - {int(jiri)}/{int(jiri_goal)}
У - {int(uglevodi)}/{int(uglevodi_goal)}"""

        return result_text

    except Exception:
        result_text = "Что-то пошло не так"
        return result_text


def format_week_history(history: list, progress_goal: tuple):
    today_date = date.today()
    dates = list((today_date - timedelta(days=i)).isoformat() for i in range(0, 7))
    layout = [(0, 0, 0, 0, date_) for date_ in reversed(dates)]
    result_text = f"История за неделю:\n{'-' * 50}\n"
    calories_goal, belki_goal, jiri_goal, uglevodi_goal = progress_goal

    for day_from_history in range(len(history)):
        for day_from_layout in range(len(layout)):
            if history[day_from_history][-1] == layout[day_from_layout][-1]:
                layout[day_from_layout] = history[day_from_history]
            
    for day_from_layout in layout:
        calories, belki, jiri, uglevodi = day_from_layout[0], day_from_layout[1], day_from_layout[2], day_from_layout[3]
        
        result_text += (
            f"Дата: {day_from_layout[-1]}\n"
            f"К - {int(calories)}/{int(calories_goal)}\n"
            f"Б - {int(belki)}/{int(belki_goal)}\n"
            f"Ж - {int(jiri)}/{int(jiri_goal)}\n"
            f"У - {int(uglevodi)}/{int(uglevodi_goal)}\n"
            f"{'-' * 50}\n"
        )

    return result_text
