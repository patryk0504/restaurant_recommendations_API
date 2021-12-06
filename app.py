from flask import Flask, g
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_json import FlaskJSON
from dotenv import load_dotenv, find_dotenv
from application.env import env

load_dotenv(find_dotenv())

app = Flask(__name__)
app.config['SECRET_KEY'] = env('SECRET_KEY')
# CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})
FlaskJSON(app)
api = Api(app)
jwt = JWTManager(app)
import application.resources.routes as routes
routes.initialize_routes(api)


# init database
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()


if __name__ == '__main__':
    app.run()
