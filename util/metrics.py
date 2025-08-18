import logging
from util.custom_logger import setup_logger

from prometheus_client import Gauge

last_sync_timestamp = Gauge('fhir_last_sync_timestamp', 'Timestamp of the last sync', ['service'])

# Metric registry for generic access
METRIC_REGISTRY = {
    'last_sync_timestamp': last_sync_timestamp,
}

setup_logger()
logger = logging.getLogger()

class MetricsService:
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def set_metric(self, metric_name: str, value: float, labels: dict = {}) -> None:
        if not self.__check_metric_exists(metric_name):
            return
        
        all_labels = {'service': self.service_name, **labels}

        try:
            METRIC_REGISTRY[metric_name].labels(**all_labels).set(value)
        except Exception:
            self.__unsupported_operation(metric_name, 'set')

    def __check_metric_exists(self, metric_name: str) -> bool:
        if metric_name not in METRIC_REGISTRY:
            logger.error(f"Metric {metric_name} not found")
            return False
        return True

    def __unsupported_operation(self, metric_name: str, operation: str) -> None:
        logger.error(f"Operation {operation} not supported for metric {metric_name}")

def get_metrics_for_service(service_name: str) -> MetricsService:
    return MetricsService(service_name) 