from rest_api.utils import get_coordinates
from flask_restful import Resource,reqparse
from flask_jwt import jwt_required
import requests
import geopandas as gpd
import pandas as pd
import csv
from shapely.geometry import Point
from datetime import datetime
from rest_api.models.user import UserModel
from rest_api.models.fire import FireModel
from rest_api import app, queue


class Fires(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("active",
                    type=bool,
                    required=True,
                    help='The active field is required'
                    )
    parser.add_argument('location',type=str)

    # fetch all current "Lighting Spot" from NASA (used for user report validate)
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


    # get all current active fires in California
    @staticmethod
    def fetchFires():
        calfireURL = "https://www.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=false"
        fires = requests.get(calfireURL).json()
        return fires

    # Notify users near the active fire
    @staticmethod
    def notice():
        # from rest_api import queue
        fires = Fires.fetchFires()
        if len(fires) == 0:
            return
        for fire in fires:
            location = fire["Location"]
            lat = fire["Latitude"]
            lon = fire["Longitude"]
            fire_start_time = fire["Started"]
            users = Fires.find_nearby_users(lat, lon)        
            notify_email_list = [user.email for user in users]
            for email in notify_email_list:
                queue.enqueue('worker.send_message',
                args = ("We detected there is a Fire near your address! at location: "
                        + location
                        + " fire is started at time: " + fire_start_time, email))

    # find user in 10km within the fire position(1 longitude ~= 111km)
    @staticmethod
    def find_nearby_users(latitude, longitude):
        users = UserModel.find_by_location(
            latitude_min = latitude - 0.1, 
            latitude_max = latitude + 0.1, 
            longitude_min = longitude - 0.1, 
            longitude_max = longitude + 0.1
        )
        return users   

    @jwt_required()
    def get(self):
        data = Fires.parser.parse_args()
        # Return 3 most recent past fires within 25 mile radius of a location using arcgis
        if (data["active"] == False):
            lat, lon = get_coordinates(data['location'])
            if lat > 90 or lat < -90 or lon >180 or lon <-180:
                return {'message':'Error: invalid coordinates.'}, 400
            try:
                coords = str(lon)+"%2C+"+str(lat)
                urlhead = "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/California_Fire_Perimeters/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry="
                # Current buffer: 25 miles, change if desired where "&distance="
                urltail = "&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&resultType=standard&distance=25.0&units=esriSRUnit_StatuteMile&returnGeodetic=false&outFields=*&returnGeometry=true&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=none&maxAllowableOffset=&geometryPrecision=&outSR=4326&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
                url = urlhead+coords+urltail
                
                # Make API request using URL and make into geodataframe.
                polys = requests.get(url).json()
                polypd = gpd.GeoDataFrame.from_features(polys["features"])
                polypd.crs = 4326 # Set CRS to match that of input dataset.
                
                # Return 3 most recent fires within 25 mile radius.
                recent = polypd.sort_values('CONT_DATE', ascending = False).head(3)
                
                # Turn original lat into point.
                geom = Point(lon, lat)
                point = gpd.GeoDataFrame(crs=4326, geometry=[geom])   
                recent = recent.to_crs(3310)
                pointproj = point.to_crs(3310)
                pointproj_geom = pointproj.iloc[0]['geometry']

                # Calculating distance from the Point to ALL Polygons, Convert distances to miles.
                recent['distances'] = recent.distance(pointproj_geom)
                recent['distances'] = recent['distances']/1609.344
                recent['date'] = recent['CONT_DATE'].apply(lambda t: datetime.utcfromtimestamp(t/1000).strftime('%Y-%m-%d'))
                recentdf = pd.DataFrame(recent.drop(columns='geometry'))
                fires = list()

                for i in recentdf.index:
                    fires.append({
                        'Name:': recentdf['FIRE_NAME'].loc[i],
                        'Date Contained:': recentdf['date'].loc[i],
                        'Size (acres):': round(recentdf['GIS_ACRES'].loc[i],2),
                        'Distance:': round(recentdf['distances'].loc[i],2)
                    })
                return fires, 200
            except:
                return {"message" : "Internal Server Error"}, 500 
        
        else:
            # return current active fires in California
            return Fires.fetchFires()


