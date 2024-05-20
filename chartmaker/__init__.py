from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.secret_key = "sdljflwejfiewj12"
    app.config.from_object(config)

    # ORM
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models


    # 블루프린트
    from .views import scatterplot
    from .views import heatmap
    app.register_blueprint(scatterplot.blue_scatter)
    app.register_blueprint(heatmap.blue_heatmap)

    return app