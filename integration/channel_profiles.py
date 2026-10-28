"""Reproducible generation of discrete-time 2x2 MIMO multipath profiles.

These educational profiles use integer-sample delays and independent,
circularly symmetric complex-Gaussian channel coefficients. They are not
intended to represent a standardized 3GPP TDL or CDL channel model.
"""

from numbers import Real
import numpy as np


def build_multipath_profile(
    delays_samples,
    tap_powers_db,
    seed,
    normalize_power=True,
):
    """Build a dense 2x2 MIMO impulse response and its metadata.

    Parameters
    ----------
    delays_samples : one-dimensional sequence of integers
        Unique, nonnegative tap delays in samples, in strictly increasing
        order. Unspecified delay positions are filled with zero matrices.
    tap_powers_db : one-dimensional sequence of real numbers
        Finite relative tap powers in dB, aligned with ``delays_samples``.
        The strongest tap has relative linear power 1 before normalization.
    seed : integer
        Nonnegative seed for a local NumPy random generator.
    normalize_power : bool
        If True, scale configured linear tap powers to sum to one.

    Returns
    -------
    channel_taps : numpy.ndarray
        Complex array with shape (max(delays_samples) + 1, 2, 2).
        Axis 0 represents delay; axes 1 and 2 represent receive and
        transmit antennas, respectively.
    metadata : dict
        Input configuration, configured linear powers, and realized
        tap energies for the specified delays.

    Notes
    -----
    Each 2x2 tap has expected squared Frobenius norm equal to its
    configured linear power. The function uses a local random generator
    and does not modify NumPy's global random state.
    """
    raw_delays = np.asarray(delays_samples, dtype=object)
    raw_powers = np.asarray(tap_powers_db, dtype=object)

    if raw_delays.ndim != 1 or raw_delays.size == 0:
        raise ValueError("delays_samples must be a nonempty 1D sequence")

    delays = []
    for value in raw_delays:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ):
            raise ValueError("delays_samples must contain integers")
        value = int(value)
        if value < 0:
            raise ValueError("delays_samples must be nonnegative")
        delays.append(value)

    if any(b <= a for a, b in zip(delays, delays[1:])):
        raise ValueError(
            "delays_samples must be unique and strictly increasing"
        )

    if raw_powers.ndim != 1 or raw_powers.size == 0:
        raise ValueError("tap_powers_db must be a nonempty 1D sequence")
    if raw_powers.size != len(delays):
        raise ValueError(
            "delays_samples and tap_powers_db must have equal lengths"
        )

    powers_db = []
    for value in raw_powers:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise ValueError("tap_powers_db must contain real numbers")
        value = float(value)
        if not np.isfinite(value):
            raise ValueError("tap_powers_db values must be finite")
        powers_db.append(value)

    if isinstance(seed, (bool, np.bool_)) or not isinstance(
        seed, (int, np.integer)
    ):
        raise ValueError("seed must be a nonnegative integer")
    seed = int(seed)
    if seed < 0:
        raise ValueError("seed must be a nonnegative integer")

    if not isinstance(normalize_power, (bool, np.bool_)):
        raise ValueError("normalize_power must be a Boolean")
    normalize_power = bool(normalize_power)

    # Express powers relative to the strongest tap. This avoids overflow
    # when converting large positive dB values directly to linear power.
    powers_db_array = np.asarray(powers_db, dtype=np.float64)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        relative_powers = np.power(
            10.0, (powers_db_array - np.max(powers_db_array)) / 10.0
        )

    if not np.all(np.isfinite(relative_powers)):
        raise ValueError("tap powers cannot be represented as linear powers")

    if normalize_power:
        configured_powers = relative_powers / np.sum(relative_powers)
    else:
        configured_powers = relative_powers.copy()

    # One dense slot per integer delay, including zero-filled delay gaps.
    channel_taps = np.zeros(
        (delays[-1] + 1, 2, 2), dtype=np.complex128
    )
    rng = np.random.default_rng(seed)

    for delay, power in zip(delays, configured_powers):
        if power == 0.0:
            continue

        real_part = rng.standard_normal((2, 2))
        imag_part = rng.standard_normal((2, 2))

        # E[||H_delay||_F^2] = power: four independent coefficients,
        # each with expected squared magnitude power / 4.
        channel_taps[delay] = (
            real_part + 1j * imag_part
        ) * np.sqrt(power / 8.0)

    realized_energies = [
        float(np.sum(np.abs(channel_taps[delay]) ** 2))
        for delay in delays
    ]

    metadata = {
        "delays_samples": list(delays),
        "tap_powers_db": list(powers_db),
        "configured_tap_powers": [
            float(power) for power in configured_powers
        ],
        "seed": seed,
        "normalize_power": normalize_power,
        "realized_tap_energies": realized_energies,
        "total_configured_power": float(np.sum(configured_powers)),
        "total_realized_energy": float(
            np.sum(np.abs(channel_taps) ** 2)
        ),
        "num_tap_slots": int(channel_taps.shape[0]),
    }

    return channel_taps, metadata
