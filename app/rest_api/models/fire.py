from rest_api import db, app
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

'''
{'latitude': '31.6914', 'longitude': '-116.59462', 'bright_ti4': '346.31', 
'scan': '0.39', 'track': '0.6', 'acq_date': '2022-04-30', 
'acq_time': '21:33', 'satellite': 'N', 'confidence': 
'nominal', 'version': '2.0NRT', 'bright_ti5': '303.38', 
'frp': '4.81', 'daynight': 'D'}
'''
class FireModel(db.Model):
    
    __tablename__ = 'fires'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    bright_ti4 = db.Column(db.Float)
    scan = db.Column(db.Float)
    track = db.Column(db.Float)
    acq_datetime = db.Column(db.String) # date + time
    satellite = db.Column(db.String)
    confidence = db.Column(db.String)
    version = db.Column(db.String)
    bright_ti5 = db.Column(db.Float)
    frp = db.Column(db.Float)
    daynight = db.Column(db.String)

    def __init__(self,
        latitude,
        longitude,
        bright_ti4,
        scan,
        track,
        acq_datetime,
        satellite,
        confidence,
        version,
        bright_ti5,
        frp,
        daynight):
        self.latitude = latitude
        self.longitude = longitude
        self.bright_ti4 = bright_ti4
        self.scan= scan
        self.track = track
        self.acq_datetime = acq_datetime
        self.satellite = satellite
        self.confidence = confidence
        self.version = version
        self.bright_ti5 = bright_ti5
        self.frp=frp
        self.daynight = daynight

    
    def json(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "bright_ti4": self.bright_ti4,
            "scan":self.scan,
            "track":self.track,
            "acq_datetime":self.acq_datetime,
            "satellite":self.satellite,
            "confidence":self.confidence,
            "version":self.version,
            "bright_ti5":self.bright_ti5,
            "frp":self.frp,
            "daynight":self.daynight}
        

    @classmethod
    def find_by_location(cls, latitude_min, latitude_max, longitude_min, longitude_max):
        with app.app_context():
            return cls.query.filter(
                cls.latitude >= latitude_min, cls.latitude<=latitude_max,
                cls.longitude>=longitude_min, cls.longitude<=longitude_max).first()


    def save_to_db(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


    def delete_from_db(self):
        with app.app_context():
            db.session.delete(self)
            db.session.commit()

    @classmethod
    def delete_all(cls):
        with app.app_context():
            cls.query.delete()

    @classmethod
    def find_all(cls):
        with app.app_context():
            return cls.query.all()

