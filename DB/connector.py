import environs
from google.oauth2 import service_account
from google.cloud import bigquery
import psycopg2

env = environs.Env()
env.read_env()
credentials = service_account.Credentials.from_service_account_file(env('credentials'))
project_id = env('projectId')
database = env('database')
client = bigquery.Client(credentials=credentials, project=project_id)


class Connectors:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = psycopg2.connect(
            host=env('POSTGRES_HOST'),
            database=env('POSTGRES_DB'),
            user=env('POSTGRES_USER'),
            password=env('POSTGRES_PASSWORD'),
            port=env('POSTGRES_PORT')
        )
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()
        self.cursor.close()

    def execute_sql(self, command):
        self.cursor.execute(command)
        self.connection.commit()

    def read_sql(self, command):
        self.cursor.execute(command)
        return self.cursor.fetchall()


connector = Connectors()
