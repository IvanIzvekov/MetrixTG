from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def help_exel():
    buttons = [
        [
            InlineKeyboardButton(
                text='Как получить отчет с Wildberries?',
                callback_data="help_wb_report"
            )
        ],
        [
            InlineKeyboardButton(
                text='Как получить отчет с Ozon?',
                callback_data="help_ozon_report"
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
    buttons = [[
        KeyboardButton(
            text='Добавить ежедневный отчет'
        ),
        KeyboardButton(
            text='Добавить кабинет'
        )
    ]]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
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
    two_buttons = []
    for cabinet in cabinets['cabinet_name']:
        if len(two_buttons) == 2:
            buttons.append(two_buttons)
            two_buttons = []
        two_buttons.append(
            KeyboardButton(
                text=cabinet
            )
        )
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
