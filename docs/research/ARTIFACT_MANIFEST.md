# Artifact Manifest

**Manifest scope:** active research authorities, schema/config artifacts, registered current evidence reports, and checkpoint availability at the clean-v3 refactor.

**Base evidence commit:** `3aa9f0fd6b6f8f92395e3f4940b839859a84664d`

A present report is not automatically a final result. Evidence class and result boundary come from the owning config, `experiments/runs_v2.jsonl`, and `CLAIMS_LEDGER.md`. SHA-256 is raw checkout bytes unless a different form is explicitly shown.

## Refactor and research artifacts

| Artifact ID | Path | SHA-256 | Present | Role |
|---|---|---|---:|---|
| bible-v3 | `docs/research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md` | `f7bea8ad60cd7ba53dd40ea3a877914bd2b845a4d183080c5f75853828d778af` | yes | Exact byte copy of the 2026-08-23 research authority |
| literature-matrix-v3 | `docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx` | `ae173e281fbcbccae7da91920980f4d208a908d2f1a6a6dcfb54af5ebdf05ac3` | yes | Exact byte copy of the 100-source evidence matrix |
| claims-ledger-v1 | `docs/research/CLAIMS_LEDGER.md` | `ecef011aa16db41d071e6ada50f26376f79c377b2a4b809c942b7c40ad894c1b` | yes | Claim-to-run/config/evidence register |
| path-hash-policy-v1 | `docs/research/PATH_AND_HASH_POLICY.md` | `a232a24a9f4c5011fc37ce6849d0e36a71c29d882f1b09804c96cd0dfea79690` | yes | Canonical path, strict newline-equivalent hash rules, and registered-evidence attribute policy |
| runs-v2 | `experiments/runs_v2.jsonl` | `8316b4605a8564aabe6f20fbef330682e23a3d8be7a86e26fa7294a360542224` | yes | 22 current-protocol records, schema 2.0.0 |
| fd002-eda-v1 | `configs/evaluation/fd002-eda-v1.json` | `55b265de76c493529e4649e268ea7a773bc117b085f4a42c690dfa55b6bb1003` | yes | Training/validation-only descriptive EDA contract |
| fd002-eda-notebook-v1 | `notebooks/01_fd002_eda.ipynb` | `bd7823b2f9ee35a5309720bf22c41f8e82690091ac14edeb56b97e52c2599ede` | yes | Output-cleared notebook; execution pending absent inputs |

The migration manifest is intentionally not self-hashed.

## Preserved registered configs

| Config or manifest ID | Path | Checkout SHA-256 | Registered hash form | Evidence class | Present |
|---|---|---|---|---|---:|
| fd002-primary-v1 | `configs/splits/fd002-primary-v1.json` | `953f6bee71022a644fc0e3e155f4c212bb2cc9a10794c2665c9d7d9cb6594327` | raw | current protocol | yes |
| fd002-preprocessing-study-v1 | `configs/preprocessing/fd002-preprocessing-study-v1.json` | `a80a6b89b5af344662762567e390f0f9e8f712f822994596a06a952a3121612f` | raw | validation only | yes |
| fd002-preprocessing-selection-v1 | `configs/preprocessing/fd002-preprocessing-selection-v1.json` | `6ebb4ae018c154d970f9a7a3b64e96cc23b366ed4a269f720ccd6996fd5243c6` | LF registered as `4b71af5fd51cea9b90feda09e8d85ba502690e31efb3469fe20ad19482565086` | validation only | yes |
| fd002-classical-baselines-v1 | `configs/baselines/fd002-classical-baselines-v1.json` | `c565bc1ab540da4416deabc64d43bdc9bcb43f222f42325e9cd1157b5e67c697` | raw | validation proxy only | yes |
| fd002-lstm-screen-v1 protocol | `configs/lstm/fd002-lstm-screen-protocol-v1.json` | `e5744a5a4f22c6c953abc9b32f90967d4c871c73cb8d0a605bbb16d117395abe` | LF registered as `1d938ffd16c1024e1ff9767ccf9fefbaadb89919f67850051b15d6796a87f509` | validation proxy only | yes |
| fd002-lstm-screen-results-v1 | `configs/lstm/fd002-lstm-screen-results-v1.json` | `26d2e6e6215d9a3c3376642396754bfae0279c53f808b809672ffbc96db05694` | raw | validation proxy only | yes |

