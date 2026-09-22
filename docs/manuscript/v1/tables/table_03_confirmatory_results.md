# Table 3. Frozen internal held-out primary result

Display rounding: FAR/1,000 to 3 decimals, FAR percentage to 4 decimals, coverage to 2 decimals, delay to 0–1 decimals, and AUCs to 5 decimals; CSV retains source precision. Delay medians include detected engines only; missed engines remain in coverage. Aggregate delay is the median of the three proxy-specific medians (25 cycles), not a pooled engine-delay median.

<!-- canonical-sha256: 10d84602757e1798239ac5f087d4fe5a674f2d295173449f516370e40e7c2c77 -->

| Endpoint proxy | FP/healthy endpoints | FAR/1,000 | FAR (%) | Detected/engines | Coverage (%) | Median delay (cycles) | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|---|
| Final 10% | 265/8169 | 32.440 | 3.2440 | 27/52 | 51.92 | 12 | 0.60267 | 0.94762 |
| Final 20% | 67/7095 | 9.443 | 0.9443 | 41/52 | 78.85 | 25 | 0.80974 | 0.92673 |
| Final 30% | 31/6016 | 5.153 | 0.5153 | 44/52 | 84.62 | 42.5 | 0.82745 | 0.86758 |
