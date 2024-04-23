import io
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    FSInputFile, ContentType, InputFile, InputMediaPhoto
from Bot.keyboards.main_keyboards import *
from Bot.states.user_info_states import *
from Bot.functions.main_functions import *
from Bot.functions.admin_functions import *
from Bot.handlers.main_handlers import cmd_start, has_cyrillic
from environs import Env

env = Env()
env.read_env()
manager_list = env.list("MANAGER_TG_ID_LIST")
manager_list = [int(i) for i in manager_list]
router = Router()


@router.message(F.text == "/add_client_cabinet")
@router.message(F.text == "/add_client_phone")
@router.message(F.text == "/add_new_client")
@router.message(F.text == "/update_cabinet_token")
@router.message(F.text == "/upload_reports")
@router.message(F.text == "/subscription")
@router.message(F.text == "/create_client")
@router.message(F.text == "/add_client_gs")
@router.message(F.text == "/upload_archive_reports")
async def input_tg_id_by_admin(message: Message, state: FSMContext):
    if message.from_user.id in manager_list:

        send_log(tg_id=message.from_user.id,
                 tg_username=message.from_user.username,
                 phone="admin",
                 is_client=True,
                 tg_command="input_tg_id_by_admin",
                 input_data=message.text,
                 client_id=0)

        if message.text == "/create_client":
            await message.answer(text=f"Введите TG ID клиента")
            await state.set_state(Admin.input_id_for_create_client)
        elif message.text == "/subscription":
            await message.answer(text=f"Введите ID клиента", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_id_for_subscription)
        elif message.text == "/upload_reports":
            await message.answer(text=f"Введите ID кабинета", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_cabinet_for_upload_reports)
        elif message.text == "/add_client_gs":
            await message.answer(text=f"Введите ID клиента", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_client_id_for_add_gs_url)
        elif message.text == "/upload_archive_reports":
            await message.answer(text=f"Введите ID кабинета", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_cabinet_for_upload_archive_reports)
        elif message.text == "/update_cabinet_token":
            await message.answer(text=f"Введите ID кабинета", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_cabinet_for_update_token)
        elif message.text == "/add_new_client":
            await message.answer(
                text=f"Введите номер телефона клиента в формате 7ХХХХХХХХХХ", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_phone_for_add_new_client)
        elif message.text == "/add_client_phone":
            await message.answer(text=f"Введите ID клиента", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_client_id_for_add_phone)
        elif message.text == "/add_client_cabinet":
            await message.answer(text=f"Введите ID клиента", reply_markup=ReplyKeyboardRemove())
            await state.set_state(Admin.input_client_id_for_add_cabinet)
    else:
        return


################ /add_client_cabinet ################
@router.message(Admin.input_client_id_for_add_cabinet)
async def input_id_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_id_for_create_client",
             input_data=message.text,
             client_id=0)
    if check_correct_client_id(message.text):
        await state.update_data(client_id_user=message.text)
        await state.set_state(Admin.select_mp_for_create_cabinet)
        await message.answer(text="Выберите МП", reply_markup=select_MP())
    else:
        await message.answer(text="Клиента с таким ID не существует, введите другое")


@router.message(Admin.select_mp_for_create_cabinet)
async def select_mp_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="select_mp_for_create_cabinet",
             input_data=message.text,
             client_id=0)

    if message.text == "Ozon":
        await state.update_data(mp_user=message.text)
        await state.set_state(Admin.input_name_for_create_cabinet)
        await message.answer(text="Введите название кабинета", reply_markup=ReplyKeyboardRemove())
    elif message.text == "Wildberries":
        await state.update_data(mp_user=message.text)
        await state.set_state(Admin.input_name_for_create_cabinet)
        await message.answer(text="Введите название кабинета", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(text="Такого МП нет, выберите другой из списка ниже")


@router.message(Admin.input_name_for_create_cabinet)
async def input_name_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_name_for_create_cabinet",
             input_data=message.text,
             client_id=0)

    user_data = await state.get_data()
    if await check_unic_cabinet(message.text, user_data['client_id_user'], user_data['mp_user']):
        await state.update_data(name_cabinet_user=message.text)
        await input_tokens_add_cabinet_by_admin(message, state)
    else:
        await message.answer(text="Кабинет с таким названием уже существует у выбранного клиента, введите другое")
        return


