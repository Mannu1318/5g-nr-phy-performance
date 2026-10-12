"""Cross-validate the C ZF implementation against the Python reference."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest

from kernels.kernel6_mimo.mimo_zf_reference import (
    NEAR_SINGULAR_CHANNEL,
    NONFINITE_INPUT,
    OK,
    SINGULAR_CHANNEL,
    zf_detect_single,
)

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests/kernel6_mimo/zf_cross_validation"

STATUS_CODES = {
    0: OK,
    1: "INVALID_SHAPE",
    2: NONFINITE_INPUT,
    3: SINGULAR_CHANNEL,
    4: NEAR_SINGULAR_CHANNEL,
    5: "NUMERICAL_FAILURE",
}


@pytest.fixture(scope="module", autouse=True)
def build_c_harness() -> None:
    """Compile the C harness before running cross-validation."""
    subprocess.run(
        [
            "gcc",
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            str(ROOT / "kernels/kernel6_mimo"),
            str(ROOT / "tests/kernel6_mimo/zf_cross_validation.c"),
            str(ROOT / "kernels/kernel6_mimo/mimo_zf_scalar.c"),
            "-lm",
            "-o",
            str(HARNESS),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("H", "y"),
    [
        (
            [[1, 0], [0, 1]],
            [0.75 + 0.5j, -1 + 0.25j],
        ),
        (
            [[2, 0], [0, 4]],
            [1 + 2j, -4 + 1j],
        ),
        (
            [[2 + 1j, 1 - 1j], [0.5 + 0.5j, 3 - 1j]],
            [1 + 2j, -0.5 + 1j],
        ),
        (
            [[1e-100, 0], [0, 1e-100]],
            [1e-100 * (0.75 + 0.5j), 1e-100 * (-1 + 0.25j)],
        ),
        (
            [[1e100, 0], [0, 1e100]],
            [1e100 * (0.75 + 0.5j), 1e100 * (-1 + 0.25j)],
        ),
        (
            [[0, 0], [0, 0]],
            [1 + 0j, 2 + 0j],
        ),
        (
            [[1, 1], [1, 1 + 1e-14]],
            [1 + 0j, 2 + 0j],
        ),
        (
            [[complex(float("inf"), 0), 0], [0, 1]],
            [1 + 0j, 2 + 0j],
        ),
    ],
    ids=[
        "identity",
        "diagonal",
        "complex-nondiagonal",
        "small-scale",
        "large-scale",
        "zero-channel",
        "near-singular",
        "nonfinite-input",
    ],
)
def test_c_matches_python(H: list, y: list) -> None:
    """Compare C and Python statuses and estimates for the same inputs."""
    channel = np.asarray(H, dtype=np.complex128)
    received = np.asarray(y, dtype=np.complex128)

    expected, expected_status = zf_detect_single(channel, received)

    values: list[float] = []
    for value in channel.flat:
        values.extend([float(value.real), float(value.imag)])
    for value in received:
        values.extend([float(value.real), float(value.imag)])

    input_text = "1\n" + " ".join(map(str, values)) + "\n"

    result = subprocess.run(
        [str(HARNESS)],
        input=input_text,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    fields = result.stdout.split()
    assert len(fields) == 5, result.stdout

    c_status_code = int(fields[0])
    assert c_status_code in STATUS_CODES
    assert STATUS_CODES[c_status_code] == expected_status

    actual = np.asarray(
        [
            complex(float(fields[1]), float(fields[2])),
            complex(float(fields[3]), float(fields[4])),
        ],
        dtype=np.complex128,
    )

    if expected_status == OK:
        np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-12)
    else:
        assert np.all(np.isnan(actual.real))
        assert np.all(np.isnan(actual.imag))
