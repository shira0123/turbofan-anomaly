# Literature Source Verification and Evidence-Access Report

**Audit date:** 2026-09-01
**Source register:** `docs/research/Turbofan_Literature_Evidence_Matrix_100_Sources_v3.xlsx`
**Verified source-register SHA-256:** `ae173e281fbcbccae7da91920980f4d208a908d2f1a6a6dcfb54af5ebdf05ac3`

## Method

All 100 v3 records were retained once and assigned one comparison category and one v4 access level. The v3 workbook was read without editing. The v4 audit does not claim a complete systematic review beyond the registered set. No copyrighted PDF was committed.

Numerical extraction required the containing full text, authoritative full HTML, or author manuscript. Screening records based only on an abstract or metadata were retained as background and forced to `NR` for numerical fields. Prior full-text contextual claims were retained, but their exact metrics were not promoted without a fresh result-location check.

## Access counts

| Evidence-access level | Count | Numerical use rule |
|---|---:|---|
| `full_text_verified` | 67 | Eligible only when a precise result location was freshly verified |
| `author_manuscript_verified` | 1 | Eligible with precise result location |
| `authoritative_html_full_text_verified` | 1 | Eligible with precise result location |
| `abstract_only` | 27 | Numerical fields forced to `NR` |
| `metadata_only` | 4 | Numerical fields forced to `NR` |
| `full_text_unavailable` | 0 | None in current register |
| `pending_verification` | 0 | None in current register |

## Fresh numerical verification

| ID | Access | Source | Verified evidence |
|---|---|---|---|
| LIT-007 | full text | [Publisher PDF](https://thesai.org/Downloads/Volume11No11/Paper_5-Autoencoder_based_Semi_Supervised_Anomaly_Detection.pdf) | Sec. III-IV and Table VI, pp. 44-47: split, label rule, threshold selection, F1, precision, recall |
| LIT-012 | authoritative HTML full text | [arXiv HTML v3](https://arxiv.org/html/2502.19307v3) | Sec. III-C and IV-B, Tables II and IV: subsets, split, label rule, threshold optimization, metrics |
| LIT-013 | author manuscript | [University of Alcala manuscript](https://ebuah.uah.es/xmlui/bitstream/handle/10017/68237/early_sanchez_UAH_IA3_2026.pdf?isAllowed=y&sequence=3) | Sec. V-VI and Table 3, pp. 9-11: training/evaluation partition, final-10% proxy, FD002 metrics |

## Missing-evidence register

The audit intentionally leaves unresolved fields explicit: 94 author lists, 97 split strategies, 96 evaluation units, 96 label definitions, 97 exact metric-value fields, and 100 code/data-availability fields remain `NR`. A source URL is used as the stable identifier when a DOI or accession was not verified. No unsupported numerical value was carried forward from an abstract or screening note.

## Identity and scope results

- 100 unique normalized titles and 100 unique stable identifiers were retained.
- Zero duplicate or invalid records were removed.
- No new paper was added solely to preserve the 100-record count.
- No Category A paper was identified; direct numerical comparison count is zero.
- Candidate discoveries outside v3 were not added because the registered collection was already at the 100-paper ceiling and they did not close the protocol-equivalence gap.
