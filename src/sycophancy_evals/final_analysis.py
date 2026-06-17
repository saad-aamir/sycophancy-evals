"""Final analysis: conditional rates + question-level bootstrap CIs.

Computes:
- Per-question rates aggregated across the 3 epochs
- Conditional rates (excluding INITIAL_INCORRECT from denominator)
- Bootstrap CIs at the question level (200 independent units, not 600)
- Cross-condition and cross-model comparisons with paired bootstrap where applicable
"""

import random
from collections import defaultdict
from pathlib import Path

from inspect_ai.log import read_eval_log


N_BOOTSTRAP = 10_000
SEED = 42

LLAMA_LOG_PATTERN = "full-arithmetic_"
QWEN_LOG_PATTERN = "full-arithmetic-qwen_"


def find_log(pattern: str, logs_dir: str = "logs") -> Path:
    log_files = [p for p in Path(logs_dir).glob("*.eval") if pattern in p.name]
    if not log_files:
        raise FileNotFoundError(f"No log files matching {pattern!r}")
    return max(log_files, key=lambda p: p.stat().st_mtime)


def binary_label(classification: str) -> str:
    """Collapse to binary MAINTAINED / NOT_MAINTAINED / INITIAL_INCORRECT."""
    if classification == "MAINTAINED":
        return "MAINTAINED"
    if classification == "INITIAL_INCORRECT":
        return "INITIAL_INCORRECT"
    return "NOT_MAINTAINED"


def load_question_data(log_path: Path) -> dict:
    """Return per-question data: {question_id: {variant: [list of binary labels across epochs]}}."""
    log = read_eval_log(str(log_path))
    data = defaultdict(lambda: defaultdict(list))
    
    for sample in log.samples:
        question_id = sample.metadata["question_id"]
        variant = sample.metadata["pushback_variant"]
        classification = sample.scores["sycophancy_scorer"].value
        data[question_id][variant].append(binary_label(classification))
    
    return data


def question_level_rates(question_data: dict, variant: str, conditional: bool) -> list:
    """For each question, compute its rate of NOT_MAINTAINED across epochs.
    
    If conditional=True, exclude INITIAL_INCORRECT epochs from the denominator.
    Returns a list of per-question rates (NaN-filtered if a question has 0 eligible epochs).
    """
    rates = []
    for question_id, by_variant in question_data.items():
        epochs = by_variant.get(variant, [])
        if not epochs:
            continue
        
        if conditional:
            eligible = [e for e in epochs if e != "INITIAL_INCORRECT"]
            if not eligible:
                continue  # Question had no first-correct epochs; drop
            not_maintained = sum(1 for e in eligible if e == "NOT_MAINTAINED")
            rates.append(not_maintained / len(eligible))
        else:
            not_maintained = sum(1 for e in epochs if e == "NOT_MAINTAINED")
            rates.append(not_maintained / len(epochs))
    
    return rates


def bootstrap_ci(values: list, n_boot: int = N_BOOTSTRAP, alpha: float = 0.05) -> tuple:
    """Non-parametric bootstrap CI for the mean."""
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(SEED)
    means = []
    n = len(values)
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot)]
    point = sum(values) / n
    return (point, lo, hi)


def paired_bootstrap_diff(values_a: list, values_b: list, n_boot: int = N_BOOTSTRAP, alpha: float = 0.05) -> tuple:
    """Paired bootstrap on the difference (a - b), assuming both lists are aligned by question."""
    if len(values_a) != len(values_b):
        raise ValueError(f"Lists must be aligned by question: {len(values_a)} vs {len(values_b)}")
    
    diffs = [a - b for a, b in zip(values_a, values_b)]
    rng = random.Random(SEED)
    n = len(diffs)
    boot_diffs = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_diffs.append(sum(sample) / n)
    boot_diffs.sort()
    lo = boot_diffs[int(alpha / 2 * n_boot)]
    hi = boot_diffs[int((1 - alpha / 2) * n_boot)]
    point = sum(diffs) / n
    return (point, lo, hi)


def unpaired_bootstrap_diff(values_a: list, values_b: list, n_boot: int = N_BOOTSTRAP, alpha: float = 0.05) -> tuple:
    """Unpaired bootstrap on the difference of means (for cross-model comparisons)."""
    rng = random.Random(SEED)
    n_a, n_b = len(values_a), len(values_b)
    boot_diffs = []
    for _ in range(n_boot):
        sample_a = [values_a[rng.randrange(n_a)] for _ in range(n_a)]
        sample_b = [values_b[rng.randrange(n_b)] for _ in range(n_b)]
        boot_diffs.append(sum(sample_a) / n_a - sum(sample_b) / n_b)
    boot_diffs.sort()
    lo = boot_diffs[int(alpha / 2 * n_boot)]
    hi = boot_diffs[int((1 - alpha / 2) * n_boot)]
    point = sum(values_a) / n_a - sum(values_b) / n_b
    return (point, lo, hi)


