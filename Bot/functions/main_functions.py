import numpy as np
import pandas as pd

from DB.connector import project_id, credentials, client, database
import pandas_gbq
import requests
import datetime
import pandas
import os
import zipfile
import hashlib


# def create_schema(df):
#     table_schema = []
#     for col in df.columns:
#         if 'object' in str(df[col].dtype):
#             table_schema.append({'name': col, 'type': 'STRING'})
#         elif 'Int64' in str(df[col].dtype):
#             table_schema.append({'name': col, 'type': 'INTEGER'})
#         elif 'dbdate' in str(df[col].dtype):
#             table_schema.append({'name': col, 'type': 'DATE'})
#         elif 'boolean' in str(df[col].dtype):
#             table_schema.append({'name': col, 'type': 'BOOLEAN'})
#
#     return table_schema


async def refresh_tg_id(client_id, tg_id):
    query = f"""
                UPDATE `{project_id}.{database}.clients`
                SET tg_id = '{tg_id}'
                WHERE client_id = {client_id}
            """
    query_job = client.query(query)
    results = query_job.result()


async def check_unic_cabinet(name, client_id):
    query = f"""SELECT cabinet_name FROM `{project_id}.{database}.cabinets` WHERE client_id = {client_id} 
    AND cabinet_name = '{name}'"""
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return True
    else:
        return False


async def check_client_id(tg_id):
    query = f"""
        SELECT phone, client_id FROM `{project_id}.{database}.clients` WHERE tg_id = '{tg_id}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return "", ""
    else:
        return df.phone[0], df.client_id[0]


async def check_client_number(phone):
    query = f"""
        SELECT client_id, tg_id FROM `{project_id}.{database}.clients` WHERE phone = '{phone}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return "", ""
    else:
        return df.client_id[0], df.tg_id[0]


async def check_token_request(token: str, mp: str, promotion=False, ozon_id=""):
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
                "Client-Id": f"{ozon_id}",
                "Api-Key": f"{token}"
            }
        )
        if response.status_code == 200:
            return True
        else:
            return False
    return False


async def check_gmail(tg_id: str):
    query = f"""
        SELECT gmail FROM `{project_id}.{database}.clients` WHERE tg_id = '{tg_id}'"""
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return ""
    else:
        return df.gmail[0]


async def write_to_db(**kwargs):
    wb_stat_token = None
    wb_promo_token = None
    ozon_id = None
    ozon_seller_token = None
    ozon_peformance_token = None
    mp = None
    if kwargs['mp'] == "Wildberries":
        mp = "WB"
        wb_stat_token = kwargs['user_data']['token_stat']
        wb_promo_token = kwargs['user_data']['token_promo']
    elif kwargs['mp'] == "Ozon":
        mp = "Ozon"
        ozon_id = kwargs['user_data']['ozon_id']
        ozon_seller_token = kwargs['user_data']['ozon_seller_token']
        ozon_peformance_token = None
    query = f"""
        INSERT INTO `{project_id}.{database}.leads` (tg_id, 
                                                    client_name, 
                                                    username, phone, 
                                                    mp, 
                                                    cabinet_name, 
                                                    gmail, 
                                                    wb_stat_token, 
                                                    wb_promo_token, 
                                                    ozon_id, 
                                                    ozon_seller_token, 
                                                    ozon_performance_token, 
                                                    date_registration
                                                    )
        VALUES ('{kwargs['tg_id']}', 
                '{kwargs['name']}', 
                '{kwargs['username']}', 
                '{kwargs['phone']}', 
                '{mp}', 
                '{kwargs['cabinet_name']}', 
                '{kwargs['gmail']}', 
                '{wb_stat_token}',
                '{wb_promo_token}',
                '{ozon_id}',
                '{ozon_seller_token}',
                '{ozon_peformance_token}',
                '{kwargs['date']}')
    """
    query_job = client.query(query)
    results = query_job.result()


async def find_cabinets(client_id):
    query = f"""
        SELECT cabinet_name FROM `{project_id}.{database}.cabinets` WHERE client_id = {client_id} AND mp <> 'Ozon'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    return df


async def have_cabinet(cabinet):
    query = f"""
        SELECT cabinet_name FROM `{project_id}.{database}.cabinets` WHERE cabinet_name = '{cabinet}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    if len(df) == 0:
        return False
    else:
        return True


