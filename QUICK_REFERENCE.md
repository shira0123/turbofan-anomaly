# Turbofan Anomaly Detection - Quick Execution Reference

## Pipeline Flowchart

```
📥 INPUT: raw_FD002.txt (26 columns × ~6000 rows)
   ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0: DATA PREPARATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▼
[1️⃣ make_splits.py]
   Input:  raw_FD002.txt
   Logic:  Split engines 70/30 (no leakage)
   Output: train.csv (70%), test.csv (30%)
   ▼
[2️⃣ fit_domain_adapter_and_save.py]
   Input:  train.csv
   Logic:  KMeans(op1,op2,op3) → 4 clusters
           Per-cluster StandardScaler on sensors
   Output: kmeans_clusterer.pkl, scaler_cluster_0-3.pkl
   ▼
[3️⃣ transform_and_save_processed.py]
   Input:  train.csv, test.csv + scalers/kmeans
   Logic:  Predict op_mode, apply per-mode scaling
   Output: train_domain_adapted.csv, test_domain_adapted.csv
           (new column: op_mode; sensor values: normalized)
   ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1: ANALYSIS (INFORMATIONAL, NO DOWNSTREAM IMPACT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▼
[4️⃣ run_eda.py] ← Parallel, optional
   Input:  train_domain_adapted.csv, test_domain_adapted.csv
   Output: reports/eda/*.csv *.png (stats, heatmaps, trends)
   ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2: WINDOWING & FEATURE EXTRACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▼
[5️⃣ create_sequences_save.py]
   Input:  train_domain_adapted.csv
   Logic:  Sliding windows [30 steps, 21 sensors]
           Step=1, healthy_fraction=0.3
           Result: ~40K windows
   Output: sequences_train.npy [40K,30,21]
           op_modes_train.npy [40K]
           is_healthy_train.npy [40K]
   ▼
   ┌────────────────────────┬────────────────────────┐
   ▼ (train healthy only)   ▼ (all windows)          
[6️⃣ run_baselines.py]  [7️⃣ train_lstm_smoke.py]
   │                        │
   ├─ Extract features      └─ Forward pass only
   │  [N, 63]                  on healthy windows
   │
   ├─ Isolation Forest      [8️⃣ export_lstm_scores.py]
   │  IF-score [N]             │
   │                           ├─ Load checkpoint
   ├─ LOF Novelty              ├─ Forward all windows
   │  LOF-score [N]            ├─ Compute MSE
   │                           └─ reconstruction_scores.csv
   └─ Evaluate metrics         [N, 4 cols]
      ROC-AUC, Prec@K, FAR    ▼
      → baseline_metrics.csv  [9️⃣ fit_adaptive_threshold.py]
                                 │
                                 ├─ Fit on healthy only
                                 ├─ Per-mode: μ, σ
                                 ├─ Threshold = μ + k*σ
                                 └─ adaptive_threshold.pkl
                                    threshold_summary.csv
   ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4: DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▼
[🔧 AnomalyService (src/api/main.py)]
   Artifacts loaded:
   - kmeans_clusterer.pkl
   - scaler_cluster_*.pkl (×4)
   - lstm_ae_*.pt (latest)
   - adaptive_threshold.pkl
   
   Inference:
   Input:  30-row window with [op1,op2,op3,sensor_1-21]
   └─ Domain adapt (op_mode + scale)
   └─ LSTM forward (reconstruction)
   └─ Compute MSE
   └─ Adaptive threshold (EWMA + consecutive violations)
   └─ Explain (top-3 sensors)
   Output: {"alert": bool, "score": float, "explanation": {...}}
   ▼
📊 OUTPUTS
```

---

## Detailed Step Summary

### Step 1: Data Split (make_splits.py)
| Aspect | Value |
|--------|-------|
| **Input** | raw_FD002.txt |
| **Output** | train.csv, test.csv |
| **Logic** | Engine-level 70/30 split (no engine leakage) |
| **Shape** | train: [~4200 rows], test: [~1800 rows] |
| **Key Insight** | Different engines = independent degradation histories |

### Step 2: Domain Adapter Fitting (fit_domain_adapter_and_save.py)
| Aspect | Value |
|--------|-------|
| **Input** | train.csv |
| **Output** | kmeans_clusterer.pkl, scaler_cluster_{0,1,2,3}.pkl |
| **Logic** | KMeans(n_clusters=4) on [op1, op2, op3] |
| **Per-Cluster** | StandardScaler fitted on 21 sensors |
| **Why** | Different operating conditions → different normal ranges |

