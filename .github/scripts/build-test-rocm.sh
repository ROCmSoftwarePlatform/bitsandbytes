#!/bin/bash
declare build_arch
declare build_os

set -xeuo pipefail
if [ "${build_os:0:6}" == ubuntu ]; then
	image=rocm/pytorch:latest
	echo "Using image $image"
	docker run --platform "linux/$build_arch" -i -d -w /src --device=/dev/kfd --device=/dev/dri --group-add video --name bnb_rocm_test "$image"
        docker cp $PWD bnb_rocm_test:/src
        docker exec bnb_rocm_test sh -c \
		"apt-get update \
      && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends cmake \
      && pip install -r requirements-ci.txt \
      && cmake -DCOMPUTE_BACKEND=hip . \
      && cmake --build . \
      && pytest --log-cli-level=DEBUG --continue-on-collection-errors tests"
        docker stop --time=0 bnb_rocm_test
	docker rm bnb_rocm_test
fi

output_dir="output/${build_os}/${build_arch}"
mkdir -p "${output_dir}"
(shopt -s nullglob && cp bitsandbytes/*.{so,dylib,dll} "${output_dir}")
