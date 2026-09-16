"""Main Streamlit application for CardioLab (Version 0.3).

This script serves as the UI frontend of the platform. It handles page layout,
collects user options for model and genetic mutation inputs, coordinates caching
for biophysical simulations, displays physiological plots (Action Potential & Pseudo-ECG),
ion current visualization, AP metrics comparison, rate-dependent restitution curves,
and renders the clinical interpretation dashboard with model fidelity indicators.
"""

import sys
from pathlib import Path

# Ensure the workspace root (parent of the CardioLab package) is on sys.path
# so that `from CardioLab.x import ...` works when Streamlit runs this file directly.
_workspace_root = Path(__file__).resolve().parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from typing import Optional, List, Dict, Tuple, Any
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from CardioLab.config import MODEL_DATABASE, COLORS, DEFAULT_MODEL
from CardioLab.mutation_database import list_mutations, get_mutation
from CardioLab.simulation import run_simulation, ION_CURRENT_VARIABLES
from CardioLab.features import extract_ap_features
from CardioLab.ecg import generate_pseudo_ecg, estimate_rr_interval, calculate_heart_rate
from CardioLab.clinical import generate_clinical_insight
from CardioLab.utils import verify_model_files
from CardioLab.restitution import run_restitution_protocol

# --- 1. CONFIGURATION & UI SETUP ---
st.set_page_config(
    page_title="CardioLab: Cardiac Digital Twin Platform",
    page_icon="🫀",
    layout="wide"
)

# Premium UI Header
st.markdown("""
    <div style="background-color:#1e272e; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h1 style="color:#ffffff; margin: 0; font-size: 2.2rem; font-family:'Outfit', 'Inter', sans-serif;">
            🫀 CardioLab
        </h1>
        <p style="color:#a4b0be; margin: 5px 0 0 0; font-size: 1.05rem;">
            Educational Biophysical Simulation & Genetic Mutation Explorer (Version 0.3)
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
Welcome to **CardioLab**, an interactive digital twin platform for modeling cellular cardiac electrophysiology.
Configure your simulation in the sidebar to observe how gene variants alter the single-cell action potential,
underlying ionic currents, and the rate-dependent restitution behavior.
""")

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.image(
    "https://img.icons8.com/color/144/heart-with-pulse.png",
    width=72
)
st.sidebar.markdown("### Digital Twin Controls")

# Biophysical Cell Model Selection (Future-proof database)
model_keys = list(MODEL_DATABASE.keys())
selected_model = st.sidebar.selectbox(
    "Biophysical Cell Model",
    model_keys,
    index=model_keys.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_keys else 0,
    help="Select the mathematical model of the cardiomyocyte membrane potential."
)

model_info = MODEL_DATABASE[selected_model]
st.sidebar.caption(f"**Model Info:** {model_info['description']}")

# Handle placeholder cell models gracefully
active_model = DEFAULT_MODEL
if not model_info["implemented"]:
    st.sidebar.info(
        f"ℹ️ **{selected_model} Model** is planned for a future version. "
        f"Running simulation with the baseline **{DEFAULT_MODEL}** model instead."
    )
    active_model = DEFAULT_MODEL
else:
    active_model = selected_model

# Simulation Mode Toggle
st.sidebar.markdown("---")
st.sidebar.markdown("### Mode & Genetic Input")
compare_mode = st.sidebar.checkbox(
    "Enable Mutation Compare Mode",
    value=False,
    help="Compare multiple mutations side-by-side on the same graphs."
)

mutation_keys = list_mutations()

if compare_mode:
    selected_mutation_keys = st.sidebar.multiselect(
        "Select Mutations to Compare",
        options=mutation_keys,
        default=["Normal", "SCN5A R1623Q", "KCNH2 N588K"],
        help="Choose two or more mutations to plot simultaneously."
    )
    if not selected_mutation_keys:
        st.error("Please select at least one mutation in the sidebar.")
        st.stop()
    # The first mutation in the list serves as the reference for details
    primary_mutation_key = selected_mutation_keys[0]
else:
    selected_mutation_key = st.sidebar.selectbox(
        "Select Mutation",
        mutation_keys,
        index=mutation_keys.index("Normal") if "Normal" in mutation_keys else 0,
        help="Select a gene variant to simulate."
    )
    selected_mutation_keys = [selected_mutation_key]
    primary_mutation_key = selected_mutation_key

