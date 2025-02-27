import logging
import threading

from flask import Flask, jsonify

from service.blaze_service import BlazeService
from service.miabis_blaze_service import MiabisBlazeService
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()

app = Flask(__name__)


def create_api(blaze_service: BlazeService,miabis_blaze_service: MiabisBlazeService = None):

    @app.route('/miabis-sync', methods=['POST'])
    def miabis_sync():
        logger.info("MIABIS on FHIR: Manually starting sync.")
        if miabis_blaze_service is None:
            return jsonify({"message": "MIABIS on FHIR is not provided. If you wish to work with MIABIS on FHIR please change environmental variable in config"})
        threading.Thread(target=miabis_blaze_service.sync).start()
        return jsonify({"message": "MIABIS sync started. see logs of fhir-module for more info"})

    @app.route('/sync', methods=['POST'])
    def sync_now():
        logger.info("Manually starting sync.")
        threading.Thread(target=blaze_service.sync).start()
        return jsonify({"message": "sync started. see logs of fhir-module for more info"})

    @app.route('/miabis-delete', methods=['POST'])
    def miabis_delete():
        logger.info("MIABIS on FHIR: Manually deleting every resource")
        if miabis_blaze_service is None:
            return jsonify({"message": "MIABIS on FHIR is not provided. If you wish to work with MIABIS on FHIR please change environmental variable in config"})
        threading.Thread(target=miabis_blaze_service.delete_everything).start()
        return jsonify({"message": "MIABIS delete started. see logs of fhir-module for more info"})


    @app.route('/delete', methods=['POST'])
    def delete():
        logger.info("Manually deleting every resource")
        threading.Thread(target=blaze_service.delete_everything).start()
        return jsonify({"message": "delete started. see logs of fhir-module for more info"})


    return app
