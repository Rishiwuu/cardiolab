# CardioLab: Cardiac Digital Twin Platform (Version 0.2)

CardioLab is an educational and research-oriented cardiac digital twin platform designed to simulate the biophysical electrical activity of human ventricular myocytes and explore how genetic variants alter cellular action potentials and resulting extracellular pseudo-ECG waveforms using a simplified transmural gradient model.

> [!WARNING]
> **Educational Disclaimer**
> CardioLab is a mathematical simulation tool for education and research. It is **NOT** a medical device, has not been evaluated by any regulatory body, and should not be used as clinical diagnostic advice or for patient treatment planning.

---

## 🏗️ Architectural Overview

CardioLab v0.2 is structured as a modular pipeline to separate concerns and maintain absolute independence among components.

```
CardioLab/
├── config.py                 # Global parameters, paths, database configurations
├── mutation_database.py      # Curated genetic mutations database with clinical annotations
├── simulation.py             # Biophysical simulation engine wrapping Myokit
├── features.py               # Feature extraction module (APD90, dV/dt_max, RMP)
├── ecg.py                    # Educational pseudo-ECG generator
├── clinical.py               # Clinical interpretation and insight formatter
├── utils.py                  # Helper functions (file verification)
├── app.py                    # Streamlit UI coordinator
├── tests/
│   └── test_modules.py       # Isolated test suite for all modules
└── requirements.txt          # Python dependency configuration
```

### Module Independence
* **Zero UI Dependencies in Compute Core**: None of the computation modules (`simulation.py`, `features.py`, `ecg.py`, `clinical.py`) import Streamlit. This ensures they can be run in batch jobs, automated tests, or external scripts.
* **Separation of Caching**: Streamlit's `@st.cache_data` is applied directly at the UI entry point (`app.py`), wrapping the compute modules.

---

## 🫀 The Pseudo-ECG Approximation (Transmural Difference Model)

### Scientific Rationale
A single cardiomyocyte simulation provides only local membrane potential $V_m(t)$ over time. A real electrocardiogram (ECG) measures the extracellular potential differences resulting from the propagation of electrical depolarization waves across millions of cells in the ventricular wall.

To create an educational, physically explainable ECG representation without running computationally expensive 3D tissue solvers, CardioLab implements a **transmural action potential difference model (two-cell dipole approximation)**. 

### Mathematical Formulation
The ventricles are represented as a virtual dipole consisting of an endocardial cell ($V_{\text{endo}}$) and an epicardial cell ($V_{\text{epi}}$):

1. **Endocardial Action Potential**: The simulated action potential is taken directly as the baseline endocardial potential:
   $$V_{\text{endo}}(t) = V_m(t)$$

2. **Epicardial Action Potential**: Epicardial cells depolarize later (due to the time it takes the electrical wavefront to propagate from endocardium to epicardial surface) and have a shorter Action Potential Duration (APD) due to higher transient outward potassium current ($I_{\text{to}}$) densities. We model this by shifting and compressing the endocardial potential:
   * For $t < t_{\text{dep}} + \Delta t_{\text{dep}}$:
     $$V_{\text{epi}}(t) = V_{\text{rest}}$$
   * For $t \ge t_{\text{dep}} + \Delta t_{\text{dep}}$:
     $$V_{\text{epi}}(t) = V_{\text{endo}}(\tau) \quad \text{where} \quad \tau = t_{\text{dep}} + (t - t_{\text{dep}} - \Delta t_{\text{dep}}) \cdot \alpha$$
   * *Where $\Delta t_{\text{dep}} = 20\text{ ms}$ is the transmural conduction delay.*
   * *Where $\alpha = 1.15$ is the epicardial APD compression factor (15% shorter APD).*
   * *$V_{\text{rest}}$ is the resting membrane potential, and $t_{\text{dep}}$ is the upstroke depolarization time ($dV/dt_{\max}$).*

3. **Extracellular Gradient (ECG)**: The extracellular potential (pseudo-ECG) is proportional to the spatial voltage gradient between the layers:
   $$\text{ECG}_{\text{raw}}(t) = V_{\text{endo}}(t) - V_{\text{epi}}(t)$$

4. **Normalization**: The signal is normalized to match standard clinical ECG amplitudes (QRS peak of $1.0\text{ mV}$):
   $$\text{ECG}(t) = \frac{\text{ECG}_{\text{raw}}(t)}{\max(|{\text{ECG}_{\text{raw}}}|)}$$

### Resulting Waveform Features
* **QRS Complex**: Depolarization starts in the endocardium first, causing $V_{\text{endo}} - V_{\text{epi}}$ to rise sharply (R-wave). As the wave depolarizes the epicardium, the difference returns to baseline (S-wave).
* **ST Segment**: During the action potential plateau, both cells are depolarized, making the voltage difference near-zero (isoelectric ST segment).
* **T-wave**: Because the epicardium repolarizes first (shorter APD) despite depolarizing later, the epicardial potential drops to rest while the endocardial potential remains elevated. This makes $V_{\text{endo}} - V_{\text{epi}}$ positive, producing an ECG-like waveform for educational visualization of depolarization and repolarization timing.

---

## 🚀 Running the Platform

### 1. Requirements Setup
Verify that your virtual environment is active and install dependencies:
```bash
pip install -r CardioLab/requirements.txt
```

### 2. Run Automated Unit Tests
To verify all modules in isolation:
```bash
python CardioLab/tests/test_modules.py
```

### 3. Run Streamlit Application
To launch the graphical explorer:
```bash
streamlit run CardioLab/app.py
```

---

## 🔮 Future Extension Points

CardioLab's modular architecture is designed to support the following upcoming expansions:

1. **Multi-Cellular 1D Fibers**: Expand `simulation.py` to support 1D multicellular tissue fibers, computing pseudo-ECGs using spatial integration over virtual lead positions.
2. **Drug Interaction Simulator**: Incorporate drug safety modeling (similar to CiPA) by scaling multiple conductances (e.g., $I_{\text{Kr}}$, $I_{\text{Na}}$, $I_{\text{CaL}}$) to simulate pharmacological QT prolongation.
3. **Advanced Models (O'Hara-Rudy & Ten Tusscher)**: Implement placeholder configurations in `config.py` with actual model and protocol files to simulate human-specific ventricular physiology.
4. **Multi-Mutation / Polygenic Risk**: Support simulating compound mutations by allowing multiple parameter modifications inside `simulation.py`.
5. **AI Diagnostic Explainer**: Integrate rule-based or classification networks to automatically interpret abnormal ECG waveforms and explain mechanisms in simple language.
6. **PDF Diagnostic Report**: Add reporting utilities to export digital twin profiles and simulated ECG charts to PDF.
7. **REST API Interface**: Wrap the simulation engine in a FastAPI web service, allowing web or mobile clients to request action potentials programmatically.

# CardioLab v0.2 (new)
.venv\Scripts\streamlit run CardioLab\app.py

# Original HeartSimulator (untouched, still works)
.venv\Scripts\streamlit run HeartSimulator\heart.py
