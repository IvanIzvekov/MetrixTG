from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def help_exel_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text='Как получить отчет с Wildberries?',
                callback_data="help_wb_report"
            )
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def help_wb_statistic_token_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text='Как получить токен статистики Wildberries?',
                callback_data='help_wb_statistic_token'
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def help_ozon_token_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text='Как получить токен Ozon?',
                callback_data='help_ozon_token'
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def help_ozon_id_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text='Как получить ID клиента Ozon?',
                callback_data='help_ozon_id'
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def help_wb_promo_token_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text='Как получить токен продвижения Wildberries?',
                callback_data='help_wb_promo_token'
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_reg_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Поделиться номером телефона',
                request_contact=True
            )
        ]
    ]

    registration_keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return registration_keyboard


def add_cabinet_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Добавить кабинет'
            )
        ]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard


def select_MP():
    buttons = [[
        KeyboardButton(
            text='Ozon'
        ),
        KeyboardButton(
            text='Wildberries'
        )
    ]]

    registration_keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return registration_keyboard


def main_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Добавить еженедельный отчет'
            ),
            KeyboardButton(
                text='Добавить кабинет'
            )
        ],
        [
            KeyboardButton(
                text='Изменить токены'
            ),
            KeyboardButton(
                text='Написать в тех. поддержку'
            )
        ]]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

    return keyboard


def back_to_main_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Назад в меню'
            )
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard


def all_cabinets(cabinets):
    buttons = []
    count = 0
    for cabinet in cabinets['cabinet_name']:
        if cabinets['mp'][count] == "WB":
            text = cabinet + " (WB)"
        else:
            text = cabinet + " (OZON)"
        buttons.append(
            [
                KeyboardButton(
                    text=text
                )
            ]
        )
        count += 1
    buttons.append(
        [
            KeyboardButton(
                text='Назад в меню'
            )
        ]
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard


def select_date(dates, is_admin=False):
    buttons = []
    for date in dates:
        buttons.append(
            [
                KeyboardButton(
                    text=date
                )
            ]
        )
    buttons = buttons[::-1]
    if not is_admin:
        buttons.append(
            [
                KeyboardButton(
                    text='Назад в меню'
                )
            ]
        )
    else:
        buttons.append(
            [
                KeyboardButton(
                    text='/start'
                )
            ]
        )
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard


def turnover_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Менее 300 тыс. руб.'
            ),
            KeyboardButton(
                text='300 - 500 тыс. руб.'
            )
        ],
        [
            KeyboardButton(
                text='500 - 1 000 тыс. руб.'
            ),
            KeyboardButton(
                text='1 000 - 2 000 тыс. руб.'
            )
        ],
        [
            KeyboardButton(
                text='Свыше 2 000 тыс. руб.'
            )
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard


def quarter_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='(2022-12-26 - 2023-04-02)'
            ),
            KeyboardButton(
                text='(2023-04-03 - 2023-07-02)'
            )
        ],
        [
            KeyboardButton(
                text='(2023-07-03 - 2023-10-01)'
            ),
            KeyboardButton(
                text='(2023-10-02 - 2023-12-31)'
            )
        ],
        [
            KeyboardButton(
                text='(2024-01-01 - 2024-01-28)'
            )
        ]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    return keyboard


def wb_token_select_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Статистика'
            ),
            KeyboardButton(
                text='Продвижение'
            )
        ],
        [
            KeyboardButton(
                text='Назад в меню'
            )
        ]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    return keyboard


def ozon_token_select_keyboard():
    buttons = [
        [
            KeyboardButton(
                text='Seller API'
            )
            # ,
            # KeyboardButton(
            #     text='Performance API'
            # )
        ],
        [
            KeyboardButton(
                text='Назад в меню'
            )
        ]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    return keyboard
