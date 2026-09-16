"""Mutation comparison helper for CardioLab.

This module coordinates running multiple simulations for a list of mutation keys
and returns their trajectories and extracted electrophysiological features.
"""

from typing import Dict, List, Tuple, Any
import myokit

from CardioLab.mutation_database import get_mutation
from CardioLab.simulation import run_simulation
from CardioLab.features import extract_ap_features


def run_multi_mutation_comparison(
    model_name: str,
    mutation_keys: List[str]
) -> Dict[str, Tuple[myokit.SimulationLog, Dict[str, float]]]:
    """Runs simulations for a list of mutations and extracts features for each.

    Args:
        model_name: Biophysical model key (e.g. 'Beeler-Reuter').
        mutation_keys: List of mutation names to simulate.

    Returns:
        A dictionary mapping mutation names to tuples of (simulation_log, features_dict).
    """
    results = {}
    for key in mutation_keys:
        mut_data = get_mutation(key)
        if not mut_data:
            continue
        sim_config = mut_data.get("simulation", {"parameter": None, "operation": "multiply", "value": 1.0})
        
        # Run simulation (the second return value is the mutated simulation log)
        _, log_mutated, _, _ = run_simulation(model_name, sim_config, log_currents=False)
        
        # Extract features
        features = extract_ap_features(log_mutated["engine.time"], log_mutated["membrane.V"])
        results[key] = (log_mutated, features)
        
    return results
