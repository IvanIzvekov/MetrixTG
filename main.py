import asyncio
from datetime import datetime
import environs
from Bot.bot import TgBot

if __name__ == '__main__':
    env = environs.Env()
    env.read_env()

    bot = TgBot(token=env('BOT_TOKEN'))

    print(f'Бот запущен в {datetime.now()}')

    asyncio.run(bot.start_bot())
