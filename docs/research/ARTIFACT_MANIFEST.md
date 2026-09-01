# Artifact Manifest

**Manifest scope:** active research authorities, schema/config artifacts, registered current evidence reports, and checkpoint availability at the clean-v3 refactor.

**Base evidence commit:** `3aa9f0fd6b6f8f92395e3f4940b839859a84664d`

A present report is not automatically a final result. Evidence class and result boundary come from the owning config, `experiments/runs_v2.jsonl`, and `CLAIMS_LEDGER.md`. SHA-256 is raw checkout bytes unless a different form is explicitly shown.

## Refactor and research artifacts

| Artifact ID | Path | SHA-256 | Present | Role |
|---|---|---|---:|---|
| bible-v3 | `docs/research/MASTER_EXECUTION_BIBLE_V3_RESEARCH_IMPLEMENTATION_2026-08-23.md` | `f7bea8ad60cd7ba53dd40ea3a877914bd2b845a4d183080c5f75853828d778af` | yes | Exact byte copy of the 2026-08-23 research authority |
| literature-matrix-v3 | `docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx` | `ae173e281fbcbccae7da91920980f4d208a908d2f1a6a6dcfb54af5ebdf05ac3` | yes | Exact byte copy of the 100-source evidence matrix |
| claims-ledger-v1 | `docs/research/CLAIMS_LEDGER.md` | `1918fd226f77b3cd903eaeb83d3b2d157405b91eca72a98c0de09944536e8ffa` | yes | Claim-to-run/config/evidence register, including bounded recovery and v2 readiness evidence |
| path-hash-policy-v1 | `docs/research/PATH_AND_HASH_POLICY.md` | `a232a24a9f4c5011fc37ce6849d0e36a71c29d882f1b09804c96cd0dfea79690` | yes | Canonical path, strict newline-equivalent hash rules, and registered-evidence attribute policy |
| runs-v2 | `experiments/runs_v2.jsonl` | `15869481cb757d8a9c6485f47084bf96906f51fe2c8e72f43f5127b0a5e56970` | yes | 29 current-protocol records, schema 2.0.0; seven final-refit records added |
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

## Final LSTM refit evidence — 2026-08-25

Every metric below is a validation-proxy diagnostic, not a final-test result. The registered protocol remained immutable at execution. The result config and reports are tracked evidence; the three model binaries are local and ignored by Git.

