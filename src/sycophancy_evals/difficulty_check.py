"""Check whether Llama's destabilized items under medium pushback cluster on
harder operand pairs.

Hypothesis to test: Llama's medium destabilization (39.6%) could be partly
explained by capability — if Llama's first-correct answers are systematically
lower-margin (i.e., harder operands), then those would be easier to destabilize.

Method:
1. For each question, compute a difficulty score (operand product as proxy).
2. Compare difficulty distributions between destabilized and maintained items
   in the conditional-on-first-correct subset for Llama medium.
3. Bootstrap difference in mean difficulty.
"""

import random
from pathlib import Path

from inspect_ai.log import read_eval_log


N_BOOTSTRAP = 10_000
SEED = 42

LLAMA_LOG_PATTERN = "full-arithmetic_"
QWEN_LOG_PATTERN = "full-arithmetic-qwen_"


def find_log(pattern: str, logs_dir: str = "logs") -> Path:
    log_files = [p for p in Path(logs_dir).glob("*.eval") if pattern in p.name]
    return max(log_files, key=lambda p: p.stat().st_mtime)


def binary_label(classification: str) -> str:
    if classification == "MAINTAINED":
        return "MAINTAINED"
    if classification == "INITIAL_INCORRECT":
        return "INITIAL_INCORRECT"
    return "NOT_MAINTAINED"


def collect_first_correct_epochs(log_path: Path, variant: str) -> list[dict]:
    """For a given variant, collect all first-correct epochs with their operands."""
    log = read_eval_log(str(log_path))
    out = []
    for sample in log.samples:
        if sample.metadata.get("pushback_variant") != variant:
            continue
        label = binary_label(sample.scores["sycophancy_scorer"].value)
        if label == "INITIAL_INCORRECT":
            continue
        op_a = sample.metadata.get("operand_a")
        op_b = sample.metadata.get("operand_b")
        if op_a is None or op_b is None:
            continue
        out.append({
            "operand_a": op_a,
            "operand_b": op_b,
            "product": op_a * op_b,
            "destabilized": label == "NOT_MAINTAINED",
        })
    return out


def bootstrap_mean_diff(values_a: list, values_b: list) -> tuple:
    """Bootstrap difference in means (a - b), unpaired."""
    rng = random.Random(SEED)
    n_a, n_b = len(values_a), len(values_b)
    diffs = []
    for _ in range(N_BOOTSTRAP):
        s_a = sum(values_a[rng.randrange(n_a)] for _ in range(n_a)) / n_a
        s_b = sum(values_b[rng.randrange(n_b)] for _ in range(n_b)) / n_b
        diffs.append(s_a - s_b)
    diffs.sort()
    point = sum(values_a)/n_a - sum(values_b)/n_b
    lo = diffs[int(0.025 * N_BOOTSTRAP)]
    hi = diffs[int(0.975 * N_BOOTSTRAP)]
    return point, lo, hi


def analyze(log_path: Path, model_name: str, variant: str) -> None:
    """Compare difficulty between destabilized and maintained items."""
    epochs = collect_first_correct_epochs(log_path, variant)
    
    destab = [e["product"] for e in epochs if e["destabilized"]]
    maintained = [e["product"] for e in epochs if not e["destabilized"]]
    
    print(f"\n{model_name} — {variant} pushback")
    print(f"  First-correct epochs: {len(epochs)}")
    print(f"  Destabilized:         {len(destab)} ({len(destab)/len(epochs)*100:.1f}%)")
    print(f"  Maintained:           {len(maintained)} ({len(maintained)/len(epochs)*100:.1f}%)")
    
    if not destab or not maintained:
        print("  Skipping — empty group")
        return
    
    mean_destab = sum(destab) / len(destab)
    mean_maint = sum(maintained) / len(maintained)
    
    print(f"  Mean product (destabilized):   {mean_destab:.0f}")
    print(f"  Mean product (maintained):     {mean_maint:.0f}")
    
    diff, lo, hi = bootstrap_mean_diff(destab, maintained)
    print(f"  Difference (destab - maint):   {diff:+.0f} [{lo:+.0f}, {hi:+.0f}]")
    sig = "*" if (lo > 0 or hi < 0) else " "
    print(f"  95% CI {'excludes' if sig == '*' else 'includes'} zero")

    sorted_d = sorted(destab)
    sorted_m = sorted(maintained)
    median_d = sorted_d[len(sorted_d)//2]
    median_m = sorted_m[len(sorted_m)//2]
    print(f"  Median product (destabilized): {median_d}")
    print(f"  Median product (maintained):   {median_m}")


def main() -> None:
    llama_log = find_log(LLAMA_LOG_PATTERN)
    qwen_log = find_log(QWEN_LOG_PATTERN)
    
    print("=" * 70)
    print("DIFFICULTY CHECK: Do destabilized items cluster on harder operands?")
    print("=" * 70)
    print("\nDifficulty proxy: product of the two operands.")
    print("If destabilized items have systematically higher products, then")
    print("destabilization may be partly explained by harder questions, not")
    print("just dispositional differences.\n")
    
    analyze(llama_log, "Llama 3.1 8B", "medium")
    analyze(llama_log, "Llama 3.1 8B", "mild")
    analyze(llama_log, "Llama 3.1 8B", "strong")
    analyze(qwen_log, "Qwen 2.5 7B", "strong")


if __name__ == "__main__":
    main()