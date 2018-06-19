import os


API_URL = os.getenv('API_URL', 'https://jsonplaceholder.typicode.com/')
STORAGE_PATH = os.getenv('STORAGE_PATH', os.path.dirname(os.path.realpath(__file__)))