async def input_tokens_add_cabinet_by_admin(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if user_data['mp_user'] == "Wildberries":
        await message.answer(text="Введите токен статистики WB", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Admin.input_token_wb_stat_for_create_cabinet)
    elif user_data['mp_user'] == "Ozon":
        await message.answer(text="Введите токен seller API Ozon", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Admin.input_token_ozon_seller_for_create_cabinet)


@router.message(Admin.input_token_ozon_seller_for_create_cabinet)
async def input_token_ozon_seller_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_token_ozon_seller_for_create_cabinet",
             input_data=message.text,
             client_id=0)
    if not has_cyrillic(message.text):
        await state.update_data(token_seller_user=message.text)
        await state.set_state(Admin.input_token_ozon_seller_id_for_create_cabinet)
        await message.answer(text="Введите Client ID seller API Ozon", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(text="Токен не прошел проверку, введите другой")


@router.message(Admin.input_token_ozon_seller_id_for_create_cabinet)
async def input_token_ozon_seller_id_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_token_ozon_seller_id_for_create_cabinet",
             input_data=message.text,
             client_id=0)

    user_data = await state.get_data()
    if check_token_seller(user_data['token_seller_user'], message.text):
        await message.answer(text="Токен прошел проверку", reply_markup=ReplyKeyboardRemove())
        await message.answer(text="Создаю новый кабинет", reply_markup=ReplyKeyboardRemove())

        try:
            await create_cabinet_client(name=None, tg_id=None, tg_username=None, phone=None, gmail=None,
                                        cabinet_name=user_data['name_cabinet_user'], mp=user_data['mp_user'],
                                        ozon_seller_token=user_data['token_seller_user'], ozon_id_seller=message.text,
                                        ozon_id_performance=None, wb_stat_token=None, ozon_performance_token=None,
                                        wb_promo_token=None, client_id=user_data['client_id_user'])

            await message.answer(text="Новый кабинет создан")
        except Exception as e:
            print(e)
            await message.answer(text="Произошла ошибка при создании кабинета")
        await cmd_start(message, state)
        # TODO Тут добавить подключение performance token вместо создания кабинета
    else:
        await message.answer(text="Токен не прошел проверку")
        await input_tokens_add_cabinet_by_admin(message, state)


@router.message(Admin.input_token_wb_stat_for_create_cabinet)
async def input_token_wb_stat_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_token_wb_stat_for_create_cabinet",
             input_data=message.text,
             client_id=0)
    if check_token_stat(message.text):
        await state.update_data(token_stat_user=message.text)
        await message.answer(text="Токен прошел проверку", reply_markup=ReplyKeyboardRemove())
        await message.answer(text="Введите токен продвижения WB", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Admin.input_token_wb_promo_for_create_cabinet)
    else:
        await message.answer(text="Токен не прошел проверку, введите другой")


@router.message(Admin.input_token_wb_promo_for_create_cabinet)
async def input_token_wb_promo_for_create_cabinet(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_token_wb_promo_for_create_cabinet",
             input_data=message.text,
             client_id=0)
    if check_token_promo(message.text):
        await state.update_data(token_promo_user=message.text)
        await message.answer(text="Токен прошел проверку", reply_markup=ReplyKeyboardRemove())
        await message.answer(text="Создаю новый кабинет", reply_markup=ReplyKeyboardRemove())

        user_data = await state.get_data()
        try:
            await create_cabinet_client(name=None, tg_id=None, tg_username=None, phone=None, gmail=None,
                                        cabinet_name=user_data['name_cabinet_user'], mp=user_data['mp_user'],
                                        ozon_seller_token=None, ozon_id_seller=None, ozon_id_performance=None,
                                        wb_stat_token=user_data['token_stat_user'], wb_promo_token=message.text,
                                        ozon_performance_token=None, client_id=user_data['client_id_user'])

            await message.answer(text="Новый кабинет создан")
        except Exception as e:
            print(e)
            await message.answer(text="Произошла ошибка при создании кабинета")
        await cmd_start(message, state)
    # TODO: добавить создание кабинета
    else:
        await message.answer(text="Токен не прошел проверку, введите другой")


################## /add_client_phone ##################
@router.message(Admin.input_client_id_for_add_phone)
async def input_id_for_add_phone(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_id_for_create_client",
             input_data=message.text,
             client_id=0)
    await state.update_data(client_id_user=message.text)
    await message.answer(text=f"Введите номер телефона клиента в формате 7ХХХХХХХХХХ", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Admin.input_phone_for_add_phone)


