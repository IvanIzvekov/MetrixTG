import io
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    FSInputFile, ContentType

from Bot.keyboards.main_keyboards import *
from Bot.states.user_info_states import *
from Bot.functions.main_functions import *
from environs import Env

env = Env()
env.read_env()

router = Router()


def has_cyrillic(text):
    return any('\u0400' <= char <= '\u04FF' for char in text)


############################ Основное меню ############################
async def main_menu(message: Message, state: FSMContext):
    await state.set_state(
        Cabinet.startCreateCabinet)
    await message.answer(
        text="Это главное меню, здесь вы можете добавить ежедневный отчет к свому кабинету, или добавить новый кабинет",
        reply_markup=main_keyboard())


@router.message(Cabinet.startCreateCabinet, F.text == "Добавить еженедельный отчет")
async def every_day_report(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="every_day_report",
             input_data=message.text)

    user_data = await state.get_data()
    cabinets = await find_cabinets(user_data['client_id'])
    await state.set_state(MainMenu.selectCabinet)
    await message.answer(text="Выберите кабинет:", reply_markup=all_cabinets(cabinets))


@router.message(F.text == "Назад в меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if "client_id" in user_data:
        await main_menu(message, state)
    else:
        await cmd_start(message, state)


@router.message(MainMenu.selectCabinet)
async def select_cabinet(message: Message, state: FSMContext):
    if not await have_cabinet(message.text):
        await message.answer(text="Такого кабинета не существует, пожалуйста введите название кабинета полностью, "
                                  "либо воспользуйтесь клавиатурой ниже", reply_markup=ReplyKeyboardRemove())
        await every_day_report(message, state)
    else:
        user_data = await state.get_data()
        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone=str(user_data["phone_number"]),
                 is_client=True if user_data["client_id"] else False,
                 tg_command="select_cabinet",
                 input_data=message.text)
        await state.update_data(cabinet_name=message.text)
        await state.set_state(MainMenu.selectDateExcel)
        cabinet_name = message.text
        await message.answer(text="Смотрим возможные даты для загрузки отчета...")
        await message.answer(text="Выберите дату отчета из предложенных ниже",
                             reply_markup=select_date(gen_date_excel(cabinet_name)))
        await state.set_state(MainMenu.selectedDateExcel)


@router.message(MainMenu.selectedDateExcel)
async def selected_date_excel(message: Message, state: FSMContext):
    user_data = await state.get_data()
    all_dates_invalid = gen_date_excel(user_data["cabinet_name"])
    all_dates = [i[16:] for i in all_dates_invalid]
    if len(message.text) == 26:
        if message.text[16:] not in all_dates:
            await message.answer(text="Такая дата отчета не существует, пожалуйста введите дату отчета из приведенных ниже")
            return
    else:
        await message.answer(text="Такая дата отчета не существует, пожалуйста введите дату отчета из приведенных ниже")
        return
    await state.update_data(dateExcel=message.text)

    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if user_data["client_id"] else False,
             tg_command="select_data_excel",
             input_data=message.text)

    await message.answer(text=f"Выбранная дата - {message.text}", reply_markup=back_to_main_keyboard())
    await state.set_state(MainMenu.waitExcel)
    await message.answer(text="Отправьте отчет в виде архива с одним Excel файлом\n По одному архиву за раз")


