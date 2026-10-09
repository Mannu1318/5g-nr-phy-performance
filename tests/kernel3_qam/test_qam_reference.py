"""
Automated correctness tests for Kernel 3
5G NR QAM Mapping and Demapping.
"""

import random

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


def test_qpsk_all_patterns():
    """Test all four possible QPSK input patterns."""

    bits = [
        0, 0,
        0, 1,
        1, 0,
        1, 1,
    ]

    symbols = qpsk_map(bits)
    recovered_bits = qpsk_demap(symbols)

    assert recovered_bits == bits


def test_qam16_all_patterns():
    """Test all sixteen possible 16-QAM input patterns."""

    bits = []

    for value in range(16):
        bits.extend([
            (value >> 3) & 1,
            (value >> 2) & 1,
            (value >> 1) & 1,
            value & 1,
        ])

    symbols = qam16_map(bits)
    recovered_bits = qam16_demap(symbols)

    assert recovered_bits == bits


def test_qpsk_random():
    """Test QPSK with random input data."""

    random.seed(1)

    bits = [random.randint(0, 1) for _ in range(1000)]

    symbols = qpsk_map(bits)
    recovered_bits = qpsk_demap(symbols)

    assert recovered_bits == bits


def test_qam16_random():
    """Test 16-QAM with random input data."""

    random.seed(2)

    bits = [random.randint(0, 1) for _ in range(1000)]

    symbols = qam16_map(bits)
    recovered_bits = qam16_demap(symbols)

    assert recovered_bits == bits


def test_qpsk_invalid_length():
    """QPSK must receive an even number of bits."""

    bits = [0, 1, 0]

    try:
        qpsk_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_qam16_invalid_length():
    """16-QAM must receive a multiple of four bits."""

    bits = [0, 1, 0]

    try:
        qam16_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_qpsk_invalid_bit():
    """QPSK must reject values other than 0 and 1."""

    bits = [0, 1, 2, 0]

    try:
        qpsk_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_qam16_invalid_bit():
    """16-QAM must reject values other than 0 and 1."""

    bits = [0, 1, 0, 3]

    try:
        qam16_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
def test_qam64_all_patterns():
    bits = []

    for value in range(64):
        bits.extend([
            (value >> 5) & 1,
            (value >> 4) & 1,
            (value >> 3) & 1,
            (value >> 2) & 1,
            (value >> 1) & 1,
            value & 1,
        ])

    symbols = qam64_map(bits)
    recovered_bits = qam64_demap(symbols)

    assert recovered_bits == bits
def test_qam64_random():
    random.seed(3)

    bits = [random.randint(0, 1) for _ in range(6000)]

    symbols = qam64_map(bits)
    recovered_bits = qam64_demap(symbols)

    assert recovered_bits == bits
def test_qam64_invalid_length():
    bits = [0, 1, 0, 1, 0]

    try:
        qam64_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
def test_qam64_invalid_bit():
    bits = [0, 1, 0, 1, 0, 2]

    try:
        qam64_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

def test_qam256_random():
    random.seed(4)

    bits = [random.randint(0, 1) for _ in range(8000)]

    symbols = qam256_map(bits)
    recovered_bits = qam256_demap(symbols)

    assert recovered_bits == bits
def test_qam256_invalid_length():
    bits = [0, 1, 0, 1, 0, 1, 0]

    try:
        qam256_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_qam256_invalid_bit():
    bits = [0, 1, 0, 1, 0, 1, 0, 2]

    try:
        qam256_map(bits)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

def test_qam16_boundary_values():
    normalization = 1.0 / (10.0 ** 0.5)
    epsilon = 1e-6

    test_values = [
        -2 - epsilon,
        -2 + epsilon,
        -epsilon,
        epsilon,
        2 - epsilon,
        2 + epsilon,
    ]

    symbols = [
        complex(value * normalization, 0)
        for value in test_values
    ]

    bits = qam16_demap(symbols)

    expected_i_bits = [
        [1, 0],  # below -2
        [1, 1],  # above -2
        [1, 1],  # below 0
        [0, 1],  # above 0
        [0, 1],  # below 2
        [0, 0],  # above 2
    ]

    expected_q_bits = [0, 1]

    expected_bits = []

    for i_bits in expected_i_bits:
        expected_bits.extend([
            i_bits[0],
            expected_q_bits[0],
            i_bits[1],
            expected_q_bits[1],
        ])

    assert bits == expected_bits

def test_qam64_boundary_values():
    normalization = 1.0 / (42.0 ** 0.5)
    epsilon = 1e-6

    boundaries = [-6, -4, -2, 0, 2, 4, 6]

    symbols = []

    for boundary in boundaries:
        symbols.append(
            complex((boundary - epsilon) * normalization, 0)
        )
        symbols.append(
            complex((boundary + epsilon) * normalization, 0)
        )

    bits = qam64_demap(symbols)

    expected_i_bits = [
        [1, 0, 0],   # below -6
        [1, 0, 1],   # above -6

        [1, 0, 1],   # below -4
        [1, 1, 0],   # above -4

        [1, 1, 0],   # below -2
        [1, 1, 1],   # above -2

        [1, 1, 1],   # below 0
        [0, 1, 1],   # above 0

        [0, 1, 1],   # below 2
        [0, 1, 0],   # above 2

        [0, 1, 0],   # below 4
        [0, 0, 1],   # above 4

        [0, 0, 1],   # below 6
        [0, 0, 0],   # above 6
    ]

    q_bits = [0, 1, 1]

    expected_bits = []

    for i_bits in expected_i_bits:
        expected_bits.extend([
            i_bits[0], q_bits[0],
            i_bits[1], q_bits[1],
            i_bits[2], q_bits[2],
        ])

    assert bits == expected_bits

def test_qam256_boundary_values():
    normalization = 1.0 / (170.0 ** 0.5)

    symbols = [
        complex(-14 * normalization, 0),
        complex(-12 * normalization, 0),
        complex(-10 * normalization, 0),
        complex(-8 * normalization, 0),
        complex(-6 * normalization, 0),
        complex(-4 * normalization, 0),
        complex(-2 * normalization, 0),
        complex(0, 0),
        complex(2 * normalization, 0),
        complex(4 * normalization, 0),
        complex(6 * normalization, 0),
        complex(8 * normalization, 0),
        complex(10 * normalization, 0),
        complex(12 * normalization, 0),
        complex(14 * normalization, 0),
    ]

    bits = qam256_demap(symbols)

    expected_i_bits = [
        [1, 0, 0, 1],
        [1, 0, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 0],
        [1, 1, 0, 1],
        [1, 1, 1, 0],
        [1, 1, 1, 1],
        [0, 1, 1, 1],
        [0, 1, 1, 0],
        [0, 1, 0, 1],
        [0, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [0, 0, 0, 0],
    ]

    q_bits = [0, 1, 1, 1]

    expected_bits = []

    for i_bits in expected_i_bits:
        expected_bits.extend([
            i_bits[0], q_bits[0],
            i_bits[1], q_bits[1],
            i_bits[2], q_bits[2],
            i_bits[3], q_bits[3],
        ])

    assert bits == expected_bits
