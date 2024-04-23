import subprocess
import numpy as np
import pandas as pd
from DB.connector import project_id, credentials, client, database, connector
import pandas_gbq
import requests
import datetime
import os
import zipfile
import hashlib
import re
import environs

env = environs.Env()
env.read_env()


def check_correct_client_id(client_id):
    query = f"""
        SELECT client_id FROM `{project_id}.{database}.clients` WHERE client_id = {client_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if df.empty:
        return False
    else:
        return True


def refresh_username(client_id, username):
    try:
        query = f"""
                    SELECT tg_username FROM `{project_id}.{database}.clients` WHERE client_id = {client_id}
                """
        df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
        if df['tg_username'][0] == username:
            return
        query = f"""
            UPDATE `{project_id}.{database}.clients` SET tg_username = '{username}' WHERE client_id = {client_id}
        """
        query_job = client.query(query)
        results = query_job.result()
    except Exception as e:
        print("Error in refresh_username function")
        print(e)


def test_email(email):
    regx = r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?"
    pattern = re.compile(regx)
    if not re.match(pattern, email):
        return False
    return True


def create_schema(df):
    table_schema = []
    for col in df.columns:
        if 'object' in str(df[col].dtype):
            table_schema.append({'name': col, 'type': 'STRING'})
        elif 'int64' in str(df[col].dtype):
            table_schema.append({'name': col, 'type': 'INTEGER'})
        elif 'float64' in str(df[col].dtype):
            table_schema.append({'name': col, 'type': 'FLOAT'})
        elif 'datetime64[ns]' in str(df[col].dtype):
            table_schema.append({'name': col, 'type': 'DATE'})
        elif 'bool' in str(df[col].dtype):
            table_schema.append({'name': col, 'type': 'BOOLEAN'})

    return table_schema


def create_client(name, tg_id, tg_username, phone, gmail):
    try:
        client_id = find_max_id(f"""SELECT MAX(client_id) FROM `{project_id}.{database}.clients`""")
        query = pd.DataFrame(data={
            'client_id': [int(client_id)],
            'created_at': [datetime.datetime.today()],
            'tg_id': [int(tg_id)],
            'tg_username': [str(tg_username)],
            'name': [str(name)],
            'phone': [str(phone)],
            'gmail': [str(gmail)],
            'end_sub': [None],
            'is_deleted': [False],
            'deleted_at': [None],
        })
        schema = create_schema(query)
        schema[1]['type'] = 'DATE'
        schema[7]['type'] = 'DATE'
        pandas_gbq.to_gbq(query, f'{project_id}.{database}.clients', project_id=project_id,
                          if_exists='append',
                          credentials=credentials,
                          table_schema=schema)
        return client_id
    except Exception as e:
        print(e)
        return False


def create_cabinet(client_id, cabinet_name, mp):
    try:
        cabinet_id = find_max_id(f"""SELECT MAX(cabinet_id) FROM `{project_id}.{database}.cabinets`""")
        query = pd.DataFrame(data={
            'cabinet_id': [int(cabinet_id)],
            'client_id': [int(client_id)],
            'cabinet_name': [str(cabinet_name)],
            'mp': ["WB" if mp == "Wildberries" else "Ozon"],
        })
        schema = create_schema(query)
        pandas_gbq.to_gbq(query, f'{project_id}.{database}.cabinets', project_id=project_id,
                          if_exists='append',
                          credentials=credentials,
                          table_schema=schema)
        return cabinet_id
    except Exception as e:
        print(e)
        return False


def create_token(cabinet_id, wb_stat_token=None, wb_promo_token=None,
                 ozon_seller_token=None,
                 ozon_id_seller=None,
                 ozon_performance_token=None,
                 ozon_id_performance=None):
    if wb_stat_token is not None:
        token_id = find_max_id(f"""SELECT MAX(id) FROM `{project_id}.{database}.wb_token`""")
        query = pd.DataFrame(data={
            'id': [int(token_id)],
            'cabinet_id': [int(cabinet_id)],
            'key': [str(wb_stat_token)],
            'type': ['stat'],
        })
        schema = create_schema(query)
        pandas_gbq.to_gbq(query, f'{project_id}.{database}.wb_token', project_id=project_id,
                          if_exists='append',
                          credentials=credentials,
                          table_schema=schema)
        token_id += 1
        query = pd.DataFrame(data={
            'id': [int(token_id)],
            'cabinet_id': [int(cabinet_id)],
            'key': [str(wb_promo_token)],
            'type': ['adv'],
        })
        schema = create_schema(query)
        pandas_gbq.to_gbq(query, f'{project_id}.{database}.wb_token', project_id=project_id,
                          if_exists='append',
                          credentials=credentials,
                          table_schema=schema)
    else:
        token_id = find_max_id(f"""SELECT MAX(id) FROM `{project_id}.{database}.ozon_token`""")
        query = pd.DataFrame(data={
            'id': [int(token_id)],
            'cabinet_id': [int(cabinet_id)],
            'key': [str(ozon_seller_token)],
            'ozon_client_id': [int(ozon_id_seller)],
            'type': ['seller'],
            'performance_client_secret': [None],
            'performance_client_id': [None]
        })

        schema = create_schema(query)
        schema[5]['type'] = "STRING"
        schema[6]['type'] = "STRING"
        pandas_gbq.to_gbq(query, f'{project_id}.{database}.ozon_token', project_id=project_id,
                          if_exists='append',
                          credentials=credentials,
                          table_schema=schema)
        token_id += 1
        # TODO вот тут добавить добавление токена performance


def find_max_id(query):
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    df = df.replace(pd.NA, 0)
    if df['f0_'][0] == 0:
        id = 1
    else:
        id = df['f0_'][0] + 1
    return id


async def check_repeat_registration(tg_id):
    try:
        query = f"""
            SELECT tg_id FROM `{project_id}.{database}.leads` WHERE tg_id = {tg_id} and is_confirmed = FALSE
        """
        df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    except Exception as e:
        return False
    if len(df) == 0:
        return False
    else:
        return True


async def refresh_tg_id(client_id, tg_id):
    query = f"""
                UPDATE `{project_id}.{database}.clients`
                SET tg_id = {tg_id}
                WHERE client_id = {client_id}
            """
    query_job = client.query(query)
    results = query_job.result()


async def check_unic_cabinet(name, client_id, mp):
    if mp == "Wildberries":
        mp = "WB"
    query = f"""SELECT cabinet_name FROM `{project_id}.{database}.cabinets` WHERE client_id = {client_id} 
    AND cabinet_name = '{name}' AND mp = '{mp}'"""
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return True
    else:
        return False


async def check_client_id(tg_id):
    query = f"""
        SELECT phone, client_id FROM `{project_id}.{database}.clients` WHERE tg_id = {tg_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return "", ""
    else:
        return df.phone[0], df.client_id[0]


async def check_client_number(phone):
    phone = str(phone)[len(phone) - 10:]
    query = f"""
        SELECT client_id, tg_id FROM `{project_id}.{database}.clients` WHERE RIGHT(phone, 10) = '{phone}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return "", ""
    else:
        return df.client_id[0], df.tg_id[0]


async def check_token_request(token: str, mp: str, promotion=False, ozon_id_seller=""):
    try:
        if mp == "Wildberries" and promotion:
            response = requests.get(
                "https://advert-api.wb.ru/adv/v1/promotion/count",
                headers={
                    "Authorization": f"{token}"
                }
            )
            if response.status_code == 200:
                return True
            else:
                return False
        elif mp == "Wildberries" and not promotion:
            response = requests.get(
                "https://statistics-api.wildberries.ru/api/v1/supplier/incomes",
                headers={
                    "Authorization": f"{token}"
                },
                params={
                    "dateFrom": (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            )
            if response.status_code == 200:
                return True
            else:
                return False
        elif mp == "Ozon":
            response = requests.post(
                "https://api-seller.ozon.ru/v1/description-category/tree",
                headers={
                    "Client-Id": f"{ozon_id_seller}",
                    "Api-Key": f"{token}"
                }
            )
            if response.status_code == 200:
                return True
            else:
                return False
        return False
    except Exception as e:
        print(e)
        return False


async def check_gmail(tg_id: str, is_client: bool):
    query = f"""
        SELECT gmail FROM `{project_id}.{database}.clients` WHERE tg_id = {tg_id}"""
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if is_client:
        if df['gmail'][0] is None:
            return ""
        else:
            return df.gmail[0]
    else:
        return ""


async def find_cabinets(client_id, only_wb=True):
    if only_wb:
        query = f"""SELECT cabinet_name, mp FROM `{project_id}.{database}.cabinets` 
        WHERE client_id = {client_id} AND mp = 'WB'"""
    else:
        query = f"""SELECT cabinet_name, mp FROM `{project_id}.{database}.cabinets` WHERE client_id = {client_id}"""

    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    return df


async def have_cabinet(cabinet, client_id, mp):
    query = f"""
        SELECT cabinet_name FROM `{project_id}.{database}.cabinets` 
        WHERE cabinet_name = '{cabinet}' AND client_id = {client_id} AND mp = '{mp}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return False
    else:
        return True


async def create_cabinet_client(name, tg_id, tg_username, phone, gmail, cabinet_name, mp, ozon_seller_token=None,
                                ozon_id_seller=None, ozon_id_performance=None, wb_stat_token=None,
                                ozon_performance_token=None, wb_promo_token=None, client_id=None):
    try:
        if client_id is None:
            client_id = create_client(name, tg_id, tg_username, phone, gmail)

        cabinet_id = create_cabinet(client_id, cabinet_name, mp)
        if mp == "Ozon":
            create_token(cabinet_id=cabinet_id, ozon_seller_token=ozon_seller_token, ozon_id_seller=ozon_id_seller,
                         ozon_id_performance=ozon_id_performance, ozon_performance_token=ozon_performance_token)
        else:
            create_token(cabinet_id=cabinet_id, wb_stat_token=wb_stat_token, wb_promo_token=wb_promo_token)
        return True
    except Exception as e:
        print(e)
        return False


async def read_excel_wb_zip(file_path, client_id, file_name, cabinet_name, date_to, mp):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall('reports/' + str(client_id) + '/')
    os.remove("reports/" + str(client_id) + "/" + str(client_id) + ".zip")
    excel_list = os.listdir('reports/' + str(client_id) + '/')
    excel_file = excel_list[0]
    os.rename('reports/' + str(client_id) + '/' + excel_file,
              'reports/' + str(client_id) + '/' + file_name.replace('.zip', '') + '.xlsx')
    try:
        result_append = read_excel_wb("reports/" + str(client_id) + "/" + file_name.replace('.zip', '') + ".xlsx",
                                      client_id,
                                      file_name.replace('.zip', '.xlsx'),
                                      cabinet_name,
                                      date_to[16:],
                                      mp)
        if result_append == -1:
            print("Error in read_excel_wb -1 from function")
            os.rmdir("reports/" + str(client_id))
            return False
    except Exception as e:
        print(e)
        print("Error in read_excel_wb")
        os.rmdir("reports/" + str(client_id))
        return False
    os.rmdir("reports/" + str(client_id))
    return True


def gen_rrd_id_wb(df, client_id, cabinet_id, correct_rdd=False):
    list_rrd_id = []
    if correct_rdd:
        for i in range(len(df)):
            list_rrd_id.append(hashlib.sha256(str(df['№'][i]).encode() +
                                              str(client_id).encode() +
                                              str(cabinet_id).encode()).hexdigest())
    else:
        for i in range(len(df)):
            list_rrd_id.append(hashlib.sha256(str(df['№'][i]).encode() +
                                              str(df['Баркод'][i]).encode() +
                                              str(df['Тип документа'][i]).encode() +
                                              str(df['Обоснование для оплаты'][i]).encode() +
                                              str(df['Дата заказа покупателем'][i]).encode() +
                                              str(df['Дата продажи'][i]).encode() +
                                              str(df['Виды логистики, штрафов и доплат'][i]).encode() +
                                              str(df['Srid'][i]).encode() +
                                              str(client_id).encode() +
                                              str(cabinet_id).encode()).hexdigest())

    return list_rrd_id


def read_excel_wb(file_path, client_id, file_name, cabinet_name, date_to, mp):
    excel = pd.read_excel(file_path).replace(np.nan, 0, regex=True)
    os.remove(file_path)
    rows_count = len(excel)
    report_id = get_report_id(file_name)
    if report_id is None:
        print('Номер отчета не найден')
        return -1
    cabinet_id = get_cabinet_id(cabinet_name, mp, client_id)
    date_to_datatime = datetime.datetime.strptime(date_to, '%d-%m-%Y')
    date_from_datatime = date_to_datatime - datetime.timedelta(days=6)
    count_miss = 0
    for item in excel['Дата продажи']:
        if str(item) != "0":
            excel_date = datetime.datetime.strptime(str(item), '%Y-%m-%d')
        else:
            continue
        if not date_from_datatime <= excel_date <= date_to_datatime:
            count_miss += 1
    if count_miss / (rows_count / 100) >= 70:
        return -1

    correct_rdd = True
    if excel['№'][0] < 100:
        correct_rdd = False
        list_rdd_id = pd.Series(gen_rrd_id_wb(excel, client_id, cabinet_id), dtype='string')
        list_id = pd.Series(gen_rrd_id_wb(excel, client_id, cabinet_id), dtype='string')
    else:
        list_rdd_id = pd.Series(excel['№'].tolist(), dtype='string')
        list_id = pd.Series(gen_rrd_id_wb(excel, client_id, cabinet_id, correct_rdd=True), dtype='string')
    try:
        new_df = pd.DataFrame(data={  # rrd_id - уникальный идентификатор, хранится в id
            'id': list_id,
            'realizationreport_id': pd.Series([report_id] * rows_count, dtype='int64'),
            'date_added': pd.Series([datetime.date.today().strftime('%Y-%m-%d')] * rows_count, dtype='datetime64[ns]'),
            'client_id': pd.Series([client_id] * rows_count, dtype='int64'),
            'cabinet_id': pd.Series([cabinet_id] * rows_count, dtype='int64'),
            'date_from': pd.Series([(datetime.datetime.strptime(date_to, '%d-%m-%Y') - datetime.timedelta(
                days=6)).strftime('%Y-%m-%dT00:00:00')] * rows_count, dtype='datetime64[ns]'),
            'date_to': pd.Series(
                [(datetime.datetime.strptime(date_to, '%d-%m-%Y')).strftime('%Y-%m-%dT00:00:00')] * rows_count,
                dtype='datetime64[ns]'),
            'create_dt': pd.Series([datetime.date.today().strftime('%Y-%m-%dT%H:%M:%S')] * rows_count,
                                   dtype='datetime64[ns]'),
            'currency_name': pd.Series(['руб'] * rows_count, dtype='string'),
            'suppliercontract_code': pd.Series([None] * rows_count, dtype='string'),
            'rrd_id': list_rdd_id,
            'gi_id': pd.Series(excel['Номер поставки'].tolist(), dtype='int64'),
            'subject_name': pd.Series(excel['Предмет'].tolist(), dtype='string'),
            'nm_id': pd.Series(excel['Код номенклатуры'].tolist(), dtype='int64'),
            'brand_name': pd.Series(excel['Бренд'].tolist(), dtype='string'),
            'sa_name': pd.Series(excel['Артикул поставщика'].tolist(), dtype='string'),
            'ts_name': pd.Series(excel['Размер'].tolist(), dtype='string'),
            'barcode': pd.Series(excel['Баркод'].tolist(), dtype='string'),
            'doc_type_name': pd.Series(excel['Тип документа'].tolist(), dtype='string'),
            'quantity': pd.Series(excel['Кол-во'].tolist(), dtype='int64'),
            'retail_price': pd.Series(excel['Цена розничная'].tolist(), dtype='float64'),
            'retail_amount': pd.Series(excel['Вайлдберриз реализовал Товар (Пр)'].tolist(), dtype='float64'),
            'sale_percentage': pd.Series(excel['Согласованный продуктовый дисконт, %'].tolist(), dtype='float64'),
            'commission_percent': pd.Series([0.0] * rows_count, dtype='float64'),
            'office_name': pd.Series([None] * rows_count, dtype='string'),
            'supplier_oper_name': pd.Series(excel['Обоснование для оплаты'].tolist(), dtype='string'),
            'order_dt': pd.Series(excel['Дата заказа покупателем'].tolist(), dtype='datetime64[ns]'),
            'sale_dt': pd.Series(excel['Дата продажи'].tolist(), dtype='datetime64[ns]'),
            'rr_dt': pd.Series(['1970-01-01T00:00:00'] * rows_count, dtype='datetime64[ns]'),
            'shk_id': pd.Series(excel['ШК'].tolist(), dtype='int64'),
            'retail_price_withdisc_rub': pd.Series(excel['Цена розничная с учетом согласованной скидки'].tolist(),
                                                   dtype='float64'),
            'delivery_amount': pd.Series(excel['Количество доставок'].tolist(), dtype='int64'),
            'return_amount': pd.Series(excel['Количество возврата'].tolist(), dtype='int64'),
            'delivery_rub': pd.Series(excel['Услуги по доставке товара покупателю'].tolist(), dtype='float64'),
            'gi_box_type_name': pd.Series(excel['Тип коробов'].tolist(), dtype='string'),
            'product_discount_for_report': pd.Series([0.0] * rows_count, dtype='float64'),
            'supplier_promo': pd.Series(excel['Промокод %'].tolist(), dtype='float64'),
            'rid': pd.Series(excel['Rid'].tolist(), dtype='int64'),
            'ppvz_spp_prc': pd.Series(
                excel[
                    'Скидка постоянного Покупателя (СПП), %' if 'Скидка постоянного Покупателя (СПП), %' in excel.columns else 'Скидка постоянного Покупателя (СПП)'].tolist(),
                dtype='float64'
            ),
            'ppvz_kvw_prc_base': pd.Series(excel['Размер  кВВ без НДС, % Базовый'].tolist(), dtype='float64'),
            'ppvz_kvw_prc': pd.Series(excel['Итоговый кВВ без НДС, %'].tolist(), dtype='float64'),
            'sup_rating_prc_up': pd.Series(excel['Размер снижения кВВ из-за рейтинга, %'].tolist(), dtype='float64'),
            'is_kgvp_v2': pd.Series(excel['Размер снижения кВВ из-за акции, %'].tolist(), dtype='float64'),
            'ppvz_sales_commission': pd.Series(
                excel['Вознаграждение с продаж до вычета услуг поверенного, без НДС'].tolist(), dtype='float64'),
            'ppvz_for_pay': pd.Series(excel['К перечислению Продавцу за реализованный Товар'].tolist(),
                                      dtype='float64'),
            'ppvz_reward': pd.Series(excel['Возмещение за выдачу и возврат товаров на ПВЗ'].tolist(), dtype='float64'),
            'acquiring_fee': pd.Series(excel['Возмещение издержек по эквайрингу'].tolist(), dtype='float64'),
            'acquiring_bank': pd.Series(excel['Наименование банка-эквайера'].tolist(), dtype='string'),
            'ppvz_vw': pd.Series(excel['Вознаграждение Вайлдберриз (ВВ), без НДС'].tolist(), dtype='float64'),
            'ppvz_vw_nds': pd.Series(excel['НДС с Вознаграждения Вайлдберриз'].tolist(), dtype='float64'),
            'ppvz_office_id': pd.Series(excel['Номер офиса'].tolist(), dtype='int64'),
            'ppvz_office_name': pd.Series(excel['Наименование офиса доставки'].tolist(), dtype='string'),
            'ppvz_supplier_id': pd.Series([0] * rows_count, dtype='int64'),
            'ppvz_supplier_name': pd.Series(excel['Партнер'].tolist(), dtype='string'),
            'ppvz_inn': pd.Series(excel['ИНН партнера'].tolist(), dtype='string'),
            'declaration_number': pd.Series(excel['Номер таможенной декларации'].tolist(), dtype='string'),
            'bonus_type_name': pd.Series(excel['Виды логистики, штрафов и доплат'].tolist(), dtype='string'),
            'sticker_id': pd.Series(excel['Стикер МП'].tolist(), dtype='string'),
            'site_country': pd.Series(excel['Страна'].tolist(), dtype='string'),
            'penalty': pd.Series(excel['Общая сумма штрафов'].tolist(), dtype='float64'),
            'additional_payment': pd.Series(excel['Доплаты'].tolist(), dtype='float64'),
            'rebill_logistic_cost': pd.Series(excel[
                                                  'Возмещение издержек по перевозке' if correct_rdd else 'Возмещение издержек по перевозке/по складским операциям с товаром'].tolist(),
                                              dtype='float64'),
            'rebill_logistic_org': pd.Series(excel['Организатор перевозки'].tolist(), dtype='string'),
            'kiz': pd.Series(excel['Код маркировки'].tolist(), dtype='string'),
            'srid': pd.Series(excel['Srid'].tolist(), dtype='string'),
            'storage_fee': pd.Series(excel['Хранение'].tolist() if "Хранение" in excel.columns else [0] * rows_count,
                                     dtype='float64'),
            'deduction': pd.Series(excel['Удержания'].tolist() if "Удержания" in excel.columns else [0] * rows_count,
                                   dtype='float64'),
            'acceptance': pd.Series(
                excel['Платная приемка'].tolist() if "Платная приемка" in excel.columns else [0] * rows_count,
                dtype='float64'),
            'report_type': pd.Series([0] * rows_count, dtype='int64'),
            'is_correct_rrd': pd.Series([correct_rdd] * rows_count, dtype='bool'),
        })
    except Exception as e:
        print(e)
        print("Не удалось создать фрейм из экселя")
        return -1
    try:
        query = f"""
        SELECT id FROM `{project_id}.{database}.reports_for_bot` WHERE client_id={client_id} AND cabinet_id={cabinet_id}
        """
        query_job = client.query(query)
        df = query_job.to_dataframe()
        if len(df) == 0:
            pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_for_bot', project_id=project_id,
                              if_exists='append',
                              credentials=credentials)
            return 0
    except Exception as e:
        print(e)
        pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_for_bot', project_id=project_id,
                          if_exists='append',
                          credentials=credentials)
        return 0
    select_id_list = df['id'].tolist()
    for item in new_df['id']:
        if item in select_id_list:
            new_df = new_df.drop(new_df[new_df['id'] == item].index)
    if not new_df.empty:
        pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_for_bot', project_id=project_id,
                          if_exists='append',
                          credentials=credentials)
    if new_df.empty:
        return -1
    return 0