# Retrieve primary variant data
primary_mutation_data = get_mutation(primary_mutation_key)
if not primary_mutation_data:
    st.error("Selected mutation profile not found in database.")
    st.stop()

# --- 3. CACHED SIMULATION ENGINE WRAPPERS ---
@st.cache_data(show_spinner=False)
def run_cached_simulation_v2(
    model_name: str,
    parameter: Optional[str],
    operation: str,
    value: float
):
    sim_config = {
        "parameter": parameter,
        "operation": operation,
        "value": value
    }
    return run_simulation(model_name, sim_config, log_currents=True)


@st.cache_data(show_spinner=False)
def run_cached_restitution_v2(
    model_name: str,
    parameter: Optional[str],
    operation: str,
    value: float,
    cycle_lengths: Tuple[float, ...]
):
    sim_config = {
        "parameter": parameter,
        "operation": operation,
        "value": value
    }
    return run_restitution_protocol(model_name, sim_config, cycle_lengths=list(cycle_lengths))


# --- 4. EXECUTION PIPELINE ---
active_model_info = MODEL_DATABASE[active_model]
if not verify_model_files(active_model_info["model_file"], active_model_info["protocol_file"]):
    st.error(
        f"❌ Simulation files not found on this system for model '{active_model}'.\n"
        f"Expected path: {active_model_info['model_file']}"
    )
    st.stop()

# Run all selected simulations
simulation_results = {}
try:
    with st.spinner("Executing biophysical cell simulations..."):
        for key in selected_mutation_keys:
            mut_data = get_mutation(key)
            sim_config = mut_data.get("simulation", {"parameter": None, "operation": "multiply", "value": 1.0})
            log_normal, log_mutated, pacing_period, warning = run_cached_simulation_v2(
                active_model,
                sim_config.get("parameter"),
                sim_config.get("operation", "multiply"),
                sim_config.get("value", 1.0)
            )
            # Extract features & ECG for each
            feats = extract_ap_features(log_mutated["engine.time"], log_mutated["membrane.V"])
            ecg_time, ecg_signal = generate_pseudo_ecg(
                log_mutated["engine.time"], log_mutated["membrane.V"], feats
            )
            simulation_results[key] = {
                "log": log_mutated,
                "features": feats,
                "ecg_time": ecg_time,
                "ecg_signal": ecg_signal,
                "warning": warning,
                "data": mut_data
            }
except Exception as e:
    st.error("Simulation engine failed during execution.")
    st.code(str(e), language="text")
    st.stop()

# Retrieve baseline reference features
ref_log = log_normal
ref_features = extract_ap_features(ref_log["engine.time"], ref_log["membrane.V"])

# --- 5. VISUALIZATION TABS ---
viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
    "📈 Action Potential & ECG Proxy",
    "⚡ Ion Currents",
    "📊 AP Metrics Dashboard",
    "🏁 Restitution Curves"
])

# Matplotlib line styling list
line_styles = [
    {"linestyle": "-", "linewidth": 2.5},
    {"linestyle": "--", "linewidth": 2.0},
    {"linestyle": "-.", "linewidth": 2.0},
    {"linestyle": ":", "linewidth": 2.5},
]
color_palette = ["#1e90ff", "#ff4b4b", "#2ecc71", "#9b59b6", "#f1c40f", "#e67e22"]

