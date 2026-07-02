"""Environment-backed runtime settings."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    qwen_api_key: str | None = os.getenv("QWEN_API_KEY")
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen3.7-plus")
    model_mode: str = os.getenv("SAFEFLOW_MODEL_MODE", "fixture_fallback")
    results_dir: str = os.getenv("SAFEFLOW_RESULTS_DIR", "data/results")
    fixtures_dir: str = os.getenv("SAFEFLOW_FIXTURES_DIR", "data/fixtures")
    benchmark_path: str = os.getenv("SAFEFLOW_BENCHMARK_PATH", "data/benchmark/support_demo.jsonl")
    api_host: str = os.getenv("SAFEFLOW_API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("SAFEFLOW_API_PORT", "8000"))
    ui_port: int = int(os.getenv("SAFEFLOW_UI_PORT", "5173"))
    refund_approval_threshold: float = float(
        os.getenv("SAFEFLOW_REFUND_APPROVAL_THRESHOLD", "500")
    )
    max_extraction_repair_attempts: int = int(
        os.getenv("SAFEFLOW_MAX_EXTRACTION_REPAIR_ATTEMPTS", "1")
    )
    eval_repeated_runs: int = int(os.getenv("SAFEFLOW_EVAL_REPEATED_RUNS", "5"))
    random_seed: int = int(os.getenv("SAFEFLOW_RANDOM_SEED", "42"))


settings = Settings()