async def create_cabinet_client(user_data):
    try:
        query = f"""
                SELECT MAX(cabinet_id) as cabinet_id FROM `{project_id}.{database}.cabinets`
            """
        df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    except Exception as e:
        print(e)
        return False
    if len(df) == 0:
        cabinet_id = 1
    else:
        cabinet_id = df['cabinet_id'][0] + 1
    try:
        query = f""" INSERT INTO `{project_id}.{database}.cabinets` (
                                                                    cabinet_id, 
                                                                    client_id, 
                                                                    cabinet_name, 
                                                                    mp)
        
                    VALUES ({cabinet_id}, 
                            {user_data['client_id']}, 
                            '{user_data['cabinet_name']}', 
                            '{"WB" if user_data['mp'] == "Wildberries" else "Ozon"}'
                            )"""
        query_job = client.query(query)
        results = query_job.result()
    except Exception as e:
        print(e)
        return False
    if user_data['mp'] == "Wildberries":
        try:
            query = f""" SELECT MAX(id) as id FROM `{project_id}.{database}.wb_token`"""
            df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
            if len(df) == 0:
                wb_token_id = 1
            else:
                wb_token_id = df['id'][0] + 1
            query = f""" INSERT INTO `{project_id}.{database}.wb_token` (
                                                                        id, 
                                                                        cabinet_id, 
                                                                        key, 
                                                                        type
                                                                        ) VALUES 
                                                                        ({wb_token_id}, 
                                                                        {cabinet_id}, 
                                                                        '{user_data['token_stat']}', 
                                                                        'stat'), 
                                                                        ({wb_token_id + 1}, 
                                                                        {cabinet_id}, 
                                                                        '{user_data['token_promo']}', 
                                                                        'adv')"""
            query_job = client.query(query)
            results = query_job.result()
        except Exception as e:
            print(e)
            return False
    else:
        try:
            query = f""" SELECT MAX(id) as id FROM `{project_id}.{database}.ozon_token`"""
            df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
            if len(df) == 0:
                ozon_token_id = 1
            else:
                ozon_token_id = df['id'][0] + 1
            query = f""" INSERT INTO `{project_id}.{database}.ozon_token` (
                                                                        id, 
                                                                        cabinet_id, 
                                                                        key, 
                                                                        ozon_client_id,
                                                                        type,
                                                                        performance_client_secret,
                                                                        performance_client_id
                                                                        ) VALUES 
                                                                        ({ozon_token_id},
                                                                        {cabinet_id},
                                                                        '{user_data['ozon_seller_token']}',
                                                                        '{user_data['ozon_id']}',
                                                                        'seller',
                                                                        {None},
                                                                        {None})
                                                                        """
            query_job = client.query(query)
            results = query_job.result()
        except Exception as e:
            print(e)
            return False
    return True


async def read_excel_wb_zip(file_path, client_id, file_name, cabinet_name, date_to):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall('reports/' + str(client_id) + '/')
    os.remove("reports/" + str(client_id) + "/" + str(client_id) + ".zip")
    excel_list = os.listdir('reports/' + str(client_id) + '/')
    excel_file = excel_list[0]
    os.rename('reports/' + str(client_id) + '/' + excel_file,
              'reports/' + str(client_id) + '/' + file_name.replace('.zip', '') + '.xlsx')
    try:
        if not read_excel_wb("reports/" + str(client_id) + "/" + file_name.replace('.zip', '') + ".xlsx",
                             client_id,
                             file_name.replace('.zip', '.xlsx'),
                             cabinet_name,
                             date_to[16:]):
            print("Error in read_excel_wb")
            os.rmdir("reports/" + str(client_id))
            return False
    except Exception as e:
        print(e)
        print("Error in read_excel_wb")
        return False
    os.rmdir("reports/" + str(client_id))
    return True


def gen_rrd_id_wb(df, client_id, cabinet_id, correct_rdd=False):
    list_rrd_id = []
    if correct_rdd:
        for i in range(len(df)):
            list_rrd_id.append(hashlib.sha256(str(df['Номер поставки'][i]).encode() +
                                              str(client_id).encode() +
                                              str(cabinet_id).encode()).hexdigest())
    else:
        for i in range(len(df)):
            list_rrd_id.append(hashlib.sha256(str(df['Номер поставки'][i]).encode() +
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


def read_excel_wb(file_path, client_id, file_name, cabinet_name, date_to):
    excel = pandas.read_excel(file_path).replace(np.nan, 0, regex=True)
    os.remove(file_path)
    rows_count = len(excel)

    report_id = get_report_id(file_name)
    if report_id is None:
        print('Номер отчета не найден')
        return False
    cabinet_id = get_cabinet_id(cabinet_name)
    correct_rdd = True
    if excel['№'][0] < 100:
        correct_rdd = False
        list_rdd_id = pd.Series(gen_rrd_id_wb(excel, client_id, cabinet_id), dtype='string')
        list_id = pd.Series(gen_rrd_id_wb(excel, client_id, cabinet_id), dtype='string')
    else:
        list_rdd_id = pd.Series(excel['№'].tolist(), dtype='string')
        list_id = pd.Series(gen_rrd_id_wb(excel, client_id, cabinet_id, correct_rdd=True), dtype='string')
    try:
        new_df = pandas.DataFrame(data={  # rrd_id - уникальный идентификатор, хранится в id
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
            'ppvz_spp_prc': pd.Series(excel['Скидка постоянного Покупателя (СПП), %'].tolist(), dtype='float64'),
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
            'storage_fee': pd.Series(excel['Хранение'].tolist(), dtype='float64'),
            'deduction': pd.Series(excel['Удержания'].tolist(), dtype='float64'),
            'acceptance': pd.Series(excel['Платная приемка'].tolist(), dtype='float64'),
            'report_type': pd.Series([0] * rows_count, dtype='int64'),
        })
    except Exception as e:
        print(e)
        print("Не удалось создать фрейм из экселя")
        return False

    try:
        if correct_rdd:
            query = f"""
            SELECT id FROM `{project_id}.{database}.reports_valid_rrd_id`
            """
        else:
            query = f"""
            SELECT id FROM `{project_id}.{database}.reports_invalid_rrd_id`
            """
        query_job = client.query(query)
        df = query_job.to_dataframe()
    except Exception as e:
        print(e)
        if correct_rdd:
            pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_valid_rrd_id', project_id=project_id,
                              if_exists='append',
                              credentials=credentials)
        else:
            pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_invalid_rrd_id', project_id=project_id,
                              if_exists='append',
                              credentials=credentials)
        return True
    select_id_list = df['id'].tolist()
    for item in new_df['id']:
        if item in select_id_list:
            new_df = new_df.drop(new_df[new_df['id'] == item].index)
    if not new_df.empty:
        if correct_rdd:
            pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_valid_rrd_id', project_id=project_id,
                              if_exists='append',
                              credentials=credentials)
        else:
            pandas_gbq.to_gbq(new_df, f'{project_id}.{database}.reports_invalid_rrd_id', project_id=project_id,
                              if_exists='append',
                              credentials=credentials)
    return True


