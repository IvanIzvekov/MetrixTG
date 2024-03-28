from DB.connector import project_id, credentials, client, database
import pandas_gbq
import requests
import datetime


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
                UPDATE `eloquent-anthem-329803.metrix_test.clients`
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
        print(df)
    except Exception:
        print(Exception)
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
    except Exception:
        print(Exception)
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
        except Exception:
            print(Exception)
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
        except Exception:
            print(Exception)
            return False
    return True

