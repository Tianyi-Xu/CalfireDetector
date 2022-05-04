# anyone can report fire , verify if the fire is actually fire from the database
# (data are fire in 24 hours in the US downloaded from nasa api every 15 mins)
# if it is verified to be a fire, then report all the users nearby(22km) 

from flask_restful import Resource,reqparse
from flask_jwt import jwt_required
from rest_api.models.fire import FireModel
from rest_api.models.user import UserModel
from rest_api.models.fire import FireModel
from rest_api.utils import get_coordinates

# for report a fire
class Report(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "location", type=str, required=True, help="location missing"
    )

    def get(self):
        data = self.parser.parse_args()
        lat, log = get_coordinates(data['location'])
        is_lit = Report.validate(lat, log)
        return {
            "is_lit": is_lit
        }, 200


    @staticmethod
    def validate(latitude, longitude):
        validated = False
        location = FireModel.find_by_location(
        latitude_min=latitude - 0.1,
        latitude_max=latitude + 0.1,
        longitude_min=longitude - 0.1,
        longitude_max=longitude + 0.1
        )
        if not location:
            return validated
        
        print("find fire", location.latitude, location.longitude)
        if location and location.bright_ti4>400:
            validated = True
            Report.notify(latitude=location.latitude, longitude=location.longitude)
        return validated

    @staticmethod
    def notify(latitude, longitude):
        # from rest_api import queue
        email_list = Report.find_nearby_users(latitude, longitude)
        for email in email_list:
            print(email + " notified")
            # queue.enqueue('worker.send_message',
            # args = ("We detected there is a possible Fire near your address!", email))
        
    
    @staticmethod
    def find_nearby_users(latitude, longitude):
        # 1 longitude = 111km find user in 11km
        users = UserModel.find_by_location(
            latitude_min = latitude - 0.1, 
            latitude_max = latitude + 0.1, 
            longitude_min = longitude - 0.1, 
            longitude_max = longitude + 0.1
        )
        notify_email_list = [user.email for user in users]
        return notify_email_list











