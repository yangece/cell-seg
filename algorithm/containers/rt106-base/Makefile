DTR ?= thrive20
BASE_IMAGE = thrive20/thrive:latest
IMG = rt106-algorithm-sdk-focal

BUILD_FLAGS = 
GIT_NOT_CLEAN_CHECK = $(shell git status --porcelain)
VERSION = $(strip $(shell cat VERSION))

build:
	@echo "Building ${IMG} from ${BASE_IMAGE}"
	@docker build ${BUILD_FLAGS} \
		--build-arg BASE_IMAGE=${BASE_IMAGE} \
		--build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` \
		--build-arg VCS_REF=`git rev-parse --short HEAD` \
		--build-arg VCS_URL=`git config --get remote.origin.url` \
		-t ${DTR}/${IMG}:latest .
	@docker tag ${DTR}/${IMG}:latest ${DTR}/${IMG}:${VERSION}

push: build
ifneq (x$(GIT_NOT_CLEAN_CHECK), x)
	$(error commit changes before pushing to DTR)
endif
	@docker push ${DTR}/${IMG}:latest
	@docker push ${DTR}/${IMG}:${VERSION}

no-cache:
	@echo "Using --no-cache"
	$(eval BUILD_FLAGS += "--no-cache")

help: 
	@echo "make [no-cache] [tensorflow] build"
	@echo "make [tensorflow] push"

.PHONY: build push no-cache tensorflow help
