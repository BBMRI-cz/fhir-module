import logging
from util.custom_logger import setup_logger

from prometheus_client import Gauge

last_sync_timestamp = Gauge('fhir_last_sync_timestamp', 'Timestamp of the last sync', ['service'])

# Progress tracking metrics
sync_progress_total = Gauge('fhir_sync_progress_total', 'Total items to sync', ['service', 'resource_type'])
sync_progress_current = Gauge('fhir_sync_progress_current', 'Current items processed', ['service', 'resource_type'])
sync_in_progress = Gauge('fhir_sync_in_progress', 'Whether sync is currently running', ['service'])
sync_current_phase = Gauge('fhir_sync_current_phase', 'Current sync phase (0=idle, 1=organizations, 2=patients, 3=conditions, 4=specimens)', ['service'])

# Metric registry for generic access
METRIC_REGISTRY = {
    'last_sync_timestamp': last_sync_timestamp,
    'sync_progress_total': sync_progress_total,
    'sync_progress_current': sync_progress_current,
    'sync_in_progress': sync_in_progress,
    'sync_current_phase': sync_current_phase,
}

setup_logger()
logger = logging.getLogger()

class MetricsService:
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def set_metric(self, metric_name: str, value: float, labels: dict = None) -> None:
        if labels is None:
            labels = {}
        
        if not self.__check_metric_exists(metric_name):
            return
        
        all_labels = {'service': self.service_name, **labels}

        try:
            METRIC_REGISTRY[metric_name].labels(**all_labels).set(value)
        except Exception:
            self.__unsupported_operation(metric_name, 'set')
    
    def set_sync_progress(self, resource_type: str, current: int, total: int) -> None:
        try:
            sync_progress_current.labels(service=self.service_name, resource_type=resource_type).set(current)
            sync_progress_total.labels(service=self.service_name, resource_type=resource_type).set(total)
        except Exception as e:
            logger.error(f"Error setting sync progress: {e}")
    
    def increment_sync_progress(self, resource_type: str) -> None:
        try:
            sync_progress_current.labels(service=self.service_name, resource_type=resource_type).inc()
        except Exception as e:
            logger.error(f"Error incrementing sync progress: {e}")
    
    def reset_sync_progress(self) -> None:
        try:
            resource_types = ['organizations', 'patients', 'conditions', 'specimens', 'biobank', 'collections']
            for resource_type in resource_types:
                sync_progress_current.labels(service=self.service_name, resource_type=resource_type).set(0)
                sync_progress_total.labels(service=self.service_name, resource_type=resource_type).set(0)
            
            sync_current_phase.labels(service=self.service_name).set(0)
        except Exception as e:
            logger.error(f"Error resetting sync progress: {e}")
    
    def start_sync(self) -> None:
        try:
            self.reset_sync_progress()
            
            sync_in_progress.labels(service=self.service_name).set(1)
        except Exception as e:
            logger.error(f"Error starting sync: {e}")
    
    def end_sync(self) -> None:
        """Mark sync as completed."""
        try:
            sync_in_progress.labels(service=self.service_name).set(0)
            sync_current_phase.labels(service=self.service_name).set(0)
        except Exception as e:
            logger.error(f"Error ending sync: {e}")
    
    def set_sync_phase(self, phase: int) -> None:
        try:
            sync_current_phase.labels(service=self.service_name).set(phase)
        except Exception as e:
            logger.error(f"Error setting sync phase: {e}")

    def __check_metric_exists(self, metric_name: str) -> bool:
        if metric_name not in METRIC_REGISTRY:
            logger.error(f"Metric {metric_name} not found")
            return False
        return True

    def __unsupported_operation(self, metric_name: str, operation: str) -> None:
        logger.error(f"Operation {operation} not supported for metric {metric_name}")

def get_metrics_for_service(service_name: str) -> MetricsService:
    return MetricsService(service_name)


def _find_metric_value_for_service(metric_gauge, service_name: str, default_value=0, value_type=int):
    """Find and return a metric value for a specific service."""
    for sample in metric_gauge.collect()[0].samples:
        if sample.labels.get('service') == service_name:
            return value_type(sample.value)
    return default_value


def _collect_resource_metrics_by_type(metric_gauge, service_name: str) -> dict:
    """Collect resource metrics grouped by resource type."""
    resource_data = {}
    for sample in metric_gauge.collect()[0].samples:
        if sample.labels.get('service') == service_name:
            resource_type = sample.labels.get('resource_type')
            resource_data[resource_type] = int(sample.value)
    return resource_data


def _calculate_resource_percentage(current: int, total: int) -> float:
    """Calculate percentage progress, handling division by zero."""
    return round((current / total * 100), 2) if total > 0 else 0


def _build_resource_progress(resource_totals: dict, resource_currents: dict) -> dict:
    """Build resource progress data with current, total, and percentage."""
    resources = {}
    all_resource_types = set(list(resource_totals.keys()) + list(resource_currents.keys()))
    
    for resource_type in all_resource_types:
        total = resource_totals.get(resource_type, 0)
        current = resource_currents.get(resource_type, 0)
        
        resources[resource_type] = {
            'current': current,
            'total': total,
            'percentage': _calculate_resource_percentage(current, total)
        }
    
    return resources


def _create_error_response(error_message: str) -> dict:
    """Create a standardized error response."""
    return {
        'in_progress': False,
        'current_phase': 0,
        'resources': {},
        'error': error_message
    }


def get_sync_progress(service_name: str) -> dict:
    """Get current sync progress for a service."""
    try:
        in_progress = _find_metric_value_for_service(
            sync_in_progress, service_name, default_value=False, value_type=bool
        )
        current_phase = _find_metric_value_for_service(
            sync_current_phase, service_name, default_value=0, value_type=int
        )
        
        resource_totals = _collect_resource_metrics_by_type(
            sync_progress_total, service_name
        )
        resource_currents = _collect_resource_metrics_by_type(
            sync_progress_current, service_name
        )
        
        resources = _build_resource_progress(resource_totals, resource_currents)
        
        return {
            'in_progress': in_progress,
            'current_phase': current_phase,
            'resources': resources
        }
    except Exception as e:
        logger.error(f"Error getting sync progress: {e}")
        return _create_error_response(str(e)) 