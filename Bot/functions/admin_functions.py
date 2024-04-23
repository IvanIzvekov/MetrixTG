from DB.connector import project_id, credentials, client, database, connector
import pandas_gbq
import pandas as pd


def refresh_phone(phone, client_id):
    query = f"""
        UPDATE `{project_id}.{database}.clients`
        SET phone = '{phone}'
        WHERE client_id = {client_id}
    """
    query_job = client.query(query)
    results = query_job.result()


async def create_potential_client_from_lead(tg_id):
    try:
        query = f"""
            UPDATE `{project_id}.{database}.leads`
            SET is_confirmed = TRUE
            WHERE tg_id = {tg_id}
        """
        query_job = client.query(query)
        results = query_job.result()
        return True
    except:
        return False


async def renew_subscription(client_id, date):
    try:
        query = f"""
            UPDATE `{project_id}.{database}.clients` SET end_sub = '{date}' WHERE client_id = {client_id}
        """
        query_job = client.query(query)
        result = query_job.result()
        return True
    except Exception as e:
        print(e)
        return False


def get_cabinet_name(cabinet_id):
    query = f"""
        SELECT cabinet_name, client_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_id = {cabinet_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    return df['cabinet_name'][0], df['client_id'][0]


def get_client_id_from_cabinet_id(cabinet_id):
    query = f"""
        SELECT client_id FROM `{project_id}.{database}.cabinets` WHERE cabinet_id = {cabinet_id}
    """
    df = pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
    return df['client_id'][0]


def refresh_url(client_id, uchet_url, finance_url):
    try:
        query = f"""
                DELETE FROM `{project_id}.{database}.clients_gs_url` WHERE client_id = {client_id}
                """
        pandas_gbq.read_gbq(query, project_id=project_id, credentials=credentials, progress_bar_type=None)
        df = pd.DataFrame(
            data={'client_id': [int(client_id)], 'gs_finance': [str(finance_url)], 'gs_uchet': [str(uchet_url)],
                  'gs_manages': [None]})
        pandas_gbq.to_gbq(df,
                          project_id=project_id,
                          credentials=credentials,
                          if_exists='append',
                          destination_table=f"{project_id}.{database}.clients_gs_url")
        return True
    except Exception as e:
        print(e)
        return False
