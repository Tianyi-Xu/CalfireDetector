from rest_api.utils import get_coordinates
from flask_restful import Resource,reqparse
from flask_jwt import jwt_required
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import requests
from datetime import datetime
from rest_api.models.user import UserModel


# return active fires in california
class CalFires(Resource):
    @jwt_required()
    def get(self):
        return CalFires.fetchFires()

    # get all current active fires 
    @staticmethod
    def fetchFires():
        calfireURL = "https://www.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=false"
        fires = requests.get(calfireURL).json()
        return fires

    @staticmethod
    def notice():
        # from rest_api import queue
        fires = CalFires.fetchFires()
        if len(fires) == 0:
            return
        for fire in fires:
            location = fire["Location"]
            lat = fire["Latitude"]
            lon = fire["Longitude"]
            fire_start_time = fire["Started"]
            users = CalFires.find_nearby_users(lat, lon)        
            notify_email_list = [user.email for user in users]
            for email in notify_email_list:
                print("notified" + email)
                # queue.enqueue('worker.send_message',
                # args = ("We detected there is a Fire near your address! at location: "
                #         + location
                #         + " fire is started at time: " + fire_start_time, email))

    # 1 longitude = 111km 
    # find user in 11km within the fire position(lat and lon)
    @staticmethod
    def find_nearby_users(latitude, longitude):
        users = UserModel.find_by_location(
            latitude_min = latitude - 0.1, 
            latitude_max = latitude + 0.1, 
            longitude_min = longitude - 0.1, 
            longitude_max = longitude + 0.1
        )
        return users




class CalPastFires(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('location',
                type=str,
                required=True,
                help='The location field is required'
                )
    # Return 3 most recent past fires within 25 mile radius of a location
    @jwt_required()
    def get(self):
        data = CalPastFires.parser.parse_args()
        lat, lon = get_coordinates(data['location'])
        # Convert coords to desired format: -122.7140548%2C+38.440429
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
            # Reproject all data to same CRS - NAD 83 ACA Albers Equal Area
            recent = recent.to_crs(3310)
            pointproj = point.to_crs(3310)
            
            # Extracting the geometry of the Point
            pointproj_geom = pointproj.iloc[0]['geometry']

            # Calculating distance from the Point to ALL Polygons
            recent['distances'] = recent.distance(pointproj_geom)
            # Convert distances to miles.
            recent['distances'] = recent['distances']/1609.344
            
            # For each fire, print year, size, and distance to user input point.
            ## To do this, convert unix time (in ms) to YMD time format.
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
            