| Artifact | Path | Raw SHA-256 | Present | Tracking / role |
|---|---|---|---:|---|
| Final-refit protocol | `configs/lstm/fd002-lstm-final-refit-protocol-v1.json` | `e6606707665e39e4b58996ce84d987e546b51d8563be0ef90dc698ac4c5a2b97` | yes | Tracked; registered before execution |
| Final-refit result | `configs/lstm/fd002-lstm-final-refit-results-v1.json` | `7567d86b9f78fa2913a3d83025a1d5a71af1c887d6f4ec296d7527a1947bd09e` | yes | Tracked evidence; completed, no threshold/test access |
| Artifact manifest report | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/artifact_manifest.csv` | `79b2429e810e07c0c6c90184d6cbd630ae860299e5bc597e09259b2a2240890e` | yes | Tracked evidence |
| Classical comparison | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/classical_comparison.csv` | `ce02986ffae6b58a4c1c03f27916473ebd528d290892588df4c9881a4456f088` | yes | Tracked validation-proxy evidence |
| Convergence engine assignment | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/convergence_engine_assignment.csv` | `11ba116bfb1038f802dab31bfabdb635099885bc25abd27d597906c684e6769f` | yes | Tracked training-only evidence |
| Convergence history | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/convergence_history.csv` | `b4b5093b227a18d9544296b20d342c6552dbee13e28cf9e5934678212731ffcf` | yes | Tracked training-only evidence |
| Convergence summary | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/convergence_summary.csv` | `4f5572721a71901c9173c7611a9c0306ee19fc75f9f431f68eafec89647310a9` | yes | Tracked training-only evidence |
| Ensemble validation scores | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/ensemble_validation_scores.csv` | `0ae618f8654f5f5f30a8c5ac820b97e34d40ea330fa4a0bb745c2e1e2b07e3a3` | yes | Tracked validation-proxy evidence |
| Epoch lock | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/epoch_lock.csv` | `39e6410fce020eceb299fe95ea2e2319b57ed4fe9cba86aecb61eaa1d27f643d` | yes | Tracked training-only evidence; locked epoch 54 |
| Locked-refit training history | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/locked_refit_training_history.csv` | `d0964357c95787e4312c1b3018f6f3cb5802d55137e23cb1b61abdbb12752b82` | yes | Tracked training-only evidence |
| Ranking metrics | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/ranking_metrics.csv` | `f3e574e554231e705031f18e06119b61b7bf7e133365785167508988fa16ffca` | yes | Tracked validation-proxy evidence |
| Reload verification | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/reload_verification.csv` | `16d6788b16e173777b52d99ac6e312b3870b3b70fa3a0680f5aaa55bde1fb8b4` | yes | Tracked evidence |
| Run summary | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/run_summary.csv` | `eac44aa68af77e37c30dcd2c57cfa65a74578450736717c22c324faa6863eda9` | yes | Tracked validation-proxy evidence |
| Runtime provenance | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/runtime_provenance.json` | `91d3cf16735cd3cdec31d3d28bd9415d225b98f31c6f7503fc481424dfc27c61` | yes | Tracked provenance |
| Per-seed validation scores | `reports/lstm_final_v1/fd002-lstm-final-refit-v1/validation_scores.csv` | `421d8f169a8bfc4a8abfc051887293590dd21e9f27fb2fe2518bf99ffefb9ca2` | yes | Tracked validation-proxy evidence |
| Final LSTM seed 43 | `models/lstm_final_v1/fd002-lstm-final-refit-v1/fd002_lstm_final_v1_locked_p1_k6_balanced_64x16_l1_seed43.pt` | `7a0a84dc11a1d5e2c21d8ccdc4be0385a844d24146be4d27fb7d47b3df8cda2e` | yes | Local/untracked model artifact |
| Final LSTM seed 44 | `models/lstm_final_v1/fd002-lstm-final-refit-v1/fd002_lstm_final_v1_locked_p1_k6_balanced_64x16_l1_seed44.pt` | `9f8406e39eda123f8878bcf58cec5e99c478e6d2d34f7ebbfff73a9a116e40e5` | yes | Local/untracked model artifact |
| Final LSTM seed 45 | `models/lstm_final_v1/fd002-lstm-final-refit-v1/fd002_lstm_final_v1_locked_p1_k6_balanced_64x16_l1_seed45.pt` | `86f4a993fc5247cfb7bacdfb7680ce6cb3a8dceb7d0059bf1f445c5d80e1a2b4` | yes | Local/untracked model artifact |

## Registered data artifact availability

The clean clone still omits raw and most processed data. Four final-refit training/validation inputs were copied from the approved old project source only after exact registered-hash verification; they remain local and ignored by Git. No data was regenerated or downloaded.

| Artifact | Canonical path | Registered SHA-256 | Evidence class | Present |
|---|---|---|---|---:|
| FD002 training source | `data/raw/train_FD002.txt` | `bc1d293b8dc6173c1bfb0fff64fe797c2cde35dbb1a1a075dae8ca1177b49a52` | current protocol input | no |
| P0 training frame | `data/processed/preprocessing/p0_global/train.csv` | `5296840dbce62d1ed372c333fe3d990d9f2b55c798c77b092578f285bff34bc5` | current protocol input | no |
| P0 validation frame | `data/processed/preprocessing/p0_global/validation.csv` | `b39bf1101f309f73c5b79c432f053bd7b0744b0ea9abdbebfada67ef1493c6bc` | validation input | no |
| P1/K6 training frame | `data/processed/preprocessing/p1_k6/train.csv` | `dd58e35cc81289fbc372797896636cbe30ccf2bdac5c3b45439e754d1b586441` | current protocol input | yes; local/ignored |
| P1/K6 validation frame | `data/processed/preprocessing/p1_k6/validation.csv` | `9918273195cedaaafe3287189256cc8042a7a50d6280e736c6278c5ba1e8d7e7` | validation input | yes; local/ignored |
| Training window metadata | `data/processed/window_metadata_train.csv` | `a6a006e3d2dd1e6200a8fb9cbfdd8aabb82526c027368af8fb6aa5cd46574f19` | current protocol input | yes; local/ignored |
| Validation window metadata | `data/processed/window_metadata_validation.csv` | `440fe967beb833f575379fd9f3d589e50858a5ae950da1a42ef469f93ef2618e` | validation input | yes; local/ignored |
| P0 training sequences | `data/processed/sequences_v2/p0_global/train.npy` | `0e19d1aaabd17f167ed65a0dab77ab7ae966fc45fba1edec0c99647008376582` | current protocol input | no |
| P0 validation sequences | `data/processed/sequences_v2/p0_global/validation.npy` | `28b68d1efc6bde51f2b35f644dd96c9bd4384ea9be3eae5fd1d56dc4aedf8f61` | validation input | no |
| P1/K6 training sequences | `data/processed/sequences_v2/p1_k6/train.npy` | `b334c60a9f8280305874a8671ef6b43104e2644c5762eecb55b99b291769867e` | current protocol input | yes; local/ignored |
| P1/K6 validation sequences | `data/processed/sequences_v2/p1_k6/validation.npy` | `a3ed2d89d7ff36daba68fb6f8eaa69ee92e12ff1264d393cf904d0d698cb58ec` | validation input | yes; local/ignored |

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