## Preserved current report bytes

| Evidence family | Path | Raw checkout SHA-256 | Evidence class | Present |
|---|---|---|---|---:|
| preprocessing | `reports/preprocessing/centroids.csv` | `371eed529074eb9ef234d4bd8a5511f92d25e387717f68770e858de6b28652fb` | validation only | yes |
| preprocessing | `reports/preprocessing/fit_summary.csv` | `26c6b2a1d42cf8c57df0d7d1922d9e6ea885ee624243e0da0d10908de1fbc183` | validation only | yes |
| preprocessing | `reports/preprocessing/model_selection.csv` | `1c289bf1d3772598a2d4bc37a0ee37c301b1a9b9337d089fc883c87b6fa93eef` | validation only | yes |
| preprocessing | `reports/preprocessing/occupancy.csv` | `ebc9c24318e40d032e197ecf7402fff3d4c6493471d73144738f168ff09a7e7d` | validation only | yes |
| classical | `reports/baselines_v2/model_selection.csv` | `9fd989c48f03e3bd9f0e1ef1da79df7d38d49d1e64d184bb180803bcebef666b` | validation proxy only | yes |
| classical | `reports/baselines_v2/policy_counts.csv` | `ee4a2b68c172107ea7961bfceefed339123df02152ef5dc469f17c4ea7da4402` | validation proxy only | yes |
| classical | `reports/baselines_v2/selected_models.csv` | `c4ad604a12bb4cf376c474bf22bf25c49a35202b60f022eb49399e879dfdcc9a` | validation proxy only | yes |
| classical | `reports/baselines_v2/validation_scores.csv` | `00e766880bb99c31656d1f10bd968590f0b94cb35e215d1e60299783aceed9ee` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/architecture_screen.csv` | `ea08361d92b605c76798b688af071b54467b6ff8d37a18d2c883408ec03ade06` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/execution_attempts.csv` | `26c173f4976ba68fd0a6d30ad4ba278d829db7eee7d1dbaa4ed77d3137514e31` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/experiment_rows.csv` | `e8001514cbb9620ab4fb6469af579a960f04b9c1ac6cb51211534dbaa0eb7178` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/model_selection.csv` | `d3619f8edb1d619c31b214a83a10b32b0b248c547b6d8229fac0622df777d015` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/monitor_engine_assignment.csv` | `11ba116bfb1038f802dab31bfabdb635099885bc25abd27d597906c684e6769f` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/robustness_summary.csv` | `cf9bddfa50871d43143470618b9f2addd5af33aa816b216f42af2c93244aad15` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/run_summary.csv` | `ce167e62630af354dd8634bebf6763dbb1893d5fb313334b7b6ee41115a86a38` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/training_history.csv` | `48fd5655aacb9afb9a52f44ea6e740b2352d905b5d4c3d84d48d501e0aecdd55` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/validation_scores.csv` | `be9c2a2cfcd441c59faceaa03aa94545f7f49990318476d671c11e2dd3b6414a` | validation proxy only | yes |
| LSTM | `reports/lstm_v2/verification_summary.csv` | `2e9c7789270374ebb34986f8121ee68181155441f5c7abef2f3e9ab79516c4b5` | validation proxy only | yes; LF registered as `d2daa7c23370df3ae272daa533953783f3fda12847d5ccf30839b5bc8490668b` |

## Registered data artifacts unavailable in this checkout

The clean clone intentionally omits raw and processed data. These identities are preserved from the registered split, baseline, and LSTM configurations; none was fetched or regenerated during the refactor.

| Artifact | Canonical path | Registered SHA-256 | Evidence class | Present |
|---|---|---|---|---:|
| FD002 training source | `data/raw/train_FD002.txt` | `bc1d293b8dc6173c1bfb0fff64fe797c2cde35dbb1a1a075dae8ca1177b49a52` | current protocol input | no |
| P0 training frame | `data/processed/preprocessing/p0_global/train.csv` | `5296840dbce62d1ed372c333fe3d990d9f2b55c798c77b092578f285bff34bc5` | current protocol input | no |
| P0 validation frame | `data/processed/preprocessing/p0_global/validation.csv` | `b39bf1101f309f73c5b79c432f053bd7b0744b0ea9abdbebfada67ef1493c6bc` | validation input | no |
| P1/K6 training frame | `data/processed/preprocessing/p1_k6/train.csv` | `dd58e35cc81289fbc372797896636cbe30ccf2bdac5c3b45439e754d1b586441` | current protocol input | no |
| P1/K6 validation frame | `data/processed/preprocessing/p1_k6/validation.csv` | `9918273195cedaaafe3287189256cc8042a7a50d6280e736c6278c5ba1e8d7e7` | validation input | no |
| Training window metadata | `data/processed/window_metadata_train.csv` | `a6a006e3d2dd1e6200a8fb9cbfdd8aabb82526c027368af8fb6aa5cd46574f19` | current protocol input | no |
| Validation window metadata | `data/processed/window_metadata_validation.csv` | `440fe967beb833f575379fd9f3d589e50858a5ae950da1a42ef469f93ef2618e` | validation input | no |
| P0 training sequences | `data/processed/sequences_v2/p0_global/train.npy` | `0e19d1aaabd17f167ed65a0dab77ab7ae966fc45fba1edec0c99647008376582` | current protocol input | no |
| P0 validation sequences | `data/processed/sequences_v2/p0_global/validation.npy` | `28b68d1efc6bde51f2b35f644dd96c9bd4384ea9be3eae5fd1d56dc4aedf8f61` | validation input | no |
| P1/K6 training sequences | `data/processed/sequences_v2/p1_k6/train.npy` | `b334c60a9f8280305874a8671ef6b43104e2644c5762eecb55b99b291769867e` | current protocol input | no |
| P1/K6 validation sequences | `data/processed/sequences_v2/p1_k6/validation.npy` | `a3ed2d89d7ff36daba68fb6f8eaa69ee92e12ff1264d393cf904d0d698cb58ec` | validation input | no |

## Registered model artifacts unavailable in this checkout

The reports/configs register these raw hashes, but the checkpoint model files are absent. The refactor did not fetch, rebuild, or substitute them.

**Evidence class for every model artifact below:** validation proxy only; none is a final or held-out-test artifact.

| Artifact ID | Canonical path | Registered SHA-256 | Present |
|---|---|---|---:|
| classical:p0:iforest | `models/baselines_v2/p0_global/isolation_forest.joblib` | `c2545d09c4299bcb1ed9b0c6ca519f64e50243281f68a4ff8b5803b08a6f64d6` | no |
| classical:p0:lof | `models/baselines_v2/p0_global/lof.joblib` | `2fef7a288136bd197e90470d86a35f05579a89711bed8b890b697f6435c4c6a1` | no |
| classical:p0:ocsvm | `models/baselines_v2/p0_global/one_class_svm.joblib` | `a519678c39f74e207292ed2abf76fabf0f3fcf11e34deea9fc61a773dfcbe8d0` | no |
| classical:p0:pca | `models/baselines_v2/p0_global/pca.joblib` | `a0fd7dc5e9a6ddfa35c5b10f3c6a23250d0983a0c752acb0162c9b32885ff8af` | no |
| classical:p1:iforest | `models/baselines_v2/p1_k6/isolation_forest.joblib` | `30d3072ddeea65f6314f45c02ba76e7c21ec9987b99955fa52d8300adaeed0db` | no |
| classical:p1:lof | `models/baselines_v2/p1_k6/lof.joblib` | `4ecc629adfdf54a76e803f4941ab95158879283a74026c06b9b7ec44389a671b` | no |
| classical:p1:ocsvm | `models/baselines_v2/p1_k6/one_class_svm.joblib` | `88cea19737b712f0116b97673ac935b759bfae7cc155789ac8dd07b789247cd5` | no |
| classical:p1:pca | `models/baselines_v2/p1_k6/pca.joblib` | `e575365a33109dbb586753f9b3768b9f2ff3ada519debc1582f0ca916cbf02e0` | no |
| fd002_lstm_v1_stage1_p1_k6_compact_32x8_l1_seed42 | `models/lstm_v2/fd002_lstm_v1_stage1_p1_k6_compact_32x8_l1_seed42.pt` | `98d7a9ed90b9e591a8b4080f8c88385f21efe48482b8868e69f11a645de8014b` | no |
| fd002_lstm_v1_stage1_p1_k6_balanced_64x16_l1_seed42 | `models/lstm_v2/fd002_lstm_v1_stage1_p1_k6_balanced_64x16_l1_seed42.pt` | `bfedeaaaaff6cdb6fe5298a64b088933493bde9a90e90f87c56efe8ee5afb262` | no |
| fd002_lstm_v1_stage1_p1_k6_stacked_64x16_l2_seed42 | `models/lstm_v2/fd002_lstm_v1_stage1_p1_k6_stacked_64x16_l2_seed42.pt` | `af2f720ec0c259e812051bac14cf2ebad65b6a8c8ba0d516f20d2bd2a6e7b80a` | no |
| fd002_lstm_v1_stage2_p0_global_balanced_64x16_l1_seed43 | `models/lstm_v2/fd002_lstm_v1_stage2_p0_global_balanced_64x16_l1_seed43.pt` | `32bf7ff2960567546f870738afd597ec2ea0dd5c302c94ddfdb83113dcc9cf83` | no |
| fd002_lstm_v1_stage2_p0_global_balanced_64x16_l1_seed44 | `models/lstm_v2/fd002_lstm_v1_stage2_p0_global_balanced_64x16_l1_seed44.pt` | `bbd1598c1d4ee0203a8d704ca1070bff4fab52fcf5fa802f577cb5f07e606727` | no |
| fd002_lstm_v1_stage2_p0_global_balanced_64x16_l1_seed45 | `models/lstm_v2/fd002_lstm_v1_stage2_p0_global_balanced_64x16_l1_seed45.pt` | `e5813e20235a423da69af412b0f1a38810b16b265329db02c9c59274f56a96fd` | no |
| fd002_lstm_v1_stage2_p1_k6_balanced_64x16_l1_seed43 | `models/lstm_v2/fd002_lstm_v1_stage2_p1_k6_balanced_64x16_l1_seed43.pt` | `afdcba8ccf1732e783ccb210c8d7f247b7f68479f7ce33e4a62f193f25484a45` | no |
| fd002_lstm_v1_stage2_p1_k6_balanced_64x16_l1_seed44 | `models/lstm_v2/fd002_lstm_v1_stage2_p1_k6_balanced_64x16_l1_seed44.pt` | `68c2268d6b7bc4700195d965d15f367df0336f4279239ecf041b26948e5df9dd` | no |
| fd002_lstm_v1_stage2_p1_k6_balanced_64x16_l1_seed45 | `models/lstm_v2/fd002_lstm_v1_stage2_p1_k6_balanced_64x16_l1_seed45.pt` | `c5e54fffbbeb459d57a6dd7fd908b2ac3beda78732374a2705c526a398bfc25f` | no |

## Access boundary

No held-out internal-test contents and no official NASA test data were opened, summarized, transformed, plotted, scored, or modeled while producing this manifest.
