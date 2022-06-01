import os
from flask import Flask
from application.config import LocalDevelopmentConfig
from application.database import db
from flask_restful import Api

app = None


def create_app():
    app = Flask(__name__, template_folder="templates")
    if os.getenv('ENV', "development") == "production":
        raise Exception("Currently no production config is setup.")
    else:
        app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    app.app_context().push()
    return app


app = create_app()
api = Api(app)
from application.controllers import *

api.add_resource(User_Dashboard_API, "/api/user/<username>")
api.add_resource(Deck_API, "/api/deck")
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