def paired_rates(question_data: dict, variant_a: str, variant_b: str, conditional: bool) -> tuple:
    """Return paired per-question rates for two variants. Drops questions missing either."""
    rates_a, rates_b = [], []
    for question_id, by_variant in question_data.items():
        epochs_a = by_variant.get(variant_a, [])
        epochs_b = by_variant.get(variant_b, [])
        if not epochs_a or not epochs_b:
            continue
        
        if conditional:
            elig_a = [e for e in epochs_a if e != "INITIAL_INCORRECT"]
            elig_b = [e for e in epochs_b if e != "INITIAL_INCORRECT"]
            if not elig_a or not elig_b:
                continue
            rate_a = sum(1 for e in elig_a if e == "NOT_MAINTAINED") / len(elig_a)
            rate_b = sum(1 for e in elig_b if e == "NOT_MAINTAINED") / len(elig_b)
        else:
            rate_a = sum(1 for e in epochs_a if e == "NOT_MAINTAINED") / len(epochs_a)
            rate_b = sum(1 for e in epochs_b if e == "NOT_MAINTAINED") / len(epochs_b)
        
        rates_a.append(rate_a)
        rates_b.append(rate_b)
    
    return rates_a, rates_b


def fmt(point: float, lo: float, hi: float) -> str:
    return f"{point*100:5.1f}% [{lo*100:5.1f}, {hi*100:5.1f}]"


def main() -> None:
    llama_data = load_question_data(find_log(LLAMA_LOG_PATTERN))
    qwen_data = load_question_data(find_log(QWEN_LOG_PATTERN))
    
    print(f"Llama questions: {len(llama_data)}")
    print(f"Qwen questions:  {len(qwen_data)}\n")
    
    variants = ["mild", "medium", "strong"]

    print("=" * 70)
    print("NOT_MAINTAINED RATES (question-level, 95% bootstrap CI)")
    print("=" * 70)
    
    for model_name, data in [("Llama 3.1 8B", llama_data), ("Qwen 2.5 7B", qwen_data)]:
        print(f"\n{model_name}:")
        print(f"  {'Variant':<10} {'Unconditional':<25} {'Conditional (first-correct)':<25}")
        for variant in variants:
            uncond = question_level_rates(data, variant, conditional=False)
            cond = question_level_rates(data, variant, conditional=True)
            uncond_stats = bootstrap_ci(uncond)
            cond_stats = bootstrap_ci(cond)
            print(f"  {variant:<10} {fmt(*uncond_stats):<25} {fmt(*cond_stats):<25}")
    
    print("\n" + "=" * 70)
    print("WITHIN-MODEL PAIRWISE DIFFERENCES (paired bootstrap, conditional rates)")
    print("=" * 70)
    
    for model_name, data in [("Llama 3.1 8B", llama_data), ("Qwen 2.5 7B", qwen_data)]:
        print(f"\n{model_name}:")
        for v_a, v_b in [("medium", "mild"), ("medium", "strong"), ("strong", "mild")]:
            rates_a, rates_b = paired_rates(data, v_a, v_b, conditional=True)
            diff_stats = paired_bootstrap_diff(rates_a, rates_b)
            sig = "*" if (diff_stats[1] > 0 or diff_stats[2] < 0) else " "
            print(f"  {v_a} − {v_b}:  {fmt(*diff_stats)}  {sig}")
    
    print("\n" + "=" * 70)
    print("CROSS-MODEL DIFFERENCES (unpaired bootstrap, conditional rates)")
    print("=" * 70)
    print("Llama − Qwen, per variant:")
    
    for variant in variants:
        llama_rates = question_level_rates(llama_data, variant, conditional=True)
        qwen_rates = question_level_rates(qwen_data, variant, conditional=True)
        diff_stats = unpaired_bootstrap_diff(llama_rates, qwen_rates)
        sig = "*" if (diff_stats[1] > 0 or diff_stats[2] < 0) else " "
        print(f"  {variant:<10} {fmt(*diff_stats)}  {sig}")
    
    print("\n* = 95% CI excludes zero")


if __name__ == "__main__":
    main()