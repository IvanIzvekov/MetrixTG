from aiogram.fsm.state import State, StatesGroup


class Cabinet(StatesGroup):
    startCreateCabinet = State()
    selectMP = State()
    inputName = State()
    wbTokenStat = State()
    wbTokenPromo = State()
    ozonTokens = State()
    ozonId = State()
    gmail = State()
    inputGmail = State()
    turnoverQuestion = State()
    chooseToken = State()
    inputNewToken = State()
    inputNewWBToken = State()
    inputNewOzonSellerToken = State()
    inputNewOzonPerformanceToken = State()
    inputNewOzonTokenId = State()


class Authorize(StatesGroup):
    startAuthorize = State()


class MainMenu(StatesGroup):
    mainMenu = State()
    selectCabinet = State()
    selectDateExcel = State()
    selectedDateExcel = State()
    waitExcel = State()
    selectCabinetForChangeToken = State()


class Admin(StatesGroup):
    input_client_id_for_add_gs_url = State()
    input_id_for_create_client = State()
    input_id_for_subscription = State()
    input_date_subscription = State()
    input_id_for_upload_reports = State()
    input_cabinet_for_upload_reports = State()
    selected_date_excel = State()
    waitExcel = State()
    input_uchet_url = State()
    input_finance_url = State()
    input_cabinet_for_upload_archive_reports = State()
    waitArchiveExcel = State()
    waitQuarter = State()
    waitDateArchiveExcel = State()
    input_cabinet_for_update_token = State()
    waitWbTokenSelect = State()
    waitOzonTokenSelect = State()
    inputToken = State()
    inputOzonId = State()

    input_phone_for_add_new_client = State()
    input_name_for_add_new_client = State()
    input_mail_for_add_new_client = State()
    input_end_sub_for_add_new_client = State()
    input_cabinet_name_for_add_new_client = State()
    input_mp_for_add_new_client = State()
    input_tokens_wb_for_add_new_client = State()
    input_tokens_wb_promo_for_add_new_client = State()
    input_tokens_ozon_for_add_new_client = State()
    input_tokens_ozon_seller_id_for_add_new_client = State()

    input_client_id_for_add_phone = State()
    input_phone_for_add_phone = State()

    input_client_id_for_add_cabinet = State()
    select_mp_for_create_cabinet = State()
    input_name_for_create_cabinet = State()
    input_token_wb_stat_for_create_cabinet = State()
    input_token_ozon_seller_for_create_cabinet = State()
    input_token_wb_promo_for_create_cabinet = State()
    input_token_ozon_seller_id_for_create_cabinet = State()