@router.message(Admin.input_phone_for_add_phone)
async def input_phone_for_add_phone(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_phone_for_add_new_client",
             input_data=message.text,
             client_id=0)
    phone = message.text
    phone = phone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "").replace("+", "")
    for i in phone:
        if not i.isdigit():
            await message.answer(text="Номер телефона должен состоять только из цифр")
            return
    if phone[0] == "8":
        phone = "7" + phone[1:]
    elif phone[0] == "9":
        phone = "7" + phone
    elif phone[0] == "7":
        phone = phone
    else:
        await message.answer(text="Номер телефона должен начинаться с 7, 8 или 9")
        return

    client_id, tg_id = await check_client_number(phone)
    if client_id != "":
        await message.answer(text="Клиент с таким номером телефона уже существует в базе")
        await cmd_start(message, state)
        return
    client_id, tg_id = await check_client_number("8" + phone[1:])
    if client_id != "":
        await message.answer(text="Клиент с таким номером телефона уже существует в базе")
        await cmd_start(message, state)
        return

    try:
        user_data = await state.get_data()
        refresh_phone(phone, user_data['client_id_user'])
        await message.answer(text=f"Телефон клиента - {user_data['client_id_user']} успешно обновлен в базе")
        await cmd_start(message, state)
    except Exception as e:
        print(e)
        await message.answer(text="Произошла ошибка при обновлении телефона в базе")
        await cmd_start(message, state)


################## /add_new_client #######################
@router.message(Admin.input_phone_for_add_new_client)
async def input_phone_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_phone_for_add_new_client",
             input_data=message.text,
             client_id=0)
    phone = message.text
    phone = phone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "").replace("+", "")
    for i in phone:
        if not i.isdigit():
            await message.answer(text="Номер телефона должен состоять только из цифр")
            return
    if phone[0] == "8":
        phone = "7" + phone[1:]
    elif phone[0] == "9":
        phone = "7" + phone
    elif phone[0] == "7":
        phone = phone
    else:
        await message.answer(text="Номер телефона должен начинаться с 7, 8 или 9")
        return
    client_id, tg_id = await check_client_number(phone)
    if client_id != "":
        await message.answer(text="Такой клиент уже существует")
        await cmd_start(message, state)
        return
    await state.update_data(phone_number_user=phone)
    await message.answer(text="Введите Имя клиента")
    await state.set_state(Admin.input_name_for_add_new_client)


@router.message(Admin.input_name_for_add_new_client)
async def input_name_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_name_for_add_new_client",
             input_data=message.text,
             client_id=0)
    await state.update_data(name_user=message.text.title())
    await message.answer(text="Введите почту клиента, в случае если она отсутствует, введите `-`")
    await state.set_state(Admin.input_mail_for_add_new_client)


@router.message(Admin.input_mail_for_add_new_client)
async def input_mail_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_mail_for_add_new_client",
             input_data=message.text,
             client_id=0)
    if message.text == "-":
        await state.update_data(mail_user="None")
    else:
        if test_email(message.text):
            await state.update_data(mail_user=message.text)
        else:
            await message.answer(text="Некорректная почта")
            return
    await message.answer(text="Введите дату окончания подписки в формате гггг-мм-дд")
    await state.set_state(Admin.input_end_sub_for_add_new_client)


@router.message(Admin.input_end_sub_for_add_new_client)
async def input_end_sub_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_end_sub_for_add_new_client",
             input_data=message.text,
             client_id=0)
    try:
        datetime.datetime.strptime(message.text, '%Y-%m-%d')
    except ValueError:
        await message.answer(text="Некорректный формат даты")
        return
    await state.update_data(end_sub_user=message.text)
    await message.answer(text="Введите название кабинета")
    await state.set_state(Admin.input_cabinet_name_for_add_new_client)


@router.message(Admin.input_cabinet_name_for_add_new_client)
async def input_cabinet_name_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_cabinet_name_for_add_new_client",
             input_data=message.text,
             client_id=0)
    await state.update_data(cabinet_name_user=message.text)
    await message.answer(text="Введите Маркетплейс кабинета (формат WB/OZON)")
    await state.set_state(Admin.input_mp_for_add_new_client)


@router.message(Admin.input_mp_for_add_new_client)
async def input_mp_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_mp_for_add_new_client",
             input_data=message.text,
             client_id=0)
    mp = message.text
    wb_var = ["Wb", "Wildberries", "Вб"]
    ozon_var = ["Ozon", "Озон"]
    if mp.title() not in wb_var and mp.title() not in ozon_var:
        await message.answer(text="Некорректное название Маркетплейса")
        return
    if mp.title() in wb_var:
        mp = "Wildberries"
    if mp.title() in ozon_var:
        mp = "Ozon"
    await state.update_data(mp_user=mp)

    await input_tokens_by_admin(message, state)


