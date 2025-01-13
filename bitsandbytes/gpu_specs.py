import dataclasses
import logging
import re
import subprocess
from typing import Optional, Tuple, Union

import torch


@dataclasses.dataclass(frozen=True)
class GPUSpecs:
    gpu_backend: str
    highest_compute_capability: Tuple[int, int]
    backend_version_string: str
    backend_version_tuple: Tuple[int, int]

    @property
    def enable_blaslt(self) -> bool:
        if torch.version.hip:
            return self.highest_compute_capability >= (6, 1)
        else:
            return self.highest_compute_capability >= (7, 5)


def get_gpu_backend() -> str:
    if torch.version.hip:
        return "rocm"
    else:
        return "cuda"


def get_compute_capabilities() -> Tuple[int, int]:
    if torch.version.hip:
        hip_major, hip_minor = get_backend_version_tuple()
        return (hip_major, hip_minor)
    else:
        return sorted(
            torch.cuda.get_device_capability(torch.cuda.device(i)) for i in range(torch.cuda.device_count())
        )[-1]


def get_backend_version_tuple() -> Tuple[int, int]:
    # https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART____VERSION.html#group__CUDART____VERSION
    if torch.version.cuda:
        major, minor = map(int, torch.version.cuda.split("."))
    elif torch.version.hip:
        major, minor = map(int, torch.version.hip.split(".")[0:2])
    return major, minor


def get_backend_version_string() -> str:
    major, minor = get_backend_version_tuple()
    return f"{major}{minor}"


def get_gpu_specs() -> Optional[GPUSpecs]:
    if not torch.cuda.is_available():
        return None

    return GPUSpecs(
        gpu_backend=get_gpu_backend(),
        highest_compute_capability=(get_compute_capabilities()),
        backend_version_string=(get_backend_version_string()),
        backend_version_tuple=get_backend_version_tuple(),
    )


def get_rocm_gpu_arch() -> str:
    logger = logging.getLogger(__name__)
    try:
        if torch.version.hip:
            result = subprocess.run(["rocminfo"], capture_output=True, text=True)
            match = re.search(r"Name:\s+gfx([a-zA-Z\d]+)", result.stdout)
            if match:
                return "gfx" + match.group(1)
            else:
                return "unknown"
        else:
            return "unknown"
    except Exception as e:
        logger.error(f"Could not detect ROCm GPU architecture: {e}")
        if torch.cuda.is_available():
            logger.warning(
                """
ROCm GPU architecture detection failed despite ROCm being available.
                """,
            )
        return "unknown"
