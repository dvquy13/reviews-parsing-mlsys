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