async def input_tokens_by_admin(message, state):
    user_data = await state.get_data()
    mp = user_data['mp_user']
    if mp == "Wildberries":
        await message.answer(text="Введите токен статистики Wildberries")
        await state.set_state(Admin.input_tokens_wb_for_add_new_client)
    else:
        await message.answer(text="Введите токен seller API Ozon")
        await state.set_state(Admin.input_tokens_ozon_for_add_new_client)


@router.message(Admin.input_tokens_ozon_for_add_new_client)
async def input_tokens_ozon_seller_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_tokens_ozon_seller_for_add_new_client",
             input_data=message.text,
             client_id=0)
    if not has_cyrillic(message.text):
        await state.update_data(token_ozon_seller_user=message.text)
        await state.set_state(Admin.input_tokens_ozon_seller_id_for_add_new_client)
        await message.answer(text="Введите Client ID seller API Ozon")
    else:
        await message.answer(text="Токен содержит кириллицу, введите другой")


@router.message(Admin.input_tokens_ozon_seller_id_for_add_new_client)
async def input_tokens_ozon_seller_id_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_tokens_ozon_seller_id_for_add_new_client",
             input_data=message.text,
             client_id=0)

    user_data = await state.get_data()
    if check_token_seller(user_data['token_ozon_seller_user'], message.text):
        await message.answer(text="Токен прошел проверку, создаю клиента")
        # TODO Тут добавить уход на спрос performance api ozon вместо добавления клиента в базу
        try:
            user_data = await state.get_data()
            await create_cabinet_client(user_data['name_user'], 1, "None", user_data['phone_number_user'],
                                        user_data['mail_user'], user_data['cabinet_name_user'], user_data['mp_user'],
                                        ozon_seller_token=user_data['token_ozon_seller_user'],
                                        ozon_id_seller=message.text, ozon_id_performance=None, wb_stat_token=None,
                                        wb_promo_token=None, ozon_performance_token=None, client_id=None)

            client_id, tg_id = await check_client_number(user_data['phone_number_user'])
            await renew_subscription(client_id, user_data['end_sub_user'])
            await message.answer(text=f"Новый клиент создан, его ID = {client_id}")
        except Exception as e:
            print(e)
            await message.answer(text="Произошла ошибка")
            await cmd_start(message, state)
    else:
        await message.answer(text="Недействительный токен, введите другой")
        await input_tokens_by_admin(message, state)
    await cmd_start(message, state)


@router.message(Admin.input_tokens_wb_for_add_new_client)
async def input_tokens_wb_stat_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_tokens_wb_stat_for_add_new_client",
             input_data=message.text,
             client_id=0)
    if not has_cyrillic(message.text):
        if check_token_stat(message.text):
            await state.update_data(token_stat_user=message.text)
            await state.set_state(Admin.input_tokens_wb_promo_for_add_new_client)
            await message.answer(text="Токен прошел проверку, введите токен продвижения Wildberries")
        else:
            await message.answer(text="Недействительный токен, введите другой")
    else:
        await message.answer(text="Токен содержит кириллицу, введите другой")


@router.message(Admin.input_tokens_wb_promo_for_add_new_client)
async def input_tokens_wb_promo_for_add_new_client(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_tokens_wb_promo_for_add_new_client",
             input_data=message.text,
             client_id=0)
    if not has_cyrillic(message.text):
        if check_token_promo(message.text):
            await state.update_data(token_promo_user=message.text)
            await message.answer(text="Токены прошли проверку, создаю нового клиента")
            try:
                user_data = await state.get_data()
                await create_cabinet_client(user_data['name_user'], 1, "None", user_data['phone_number_user'],
                                            user_data['mail_user'], user_data['cabinet_name_user'],
                                            user_data['mp_user'],
                                            ozon_seller_token=None, ozon_id_seller=None, ozon_id_performance=None,
                                            wb_stat_token=user_data['token_stat_user'],
                                            wb_promo_token=user_data['token_promo_user'], ozon_performance_token=None,
                                            client_id=None)

                client_id, tg_id = await check_client_number(user_data['phone_number_user'])
                await renew_subscription(client_id, user_data['end_sub_user'])
                await message.answer(text=f"Новый клиент создан, его ID = {client_id}")
            except Exception as e:
                print(e)
                await message.answer(text="Произошла ошибка")
            await cmd_start(message, state)
        else:
            await message.answer(text="Недействительный токен, введите другой")
    else:
        await message.answer(text="Токен содержит кириллицу, введите другой")


