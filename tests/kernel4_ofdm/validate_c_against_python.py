
"""Cross-validate the Kernel 4 C FFT/IFFT against NumPy."""

import ctypes
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from kernels.kernel4_ofdm.ofdm_reference import fft, ifft

LIBRARY_PATH = Path("/tmp/libofdm.so")
FFT_SIZES = (64, 128, 256, 512, 1024, 2048)
TOLERANCE = 1e-9


class OfdmSample(ctypes.Structure):
    """C structure containing a double-precision complex sample."""

    _fields_ = [
        ("real", ctypes.c_double),
        ("imag", ctypes.c_double),
    ]


SamplePointer = ctypes.POINTER(OfdmSample)


def load_library():
    """Load the C library and declare function interfaces."""
    if not LIBRARY_PATH.exists():
        raise FileNotFoundError(
            f"{LIBRARY_PATH} not found. Compile the C shared library first."
        )

    library = ctypes.CDLL(str(LIBRARY_PATH))

    library.ofdm_fft.argtypes = [
        SamplePointer,
        SamplePointer,
        ctypes.c_size_t,
    ]
    library.ofdm_fft.restype = ctypes.c_int

    library.ofdm_ifft.argtypes = [
        SamplePointer,
        SamplePointer,
        ctypes.c_size_t,
    ]
    library.ofdm_ifft.restype = ctypes.c_int

    return library


def to_c_samples(values):
    """Convert a NumPy complex array into an array of C structures."""
    values = np.ascontiguousarray(values, dtype=np.complex128)
    samples = (OfdmSample * len(values))()

    for i, value in enumerate(values):
        samples[i].real = value.real
        samples[i].imag = value.imag

    return samples


def from_c_samples(samples):
    """Convert C structures back into a NumPy complex array."""
    return np.array(
        [sample.real + 1j * sample.imag for sample in samples],
        dtype=np.complex128,
    )


def run_transform(library, function_name, values):
    """Run one C transform and return its complex output."""
    values = np.ascontiguousarray(values, dtype=np.complex128)
    c_input = to_c_samples(values)
    c_output = (OfdmSample * len(values))()

    function = getattr(library, function_name)
    status = function(c_input, c_output, len(values))

    if status != 0:
        raise RuntimeError(
            f"{function_name} failed with status {status}"
        )

    return from_c_samples(c_output)


def main():
    library = load_library()
    rng = np.random.default_rng(seed=20261009)

    print("Kernel 4: C versus NumPy cross-validation")
    print(f"Tolerance: {TOLERANCE:.1e}\n")

    failures = 0

    for n in FFT_SIZES:
        # Deterministic complex-valued time-domain input.
        time_samples = (
            rng.standard_normal(n) + 1j * rng.standard_normal(n)
        )

        c_fft = run_transform(library, "ofdm_fft", time_samples)
        python_fft = fft(time_samples)
        fft_error = float(np.max(np.abs(c_fft - python_fft)))

        # Independently compare IFFT for frequency-domain input.
        frequency_samples = (
            rng.standard_normal(n) + 1j * rng.standard_normal(n)
        )

        c_ifft = run_transform(
            library, "ofdm_ifft", frequency_samples
        )
        python_ifft = ifft(frequency_samples)
        ifft_error = float(np.max(np.abs(c_ifft - python_ifft)))

        fft_ok = fft_error < TOLERANCE
        ifft_ok = ifft_error < TOLERANCE
        passed = fft_ok and ifft_ok

        print(
            f"N={n:4d} | "
            f"FFT max error={fft_error:.3e} | "
            f"IFFT max error={ifft_error:.3e} | "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            failures += 1

    print(
        f"\nResults: {len(FFT_SIZES) - failures} of "
        f"{len(FFT_SIZES)} FFT-size groups passed."
    )

    if failures:
        raise SystemExit(1)

    print("C FFT and IFFT match the NumPy reference within tolerance.")


if __name__ == "__main__":
    main()
