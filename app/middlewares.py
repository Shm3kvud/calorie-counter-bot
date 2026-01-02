from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable


class TextCheckMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]) -> Any:
        state = data.get('state')
        
        if state:
            current_state = await state.get_state()
            if current_state: 
                if event.text is None:
                    await event.answer(text="Кажется, ты не ввел текст, попробуй еще раз.")
                    return
        
        return await handler(event, data)