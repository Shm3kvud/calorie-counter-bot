from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional



class Registration(BaseModel):
    age: Optional[int] = Field(None, description="возраст, от 12 до 122")
    height: Optional[float] = Field(None, desValueErrorcription="рост, от 130 до 210")
    weight: Optional[float] = Field(None, description="вес, от 20 до 300")
    goal: Optional[str] = Field(None, description="цель")
    kbju_setting: Optional[str] = Field(None, description="вариант установки кбжу")
    gender: Optional[str] = Field(None, description="пол")
    activity_level: Optional[str] = Field(None, description="уровень активности")
    
    
    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v and v < 12:
            raise ValueError("Минимальный возраст - 12.")
        if v and v > 122:
            raise ValueError("Максимальный возраст - 122.")
        return v
    
    @field_validator("height")
    @classmethod
    def validate_height(cls, v):
        if v and v < 130:
            raise ValueError("Минимальный рост - 130.")
        if v and v > 210:
            raise ValueError("Максимальный рост - 210.")
        return v
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v and v < 20:
            raise ValueError("Минимальный вес - 20.")
        if v and v > 300:
            raise ValueError("Максимальный вес - 300.")
        return v
    
    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v):
        if v and (v not in ("Набрать", "Похудеть")):
            raise ValueError("Нажми на кнопки на месте твоей клавиатуры для выбора.")
        return v
    
    @field_validator("kbju_setting")
    @classmethod
    def validate_kbju_setting(cls, v):
        if v and (v not in ("Самостоятельно", "Автоматически")):
            raise ValueError("Нажми на кнопки на месте твоей клавиатуры для выбора.")
        return v
        
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and (v not in ("Мужской", "Женский")):
            raise ValueError("Нажми на кнопки на месте твоей клавиатуры для выбора.")
        return v
    
    @field_validator("activity_level")
    @classmethod
    def validate_activity_level(cls, v):
        if v and (v not in ("Низкая", "Умеренная", "Высокая")):
            raise ValueError("Нажми на кнопки на месте твоей клавиатуры для выбора.")
        return v
    
    @model_validator(mode="after")
    def validate_imt(self):
        if self.height and self.weight:
            imt = (self.weight / ((self.height / 100) ** 2))
            
            if imt < 10:
                raise ValueError(
                    "Ваш ИМТ получается слишком маленьким, "
                    "это значение летально, введите верный вес."
                    )
            
            if imt > 81:
                raise ValueError(
                    "Ваш ИМТ получается слишком высоким, "
                    "такое значение крайне редкое и опасное, "
                    "проконсультируйтесь с врачом/введите верное значение веса."
                    )
            
        return self
    
class ValuesKBJU(BaseModel):
    #передаю значение кбжу фулл строкой тк без этого смысл валидатора теряется просто
    #там можно тогда и без него было бы сделать, а я хочу минимизировать
    #валидацию в хендлерах
    KBJU: str = Field(min_length=7,
                      max_length=20,
                      description="значения КБЖУ, передаются строкой")
    
    @model_validator(mode="after")
    def validate_values(self):
        try:
            if self.KBJU == "ПЛОХИЕ ДАННЫЕ":
                raise ValueError("Возможно, ты ввел что-то не то, попробуй еще раз.")
            
            calories, belki, jiri, uglevodi = self.KBJU.split()
            
            calories, belki, jiri, uglevodi = float(calories), float(belki), float(jiri), float(uglevodi)
            
        except ValueError:
            raise ValueError(
                "Данные введены в неверном формате."
            )
        except AttributeError:
            raise AttributeError(
                "Кажется, ты не ввел текст, попробуй еще раз."
            )
        
        return self