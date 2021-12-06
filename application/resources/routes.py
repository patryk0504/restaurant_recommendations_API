from application.resources.auth import Register, Login
from application.resources.restaurants import LocationList, CuisineList, RestaurantList, RestaurantListByLocation, \
    RestaurantListByCuisine, RestaurantListRatedByUser, RestaurantRecommendationsByRating, \
    RestaurantRecommendationsByRestaurantAllCountry, RestaurantRecommendationsByRestaurantInCity
from application.resources.user import RateRestaurant, SimilarUsers, Rates


def initialize_routes(api):
    api.add_resource(Register, "/api/auth/register")
    api.add_resource(Login, "/api/auth/login")

    # api.add_resource(LocationList, "/api/location/list")
    api.add_resource(CuisineList, "/api/cuisine/list")

    api.add_resource(RestaurantList, "/api/restaurant/list")
    # api.add_resource(RestaurantListByLocation, "/api/restaurant/location/<string:location_id>")
    # api.add_resource(RestaurantListByCuisine, "/api/restaurant/cuisine/<string:cuisine_id>")
    # api.add_resource(RestaurantListRatedByUser, "/api/restaurant/rated")
    api.add_resource(RestaurantRecommendationsByRating, "/api/restaurant/recommendations/rating")
    api.add_resource(RestaurantRecommendationsByRestaurantAllCountry,
                     "/api/restaurant/<int:restaurant_id>/recommendations/country")
    api.add_resource(RestaurantRecommendationsByRestaurantInCity,
                     "/api/restaurant/<int:restaurant_id>/recommendations/city")

    api.add_resource(RateRestaurant, "/api/restaurant/<int:restaurant_id>/rate")
    api.add_resource(SimilarUsers, "/api/users/similar")
    api.add_resource(Rates, "/api/restaurant/<int:restaurant_id>/rates")
