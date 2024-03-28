import environs
from google.oauth2 import service_account
from google.cloud import bigquery

env = environs.Env()
env.read_env()
credentials = service_account.Credentials.from_service_account_file(env('credentials'))
project_id = env('projectId')
database = env('database')
client = bigquery.Client(credentials=credentials, project=project_id)