################### /update_cabinet_token ###################
@router.message(Admin.input_cabinet_for_update_token)
async def input_cabinet_for_update_token(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_cabinet_for_update_token",
             input_data=message.text,
             client_id=0)
    try:
        cabinet_name, client_id = get_cabinet_name(message.text)
    except Exception as e:
        await message.answer(text="Кабинет не найден, введите корректное ID кабинета")
        return
    await state.update_data(cabinet_id_user=message.text)
    mp = check_mp(message.text)
    if mp == "WB":
        await message.answer(text="Выберите токен для обновления", reply_markup=wb_token_select_keyboard())
        await state.set_state(Admin.waitWbTokenSelect)
    elif mp == "Ozon":
        await message.answer(text="Выберите токен для обновления", reply_markup=ozon_token_select_keyboard())
        await state.set_state(Admin.waitOzonTokenSelect)
    else:
        await message.answer(text="Кабинет найден, но в базе отсутствует запись о маркетплейсе")
        await cmd_start(message)
        return


@router.message(Admin.waitWbTokenSelect)
@router.message(Admin.waitOzonTokenSelect)
async def wait_token_select(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="wait_token_select",
             input_data=message.text,
             client_id=0)
    if message.text == "Статистика":
        await message.answer(text="Введите токен для статистики WB", reply_markup=ReplyKeyboardRemove())
        await state.update_data(token_user_api=message.text)
        await state.set_state(Admin.inputToken)
    elif message.text == "Продвижение":
        await message.answer(text="Введите токен для продвижения WB", reply_markup=ReplyKeyboardRemove())
        await state.update_data(token_user_api=message.text)
        await state.set_state(Admin.inputToken)
    elif message.text == "Seller API":
        await message.answer(text="Введите токен для Seller API Ozon", reply_markup=ReplyKeyboardRemove())
        await state.update_data(token_user_api=message.text)
        await state.set_state(Admin.inputToken)
    elif message.text == "Performance API":
        await message.answer(text="Введите Performance API secret", reply_markup=ReplyKeyboardRemove())
        await state.update_data(token_user_api=message.text)
        await state.set_state(Admin.inputToken)
    elif message.text == "Назад в меню":
        await state.set_state(Admin.input_cabinet_for_update_token)
    else:
        await message.answer(text="Такого варианта нет, введие корректное значение")


@router.message(Admin.inputToken)
async def input_token_by_admin(message: Message, state: FSMContext, ozon_id_have=False):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_token_by_admin",
             input_data=message.text,
             client_id=0)
    wb_stat = False
    wb_promo = False
    ozon_seller = False
    ozon_performance = False
    user_data = await state.get_data()
    if user_data['token_user_api'] == "Статистика":
        if not has_cyrillic(message.text):
            check = check_token_stat(message.text)
            wb_stat = True
            await state.update_data(token_user=message.text)
    elif user_data['token_user_api'] == "Продвижение":
        if not has_cyrillic(message.text):
            check = check_token_promo(message.text)
            wb_promo = True
            await state.update_data(token_user=message.text)
    elif user_data['token_user_api'] == "Seller API":
        if ozon_id_have:
            user_data = await state.get_data()
            ozon_seller = True
            if not has_cyrillic(user_data['token_user']):
                check = check_token_seller(user_data['token_user'], message.text)
        else:
            await state.update_data(token_user=message.text)
            await message.answer(text="Введите Client ID Ozon")
            await state.set_state(Admin.inputOzonId)
            return
    elif user_data['token_user_api'] == "Performance API":
        if ozon_id_have:
            user_data = await state.get_data()
            ozon_performance = True
            if not has_cyrillic(user_data['token_user']):
                check = check_token_performance(user_data['token_user'], message.text)
        else:
            await state.update_data(token_user=message.text)
            await message.answer(text="Введите Client ID Ozon")
            await state.set_state(Admin.inputOzonId)
            return

    if not check:
        await message.answer(text="Токен недействителен, введие корректное значение")
        return
    else:
        await message.answer(text="Токен успешно прошел проверку")
        try:
            user_data = await state.get_data()
            if wb_stat:
                refresh_wb_token(user_data['token_user'], type="stat", cabinet_id=user_data["cabinet_id_user"])
            if wb_promo:
                refresh_wb_token(user_data['token_user'], type="adv", cabinet_id=user_data["cabinet_id_user"])
            if ozon_seller:
                refresh_ozon_token(user_data['token_user'], user_data['ozon_id_user'], type="seller",
                                   cabinet_id=user_data["cabinet_id_user"])
            if ozon_performance:
                refresh_ozon_token(user_data['token_user'], user_data['ozon_id_user'], type="performance",
                                   cabinet_id=user_data["cabinet_id_user"])
            await message.answer(text="Токен успешно обновлен в базе данных")
            await cmd_start(message, state)
        except Exception as e:
            print(e)
            await message.answer(text="Произошла ошибка при обновлении токена в базе данных")
            await cmd_start(message, state)


