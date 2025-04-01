from ..get_vector_db import get_vector_db

def getDatabases(model, namespace):
    if (model == None): model = 'nomic-embed-text'

    db = get_vector_db(model, f'str_{namespace}')

    return db
