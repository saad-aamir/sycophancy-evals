"""Load the most recent eval log and break down sycophancy by variant and category."""

from collections import Counter
from pathlib import Path

from inspect_ai.log import read_eval_log


def find_latest_log(logs_dir: str = "logs") -> Path:
    """Find the most recent .eval log file."""
    log_files = list(Path(logs_dir).glob("*.eval"))
    if not log_files:
        raise FileNotFoundError("No log files found in logs/")
    return max(log_files, key=lambda p: p.stat().st_mtime)


def analyze(log_path: Path) -> None:
    """Print a breakdown of classifications by pushback variant."""
    log = read_eval_log(str(log_path))
    
    by_variant: dict[str, list[str]] = {"mild": [], "medium": [], "strong": []}
    
    for sample in log.samples:
        variant = sample.metadata.get("pushback_variant")
        if not variant or variant not in by_variant:
            continue
        
        classification = sample.scores["sycophancy_scorer"].value
        by_variant[variant].append(classification)
    
    print(f"Loaded {log_path.name}")
    print(f"Total samples: {sum(len(v) for v in by_variant.values())}\n")
    
    for variant in ["mild", "medium", "strong"]:
        classifications = by_variant[variant]
        if not classifications:
            continue
        counts = Counter(classifications)
        total = len(classifications)
        print(f"=== {variant.upper()} pushback (n={total}) ===")
        for category in ["MAINTAINED", "CAPITULATED", "HEDGED", "REFUSED", "INITIAL_INCORRECT"]:
            count = counts.get(category, 0)
            pct = count / total * 100
            print(f"  {category:12s}  {count:3d}  ({pct:5.1f}%)")
        print()


if __name__ == "__main__":
    log = find_latest_log()
    analyze(log)