from rest_api import app, db



if __name__ == '__main__':
    db.init_app(app) # only init the sqlalchemy when start the app
    app.app_context().push()
    app.run(host="0.0.0.0",port=5000, debug=True)
