"""CuPy GPU acceptance with synchronized timings and CPU references."""
import json
from pathlib import Path
import time
import numpy as np
import cupy as cp
import cupyx.scipy.sparse as sparse
from cupyx.scipy.sparse.linalg import spsolve

device = cp.cuda.Device(0)
properties = cp.cuda.runtime.getDeviceProperties(0)
checks, metrics = [], {}


def check(name, passed, **details):
    checks.append({"name": name, "passed": bool(passed), **details})


rng = np.random.default_rng(314159)
a, b = rng.normal(size=(128,128)), rng.normal(size=(128,128))
start = time.perf_counter()
ga, gb = cp.asarray(a), cp.asarray(b)
device.synchronize()
metrics["host_to_device_seconds"] = time.perf_counter()-start
ga @ gb  # Warmup is excluded from the measured operation.
device.synchronize()
start = time.perf_counter()
product = ga @ gb
device.synchronize()
metrics["matmul_seconds"] = time.perf_counter()-start
check("device_array", isinstance(product, cp.ndarray) and product.device.id == device.id)
check("float64_matmul", np.allclose(cp.asnumpy(product), a@b, rtol=1e-10, atol=1e-12), rtol=1e-10, atol=1e-12)
signal = cp.asarray(rng.normal(size=4096))
transformed = cp.fft.fft(signal, norm="ortho")
restored = cp.fft.ifft(transformed, norm="ortho")
fft_error = float(cp.linalg.norm(restored-signal)/cp.linalg.norm(signal))
check("orthonormal_fft_roundtrip", fft_error < 1e-10, relative_error=fft_error)
n = 256
matrix = sparse.diags([-cp.ones(n-1), 2*cp.ones(n), -cp.ones(n-1)], [-1,0,1], shape=(n,n), format="csr")
truth = cp.sin(cp.arange(1,n+1,dtype=cp.float64))
rhs = matrix@truth
answer = spsolve(matrix, rhs)
error = float(cp.linalg.norm(answer-truth)/cp.linalg.norm(truth))
residual = float(cp.linalg.norm(matrix@answer-rhs)/cp.linalg.norm(rhs))
check("sparse_solution", isinstance(answer, cp.ndarray) and error < 1e-7 and residual < 1e-9, relative_error=error, relative_residual=residual)
metrics.update(device_name=properties["name"].decode() if isinstance(properties["name"], bytes) else properties["name"], device_ordinal=0, compute_capability=f"{properties['major']}.{properties['minor']}", driver_version=cp.cuda.runtime.driverGetVersion(), runtime_version=cp.cuda.runtime.runtimeGetVersion(), precision="float64", fft_normalization="ortho", sparse_analytic_condition_2=float((1+np.cos(np.pi/(n+1)))/(1-np.cos(np.pi/(n+1)))), pool_peak_observation_bytes=cp.get_default_memory_pool().total_bytes())
Path("/output/experiment.json").write_text(json.dumps({"checks": checks, "metrics": metrics, "limitations": ["Observed CuPy pool allocation is not a process-wide peak or hard VRAM limit. Timings are illustrative, not a speedup claim."]}, indent=2)+"\n")
raise SystemExit(0 if all(c["passed"] for c in checks) else 1)
