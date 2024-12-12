import logging
import threading

from flask import Flask, jsonify

from service.blaze_service import BlazeService
from service.miabis_blaze_service import MiabisBlazeService
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()

app = Flask(__name__)


def create_api(miabis_blaze_service: MiabisBlazeService, blaze_service: BlazeService):

    @app.route('/miabis-sync', methods=['POST'])
    def miabis_sync():
        logger.info("MIABIS on FHIR: Manually starting sync.")
        threading.Thread(target=miabis_blaze_service.sync).start()
        return jsonify({"message": "sync finished. see logs of fhir-module for more info"})

    @app.route('/sync', methods=['POST'])
    def sync_now():
        logger.info("Manually starting sync.")
        threading.Thread(target=blaze_service.sync).start()
        return jsonify({"message": "sync finished"})

    @app.route('/miabis-delete', methods=['POST'])
    def miabis_delete():
        logger.info("MIABIS on FHIR: Manually deleting every resource")
        threading.Thread(target=miabis_blaze_service.delete_everything).start()
        return jsonify({"message": "delete finished"})


    @app.route('/delete', methods=['POST'])
    def delete():
        logger.info("Manually deleting every resource")
        threading.Thread(target=blaze_service.delete_everything).start()
        return jsonify({"message": "delete finished"})


    return app
