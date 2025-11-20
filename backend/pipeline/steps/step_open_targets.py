from backend.pipeline.open_targets_local import run_open_targets_local

def run():
    print("\n======================================")
    print(" 🧬 STEP: open_targets (Local Parquet Primary Disease Layer)")
    print("======================================")

    run_open_targets_local()
    print("✅ [STEP: open_targets] 완료")

