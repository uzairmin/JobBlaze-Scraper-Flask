from flask import Blueprint, jsonify, request
import threading
from pydantic import ValidationError

from scraper import PORTALS
from scraper.validator import ScraperData
from utils.helpers import validation_err_msg

scraping_blueprint = Blueprint("scraping", __name__)


@scraping_blueprint.route("/run-scraper", methods=["POST"])
def run_scraper():
    try:
        data = request.get_json()
        validated_data = ScraperData(**data)
        thread = threading.Thread(
            target=PORTALS[validated_data.source.value], args=(validated_data.links,)
        )
        thread.start()
        return jsonify({"message": "Scraper started successfully"}), 200

    except ValidationError as e:
        return jsonify({"error": validation_err_msg(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
