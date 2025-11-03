import logging
import threading

from flask import Flask, jsonify

from service.blaze_service import BlazeService
from service.miabis_blaze_service import MiabisBlazeService
from util.custom_logger import setup_logger
from util.metrics import get_sync_progress

setup_logger()
logger = logging.getLogger()

app = Flask(__name__)


def create_api(blaze_service: BlazeService,miabis_blaze_service: MiabisBlazeService = None):

    @app.route('/miabis-sync', methods=['POST'])
    def miabis_sync():
        logger.info("MIABIS on FHIR: Manually starting sync.")
        if miabis_blaze_service is None:
            return jsonify({"error": "MIABIS on FHIR service is not initialized. Please check if MIABIS is enabled and mapping file configuration is correct."}), 503
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
            return jsonify({"error": "MIABIS on FHIR service is not initialized. Please check if MIABIS is enabled and mapping file configuration is correct."}), 503
        threading.Thread(target=miabis_blaze_service.delete_everything).start()
        return jsonify({"message": "Delete started. see logs of fhir-module for more info"})

    @app.route('/delete', methods=['POST'])
    def delete():
        logger.info("Manually deleting every resource")
        threading.Thread(target=blaze_service.delete_everything).start()
        return jsonify({"message": "Delete started. see logs of fhir-module for more info"})

    @app.route('/sync-progress', methods=['GET'])
    def get_standard_sync_progress():
        """Get progress of the standard FHIR sync operation"""
        progress = get_sync_progress('blaze')
        return jsonify(progress)

    @app.route('/miabis-sync-progress', methods=['GET'])
    def get_miabis_sync_progress():
        """Get progress of the MIABIS on FHIR sync operation"""
        if miabis_blaze_service is None:
            return jsonify({"error": "MIABIS on FHIR service is not initialized. Please check if MIABIS is enabled and mapping file configuration is correct."}), 503
        progress = get_sync_progress('miabis_blaze')
        return jsonify(progress)

    return app