def get_cabinet_id(cabinet_name):
    query = f"""
        SELECT cabinet_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_name = '{cabinet_name}'
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
        return None
    return report_id


def gen_date_excel(cabinet_name):
    query = f"""
        SELECT cabinet_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_name = '{cabinet_name}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    cabinet_id = df['cabinet_id'][0]
    today = datetime.date(2024, 4, 3)
    today_num = today.weekday()
    day_end = today - datetime.timedelta(days=today_num + 1)
    all_days_list = check_report_date(cabinet_id)
    if all_days_list is None:
        all_days_list = []
    result = []
    while day_end >= datetime.date(2024, 1, 29):
        if day_end.strftime('%d-%m-%Y') not in all_days_list:
            result.append(f"С "
                          f"{(day_end - datetime.timedelta(days=6)).strftime('%d-%m-%Y')} "
                          f"по "
                          f"{day_end.strftime('%d-%m-%Y')}")
        day_end = day_end - datetime.timedelta(days=7)
    return result


def check_report_date(cabinet_id):
    query = f"""
        SELECT DISTINCT date_to FROM `{project_id}.{database}.reports_valid_rrd_id` 
        WHERE cabinet_id = {cabinet_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    query = f"""
        SELECT DISTINCT date_to FROM `{project_id}.{database}.reports_invalid_rrd_id` 
        WHERE cabinet_id = {cabinet_id}
        """
    df2 = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    result = []
    if len(df) != 0:
        for item in df['date_to'].tolist():
            date = str(item)[0:10]
            result.append(date[8:10] + "-" + date[5:7] + "-" + date[0:4])
    if len(df2) != 0:
        for item in df2['date_to'].tolist():
            date = str(item)[0:10]
            result.append(date[8:10] + "-" + date[5:7] + "-" + date[0:4])

    return result


def send_log(tg_id, tg_username, phone, is_client, tg_command, input_data):
    query = f"""
        SELECT MAX(id) AS id FROM `{project_id}.{database}.logs`"""
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    df = df.replace(pd.NA, 0)
    if df['id'][0] == 0:
        id = 1
    else:
        id = df['id'][0] + 1
    query = f"""
        INSERT INTO `{project_id}.{database}.logs` 
        (id, date, tg_id, tg_username, phone, is_client, tg_command, input_data)
        VALUES
        ({id},'{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}', {tg_id}, '{tg_username}', '{phone}', {is_client}, '{tg_command}', '{input_data}')
    """
    query_job = client.query(query)
    query_job.result()


def check_correct_date(date, cabinet_name):
    query = f"""
        SELECT cabinet_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_name = '{cabinet_name}'
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    cabinet_id = df['cabinet_id'][0]
    # timestamp_date = datetime.datetime.strptime(date[16:], '%d-%m-%Y').strftime('%Y-%m-%d 00:00:00 UTC')
    # print(timestamp_date)
    # query = f"""
    #     SELECT  FROM `{project_id}.{database}.reports_valid_rrd_id`
    #     WHERE cabinet_id = {cabinet_id} AND date_to = TIMESTAMP('{timestamp_date}')
    # """
    # df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    # if len(df) == 0:
    #     return False
    # return True
    query = f"""
            SELECT DISTINCT date_to FROM `{project_id}.{database}.reports_valid_rrd_id` 
            WHERE cabinet_id = {cabinet_id}
        """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    query = f"""
            SELECT DISTINCT date_to FROM `{project_id}.{database}.reports_invalid_rrd_id` 
            WHERE cabinet_id = {cabinet_id}
            """
    df2 = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    result = []
    if len(df) != 0:
        for item in df['date_to'].tolist():
            date = str(item)[0:10]
            result.append(date[8:10] + "-" + date[5:7] + "-" + date[0:4])
    if len(df2) != 0:
        for item in df2['date_to'].tolist():
            date = str(item)[0:10]
            result.append(date[8:10] + "-" + date[5:7] + "-" + date[0:4])
    print(result)