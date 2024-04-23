from aiogram import Router, F, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    FSInputFile, ContentType, InputFile, InputMediaPhoto
from Bot.keyboards.main_keyboards import *
from Bot.states.user_info_states import *
from Bot.functions.main_functions import *
from environs import Env

env = Env()
env.read_env()
manager_list = env.list("MANAGER_TG_ID_LIST")
manager_list = [int(i) for i in manager_list]

router = Router()


def has_cyrillic(text):
    return any('\u0400' <= char <= '\u04FF' for char in text)


############################ Основное меню ############################
async def main_menu(message: Message, state: FSMContext):
    user_data = await state.get_data()
    refresh_username(user_data["client_id"], message.from_user.username)
    client_id = user_data["client_id"]
    phone = user_data["phone_number"]
    await state.clear()
    await state.set_state(Cabinet.startCreateCabinet)
    await state.update_data(client_id=client_id, phone_number=phone)
    await message.answer(
        text="Это главное меню, здесь вы можете добавить ежедневный отчет к свому кабинету, или добавить новый кабинет",
        reply_markup=main_keyboard())


@router.message(Cabinet.startCreateCabinet, F.text == "Изменить токены")
async def change_tokens(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="change_tokens",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    await state.set_state(MainMenu.selectCabinetForChangeToken)
    cabinets = await find_cabinets(user_data['client_id'], only_wb=False)
    await message.answer(text="Выберите кабинет:",
                         reply_markup=all_cabinets(cabinets))


@router.message(MainMenu.selectCabinetForChangeToken)
async def select_cabinet_for_change_token(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="select_cabinet_for_change_token",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if message.text == "Назад в меню":
        await main_menu(message, state)
        return
    cabinets = await find_cabinets(user_data['client_id'], only_wb=False)

    chosen_cabinet = message.text
    try:
        if message.text[len(message.text) - 5:] == " (WB)":
            chosen_cabinet = message.text[:len(message.text) - 5]
        else:
            chosen_cabinet = message.text[:len(message.text) - 7]
    except IndexError:
        pass

    if chosen_cabinet in cabinets['cabinet_name'].to_list():
        await state.set_state(Cabinet.chooseToken)
        if message.text[len(message.text) - 5:] == " (WB)":
            await state.update_data(mp="Wildberries")
            await state.update_data(
                cabinet_id=get_cabinet_id(message.text[:len(message.text) - 5], "Wildberries", user_data["client_id"]))
            await state.set_state(Cabinet.inputNewToken)
            await message.answer(text="Выберите токен для изменения:", reply_markup=wb_token_select_keyboard())
        else:
            await state.update_data(mp="Ozon")
            await state.update_data(
                cabinet_id=get_cabinet_id(message.text[:len(message.text) - 7], "Ozon", user_data["client_id"]))
            await state.set_state(Cabinet.inputNewToken)
            await message.answer(text="Выберите токен для изменения:", reply_markup=ozon_token_select_keyboard())
    else:
        await message.answer(text="Такого кабинета нет, выберите кабинет из предложенных ниже")
        return


@router.message(Cabinet.inputNewToken)
async def input_new_token(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="input_new_token",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if message.text == "Назад в меню":
        await main_menu(message, state)
        return
    if message.text == "Статистика":
        await state.update_data(token_type="stat")
        await state.set_state(Cabinet.inputNewWBToken)
        await message.answer(text="Введите токен статистики (WB):", reply_markup=ReplyKeyboardRemove())
    elif message.text == "Продвижение":
        await state.update_data(token_type="adv")
        await state.set_state(Cabinet.inputNewWBToken)
        await message.answer(text="Введите токен продвижения (WB):", reply_markup=ReplyKeyboardRemove())
    elif message.text == "Seller API":
        await state.update_data(token_type="seller")
        await state.set_state(Cabinet.inputNewOzonSellerToken)
        await message.answer(text="Введите токен seller API (Ozon):", reply_markup=ReplyKeyboardRemove())
    elif message.text == "Performance API":
        await state.update_data(token_type="performance")
        await state.set_state(Cabinet.inputNewOzonPerformanceToken)
        await message.answer(text="Введите токен performance API secret (Ozon):", reply_markup=ReplyKeyboardRemove())
    elif message.text == "Promo API":
        await state.update_data(token_type="promo")
    else:
        await message.answer(text="Такого токена нет, выберите токен из предложенных ниже")
        return


@router.message(Cabinet.inputNewOzonSellerToken)
async def input_new_ozon_seller_token(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="input_new_ozon_seller_token",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if not has_cyrillic(message.text):
        await state.update_data(new_token=message.text)
    else:
        await message.answer(text="Введите корректный токен")
        return
    await message.answer(text="Введите Client ID (Ozon)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Cabinet.inputNewOzonTokenId)


@router.message(Cabinet.inputNewOzonPerformanceToken)
async def input_new_ozon_performance_token(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="input_new_ozon_performance_token",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    if not has_cyrillic(message.text):
        await state.update_data(new_token=message.text)
    else:
        await message.answer(text="Введите корректный токен")
        return
    await message.answer(text="Введите Performance Client ID (Ozon)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Cabinet.inputNewOzonTokenId)


@router.message(Cabinet.inputNewOzonTokenId)
async def input_new_ozon_token_id(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="input_new_ozon_token_id",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    await state.update_data(new_token_id=message.text)
    await check_token(message, state)


@router.message(Cabinet.inputNewWBToken)
async def input_new_wb_token(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="input_new_wb_token",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if not has_cyrillic(message.text):
        await state.update_data(new_token=message.text)
    else:
        await message.answer(text="Введите корректный токен")
        return
    await check_token(message, state)


async def check_token(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="check_token",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    if user_data["token_type"] == "stat":
        if check_token_stat(user_data["new_token"]):
            await message.answer(text="Токен успешно прошел проверку")
            if refresh_wb_token(user_data["new_token"], "stat", user_data['cabinet_id']):
                await message.answer(text="Ваши токены обновлены")
            else:
                await message.answer(text="При обновлении токена произошла ошибка")
        else:
            await message.answer(text="Токен недействителен")
    elif user_data["token_type"] == "adv":
        if check_token_promo(user_data["new_token"]):
            await message.answer(text="Токен успешно прошел проверку")
            if refresh_wb_token(user_data["new_token"], "adv", user_data['cabinet_id']):
                await message.answer(text="Ваши токены обновлены")
            else:
                await message.answer(text="При обновлении токена произошла ошибка")
        else:
            await message.answer(text="Токен недействителен")
    elif user_data["token_type"] == "seller":
        if check_token_seller(user_data["new_token"], user_data['new_token_id']):
            await message.answer(text="Токен успешно прошел проверку")
            if refresh_ozon_token(user_data["new_token"], user_data['new_token_id'], "seller", user_data['cabinet_id']):
                await message.answer(text="Ваши токены обновлены")
            else:
                await message.answer(text="При обновлении токена произошла ошибка")
        else:
            await message.answer(text="Токен недействителен")
    elif user_data["token_type"] == "performance":
        if check_token_performance(user_data["new_token"], user_data['new_token_id']):
            await message.answer(text="Токен успешно прошел проверку")
            if refresh_ozon_token(user_data["new_token"], user_data['new_token_id'], "performance",
                                  user_data['cabinet_id']):
                await message.answer(text="Ваши токены обновлены")
            else:
                await message.answer(text="При обновлении токена произошла ошибка")
        else:
            await message.answer(text="Токен недействителен")
    await main_menu(message, state)


@router.message(Cabinet.startCreateCabinet, F.text == "Добавить еженедельный отчет")
async def every_day_report(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="every_day_report",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    user_data = await state.get_data()
    cabinets = await find_cabinets(user_data['client_id'])
    await state.set_state(MainMenu.selectCabinet)
    await message.answer(text="Выберите кабинет:", reply_markup=all_cabinets(cabinets))


@router.message(F.text == "Написать в тех. поддержку")
async def write_to_support(message: Message, state: FSMContext):
    await message.answer(
        text=f"Вы можете связаться с техническим специалистом по вот этой ссылке: @{env('SUPPORT_CHAT_NAME')}")


@router.message(F.text == "Назад в меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if "client_id" in user_data:
        phone = user_data["phone_number"]
        client_id = user_data["client_id"]
        await state.clear()
        await state.set_state(MainMenu.mainMenu)
        await state.update_data(phone_number=phone, client_id=client_id)
        await main_menu(message, state)
    else:
        await cmd_start(message, state)


@router.message(MainMenu.selectCabinet)
async def select_cabinet(message: Message, state: FSMContext):
    user_data = await state.get_data()
    mp = 'unknown'
    if len(message.text) > 5:
        if message.text[len(message.text) - 5:len(message.text)] == " (WB)":
            mp = 'WB'
            await state.update_data(mp_for_excel=mp)
        else:
            mp = 'OZON'
            await state.update_data(mp_for_excel=mp)
    if not await have_cabinet(message.text.replace(' (WB)', '').replace(' (OZON)', ''),
                              user_data["client_id"],
                              mp):
        await message.answer(text="Такого кабинета не существует, пожалуйста введите название кабинета полностью, "
                                  "либо воспользуйтесь клавиатурой ниже", reply_markup=ReplyKeyboardRemove())
        await every_day_report(message, state)
    else:
        user_data = await state.get_data()
        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone=str(user_data["phone_number"]),
                 is_client=True if "client_id" in user_data else False,
                 tg_command="select_cabinet",
                 input_data=message.text,
                 client_id=user_data["client_id"] if "client_id" in user_data else None)
        await state.update_data(cabinet_name=message.text.replace(' (WB)', '').replace(' (OZON)', ''))
        await state.set_state(MainMenu.selectDateExcel)
        cabinet_name = message.text.replace(' (WB)', '').replace(' (OZON)', '')
        await message.answer(text="Смотрим возможные даты для загрузки отчета...")
        cabinet_for_keyboard = gen_date_excel(cabinet_name, mp, user_data["client_id"])
        if not cabinet_for_keyboard:
            await message.answer(text="По данному кабинету вы уже отправили все отчеты")
            user_data = await state.get_data()
            client_id = user_data["client_id"]
            phone = user_data["phone_number"]
            await state.clear()
            await state.set_state(MainMenu.mainMenu)
            await state.update_data(phone_number=phone)
            await state.update_data(client_id=client_id)
            await main_menu(message, state)
            return
        await message.answer(text="Выберите дату отчета из предложенных ниже",
                             reply_markup=select_date(cabinet_for_keyboard))
        await state.set_state(MainMenu.selectedDateExcel)


@router.message(MainMenu.selectedDateExcel)
async def selected_date_excel(message: Message, state: FSMContext):
    user_data = await state.get_data()
    all_dates_invalid = gen_date_excel(user_data["cabinet_name"], user_data["mp_for_excel"], user_data["client_id"])
    all_dates = [i[16:] for i in all_dates_invalid]
    if len(message.text) == 26:
        if message.text[16:] not in all_dates:
            await message.answer(
                text="Такая дата отчета не существует, пожалуйста введите дату отчета из приведенных ниже")
            return
    else:
        await message.answer(text="Такая дата отчета не существует, пожалуйста введите дату отчета из приведенных ниже")
        return
    await state.update_data(dateExcel=message.text)

    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="select_data_excel",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    await message.answer(text=f"Выбранная дата - {message.text}", reply_markup=back_to_main_keyboard())
    await state.set_state(MainMenu.waitExcel)
    await message.answer(text="Отправьте отчет в виде архива с одним Excel файлом\n По одному архиву за раз",
                         reply_markup=help_exel_keyboard())


@router.message(MainMenu.waitExcel, F.content_type == ContentType.DOCUMENT)
async def wait_excel(message: Message, state: FSMContext):
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
                file_path="reports/" + str(user_data["client_id"]) + "/" + str(user_data["client_id"]) + ".zip",
                client_id=user_data["client_id"],
                file_name=file_name,
                cabinet_name=user_data['cabinet_name'],
                date_to=user_data['dateExcel'],
                mp=user_data['mp_for_excel']):
            await message.answer(text="Отчет успешно добавлен")

            send_log(tg_id=message.from_user.id,
                     tg_username=message.from_user.username,
                     phone=str(user_data["phone_number"]),
                     is_client=True if "client_id" in user_data else False,
                     tg_command="wait_excel",
                     input_data=file_name,
                     client_id=user_data["client_id"] if "client_id" in user_data else None)

            user_data = await state.get_data()
            client_id = user_data["client_id"]
            phone = user_data["phone_number"]
            await state.clear()
            await state.set_state(MainMenu.mainMenu)
            await state.update_data(client_id=client_id, phone_number=phone)
            await main_menu(message, state)
        else:
            await message.answer(text=f"Произошла ошибка, убедитесь, что вы выбрали верный файл, возможно вы уже "
                                      f"загружали этот отчет.\n"
                                      f"В случае, если вы уверены, что все делаете верно, свяжитесь с поддержкой "
                                      f"@{env('SUPPORT_CHAT_NAME')}")
    else:
        await message.answer(text="Данный файл не поддерживается, попробуйте снова, но с другим файлом, "
                                  f"в случае, если вы уверены, что все делаете верно, свяжитесь с поддержкой "
                                  f"@{env('SUPPORT_CHAT_NAME')}")


############################### Авторизация и начало создания кабинета ################################
@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id in manager_list:
        await message.answer(text="Добро пожаловать в админ панель, доступные команды:\n"
                                  "/create_client - перенос клиента из базы leads\n"
                                  "/subscription - продление подписки для действующих клиентов\n"
                                  "/upload_reports - загрузка отчетов\n"
                                  "/add_client_gs - Добавление (изменение) ссылок на таблицы Google Sheets\n"
                                  "/upload_archive_reports - загрузка архивных отчетов\n"
                                  "/update_cabinet_token - обновление токена кабинета\n"
                                  "/add_new_client - добавление нового клиента\n"
                                  "/add_client_phone - обновление телефона клиента\n"
                                  "/add_client_cabinet - добавление нового кабинета клиента\n",
                             reply_markup=ReplyKeyboardRemove())
        await state.update_data(client_id=0, phone_number="")

    if await check_repeat_registration(message.from_user.id):
        await message.answer(text="Вы уже зарегистрировались, ожидайте ответа от менеджера",
                             reply_markup=ReplyKeyboardRemove())
        return

    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=user_data["phone_number"] if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="start",
             input_data="/start",
             client_id=user_data["client_id"] if "client_id" in user_data else 0)

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
        phone_check, client_id = await check_client_id(message.from_user.id)
        if client_id != "":
            await state.update_data(client_id=client_id)
            await state.update_data(phone_number=phone_check)
            await main_menu(message, state)
        else:
            await state.clear()
            await cmd_start(message, state)


@router.message(F.contact)
async def get_phone(message: Message, state: FSMContext):
    await message.answer(text=f'Спасибо, {message.contact.first_name}! Ваш номер - {message.contact.phone_number}',
                         reply_markup=ReplyKeyboardRemove())
    await state.update_data(phone_number=message.contact.phone_number.replace("+", ""))

    client_id_check, client_tg_id = await check_client_number(message.contact.phone_number.replace("+", ""))
    if client_id_check == "":
        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone=message.contact.phone_number,
                 is_client=False,
                 tg_command="get_phone",
                 input_data=str(message.contact.phone_number),
                 client_id=None)
        if not check_confirmed(message.from_user.id):
            await state.set_state(Cabinet.turnoverQuestion)
            await message.answer(text="Выберите ваш текущий оборот в месяц", reply_markup=turnover_keyboard())
        else:
            await state.set_state(Cabinet.startCreateCabinet)
            await message.answer(text=f'Для начала нужно добавить кабинет', reply_markup=add_cabinet_keyboard())
    else:
        if int(client_tg_id) != message.from_user.id:
            await refresh_tg_id(client_id_check, message.from_user.id)
        await state.update_data(client_id=client_id_check)
        await main_menu(message, state)


@router.message(Cabinet.turnoverQuestion)
async def turnover_question(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="turnover_question",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    flag_turnover = False
    if message.text == "Менее 300 тыс. руб.":
        await state.update_data(turnover="Менее 300 тыс. руб.")
    elif message.text == "300 - 500 тыс. руб.":
        flag_turnover = True
        await state.update_data(turnover="300 - 500 тыс. руб.")
    elif message.text == "500 - 1 000 тыс. руб.":
        flag_turnover = True
        await state.update_data(turnover="500 - 1 000 тыс. руб.")
    elif message.text == "1 000 - 2 000 тыс. руб.":
        flag_turnover = True
        await state.update_data(turnover="1 000 - 2 000 тыс. руб.")
    elif message.text == "Свыше 2 000 тыс. руб.":
        flag_turnover = True
        await state.update_data(turnover="Свыше 2 000 тыс. руб.")
    else:
        await message.answer(text=f'Пожалуйста, введите оборот из приведенных ниже', reply_markup=turnover_keyboard())

    if flag_turnover:
        await state.set_state(Cabinet.startCreateCabinet)
        await message.answer(text=f'Для начала нужно добавить кабинет', reply_markup=add_cabinet_keyboard())

        add_new_potential_client(tg_id=message.from_user.id,
                                 name=message.from_user.first_name,
                                 phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
                                 turnover=message.text,
                                 tg_username=message.from_user.username,
                                 date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 is_finish_reg=False)
    else:
        user_data = await state.get_data()
        print(user_data["turnover"])
        print(user_data["phone_number"])
        write_new_lead(tg_id=message.from_user.id,
                       tg_username=message.from_user.username,
                       phone_number=user_data["phone_number"],
                       name=message.from_user.first_name,
                       turnover=message.text)
        await message.answer(text=f'Ожидайте ответа менеджера', reply_markup=ReplyKeyboardRemove())
        message_for_manager = "Получен новый лид: \n"
        message_for_manager += f'TG ID: {message.from_user.id}\n'
        message_for_manager += f'Имя: {message.from_user.first_name}\n' if message.from_user.first_name is not None else ''
        message_for_manager += f'Телефон: {user_data["phone_number"]}\n' if user_data[
                                                                                "phone_number"] is not None else ''
        message_for_manager += f'@{message.from_user.username}\n' if message.from_user.username is not None else ''
        message_for_manager += f'Дата добавления: {datetime.datetime.now().strftime("%d-%m-%Y %H:%M")}\n'
        message_for_manager += f'Оборот: {user_data["turnover"]}\n'
        message_for_manager += f'Токены не указаны\n'
        message_for_manager += f'#Лид'
        await message.bot.send_message(env('MANAGER_CHAT_ID'), text=message_for_manager)
        await state.clear()


@router.message(Cabinet.startCreateCabinet, F.text == "Добавить кабинет")
async def selectMP(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]),
             is_client=True if "client_id" in user_data else False,
             tg_command="selectMP",
             input_data="Добавить кабинет",
             client_id=user_data["client_id"] if "client_id" in user_data else None)

    await state.set_state(Cabinet.selectMP)
    await message.answer(text="Кабинет какого маркетплейса вы хотите добавить?", reply_markup=select_MP())


@router.message(Cabinet.selectMP)
async def enter_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="enter_name",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
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
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="check_cabinet_name",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    client_id = ""
    if "client_id" in user_data:
        client_id = user_data["client_id"]
    if client_id != "":
        if await check_unic_cabinet(message.text, client_id, user_data["mp"]):
            await state.update_data(cabinet_name=message.text)
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
        if user_data["mp"] == "Wildberries":
            await state.set_state(Cabinet.wbTokenStat)
            await wb_tokens_stat(message, state)
        elif user_data["mp"] == "Ozon":
            await state.set_state(Cabinet.ozonTokens)
            await ozon_tokens(message, state)


############################ Ввод токенов и их проверка ################################
@router.message(Cabinet.wbTokenStat)
async def wb_token_stat_check(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="wb_token_stat_check",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    await message.answer(text="Проверяем...")
    if not has_cyrillic(message.text):
        if await check_token_request(message.text, "Wildberries"):
            await state.update_data(token_stat=message.text)
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
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="wb_token_promo_check",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    await message.answer(text="Проверяем...")
    if not has_cyrillic(message.text):
        if await check_token_request(message.text, "Wildberries", promotion=True):
            await state.update_data(token_promo=message.text)
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
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="ozon_tokens_input",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if not has_cyrillic(message.text):
        await state.set_state(Cabinet.ozonId)
        await state.update_data(ozon_seller_token=message.text)
        await message.answer(text="Введите ID клиента Ozon seller API", reply_markup=help_ozon_id_keyboard())
    else:
        await message.answer(text="Некорректный токен, попробуйте снова\nВведите токен Ozon seller API",
                             reply_markup=help_ozon_token_keyboard())
        await ozon_tokens(message, state, repeating=True)


@router.message(Cabinet.ozonId)
async def ozon_id_check(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="ozon_id_check",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if not has_cyrillic(message.text):
        user_data = await state.get_data()
        if await check_token_request(user_data["ozon_seller_token"], "Ozon", ozon_id_seller=message.text):
            await state.update_data(ozon_id_seller=message.text)
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
        await message.answer(text="Введите токен Ozon seller API", reply_markup=help_ozon_token_keyboard())
    await state.set_state(Cabinet.ozonTokens)


############################ Коллбеки для помощи ################################

@router.callback_query(F.data == "help_wb_report")
async def help_wb_report(callback: CallbackQuery):
    photo = FSInputFile('media/wb_report1.jpg')
    await callback.message.answer_photo(photo,
                                        caption="1. На главной странице WB Seller нажмите на кнопку \"Финансовые "
                                                "отчеты\"")
    photo = FSInputFile('media/wb_report2.jpg')
    await callback.message.answer_photo(photo,
                                        caption="2. Выберите необходимый отчет, и нажмите на 3 точки, возле его номера\n"
                                                "3. Далее нажмите появившуюся кнопку \"Детализация\"")
    photo = FSInputFile('media/wb_report3.jpg')
    await callback.message.answer_photo(photo,
                                        caption="4. В открывшемся окне нажмите кнопку \"скачать\", и выберите \"Детализация\"\n"
                                                "5. Далее скачанный .zip файл отправьте боту")
    await callback.answer()


@router.callback_query(F.data == "help_ozon_id")
async def help_ozon_id(callback: CallbackQuery):
    photo = FSInputFile('media/ozon_seller_id.jpg')
    await callback.message.answer_photo(photo,
                                        caption="Зайдите в личный кабинет Seller Ozon\n" +
                                                "1. Перейдите в раздел \"Настройки\"\n" +
                                                "2. Справа в меню выберите пункт \"API ключи\"\n" +
                                                "Вы увидите ваш \"Client ID\"")
    await callback.answer()


@router.callback_query(F.data == "help_wb_promo_token")
async def help_wb_promo_token(callback: CallbackQuery):
    photo = FSInputFile('media/wb_token1.jpg')
    await callback.message.answer_photo(photo,
                                        caption="1. В личном кабинете WB Seller в правом верхнем углу нажмите на свой "
                                                "профиль, и нажмите кнопку \"Настройки\"")
    photo = FSInputFile('media/wb_token2.jpg')
    await callback.message.answer_photo(photo,
                                        caption="2. Далее в открывшемся окне перейдите во вкладку \"Доступ к API\"\n" +
                                                "3. И нажмите кнопку \"Создать новый токен\"")
    photo = FSInputFile('media/wb_token_adv.jpg')
    await callback.message.answer_photo(photo,
                                        caption="4. Введите любое понятное вам название для токена\n" +
                                                "5. Выберите методы \"Продвижение\"\n" +
                                                "6. Нажмите кнопку \"Создать токен\"\n" +
                                                "7. Полученный токен отправьте боту")
    await callback.answer()


@router.callback_query(F.data == "help_wb_statistic_token")
async def help_wb_statistic_token(callback: CallbackQuery):
    photo = FSInputFile('media/wb_token1.jpg')
    await callback.message.answer_photo(photo,
                                        caption="1. В личном кабинете WB Seller в правом верхнем углу нажмите на свой "
                                                "профиль, и нажмите кнопку \"Настройки\"")
    photo = FSInputFile('media/wb_token2.jpg')
    await callback.message.answer_photo(photo,
                                        caption="2. Далее в открывшемся окне перейдите во вкладку \"Доступ к API\"\n" +
                                                "3. И нажмите кнопку \"Создать новый токен\"")
    photo = FSInputFile('media/wb_token_stat.jpg')
    await callback.message.answer_photo(photo,
                                        caption="4. Введите любое понятное вам название для токена\n" +
                                                "5. Выберите методы \"Статистика\"\n" +
                                                "6. Нажмите кнопку \"Создать токен\"\n" +
                                                "7. Полученный токен отправьте боту")
    await callback.answer()


@router.callback_query(F.data == "help_ozon_token")
async def help_ozon_token(callback: CallbackQuery):
    photo = FSInputFile('media/ozon_seller_token1.jpg')
    await callback.message.answer_photo(photo,
                                        caption="Зайдите в личный кабинет Seller Ozon\n" +
                                                "1. Перейдите в раздел \"Настройки\"\n" +
                                                "2. Справа в меню выберите пункт \"API ключи\"\n" +
                                                "3. Нажмите кнопку \"Сгенерировать ключи\"")
    photo = FSInputFile('media/ozon_seller_token2.jpg')
    await callback.message.answer_photo(photo,
                                        caption="В появившемся окне введите любое понятное вам название для ключа.\n" +
                                                "В \"Типах токена\" выберите \"Admin read only\"")
    await callback.answer()


@router.callback_query(F.data == "help_wb_report")
async def help_exel(callback: CallbackQuery):
    photo = FSInputFile('media/help_excel1.jpg')
    await callback.message.answer_photo(photo,
                                        caption="1. На главной странице WB Seller нажмите на кнопку \"Финансовые отчеты\"")
    photo = FSInputFile('media/help_excel2.jpg')
    await callback.message.answer_photo(photo,
                                        caption="2. Выберите необходимый отчет, и нажмите на 3 точки, возле его номера\n" +
                                                "3. Далее нажмите появившуюся кнопку \"Детализация\"")
    photo = FSInputFile('media/help_excel3.jpg')
    await callback.message.answer_photo(photo,
                                        caption="4. В открывшемся окне нажмите кнопку \"скачать\", и выберите \"Детализация\"\n" +
                                                "5. Далее скачанный .zip файл отправьте боту")
    await callback.answer()


############################ Последняя часть регистрации ################################
async def success_tokens(message: Message, state: FSMContext, mail: bool = False):
    is_client = False
    if not mail:
        await message.answer(text="Все токены прошли проверку", reply_markup=ReplyKeyboardRemove())
    phone, client_id = await check_client_id(message.from_user.id)
    if client_id != "":
        await state.update_data(client_id=client_id)
        is_client = True

    user_data = await state.get_data()
    gmail = await check_gmail(str(message.from_user.id), is_client=is_client)
    if gmail == "":
        if not mail:
            await message.answer(text="Введите свою почту mail", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Cabinet.inputGmail)
            return
        else:
            gmail = user_data["gmail"]
            await message.answer(text=f"Ваш почтовый ящик - {gmail}", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(text=f"Ваш почтовый ящик - {gmail}", reply_markup=ReplyKeyboardRemove())

    if not mail:
        await state.update_data(gmail=gmail)

    user_data = await state.get_data()
    try:
        ozon_id_seller = user_data["ozon_id_seller"]
    except KeyError:
        ozon_id_seller = None
    try:
        ozon_seller_token = user_data["ozon_seller_token"]
    except KeyError:
        ozon_seller_token = None
    try:
        wb_stat_token = user_data["token_stat"]
    except KeyError:
        wb_stat_token = None
    try:
        wb_promo_token = user_data["token_promo"]
    except KeyError:
        wb_promo_token = None

    if "client_id" in user_data:
        if await create_cabinet_client(name=message.from_user.first_name, tg_id=message.from_user.id,
                                       tg_username=message.from_user.username, phone=user_data['phone_number'],
                                       gmail=user_data["gmail"], cabinet_name=user_data["cabinet_name"],
                                       mp=user_data["mp"], ozon_seller_token=ozon_seller_token,
                                       ozon_id_seller=ozon_id_seller, ozon_id_performance=None,
                                       wb_stat_token=wb_stat_token, ozon_performance_token=None,
                                       wb_promo_token=wb_promo_token, client_id=user_data["client_id"]):
            await message.answer(text="Успешно! Новый кабинет создан", reply_markup=ReplyKeyboardRemove())
            cabinet_id = get_cabinet_id(user_data["cabinet_name"], user_data["mp"], user_data['client_id'])

            await message.bot.send_message(env('MANAGER_CHAT_ID'), text=f"Новый кабинет создан!\n"
                                                                        f"ID клиента: {user_data['client_id']}\n"
                                                                        f"ID кабинета: {cabinet_id}\n"
                                                                        f"USERNAME TG: @{message.from_user.username}\n"
                                                                        f"Название кабинета: {user_data['cabinet_name']}\n"
                                                                        f"Номер телефона клиента: {user_data['phone_number']}\n"
                                                                        f"Маркетплейс: {user_data['mp']}\n"
                                                                        f"Почта: {user_data['gmail']}\n"
                                                                        f"#Кабинет")
            phone = user_data["phone_number"]
            client_id = user_data["client_id"]
        else:
            await message.answer(text="Произошла ошибка при создании кабинета, попробуйте снова через некоторое время",
                                 reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await state.set_state(MainMenu.mainMenu)
        await state.update_data(phone_number=phone, client_id=client_id)
        await main_menu(message, state)
    else:
        if await create_cabinet_client(name=message.from_user.first_name, tg_id=message.from_user.id,
                                       tg_username=message.from_user.username, phone=user_data['phone_number'],
                                       gmail=user_data["gmail"], cabinet_name=user_data["cabinet_name"],
                                       mp=user_data["mp"], ozon_seller_token=ozon_seller_token,
                                       ozon_id_seller=ozon_id_seller, ozon_id_performance=None,
                                       wb_stat_token=wb_stat_token, ozon_performance_token=None,
                                       wb_promo_token=wb_promo_token):
            await message.answer(text="Успешно! Ваш аккаунт и кабинет созданы", reply_markup=ReplyKeyboardRemove())

            update_potential_clients(message.from_user.id)

            phone, client_id = await check_client_id(message.from_user.id)
            cabinet_id = get_cabinet_id(user_data["cabinet_name"], user_data["mp"], client_id)
            await message.bot.send_message(env('MANAGER_CHAT_ID'), text=f"Новый клиент!\n"
                                                                        f"ID клиента: {client_id}\n"
                                                                        f"ID кабинета: {cabinet_id}\n"
                                                                        f"USERNAME TG: @{message.from_user.username}\n"
                                                                        f"Название кабинета: {user_data['cabinet_name']}\n"
                                                                        f"Номер телефона клиента: {user_data['phone_number']}\n"
                                                                        f"Маркетплейс: {user_data['mp']}\n"
                                                                        f"Почта: {user_data['gmail']}\n"
                                                                        f"#Клиент\n"
                                                                        f"#Кабинет")
            await state.clear()
            await state.set_state(MainMenu.mainMenu)
            await state.update_data(phone_number=phone, client_id=client_id)
            await main_menu(message, state)
        else:
            await message.answer(text="Произошла ошибка при создании аккаунта, попробуйте снова через некоторое время",
                                 reply_markup=ReplyKeyboardRemove())
            await state.clear()
            await cmd_start(message, state)


@router.message(Cabinet.inputGmail)
async def input_gmail(message: Message, state: FSMContext):
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone=str(user_data["phone_number"]) if "phone_number" in user_data else "",
             is_client=True if "client_id" in user_data else False,
             tg_command="input_gmail",
             input_data=message.text,
             client_id=user_data["client_id"] if "client_id" in user_data else None)
    if test_email(message.text):
        await state.update_data(gmail=message.text)
        if "client_id" in user_data:
            update_client_gmail(user_data["client_id"], message.text)
        await success_tokens(message, state, mail=True)
    else:
        await message.answer(text="Некорректная почта,\nПример: xxxxxx@gmail.com",
                             reply_markup=ReplyKeyboardRemove())