### Step 3: Domain Adaptation (transform_and_save_processed.py)
| Aspect | Value |
|--------|-------|
| **Input** | train.csv, test.csv + fitted adapters |
| **Output** | train_domain_adapted.csv, test_domain_adapted.csv |
| **New Column** | op_mode (0, 1, 2, or 3) |
| **Transformation** | Sensors normalized per cluster (mean≈0, std≈1) |
| **Effect** | Removes operating-mode bias from sensor values |

### Step 4: EDA (run_eda.py)
| Aspect | Value |
|--------|-------|
| **Input** | domain_adapted CSVs |
| **Output** | 8 files (CSVs + PNGs) in reports/eda/ |
| **Key Metrics** | Silhouette score, correlation matrix, degradation trends |
| **Purpose** | Informational; doesn't affect downstream |

### Step 5: Windowing (create_sequences_save.py)
| Aspect | Value |
|--------|-------|
| **Input** | train_domain_adapted.csv |
| **Output** | sequences_train.npy, op_modes_train.npy, is_healthy_train.npy |
| **Window Size** | 30 timesteps |
| **Stride** | 1 (overlapping windows) |
| **Output Shape** | [~40,000 windows, 30 timepoints, 21 sensors] |
| **Healthy Label** | First 30% of engine life = 1, rest = 0 |

### Step 6: Baselines (run_baselines.py)
| Aspect | Value |
|--------|-------|
| **Input** | sequences, op_modes, is_healthy + metadata |
| **Output** | baseline_metrics.csv, experiments.csv entries |
| **Feature Extraction** | [mean, std, slope] per sensor → [63 features] |
| **Models** | Isolation Forest (n=300), LOF (k=35) |
| **Metrics** | ROC-AUC, Precision@K, FAR, Detection Delay, Coverage |
| **Training** | Healthy windows only |

### Step 7: LSTM Training (train_lstm_smoke.py)
| Aspect | Value |
|--------|-------|
| **Input** | sequences, is_healthy |
| **Output** | lstm_ae_*.pt, training_curve_*.csv |
| **Architecture** | 2-layer LSTM encode→16-dim latent→decode |
| **Capacity** | Input(21) → Hidden(64) → Latent(16) → Output(21) |
| **Training Data** | Healthy windows only (~30K-35K) |
| **Epochs** | 15 |
| **Optimizer** | Adam (lr=1e-3, weight_decay=1e-5) |
| **Loss** | MSE (reconstruction error) |

### Step 8: Score Export (export_lstm_scores.py)
| Aspect | Value |
|--------|-------|
| **Input** | lstm_ae_*.pt + all sequences |
| **Output** | reconstruction_scores.csv |
| **Computation** | Per-window MSE from LSTM reconstruction |
| **Output Shape** | [40,000 windows, 4 cols]: window_idx, op_mode, is_healthy, reconstruction_error |
| **Score Range** | Healthy: 0.01-0.05, Anomaly: 0.1-0.5+ |

### Step 9: Threshold Calibration (fit_adaptive_threshold.py)
| Aspect | Value |
|--------|-------|
| **Input** | reconstruction_scores.csv |
| **Output** | adaptive_threshold.pkl, threshold_summary.csv |
| **Calibration** | Per-mode: μ = mean(healthy_errors), σ = std(healthy_errors) |
| **Threshold** | μ + k*σ (k=2.5, so ~2.5 standard deviations) |
| **Adaptation** | EWMA smoothing (α=0.15) + decay (0.98) |
| **Alert Rule** | ≥3 consecutive violations above threshold |

---

## Input/Output Mapping

### Raw Inputs
- `data/raw/train_FD002.txt` — Raw sensor dataset (1 file)

### Intermediate Files
```
data/splits/
  ├── train.csv (step 1 output)
  └── test.csv (step 1 output)

models/
  ├── kmeans_clusterer.pkl (step 2 output)
  ├── scaler_cluster_0.pkl (step 2 output)
  ├── scaler_cluster_1.pkl (step 2 output)
  ├── scaler_cluster_2.pkl (step 2 output)
  ├── scaler_cluster_3.pkl (step 2 output)
  ├── lstm_ae_full_20260629_222541.pt (step 7 output)
  └── adaptive_threshold.pkl (step 9 output)

data/processed/
  ├── train_domain_adapted.csv (step 3 output)
  ├── test_domain_adapted.csv (step 3 output)
  ├── sequences_train.npy (step 5 output)
  ├── op_modes_train.npy (step 5 output)
  └── is_healthy_train.npy (step 5 output)

reports/
  ├── eda/
  │   ├── sensor_distribution_stats.csv (step 4)
  │   ├── op_mode_counts.csv (step 4)
  │   ├── cluster_validation.csv (step 4)
  │   ├── sensor_correlation_matrix.csv (step 4)
  │   ├── degradation_trends.csv (step 4)
  │   └── *.png (visualizations)
  ├── baselines/
  │   └── baseline_metrics.csv (step 6)
  └── lstm_ae/
      ├── training_curve_20260629_222541.csv (step 7)
      ├── reconstruction_scores.csv (step 8)
      └── threshold_summary.csv (step 9)

experiments/
  └── experiments.csv (appended by steps 6, 7, 9)
```