# ---------- TAB 1: Action Potential & Pseudo-ECG ----------
with viz_tab1:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)

    # If not in compare mode and the only selected variant is not Normal, overlay baseline Normal as reference
    if not compare_mode and primary_mutation_key != "Normal":
        ax1.plot(
            ref_log["engine.time"],
            ref_log["membrane.V"],
            label="Baseline Normal (WT)",
            color=COLORS["normal"],
            linestyle=":",
            alpha=0.8,
            linewidth=1.8
        )
        # ECG Normal reference
        normal_ecg_t, normal_ecg_s = generate_pseudo_ecg(ref_log["engine.time"], ref_log["membrane.V"], ref_features)
        ax2.plot(
            normal_ecg_t,
            normal_ecg_s,
            label="Normal Pseudo-ECG",
            color=COLORS["ecg_normal"],
            linestyle=":",
            alpha=0.8,
            linewidth=1.8
        )

    # Plot each selected mutation
    for i, key in enumerate(selected_mutation_keys):
        res = simulation_results[key]
        log_m = res["log"]
        style = line_styles[i % len(line_styles)]
        color = color_palette[i % len(color_palette)] if compare_mode else COLORS["mutated"]
        if key == "Normal" and compare_mode:
            color = COLORS["normal"]
            style = {"linestyle": "--", "linewidth": 2.0}

        ax1.plot(
            log_m["engine.time"],
            log_m["membrane.V"],
            label=f"{key}",
            color=color,
            **style
        )

        ax2.plot(
            res["ecg_time"],
            res["ecg_signal"],
            label=f"{key} ECG",
            color=color,
            **style
        )

    ax1.set_ylabel("Membrane Potential (mV)", fontsize=11, fontweight="bold")
    ax1.title.set_text("Cellular Membrane Action Potential (Vm)")
    ax1.grid(True, color=COLORS["grid"], linestyle="-", linewidth=0.5)
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    ax2.set_xlabel("Time (ms)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Normalized Pseudo-ECG (a.u.)", fontsize=11, fontweight="bold")
    ax2.title.set_text("Transmural Gradient Pseudo-ECG (Educational Approximation)")
    ax2.grid(True, color=COLORS["grid"], linestyle="-", linewidth=0.5)
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)

    st.caption(
        "⚠️ **Note:** The pseudo-ECG is a simplified transmural gradient approximation "
        "(Vendo − Vepi), not a clinical surface ECG. It does not model volume conduction, "
        "electrode geometry, or atrial activity. For educational visualization only."
    )

# ---------- TAB 2: Ion Currents ----------
with viz_tab2:
    st.markdown("### Individual Ion Current Traces")
    st.markdown(
        "Visualize the individual ionic currents underlying the action potentials. "
        "This shows **why** the action potential shape changed, not just **that** it changed."
    )

    # Get available currents for the active model
    available_currents = ION_CURRENT_VARIABLES.get(active_model, {})

    # Filter out non-current variables for the primary selector (exclude Cai and stimulus by default)
    primary_currents = {k: v for k, v in available_currents.items()
                        if k not in ("calcium.Cai", "membrane.i_stim")}
    extra_currents = {k: v for k, v in available_currents.items()
                      if k in ("calcium.Cai", "membrane.i_stim")}

    selected_currents = st.multiselect(
        "Select ion currents to display:",
        options=list(primary_currents.keys()),
        default=list(primary_currents.keys()),
        format_func=lambda x: primary_currents[x]
    )

    show_extras = st.checkbox("Show stimulus current & calcium transient", value=False)
    if show_extras:
        selected_currents.extend(extra_currents.keys())

    if selected_currents:
        # Determine subplot layout
        n_plots = len(selected_currents)
        fig_currents, axes = plt.subplots(n_plots, 1, figsize=(10, 2.8 * n_plots), sharex=True)

        if n_plots == 1:
            axes = [axes]

        for idx, current_key in enumerate(selected_currents):
            ax = axes[idx]
            label = available_currents.get(current_key, current_key)

            # If not in compare mode and not Normal, plot Normal reference current
            if not compare_mode and primary_mutation_key != "Normal":
                if current_key in ref_log:
                    ax.plot(
                        ref_log["engine.time"],
                        ref_log[current_key],
                        label="Normal (WT)",
                        color=COLORS["normal"],
                        linestyle=":",
                        alpha=0.8,
                        linewidth=1.2
                    )

            # Plot each selected mutation trace
            for i, key in enumerate(selected_mutation_keys):
                res = simulation_results[key]
                log_m = res["log"]
                color = color_palette[i % len(color_palette)] if compare_mode else COLORS["mutated"]
                style = line_styles[i % len(line_styles)]
                if key == "Normal" and compare_mode:
                    color = COLORS["normal"]
                    style = {"linestyle": "--", "linewidth": 1.5}

                if current_key in log_m:
                    ax.plot(
                        log_m["engine.time"],
                        log_m[current_key],
                        label=f"{key}",
                        color=color,
                        **style
                    )

            # Units label
            unit = "mM" if current_key == "calcium.Cai" else "µA/cm²"
            ax.set_ylabel(f"{label}\n({unit})", fontsize=9, fontweight="bold")
            ax.legend(loc="upper right", fontsize=8, framealpha=0.8)
            ax.grid(True, color=COLORS["grid"], linestyle="-", linewidth=0.4)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        axes[-1].set_xlabel("Time (ms)", fontsize=11, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig_currents)

        st.caption(
            "**Current sign convention:** Inward currents (INa, Isi) are negative; "
            "outward currents (IK1, Ix1) are positive. Current magnitudes are in µA/cm²."
        )
    else:
        st.info("Select at least one ion current to display in the selector above.")

