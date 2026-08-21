# Turbofan Anomaly Detection - Complete Codebase Execution Guide

## Project Overview
This is an unsupervised anomaly detection system for turbofan engines using the C-MAPSS FD002 dataset. It detects degradation patterns in sensor streams through reconstruction-based anomaly detection using LSTM autoencoders.

---

## Complete Execution Pipeline

### **PHASE 0: Data Preparation**

#### **Step 1: `make_splits.py`**
**Location:** `scripts/make_splits.py`

**Purpose:** Split raw turbofan data into train/test sets at the engine level

**Input:**
- `data/raw/train_FD002.txt` - Raw C-MAPSS FD002 dataset
  - Format: Whitespace-separated, 26 columns
  - Columns: engine, cycle, op1, op2, op3, sensor_1...sensor_21
  - Contains data from multiple turbofan engines with multiple operational cycles

**Processing Steps:**
1. Load raw CSV with 26 columns (engine, cycle, 3 operating conditions, 21 sensors)
2. Extract unique engine IDs and sort them
3. Calculate split index: 70% of unique engines → train, 30% → test
4. Filter dataframe by engine ID sets
5. Save both splits separately

**Output:**
- `data/splits/train.csv` (~70% of engines, all cycles from those engines)
  - Example: 100 engines total → 70 to train set
  - Contains all cycles for each train engine
- `data/splits/test.csv` (~30% of engines, all cycles from those engines)
  - Contains all cycles for each test engine

**Data Shape Changes:**
- Input: 1 file
- Output: 2 files
- Row count: ~6,000 cycles × 21 sensors (varies per dataset)

**Key Logic:**
- Engine-level split ensures no data leakage (same engine never in both train/test)
- Validation checks that no engine appears in both sets

---

#### **Step 2: `fit_domain_adapter_and_save.py`**
**Location:** `scripts/fit_domain_adapter_and_save.py`

**Purpose:** Learn operating condition clusters and per-cluster sensor normalizers

**Input:**
- `data/splits/train.csv` - Training split from Step 1

**Processing Steps:**
1. Load training data
2. Instantiate `OperatingConditionNormalizer(n_clusters=4)`
3. Fit KMeans clustering on operating condition columns (op1, op2, op3)
   - KMeans learns 4 cluster centroids from the 3D operating condition space
   - Each row assigned to nearest centroid
4. For each of the 4 clusters:
   - Filter training rows belonging to that cluster
   - Fit a `StandardScaler` on sensor columns for that cluster
   - Store scaler object

**Output:**
- `models/kmeans_clusterer.pkl` - Trained KMeans model with 4 centroids
- `models/scaler_cluster_0.pkl` - StandardScaler fitted on Cluster 0 sensors
- `models/scaler_cluster_1.pkl` - StandardScaler fitted on Cluster 1 sensors
- `models/scaler_cluster_2.pkl` - StandardScaler fitted on Cluster 2 sensors
- `models/scaler_cluster_3.pkl` - StandardScaler fitted on Cluster 3 sensors

**Data Flow Diagram:**
```
[train.csv]
  ↓
[Extract op1, op2, op3 columns]
  ↓
[KMeans.fit()] → [kmeans_clusterer.pkl]
  ↓
For each cluster 0-3:
  [Filter sensors by cluster]
    ↓
  [StandardScaler.fit()] → [scaler_cluster_X.pkl]
```

**Key Insight:**
- Different operating conditions have different normal sensor ranges
- Per-cluster scalers normalize sensors within their operating condition context
- Prevents false anomalies from different operating modes looking abnormal

---

#### **Step 3: `transform_and_save_processed.py`**
**Location:** `scripts/transform_and_save_processed.py`

**Purpose:** Apply domain adaptation (clustering + scaling) to train and test splits

**Input:**
- `data/splits/train.csv` - Original training split
- `data/splits/test.csv` - Original test split
- `models/kmeans_clusterer.pkl` - From Step 2
- `models/scaler_cluster_*.pkl` - From Step 2

**Processing Steps:**
1. Load train and test CSVs
2. Convert sensor columns to float type
3. Load saved KMeans and 4 scalers
4. For each dataset (train and test):
   a. Predict operating mode cluster for each row using KMeans
   b. Add new column: `op_mode` (0, 1, 2, or 3)
   c. For each cluster 0-3:
      - Identify rows with that op_mode
      - Apply corresponding scaler's transform() to sensor columns
      - Update sensor values with scaled versions
   d. Save modified dataframe

