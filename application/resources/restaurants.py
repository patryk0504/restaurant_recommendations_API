from flask_jwt_extended import create_access_token, get_jwt_identity, create_refresh_token, jwt_required, decode_token
from flask_restful import Resource
from application.database.db_conf import get_db


class LocationList(Resource):
    @staticmethod
    def _serialize_locations(location):
        return {
            "id": location["id"],
            "name": location["name"]
        }

    @jwt_required()
    def get(self):
        def get_locations(q):
            return list(q.run('MATCH (l:Location)  SET l.id=id(l) RETURN l'))

        db = get_db()
        result = db.write_transaction(get_locations)
        return [LocationList._serialize_locations(record['l']) for record in result]


class CuisineList(Resource):
    @staticmethod
    def _serialize_cuisine(cuisine):
        return {
            "id": cuisine["id"],
            "name": cuisine["name"]
        }

    @jwt_required()
    def get(self):
        def get_cuisine(q):
            return list(q.run('MATCH (n:Cuisine) SET n.id = id(n) RETURN n order by (n.name)'))

        db = get_db()
        result = db.write_transaction(get_cuisine)
        return [CuisineList._serialize_cuisine(record['n']) for record in result]


class RestaurantList(Resource):
    @staticmethod
    def _serialize_restaurant(restaurant):
        return {
            "id": restaurant["id"],
            "restaurant_id": restaurant["restaurant_id"],
            "name": restaurant["name"],
            "address": restaurant["address"],
            "address_latitude": restaurant["address_latitude"],
            "address_longitude": restaurant["address_longitude"],
            "average_rating": restaurant["average_rating"],
            "gluten_free": restaurant["gluten_free"],
            "vegan_options": restaurant["vegan_options"],
            "vegetarian_friendly": restaurant["vegetarian_friendly"],
            "price_level": restaurant["price_level"],
            "popularity_detailed": restaurant["popularity_detailed"],
            "popularity_generic": restaurant["popularity_generic"]
        }

    @staticmethod
    def _serialize_restaurant_with_relationships(restaurant):
        return {
            "id": restaurant["n"]["id"],
            "restaurant_id": restaurant["n"]["restaurant_id"],
            "name": restaurant["n"]["name"],
            "address": restaurant["n"]["address"],
            "address_latitude": restaurant["n"]["address_latitude"],
            "address_longitude": restaurant["n"]["address_longitude"],
            "average_rating": restaurant["n"]["average_rating"],
            "gluten_free": restaurant["n"]["gluten_free"],
            "vegan_options": restaurant["n"]["vegan_options"],
            "vegetarian_friendly": restaurant["n"]["vegetarian_friendly"],
            "price_level": restaurant["n"]["price_level"],
            "popularity_detailed": restaurant["n"]["popularity_detailed"],
            "popularity_generic": restaurant["n"]["popularity_generic"],
            "cuisines": restaurant["cuisines"],
            "location": restaurant["location"]
        }

    @jwt_required()
    def get(self):
        def get_restaurant(q):
            return list(q.run(
                '''
                MATCH (l:Location)<-[:LOCATED_IN]-(n:Restaurant)-[:SERVES]->(c:Cuisine) 
                SET n.id = id(n)
                RETURN n, collect(c.name) as cuisines, l.name as location
                '''
            ))

        db = get_db()
        result = db.write_transaction(get_restaurant)
        # return [RestaurantList._serialize_restaurant(record['r']) for record in result]
        return [RestaurantList._serialize_restaurant_with_relationships(record) for record in result]


class RestaurantListByLocation(Resource):
    @jwt_required()
    def get(self, location_id):
        def get_restaurant(q, location_id):
            return list(q.run(
                '''
                MATCH (r:Restaurant) -[:LOCATED_IN]-> (l:Location) 
                WHERE l.id = toInteger($location_id)
                RETURN r
                ''', {'location_id': location_id}
            ))

        db = get_db()
        result = db.read_transaction(get_restaurant, location_id)
        return [RestaurantList._serialize_restaurant(record['r']) for record in result]