@router.message(Admin.inputOzonId)
async def input_client_id_ozon_by_admin(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_client_id_ozon_by_admin",
             input_data=message.text,
             client_id=0)
    await state.update_data(ozon_id_user=message.text)
    await input_token_by_admin(message, state, ozon_id_have=True)


################# /upload_archive_reports #################
@router.message(Admin.input_cabinet_for_upload_archive_reports)
async def input_cabinet_for_upload_archive_reports(message: Message, state: FSMContext):
    try:
        cabinet_name, client_id = get_cabinet_name(message.text)
    except Exception as e:
        await message.answer(text="Кабинет не найден, введие кабинет корректно")
        return
    await state.update_data(cabinet_name_user=cabinet_name, client_id_user=client_id)
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_cabinet_for_upload_archive_reports",
             input_data=message.text,
             client_id=0)
    await message.answer(text="Выберите квартал даты отчета", reply_markup=quarter_keyboard())
    await state.set_state(Admin.waitQuarter)


@router.message(Admin.waitQuarter)
async def wait_quarter(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="wait_quarter",
             input_data=message.text,
             client_id=0)
    if message.text in ["(2022-12-26 - 2023-04-02)", "(2023-04-03 - 2023-07-02)", "(2023-07-03 - 2023-10-01)",
                        "(2023-10-02 - 2023-12-31)", "(2024-01-01 - 2024-01-28)"]:
        await state.update_data(quarter_report=message.text)
        user_data = await state.get_data()
        date_for_keyboard = gen_date_excel(user_data['cabinet_name_user'], "WB", user_data['client_id_user'],
                                           is_archive=True, quarter=user_data['quarter_report'])
        if date_for_keyboard:
            await message.answer(text="Выберите дату отчета из предложенных ниже",
                                 reply_markup=select_date(date_for_keyboard, is_admin=True))
            await state.set_state(Admin.waitDateArchiveExcel)
        else:
            await message.answer(text="Для этого квартала уже загружены все отчеты", reply_markup=quarter_keyboard())
            return
    else:
        await message.answer(text="Некорректный квартал, выберите из предложенных ниже",
                             reply_markup=quarter_keyboard())
        return


@router.message(Admin.waitDateArchiveExcel)
async def wait_date_archive_excel(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="wait_date_archive_excel",
             input_data=message.text,
             client_id=0)
    user_data = await state.get_data()
    check_date = gen_date_excel(user_data['cabinet_name_user'], "WB", user_data['client_id_user'], is_archive=True,
                                quarter=user_data['quarter_report'])
    if message.text not in check_date:
        await message.answer(text="Некорректная дата, выберите из предложенных ниже",
                             reply_markup=select_date(check_date, is_admin=True))
        return
    await state.update_data(selected_date_excel=message.text)
    await message.answer(
        text="Отправьте .zip архив, который вы скачали с личного кабинета, не изменяя названия содержимого")
    await state.set_state(Admin.waitArchiveExcel)