**Output:**
- `data/processed/train_domain_adapted.csv` - Training data with op_mode and scaled sensors
- `data/processed/test_domain_adapted.csv` - Test data with op_mode and scaled sensors

**Data Shape Changes:**
- New column: `op_mode` (integer 0-3)
- Sensor values: Now normalized per cluster (mean ≈ 0, std ≈ 1 within each cluster)

**Example Row Before/After:**
```
Before: engine=1, cycle=10, op1=0.002, op2=0.043, op3=150.0, sensor_1=643.2, ...
After:  engine=1, cycle=10, op1=0.002, op2=0.043, op3=150.0, op_mode=2, sensor_1=-0.523, ...
```

---

### **PHASE 1: Exploratory Data Analysis (EDA)**

#### **Step 4: `run_eda.py`**
**Location:** `scripts/run_eda.py`

**Purpose:** Generate statistical summaries and visualizations of processed data

**Input:**
- `data/processed/train_domain_adapted.csv`
- `data/processed/test_domain_adapted.csv`

**Processing Steps:**

1. **Sensor Distribution Stats**
   - Compute mean, std, min, 25%, 50%, 75%, max for each sensor
   - Compare train vs test statistics
   - Output: CSV with descriptive statistics

2. **Operating Mode Counts**
   - Count rows per operating mode (0, 1, 2, 3) in train and test
   - Create bar chart showing distribution
   - Output: CSV and PNG visualization

3. **Cluster Validation**
   - Compute Silhouette Score of KMeans clustering
   - Measures how well-separated clusters are in op-space
   - Output: CSV with single silhouette score metric

4. **Sensor Correlation Heatmap**
   - Compute Pearson correlation matrix across all 21 sensors
   - Visualize as color heatmap
   - Output: CSV correlation matrix + PNG heatmap image

5. **Degradation Trends**
   - Group each engine by life fraction (0=new, 1=end-of-life)
   - Calculate mean sensor value for 10 life bins
   - Identify key degradation indicators
   - Output: CSV trend data + line plot PNG

**Outputs:**
- `reports/eda/sensor_distribution_stats.csv` - Descriptive statistics
- `reports/eda/op_mode_counts.csv` - Mode distribution counts
- `reports/eda/op_mode_counts.png` - Bar chart
- `reports/eda/cluster_validation.csv` - Silhouette score
- `reports/eda/sensor_correlation_matrix.csv` - Correlation matrix
- `reports/eda/sensor_correlation_heatmap.png` - Correlation heatmap
- `reports/eda/degradation_trends.csv` - Trend data by life fraction
- `reports/eda/degradation_trends.png` - Trend line plot

**Note:** EDA is informational only; doesn't affect downstream processing

---

### **PHASE 2: Windowing for Sequence Modeling**

#### **Step 5: `create_sequences_save.py`**
**Location:** `scripts/create_sequences_save.py`

**Purpose:** Create sliding windows of sensor time series for LSTM training

**Input:**
- `data/processed/train_domain_adapted.csv` - Domain-adapted training data

**Processing Steps:**

1. Extract 21 sensor columns
2. For each engine in training data:
   a. Sort cycles in order
   b. Extract sensor array shape: [n_cycles, 21_sensors]
   c. Define "healthy window" as first 30% of engine's life (healthy_fraction=0.3)
   d. Slide 30-timestep window with stride=1 across entire engine:
      - Window[i]: rows[i:i+30] (30 timepoints × 21 sensors)
      - Store in sequences array
      - Record operating mode at window midpoint (cycle i+15)
      - Mark as healthy if window_end_cycle <= healthy_cutoff_cycle
   e. Move to next window (step=1)

3. Convert to numpy arrays:
   - Sequences: [N_windows, 30, 21] float32 array
   - Op modes: [N_windows] int array (0-3)
   - Is healthy: [N_windows] binary array (1=healthy, 0=anomaly)

**Example Window Creation:**
```
Engine 1 has 192 cycles
Healthy cutoff = 192 * 0.3 = 57 cycles
Max windows = 192 - 30 + 1 = 163 windows
Windows: [0:30], [1:31], [2:32], ... [162:192]
Healthy label: 1 if window_end <= 57, else 0
```

