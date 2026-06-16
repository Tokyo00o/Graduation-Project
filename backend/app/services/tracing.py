from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from fastapi import FastAPI


def setup_tracing(
    app: FastAPI,
    service_name: str = "fuzzguard",
    otlp_endpoint: str = None,
    enable_console: bool = False,
):
    resource = Resource.create({SERVICE_NAME: service_name})

    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    elif enable_console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

    try:
        from app.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception:
        pass

    return trace.get_tracer(service_name)
