import os
import random
import time
import logging
from uuid import uuid4
from flask import Flask, request, jsonify

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler, set_logger_provider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# ------------------------------
# Configuration
# ------------------------------
ALLOY_ENDPOINT = "http://alloy:4317"

resource = Resource.create(attributes={
    SERVICE_NAME: "flask-demo-app",
    "environment": "kind-lab",
    "instance.id": str(uuid4())
})

# ------------------------------
# Tracing
# ------------------------------
trace_provider = TracerProvider(resource=resource)
otlp_trace_exporter = OTLPSpanExporter(endpoint=ALLOY_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# ------------------------------
# Metrics
# ------------------------------
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=ALLOY_ENDPOINT, insecure=True)
)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)
meter = metrics.get_meter("flask-demo-meter")
request_counter = meter.create_counter("http_requests_total", description="Number of HTTP requests")

# ------------------------------
# Logging
# ------------------------------
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(
    OTLPLogExporter(endpoint=ALLOY_ENDPOINT, insecure=True)
))
set_logger_provider(logger_provider)

otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)
LoggingInstrumentor().instrument(set_logging_format=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ------------------------------
# Flask App
# ------------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def home():
    with tracer.start_as_current_span("home-request"):
        logger.info("Home route accessed")
        request_counter.add(1)
        return """
        <h1>Flask OpenTelemetry Demo</h1>
        <p>Available endpoints:</p>
        <ul>
            <li>/simple</li>
            <li>/nested</li>
            <li>/error</li>
            <li>/chain</li>
            <li>/delayed-chain</li>
        </ul>
        """

@app.route("/simple")
def simple_trace():
    with tracer.start_as_current_span("simple-operation") as span:
        span.set_attribute("operation.type", "simple")
        logger.info("Simple operation executed")
        request_counter.add(1)
        return {"status": "ok", "message": "Simple trace generated"}

@app.route("/nested")
def nested_trace():
    with tracer.start_as_current_span("parent-operation") as parent:
        parent.set_attribute("operation.type", "parent")
        time.sleep(0.05)
        with tracer.start_as_current_span("child-operation-1") as c1:
            c1.set_attribute("operation.type", "child")
            time.sleep(0.05)
        with tracer.start_as_current_span("child-operation-2") as c2:
            c2.set_attribute("operation.type", "child")
            time.sleep(0.05)
        logger.info("Nested operation executed")
        request_counter.add(1)
        return {"status": "ok", "message": "Nested trace generated"}

@app.route("/error")
def error_trace():
    with tracer.start_as_current_span("error-operation") as span:
        try:
            1 / 0
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            logger.error("Error operation triggered")
            request_counter.add(1)
            return {"status": "error", "message": "Error trace generated"}

@app.route("/chain")
def chain_trace():
    with tracer.start_as_current_span("chain-root") as span:
        span.set_attribute("operation.step", "start")
        logger.info("Chain operation started")
        request_counter.add(1)
        return {"status": "ok", "message": "Chain trace generated"}

# ------------------------------
# Delayed chain for latency demonstration
# ------------------------------
@app.route("/delayed-chain")
def delayed_chain():
    with tracer.start_as_current_span("delayed-chain-root") as span:
        span.set_attribute("operation.type", "delayed-chain")
        logger.info("Delayed chain started")
        request_counter.add(1)
        time.sleep(random.uniform(1.0, 3.0))
        return {"status": "ok", "message": "Delayed chain trace generated"}

# ------------------------------
# Run app
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