@router.message(MainMenu.waitExcel, F.content_type == ContentType.DOCUMENT)
async def wait_excel(message: Message, state: FSMContext):
    # if len(message.attachments) > 1:
    #     await message.answer(text="Пожалуйста, отправьте отчет в виде архива с одним Excel файлом\n"
    #                               "В данном случае файлов больше одного")
    #     return
    user_data = await state.get_data()
    await state.update_data(file_id=message.document.file_id)
    file_id = message.document.file_id
    file_name = message.document.file_name
    if file_name[-5:] == ".xlsx":
        await message.answer(
            text="Отправьте .zip архив, который вы скачали с личного кабинета, не изменяя названия содержимого")
    elif file_name[-4:] == ".xls":
        await message.answer(
            text="Отправьте .zip архив, который вы скачали с личного кабинета, не изменяя названия содержимого")
    elif file_name[-4:] == ".zip":
        try:
            os.mkdir(f'reports/{user_data["client_id"]}')
        except FileExistsError:
            await message.answer(text="Пожалуйста, отправьте только один архив с отчетом")
            return
        await message.bot.download(file_id, f'reports/{user_data["client_id"]}/{user_data["client_id"]}.zip')
        if await read_excel_wb_zip(
                "reports/" + str(user_data["client_id"]) + "/" + str(user_data["client_id"]) + ".zip",
                user_data["client_id"],
                file_name,
                user_data['cabinet_name'],
                date_to=user_data['dateExcel']):
            await message.answer(text="Отчет успешно добавлен")
            await main_menu(message, state)
        else:
            await message.answer(text=f"Произошла ошибка, убедитесь, что вы выбрали верный файл, "
                                      f"в случае, если вы уверены, что все делаете верно, свяжитесь с менеджером "
                                      f"@{env('MANAGER_CHAT_ID')}")
    else:
        await message.answer(text="Данный файл не поддерживается, попробуйте снова, но с другим файлом, "
                                  f"в случае, если вы уверены, что все делаете верно, свяжитесь с менеджером "
                                  f"@{env('MANAGER_CHAT_ID')}")


############################### Авторизация и начало создания кабинета ################################
@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=user_data["phone_number"] if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="start",
             input_data="/start")

    await message.answer(text=f'Привет!👋\n\n'
                              f'На связи <b>бот-помощник Metrix</b> - это удобный инструмент для продавцов '
                              f'Wildberries, объединяющий складской учет, товарную, рекламную и финансовую '
                              f'аналитику в одном месте📈\n\nС нашей помощью вы сможете отслеживать прибыль '
                              f'и другие показатели в режиме реального времени🚀', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Authorize.startAuthorize)
    user_data = await state.get_data()
    if "phone_number" not in user_data:
        phone_check, client_id = await check_client_id(message.from_user.id)
        if phone_check != "":
            await state.update_data(client_id=client_id)
            await state.update_data(phone_number=phone_check)
            await main_menu(message, state)
        else:
            await message.answer(text=f'Для авторизации нажмите на кнопку "Отправить мой номер" в меню бота , '
                                      f'чтобы поделиться им с нами.\n\n'
                                      f'Если кнопка не появилась, нажмите на значок рядом с иконкой отправки '
                                      f'сообщения, появится меню с кнопкой.', reply_markup=get_reg_keyboard())
    else:
        await main_menu(message, state)


@router.message(F.contact)
async def get_phone(message: Message, state: FSMContext):
    await message.answer(text=f'Спасибо, {message.contact.first_name}! Ваш номер - {message.contact.phone_number}',
                         reply_markup=ReplyKeyboardRemove())
    await state.update_data(phone_number=message.contact.phone_number)

    client_id_check, client_tg_id = await check_client_number(message.contact.phone_number)
    if client_id_check == "":

        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone=message.contact.phone_number,
                 is_client=None,
                 tg_command="get_phone",
                 input_data=str(message.contact.phone_number))

        await state.set_state(Cabinet.startCreateCabinet)
        await message.answer(text=f'Для начала нужно добавить кабинет', reply_markup=add_cabinet_keyboard())
    else:
        if int(client_tg_id) != message.from_user.id:
            await refresh_tg_id(client_id_check, message.from_user.id)
        await state.update_data(client_id=client_id_check)
        await main_menu(message, state)