def get_cabinet_id(cabinet_name, mp, client_id):
    if mp == "Wildberries":
        mp = "WB"
    query = f"""
        SELECT cabinet_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_name = '{cabinet_name}' AND mp = '{mp}' 
        AND client_id = {client_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    return df['cabinet_id'][0]


def get_report_id(file_name):
    file_name = file_name.replace('.xlsx', '')
    file_name_split = file_name.split('_')
    report_id = 0
    for i in file_name_split:
        if i[0] == "№":
            report_id = i[1:]
    if report_id == 0:
        file_name = file_name.replace('.xlsx', '')
        file_name_split = file_name.split(' ')
        report_id = 0
        for i in file_name_split:
            if i[0].isdigit():
                report_id = i[0:]
        if report_id == 0:
            return None
        else:
            return report_id
    else:
        return report_id


def gen_date_excel(cabinet_name, mp, client_id, is_archive=False, quarter=None):
    query = f"""
        SELECT cabinet_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_name = '{cabinet_name}' AND mp = '{mp}' AND client_id = {client_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    cabinet_id = df['cabinet_id'][0]
    today = datetime.date.today()
    today_num = today.weekday()
    day_end = today - datetime.timedelta(days=today_num + 1)
    start_date = datetime.date(2024, 1, 29)

    if is_archive:
        quarter = quarter.replace('(', '').replace(')', '')
        quarter = quarter.split(' - ')
        start_date = datetime.datetime.strptime(quarter[0], '%Y-%m-%d').date()
        day_end = datetime.datetime.strptime(quarter[1], '%Y-%m-%d').date()

    all_days_list = check_report_date(cabinet_id)
    if all_days_list is None:
        all_days_list = []
    result = []

    while day_end >= start_date:
        if day_end.strftime('%d-%m-%Y') not in all_days_list:
            result.append(f"С "
                          f"{(day_end - datetime.timedelta(days=6)).strftime('%d-%m-%Y')} "
                          f"по "
                          f"{day_end.strftime('%d-%m-%Y')}")
        day_end = day_end - datetime.timedelta(days=7)
    return result


def check_report_date(cabinet_id):
    query = f"""
        SELECT DISTINCT date_to FROM `{project_id}.{database}.view_report_union_api_bot`
        WHERE cabinet_id = {cabinet_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)

    result = []
    if len(df) != 0:
        for item in df['date_to'].tolist():
            date = str(item)
            result.append(date[8:10] + "-" + date[5:7] + "-" + date[0:4])
    return result


def send_log(tg_id, tg_username, phone, is_client, tg_command, input_data, client_id):
    connector.connect()
    query = f"""
                INSERT INTO {env('POSTGRES_SCHEMA')}.logs (date, 
                                                            tg_id, 
                                                            tg_username, 
                                                            phone, 
                                                            is_client, 
                                                            tg_command, 
                                                            input_data, 
                                                            client_id)
                VALUES ('{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'::timestamp, 
                        {tg_id}, 
                        '{tg_username}', 
                        '{phone}', 
                        {is_client}, 
                        '{tg_command}', 
                        '{input_data}', 
                        '{client_id}')
            """
    connector.execute_sql(command=query)
    connector.close()


def write_new_lead(tg_id, tg_username, phone_number, name, turnover):
    query = pd.DataFrame(data={
        'tg_id': [int(tg_id)],
        'tg_username': [str(tg_username)],
        'name': [name],
        'phone_number': [str(phone_number)],
        'date': [datetime.datetime.now()],
        'turnover': [str(turnover)],
        'is_confirmed': [False]
    })
    schema = create_schema(query)
    schema[4]['type'] = 'DATETIME'

    pandas_gbq.to_gbq(query, f'{project_id}.{database}.leads', project_id=project_id,
                      if_exists='append',
                      credentials=credentials,
                      table_schema=schema)


def check_confirmed(tg_id):
    query = f"""
        SELECT is_confirmed FROM `{project_id}.{database}.leads` WHERE tg_id = {tg_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) != 0 and df['is_confirmed'][0] == True:
        return True
    else:
        return False


def update_client_gmail(client_id, gmail):
    try:
        query = f"""
            UPDATE `{project_id}.{database}.clients` SET gmail = '{gmail}' WHERE client_id = {client_id}
        """
        query_job = client.query(query)
        result = query_job.result()
        return True
    except Exception as e:
        print(e)
        return False


def add_new_potential_client(tg_id, name, phone, turnover, tg_username, date, is_finish_reg):
    query = f"""
        INSERT INTO {env('POSTGRES_SCHEMA')}.potential_clients
        VALUES ({tg_id}, '{name}', '{phone}', '{turnover}', '{tg_username}', '{date}'::timestamp, {is_finish_reg})
        ON CONFLICT (tg_id) DO NOTHING
    """
    connector.connect()
    connector.execute_sql(command=query)
    connector.close()


def update_potential_clients(tg_id):
    query = f"""
        UPDATE {env('POSTGRES_SCHEMA')}.potential_clients
        SET is_finish_reg = TRUE
        WHERE tg_id = {tg_id}
    """
    connector.connect()
    connector.execute_sql(command=query)
    connector.close()


def check_potential_users():
    query = f"""
        SELECT * FROM {env('POSTGRES_SCHEMA')}.potential_clients
        WHERE 
        date < '{(datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")}'
        AND 
        is_finish_reg = FALSE 
    """
    connector.connect()
    df = connector.read_sql(query)
    connector.close()
    return df


def clear_potential_users(tg_id_list):
    result = ",".join([str(i) for i in tg_id_list])
    query = f"""UPDATE {env('POSTGRES_SCHEMA')}.potential_clients 
    SET is_finish_reg = TRUE 
    WHERE tg_id IN ({result})"""

    connector.connect()
    connector.execute_sql(command=query)
    connector.close()


def get_tg_id_from_client_id(client_id):
    query = f"""
        SELECT tg_id FROM `{project_id}.{database}.clients` WHERE client_id = {client_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) != 0:
        return df['tg_id'][0]
    else:
        return 1


def check_mp(cabinet_id):
    query = f"""
        SELECT mp FROM `{project_id}.{database}.cabinets` WHERE cabinet_id = {cabinet_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    return df['mp'][0]


def check_token_promo(token):
    response = requests.get(
        "https://advert-api.wb.ru/adv/v1/promotion/count",
        headers={
            "Authorization": f"{token}"
        }
    )
    if response.status_code == 200:
        return True
    else:
        return False


def check_token_stat(token):
    response = requests.get(
        "https://statistics-api.wildberries.ru/api/v1/supplier/incomes",
        headers={
            "Authorization": f"{token}"
        },
        params={
            "dateFrom": (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        }
    )
    if response.status_code == 200:
        return True
    else:
        return False


def check_token_seller(token, ozon_id_seller):
    response = requests.post(
        "https://api-seller.ozon.ru/v1/description-category/tree",
        headers={
            "Client-Id": f"{ozon_id_seller}",
            "Api-Key": f"{token}"
        }
    )
    if response.status_code == 200:
        return True
    else:
        return False


def check_token_performance(token, ozon_id_performance):
    pass


def refresh_wb_token(token, type, cabinet_id):
    try:
        query = f"""UPDATE `{project_id}.{database}.wb_token` SET key = '{token}' WHERE cabinet_id = {cabinet_id} AND type = '{type}'"""
        query_job = client.query(query)
        results = query_job.result()
        return True
    except Exception as e:
        print(e)
        return False


def refresh_ozon_token(token, client_id, type, cabinet_id):
    try:
        if type == "seller":
            query = f"""UPDATE `{project_id}.{database}.ozon_token` SET key = '{token}', ozon_client_id = {client_id} WHERE cabinet_id = {cabinet_id} AND type = '{type}'"""
        elif type == "performance":
            query = f"""UPDATE `{project_id}.{database}.ozon_token` SET performance_client_secret = '{token}', performance_client_id = {client_id} WHERE cabinet_id = {cabinet_id} AND type = '{type}'"""
        else:
            return False
        query_job = client.query(query)
        results = query_job.result()
        return True
    except Exception as e:
        print(e)
        return False
