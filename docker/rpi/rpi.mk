BOARDS += rpi

local-rpi: version
	docker buildx bake --file=docker/rpi/bake.hcl --set rpi.tagsfrigate:latest-rpi rpi

build-rpi: version
	docker buildx bake --file=docker/rpi/bake.hcl --set rpi.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-rpi rpi

push-rpi: build-rpi
	docker buildx bake --push --file=docker/rpi/bake.hcl --set rpi.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-rpi rpi