# ---------- TAB 3: AP Metrics Dashboard ----------
with viz_tab3:
    st.markdown("### Action Potential Metrics Comparison")
    st.markdown(
        "Quantitative comparison of electrophysiological biomarkers extracted from simulated waveforms."
    )

    metric_labels = {
        "apd90": ("APD90 (ms)", "ms"),
        "apd50": ("APD50 (ms)", "ms"),
        "resting_potential": ("Resting Potential Vrest (mV)", "mV"),
        "peak_voltage": ("Peak Voltage Vmax (mV)", "mV"),
        "amplitude": ("Amplitude APA (mV)", "mV"),
        "max_upstroke_velocity": ("Max Upstroke Velocity dV/dt_max (mV/ms)", "mV/ms"),
        "depolarization_time": ("Depolarization Time (ms)", "ms"),
    }

    # Build side-by-side comparison columns
    comparison_data = {"Metric": [label for label, _ in metric_labels.values()]}

    # Add Normal column as a reference always
    comparison_data["Normal (WT)"] = [
        f"{ref_features.get(k, 0.0):.2f}" for k in metric_labels.keys()
    ]

    # Add selected mutation columns
    for key in selected_mutation_keys:
        # Avoid duplicate Normal column
        if key == "Normal":
            continue
        feats = simulation_results[key]["features"]
        col_vals = []
        for k in metric_labels.keys():
            val = feats.get(k, 0.0)
            ref_val = ref_features.get(k, 0.0)
            if abs(ref_val) > 1e-9:
                delta = ((val - ref_val) / abs(ref_val)) * 100.0
                delta_str = f" ({delta:+.1f}%)"
            else:
                delta_str = ""
            col_vals.append(f"{val:.2f}{delta_str}")
        comparison_data[key] = col_vals

    df_metrics = pd.DataFrame(comparison_data)
    st.dataframe(
        df_metrics,
        use_container_width=True,
        hide_index=True
    )

