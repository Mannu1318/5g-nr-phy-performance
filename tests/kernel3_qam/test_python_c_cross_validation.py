import subprocess
from pathlib import Path

import pytest

from kernels.kernel3_qam.qam_reference import (
    qpsk_map,
    qpsk_demap,
    qam16_map,
    qam16_demap,
    qam64_map,
    qam64_demap,
    qam256_map,
    qam256_demap,
)


ROOT = Path(__file__).resolve().parents[2]

C_TEST = (
    ROOT
    / "tests"
    / "kernel3_qam"
    / "test_qam_cross_validation"
)


MODULATIONS = [
    ("qpsk", 2, qpsk_map, qpsk_demap),
    ("qam16", 4, qam16_map, qam16_demap),
    ("qam64", 6, qam64_map, qam64_demap),
    ("qam256", 8, qam256_map, qam256_demap),
]


def generate_bits(bits_per_symbol, n_symbols=16):
    n_bits = bits_per_symbol * n_symbols

    return [
        (i * 7 + 3) % 2
        for i in range(n_bits)
    ]


def run_c_test(modulation):
    result = subprocess.run(
        [str(C_TEST), modulation],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout


def parse_c_output(output):
    lines = output.strip().splitlines()

    assert lines[0] == "SYMBOLS"

    bits_index = lines.index("BITS")

    symbol_lines = lines[1:bits_index]
    recovered_bits = lines[bits_index + 1].strip()

    symbols = []

    for line in symbol_lines:
        real, imag = map(float, line.split())
        symbols.append(complex(real, imag))

    bits = [int(bit) for bit in recovered_bits]

    return symbols, bits


@pytest.mark.parametrize(
    "modulation,bits_per_symbol,python_map,python_demap",
    MODULATIONS,
)
def test_python_c_cross_validation(
    modulation,
    bits_per_symbol,
    python_map,
    python_demap,
):
    bits = generate_bits(bits_per_symbol)

    # Python reference mapping.
    python_symbols = python_map(bits)

    # Run the C implementation.
    c_output = run_c_test(modulation)

    c_symbols, c_recovered_bits = parse_c_output(
        c_output
    )

    # ---------------------------------------------------------
    # 1. Compare Python mapper against C mapper.
    # ---------------------------------------------------------

    assert len(python_symbols) == len(c_symbols)

    for python_symbol, c_symbol in zip(
        python_symbols,
        c_symbols,
    ):
        assert c_symbol.real == pytest.approx(
            python_symbol.real,
            abs=1e-6,
        )

        assert c_symbol.imag == pytest.approx(
            python_symbol.imag,
            abs=1e-6,
        )

    # ---------------------------------------------------------
    # 2. Verify C demapper recovered the original bits.
    # ---------------------------------------------------------

    assert c_recovered_bits == bits

    # ---------------------------------------------------------
    # 3. Verify Python demapper also recovers the bits.
    # ---------------------------------------------------------

    python_recovered_bits = python_demap(
        python_symbols
    )

    assert python_recovered_bits == bits

    # ---------------------------------------------------------
    # 4. Cross-check Python demapper against C demapper.
    # ---------------------------------------------------------

    assert python_recovered_bits == c_recovered_bits