---

## Execution Command Quick Reference

```bash
# Setup environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run pipeline
python -m scripts.make_splits                          # Step 1
python -m scripts.fit_domain_adapter_and_save          # Step 2
python -m scripts.transform_and_save_processed         # Step 3
python -m scripts.run_eda                              # Step 4
python -m scripts.create_sequences_save                # Step 5
python -m scripts.run_baselines                        # Step 6
python -m scripts.train_lstm_smoke --full              # Step 7 (full=no smoke test)
python -m scripts.export_lstm_scores                   # Step 8
python -m scripts.fit_adaptive_threshold               # Step 9

# Test
pytest tests/test_api_inference.py

# Inference API
uvicorn src.api.main:app --reload
```

---

## Data Transformation Summary Table

| Step | Input Dimension | Output Dimension | Transformation Type |
|------|-----------------|------------------|---------------------|
| 1 | [N, 26] (1 file) | [N, 26] (2 files) | Split by engine ID |
| 2 | [N, 26] | (5 .pkl) | KMeans + scalers |
| 3 | [N, 26] | [N, 27] | Add op_mode, scale sensors |
| 4 | [N, 27] | (reports) | Statistics & charts |
| 5 | [N, 27] | [K, 30, 21] (K≈40K) | Windowing |
| 6 | [K, 30, 21] | [K, 63] then scores | Feature extraction |
| 7 | [K_healthy, 30, 21] | model.pt | Deep learning |
| 8 | model.pt | [K, 4] | LSTM forward pass |
| 9 | [K, 4] | 2 files | Threshold fitting |

---

## Key Variables & Their Meanings

| Variable | Meaning | Range |
|----------|---------|-------|
| **op_mode** | Operating condition cluster ID | 0-3 |
| **window_size** | Timesteps per window | 30 (fixed) |
| **sensor_*_** | Normalized sensor value | ≈ [-3, 3] (std units) |
| **reconstruction_error** | MSE between input & reconstruction | 0.01-0.5 |
| **is_healthy** | Label: 1=normal, 0=degraded | 0 or 1 |
| **threshold** | Per-mode alert boundary | Mode-specific |
| **smoothed_score** | EWMA-filtered reconstruction error | Continuous |
| **consecutive_violations** | Count of threshold exceedances | 0+ |

---

## File Dependencies

```
make_splits.py
  → train.csv, test.csv
    → fit_domain_adapter_and_save.py
        → kmeans_clusterer.pkl, scaler_cluster_*.pkl
          → transform_and_save_processed.py
              → train_domain_adapted.csv, test_domain_adapted.csv
                ├─→ run_eda.py
                │   → reports/eda/*
                │
                └─→ create_sequences_save.py
                    → sequences_train.npy, op_modes_train.npy, is_healthy_train.npy
                      ├─→ run_baselines.py
                      │   → baseline_metrics.csv
                      │
                      └─→ train_lstm_smoke.py
                          → lstm_ae_*.pt, training_curve.csv
                            → export_lstm_scores.py
                                → reconstruction_scores.csv
                                  → fit_adaptive_threshold.py
                                      → adaptive_threshold.pkl, threshold_summary.csv

Deployment:
  AnomalyService() loads:
    - kmeans_clusterer.pkl
    - scaler_cluster_*.pkl
    - lstm_ae_*.pt
    - adaptive_threshold.pkl
```

---

## Common Issues & Fixes

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| "No healthy windows available" | is_healthy_fraction=0.3 too small | Adjust healthy_fraction or data |
| Model overfits | Smoke mode (256 windows) used | Use `--full` flag in train |
| Threshold too loose | k=2.5 too small | Increase k or use more data |
| Threshold too strict | k=2.5 too large | Decrease k or check data distribution |
| Engine leakage | Scales fitted on test data | Always fit on train only |
| Low baseline scores | Features too simple | Baseline is intentionally simple; LSTM expected to improve |