## Phase 5 alert-policy evidence — 2026-08-27

Every result below is validation-proxy operational evidence, not final-test performance. The v1 protocol is preserved as blocked; v2 changes only window-context metadata lineage. Generated model bundles remain local and ignored.

| Artifact | Path | Raw SHA-256 | Present | Tracking / role |
|---|---|---|---:|---|
| Blocked Phase 5 protocol v1 | `configs/alerting/fd002-alert-policy-study-protocol-v1.json` | `9734c465071401387f7ad2fc79abfc207d0eeb0e8724685267f74b7528f8cb6c` | yes | Tracked; blocked by missing window-context lineage |
| Corrected Phase 5 protocol v2 | `configs/alerting/fd002-alert-policy-study-protocol-v2.json` | `47f165b7c35b772ee776e938d10dffd4af24dc3d069f34581ee11391918d6ff5` | yes | Tracked; registered before corrected execution |
| Phase 5 result | `configs/alerting/fd002-alert-policy-study-results-v1.json` | `57080e52d05d6b95747c831fcf819a606d334cf874257421847a5c24aacb8ac2` | yes | Tracked validation-only result; policy subsequently frozen at Gate 4 |
| P1/K6 endpoint-context train metadata | `data/processed/window_context/p1_k6/train.csv` | `78ad3855b62bdcda51d0232bfa78f0adf6c858475b7a6dd8a256debfcab2268f` | yes | Local/ignored; derived from registered endpoint modes |
| P1/K6 endpoint-context validation metadata | `data/processed/window_context/p1_k6/validation.csv` | `318dfc7b303cd9b2dc29656b36211922464580a92c9520db06cf437d77b2a692` | yes | Local/ignored; derived from registered endpoint modes |
| Report artifact manifest | `reports/alerting_v1/fd002-alert-policy-study-v1/artifact_manifest.csv` | `759b17a7e818f956e1abc3930ebf833988795402f8d8abe790d1ec983121edc2` | yes | Tracked evidence |
| Per-detector winners | `reports/alerting_v1/fd002-alert-policy-study-v1/best_policy_per_detector.csv` | `91f97e39398c390841b5a0a2e5b41f84aa98aa32165ed7b6fc4fd416fc49517d` | yes | Tracked validation evidence |
| Candidate-policy metrics | `reports/alerting_v1/fd002-alert-policy-study-v1/candidate_policy_metrics.csv` | `da98b18f617fcbef3724764016671d62646dc613ceb4a7825b94325fe2a178e5` | yes | Tracked exhaustive metric evidence |
| Candidate selection trace | `reports/alerting_v1/fd002-alert-policy-study-v1/candidate_selection.csv` | `5f895859745ae37546d55e68244ffc932598455c80bec9f5cd506d1f0d538477` | yes | Tracked selection evidence |
| Candidate registry | `reports/alerting_v1/fd002-alert-policy-study-v1/candidates.csv` | `26d4e3f99701de2ea8897413dd126cb9fdd03814773b7722d36e409492a47681` | yes | Tracked grid evidence |
| Detector complementarity | `reports/alerting_v1/fd002-alert-policy-study-v1/detector_complementarity.csv` | `2bb9f0c4a7aa1adacf1e8bb435b1fb5b72bb23604fd6b24d954c889ea8a97153` | yes | Tracked; no fusion evaluated |
| Overall recommendation | `reports/alerting_v1/fd002-alert-policy-study-v1/overall_recommendation.csv` | `420bc1f7c07af0f1e1133c8de95f80f88eb6ef24ea6f7678939438a8e6d5e0f2` | yes | Tracked; approved and frozen at Gate 4 |
| Per-engine metrics | `reports/alerting_v1/fd002-alert-policy-study-v1/per_engine_metrics.csv` | `63e5b91800e6fcc319c8409610d7a0304fd3a91ee6eb99709c2584edff3deae9` | yes | Tracked validation evidence |
| Runtime provenance | `reports/alerting_v1/fd002-alert-policy-study-v1/runtime_provenance.json` | `b74fc74c80ddc739757b7e38911ffb20bda265bf35dfccb8f324995704dabc86` | yes | Tracked provenance; CUDA execution |
| Selected events | `reports/alerting_v1/fd002-alert-policy-study-v1/selected_events.csv` | `dc098034e793d0ca512bd2c6f7ca8474e7133fdb4fb233987483559e97c0f904` | yes | Tracked event evidence |
| Selected validation alert trace | `reports/alerting_v1/fd002-alert-policy-study-v1/selected_validation_alert_trace.csv` | `1db558a8026e7ea9841ff56c90215c3835aa1b95208c98b49a07d8221c07219c` | yes | Tracked validation-only trace |
| Target attainment | `reports/alerting_v1/fd002-alert-policy-study-v1/target_attainment.csv` | `72a34a1e3e39fccc68d2d5bee7694fe11c6c66bd3f68cdcb4ebb166fd7645a3d` | yes | Tracked target evidence |
| Threshold table | `reports/alerting_v1/fd002-alert-policy-study-v1/threshold_table.csv` | `c6e6a1e1d4f3842fa6e16bd41436e0a1c00764d1e32dcec0d304f3aa7164681e` | yes | Tracked training-derived thresholds |
| Training score reference | `reports/alerting_v1/fd002-alert-policy-study-v1/training_score_reference_summary.csv` | `162b7f8f1c48f82aa30a2b46b51a7d29c5f9bdc95bf19b888f92ddcf05e7d3de` | yes | Tracked training-only reference |
| Score reproduction | `reports/alerting_v1/fd002-alert-policy-study-v1/validation_score_reproduction_summary.csv` | `8d88352fb0b90ca95846e53edca8a7be8225716ad8b6aad767304a00723c5864` | yes | Tracked validation reproduction evidence |
| Verification summary | `reports/alerting_v1/fd002-alert-policy-study-v1/verification_summary.csv` | `0da109ef11510641b95955307ffa015f39a5699c9eb0c28a6f688fb2a3e3e3a2` | yes | Tracked evidence |
| Reproduced LOF bundle | `models/alerting_v1/fd002-alert-policy-study-v1/lof.joblib` | `58ec2509bf1827c70b408287991843a10f1043d02353af335812ab3f7ccd2610` | yes | Local/ignored; reproduction, not retuning |
| Reproduced One-Class SVM bundle | `models/alerting_v1/fd002-alert-policy-study-v1/one_class_svm.joblib` | `d21b4b441462a543e6288bb8f1e84b0b509c0cef406635dfe532a0d74affb384` | yes | Local/ignored; reproduction, not retuning |
| Reproduced Isolation Forest bundle | `models/alerting_v1/fd002-alert-policy-study-v1/isolation_forest.joblib` | `0c62302b2689c8b026bdd56227e0c6c181c57450c10d3abdbed52adfc2ae162a` | yes | Local/ignored; reproduction, not retuning |
| Reproduced PCA bundle | `models/alerting_v1/fd002-alert-policy-study-v1/pca_reconstruction.joblib` | `d56a6d41e63c0781da763565f71c4a13b144eacd487a351428113c8ebf2ba9aa` | yes | Local/ignored; reproduction, not retuning |
| LSTM ensemble bundle | `models/alerting_v1/fd002-alert-policy-study-v1/lstm_calibrated_ensemble.json` | `efae8c17a834d5837aef2b09281ded44f90da700b462978436965888c5932588` | yes | Local/ignored; frozen calibrated aggregation |
| Run ledger after Phase 5 | `experiments/runs_v2.jsonl` | `22838b7321ed5d246852b95fd7f43880769bddb97ece30005c0e06bb8bdc23fe` | yes | Tracked; six Phase 5 rows appended |