**Output:**
- `data/processed/sequences_train.npy` - Shape: [~40,000, 30, 21] windows
- `data/processed/op_modes_train.npy` - Shape: [~40,000] mode per window
- `data/processed/is_healthy_train.npy` - Shape: [~40,000] health labels

**Data Transformation:**
- Input: [n_cycles, 21] per engine
- Output: [n_windows, 30, 21] stacked across all engines

---

### **PHASE 2b: Baseline Anomaly Detection (Parallel)**

#### **Step 6: `run_baselines.py`**
**Location:** `scripts/run_baselines.py`

**Purpose:** Train and evaluate Isolation Forest and Local Outlier Factor models

**Input:**
- `data/processed/sequences_train.npy` - Windowed sequences
- `data/processed/is_healthy_train.npy` - Health labels
- `data/processed/op_modes_train.npy` - Operating modes
- `data/processed/train_domain_adapted.csv` - For metadata reconstruction

**Processing Steps:**

1. **Build Sequence Metadata:**
   - For each engine and each window, create metadata row
   - Columns: engine, local_window_idx, window_end, is_healthy, onset_idx
   - Tracks which cycle each window ends at, and degradation onset

2. **Extract Features from Sequences:**
   - Function: `sequence_summary_features()`
   - For each [30, 21] window, compute:
     - **Mean features**: mean across 30 timepoints for each sensor → [21]
     - **Std features**: std across 30 timepoints for each sensor → [21]
     - **Slope features**: sensor_value[last] - sensor_value[first] → [21]
   - Concatenate: [21_mean, 21_std, 21_slope] = [63 features]
   - Result: [N_windows, 63] feature matrix

3. **Train Isolation Forest:**
   - Filter healthy windows only
   - Contamination ratio from data (typically ~0.15-0.20)
   - `IsolationForest(n_estimators=300, contamination=contamination, n_jobs=-1)`
   - Fit on healthy windows
   - Score entire feature matrix (anomaly_score)

4. **Train LOF (Novelty Mode):**
   - Same data split and contamination
   - `LocalOutlierFactor(n_neighbors=35, contamination=contamination, novelty=True)`
   - Fit on healthy windows
   - Score entire feature matrix

5. **Evaluate Both Models:**
   - Compute ROC-AUC score
   - Compute Precision@K (K = number of anomaly windows)
   - Compute False Alarm Rate on healthy windows
   - Compute Mean Detection Delay: average windows until first positive after degradation onset
   - Compute Detection Coverage: % of engines with at least one positive detection

6. **Log Experiment:**
   - Write results to `experiments/experiments.csv`
   - Track: model name, parameters, metrics, artifact paths

**Output:**
- `reports/baselines/baseline_metrics.csv` - Metrics summary for both models
- `experiments/experiments.csv` - Updated with experiment entries (2 rows: IF, LOF)

**Typical Baseline Performance:**
- Isolation Forest: ROC-AUC ~0.72, Precision@K ~0.85
- LOF: ROC-AUC ~0.70, Precision@K ~0.85
- Both have ~60-65% false alarm rate on healthy data

---

### **PHASE 3: Deep Learning Anomaly Detection**

#### **Step 7: `train_lstm_smoke.py`**
**Location:** `scripts/train_lstm_smoke.py`

**Purpose:** Train an LSTM autoencoder on healthy window sequences

**Input:**
- `data/processed/sequences_train.npy` - All windowed sequences
- `data/processed/is_healthy_train.npy` - Health labels

**Processing Steps:**

1. **Load & Filter Healthy Windows:**
   - Load sequences [N, 30, 21]
   - Load health labels [N]
   - Filter to healthy windows only (is_healthy == 1)
   - If smoke mode: limit to first 256 windows (quick test)
   - If full: use all ~30,000-35,000 healthy windows

2. **Create Train/Valid Split:**
   - 90% train, 10% validation from healthy windows
   - Minimum 1 sample per set
   - Convert to PyTorch tensors (float32)

3. **Build Model Architecture:**
   ```
   LSTMAutoencoder:
   - Input: [batch, 30_timesteps, 21_sensors]
   - Encoder LSTM: 2 layers, 64 hidden units, dropout=0.2
   - Bottleneck: Linear(64 → 16) to latent code
   - Decoder LSTM: 2 layers, 64 hidden units
   - Output Linear: (64 → 21) per timestep
   - Output: [batch, 30, 21] reconstruction
   ```

