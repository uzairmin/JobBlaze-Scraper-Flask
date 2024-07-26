from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from app.database import db_config
from scraper.blueprint import scraping_blueprint

load_dotenv()

app = Flask(__name__)
db_config(app)
app.register_blueprint(scraping_blueprint)

SWAGGER_URL="/swagger"
API_URL="/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Access API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)