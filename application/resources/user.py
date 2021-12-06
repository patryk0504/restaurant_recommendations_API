from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from application.database.db_conf import get_db
from flask import request


class Rates(Resource):
    @jwt_required()
    def get(self, restaurant_id):
        user_id = get_jwt_identity()

        def get_rates(q, user_id, restaurant_id):
            return list(q.run(
                '''
                MATCH (u:User)-[r:RATED]->(n:Restaurant) 
                WHERE id(u) = toInteger($user_id) AND id(n) = toInteger($restaurant_id)
                RETURN n.id, r.rating as rating
                ''', {"user_id": user_id, "restaurant_id": restaurant_id}
            ))

        db = get_db()
        result = db.read_transaction(get_rates, user_id, restaurant_id)
        if result:
            return {"id": result[0]['n.id'], "rating": result[0]['rating']}
        return {"status": "success", "message": "Not rated yet"}


class RateRestaurant(Resource):
    @jwt_required()
    def post(self, restaurant_id):
        user_id = get_jwt_identity()
        data = request.get_json()
        rate = data.get('rating')
        print(data)
        if rate < 0 or rate > 5:
            return {
                       "status": "fail",
                       "message": "Rate must be between 0 and 5"
                   }, 400

        def rate_restaurant(q, user_id, restaurant_id, rate):
            return q.run(
                '''
                MATCH(u : User)
                MATCH(r : Restaurant)
                WHERE id(u) = toInteger($user_id) and id(r) = toInteger($restaurant_id)
                WITH u,r
                MERGE (u)-[r2:RATED]->(r)
                SET r2.rating = toInteger($rate)
                RETURN r
                ''', {"user_id": user_id, "restaurant_id": restaurant_id, "rate": rate}
            )

        db = get_db()
        results = db.write_transaction(rate_restaurant, user_id, restaurant_id, rate)
        return {
                   "status": "success",
                   "message": "Successfully rated restaurant",
                   "rating": rate
               }, 200


class SimilarUsers(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        def get_users(q, user_id):
            return list(q.run(
                '''
                MATCH (p1:User)-[x:RATED]->(r:Restaurant)<-[y:RATED]-(p2:User)
                WHERE id(p1) = toInteger($user_id)
                WITH COUNT(r) AS numberrated,SUM(x.rating * y.rating) AS xyDotProduct,
                SQRT(REDUCE(xDot = 0.0, a IN COLLECT(x.rating) | xDot + a^2)) AS xLength,
                SQRT(REDUCE(yDot = 0.0, b IN COLLECT(y.rating) | yDot + b^2)) AS yLength,
                collect(r.name) as restaurants,
                p1, p2 WHERE numberrated > 0
                RETURN restaurants, p1.username as currentUser, p2.username as similarUser, numberrated as numberSimilarRestaurants, round(xyDotProduct / (xLength * yLength), 2) AS sim
                ORDER BY sim DESC
                LIMIT 100;
                ''', {"user_id": user_id}
            ))

        db = get_db()
        result = db.read_transaction(get_users, user_id)
        return [{"restaurants" : record["restaurants"], "username": record['similarUser'], "sim": record['sim']} for record in result]
