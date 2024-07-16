.PHONY:
.ONESHELL:

# Set up env
include .env
export

build:
	docker build -t ${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG} .

run:
	docker run -it --rm -p 8080:8080 --env-file ../../.env.staging ${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG}

push:
	docker tag ${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG} ${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG}
	docker push ${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG}
	echo "Successfully pushed image ${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG}"

jaeger-up:
	docker run --rm -d \
		-e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
		-p 16686:16686 \
		-p 4317:4317 \
		-p 4318:4318 \
		-p 9411:9411 \
		-p 6831:6831 \
		jaegertracing/all-in-one:1.59

up:
	docker compose up -d

up-build:
	docker compose up -d --build
