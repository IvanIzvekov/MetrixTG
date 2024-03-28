import asyncio
from datetime import datetime

import environs

from Bot.bot import TgBot


# from DB import connect_db


if __name__ == '__main__':
    env = environs.Env()
    env.read_env()

    # connect_db.Base.metadata.create_all(bind=connect_db.engine)

    bot = TgBot(token=env('BOT_TOKEN'))

    print(f'Бот запущен в {datetime.now()}')

    asyncio.run(bot.start_bot())