# ---------- TAB 4: Restitution Curves ----------
with viz_tab4:
    st.markdown("### APD90 Restitution Curves")
    st.markdown(
        "Cardiac APD restitution describes how the Action Potential Duration (APD90) "
        "adapts to changes in the pacing frequency (cycle length). At shorter pacing cycle lengths "
        "(higher heart rates), the cell has less time to recover, causing APD90 to shorten. "
        "Genetic mutations can alter this rate-dependent behavior, causing electrical instability."
    )

    # Default PCL list for the sweep
    cycle_lengths_tuple = (1000.0, 800.0, 600.0, 500.0, 400.0, 300.0, 250.0)

    try:
        with st.spinner("Running restitution pacing protocol sweeps..."):
            restitution_curves = {}

            # Always run Normal baseline restitution as reference
            wt_mut = get_mutation("Normal")
            wt_config = wt_mut.get("simulation", {"parameter": None, "operation": "multiply", "value": 1.0})
            restitution_curves["Normal"] = run_cached_restitution_v2(
                active_model,
                wt_config.get("parameter"),
                wt_config.get("operation", "multiply"),
                wt_config.get("value", 1.0),
                cycle_lengths_tuple
            )

            # Run for other selected mutations
            for key in selected_mutation_keys:
                if key == "Normal":
                    continue
                mut_data = get_mutation(key)
                sim_config = mut_data.get("simulation", {"parameter": None, "operation": "multiply", "value": 1.0})
                restitution_curves[key] = run_cached_restitution_v2(
                    active_model,
                    sim_config.get("parameter"),
                    sim_config.get("operation", "multiply"),
                    sim_config.get("value", 1.0),
                    cycle_lengths_tuple
                )

        # Plot restitution curves
        fig_rest = plt.figure(figsize=(10, 5))
        ax_rest = fig_rest.add_subplot(111)

        # Plot Normal baseline reference
        n_pcls, n_apds = zip(*restitution_curves["Normal"])
        ax_rest.plot(
            n_pcls,
            n_apds,
            label="Normal (WT)",
            color=COLORS["normal"],
            linestyle="--",
            marker="o",
            alpha=0.85
        )

        for i, (key, curve_data) in enumerate(restitution_curves.items()):
            if key == "Normal":
                continue
            pcls, apds = zip(*curve_data)
            color = color_palette[i % len(color_palette)] if compare_mode else COLORS["mutated"]
            style = line_styles[i % len(line_styles)]
            ax_rest.plot(
                pcls,
                apds,
                label=key,
                color=color,
                marker="s",
                linewidth=2.0,
                linestyle=style.get("linestyle", "-")
            )

        ax_rest.set_xlabel("Pacing Cycle Length (PCL, ms)", fontsize=11, fontweight="bold")
        ax_rest.set_ylabel("Steady-State APD90 (ms)", fontsize=11, fontweight="bold")
        ax_rest.set_title("Steady-State APD90 Restitution Curve (5-Beat Pacing Steady State)")
        ax_rest.grid(True, color=COLORS["grid"], linestyle="-", linewidth=0.5)
        ax_rest.legend(loc="lower right", framealpha=0.9)
        ax_rest.spines['top'].set_visible(False)
        ax_rest.spines['right'].set_visible(False)

        st.pyplot(fig_rest)

        # Tabulate data
        st.markdown("**Restitution Data Table (Steady-State APD90 in ms):**")
        table_data = {"Pacing Cycle Length (ms)": [str(int(pcl)) for pcl in cycle_lengths_tuple]}
        for key, curve_data in restitution_curves.items():
            table_data[key] = [f"{apd:.1f}" for _, apd in curve_data]

        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error("Restitution protocol execution failed.")
        st.code(str(e), language="text")


# --- 6. UI HELPER FUNCTIONS (clinical panel) ---

def _render_mechanism_flowchart(steps: list) -> str:
    """Builds an HTML mechanism cascade flowchart from a list of step strings."""
    if not steps:
        return ""
    rows = []
    for i, step in enumerate(steps):
        if i == 0:
            rows.append(
                f'<div style="background:#1e272e;color:#ffffff;padding:8px 16px;border-radius:8px;'
                f'font-weight:700;font-size:0.92rem;text-align:center;'
                f'box-shadow:0 2px 6px rgba(0,0,0,0.25);">{step}</div>'
            )
        else:
            arrow_color = "#ff4b4b" if "\u2191" in step else ("#1e90ff" if "\u2193" in step else "#a4b0be")
            rows.append(
                '<div style="text-align:center;color:#a4b0be;font-size:1.1rem;'
                'line-height:1.2;margin:2px 0;">\u2193</div>'
            )
            rows.append(
                f'<div style="background:#f1f2f6;color:#2c3e50;padding:7px 14px;border-radius:6px;'
                f'font-size:0.88rem;text-align:center;border-left:4px solid {arrow_color};">{step}</div>'
            )
    return (
        '<div style="display:flex;flex-direction:column;gap:2px;max-width:380px;margin:0 auto;">'
        + "".join(rows)
        + "</div>"
    )


def _render_protein_domain(
    gene: str, mutation: str, protein_length: int, mutation_residue: int
) -> str:
    """Renders a simple SVG-style protein domain bar with mutation position marker."""
    if protein_length <= 0:
        return ""
    pct = max(2.0, min(98.0, (mutation_residue / protein_length) * 100))
    return f"""
    <div style="font-family:'Courier New', monospace; margin:10px 0 4px 0;">
        <div style="font-size:0.82rem;color:#7f8c8d;margin-bottom:6px;">
            <b>{gene}</b> protein &nbsp;&middot;&nbsp; {protein_length} residues
        </div>
        <div style="position:relative;height:22px;background:linear-gradient(90deg,#2980b9 0%,#8e44ad 50%,#e74c3c 100%);
                    border-radius:5px;box-shadow:0 2px 6px rgba(0,0,0,0.18);">
            <div style="position:absolute;left:{pct}%;top:-6px;transform:translateX(-50%);
                        width:3px;height:34px;background:#ffffff;border:2px solid #2c3e50;border-radius:2px;">
            </div>
        </div>
        <div style="position:relative;height:22px;font-size:0.78rem;">
            <span style="position:absolute;left:0;color:#7f8c8d;">N-term</span>
            <span style="position:absolute;left:{pct}%;transform:translateX(-50%);
                         font-weight:700;color:#e74c3c;">{mutation}</span>
            <span style="position:absolute;right:0;color:#7f8c8d;">C-term</span>
        </div>
    </div>
    """