@router.message(Admin.waitArchiveExcel, F.content_type == ContentType.DOCUMENT)
async def wait_archive_excel(message: Message, state: FSMContext):
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="wait_archive_excel",
             input_data=message.text,
             client_id=0)
    user_data = await state.get_data()
    client_id = user_data['client_id_user']
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
            os.mkdir(f'reports/{client_id}')
        except FileExistsError:
            await message.answer(text="Пожалуйста, отправьте только один архив с отчетом")
            return
        await message.bot.download(file_id, f'reports/{client_id}/{client_id}.zip')
        if await read_excel_wb_zip(
                file_path="reports/" + str(client_id) + "/" + str(client_id) + ".zip",
                client_id=client_id,
                file_name=file_name,
                cabinet_name=user_data['cabinet_name_user'],
                date_to=user_data['selected_date_excel'],
                mp="WB"):
            await message.answer(text="Отчет успешно добавлен")
            await state.clear()
            await cmd_start(message, state)
        else:
            await message.answer(text=f"Произошла ошибка, убедитесь, что вы выбрали верный файл, возможно вы уже "
                                      f"загружали этот отчет")
    else:
        await message.answer(text="Данный файл не поддерживается, попробуйте снова, но с другим файлом")


################## /add_client_gs ##################
@router.message(Admin.input_client_id_for_add_gs_url)
async def input_client_id_for_add_gs_url(message: Message, state: FSMContext):
    await state.update_data(client_id_for_add_gs_url=message.text)
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_client_id_for_add_gs_url",
             input_data=message.text,
             client_id=0)
    await message.answer(text="Введите ссылку на таблицу учета")
    await state.set_state(Admin.input_uchet_url)


@router.message(Admin.input_uchet_url)
async def input_uchet_url(message: Message, state: FSMContext):
    await state.update_data(uchet_url=message.text)
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_uchet_url",
             input_data=message.text,
             client_id=0)
    await message.answer(text="Введите ссылку на таблицу финансов")
    await state.set_state(Admin.input_finance_url)


@router.message(Admin.input_finance_url)
async def input_finance_url(message: Message, state: FSMContext):
    await state.update_data(finance_url=message.text)
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_finance_url",
             input_data=message.text,
             client_id=0)
    user_data = await state.get_data()
    check = refresh_url(client_id=user_data["client_id_for_add_gs_url"],
                        uchet_url=user_data["uchet_url"],
                        finance_url=user_data["finance_url"])
    if check:
        await message.answer(text="Успешно!")
        try:
            tg_id_client = get_tg_id_from_client_id(user_data["client_id_for_add_gs_url"])
            if tg_id_client != 1:
                message_for_client = (f"Ваши таблицы обновлены!\n\n"
                                      f"Финансы:\n"
                                      f"{user_data['finance_url']}\n\n"
                                      f"Учет:\n"
                                      f"{user_data['uchet_url']}\n\n"
                                      f"Инструкция по финансовой таблице: https://youtu.be/pRQkrbIy0fc\n\n"
                                      f'▶️ Настройки\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=0s\n'
                                      f'▶️ Дашборд\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=213s\n'
                                      f'▶️ ОПУ\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=368s\n'
                                      f'▶️ Выгрузка фин. отчета (WB)\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=769s\n'
                                      f'▶️ ДДС\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=1179s\n'
                                      f'▶️ Баланс\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=1387s\n'
                                      f'▶️ АВС - анализ\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=1555s\n'
                                      f'▶️ Выгрузка (реклама)\nhttps://www.youtube.com/watch?v=pRQkrbIy0fc&t=1926s\n\n'
                                      f'▶️ Инструкция по учетной таблице:\nhttps://youtu.be/W_dBhEHeD5I\n\n'
                                      f'▶️ Авторизация пользователя\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=0s\n'
                                      f'▶️ Товары и себестоимость\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=98s\n'
                                      f'▶️ Дашборд\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=243s\n'
                                      f'▶️ Мои счета\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=362s\n'
                                      f'▶️ Мои склады\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=420s\n'
                                      f'▶️ Контрагенты\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=503s\n'
                                      f'▶️ Создание операций\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=540s\n'
                                      f'▶️ Учетные статьи\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=680s\n'
                                      f'▶️ Складской учет\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=982s\n'
                                      f'▶️ Складской учет (массовая загрузка)\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=1410s\n'
                                      f'▶️ Сводная по остаткам\nhttps://www.youtube.com/watch?v=W_dBhEHeD5I&t=1490s')

                await message.bot.send_message(tg_id_client, text=message_for_client, disable_web_page_preview=True)
            else:
                await message.answer(text=f"Пользователь {user_data['client_id_for_add_gs_url']} не заходил в бота, "
                                          f"сообщение о новых ссылках не доставлено.")
        except Exception as e:
            print(e)
    else:
        await message.answer(text="Произошла ошибка")
    await state.clear()
    await cmd_start(message, state)


