from flask import Flask, request, jsonify
import logging
import time
import random
import requests

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Initialize Flask
app = Flask(__name__)

# Define OpenTelemetry resource (service identity)
resource = Resource(attributes={"service.name": "flask-demo-app"})

# --- Tracing setup ---
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
otlp_exporter = OTLPSpanExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# --- Metrics setup ---
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)
meter = metrics.get_meter("flask-demo-meter")
request_counter = meter.create_counter("http_requests_total", description="Number of HTTP requests")

# --- Instrumentation setup ---
LoggingInstrumentor().instrument(set_logging_format=True)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Tracer instance ---
tracer = trace.get_tracer(__name__)

@app.route("/")
def home():
    with tracer.start_as_current_span("home-request"):
        logger.info("Home route accessed.")
        request_counter.add(1)
        return "Hello from Flask + OpenTelemetry + Grafana Stack!"

@app.route("/work")
def do_work():
    with tracer.start_as_current_span("work-operation"):
        logger.info("Started /work route.")
        time.sleep(0.8)
        logger.info("Finished /work route.")
        request_counter.add(1)
        return "Work simulated successfully!"

@app.route("/db")
def database_operation():
    with tracer.start_as_current_span("db-operation") as span:
        logger.info("Simulating DB query...")
        query_time = random.uniform(0.3, 1.2)
        time.sleep(query_time)
        result = {"status": "success", "query_time": f"{query_time:.2f}s"}
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.statement", "SELECT * FROM users WHERE active=1")
        logger.info("DB operation done.")
        request_counter.add(1)
        return jsonify(result)

@app.route("/external")
def external_api_call():
    with tracer.start_as_current_span("external-api"):
        url = "https://httpbin.org/delay/1"
        logger.info(f"Calling external API: {url}")
        response = requests.get(url)
        logger.info(f"External API responded with {response.status_code}")
        request_counter.add(1)
        return jsonify({"external_status": response.status_code})

@app.route("/chain")
def chain_operations():
    with tracer.start_as_current_span("chained-request") as parent_span:
        logger.info("Starting chained operation.")

        # Simulate sequential internal calls
        with tracer.start_as_current_span("fetch-user", parent=parent_span):
            time.sleep(random.uniform(0.2, 0.5))
            logger.info("Fetched user data.")

        with tracer.start_as_current_span("process-order", parent=parent_span):
            time.sleep(random.uniform(0.4, 0.9))
            logger.info("Order processed.")

        with tracer.start_as_current_span("notify-service", parent=parent_span):
            time.sleep(random.uniform(0.3, 0.7))
            logger.info("Notification sent.")

        request_counter.add(1)
        logger.info("Chained operation finished.")
        return "Chained operations completed!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
