"""Feature extraction module for the CardioLab platform.

This module processes raw membrane potential trajectories to extract key physiological
biomarkers (e.g., APD90, APD50, resting membrane potential, and upstroke velocity)
which serve as inputs for ECG generation and clinical interpretation.
"""

from typing import Dict, List, Union
import numpy as np


def extract_ap_features(
    time: Union[List[float], np.ndarray],
    voltage: Union[List[float], np.ndarray],
    threshold_pct: float = 0.90
) -> Dict[str, float]:
    """Analyzes a membrane potential trajectory and extracts electrophysiological biomarkers.

    Args:
        time: List or numpy array of time steps (ms).
        voltage: List or numpy array of membrane potentials (mV).
        threshold_pct: Percentage threshold for primary APD calculation (default 0.90).

    Returns:
        A dictionary containing the following extracted features:
            - "resting_potential": The baseline resting membrane potential (mV).
            - "peak_voltage": The peak overshoot potential during depolarization (mV).
            - "amplitude": The action potential amplitude (APA, mV).
            - "max_upstroke_velocity": The maximum rate of rise of voltage (dV/dt_max, mV/ms).
            - "depolarization_time": The time of maximum rate of rise (ms).
            - "apd90": The Action Potential Duration at 90% repolarization (ms).
            - "apd50": The Action Potential Duration at 50% repolarization (ms).
    """
    time_arr = np.asarray(time, dtype=float)
    voltage_arr = np.asarray(voltage, dtype=float)

    if len(time_arr) < 2 or len(voltage_arr) < 2:
        return {
            "resting_potential": 0.0,
            "peak_voltage": 0.0,
            "amplitude": 0.0,
            "max_upstroke_velocity": 0.0,
            "depolarization_time": 0.0,
            "apd90": 0.0,
            "apd50": 0.0
        }

    # Resting Potential is defined as the starting baseline potential (under BR77 conditions,
    # before stimulus triggers at 100 ms) or the minimum recorded potential.
    v_rest = float(voltage_arr[0])
    v_max = float(np.max(voltage_arr))
    amplitude = v_max - v_rest

    # Calculate first derivative dV/dt to find upstroke characteristics
    dt = np.diff(time_arr)
    dv = np.diff(voltage_arr)
    
    # Avoid division by zero in case of duplicate time steps
    dt_safe = np.where(dt == 0, 1e-9, dt)
    dv_dt = dv / dt_safe

    max_dv_dt_idx = int(np.argmax(dv_dt))
    max_upstroke_velocity = float(dv_dt[max_dv_dt_idx])
    depolarization_time = float(time_arr[max_dv_dt_idx])

    # Sub-function to calculate Action Potential Duration at a given percentage (e.g., 90% or 50%)
    def calculate_apd(pct: float) -> float:
        # Repolarization target potential (e.g. for APD90, it is V_rest + 10% of amplitude)
        v_thresh = v_rest + (1.0 - pct) * amplitude
        
        # Upstroke crossing index (where membrane potential crosses threshold from below)
        upstroke_indices = np.where((voltage_arr >= v_thresh) & (time_arr >= depolarization_time - 5.0))[0]
        if len(upstroke_indices) == 0:
            return 0.0
        idx_up = upstroke_indices[0]
        t_up = time_arr[idx_up]

        # Repolarization crossing index (where potential crosses back below threshold after upstroke)
        repol_indices = np.where((voltage_arr[idx_up:] < v_thresh))[0]
        if len(repol_indices) == 0:
            # If cell doesn't fully repolarize within the simulation window, estimate APD
            # by using the end of the simulation.
            return float(time_arr[-1] - t_up)
        
        idx_down = idx_up + repol_indices[0]
        t_down = time_arr[idx_down]
        return float(t_down - t_up)

    apd90 = calculate_apd(0.90)
    apd50 = calculate_apd(0.50)

    # If primary requested threshold differs from 90% or 50%
    custom_key = f"apd{int(threshold_pct*100)}"
    custom_apd = calculate_apd(threshold_pct)

    features = {
        "resting_potential": v_rest,
        "peak_voltage": v_max,
        "amplitude": amplitude,
        "max_upstroke_velocity": max_upstroke_velocity,
        "depolarization_time": depolarization_time,
        "apd90": apd90,
        "apd50": apd50
    }

    if custom_key not in ["apd90", "apd50"]:
        features[custom_key] = custom_apd

    return features
