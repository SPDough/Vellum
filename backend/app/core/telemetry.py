from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings


def setup_telemetry(settings: Settings) -> None:
    """Set up OpenTelemetry instrumentation."""

    # Create resource with service information
    resource = Resource.create(
        {
            SERVICE_NAME: settings.otel_service_name,
            SERVICE_VERSION: "1.0.0",
            "service.environment": settings.environment,
        }
    )

    # Set up tracing
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)

    # Configure OTLP span exporter
    otlp_span_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,  # Use for development; set to False in production with TLS
    )

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_span_exporter)
    trace_provider.add_span_processor(span_processor)

    # Set up metrics
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_exporter_otlp_endpoint, insecure=True
    )

    metric_reader = PeriodicExportingMetricReader(
        exporter=otlp_metric_exporter,
        export_interval_millis=10000,  # Export every 10 seconds
    )

    metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metric_provider)

    # Instrument libraries
    SQLAlchemyInstrumentor().instrument(enable_commenter=True)
    Psycopg2Instrumentor().instrument(enable_commenter=True)

    print(f"✅ OpenTelemetry configured for {settings.otel_service_name}")


def instrument_fastapi(app):
    """Instrument FastAPI application."""
    FastAPIInstrumentor.instrument_app(app)


# Utility functions for custom spans and metrics
def get_tracer(name: str = "otomeshon"):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str = "otomeshon"):
    """Get a meter instance."""
    return metrics.get_meter(name)


# Custom metrics for business logic
class BusinessMetrics:
    """Custom business metrics for the application."""

    def __init__(self):
        self.meter = get_meter("otomeshon.business")

        # Trade processing metrics
        self.trade_counter = self.meter.create_counter(
            name="trades_processed_total",
            description="Total number of trades processed",
            unit="1",
        )

        self.trade_processing_time = self.meter.create_histogram(
            name="trade_processing_duration_seconds",
            description="Time taken to process trades",
            unit="s",
        )

        self.trade_exceptions = self.meter.create_counter(
            name="trade_exceptions_total",
            description="Total number of trade exceptions",
            unit="1",
        )

        # Workflow metrics
        self.workflow_executions = self.meter.create_counter(
            name="workflow_executions_total",
            description="Total number of workflow executions",
            unit="1",
        )

        self.workflow_duration = self.meter.create_histogram(
            name="workflow_execution_duration_seconds",
            description="Time taken for workflow execution",
            unit="s",
        )

        self.human_interventions = self.meter.create_counter(
            name="human_interventions_total",
            description="Total number of human interventions required",
            unit="1",
        )

        # LLM metrics
        self.llm_calls = self.meter.create_counter(
            name="llm_calls_total",
            description="Total number of LLM API calls",
            unit="1",
        )

        self.llm_tokens = self.meter.create_counter(
            name="llm_tokens_total",
            description="Total number of LLM tokens used",
            unit="1",
        )

        self.llm_cost = self.meter.create_counter(
            name="llm_cost_total", description="Total cost of LLM usage", unit="USD"
        )

        # SOP metrics
        self.sop_searches = self.meter.create_counter(
            name="sop_searches_total",
            description="Total number of SOP searches",
            unit="1",
        )

        self.automation_suggestions = self.meter.create_counter(
            name="automation_suggestions_total",
            description="Total number of automation suggestions generated",
            unit="1",
        )

    def record_trade_processed(self, trade_type: str, status: str, duration: float):
        """Record a trade processing event."""
        self.trade_counter.add(1, {"trade_type": trade_type, "status": status})
        self.trade_processing_time.record(duration, {"trade_type": trade_type})

    def record_trade_exception(self, exception_type: str, severity: str):
        """Record a trade exception."""
        self.trade_exceptions.add(
            1, {"exception_type": exception_type, "severity": severity}
        )

    def record_workflow_execution(
        self, workflow_type: str, status: str, duration: float
    ):
        """Record a workflow execution."""
        self.workflow_executions.add(
            1, {"workflow_type": workflow_type, "status": status}
        )
        self.workflow_duration.record(duration, {"workflow_type": workflow_type})

    def record_human_intervention(self, workflow_type: str, reason: str):
        """Record a human intervention event."""
        self.human_interventions.add(
            1, {"workflow_type": workflow_type, "reason": reason}
        )

    def record_llm_call(self, model: str, provider: str, tokens: int, cost: float):
        """Record an LLM API call."""
        self.llm_calls.add(1, {"model": model, "provider": provider})
        self.llm_tokens.add(tokens, {"model": model, "provider": provider})
        self.llm_cost.add(cost, {"model": model, "provider": provider})

    def record_sop_search(self, search_type: str, results_count: int):
        """Record an SOP search."""
        self.sop_searches.add(
            1,
            {
                "search_type": search_type,
                "results_found": "yes" if results_count > 0 else "no",
            },
        )

    def record_automation_suggestion(self, sop_category: str, confidence: float):
        """Record an automation suggestion."""
        self.automation_suggestions.add(
            1,
            {
                "sop_category": sop_category,
                "confidence_level": (
                    "high"
                    if confidence > 0.8
                    else "medium" if confidence > 0.5 else "low"
                ),
            },
        )


# Global metrics instance
business_metrics = BusinessMetrics()