4. **Training Loop (15 epochs default):**
   - Batch size: 64
   - Optimizer: Adam, lr=1e-3, weight_decay=1e-5
   - Loss: MSE between input and reconstruction
   - For each epoch:
     - Forward pass on train batches
     - Compute MSE loss
     - Backward pass, gradient descent
     - Evaluate on validation set
     - Track losses per epoch

5. **Save Artifacts:**
   - Model state dict and config → `models/lstm_ae_full_<timestamp>.pt`
   - Training curves → `reports/lstm_ae/training_curve_<timestamp>.csv`
   - Epoch-wise train/validation losses

**Output:**
- `models/lstm_ae_full_20260629_222541.pt` - Trained model checkpoint
- `reports/lstm_ae/training_curve_20260629_222541.csv` - Epoch losses
  - Columns: epoch, train_loss, valid_loss

**Typical Training Dynamics:**
- Train loss: ~0.15 → 0.08 (over 15 epochs)
- Valid loss: ~0.14 → 0.09
- Converges smoothly; model learns normal reconstruction patterns

---

#### **Step 8: `export_lstm_scores.py`**
**Location:** `scripts/export_lstm_scores.py`

**Purpose:** Run trained LSTM on all windows and compute reconstruction errors

**Input:**
- `models/lstm_ae_full_<timestamp>.pt` - Trained model (auto-finds latest)
- `data/processed/sequences_train.npy` - All sequences
- `data/processed/op_modes_train.npy` - Operating modes per window
- `data/processed/is_healthy_train.npy` - Health labels

**Processing Steps:**

1. **Load Latest Checkpoint:**
   - Find most recent `lstm_ae_*.pt` in models/
   - Load state dict
   - Instantiate model with saved config
   - Move to eval mode

2. **Compute Reconstruction Errors:**
   - For each window in sequences [N, 30, 21]:
     a. Forward pass through model
     b. Get reconstruction [30, 21]
     c. Compute MSE: mean((input - reconstruction)^2) over all 630 values
     d. Returns [N] error values
   - No gradients (with torch.no_grad())

3. **Create Output DataFrame:**
   - Columns: window_index, op_mode, is_healthy, reconstruction_error
   - Each row = one window + its error score
   - Sort by window index (preserved order)

**Output:**
- `reports/lstm_ae/reconstruction_scores.csv` - Per-window scores
  ```
  window_index,op_mode,is_healthy,reconstruction_error
  0,0,1,0.0234
  1,0,1,0.0198
  ...
  40000,2,0,0.1543
  ```

**Data Properties:**
- Healthy windows: low reconstruction errors (< 0.05 typically)
- Anomalous windows: higher reconstruction errors (0.1-0.5+)
- Error distribution used for threshold calibration in next step

---

### **PHASE 4: Adaptive Thresholding**

#### **Step 9: `fit_adaptive_threshold.py`**
**Location:** `scripts/fit_adaptive_threshold.py`

**Purpose:** Calibrate per-operating-mode anomaly thresholds from reconstruction scores

**Input:**
- `reports/lstm_ae/reconstruction_scores.csv` - From Step 8

**Processing Steps:**

1. **Filter Healthy Windows Only:**
   - From reconstruction_scores, keep only is_healthy==1 rows
   - These represent normal operation patterns

2. **Fit Baseline Parameters Per Mode:**
   - For each operating mode (0, 1, 2, 3):
     a. Filter reconstruction errors for that mode
     b. Compute μ (mean) of errors
     c. Compute σ (standard deviation) of errors
     d. Store both in AdaptiveThresholdEngine
   - Creates per-mode Gaussian baseline

3. **Create AdaptiveThresholdEngine:**
   - Parameters:
     - `alpha=0.15` - EWMA smoothing factor
     - `k=2.5` - Threshold = μ + k*σ (2.5 standard deviations above mean)
     - `m=3` - Require 3 consecutive violations for alert
     - `decay=0.98` - Exponential decay for online updates
     - `update_interval=50` - Recalibrate baseline every 50 steps
   - Instantiate and fit baseline parameters

4. **Save Engine & Summary:**
   - Save engine to `models/adaptive_threshold.pkl` (joblib)
   - For each mode, create summary row:
     - op_mode, healthy_windows_count, μ, σ, threshold
   - Save summary to CSV

