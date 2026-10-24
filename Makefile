.PHONY: build kind-up deploy status logs test clean port-forward

build:
	docker build -f services/payment-core/Dockerfile -t or-txcore/payment-core:local .
	docker build -f services/fraudshield-ml/Dockerfile -t or-txcore/fraudshield-ml:local .
	docker build -f services/outbox-worker/Dockerfile -t or-txcore/outbox-worker:local .
	docker build -f services/audit-service/Dockerfile -t or-txcore/audit-service:local .
	docker build -f services/fraudshield-dashboard/Dockerfile -t or-txcore/fraudshield-dashboard:local .

kind-up:
	kind create cluster --name or-txcore

deploy: build
	kind load docker-image or-txcore/payment-core:local or-txcore/fraudshield-ml:local or-txcore/outbox-worker:local or-txcore/audit-service:local or-txcore/fraudshield-dashboard:local --name or-txcore
	helm upgrade --install nats oci://registry-1.docker.io/bitnamicharts/nats -n or-txcore --create-namespace -f helm/nats-values-local.yaml
	kubectl apply -k k8s/overlays/local

status:
	kubectl get pods,svc,pvc -n or-txcore

logs:
	kubectl logs -n or-txcore deploy/payment-core -f

port-forward:
	kubectl port-forward -n or-txcore svc/payment-core 8000:8000

test:
	.venv/bin/python -m pytest

clean:
	kind delete cluster --name or-txcore
