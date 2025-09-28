KIND_CLUSTER_NAME := rightsizer-kind
IMAGE_PREFIX ?= rightsizer-local

.PHONY: all build-images kind-create kind-delete k8s-apply k8s-clean

all: build-images

build-images:
	docker build -t $(IMAGE_PREFIX)/dcgm-mock:latest dcgm-mock
	docker build -t $(IMAGE_PREFIX)/rightsizer-collector:latest rightsizer-collector
	docker build -t $(IMAGE_PREFIX)/rightsizer-nginx:latest rightsizer-nginx

kind-create:
	kind create cluster --name $(KIND_CLUSTER_NAME) --config kind/kind-config.yaml

kind-delete:
	kind delete cluster --name $(KIND_CLUSTER_NAME)

k8s-apply:
	kubectl apply -k k8s/

k8s-clean:
	kubectl delete -k k8s/

load-images:
	# Load local images into kind (run after kind-create)
	kind load docker-image $(IMAGE_PREFIX)/dcgm-mock:latest --name $(KIND_CLUSTER_NAME)
	kind load docker-image $(IMAGE_PREFIX)/rightsizer-collector:latest --name $(KIND_CLUSTER_NAME)
	kind load docker-image $(IMAGE_PREFIX)/rightsizer-nginx:latest --name $(KIND_CLUSTER_NAME)

.PHONY: load-images-verify
load-images-verify: load-images
	# Run small verification script that checks images exist inside the kind node
	./scripts/kind-ensure-images.sh $(KIND_CLUSTER_NAME) $(IMAGE_PREFIX)/dcgm-mock:latest $(IMAGE_PREFIX)/rightsizer-collector:latest $(IMAGE_PREFIX)/rightsizer-nginx:latest

deploy-local: build-images kind-create load-images k8s-apply
	@echo "Deployed to kind cluster '$(KIND_CLUSTER_NAME)'."
