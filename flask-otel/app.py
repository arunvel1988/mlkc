from flask import Flask, request, jsonify, render_template_string
import logging
import time
import random
import requests

# --- OpenTelemetry imports ---
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource

# Traces
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import set_logger_provider

# --- Flask initialization ---
app = Flask(__name__)

# --- Resource definition ---
resource = Resource(attributes={"service.name": "flask-demo-app"})

# ========================
# 🚀 OpenTelemetry Setup
# ========================

# --- Tracing setup ---
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
otlp_trace_exporter = OTLPSpanExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))

# --- Metrics setup ---
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)
meter = metrics.get_meter("flask-demo-meter")
request_counter = meter.create_counter("http_requests_total", description="Number of HTTP requests")

# --- Logs setup ---
log_exporter = OTLPLogExporter(endpoint="http://alloy.alloy.svc.cluster.local:4317", insecure=True)
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
set_logger_provider(logger_provider)

# Attach OTel handler to Python logging
otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)

# --- Instrumentation setup ---
LoggingInstrumentor().instrument(set_logging_format=True)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# --- Python logger ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Tracer instance ---
tracer = trace.get_tracer(__name__)

# --- List of endpoints for home page ---
ENDPOINTS = [
    {"path": "/", "description": "Home page with all available endpoints"},
    {"path": "/work", "description": "Simulate some work operation"},
    {"path": "/db", "description": "Simulate a database operation"},
    {"path": "/external", "description": "Call an external API"},
    {"path": "/chain", "description": "Simulate a chain of operations"},
]

# ========================
# 🌐 Flask Routes
# ========================

@app.route("/")
def home():
    with tracer.start_as_current_span("home-request"):
        logger.info("Home route accessed.")
        request_counter.add(1)

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flask + OpenTelemetry Demo</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f6f7; color: #333; padding: 20px; }
                h1 { color: #2c3e50; }
                ul { list-style-type: none; padding: 0; }
                li { margin: 10px 0; }
                a { text-decoration: none; padding: 10px 15px; background-color: #3498db; color: white; border-radius: 5px; transition: 0.3s; }
                a:hover { background-color: #2980b9; }
                .endpoint-desc { font-size: 0.9em; color: #555; margin-left: 5px; }
                .container { max-width: 800px; margin: auto; }
                .footer { margin-top: 40px; font-size: 0.8em; color: #777; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Flask + OpenTelemetry Demo!</h1>
                <p>Explore the available endpoints below:</p>
                <ul>
                    {% for ep in endpoints %}
                    <li>
                        <a href="{{ ep.path }}">{{ ep.path }}</a>
                        <span class="endpoint-desc">{{ ep.description }}</span>
                    </li>
                    {% endfor %}
                </ul>
                <div class="footer">
                    <p>Traces, metrics, and logs are exported to OpenTelemetry via OTLP.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template, endpoints=ENDPOINTS)


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


# ========================
# 🏁 App Entry Point
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