class RestaurantListByCuisine(Resource):
    @jwt_required()
    def get(self, cuisine_id):
        def get_restaurant(q, cuisine_id):
            return list(q.run(
                '''
                MATCH (r:Restaurant) -[:SERVES]-> (c:Cuisine) 
                WHERE c.id = toInteger($cuisine_id)
                RETURN r
                ''', {'cuisine_id': cuisine_id}
            ))

        db = get_db()
        result = db.read_transaction(get_restaurant, cuisine_id)
        return [RestaurantList._serialize_restaurant(record['r']) for record in result]


class RestaurantListRatedByUser(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        def get_restaurant(q, user_id):
            return list(q.run(
                '''
                MATCH (u:User) -[:RATED]-> (r:Restaurant)
                WHERE id(u) = toInteger($user_id)
                RETURN r
                ''', {'user_id': user_id}
            ))

        db = get_db()
        result = db.read_transaction(get_restaurant, user_id)
        return [RestaurantList._serialize_restaurant(record['r']) for record in result]


class RestaurantRecommendationsByRating(Resource):
    @staticmethod
    def _serialize_restaurant_recommendations(restaurant):
        return {
            "id": restaurant["restaurant"]["id"],
            "restaurant_id": restaurant["restaurant"]["restaurant_id"],
            "name": restaurant["restaurant"]["name"],
            "address": restaurant["restaurant"]["address"],
            "address_latitude": restaurant["restaurant"]["address_latitude"],
            "address_longitude": restaurant["restaurant"]["address_longitude"],
            "average_rating": restaurant["restaurant"]["average_rating"],
            "gluten_free": restaurant["restaurant"]["gluten_free"],
            "vegan_options": restaurant["restaurant"]["vegan_options"],
            "vegetarian_friendly": restaurant["restaurant"]["vegetarian_friendly"],
            "price_level": restaurant["restaurant"]["price_level"],
            "popularity_detailed": restaurant["restaurant"]["popularity_detailed"],
            "popularity_generic": restaurant["restaurant"]["popularity_generic"],
            "location": restaurant["location"],
            "other_users": restaurant['other_users'],
            "avg_rating": restaurant['avgRating']
        }

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        def get_restaurant(q, user_id):
            return list(q.run(
                '''
                MATCH (me:User)-[my:RATED]->(r:Restaurant)
                MATCH (other:User)-[their:RATED]->(r)
                WHERE id(me) = toInteger($user_id)
                AND me <> other
                AND abs(my.rating - their.rating) < 2
                WITH other,r
                MATCH (other)-[otherRating:RATED]->(r2:Restaurant)
                WHERE r2 <> r
                WITH avg(otherRating.rating) AS avgRating, r2, collect(other.username) as other_users
                MATCH (r2) -[:LOCATED_IN]-> (l:Location)
                RETURN r2 as restaurant, avgRating, l.name as location, other_users
                ORDER BY avgRating desc
                LIMIT 25
                ''', {"user_id": user_id}
            ))

        db = get_db()
        result = db.read_transaction(get_restaurant, user_id)
        print(result)
        if result:
            return {
                "status": "success",
                "message": "Recommendations found",
                "recommended": [RestaurantRecommendationsByRating._serialize_restaurant_recommendations(record) for
                                record in result]}
        else:
            return {
                "status": "fail",
                "message": "Recommendations not found",
                "recommended": []
            }


class RestaurantRecommendationsByRestaurantAllCountry(Resource):
    @staticmethod
    def _serialize_restaurant_recommendations(record):
        return {
            "id": record['other']["id"],
            "restaurant_id": record['other']["restaurant_id"],
            "name": record['other']["name"],
            "address": record['other']["address"],
            "address_latitude": record['other']["address_latitude"],
            "address_longitude": record['other']["address_longitude"],
            "average_rating": record['other']["average_rating"],
            "gluten_free": record['other']["gluten_free"],
            "vegan_options": record['other']["vegan_options"],
            "vegetarian_friendly": record['other']["vegetarian_friendly"],
            "price_level": record['other']["price_level"],
            "popularity_detailed": record['other']["popularity_detailed"],
            "popularity_generic": record['other']["popularity_generic"],

            "base_restaurant": record['m.name'],
            "jaccard": record['jaccard'],
            "base_params": record['s1'],
            "recommended_params": record['s2'],
            "location": record['s2'][0]
        }

    @jwt_required()
    def get(self, restaurant_id):
        def get_restaurant(q, restaurant_id):
            return list(q.run(
                '''
                MATCH (m:Restaurant)-[:SERVES|LOCATED_IN]-(t)-[:SERVES|LOCATED_IN]-(other:Restaurant)
                where id(m) = toInteger($restaurant_id)
                WITH m, other, COUNT(t) AS intersection, COLLECT(t.name) AS i
                
                MATCH (m)-[:SERVES|LOCATED_IN]-(mt)
                WITH m, other, intersection,i, COLLECT(mt.name) AS s1
                
                MATCH (other)-[:SERVES|LOCATED_IN]-(ot)
                WITH m,other,intersection,i, s1, COLLECT(ot.name) AS s2
                
                WITH m,other,intersection,s1,s2
                WITH m,other,intersection,s1+[x IN s2 WHERE NOT x IN s1] AS union, s1, s2
                
                RETURN m.name, other, s1,s2, round(((1.0*intersection)/SIZE(union)), 2) AS jaccard ORDER BY jaccard DESC LIMIT 100
                ''', {"restaurant_id": restaurant_id}
            ))

        db = get_db()
        result = db.read_transaction(get_restaurant, restaurant_id)
        if (result):
            return {
                "status": "success",
                "message": "Recommendations found",
                "recommended": [
                    RestaurantRecommendationsByRestaurantAllCountry._serialize_restaurant_recommendations(record)
                    for record in result]}
        else:
            return {
                "status": "fail",
                "message": "Recommendations not found",
                "recommended": []
            }


class RestaurantRecommendationsByRestaurantInCity(Resource):
    @jwt_required()
    def get(self, restaurant_id):
        def get_restaurant(q, restaurant_id):
            return list(q.run(
                '''
                MATCH (m:Restaurant)-[:LOCATED_IN]->(location:Location)<-[:LOCATED_IN]-(other:Restaurant)
                where id(m) = toInteger($restaurant_id)
                MATCH (m)-[:SERVES]-(t)-[:SERVES]-(other)
                WITH m, other, COUNT(t) AS intersection, COLLECT(t.name) AS i
                MATCH (m)-[:SERVES|LOCATED_IN]-(mt)
                WITH m, other, intersection,i, COLLECT(mt.name) AS s1
                MATCH (other)-[:SERVES|LOCATED_IN]-(ot)
                WITH m,other,intersection,i, s1, COLLECT(ot.name) AS s2
                
                WITH m,other,intersection,s1,s2
                
                WITH m,other,intersection,s1+[x IN s2 WHERE NOT x IN s1] AS union, s1, s2
                
                RETURN m.name, other, s1,s2,round(((1.0*intersection)/SIZE(union)), 2) AS jaccard ORDER BY jaccard DESC LIMIT 100
                ''', {"restaurant_id": restaurant_id}
            ))

        db = get_db()
        result = db.read_transaction(get_restaurant, restaurant_id)
        if (result):
            return {
                "status": "success",
                "message": "Recommendations found",
                "recommended": [
                    RestaurantRecommendationsByRestaurantAllCountry._serialize_restaurant_recommendations(record)
                    for record in result]}
        else:
            return {
                "status": "fail",
                "message": "Recommendations not found",
                "recommended": []
            }
