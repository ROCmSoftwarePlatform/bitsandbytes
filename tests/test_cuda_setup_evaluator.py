import pytest

from bitsandbytes.cextension import HIP_ENVIRONMENT, get_gpu_bnb_library_path
from bitsandbytes.gpu_specs import GPUSpecs


@pytest.fixture
def cuda120_spec() -> GPUSpecs:
    return GPUSpecs(
        backend_version_string="120",
        highest_compute_capability=(8, 6),
        backend_version_tuple=(12, 0),
    )


@pytest.fixture
def cuda111_noblas_spec() -> GPUSpecs:
    return GPUSpecs(
        backend_version_string="111",
        highest_compute_capability=(7, 2),
        backend_version_tuple=(11, 1),
    )


@pytest.mark.skipif(HIP_ENVIRONMENT, reason="this test is not supported on ROCm")
def test_get_gpu_bnb_library_path(monkeypatch, cuda120_spec):
    monkeypatch.delenv("BNB_CUDA_VERSION", raising=False)
    assert get_gpu_bnb_library_path(cuda120_spec).stem == "libbitsandbytes_cuda120"


@pytest.mark.skipif(HIP_ENVIRONMENT, reason="this test is not supported on ROCm")
def test_get_gpu_bnb_library_path_override(monkeypatch, cuda120_spec, caplog):
    monkeypatch.setenv("BNB_CUDA_VERSION", "110")
    assert get_gpu_bnb_library_path(cuda120_spec).stem == "libbitsandbytes_cuda110"
    assert "BNB_CUDA_VERSION" in caplog.text  # did we get the warning?


@pytest.mark.skipif(HIP_ENVIRONMENT, reason="this test is not supported on ROCm")
def test_get_gpu_bnb_library_path_nocublaslt(monkeypatch, cuda111_noblas_spec):
    monkeypatch.delenv("BNB_CUDA_VERSION", raising=False)
    assert get_gpu_bnb_library_path(cuda111_noblas_spec).stem == "libbitsandbytes_cuda111_nocublaslt"
