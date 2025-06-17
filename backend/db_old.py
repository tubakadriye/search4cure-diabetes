# db.py

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus

def get_database():
    username = quote_plus('Tuba')
    password = quote_plus('di+ig3n(')

    uri = 'mongodb+srv://' + username + ':' + password + "@diamind.q4fmjuw.mongodb.net/?retryWrites=true&w=majority&appName=DiaMind"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['diabetes_db']
    return db
