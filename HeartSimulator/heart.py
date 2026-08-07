import streamlit as st
import myokit
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. CONFIGURATION & UI ---
st.set_page_config(page_title="Cardiac Digital Twin", page_icon="🫀")
st.title("Cardiac Mutation Simulator")
st.markdown("""
    Type a mutation to see how it changes your heart cell's electrical 'pulse'.
    *Real-time simulation using the Beeler-Reuter (1977) Human Myocyte Model.*
""")

# --- 2. THE MUTATION LIBRARY ---
# In a real app, this connects to a database like ClinVar
MUTATION_DATABASE = {
    "SCN5A R1623Q": {"channel": "ina.gNaBar", "multiplier": 1.5, "syndrome": "Long QT Syndrome Type 3"},
    "KCNH2 N588K": {"channel": "isi.gsBar", "multiplier": 0.4, "syndrome": "Short QT Syndrome"},
    "Normal": {"channel": None, "multiplier": 1.0, "syndrome": "Healthy Heart"}
}

# Map common channel names to Beeler-Reuter (1977) model variables
CHANNEL_ALIASES = {
    "ina.gNa": "ina.gNaBar",
    "gNa": "ina.gNaBar",
    "ikr.gKr": "isi.gsBar",
    "gKr": "isi.gsBar",
    "gs": "isi.gsBar",
}

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("Input Genetic Data")
user_input = st.sidebar.selectbox("Select or Type Mutation", list(MUTATION_DATABASE.keys()))
mutation_data = MUTATION_DATABASE.get(user_input, {"channel": None, "multiplier": 1.0, "syndrome": "Unknown Mutation"})

# --- 4. HEART SIMULATION ENGINE (MYOKIT) ---
MYOKIT_DATA_DIR = Path(myokit.__path__[0]) / 'tests' / 'data'
MODEL_FILE = MYOKIT_DATA_DIR / 'beeler-1977-model.mmt'
PROTOCOL_FILE = MYOKIT_DATA_DIR / 'beeler-1977-protocol.mmt'

@st.cache_data # This keeps the website fast
def run_simulation(channel_name, multiplier):
    if not MODEL_FILE.exists() or not PROTOCOL_FILE.exists():
        raise FileNotFoundError(
            f"Myokit model or protocol file not found. Expected: {MODEL_FILE} and {PROTOCOL_FILE}"
        )

    model = myokit.load_model(str(MODEL_FILE))
    protocol = myokit.load_protocol(str(PROTOCOL_FILE))
    
    sim_normal = myokit.Simulation(model, protocol)
    log_normal = sim_normal.run(600)
    
    if channel_name:
        resolved_channel = CHANNEL_ALIASES.get(channel_name, channel_name)
        if model.has_variable(resolved_channel):
            var = model.get(resolved_channel)
            var.set_rhs(float(var.rhs()) * float(multiplier))
        else:
            st.warning(f"Channel '{channel_name}' is not in the Beeler-Reuter model.")
    
    sim_mutated = myokit.Simulation(model, protocol)
    log_mutated = sim_mutated.run(600)
    
    return log_normal, log_mutated

# --- 5. EXECUTION & RESULTS ---
try:
    with st.spinner('Simulating ion channels...'):
        normal, mutated = run_simulation(mutation_data['channel'], mutation_data['multiplier'])
except myokit.CompilationError as e:
    st.error('Simulation engine compilation failed.')
    st.markdown(
        'Myokit needs a C compiler on Windows. Install **Microsoft C++ Build Tools** and retry. '
        '[Download here](https://visualstudio.microsoft.com/visual-cpp-build-tools/).'
    )
    st.code(str(e), language='text')
    st.stop()

# Calculate "Plain English" metrics
normal_apd = len([v for v in normal['membrane.V'] if v > -70])
mutated_apd = len([v for v in mutated['membrane.V'] if v > -70])
diff = ((mutated_apd - normal_apd) / normal_apd) * 100

# --- 6. VISUALIZATION ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(normal['engine.time'], normal['membrane.V'], label="Normal", color="gray", alpha=0.5)
ax.plot(mutated['engine.time'], mutated['membrane.V'], label=f"Mutated ({user_input})", color="#ff4b4b", linewidth=2)
ax.set_ylabel("Voltage (mV)")
ax.set_xlabel("Time (ms)")
ax.legend()
st.pyplot(fig)

# --- 7. DIAGNOSTIC PANEL ---
st.subheader("Clinical Insight")
col1, col2 = st.columns(2)
with col1:
    st.metric("Pulse Duration Change", f"{diff:.1f}%")
with col2:
    st.info(f"**Likely Match:** {mutation_data['syndrome']}")

st.warning("This is a mathematical simulation for educational use at KMIT, not a medical diagnosis.")