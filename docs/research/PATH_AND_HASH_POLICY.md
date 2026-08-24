# Repository Path and Hash Policy

## Canonical paths

New serialized paths must be repository-relative POSIX strings, for example `reports/lstm_v2/run_summary.csv`. They must not contain a drive prefix, UNC prefix, leading slash, parent traversal, or a path outside the repository. Code must resolve them from the discovered repository root and serialize with `Path(...).as_posix()`.

Historical registered configs contain both POSIX paths and Windows backslashes. Their bytes are evidence and must not be rewritten merely for portability. The path resolver may interpret a historical backslash as a separator at runtime, but the stored config remains unchanged.

## SHA-256 byte views

SHA-256 covers a declared byte representation:

- **raw:** exact on-disk bytes;
- **lf:** the same valid UTF-8 text with each CRLF changed to LF;
- **crlf:** the same valid UTF-8 text with each LF changed to CRLF.

New artifacts use raw-byte SHA-256. A historical registered hash may use any explicitly recorded form. Verification first checks raw bytes and then, only for valid UTF-8 text without lone carriage returns, checks strict LF/CRLF equivalents. It must not trim whitespace, add or remove a final newline, change a BOM, normalize Unicode, reserialize JSON/CSV, reorder fields, or change numeric text. Binary artifacts have only the raw form.

This exception is verification-only. Do not bulk-normalize registered configs or reports. If content changes for any reason other than a verified line-ending representation, create a new version and hash.

## Git attribute protection for registered evidence

General source, documentation, JSON, JSONL, notebook, and CSV files use LF. The existing registered evidence was checked out as CRLF and its registered raw hashes describe those working-tree bytes, while the existing Git blobs use LF. Later, path-specific `text eol=crlf` rules in `.gitattributes` therefore keep the registered working-tree bytes stable and make Git's clean view match the existing blobs, so a broad `git add -A` does not stage line-ending-only changes. The last matching rule wins. The protected scopes are:

- `configs/splits/fd002-primary-v1.json`;
- `configs/preprocessing/fd002-preprocessing-*.json`;
- `configs/baselines/fd002-classical-baselines-v1.json`;
- `configs/lstm/fd002-lstm-screen-*.json`;
- `reports/preprocessing/*.csv`;
- `reports/baselines_v2/*.csv`;
- `reports/lstm_v2/*.csv`.

These exceptions preserve already registered checkout bytes; they do not authorize content changes or make CRLF the default for new evidence. A future evidence version must use a new versioned filename or artifact ID, be hashed from its final raw bytes, declare its line-ending form, evidence class, and predecessor, and be added to the artifact and claims manifests before it is treated as registered evidence. If a new protected scope is necessary, add the narrowest path-specific `.gitattributes` rule after the general text rules and verify both its checkout hash and its clean/index behavior through a temporary-index `git add -A` simulation.

## Registered examples at the base checkpoint

| Path | Checkout/raw SHA-256 | Alternate or registered SHA-256 | Interpretation |
|---|---|---|---|
| `experiments/experiments.csv` | `021133b38a07268b2eb2a76c07ab7346749161965922b28eee4d380f789e240f` | `f1b65636d738d4c15949663c1d43a9170cd94f40ad083b77a27cd311445a3e37` | CRLF checkout; Git/LF view |
| `configs/splits/fd002-primary-v1.json` | `953f6bee71022a644fc0e3e155f4c212bb2cc9a10794c2665c9d7d9cb6594327` | LF view `1aff6dc171317931317469237cfd5a71002954a490d6ce1812d09bcf3537eec1` | Registered hash is raw checkout |
| `configs/preprocessing/fd002-preprocessing-study-v1.json` | `a80a6b89b5af344662762567e390f0f9e8f712f822994596a06a952a3121612f` | LF view `404b5075539d40414f23a18d411bb57f5d48f48c201945b6834479d9d3f67b4a` | Current row uses raw checkout |
| `configs/preprocessing/fd002-preprocessing-selection-v1.json` | `6ebb4ae018c154d970f9a7a3b64e96cc23b366ed4a269f720ccd6996fd5243c6` | registered LF `4b71af5fd51cea9b90feda09e8d85ba502690e31efb3469fe20ad19482565086` | Strict newline-equivalent match |
| `configs/baselines/fd002-classical-baselines-v1.json` | `c565bc1ab540da4416deabc64d43bdc9bcb43f222f42325e9cd1157b5e67c697` | LF view `89b4b68dc64b4155ad076b1fe78a7d701dad964e9daad7740f09a47d34a0fb6e` | Registered hash is raw checkout |
| `configs/lstm/fd002-lstm-screen-protocol-v1.json` | `e5744a5a4f22c6c953abc9b32f90967d4c871c73cb8d0a605bbb16d117395abe` | registered LF `1d938ffd16c1024e1ff9767ccf9fefbaadb89919f67850051b15d6796a87f509` | Strict newline-equivalent match |
| `configs/lstm/fd002-lstm-screen-results-v1.json` | `26d2e6e6215d9a3c3376642396754bfae0279c53f808b809672ffbc96db05694` | LF view `4ded89827b1b8ac0f4cb86527993d2b65d0c3c32b8fb595adcdba38985020392` | Current manifest uses raw checkout |
| `reports/lstm_v2/verification_summary.csv` | `2e9c7789270374ebb34986f8121ee68181155441f5c7abef2f3e9ab79516c4b5` | registered LF `d2daa7c23370df3ae272daa533953783f3fda12847d5ccf30839b5bc8490668b` | Strict newline-equivalent match |

## Ledger row hashes

Each `source_row_sha256` in `experiments/runs_v2.jsonl` covers the exact UTF-8 bytes of one physical legacy CSV row, excluding its CRLF delimiter. The raw source-file hash and Git/LF source-file hash are recorded separately. This lets reviewers prove row identity without preserving malformed CSV as the active ledger.

## Verification and change control

1. Select the registered hash and its declared byte view from the owning config or manifest.
2. Verify raw or strict newline-equivalent bytes; report which form matched.
3. Treat every other mismatch as a failure.
4. Never overwrite an artifact under the same ID after a content change.
5. Use a new config/artifact version, record the reason and predecessor, and update the claims and artifact manifests.
