"""Mutation database module for the CardioLab platform.

This module stores all genetic mutations affecting ion channels, along with their
clinical descriptions, database references, and simulation instruction parameters.
"""

from typing import Dict, List, Optional, Any

MUTATION_DATABASE: Dict[str, Dict[str, Any]] = {
    "SCN5A R1623Q": {
        "gene": "SCN5A",
        "mutation": "R1623Q",
        "protein": "p.Arg1623Gln",
        "syndrome": "Long QT Syndrome Type 3 (LQT3)",
        "parameter": "ina.gNaBar",
        "multiplier": 1.5,
        # Ion channel annotation
        "affected_channel": "Nav1.5",
        "current": "INa (Fast inward sodium current)",
        "phase": "Phase 0 (Depolarization) / Phase 2 (Persistent late INa)",
        # Mechanism of disease
        "effect": "Gain-of-function (impaired fast inactivation leading to persistent late sodium current, INa-Late)",
        "description": (
            "Persistent late sodium current prolongs the ventricular action potential plateau. "
            "Increased net inward sodium entry during Phase 2 delays repolarization, manifesting "
            "as a prolonged QT interval on the ECG and predisposing patients to torsades de pointes (TdP)."
        ),
        # Cascade of events for mechanism flowchart
        "mechanism_steps": [
            "SCN5A R1623Q Mutation",
            "Impaired fast inactivation of Nav1.5",
            "Persistent late INa during plateau (Phase 2)",
            "Prolonged action potential plateau",
            "↑ APD90",
            "↑ QT interval",
            "Risk: Torsades de pointes (TdP)"
        ],
        # Protein domain positioning for visualization
        "protein_length": 2016,        # Nav1.5 total residues
        "mutation_residue": 1623,       # R1623 position
        # Model-level approximation note (scientific transparency)
        "model_approximation": (
            "The Beeler-Reuter (1977) model includes a simplified fast sodium current (INa) via "
            "ina.gNaBar. Scaling this conductance upward approximates the increased net sodium entry "
            "associated with impaired channel inactivation, reproducing the qualitative APD prolongation "
            "phenotype. It does not model the distinct kinetics of persistent late-current INa-Late."
        ),
        # Model fidelity classification
        "fidelity": "phenotypic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "phenotypic",
                "target": "ina.gNaBar",
                "reason": (
                    "BR77 contains a fast sodium current (INa) but does not distinguish between "
                    "peak INa and persistent late INa (INa-Late). Scaling gNaBar approximates "
                    "the net gain-of-function phenotype without modeling inactivation kinetics."
                )
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": "INaL.GNaL",
                "reason": (
                    "ORd explicitly represents late sodium current (INaL) as a separate formulation, "
                    "enabling direct mechanistic simulation of impaired fast inactivation."
                )
            }
        },
        # Clinical evidence
        "inheritance": "Autosomal Dominant",
        "evidence_level": "★★★★★ Pathogenic",
        "clinvar_classification": "Pathogenic",
        "reference": "Bennett et al., 1995 (Nature 376: 683-685)",
        "clinvar": "RCV000003294",
        "omim": "603830",
        "simulation": {
            "parameter": "ina.gNaBar",
            "operation": "multiply",
            "value": 1.5
        }
    },
    "KCNH2 N588K": {
        "gene": "KCNH2",
        "mutation": "N588K",
        "protein": "p.Asn588Lys",
        "syndrome": "Short QT Syndrome Type 1 (SQTS1)",
        "parameter": "ix1.Ix1",
        "multiplier": 2.0,
        # Ion channel annotation
        "affected_channel": "hERG (Kv11.1)",
        "current": "IKr (Rapid delayed rectifier potassium current)",
        "phase": "Phase 3 (Rapid Repolarization)",
        # Mechanism of disease
        "effect": "Gain-of-function (reduced channel inactivation leading to increased rapid delayed rectifier potassium current, IKr)",
        "description": (
            "Reduced inactivation of hERG channels allows more outward potassium current to flow during the "
            "action potential plateau and rapid repolarization phase (Phase 3). This accelerates ventricular "
            "repolarization, shortens APD, and increases susceptibility to re-entrant "
            "ventricular arrhythmias, including ventricular fibrillation."
        ),
        # Cascade of events for mechanism flowchart
        "mechanism_steps": [
            "KCNH2 N588K Mutation",
            "Reduced hERG channel inactivation",
            "↑ IKr during action potential plateau",
            "Accelerated ventricular repolarization",
            "↓ APD90",
            "↓ APD90 (QT Proxy)",
            "↑ Risk of re-entrant ventricular arrhythmias"
        ],
        # Protein domain positioning for visualization
        "protein_length": 1159,        # KCNH2/hERG total residues
        "mutation_residue": 588,        # N588 position (S5–pore linker domain)
        # Model-level approximation note (scientific transparency)
        "model_approximation": (
            "The Beeler-Reuter (1977) model predates the molecular identification of hERG/IKr and does not "
            "include an explicit rapid delayed rectifier current. The electrophysiological phenotype of "
            "KCNH2 N588K (accelerated repolarization) is approximated by scaling up the time-dependent outward "
            "potassium current ix1.Ix1 to accelerate repolarization."
        ),
        # Model fidelity classification
        "fidelity": "phenotypic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "phenotypic",
                "target": "ix1.Ix1",
                "reason": (
                    "BR77 predates explicit hERG/IKr representation. Scaling up ix1.Ix1 (time-dependent outward "
                    "current) reproduces the qualitative APD shortening phenotype."
                )
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": "IKr.GKr",
                "reason": (
                    "ORd explicitly represents IKr with Markov-state gating, enabling direct "
                    "simulation of hERG inactivation defects."
                )
            }
        },
        # Clinical evidence
        "inheritance": "Autosomal Dominant",
        "evidence_level": "★★★★★ Pathogenic",
        "clinvar_classification": "Pathogenic",
        "reference": "Brugada et al., 2004 (Circulation 109: 30-35)",
        "clinvar": "RCV000162534",
        "omim": "609620",
        "simulation": {
            "parameter": "ix1.Ix1",
            "operation": "multiply",
            "value": 2.0
        }
    },
    "KCNH2 A561V": {
        "gene": "KCNH2",
        "mutation": "A561V",
        "protein": "p.Ala561Val",
        "syndrome": "Long QT Syndrome Type 2 (LQT2)",
        "parameter": "ix1.Ix1",
        "multiplier": 0.5,
        "affected_channel": "hERG (Kv11.1)",
        "current": "IKr (Rapid delayed rectifier potassium current)",
        "phase": "Phase 3 (Rapid Repolarization)",
        "effect": "Loss-of-function (trafficking defect or gating impairment leading to reduced repolarizing potassium current, IKr)",
        "description": (
            "Reduction in functional hERG channels on the membrane surface impairs outward potassium efflux during "
            "Phase 3 repolarization. This delays ventricular repolarization, prolongs the APD, and increases risk of "
            "early afterdepolarizations (EADs) and torsades de pointes (TdP)."
        ),
        "mechanism_steps": [
            "KCNH2 A561V Mutation",
            "Impaired hERG trafficking/conduction",
            "↓ IKr during action potential repolarization",
            "Delayed ventricular repolarization",
            "↑ APD90",
            "↑ APD90 (QT Proxy)",
            "Risk: Early Afterdepolarizations & TdP"
        ],
        "protein_length": 1159,
        "mutation_residue": 561,
        "model_approximation": (
            "The Beeler-Reuter (1977) model does not have an explicit hERG/IKr current. KCNH2 loss-of-function "
            "is approximated by scaling down the outward potassium current ix1.Ix1 by 50% to slow repolarization."
        ),
        "fidelity": "phenotypic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "phenotypic",
                "target": "ix1.Ix1",
                "reason": (
                    "BR77 lacks explicit hERG. Scaling down ix1.Ix1 (repolarizing outward current) "
                    "approximates delayed repolarization."
                )
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": "IKr.GKr",
                "reason": "ORd represents IKr explicitly, permitting direct mapping of conductance reductions."
            }
        },
        "inheritance": "Autosomal Dominant",
        "evidence_level": "★★★★★ Pathogenic",
        "clinvar_classification": "Pathogenic",
        "reference": "Splawski et al., 2000 (Circulation 102: 1178-1185)",
        "clinvar": "RCV000003503",
        "omim": "152427",
        "simulation": {
            "parameter": "ix1.Ix1",
            "operation": "multiply",
            "value": 0.5
        }
    },
    "KCNQ1 Y111C": {
        "gene": "KCNQ1",
        "mutation": "Y111C",
        "protein": "p.Tyr111Cys",
        "syndrome": "Long QT Syndrome Type 1 (LQT1)",
        "parameter": "ix1.Ix1",
        "multiplier": 0.6,
        "affected_channel": "KvLQT1 (Kv7.1)",
        "current": "IKs (Slow delayed rectifier potassium current)",
        "phase": "Phase 2/3 (Plateau and Repolarization)",
        "effect": "Loss-of-function (impaired slow delayed rectifier current, IKs)",
        "description": (
            "Loss of functional IKs channels limits the cardiac repolarization reserve. This impairs the cell's "
            "ability to shorten action potential duration during heart rate increases (e.g., sympathetic stimulation), "
            "prolonging APD and increasing susceptibility to tachyarrhythmias."
        ),
        "mechanism_steps": [
            "KCNQ1 Y111C Mutation",
            "Impaired Kv7.1 channel assembly/conduction",
            "↓ IKs repolarization current reserve",
            "Delayed repolarization",
            "↑ APD90",
            "↑ APD90 (QT Proxy)",
            "Risk: Stress-induced arrhythmias"
        ],
        "protein_length": 676,
        "mutation_residue": 111,
        "model_approximation": (
            "The Beeler-Reuter (1977) model contains only a single time-dependent outward potassium current, ix1.Ix1. "
            "KCNQ1 loss-of-function is approximated by reducing ix1.Ix1 by 40%."
        ),
        "fidelity": "phenotypic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "phenotypic",
                "target": "ix1.Ix1",
                "reason": "BR77 does not distinguish IKr and IKs; ix1.Ix1 represents their combined repolarizing effect."
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": "IKs.GKs",
                "reason": "ORd includes a distinct, fully parameterized slow outward potassium current (IKs)."
            }
        },
        "inheritance": "Autosomal Dominant",
        "evidence_level": "★★★★★ Pathogenic",
        "clinvar_classification": "Pathogenic",
        "reference": "Neyroud et al., 1997 (Nat. Genet. 15: 186-189)",
        "clinvar": "RCV000003444",
        "omim": "191330",
        "simulation": {
            "parameter": "ix1.Ix1",
            "operation": "multiply",
            "value": 0.6
        }
    },
    "CACNA1C G406R": {
        "gene": "CACNA1C",
        "mutation": "G406R",
        "protein": "p.Gly406Arg",
        "syndrome": "Timothy Syndrome (Long QT Type 8 / LQT8)",
        "parameter": "isi.gsBar",
        "multiplier": 2.0,
        "affected_channel": "Cav1.2",
        "current": "ICaL (L-type calcium current)",
        "phase": "Phase 2 (Plateau Phase)",
        "effect": "Gain-of-function (impaired voltage-dependent channel inactivation leading to persistent inward Ca²⁺ entry)",
        "description": (
            "Mutations in Cav1.2 delay its inactivation, causing a sustained influx of calcium during Phase 2. "
            "This severely prolongs the action potential plateau, increases intracellular calcium load, and creates "
            "a highly unstable electrophysiological substrate prone to EADs and lethal arrhythmias."
        ),
        "mechanism_steps": [
            "CACNA1C G406R Mutation",
            "Impaired Cav1.2 channel inactivation",
            "↑ Inward ICaL during plateau phase",
            "Sustained action potential plateau",
            "↑ APD90",
            "↑ APD90 (QT Proxy)",
            "Risk: Severe EADs & multiorgan symptoms"
        ],
        "protein_length": 2221,
        "mutation_residue": 406,
        "model_approximation": (
            "The Beeler-Reuter (1977) model represents L-type calcium current via the slow inward current isi.gsBar. "
            "Timothy Syndrome is approximated by scaling up isi.gsBar by 2.0 to simulate increased calcium entry."
        ),
        "fidelity": "phenotypic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "phenotypic",
                "target": "isi.gsBar",
                "reason": (
                    "BR77 uses isi.gsBar for calcium current. Scaling this parameter models increased total calcium influx "
                    "but does not capture the inactivation kinetics alterations directly."
                )
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": "ical.PCa",
                "reason": "ORd models detailed L-type calcium current kinetics, allowing realistic gating alterations."
            }
        },
        "inheritance": "Autosomal Dominant (De Novo)",
        "evidence_level": "★★★★★ Pathogenic",
        "clinvar_classification": "Pathogenic",
        "reference": "Splawski et al., 2004 (Cell 119: 19-31)",
        "clinvar": "RCV000003929",
        "omim": "601005",
        "simulation": {
            "parameter": "isi.gsBar",
            "operation": "multiply",
            "value": 2.0
        }
    },
    "KCNJ2 V302M": {
        "gene": "KCNJ2",
        "mutation": "V302M",
        "protein": "p.Val302Met",
        "syndrome": "Andersen-Tawil Syndrome (LQT7)",
        "parameter": "ik1.IK1",
        "multiplier": 0.5,
        "affected_channel": "Kir2.1",
        "current": "IK1 (Inward rectifier potassium current)",
        "phase": "Phase 4 (Resting Membrane Potential) / Phase 3 (Terminal Repolarization)",
        "effect": "Loss-of-function (reduced inward rectifier potassium current, IK1)",
        "description": (
            "Loss of IK1 reduces repolarization reserve during terminal repolarization (Phase 3) and impairs the "
            "stabilization of Phase 4 resting membrane potential. This depolarizes the resting potential, prolongs APD "
            "with a characteristic slow final repolarization phase, and triggers spontaneous activity."
        ),
        "mechanism_steps": [
            "KCNJ2 V302M Mutation",
            "Reduced Kir2.1 channel conductance",
            "↓ IK1 current during Phase 3 & 4",
            "Impaired terminal repolarization & RMP stabilization",
            "Depolarized resting potential & ↑ APD90",
            "↑ APD90 (QT Proxy)",
            "Risk: Ventricular ectopy & periodic paralysis"
        ],
        "protein_length": 427,
        "mutation_residue": 302,
        "model_approximation": (
            "The Beeler-Reuter (1977) model contains an analytical formulation for ik1.IK1. KCNJ2 loss-of-function "
            "is approximated by scaling down the total ik1.IK1 current by 50%."
        ),
        "fidelity": "phenotypic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "phenotypic",
                "target": "ik1.IK1",
                "reason": "BR77 models IK1 as a direct algebraic current. We scale the entire formula to simulate loss of function."
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": "IK1.GK1",
                "reason": "ORd contains a fully separate, conductance-scaled formulation for IK1."
            }
        },
        "inheritance": "Autosomal Dominant",
        "evidence_level": "★★★★★ Pathogenic",
        "clinvar_classification": "Pathogenic",
        "reference": "Plaster et al., 2001 (Cell 105: 511-519)",
        "clinvar": "RCV000003507",
        "omim": "170390",
        "simulation": {
            "parameter": "ik1.IK1",
            "operation": "multiply",
            "value": 0.5
        }
    },
    "Normal": {
        "gene": "None",
        "mutation": "None",
        "protein": "Wild-type",
        "syndrome": "Healthy Heart (Baseline)",
        "parameter": None,
        "multiplier": 1.0,
        "affected_channel": "N/A",
        "current": "N/A",
        "phase": "N/A",
        "effect": "Physiological baseline (no mutation)",
        "description": (
            "Baseline simulation representing a healthy ventricular myocyte. Conductances and kinetics "
            "are set to standard physiological parameters as originally modeled by Beeler and Reuter in 1977."
        ),
        "mechanism_steps": [
            "Healthy Baseline",
            "All channels at physiological conductances",
            "Normal depolarization (Phase 0)",
            "Normal plateau (Phase 2)",
            "Normal repolarization (Phase 3)",
            "Normal APD90",
            "Normal QT interval"
        ],
        "protein_length": 0,
        "mutation_residue": 0,
        "model_approximation": (
            "Standard Beeler-Reuter (1977) parameters used without modification. Represents the "
            "published wild-type ventricular myocyte model."
        ),
        # Model fidelity classification
        "fidelity": "mechanistic",
        "model_mapping": {
            "Beeler-Reuter": {
                "fidelity": "mechanistic",
                "target": None,
                "reason": "Unmodified baseline — no parameter changes applied."
            },
            "O'Hara-Rudy": {
                "fidelity": "mechanistic",
                "target": None,
                "reason": "Unmodified baseline — no parameter changes applied."
            }
        },
        "inheritance": "N/A",
        "evidence_level": "N/A",
        "clinvar_classification": "N/A",
        "reference": "Beeler & Reuter, 1977 (J. Physiol. 268: 177-210)",
        "clinvar": "N/A",
        "omim": "N/A",
        "simulation": {
            "parameter": None,
            "operation": "multiply",
            "value": 1.0
        }
    }
}


def list_mutations() -> List[str]:
    """Returns a list of all mutation keys available in the database.

    Returns:
        A list of string keys.
    """
    return list(MUTATION_DATABASE.keys())


def get_mutation(mutation_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves the mutation profile for a specific mutation name.

    Args:
        mutation_name: The name of the mutation (key).

    Returns:
        The mutation data dictionary if found, otherwise None.
    """
    return MUTATION_DATABASE.get(mutation_name)