@router.message(Cabinet.startCreateCabinet, F.text == "Добавить кабинет")
async def selectMP(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if user_data["client_id"] else False,
             tg_command="selectMP",
             input_data="Добавить кабинет")

    await state.set_state(Cabinet.selectMP)
    await message.answer(text="Кабинет какого маркетплейса вы хотите добавить?", reply_markup=select_MP())


@router.message(Cabinet.selectMP)
async def enter_name(message: Message, state: FSMContext):
    if message.text == "Wildberries":
        await state.update_data(mp="Wildberries")
    elif message.text == "Ozon":
        await state.update_data(mp="Ozon")
    else:
        await message.answer(text="Пожалуйста введите название маркетплейса корректно")
        await state.set_state(Cabinet.startCreateCabinet)
        await selectMP(message, state)
        return
    await state.set_state(Cabinet.inputName)
    await message.answer(text="Введите название кабинета", reply_markup=ReplyKeyboardRemove())


@router.message(Cabinet.inputName)
async def check_cabinet_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    client_id = ""
    if "client_id" in user_data:
        client_id = user_data["client_id"]
    if client_id != "":
        if await check_unic_cabinet(message.text, client_id):
            await state.update_data(cabinet_name=message.text)

            user_data = await state.get_data()
            send_log(tg_id=message.from_user.id,
                     tg_username=message.from_user.username,
                     phone=str(user_data["phone_number"]),
                     is_client=True,
                     tg_command="check_cabinet_name",
                     input_data=user_data["cabinet_name"])

            if user_data["mp"] == "Wildberries":
                await state.set_state(Cabinet.wbTokenStat)
                await wb_tokens_stat(message, state)
            elif user_data["mp"] == "Ozon":
                await state.set_state(Cabinet.ozonTokens)
                await ozon_tokens(message, state)
        else:
            await message.answer(text="У вас уже существует кабинет с таким названием, введите другое")
    else:
        await state.update_data(cabinet_name=message.text)
        user_data = await state.get_data()
        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone=str(user_data["phone_number"]),
                 is_client=False,
                 tg_command="check_cabinet_name",
                 input_data=user_data["cabinet_name"])
        if user_data["mp"] == "Wildberries":
            await state.set_state(Cabinet.wbTokenStat)
            await wb_tokens_stat(message, state)
        elif user_data["mp"] == "Ozon":
            await state.set_state(Cabinet.ozonTokens)
            await ozon_tokens(message, state)


############################ Ввод токенов и их проверка ################################
@router.message(Cabinet.wbTokenStat)
async def wb_token_stat_check(message: Message, state: FSMContext):
    await message.answer(text="Проверяем...")
    if not has_cyrillic(message.text):
        if await check_token_request(message.text, "Wildberries"):
            await state.update_data(token_stat=message.text)

            user_data = await state.get_data()
            send_log(tg_id=message.from_user.id,
                     tg_username=message.from_user.username,
                     phone=str(user_data["phone_number"]),
                     is_client=True if "client_id" in user_data else False,
                     tg_command="wb_token_stat_check",
                     input_data=user_data["token_stat"])

            await wb_tokens_promo(message, state)
        else:
            await message.answer(text="Некорректный токен, попробуйте снова",
                                 reply_markup=help_wb_statistic_token_keyboard())
            await wb_tokens_stat(message, state, repeating=True)
    else:
        await message.answer(text="Некорректный токен, попробуйте снова",
                             reply_markup=help_wb_statistic_token_keyboard())
        await wb_tokens_stat(message, state, repeating=True)


async def wb_tokens_stat(message: Message, state: FSMContext, repeating=False):
    if not repeating:
        await message.answer(text="Введите токен статистики Wildberries",
                             reply_markup=help_wb_statistic_token_keyboard())
    await state.set_state(Cabinet.wbTokenStat)


