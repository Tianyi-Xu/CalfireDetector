from rest_api.utils import get_coordinates
from flask_restful import Resource
from flask_jwt import jwt_required
import requests
import csv
import requests
from rest_api.models.fire import FireModel
from rest_api import app


# return the newest fires today in the database
class Fires(Resource):
    # return all the fires in 24 hours in the us
    @jwt_required()
    def get(self):
        return {'fires': [row.json() for row in FireModel.find_all()]}
        
    @staticmethod
    def fetchDB(): 
        with app.app_context():
            # delete all fires
            FireModel.delete_all()
            headers = {'Authorization': 'Bearer EDL-U1fd791d466531fe4fa131d52e4d6e2a08b688614b6814efbf8769790b1d'}
            download_header = {'Authorization': 'Bearer dGlhbnlpX3h1OmVIUjVjMnQ1WlVCNVlXaHZieTVqYjIwPToxNjUxMzYwOTQ0OjNlZWYyMTU4YTNlZGVhNzA5OTNiNTgwYmE3YmQxZmUxMjgzMTY3ODQ'}
            filesListURL = "https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/FIRMS/suomi-npp-viirs-c2/USA_contiguous_and_Hawaii?fields=all&format=json"
            files = requests.get(filesListURL, headers=headers).json()
            newest_file_URL = files["content"][-1]["downloadsLink"]
            newestFile = requests.get(newest_file_URL, headers=download_header, allow_redirects=True)
            fires = []
            reader = csv.DictReader(newestFile.text.splitlines())
            for line in reader:
                fires.append(line)
                # print(line)
            for line in fires:
                datetime= (
                    line['acq_date'][0:4]+line['acq_date'][5:7]+line['acq_date'][8:10]+
                    line['acq_time'][0:2]+line['acq_time'][3:5]
                )
                f = FireModel(
                    latitude= float(line['latitude']),
                    longitude= float(line['longitude']),
                    bright_ti4 = float(line['bright_ti4']),
                    scan = float(line['scan']),
                    track = float(line['track']),
                    acq_datetime = datetime,
                    satellite = line['satellite'],
                    confidence = line['confidence'],
                    version = line['version'],
                    bright_ti5 = float(line['bright_ti5']),
                    frp= float(line['frp']),
                    daynight = line['daynight']
                )
                # save all fires
                f.save_to_db()