## Gate 4 final-evaluation preregistration — 2026-08-30

The readiness audit hashes only registered authorities and training-fitted model artifacts. It does not resolve, inspect, hash, open, preprocess, score, or summarize held-out or official-test inputs.

| Artifact | Path | Raw SHA-256 | Present | Tracking / role |
|---|---|---|---:|---|
| Final-evaluation protocol v1 | `configs/evaluation/fd002-final-evaluation-protocol-v1.json` | `ed5d3ca6a847365256a238684086266fae8bab72a79ff6b4f9d8af3fa6a84133` | yes | Tracked; registered before test access; readiness blocked |
| Final-evaluation readiness report | `reports/final_evaluation_v1/fd002-confirmatory-evaluation-v1/readiness.json` | `1e503b64da1d13651c9e233f92d2d42de81727cd2041b27537689f5320a62ef6` | yes | Tracked; 10 authority and 5 available model hashes verified; zero held-out inputs checked |
| Frozen PCA primary bundle | `models/alerting_v1/fd002-alert-policy-study-v1/pca_reconstruction.joblib` | `d56a6d41e63c0781da763565f71c4a13b144eacd487a351428113c8ebf2ba9aa` | yes | Local/ignored; hash verified; primary detector and calibration bundle |
| Frozen LSTM comparator bundle | `models/alerting_v1/fd002-alert-policy-study-v1/lstm_calibrated_ensemble.json` | `efae8c17a834d5837aef2b09281ded44f90da700b462978436965888c5932588` | yes | Local/ignored; hash verified; comparator only, no fusion |
| Required fitted P1/K=6 preprocessor | `models/preprocessing/p1_k6.joblib` | not registered | no | Readiness blocker; do not substitute, infer, or access test data to reconstruct |
| Registered FD002 source for reproducible preprocessing | `data/raw/train_FD002.txt` | `bc1d293b8dc6173c1bfb0fff64fe797c2cde35dbb1a1a075dae8ca1177b49a52` | no | Readiness blocker for an independent training-only preprocessor rebuild; contents not opened |

