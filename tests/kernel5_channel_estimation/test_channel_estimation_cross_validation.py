import ctypes
import subprocess
from pathlib import Path

import numpy as np
import pytest

from kernels.kernel5_channel_estimation.channel_estimation_reference import (
    estimate_channel,
)


class ChannelSample(ctypes.Structure):
    _fields_ = [
        ("real", ctypes.c_double),
        ("imag", ctypes.c_double),
    ]


@pytest.fixture(scope="module")
def c_estimator(tmp_path_factory):
    """Compile the C implementation and expose it through ctypes."""
    root = Path(__file__).resolve().parents[2]
    build_dir = tmp_path_factory.mktemp("channel_estimation_c")
    library_path = build_dir / "libchannel_estimation.so"

    subprocess.run(
        [
            "gcc",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-std=c11",
            "-shared",
            "-fPIC",
            f"-I{root / 'kernels/kernel5_channel_estimation/include'}",
            str(
                root
                / "kernels/kernel5_channel_estimation/src/channel_estimation.c"
            ),
            "-lm",
            "-o",
            str(library_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    library = ctypes.CDLL(str(library_path))
    function = library.estimate_channel

    sample_pointer = ctypes.POINTER(ChannelSample)
    index_pointer = ctypes.POINTER(ctypes.c_size_t)

    function.argtypes = [
        sample_pointer,
        sample_pointer,
        index_pointer,
        ctypes.c_size_t,
        index_pointer,
        ctypes.c_size_t,
        sample_pointer,
    ]
    function.restype = ctypes.c_int

    def call_c(pilot_symbols, received_pilots, pilot_indices, estimate_indices):
        pilot_symbols = np.asarray(pilot_symbols, dtype=np.complex128)
        received_pilots = np.asarray(received_pilots, dtype=np.complex128)

        c_pilots = (ChannelSample * len(pilot_symbols))(
            *(ChannelSample(float(z.real), float(z.imag)) for z in pilot_symbols)
        )
        c_received = (ChannelSample * len(received_pilots))(
            *(ChannelSample(float(z.real), float(z.imag)) for z in received_pilots)
        )
        c_pilot_indices = (ctypes.c_size_t * len(pilot_indices))(
            *pilot_indices
        )
        c_estimate_indices = (ctypes.c_size_t * len(estimate_indices))(
            *estimate_indices
        )
        c_output = (ChannelSample * len(estimate_indices))()

        status = function(
            c_pilots,
            c_received,
            c_pilot_indices,
            len(pilot_indices),
            c_estimate_indices,
            len(estimate_indices),
            c_output,
        )

        assert status == 0, f"C estimator returned status {status}"

        return np.array(
            [sample.real + 1j * sample.imag for sample in c_output],
            dtype=np.complex128,
        )

    return call_c


@pytest.mark.parametrize(
    "pilot_symbols,received_pilots,pilot_indices,estimate_indices",
    [
        (
            [1 + 0j, 1 + 0j],
            [2 + 3j, 2 + 3j],
            [0, 4],
            [0, 1, 2, 3, 4],
        ),
        (
            [1 + 1j, 2 - 1j, 0.5 + 0.25j],
            [
                (1 + 1j) * (0.5 + 0.25j),
                (2 - 1j) * (1.2 - 0.4j),
                (0.5 + 0.25j) * (-0.2 + 0.8j),
            ],
            [2, 6, 10],
            [2, 3, 5, 6, 9, 10],
        ),
        (
            [1 - 2j, 0.5 + 1.5j],
            [(1 - 2j) * (0.3 + 0.7j), (0.5 + 1.5j) * (-1.1 + 0.2j)],
            [3, 9],
            [9, 4, 6, 3],
        ),
    ],
    ids=[
        "constant-channel",
        "complex-pilots-and-interpolation",
        "requested-output-order",
    ],
)
def test_c_matches_python_reference(
    c_estimator,
    pilot_symbols,
    received_pilots,
    pilot_indices,
    estimate_indices,
):
    expected = estimate_channel(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
    )

    actual = c_estimator(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
    )

    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
