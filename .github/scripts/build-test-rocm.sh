#!/bin/bash
declare build_arch
declare build_os

set -xeuo pipefail
if [ "${build_os:0:6}" == ubuntu ]; then
	image=rocm/dev-ubuntu-22.04:6.1-complete
	echo "Using image $image"
	docker run --rm --platform "linux/$build_arch" -i -w /src -v "$PWD:/src" --device=/dev/kfd \
		--device=/dev/dri --group-add video "$image" sh -c \
		"apt-get update \
      && apt-get install -y software-properties-common \
      && add-apt-repository ppa:deadsnakes/ppa \
      && apt-get update \
      && apt-get install -y python3.9-dev python3-pip \
      && pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/rocm6.1/ \
      && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends cmake \
      && pip install -r requirements-ci.txt \
      && cmake -DCOMPUTE_BACKEND=hip . \
      && cmake --build . \
      && echo \"Running Unittests...\" \
      && pytest --log-cli-level=DEBUG --continue-on-collection-errors tests"
fi

#output_dir="output/${build_os}/${build_arch}"
#mkdir -p "${output_dir}"
#(shopt -s nullglob && cp bitsandbytes/*.{so,dylib,dll} "${output_dir}")