## Access boundary

No held-out internal-test contents and no official NASA test data were opened, summarized, transformed, plotted, scored, or modeled while producing this manifest.

## P1/K=6 preprocessor recovery and final-evaluation v2 readiness - 2026-09-01

Protocol/readiness v1 remain preserved at the hashes above. The recovery used the complete authorized local run-to-failure source only for structural partition reconstruction and immediately retained the frozen training allowlist. No existing internal held-out split artifact or official NASA test artifact was opened or checked.

| Artifact | Path | Raw SHA-256 | Present | Tracking / role |
|---|---|---|---:|---|
| Recovery protocol v1 | `configs/preprocessing/fd002-p1-k6-recovery-protocol-v1.json` | `45a72d077f07225fa77beeb83029c426b75084cfb0a396ffb7f3a58f861e7225` | yes | Tracked; committed before project-data fitting |
| Recovery result | `reports/preprocessing_recovery/fd002-p1-k6-recovery-v1/result.json` | `3307c0407729352fa13dc7999a131be30729ac7ff80f4ad757c32d5000ec6371` | yes | Tracked compact provenance and reproduction evidence |
| Independent recovery verification | `reports/preprocessing_recovery/fd002-p1-k6-recovery-v1/verification.json` | `911c3c9c77c54fbad04c1ad2ffa830f6cb4e4ca312c5e1133df7ad86946ca544` | yes | Tracked; state, lineage, PCA, and Phase 5 reproduction verified |
| Authorized local source | `data/raw/train_FD002.txt` | `dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f` | yes | Local/ignored; 9,082,480-byte source-lineage correction |
| Unavailable historical source copy | historical reference only | `bc1d293b8dc6173c1bfb0fff64fe797c2cde35dbb1a1a075dae8ca1177b49a52` | no | Preserved blocked provenance; not rewritten or reinterpreted |
| Reconstructed training split | `data/splits/train.csv` | `cf8850d04c83f115874e99b11ae4b0ddc01f04820733c0b964b439dd495c0afc` | yes | Local/ignored; Route B semantic reconstruction, 32,107 rows/156 engines |
| Registered validation split | `data/splits/validation.csv` | `7587a365edda0d95f7e6e681a900220f18bfb619954b47cb2c61fce5330fe9ad` | yes | Local/ignored; diagnostics only after state freeze |
| Recovered P1/K=6 preprocessor | `models/preprocessing/p1_k6.joblib` | `c4f626743a8f6710dbca0487c12455169b819f928d847c6033f2ef365aa4a10a` | yes | Local/ignored; 135,914 bytes; identical across two isolated recovery processes |
| Final-evaluation protocol v2 | `configs/evaluation/fd002-final-evaluation-protocol-v2.json` | `77029d2aa9b4ac3059ece1409f6a8fc30d1be508593ef523dcf4910b2d269ede` | yes | Tracked provenance-only overlay; frozen Gate 4 contract unchanged |
| Final-evaluation readiness v2 | `reports/final_evaluation_v2/fd002-confirmatory-evaluation-v2/readiness.json` | `de8024ff03f0243353016035b0fa2cfe93ec6b198dacf43542a68de6b6cae56e` | yes | Tracked; ready for separately authorized held-out provisioning; zero held-out inputs checked |
| Confirmatory execution protocol v1 | `configs/evaluation/fd002-confirmatory-execution-protocol-v1.json` | `594278a3e81a8d98a979c946b33bebdadf7b51ae6301006d39ddaa84a77fe758` | yes | Tracked and committed before held-out access |
| Confirmatory result manifest | `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/result.json` | `70d6be0d608cb833b27924430a57f8534c31b35d115a953ac199b93cc1305d5d` | yes | Tracked internal held-out proxy evidence; not official NASA test |
| Confirmatory verification | `reports/final_evaluation_v2/fd002-confirmatory-internal-held-out-v1/verification.json` | `5195ccd96f9ab89e13bb5ef4cf78334334255397a6b98cfbf14a0d599d4fded7` | yes | Independent partition, transform, mode, window, score, alert, metric, contract, and report-hash reproduction |

