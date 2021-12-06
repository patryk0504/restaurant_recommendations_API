from neo4j import GraphDatabase, basic_auth
from application.env import env
from flask import g

DATABASE_USERNAME = env('RESTAURANT_DATABASE_USERNAME')
DATABASE_PASSWORD = env('RESTAURANT_DATABASE_PASSWORD')
DATABASE_URL = env('RESTAURANT_DATABASE_URL')
driver = GraphDatabase.driver(DATABASE_URL, auth=basic_auth(DATABASE_USERNAME, str(DATABASE_PASSWORD)))


def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db
