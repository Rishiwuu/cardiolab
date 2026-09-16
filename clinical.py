"""Clinical interpretation module for the CardioLab platform.

This module processes extracted electrophysiological features and genetic data to generate
clinical insight summaries, syndrome classifications, and metric comparisons.
It serves as the interface between raw biophysical simulation data and medical-educational explanations.
"""

from typing import Dict, Any


def generate_clinical_insight(
    mutation_data: Dict[str, Any],
    normal_features: Dict[str, float],
    mutated_features: Dict[str, float],
    heart_rate: float
) -> Dict[str, str]:
    """Generates structured educational insights and metrics based on simulation results.

    Translates mathematical action potential measurements (like APD90) into clinical indicators
    (like estimated QT intervals) and formats mutation information.

    Args:
        mutation_data: The record of the mutation from the mutation database.
        normal_features: Dictionary of extracted AP features for the baseline simulation.
        mutated_features: Dictionary of extracted AP features for the mutated simulation.
        heart_rate: The nominal heart rate (bpm) calculated from pacing.

    Returns:
        A dictionary containing clean, formatted display strings for the UI:
            Core metrics:
                - "mutation_title", "protein", "syndrome", "inheritance"
                - "clinvar_id", "omim_id", "normal_apd90", "mutated_apd90", "apd90_change"
                - "heart_rate", "effect", "description", "reference"
            Channel annotation:
                - "affected_channel", "current", "phase"
            Evidence:
                - "evidence_level", "clinvar_classification"
            Mechanism:
                - "mechanism_steps" (list of str)
            Model transparency:
                - "model_approximation"
                - "simulation_notes"
            Protein domain:
                - "protein_length" (int), "mutation_residue" (int)
            Disclaimer:
                - "disclaimer"
    """
    normal_apd90 = normal_features.get("apd90", 0.0)
    mutated_apd90 = mutated_features.get("apd90", 0.0)

    # Compute percent APD90 change relative to baseline
    if normal_apd90 > 0:
        pct_change = ((mutated_apd90 - normal_apd90) / normal_apd90) * 100.0
        apd90_change_str = f"{pct_change:+.1f}%"
    else:
        apd90_change_str = "0.0%"

    # Build educational simulation notes from simulation config
    sim_info = mutation_data.get("simulation", {})
    param = sim_info.get("parameter")
    op = sim_info.get("operation")
    val = sim_info.get("value")
    channel = mutation_data.get("affected_channel", "N/A")
    current = mutation_data.get("current", "N/A")

    if param:
        notes = (
            f"Target mutation:            {mutation_data.get('gene', 'N/A')} {mutation_data.get('mutation', 'N/A')}\n"
            f"Physiological target:       {current}\n"
            f"Beeler-Reuter approximation: {param} × {val}\n"
            f"Operation:                  {op}\n"
            f"\nReason:\n{mutation_data.get('model_approximation', '')}"
        )
    else:
        notes = (
            f"Target mutation:  None (Wild-type baseline)\n"
            f"Model parameters: Unmodified\n"
            f"\n{mutation_data.get('model_approximation', '')}"
        )

    return {
        # Core identifiers
        "mutation_title": f"{mutation_data.get('gene', 'N/A')} {mutation_data.get('mutation', 'WT')}",
        "protein": mutation_data.get("protein", "N/A"),
        "syndrome": mutation_data.get("syndrome", "Healthy Baseline"),
        "inheritance": mutation_data.get("inheritance", "N/A"),
        "clinvar_id": mutation_data.get("clinvar", "N/A"),
        "omim_id": mutation_data.get("omim", "N/A"),
        # APD90 metrics (cellular action potential duration, not surface-ECG QT interval)
        "normal_apd90": f"{normal_apd90:.1f} ms",
        "mutated_apd90": f"{mutated_apd90:.1f} ms",
        "apd90_change": apd90_change_str,
        "heart_rate": f"{heart_rate:.1f} bpm",
        # Mechanism & effect
        "effect": mutation_data.get("effect", "N/A"),
        "description": mutation_data.get("description", ""),
        "mechanism_steps": mutation_data.get("mechanism_steps", []),
        # Channel annotation
        "affected_channel": mutation_data.get("affected_channel", "N/A"),
        "current": mutation_data.get("current", "N/A"),
        "phase": mutation_data.get("phase", "N/A"),
        # Evidence
        "evidence_level": mutation_data.get("evidence_level", "N/A"),
        "clinvar_classification": mutation_data.get("clinvar_classification", "N/A"),
        # Model transparency
        "model_approximation": mutation_data.get("model_approximation", "N/A"),
        "simulation_notes": notes,
        # Reference
        "reference": mutation_data.get("reference", "N/A"),
        # Protein domain visualization data (passed as raw values)
        "protein_length": mutation_data.get("protein_length", 0),
        "mutation_residue": mutation_data.get("mutation_residue", 0),
        # Disclaimer
        "disclaimer": (
            "Educational Disclaimer: CardioLab is an interactive, educational tool designed for teaching "
            "cardiac electrophysiology. It is NOT a medical device, is not cleared by any regulatory agency, "
            "and should not be used as clinical diagnostic advice or for patient care decisions."
        )
    }
