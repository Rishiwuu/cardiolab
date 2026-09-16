"""Global configurations and constants for the CardioLab platform.

This module houses paths, physical constants, parameters for cell models, and color palettes
used by the plotting functions to separate UI details from domain logic.
"""

from pathlib import Path
import myokit

# --- PATHS ---
MYOKIT_DATA_DIR = Path(myokit.__path__[0]) / 'tests' / 'data'

# --- MODEL DATABASE ---
MODEL_DATABASE = {
    "Beeler-Reuter": {
        "model_file": str(MYOKIT_DATA_DIR / 'beeler-1977-model.mmt'),
        "protocol_file": str(MYOKIT_DATA_DIR / 'beeler-1977-protocol.mmt'),
        "description": (
            "Beeler-Reuter (1977) mammalian ventricular cell model. Historical milestone in "
            "computational electrophysiology representing fast sodium current, slow inward current "
            "(calcium), and potassium currents."
        ),
        "implemented": True
    },
    "Ten Tusscher": {
        "model_file": None,
        "protocol_file": None,
        "description": (
            "Ten Tusscher (2006) human ventricular cell model. Features detailed formulations for "
            "epicardial, endocardial, and M-cell subtypes, along with advanced intracellular calcium handling."
        ),
        "implemented": False
    },
    "O'Hara-Rudy": {
        "model_file": None,
        "protocol_file": None,
        "description": (
            "O'Hara-Rudy (2011) human ventricular model. The current gold standard for cardiac safety "
            "simulations, parameterized extensively with human experimental data."
        ),
        "implemented": False
    }
}

# --- SIMULATION CONFIGURATION ---
DEFAULT_MODEL = "Beeler-Reuter"
SIMULATION_TIME = 600.0  # ms
DEFAULT_THRESHOLD_PCT = 0.90  # APD90 threshold ratio

# Channel aliases to translate generic biological names to model variables
CHANNEL_ALIASES = {
    "ina.gNa": "ina.gNaBar",
    "gNa": "ina.gNaBar",
    "ikr.gKr": "ix1.Ix1",    # Map IKr/hERG to repolarizing Ix1 in BR77
    "gKr": "ix1.Ix1",
    "iks.gKs": "ix1.Ix1",    # Map IKs/slow delayed rectifier to Ix1 in BR77
    "gKs": "ix1.Ix1",
    "ik1.gK1": "ik1.IK1",    # Map IK1/inward rectifier to IK1 in BR77
    "gK1": "ik1.IK1",
    "gCa": "isi.gsBar",      # Map ICaL/slow inward to gsBar in BR77
    "gs": "isi.gsBar",
}

# --- STYLING & PALETTES ---
COLORS = {
    "normal": "#7f8c8d",      # Muted slate gray for baseline reference
    "mutated": "#ff4b4b",     # Streamlit-vibrant red for mutations
    "ecg_normal": "#57606f",  # Darker gray for baseline ECG
    "ecg_mutated": "#1e90ff", # Dodger blue for mutated ECG
    "grid": "#e1e2e6",        # Soft light gray for plot grid lines
}