@router.message(Cabinet.wbTokenPromo)
async def wb_token_promo_check(message: Message, state: FSMContext):
    await message.answer(text="Проверяем...")
    if not has_cyrillic(message.text):
        if await check_token_request(message.text, "Wildberries", promotion=True):
            await state.update_data(token_promo=message.text)

            user_data = await state.get_data()
            send_log(tg_id=message.from_user.id,
                     tg_username=message.from_user.username,
                     phone=str(user_data["phone_number"]),
                     is_client=True if "client_id" in user_data else False,
                     tg_command="wb_token_promo_check",
                     input_data=user_data["token_promo"])

            await success_tokens(message, state)
        else:
            await message.answer(text="Некорректный токен, попробуйте снова",
                                 reply_markup=help_wb_promo_token_keyboard())
            await wb_tokens_promo(message, state, repeating=True)
    else:
        await message.answer(text="Некорректный токен, попробуйте снова",
                             reply_markup=help_wb_promo_token_keyboard())
        await wb_tokens_promo(message, state, repeating=True)


async def wb_tokens_promo(message: Message, state: FSMContext, repeating=False):
    if not repeating:
        await message.answer(text="Введите токен продвижения Wildberries",
                             reply_markup=help_wb_promo_token_keyboard())
    await state.set_state(Cabinet.wbTokenPromo)


@router.message(Cabinet.ozonTokens)
async def ozon_tokens_input(message: Message, state: FSMContext):
    if not has_cyrillic(message.text):
        await state.set_state(Cabinet.ozonId)
        await state.update_data(ozon_seller_token=message.text)
        await message.answer(text="Введите ID клиента Ozon", reply_markup=help_ozon_id_keyboard())
    else:
        await message.answer(text="Некорректный токен, попробуйте снова\nВведите токен Ozon",
                             reply_markup=help_ozon_token_keyboard())
        await ozon_tokens(message, state, repeating=True)


@router.message(Cabinet.ozonId)
async def ozon_id_check(message: Message, state: FSMContext):
    if not has_cyrillic(message.text):
        user_data = await state.get_data()
        if await check_token_request(user_data["ozon_seller_token"], "Ozon", ozon_id=message.text):
            await state.update_data(ozon_id=message.text)

            user_data = await state.get_data()
            send_log(tg_id=message.from_user.id,
                     tg_username=message.from_user.username,
                     phone=str(user_data["phone_number"]),
                     is_client=True if "client_id" in user_data else False,
                     tg_command="ozon_token_and_id_check",
                     input_data=message.text)

            await success_tokens(message, state)
        else:
            await message.answer(text="Некорректный ID или токен, попробуйте снова.\nВведите токен Ozon",
                                 reply_markup=help_ozon_token_keyboard())
            await ozon_tokens(message, state, repeating=True)
    else:
        await message.answer(text="Некорректный ID или токен, попробуйте снова.\nВведите токен Ozon",
                             reply_markup=help_ozon_token_keyboard())
        await ozon_tokens(message, state, repeating=True)


async def ozon_tokens(message: Message, state: FSMContext, repeating=False):
    if not repeating:
        await message.answer(text="Введите токен Ozon", reply_markup=help_ozon_token_keyboard())
    await state.set_state(Cabinet.ozonTokens)


############################ Коллбеки для помощи ################################
@router.callback_query(F.data == "help_ozon_report")
async def help_ozon_report(callback: CallbackQuery):
    await callback.message.answer(text="Фотографии с примерами отчета Ozon")
    await callback.answer()


@router.callback_query(F.data == "help_wb_report")
async def help_wb_report(callback: CallbackQuery):
    await callback.message.answer(text="Фотографии с примерами отчета Wildberries")
    await callback.answer()


@router.callback_query(F.data == "help_ozon_id")
async def help_ozon_id(callback: CallbackQuery):
    await callback.message.answer(text="Фотографии с примерами ID клиента Ozon")
    await callback.answer()


@router.callback_query(F.data == "help_wb_promo_token")
async def help_wb_promo_token(callback: CallbackQuery):
    await callback.message.answer(text="Фотографии с примерами токенов продвижения Wildberries")
    await callback.answer()


