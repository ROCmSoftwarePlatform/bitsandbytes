#!/bin/bash
declare build_arch
declare build_os

set -xeuo pipefail
if [ "${build_os:0:6}" == ubuntu ]; then
	image=rocm/pytorch:latest
	echo "Using image $image"
	docker run --platform "linux/$build_arch" -i -w /src -v "$PWD:/src" "$image" sh -c \
		"apt-get update \
      && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends cmake \
      && cmake -DCOMPUTE_BACKEND=hip . \
      && cmake --build ."
fi

pytest --log-cli-level=DEBUG --continue-on-collection-errors tests

output_dir="output/${build_os}/${build_arch}"
mkdir -p "${output_dir}"
(shopt -s nullglob && cp bitsandbytes/*.{so,dylib,dll} "${output_dir}")
