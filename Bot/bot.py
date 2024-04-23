from aiogram import Bot, Dispatcher
from Bot.handlers import main_handlers, admin_handlers
from Bot.functions.main_functions import check_potential_users, clear_potential_users
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from environs import Env

env = Env()
env.read_env()


class TgBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token, parse_mode='HTML')
        self.dp = Dispatcher()
        self.sheduler = AsyncIOScheduler()
        self.sheduler.add_job(check_unauthorized_users, 'cron', hour='*', minute=0, args=[self.bot])
        self.dp.include_routers(
            main_handlers.router,
            admin_handlers.router
        )

    async def start_bot(self):
        await self.bot.delete_webhook(drop_pending_updates=True)
        self.sheduler.start()
        await self.dp.start_polling(self.bot)


async def check_unauthorized_users(bot: Bot):
    all_potential_users = check_potential_users()
    message_for_manager = "Список клиентов незавершивших авторизацию в течении последних суток:\n"
    count = 1
    if not all_potential_users:
        return
    tg_id_list = []
    for user in all_potential_users:
        message_for_manager += (f"{count})  TG Username: @{user[4]}\n"
                                f"Имя: {user[1]}\n"
                                f"Телефон: {user[2]}\n"
                                f"Оборот: {user[3]}\n"
                                f"Дата начала регистрации: {user[5].strftime('%d.%m.%Y %H:%M')}\n\n")
        count += 1
        tg_id_list.append(user[0])
    message_for_manager += f"#Не_завершил"
    clear_potential_users(tuple(tg_id_list))
    await bot.send_message(env('MANAGER_CHAT_ID'), text=message_for_manager)
