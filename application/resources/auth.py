import binascii
import datetime
import os

from flask import request
from flask_restful import Resource
from application.database.db_conf import get_db
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, create_refresh_token, jwt_required, decode_token
import hashlib
import sys
import uuid


def hash_password(password):
    return generate_password_hash(password).decode('utf8')


def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)


def hash_avatar(username):
    if sys.version[0] == 2:
        s = username
    else:
        s = username.encode('utf-8')
    return hashlib.md5(s).hexdigest()


def serialize_user(user):
    return {
        'id': user['id'],
        'username': user['username'],
        'avatar': {
            'full_size': 'https://www.gravatar.com/avatar/{}?d=retro'.format(hash_avatar(user['username']))
        }
    }


class Register(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get('password')
        if not username:
            return {'username': 'This field is required.'}, 400
        if not password:
            return {'password': 'This field is required.'}, 400

        def get_user_by_username(tx, username):
            return tx.run(
                '''
                MATCH (user:User {username: $username}) RETURN user
                ''', {'username': username}
            ).single()

        db = get_db()
        result = db.read_transaction(get_user_by_username, username)
        if result and result.get('user'):
            return {'username': 'username already in use'}, 400

        def create_user(tx, username, password):
            # CREATE (user:User {id: $id, username: $username, password: $password, api_key: $api_key}) RETURN user
            return tx.run(
                '''
                CREATE (user:User {id: $id, username: $username, password: $password}) RETURN user

                ''',
                {
                    'id': str(uuid.uuid4()),
                    'username': username,
                    'password': hash_password(password),
                    # 'api_key': binascii.hexlify(os.urandom(20)).decode()
                }
            ).single()

        results = db.write_transaction(create_user, username, password)
        user = results['user']
        return serialize_user(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username:
            return {'username': 'This field is required.'}, 400
        if not password:
            return {'password': 'This field is required.'}, 400

        def get_user_by_username(tx, username):
            return tx.run(
                '''
                MATCH (user:User {username: $username}) RETURN user
                ''', {'username': username}
            ).single()

        db = get_db()
        result = db.read_transaction(get_user_by_username, username)
        try:
            user = result['user']
        except KeyError:
            return {
                       'status': 'fail',
                       'message': 'username does not exist'}, 400

        if check_password(user['password'], password):
            expires = datetime.timedelta(minutes=20)
            access_token = create_access_token(identity=str(user.id), expires_delta=expires)
            return {
                       'status': 'success',
                       'message': 'Successfully logged in.',
                       'auth_token': access_token
                   }, 200
        return {
            'status': 'fail',
            'message': 'Wrong password'
        }