**Output:**
- `models/adaptive_threshold.pkl` - Fitted AdaptiveThresholdEngine
- `reports/lstm_ae/threshold_summary.csv` - Per-mode threshold parameters
  ```
  op_mode,healthy_windows,mu,sigma,threshold
  0,8234,0.0245,0.0089,0.0468
  1,9123,0.0267,0.0102,0.0523
  2,7845,0.0201,0.0065,0.0414
  3,6234,0.0289,0.0115,0.0577
  ```

**Thresholding Logic (Inference):**
- When scoring a new window in mode X:
  1. Get threshold for mode X: μ_X + 2.5*σ_X
  2. Apply EWMA smoothing to raw error
  3. If smoothed_error > threshold for ≥3 consecutive windows → ALERT

---

## Inference & Production Deployment

### **API Service**

**Location:** `src/api/main.py`

**Class:** `AnomalyService`

**Artifacts Loaded:**
- `models/kmeans_clusterer.pkl`
- `models/scaler_cluster_*.pkl` (4 files)
- `models/lstm_ae_*.pt` (latest)
- `models/adaptive_threshold.pkl`

**Main Inference Flow:**

```python
service = AnomalyService()
window_records = [
    {"engine": 5, "cycle": 100, "op1": 0.002, "op2": 0.043, "op3": 150.0, "sensor_1": 643.2, ...},
    {"engine": 5, "cycle": 101, "op1": 0.002, "op2": 0.044, "op3": 150.1, "sensor_1": 644.1, ...},
    ...  # 30 rows
]

result = service.predict_window(window_records)
# Returns: {
#   "alert": False,
#   "score": 0.0287,
#   "threshold": 0.0468,
#   "op_mode": 0,
#   "reconstruction_error": 0.0287,
#   "smoothed_score": 0.0245,
#   "explanation": {
#     "shap_top3": [...],
#     "sensor_top3": [
#       {"sensor": "sensor_2", "error": 0.089},
#       {"sensor": "sensor_7", "error": 0.076},
#       {"sensor": "sensor_11", "error": 0.065}
#     ]
#   }
# }
```

**Inference Steps:**
1. **Prepare Window:**
   - Convert list of row dicts to DataFrame
   - Extract 30 rows × 21 sensors
   - Pass through domain adapter: predict op_mode + apply scaler
   - Result: [30, 21] normalized array

2. **Compute Reconstruction Error:**
   - Forward through LSTM AE
   - Get reconstruction [30, 21]
   - MSE: mean((input - reconstruction)^2)
   - Single scalar error value

3. **Threshold Decision:**
   - Get threshold for predicted op_mode from engine
   - Apply EWMA smoothing
   - Check if ≥ m consecutive violations
   - Return alert boolean

4. **Explain:**
   - Identify top-3 sensors by deviation from baseline
   - Compute SHAP values (if enabled)
   - Return explanations with service.explanation_payload()

---

## File Organization & Data Flow Summary

```
raw_FD002.txt
    ↓ [Step 1: make_splits]
data/splits/
    ├── train.csv (70% engines)
    └── test.csv (30% engines)
    
    ↓ [Step 2: fit_domain_adapter_and_save]
models/
    ├── kmeans_clusterer.pkl
    └── scaler_cluster_0.pkl through 3.pkl
    
    ↓ [Step 3: transform_and_save_processed]
data/processed/
    ├── train_domain_adapted.csv (with op_mode + scaled sensors)
    ├── test_domain_adapted.csv
    │
    ├─┬─ [Step 4: run_eda]
    │ └─→ reports/eda/*.csv, *.png
    │
    ├─┬─ [Step 5: create_sequences_save]
    │ └─→ data/processed/
    │     ├── sequences_train.npy
    │     ├── op_modes_train.npy
    │     └── is_healthy_train.npy
    │     
    │     ├─┬─ [Step 6: run_baselines]
    │     │ └─→ reports/baselines/baseline_metrics.csv
    │     │
    │     └─┬─ [Step 7: train_lstm_smoke]
    │       └─→ models/lstm_ae_*.pt + reports/lstm_ae/training_curve_*.csv
    │           ↓
    │           [Step 8: export_lstm_scores]
    │           └─→ reports/lstm_ae/reconstruction_scores.csv
    │               ↓
    │               [Step 9: fit_adaptive_threshold]
    │               └─→ models/adaptive_threshold.pkl + reports/lstm_ae/threshold_summary.csv

Inference:
    AnomalyService loads all .pkl and .pt artifacts
    predict_window(30-row window) → {"alert": bool, "score": float, ...}
```

