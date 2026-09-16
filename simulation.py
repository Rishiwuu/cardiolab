"""Simulation engine module for the CardioLab platform.

This module interface handles loading Myokit cell models and stimulus protocols,
modifying ion channel conductances based on mutation profiles, and executing
ventricular action potential simulations.
"""

import sys
import warnings
from pathlib import Path
from typing import Dict, Tuple, Any, Optional
import myokit

_workspace_root = Path(__file__).resolve().parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from CardioLab.config import MODEL_DATABASE, CHANNEL_ALIASES, SIMULATION_TIME

# Ion current variables available for logging in each supported model.
# These are the exact Myokit variable names confirmed via model inspection.
ION_CURRENT_VARIABLES = {
    "Beeler-Reuter": {
        "ina.INa": "INa (Fast Sodium)",
        "isi.Isi": "Isi (Slow Inward / Calcium)",
        "ik1.IK1": "IK1 (Inward Rectifier K\u207a)",
        "ix1.Ix1": "Ix1 (Time-Dependent Outward K\u207a)",
        "membrane.i_stim": "Stimulus Current",
        "calcium.Cai": "Intracellular Ca\u00b2\u207a"
    }
}


def extract_pacing_period(protocol: myokit.Protocol) -> float:
    """Extracts the pacing stimulus period from a Myokit protocol.

    Args:
        protocol: The Myokit protocol object containing stimulus events.

    Returns:
        The pacing period in milliseconds. Falls back to 1000.0 ms if no repeating event.
    """
    for event in protocol.events():
        if event.level() > 0 and event.period() > 0:
            return float(event.period())
    return 1000.0


def run_simulation(
    model_name: str,
    sim_config: Dict[str, Any],
    log_currents: bool = True
) -> Tuple[myokit.SimulationLog, myokit.SimulationLog, float, Optional[str]]:
    """Runs a parallel simulation comparing baseline (normal) and mutated cardiac activity.

    Args:
        model_name: The key of the biophysical model in MODEL_DATABASE.
        sim_config: A dictionary defining mutation parameters:
            - 'parameter': The model variable name to modify.
            - 'operation': The modification operation ('multiply', 'add', 'replace').
            - 'value': The scale or value to apply.
        log_currents: If True, also log individual ionic currents for visualization.

    Returns:
        A tuple containing:
            - log_normal: SimulationLog of the wild-type/baseline model.
            - log_mutated: SimulationLog of the modified model.
            - pacing_period: The pacing interval (ms) extracted from the protocol.
            - warning_msg: An optional warning string if parameter injection failed.

    Raises:
        ValueError: If the model name is unknown, or if the model is not implemented.
        FileNotFoundError: If the model files cannot be found.
    """
    # Determine which variables to log
    base_log_vars = ['engine.time', 'membrane.V']
    if log_currents:
        model_currents = ION_CURRENT_VARIABLES.get(model_name, {})
        base_log_vars.extend(model_currents.keys())

    if model_name not in MODEL_DATABASE:
        raise ValueError(f"Unknown cell model requested: '{model_name}'")

    model_info = MODEL_DATABASE[model_name]
    if not model_info["implemented"]:
        raise ValueError(f"Model '{model_name}' is not currently implemented in CardioLab.")

    model_path = model_info["model_file"]
    protocol_path = model_info["protocol_file"]

    if not model_path or not protocol_path:
        raise FileNotFoundError(f"Model configuration path error for '{model_name}'")

    # Load structures
    model = myokit.load_model(model_path)
    protocol = myokit.load_protocol(protocol_path)

    # 1. Run Baseline (Normal) Simulation
    sim_normal = myokit.Simulation(model, protocol)
    log_normal = sim_normal.run(SIMULATION_TIME, log=base_log_vars)

    # Extract pacing period from protocol
    pacing_period = extract_pacing_period(protocol)

    # 2. Modify Model for Mutation Simulation
    warning_msg = None
    param_name = sim_config.get("parameter")

    if param_name:
        # Resolve target channel using aliases
        resolved_channel = CHANNEL_ALIASES.get(param_name, param_name)
        if model.has_variable(resolved_channel):
            var = model.get(resolved_channel)
            op = sim_config.get("operation", "multiply")
            val = sim_config.get("value", 1.0)

            # Apply operation
            if var.is_constant():
                current_rhs = float(var.rhs())
                if op == "multiply":
                    new_rhs = current_rhs * float(val)
                elif op == "add":
                    new_rhs = current_rhs + float(val)
                elif op == "replace":
                    new_rhs = float(val)
                else:
                    raise ValueError(f"Unsupported mutation operation: '{op}'")
                var.set_rhs(new_rhs)
            else:
                # For non-constants (e.g. currents like ix1.Ix1 or ik1.IK1), set RHS as a formula
                if op == "multiply":
                    new_rhs_str = f"({var.rhs()}) * {val}"
                elif op == "add":
                    new_rhs_str = f"({var.rhs()}) + {val}"
                elif op == "replace":
                    new_rhs_str = f"{val}"
                else:
                    raise ValueError(f"Unsupported mutation operation: '{op}'")
                var.set_rhs(new_rhs_str)
        else:
            warning_msg = f"Target variable '{param_name}' is not present in cell model '{model_name}'."
            warnings.warn(warning_msg, UserWarning)

    # 3. Run Mutated Simulation
    sim_mutated = myokit.Simulation(model, protocol)
    log_mutated = sim_mutated.run(SIMULATION_TIME, log=base_log_vars)

    return dict(log_normal), dict(log_mutated), pacing_period, warning_msg
