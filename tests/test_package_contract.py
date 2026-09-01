from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAMES = (
    "make_splits.py",
    "create_window_metadata.py",
    "run_preprocessing_study.py",
    "run_classical_baselines.py",
    "run_lstm_screen.py",
    "verify_lstm_screen.py",
    "run_lstm_final_refit.py",
    "verify_lstm_final_refit.py",
    "run_alert_policy_study.py",
    "verify_alert_policy_study.py",
    "verify_final_evaluation.py",
    "recover_p1_preprocessor.py",
    "verify_p1_preprocessor.py",
)


def test_top_level_and_provenance_import_without_scientific_stack() -> None:
    source = (
        "import sys; "
        f"sys.path.insert(0, {str(REPO_ROOT / 'src')!r}); "
        "import turbofan_anomaly; "
        "import turbofan_anomaly.evaluation.provenance; "
        "assert 'numpy' not in sys.modules; "
        "assert 'pandas' not in sys.modules; "
        "assert 'sklearn' not in sys.modules; "
        "assert 'torch' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", source], check=True)


def test_retained_scripts_are_thin_package_wrappers() -> None:
    for name in SCRIPT_NAMES:
        path = REPO_ROOT / "scripts" / name
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert len(source.splitlines()) <= 10
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        assert len(imports) == 1
        assert imports[0].module.startswith("turbofan_anomaly.workflows.")
        assert [alias.name for alias in imports[0].names] == ["main"]


def test_cublas_environment_is_set_before_torch_import() -> None:
    for name in (
        "run_lstm_screen.py",
        "verify_lstm_screen.py",
        "run_lstm_final_refit.py",
        "verify_lstm_final_refit.py",
        "run_alert_policy_study.py",
        "verify_alert_policy_study.py",
    ):
        source = (
            REPO_ROOT / "src" / "turbofan_anomaly" / "workflows" / name
        ).read_text(encoding="utf-8")
        assert source.index('os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG"') < (
            source.index("import torch")
        )
