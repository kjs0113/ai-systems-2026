from pathlib import Path

def check_progress(log_file="harness.log"):
    lines = Path(log_file).read_text().splitlines()

    errors = [l for l in lines if "ERROR" in l or "FAILED" in l]

    return {
        "iterations": len([l for l in lines if "ITER" in l]),
        "error_count": len(errors),
        "stalled": len(set(errors)) == 1 if len(errors) > 3 else False
    }