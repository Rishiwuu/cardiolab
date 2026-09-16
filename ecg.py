"""Pseudo-ECG simulator module for the CardioLab platform.

This module implements an educational biophysical approximation of an extracellular
pseudo-ECG using a transmural action potential difference model (two-cell dipole
approximation). It constructs a virtual epicardial action potential from the simulated
endocardial potential, computes their difference representing the transmural voltage
gradient, and produces an ECG-like waveform for educational visualization of
depolarization and repolarization timing.

Scientific Assumptions & Disclaimers:
1. This is a simplified 1D/two-cell dipole approximation representing the electrical
   gradient across the ventricular wall. It does NOT model volume conduction, electrode
   geometry, or torso inhomogeneities required for a clinical surface ECG (e.g., Lead II).
   It is designed for educational and conceptual visualization of APD prolongation and
   shortening effects, NOT for clinical diagnostic use.
2. The P-wave (atrial activity) is not represented because the underlying simulation uses a
   ventricular myocyte model (Beeler-Reuter 1977).
3. The RR interval and Heart Rate are derived from the pacing protocol of the simulation rather
   than autonomous physiological sinus pacing.
"""

from typing import Dict, List, Tuple, Union
import numpy as np


def generate_pseudo_ecg(
    time: Union[List[float], np.ndarray],
    voltage: Union[List[float], np.ndarray],
    ap_features: Dict[str, float],
    transmural_delay: float = 20.0,
    epicardial_compression: float = 1.15
) -> Tuple[np.ndarray, np.ndarray]:
    """Generates an educational pseudo-ECG signal from a single action potential.

    Constructs a virtual epicardial action potential (V_epi) by shifting the endocardial
    action potential (V_endo) in time (representing transmural conduction delay) and compressing
    the repolarization phase (representing the shorter action potential duration typical of
    epicardial cells). The pseudo-ECG is calculated as V_endo - V_epi and normalized.

    Args:
        time: List or numpy array of simulation time steps (ms).
        voltage: List or numpy array of simulated membrane potentials (V_endo, mV).
        ap_features: Extracted features from features.py, containing:
            - 'depolarization_time': The onset of the action potential (ms).
            - 'resting_potential': The baseline membrane potential (mV).
        transmural_delay: Time delay for epicardial depolarization wavefront arrival (default 20.0 ms).
        epicardial_compression: Factor to compress epicardial repolarization phase,
            representing shorter APD (default 1.15).

    Returns:
        A tuple of:
            - ecg_time: Numpy array of time steps (ms) matching input time.
            - ecg_signal: Numpy array of the normalized pseudo-ECG potential (mV).
    """
    time_arr = np.asarray(time, dtype=float)
    v_endo = np.asarray(voltage, dtype=float)

    v_rest = ap_features.get("resting_potential", -84.6)
    t_dep = ap_features.get("depolarization_time", 100.0)

    # Reconstruct virtual epicardial action potential (V_epi)
    v_epi = []
    for t in time_arr:
        if t < t_dep + transmural_delay:
            # Epicardium remains at rest before the depolarization wave propagates to it
            v_epi.append(v_rest)
        else:
            # Compress the time axis post-depolarization to simulate faster epicardial repolarization
            tau = t_dep + (t - t_dep - transmural_delay) * epicardial_compression
            v_epi.append(float(np.interp(tau, time_arr, v_endo)))

    v_epi_arr = np.array(v_epi)

    # Compute raw transmural voltage gradient (extracellular potential difference)
    # ECG = V_endo - V_epi
    ecg_raw = v_endo - v_epi_arr

    # Normalize to make the R-wave peak exactly 1.0 mV
    max_val = np.max(np.abs(ecg_raw))
    if max_val > 0:
        ecg_signal = ecg_raw / max_val
    else:
        ecg_signal = ecg_raw

    return time_arr, ecg_signal


def estimate_rr_interval(pacing_period: float) -> float:
    """Estimates the RR interval from the cell pacing period.

    Since single-cell model pacing is driven externally by the stimulus protocol, the nominal
    time between heartbeats (RR interval) is equivalent to the pacing stimulus period.

    Args:
        pacing_period: Pacing period of the simulation protocol in ms.

    Returns:
        The estimated RR interval in milliseconds.
    """
    return pacing_period


def calculate_heart_rate(rr_interval: float) -> float:
    """Calculates the nominal Heart Rate in beats per minute (bpm).

    Args:
        rr_interval: RR interval in milliseconds.

    Returns:
        Heart rate (bpm).
    """
    if rr_interval <= 0:
        return 0.0
    return 60000.0 / rr_interval
