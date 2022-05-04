from datetime import timedelta
from flask import Flask
from flask_restful import Api
from flask_jwt import JWT
from apscheduler.schedulers.background import BackgroundScheduler
from redis import Redis
from rq import Queue
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)

# flask-sqlalchemy track all the changed we made to the object, took some resources
# sqlalchemy has its own tracker
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret"
app.config['JWT_AUTH_URL_RULE'] = '/login' #change /auth to /login
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=86400) # 1 day

db = SQLAlchemy(app) # binding the db with the app
db.app = app


from rest_api.resources.user import UserRegister
from rest_api.resources.calfire import CalFires, CalPastFires
from rest_api.resources.fire import Fires
from rest_api.resources.report import Report
from rest_api.security import authenticate, identity
jwt = JWT(app, authenticate, identity) # JWT create a /auth for us 

# r = Redis(host='redis', port=6379)
# queue = Queue(connection=r)

@app.before_first_request
def create_tables():
    # create tables in sqlite db
    with app.app_context():
        db.create_all()
        # fetch nasa data 
        Fires.fetchDB()


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(Fires.fetchDB, 'interval', minutes=1) # run every 15 mins
scheduler.add_job(CalFires.notice, 'interval', minutes= 1) # run every day


api.add_resource(Fires, '/fires')
api.add_resource(CalFires, '/calfires')
api.add_resource(CalPastFires, '/calpastfires')
api.add_resource(Report,'/report')
api.add_resource(UserRegister, '/register')