## Literature comparison and final claims governance - 2026-09-01

These are versioned research/documentation derivatives. Bible v3, literature matrix v3, confirmatory configs, and confirmatory reports remain unchanged.

| Artifact | Path | Canonical LF SHA-256 | Tracking / role |
|---|---|---|---|
| Literature evidence matrix v4 JSON | `docs/research/LITERATURE_EVIDENCE_MATRIX_V4.json` | `7e78011c3feeaf6b96eae56d45ee3ae073046daaccf44d7ecfd5aa32a1792a86` | Audits all 100 v3 records; v3 source preserved |
| Literature/project comparison JSON | `docs/research/literature_to_project_metric_comparison.json` | `9bc9920d05b77a0841cb698d87b98ba0ce519bcb113a99860c17fbb2983dcb5b` | Exact project metrics copied from committed authority; zero Category A comparators |
| Literature audit summary | `docs/research/literature_audit_summary.json` | `ba60ed5801840fcf78074335859b52b46c011516cd83900595d95ce378dcb69f` | Category, access, verification, and missing-evidence counts |
| Final claims audit Markdown | `docs/research/FINAL_CLAIMS_AUDIT.md` | `3ac5147f005a6eddc945cf80d2410a157bef76578b3a9baeb5ae32ebde154384` | Human-readable permitted/prohibited claim boundary |
| Final claims audit JSON | `docs/research/final_claims_audit.json` | `f10cdeb3288d70ab43b99cee7eeb8bd4685b02f3f57e1e07108c63fb322f444c` | Machine-readable 17-claim audit |
| Post-confirmatory roadmap | `docs/research/POST_CONFIRMATORY_IMPLEMENTATION_ROADMAP.md` | `6b663f779ff343e900933632f1c79155b34361c5de805a59309305821fa200ab` | Immutable-result rule and remaining research/implementation/future work |

## Frozen inference and explanation implementation - 2026-09-01

| Artifact | Path | Raw SHA-256 | Tracking / role |
|---|---|---|---|
| Frozen inference/attribution protocol | `configs/inference/fd002-frozen-inference-protocol-v1.json` | `1c5f68d818405126655b298b9010de2255a42f5740aa4d75068be67c110d03e8` | Tracked; pre-registered semantics, artifact identities, and frozen policy |
| Validation-only regression | `reports/inference_validation_v1/validation_regression.json` | `31df347a0892e5399640dd469d8802659c8e64dab22a2ca4e60e3248d04dee96` | Tracked; compact score/alert parity evidence, no input rows |
