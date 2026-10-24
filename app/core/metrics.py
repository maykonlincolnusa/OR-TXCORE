from prometheus_client import Counter, Histogram, make_asgi_app

payment_requests = Counter("ortxcore_payment_requests_total", "Payment requests", ["status"])
payment_latency = Histogram("ortxcore_payment_duration_seconds", "Payment request latency")
metrics_app = make_asgi_app()
