"""Action Potential Duration (APD) restitution protocol for CardioLab.

This module runs cardiac cell simulations under a range of pacing cycle lengths (PCLs)
to extract the steady-state APD90 restitution curve for normal and mutated profiles.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import myokit

from CardioLab.config import MODEL_DATABASE
from CardioLab.simulation import run_simulation
from CardioLab.features import extract_ap_features


def run_restitution_protocol(
    model_name: str,
    sim_config: Dict[str, Any],
    cycle_lengths: List[float] = None,
    beats_to_steady_state: int = 5
) -> List[Tuple[float, float]]:
    """Runs a pacing rate sweep protocol to compute APD90 restitution.

    For each cycle length (PCL), the cell is paced multiple times to reach a
    near-steady state, and the APD90 of the final action potential is measured.

    Args:
        model_name: The key of the cell model in MODEL_DATABASE.
        sim_config: Configuration dictionary for the mutation.
        cycle_lengths: List of cycle lengths to test (ms). Defaults to [1000, 800, 600, 500, 400, 300, 250].
        beats_to_steady_state: Number of pacing beats to run at each rate (default 5).

    Returns:
        A list of tuples: (cycle_length, apd90) ordered from longest to shortest PCL.
    """
    if cycle_lengths is None:
        cycle_lengths = [1000.0, 800.0, 600.0, 500.0, 400.0, 300.0, 250.0]

    model_info = MODEL_DATABASE[model_name]
    if not model_info["implemented"]:
        raise ValueError(f"Model '{model_name}' is not implemented.")

    model_path = model_info["model_file"]
    if not model_path:
        raise FileNotFoundError(f"Model path error for '{model_name}'")

    results = []

    for pcl in cycle_lengths:
        # Load a fresh copy of the model for this simulation run
        model = myokit.load_model(model_path)
        
        # Build a dynamic stimulus protocol for the target cycle length
        # Start time = 100ms, duration = 2ms, period = pcl
        protocol = myokit.Protocol()
        protocol.add(myokit.ProtocolEvent(level=1.0, start=100.0, duration=2.0, period=pcl, multiplier=0))

        # Apply mutation parameters to the model if configured
        param_name = sim_config.get("parameter")
        if param_name:
            from CardioLab.config import CHANNEL_ALIASES
            resolved_channel = CHANNEL_ALIASES.get(param_name, param_name)
            if model.has_variable(resolved_channel):
                var = model.get(resolved_channel)
                op = sim_config.get("operation", "multiply")
                val = sim_config.get("value", 1.0)

                # Set new RHS expression on the model
                if var.is_constant():
                    current_rhs = float(var.rhs())
                    if op == "multiply":
                        new_rhs = current_rhs * float(val)
                    elif op == "add":
                        new_rhs = current_rhs + float(val)
                    elif op == "replace":
                        new_rhs = float(val)
                    var.set_rhs(new_rhs)
                else:
                    if op == "multiply":
                        new_rhs_str = f"({var.rhs()}) * {val}"
                    elif op == "add":
                        new_rhs_str = f"({var.rhs()}) + {val}"
                    elif op == "replace":
                        new_rhs_str = f"{val}"
                    var.set_rhs(new_rhs_str)

        # Run the multi-beat pacing simulation
        # Run until 100ms plus the time for N beats of period pcl
        sim_time = 100.0 + (beats_to_steady_state * pcl)
        sim = myokit.Simulation(model, protocol)
        log = sim.run(sim_time, log=['engine.time', 'membrane.V'])

        # Slice out the final paced beat cycle to measure its APD90 in isolation
        time_arr = np.array(log['engine.time'])
        voltage_arr = np.array(log['membrane.V'])

        # Last cycle window: from start of last stimulus to end of pacing cycle
        cycle_start = 100.0 + (beats_to_steady_state - 1) * pcl
        cycle_end = 100.0 + beats_to_steady_state * pcl

        mask = (time_arr >= cycle_start) & (time_arr <= cycle_end)
        
        # Shift the time array to align with a 0-indexed baseline
        t_slice = time_arr[mask] - (cycle_start - 100.0)
        v_slice = voltage_arr[mask]

        features = extract_ap_features(t_slice, v_slice)
        apd90 = features.get("apd90", 0.0)
        results.append((pcl, apd90))

    return results
