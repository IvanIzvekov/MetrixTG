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
    final = State()


class Authorize(StatesGroup):
    startAuthorize = State()


class MainMenu(StatesGroup):
    mainMenu = State()
    selectCabinet = State()
    selectDateExcel = State()
    selectedDateExcel = State()
    waitExcel = State()
