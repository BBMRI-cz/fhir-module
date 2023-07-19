import time

import requests

from util.custom_logger import logger


def is_endpoint_available(endpoint_url, max_attempts=10, wait_time=60) -> bool:
    """
    Check for the availability of a http endpoint
    :param endpoint_url: URL for the endpoint
    :param max_attempts: max number of attempts for connection retries
    :param wait_time: time in between unsuccessful connection attempts
    :return: true if reachable, false otherwise
    """
    attempts = 0
    while attempts < max_attempts:
        try:
            response = requests.get(endpoint_url)
            response.raise_for_status()
            logger.info(f"Endpoint '{endpoint_url}' is available.")
            return True
        except requests.exceptions.RequestException as e:
            logger.info(
                f"Attempt {attempts + 1}/{max_attempts}: Endpoint not available yet. Retrying in {wait_time} seconds.")
            attempts += 1
            time.sleep(wait_time)

    logger.warning(f"Endpoint '{endpoint_url}' was not available after {max_attempts} attempts.")
    return False
