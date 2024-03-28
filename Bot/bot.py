from aiogram import Bot, Dispatcher
from Bot.handlers import main_handlers


class TgBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token, parse_mode='HTML')
        self.dp = Dispatcher()
        self.dp.include_routers(
            main_handlers.router
        )

    async def start_bot(self):
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)