def _render_fidelity_badge(fidelity: str, model_name: str, mutation_data: dict) -> str:
    """Renders a Model Fidelity indicator badge with explanation."""
    badge_config = {
        "mechanistic": {
            "icon": "\U0001f7e2",
            "label": "Mechanistic",
            "color": "#27ae60",
            "bg": "#eafaf1",
            "desc": "Mutation directly represented by model ion currents."
        },
        "phenotypic": {
            "icon": "\U0001f7e1",
            "label": "Phenotypic Approximation",
            "color": "#f39c12",
            "bg": "#fef9e7",
            "desc": "Mutation approximated through a related conductance parameter."
        },
        "unsupported": {
            "icon": "\U0001f534",
            "label": "Unsupported",
            "color": "#e74c3c",
            "bg": "#fdedec",
            "desc": "No validated model mapping exists for this mutation."
        }
    }
    cfg = badge_config.get(fidelity, badge_config["unsupported"])

    model_mapping = mutation_data.get("model_mapping", {})
    model_info = model_mapping.get(model_name, {})
    reason = model_info.get("reason", "")

    reason_html = ""
    if reason and fidelity != "mechanistic":
        reason_html = f"""
        <div style="font-size:0.82rem;color:#555;margin-top:6px;padding-top:6px;
                    border-top:1px solid #e0e0e0;">
            <b>Reason:</b> {reason}
        </div>
        """

    return f"""
    <div style="background:{cfg['bg']};border:1px solid {cfg['color']};border-radius:10px;
                padding:12px 16px;margin:8px 0;">
        <div style="font-size:0.75rem;font-weight:600;color:#6c757d;
                     text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">
            Simulation Fidelity ({model_name})
        </div>
        <div style="font-size:1.1rem;font-weight:700;color:{cfg['color']};">
            {cfg['icon']} {cfg['label']}
        </div>
        <div style="font-size:0.85rem;color:#555;margin-top:3px;">
            {cfg['desc']}
        </div>
        {reason_html}
    </div>
    """


# --- 7. CLINICAL INSIGHTS PANEL ---
st.markdown("---")
st.subheader("📋 Clinical Insight Panel")

# If multiple mutations are selected, let the user select which one's clinical details to display
if len(selected_mutation_keys) > 1:
    insight_key = st.selectbox(
        "Select variant to view clinical annotations:",
        options=selected_mutation_keys
    )
else:
    insight_key = primary_mutation_key

# Get specific results and clinical insights for focus variant
focus_res = simulation_results[insight_key]
focus_mutation_data = focus_res["data"]
focus_features = focus_res["features"]
focus_warning = focus_res["warning"]

if focus_warning:
    st.warning(focus_warning)

rr_interval = estimate_rr_interval(pacing_period)
heart_rate = calculate_heart_rate(rr_interval)
insights = generate_clinical_insight(focus_mutation_data, ref_features, focus_features, heart_rate)

# Row 1: Primary Metrics Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="APD90 (QT Proxy)",
        value=insights["mutated_apd90"],
        delta=insights["apd90_change"],
        delta_color="inverse"
    )
with col2:
    st.metric(
        label="Nominal Heart Rate",
        value=insights["heart_rate"],
        delta="Paced (1 Hz)"
    )
with col3:
    st.metric(
        label="Likely Syndrome Match",
        value=insights["syndrome"]
    )

# Model Fidelity Badge
fidelity = focus_mutation_data.get("fidelity", "unsupported")
fidelity_html = _render_fidelity_badge(fidelity, active_model, focus_mutation_data)

