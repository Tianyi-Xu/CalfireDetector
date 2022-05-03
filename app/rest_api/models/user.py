from rest_api import db,app
from rest_api.utils import get_coordinates

class UserModel(db.Model):
    __tablename__ = 'users' 
    id = db.Column(db.Integer, primary_key = True) # tell sqlalchmy what column in the table it maps to
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(80), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float,nullable=False)


    def __init__(self, username, password, email, address):
        self.username = username
        self.password = password # those instance variables name need to match the class variable name
        self.email = email
        self.address = address
        lat,log = get_coordinates(address)
        self.latitude = lat
        self.longitude = log

    @classmethod # since we used the class name user
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id = _id).first()

    @classmethod
    def find_by_location(cls, latitude_min, latitude_max, longitude_min, longitude_max):
        with app.app_context():
            return cls.query.filter(
                cls.latitude >= latitude_min, cls.latitude<=latitude_max,
                cls.longitude>=longitude_min, cls.longitude<=longitude_max).all()
        

    def save_to_db(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()