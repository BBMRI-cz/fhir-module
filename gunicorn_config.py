# Gunicorn configuration file for multiprocess Prometheus metrics
import threading

from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


def when_ready(_server):
    GunicornPrometheusMetrics.start_http_server_when_ready(8080)


def child_exit(_server, worker):
    GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)


def post_fork(_server, _worker):
    from main import blaze_service, miabis_blaze_service

    if blaze_service is not None:
        blaze_service._sync_lock = threading.Lock()
    if miabis_blaze_service is not None:
        miabis_blaze_service._sync_lock = threading.Lock()