# Evidence box + Fidelity badge
if insights["evidence_level"] != "N/A" or fidelity != "mechanistic":
    ev_col1, ev_col2 = st.columns([1, 1])
    with ev_col1:
        if insights["evidence_level"] != "N/A":
            st.markdown(
                f"""
                <div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:10px;
                            padding:14px 18px;margin-top:8px;">
                    <div style="font-size:0.78rem;font-weight:600;color:#6c757d;
                                 text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">
                        Evidence
                    </div>
                    <div style="font-size:1.05rem;font-weight:700;color:#2c3e50;margin-bottom:4px;">
                        {insights['evidence_level']}
                    </div>
                    <div style="font-size:0.85rem;color:#e74c3c;font-weight:600;">
                        ClinVar: {insights['clinvar_classification']}
                    </div>
                    <hr style="margin:8px 0;border-color:#dee2e6;">
                    <div style="font-size:0.78rem;color:#6c757d;">
                        <b>Inheritance:</b> {insights['inheritance']}<br>
                        <b>Reference:</b> <i>{insights['reference']}</i>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    with ev_col2:
        st.markdown(fidelity_html, unsafe_allow_html=True)
elif fidelity == "mechanistic" and insight_key != "Normal":
    st.markdown(fidelity_html, unsafe_allow_html=True)

# Row 2: Detailed Annotations
tab1, tab2, tab3 = st.tabs(["Variant Summary", "Mechanism", "Model Settings"])

with tab1:
    col_t1_1, col_t1_2 = st.columns(2)
    with col_t1_1:
        st.markdown(f"**Gene:** `{focus_mutation_data.get('gene', 'N/A')}`")
        st.markdown(f"**Mutation:** `{focus_mutation_data.get('mutation', 'N/A')}`")
        st.markdown(f"**Protein Modification:** `{insights['protein']}`")
        st.markdown("---")
        st.markdown(f"**Affected Channel:** `{insights['affected_channel']}`")
        st.markdown(f"**Current:** `{insights['current']}`")
        st.markdown(f"**AP Phase:** {insights['phase']}")
    with col_t1_2:
        st.markdown(f"**Syndrome:** {insights['syndrome']}")
        st.markdown(f"**Inheritance Mode:** {insights['inheritance']}")
        st.markdown(
            f"**ClinVar ID:** [`{insights['clinvar_id']}`]"
            f"(https://www.ncbi.nlm.nih.gov/clinvar/?term={insights['clinvar_id']})"
        )
        st.markdown(
            f"**OMIM Reference:** [`{insights['omim_id']}`]"
            f"(https://omim.org/entry/{insights['omim_id']})"
        )

    # Protein domain visualization
    protein_svg = _render_protein_domain(
        gene=focus_mutation_data.get("gene", ""),
        mutation=focus_mutation_data.get("mutation", ""),
        protein_length=insights["protein_length"],
        mutation_residue=insights["mutation_residue"]
    )
    if protein_svg:
        st.markdown("---")
        st.markdown("**Protein Domain Map**")
        st.markdown(protein_svg, unsafe_allow_html=True)

with tab2:
    st.markdown(f"**Functional Effect:** {insights['effect']}")
    st.markdown("")

    # Mechanism flowchart
    steps = insights.get("mechanism_steps", [])
    if steps:
        st.markdown("**Pathophysiological Cascade:**")
        flowchart_html = _render_mechanism_flowchart(steps)
        st.markdown(flowchart_html, unsafe_allow_html=True)
        st.markdown("")

    # Description + model approximation note
    if insights["description"]:
        st.info(insights["description"])

    if insights.get("model_approximation") and insights["model_approximation"] != "N/A":
        st.markdown(
            f"##### Beeler-Reuter Model Notes"
        )
        st.markdown(
            f"""
            <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:10px 14px;
                        border-radius:4px;font-size:0.87rem;color:#856404;margin-top:8px;">
                <b>⚠️ Model Approximation Note</b><br>
                {insights['model_approximation']}
            </div>
            """,
            unsafe_allow_html=True
        )

with tab3:
    st.markdown("**Simulation Configuration:**")
    st.code(insights["simulation_notes"], language="text")
    st.markdown(
        f"**Baseline APD90:** `{insights['normal_apd90']}` &nbsp;|&nbsp; "
        f"**Mutated APD90:** `{insights['mutated_apd90']}`"
    )

# Footer Disclaimer
st.warning(insights["disclaimer"])
