from flask import Flask, request
import logging
import time

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

# Define service name for identification in Loki/Tempo/Mimir
resource = Resource(attributes={"service.name": "flask-demo-app"})

# Setup tracing
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

# OTLP exporter (sends data to Grafana Alloy)
otlp_exporter = OTLPSpanExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Setup metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)
meter = metrics.get_meter("flask-demo-meter")
request_counter = meter.create_counter("http_requests_total", description="Number of HTTP requests")

# Setup logging
LoggingInstrumentor().instrument(set_logging_format=True)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@app.route("/")
def home():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("home-request"):
        logger.info("Home route accessed.")
        request_counter.add(1)
        return "Hello from Flask + OpenTelemetry + Grafana Stack!"

@app.route("/work")
def do_work():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("work-operation"):
        logger.info("Started /work route.")
        time.sleep(0.8)
        logger.info("Finished /work route.")
        request_counter.add(1)
        return "Work simulated successfully!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