############### /upload_reports ################
@router.message(Admin.input_cabinet_for_upload_reports)
async def upload_reports_by_admin(message: Message, state: FSMContext):
    await state.update_data(cabinet_id_user=message.text.replace(' ', ''))
    user_data = await state.get_data()
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="upload_reports_by_admin",
             input_data=message.text,
             client_id=0)
    cabinet_name, client_id = get_cabinet_name(user_data["cabinet_id_user"])
    await state.update_data(cabinet_name_user=cabinet_name, client_id_user=client_id)
    date_for_keyboard = gen_date_excel(cabinet_name, "WB", client_id)
    if date_for_keyboard:
        await message.answer(text="Выберите дату отчета из предложенных ниже",
                             reply_markup=select_date(date_for_keyboard))
        await state.set_state(Admin.selected_date_excel)


@router.message(Admin.selected_date_excel)
async def selected_date_excel_by_admin(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await state.update_data(selected_date_excel=message.text)
    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="selected_date_excel_by_admin",
             input_data=message.text,
             client_id=0)
    await message.answer(text="Отправьте .zip архив, который вы скачали с личного кабинета")
    await state.set_state(Admin.waitExcel)


@router.message(Admin.waitExcel, F.content_type == ContentType.DOCUMENT)
async def wait_excel_by_admin(message: Message, state: FSMContext):
    user_data = await state.get_data()

    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="wait_excel_by_admin",
             input_data=message.text,
             client_id=0)
    client_id = get_client_id_from_cabinet_id(user_data["cabinet_id_user"])
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
            os.mkdir(f'reports/{client_id}')
        except FileExistsError:
            await message.answer(text="Пожалуйста, отправьте только один архив с отчетом")
            return
        await message.bot.download(file_id, f'reports/{client_id}/{client_id}.zip')
        if await read_excel_wb_zip(
                file_path="reports/" + str(client_id) + "/" + str(client_id) + ".zip",
                client_id=client_id,
                file_name=file_name,
                cabinet_name=user_data['cabinet_name_user'],
                date_to=user_data['selected_date_excel'],
                mp="WB"):
            await message.answer(text="Отчет успешно добавлен")
            await state.clear()
            await cmd_start(message, state)
        else:
            await message.answer(text=f"Произошла ошибка, убедитесь, что вы выбрали верный файл, возможно вы уже "
                                      f"загружали этот отчет")
    else:
        await message.answer(text="Данный файл не поддерживается, попробуйте снова, но с другим файлом")


############### /subscription ################
@router.message(Admin.input_id_for_subscription)
async def input_id_for_subscription_by_admin(message: Message, state: FSMContext):
    client_id = message.text.replace(' ', '')
    await state.update_data(client_id_user=client_id)

    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_tg_id_for_renew_subscription",
             input_data=message.text,
             client_id=0)

    await message.answer(text=f"ВАЖНО! Введите дату в формате ГГГГ-ММ-ДД\nНапример: 2022-01-01")
    await state.set_state(Admin.input_date_subscription)


@router.message(Admin.input_date_subscription)
async def renew_subscription_by_admin(message: Message, state: FSMContext):
    user_data = await state.get_data()

    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_date_for_renew_subscription",
             input_data=message.text,
             client_id=0)

    if await renew_subscription(user_data['client_id_user'], message.text.replace(' ', '')):
        await message.answer(
            text=f"Подписка пользователя {user_data['client_id_user']} продлена до {message.text.replace(' ', '')}")
    else:
        await message.answer(text=f"Произошла ошибка, проверьте корректность ввода ID клиента или даты\n"
                                  f"/subscription для повторной попытки")
    await cmd_start(message, state)


################## /create_client ################
@router.message(Admin.input_id_for_create_client)
async def refresh_lead_status_by_admin(message: Message, state: FSMContext):
    tg_id = message.text.replace(' ', '')

    send_log(tg_id=message.from_user.id,
             tg_username=message.from_user.username,
             phone="admin",
             is_client=True,
             tg_command="input_tg_id_for_refresh_lead_status",
             input_data=message.text,
             client_id=0)

    if await create_potential_client_from_lead(tg_id):
        await message.answer(text=f"Пользователь {tg_id} разблокирован, и может пройти регистрацию")
        await message.bot.send_message(tg_id,
                                       "Менеджер подтвердил ваш запрос на регистрацию.\nВведите /start, чтобы продолжить")
    else:
        await message.answer(text=f"Произошла ошибка, проверьте корректность ввода TG ID\n"
                                  f"/create_client для повторной попытки")
    await cmd_start(message, state)
