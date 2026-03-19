<div align="center">

# 📊 Each_Market_Donation — Final Project Proposal

</div>

<div align="center">

**Step 1: Project Proposal (Due Thursday by 11:59pm)** ✅  
Final Project: Implementation + conference-style paper + design review ✍️🧠

</div>

---

## 👥 Team Members
- **Adarash** 
- **Barath** 
- **Smirti** 
- **Pranav**


---

## 🎯 Project Proposal (What we will build)

<div align="center">

### 📌 One-line idea
**We will build an interactive system that compares donor sentiment extracted from donation data (cumulative + non-cumulative, segmented by donor strength) against prediction-market signals extracted from trades (cumulative prediction odds) and Polymarket price movements.**

</div>

---

## 🧩 Data Science Problem

<div align="center">

Elections are influenced by both **who donates** and **what markets believe**. While donation data can reflect supporter sentiment, its effect is indirect and timing-dependent. Prediction markets aggregate beliefs—but they can be noisy or biased.

**Our concrete data science problem:**  
> *How well do donation sentiment signals (segmented + cumulative/non-cumulative) explain or predict the direction and magnitude of election probabilities implied by prediction markets and trade odds over time?*

</div>

---

## 📚 Main Dataset (Primary Source)

<div align="center">

We will use the dataset produced by the **`per_market_analysis` pipeline** in this repository. It contains per-election/event time series derived from donations and prediction markets:

- **Donation signals**
  - **Cumulative donation ratios** by segment (All / Small / Medium / Large)
  - **Non-cumulative donation ratios** by segment (period-specific, no carry-forward)
- **Prediction signals**
  - **Polymarket price history** (used to derive market-implied probability trajectories)
  - **Trade-based odds** from blockchain trades (investment-weighted prediction odds)

</div>

### 🧠 What the data represents
- Donation signals estimate the **Democratic share** via `Dem_Ratio` (Dem/(Dem+Rep))
- Non-cumulative ratios isolate sentiment shifts per time window
- Trade odds represent beliefs inferred from participants’ capital-weighted activity
- Polymarket prices represent market-implied probabilities over the same timeline

---

## ➕ At Least One Additional Data Source (Augmentation)

<div align="center">

We will augment with **external time-indexed election/political context** to reduce overfitting and help interpret whether improvements reflect real signal rather than spurious correlation.

**Option A (recommended): Polling averages**
- Source: public polling datasets / polling aggregates
- Why: provides an external proxy for changing election probabilities over time

**Option B: Demographic or geography context**
- Source: US Census-style demographic data
- Why: helps explain segment differences and improves interpretability

</div>

---

## 💡 Proposed Novel Solution

<div align="center">

### 🧠 “Signal Convergence Dashboard” (Interactive Evidence Workflow)
We propose an interactive, evidence-based workflow that:

1. **Aligns timelines** across donations (cumulative/non-cumulative), Polymarket prices, and trade odds
2. **Displays segment-level views** to reveal whether “small/medium/large donor” behavior drives market moves differently
3. **Computes lag/lead relationships** to test timing hypotheses:
   - Do donation sentiment changes appear *before* market odds changes?
   - Or does market movement lead donation behavior?
4. Adds interpretability and transparency by embedding:
   - what each curve shows
   - how each curve is calculated
   - plain-English guidance for interpretation

</div>

---

## 🛠️ Methodology (How we will solve it)

<div align="center">

### 1) Feature construction 📊
From the pipeline outputs, we will derive aligned time-series features per event:

- Donation cumulative segment ratios: `Dem_Ratio(segment, cumulative)`
- Donation non-cumulative segment ratios: `Dem_Ratio(segment, non-cumulative)`
- Polymarket price-derived odds trajectories
- Trade odds trajectories (investment-weighted)

### 2) Alignment + controlled smoothing (readability only)
For visualization and exploration, we will offer optional smoothing (e.g., moving average).  
**Evaluation will be done on the underlying unsmoothed series** to avoid bias.

### 3) Predictive evaluation
We will test hypotheses using time-series evaluation such as:

- **Lag correlation**: correlation of donation deltas vs odds deltas across multiple lead/lag windows
- **Directional accuracy**: whether donation signal changes predict the direction of market movement
- **Model comparisons**:
  - baseline: market-only or prior-only
  - donation-enhanced: cumulative vs non-cumulative vs segment-specific

### 4) Interpretability + story mode
The dashboard emphasizes interpretability:
- explanation panels for each visualization
- “what changed when” narratives per event
- consistent calculation documentation for auditability

</div>

---

## ✅ Evaluation Plan (How we’ll know it works)

<div align="center">

We will evaluate success using:

1. **Predictive signal quality**
   - Do donation signals (especially by segment) explain variation in market odds changes?
2. **Timing plausibility**
   - Do donation shifts lead market shifts (or vice versa)?
3. **Robustness**
   - Are results consistent across multiple events?
4. **Human interpretability**
   - Can a reader use the visualization to form coherent conclusions about drivers?

</div>

---

## 🎨 Why this is creative / novel

<div align="center">

This project combines:

- **segmented donation sentiment** (cumulative + non-cumulative)
- **two prediction modalities** (Polymarket price and blockchain trade odds)
- a UI designed for **timing/convergence analysis**, not only static charting
- interpretability that makes calculations auditable and understandable

</div>

---

## 📅 Timeline (High-level)

<div align="center">

- **Week 1–2:** finalize dataset alignment + augmentation plan
- **Week 2–3:** implement features and time-series evaluation metrics
- **Week 3–4:** build dashboard pages + explanation components
- **Week 4–5:** run experiments across events + iterate
- **Final:** produce paper + final presentation

</div>

---

## 🚀 Implementation Deliverable (What we will ship)

<div align="center">

- Streamlit interactive dashboard supporting:
  - cumulative donation segments
  - non-cumulative donation segments
  - cumulative prediction odds from trades (user analysis)
  - 4-signal summary convergence view (donation + prediction; cumulative + non-cumulative)
- Evaluation scripts/notebooks to generate:
  - lag/lead plots
  - predictive metrics per event
  - aggregated results for the paper

</div>

---

## ▶️ How to Run the Dashboard (Local)

<div align="center">

streamlit run per_market_analysis/UI/app.py

</div>