---

## Key Data Transformations

| Step | Input Shape | Output Shape | Key Transformation |
|------|------------|--------------|-------------------|
| 1    | 1 raw file | 2 CSVs | Engine-level split |
| 2    | train.csv [6000, 26] | 5 .pkl files | KMeans + StandardScaler per cluster |
| 3    | 2 CSVs | 2 CSVs [6000, 27] | Add op_mode, scale sensors |
| 4    | 2 CSVs | EDA reports | Statistics & visualizations |
| 5    | 1 CSV [6000, 27] | 3 .npy arrays | Sliding windows: [40000, 30, 21] |
| 6    | 3 .npy arrays | metrics CSV | Feature extraction + IF/LOF |
| 7    | 3 .npy arrays | model.pt | LSTM training |
| 8    | model.pt + 3 .npy | scores CSV [40000, 4] | Forward pass → MSE |
| 9    | scores CSV | 2 files | Threshold calibration per mode |

---

## Important Notes

### Data Leakage Prevention
- Engine-level split (Step 1) ensures no engine appears in both train and test
- Domain adapter fitted only on training data (Steps 2-3)
- Baselines and LSTM trained only on training healthy windows

### Anomaly Definition
- First 30% of each engine's life = "healthy"
- Remaining 70% = "anomalous" (degradation phase)
- Reconstruction error expected to rise as engine degrades

### Operating Modes
- KMeans groups 3 continuous variables (op1, op2, op3) into 4 discrete modes
- Modes roughly correspond to: Low Power, Medium Load, High Load, High Altitude
- Different modes have different normal sensor ranges (hence per-mode scaling and thresholds)

### Model Selection
- LSTM AE over Isolation Forest because:
  - Captures temporal dependencies in sequences
  - Learns distributed representations of degradation
  - Reconstruction error is more interpretable than anomaly scores
  - Better generalization to unseen degradation patterns

### Threshold Strategy
- Adaptive thresholding (not fixed threshold) because:
  - Different modes have different error distributions
  - EWMA smoothing reduces noise
  - Consecutive violation requirement reduces false positives
  - Online updates (decay) adapt to changing conditions

---

## Running the Complete Pipeline

```bash
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Place data
# data/raw/train_FD002.txt

# Execute pipeline in order
python -m scripts.make_splits
python -m scripts.fit_domain_adapter_and_save
python -m scripts.transform_and_save_processed
python -m scripts.run_eda
python -m scripts.create_sequences_save
python -m scripts.run_baselines
python -m scripts.train_lstm_smoke --full  # Full training
python -m scripts.export_lstm_scores
python -m scripts.fit_adaptive_threshold

# Test inference
pytest tests/test_api_inference.py

# Run inference service
# (FastAPI app in src/api/main.py)
uvicorn src.api.main:app --reload
```

---

## Testing

**Test File:** `tests/test_api_inference.py`

**Test Case:** `test_predict_window_returns_alert_payload()`
- Loads 30 rows from train.csv
- Calls `service.predict_window(window_records)`
- Validates output structure:
  - alert (bool)
  - score (float)
  - threshold (float)
  - op_mode (int)
  - reconstruction_error (float)
  - explanation (dict with top-3 sensors)

---

## Experiment Tracking

**File:** `experiments/experiments.csv`

**Logged Per Script:**
- Baseline models: 2 entries (IF, LOF)
- LSTM training: 1 entry
- Threshold calibration: 1 entry

**Columns:** run_id, datetime, owner, experiment_name, model_name, params, train_size, valid_size, metric_name, metric_value, notes, artifact_path

---

## Summary

This pipeline implements a **production-ready anomaly detection system**:

1. **Preprocessing** (Steps 1-3): Data cleaning, context-aware normalization
2. **Exploration** (Step 4): Statistical understanding of data
3. **Feature Engineering** (Step 5): Temporal windowing for sequences
4. **Baselines** (Step 6): Reference performance metrics
5. **Deep Learning** (Steps 7-8): LSTM reconstruction-based detection
6. **Calibration** (Step 9): Adaptive thresholding per context
7. **Deployment** (API): Real-time inference with explanations

Each step has clear inputs, outputs, and purposes, enabling reproducibility, debugging, and extension.