@router.callback_query(F.data == "help_wb_statistic_token")
async def help_wb_statistic_token(callback: CallbackQuery):
    await callback.message.answer(text="Фотографии с примерами токенов статистики Wildberries")
    await callback.answer()


@router.callback_query(F.data == "help_ozon_token")
async def help_ozon_token(callback: CallbackQuery):
    await callback.message.answer(text="Фотографии с примерами токенов Ozon")
    await callback.answer()


############################ Последняя часть регистрации ################################
async def success_tokens(message: Message, state: FSMContext):
    await message.answer(text="Успешно!", reply_markup=ReplyKeyboardRemove())
    user_data = await state.get_data()
    if "client_id" in user_data:
        if await create_cabinet_client(user_data):
            user_data = await state.get_data()
            phone = user_data["phone_number"]
            client_id = user_data["client_id"]
            await state.clear()
            await state.set_state(MainMenu.mainMenu)
            await state.update_data(phone_number=phone, client_id=client_id)
            await main_menu(message, state)
        else:
            await message.answer(text="Произошла ошибка, попробуйте снова через некоторое время",
                                 reply_markup=ReplyKeyboardRemove())
            await state.clear()
            await cmd_start(message, state)
    else:
        await state.set_state(Cabinet.gmail)
        gmail = await check_gmail(str(message.from_user.id))
        if gmail == "":
            await message.answer(text="Введите свою почту gmail", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Cabinet.inputGmail)
        else:
            await message.answer(text=f"Ваш почтовый ящик - {gmail}", reply_markup=ReplyKeyboardRemove())
        await state.update_data(gmail=gmail)


@router.message(Cabinet.inputGmail)
async def input_gmail(message: Message, state: FSMContext):
    if message.text.find("@gmail.com") != -1:
        await state.update_data(gmail=message.text)

        user_data = await state.get_data()
        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone=str(user_data["phone_number"]),
                 is_client=True if "client_id" in user_data else False,
                 tg_command="input_gmail",
                 input_data=message.text)

        await state.set_state(Cabinet.final)
        await final(message, state)
    else:
        await message.answer(text="Некорректная почта, нужна именно Google почта\nПример: xxxxxx@gmail.com",
                             reply_markup=ReplyKeyboardRemove())


async def final(message: Message, state: FSMContext):
    await message.answer(text="Регистрация прошла успешно! Ожидайте, скоро с вами свяжется менеджер",
                         reply_markup=ReplyKeyboardRemove())
    user_data = await state.get_data()
    if user_data["mp"] == "Wildberries":
        str = f"Токен статистики: {user_data['token_stat']}\nТокен продвижения: {user_data['token_promo']}\n"
    else:
        str = f"Токен Ozon seller: {user_data['ozon_seller_token']}\nOzon ID: {user_data['ozon_id']}\n"
    await message.bot.send_message(chat_id=env('MANAGER_CHAT_ID'),
                                   text=f"Новый пользователь!\n"
                                        f"ID Телеграм: {message.from_user.id}\n"
                                        f"Имя: {message.from_user.first_name}\n"
                                        f"Username Телеграм: @{message.from_user.username}\n"
                                        f"Телефон: {user_data['phone_number']}\n"
                                        f"Почта: {user_data['gmail']}\n"
                                        f"Маркетплейс: {user_data['mp']}\n"
                                        f"Кабинет: {user_data['cabinet_name']}\n" + str +
                                        f"Дата регистрации: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
    await write_to_db(user_data=user_data,
                      tg_id=message.from_user.id,
                      name=message.from_user.first_name,
                      username=message.from_user.username,
                      phone=user_data["phone_number"],
                      mp=user_data["mp"],
                      cabinet_name=user_data["cabinet_name"],
                      gmail=user_data["gmail"],
                      date=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    await state.clear()
