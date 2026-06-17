"""Stratified sampling for manual judge validation.

Reads both eval logs (Llama and Qwen), stratified-samples conversations
across (model, classification) cells, and writes them to a markdown file
for manual labeling. Sonnet's classifications are hidden.
"""

import random
from collections import defaultdict
from pathlib import Path

from inspect_ai.log import read_eval_log


SAMPLES_PER_CELL = 13
SEED = 42

LLAMA_LOG_PATTERN = "full-arithmetic_"
QWEN_LOG_PATTERN = "full-arithmetic-qwen_"

OUTPUT_FILE = "validation_to_label.md"
ANSWER_KEY_FILE = "validation_answer_key.json"


def find_log(pattern: str, logs_dir: str = "logs") -> Path:
    """Find the most recent log file matching the pattern."""
    log_files = [p for p in Path(logs_dir).glob("*.eval") if pattern in p.name]
    if not log_files:
        raise FileNotFoundError(f"No log files matching {pattern!r} in {logs_dir}/")
    return max(log_files, key=lambda p: p.stat().st_mtime)


def collect_samples(log_path: Path, model_label: str) -> dict:
    """Bucket samples by (model_label, classification)."""
    log = read_eval_log(str(log_path))
    buckets = defaultdict(list)
    
    for sample in log.samples:
        classification = sample.scores["sycophancy_scorer"].value
        key = (model_label, classification)
        buckets[key].append(sample)
    
    return buckets


def write_labeling_file(selected: list, answer_key: dict) -> None:
    """Write a markdown file with conversations for manual labeling."""
    
    lines = []
    lines.append("# Judge Validation — Labeling File\n")
    lines.append("Read each conversation below. For each one, write your "
                 "classification at the bottom in the MY LABEL field.\n")
    lines.append("Valid labels: MAINTAINED, CAPITULATED, HEDGED, REFUSED, INITIAL_INCORRECT\n")
    lines.append("**Do not look at Sonnet's classification — they're stored in a separate "
                 "file that won't be revealed until you've labeled everything.**\n")
    lines.append("---\n")
    
    for i, (model_label, sample) in enumerate(selected, 1):
        messages = sample.messages
        question = messages[0].text
        first_response = messages[1].text
        pushback = messages[2].text

        second_response = messages[3].text if len(messages) > 3 else "(no second response — regex caught INITIAL_INCORRECT)"
        
        target = sample.target
        variant = sample.metadata.get("pushback_variant", "?")
        
        sonnet_label = sample.scores["sycophancy_scorer"].value
        answer_key[str(i)] = {
            "sample_id": sample.id,
            "model": model_label,
            "sonnet_label": sonnet_label,
        }
        
        lines.append(f"## Sample {i}/{len(selected)}\n")
        lines.append(f"- Test model: **{model_label}**")
        lines.append(f"- Pushback variant: **{variant}**")
        lines.append(f"- Correct answer: **{target}**\n")
        lines.append(f"**Q:** {question}\n")
        lines.append(f"**A1:** {first_response}\n")
        lines.append(f"**Pushback:** {pushback}\n")
        lines.append(f"**A2:** {second_response}\n")
        lines.append("MY LABEL: ____________________\n")
        lines.append("---\n")
    
    Path(OUTPUT_FILE).write_text("\n".join(lines))


def main() -> None:
    random.seed(SEED)
    
    llama_log = find_log(LLAMA_LOG_PATTERN)
    qwen_log = find_log(QWEN_LOG_PATTERN)
    print(f"Loading Llama log: {llama_log.name}")
    print(f"Loading Qwen log:  {qwen_log.name}\n")
    
    buckets = {}
    buckets.update(collect_samples(llama_log, "Llama 3.1 8B"))
    buckets.update(collect_samples(qwen_log, "Qwen 2.5 7B"))
    
    categories = ["MAINTAINED", "CAPITULATED", "HEDGED", "REFUSED"]
    models = ["Llama 3.1 8B", "Qwen 2.5 7B"]
    
    print("Available samples per (model, classification) cell:")
    for model in models:
        for category in categories:
            n = len(buckets.get((model, category), []))
            print(f"  {model} × {category}: {n}")
    print()
    
    selected = []
    for model in models:
        for category in categories:
            cell = buckets.get((model, category), [])
            n_to_take = min(SAMPLES_PER_CELL, len(cell))
            selected.extend((model, s) for s in random.sample(cell, n_to_take))
    
    random.shuffle(selected)
    
    answer_key = {}
    write_labeling_file(selected, answer_key)
    
    import json
    Path(ANSWER_KEY_FILE).write_text(json.dumps(answer_key, indent=2))
    
    print(f"Selected {len(selected)} samples for labeling.")
    print(f"Conversations: {OUTPUT_FILE}")
    print(f"Answer key:    {ANSWER_KEY_FILE}  (don't look at this until done labeling)")


if __name__ == "__main__":
    main()