"""Compare manual labels against Sonnet's judge classifications.

Reports agreement at three taxonomy levels:
- Four-way: MAINTAINED / CAPITULATED / HEDGED / REFUSED (original)
- Three-way: MAINTAINED / DESTABILIZED / REFUSED (collapse HEDGED+CAPITULATED)
- Binary: MAINTAINED / NOT_MAINTAINED
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


VALID_LABELS = {"MAINTAINED", "CAPITULATED", "HEDGED", "REFUSED", "INITIAL_INCORRECT"}


def parse_labels(label_file: Path) -> dict[str, str]:
    """Extract MY LABEL values from the markdown file."""
    text = label_file.read_text()
    
    sample_pattern = re.compile(r"## Sample (\d+)/\d+")
    label_pattern = re.compile(r"MY LABEL:\s*(\S+)")
    
    sections = sample_pattern.split(text)[1:]
    labels = {}
    
    for i in range(0, len(sections), 2):
        sample_num = sections[i]
        section_text = sections[i + 1]
        match = label_pattern.search(section_text)
        if not match:
            continue
        label = match.group(1).strip().upper().rstrip(",;.")
        if label not in VALID_LABELS:
            continue
        labels[sample_num] = label
    
    return labels


def collapse_three(label: str) -> str:
    """MAINTAINED / DESTABILIZED / REFUSED / INITIAL_INCORRECT."""
    if label in {"HEDGED", "CAPITULATED"}:
        return "DESTABILIZED"
    return label


def collapse_binary(label: str) -> str:
    """MAINTAINED vs NOT_MAINTAINED (everything else)."""
    if label == "MAINTAINED":
        return "MAINTAINED"
    return "NOT_MAINTAINED"


def compute_agreement(pairs: list, collapse_fn=None) -> tuple[int, int]:
    """Compute agreement, optionally applying a collapse function."""
    if collapse_fn is None:
        collapse_fn = lambda x: x
    n_agree = sum(
        1 for p in pairs
        if collapse_fn(p["my_label"]) == collapse_fn(p["sonnet_label"])
    )
    return n_agree, len(pairs)


def per_category_agreement(pairs: list, collapse_fn=None) -> dict:
    """Per-Sonnet-category agreement after applying collapse."""
    if collapse_fn is None:
        collapse_fn = lambda x: x
    by_sonnet = defaultdict(list)
    for p in pairs:
        sonnet_collapsed = collapse_fn(p["sonnet_label"])
        my_collapsed = collapse_fn(p["my_label"])
        by_sonnet[sonnet_collapsed].append(sonnet_collapsed == my_collapsed)
    
    return {
        cat: (sum(results), len(results))
        for cat, results in sorted(by_sonnet.items())
    }


def main() -> None:
    label_file = Path("validation_to_label.md")
    answer_key_file = Path("validation_answer_key.json")
    
    my_labels = parse_labels(label_file)
    answer_key = json.loads(answer_key_file.read_text())
    
    pairs = []
    for sample_num, my_label in my_labels.items():
        if sample_num not in answer_key:
            continue
        sonnet_label = answer_key[sample_num]["sonnet_label"]
        model = answer_key[sample_num]["model"]
        pairs.append({
            "sample": sample_num,
            "my_label": my_label,
            "sonnet_label": sonnet_label,
            "model": model,
        })
    
    print(f"Loaded {len(pairs)} paired labels\n")
    
    print("=" * 60)
    print("AGREEMENT AT MULTIPLE TAXONOMY LEVELS")
    print("=" * 60)
    
    n_four, n = compute_agreement(pairs)
    n_three, _ = compute_agreement(pairs, collapse_three)
    n_binary, _ = compute_agreement(pairs, collapse_binary)
    
    print(f"\nFour-way (MAINTAINED / CAPITULATED / HEDGED / REFUSED):")
    print(f"  {n_four}/{n} = {n_four/n*100:.1f}%")
    
    print(f"\nThree-way (MAINTAINED / DESTABILIZED / REFUSED):")
    print(f"  {n_three}/{n} = {n_three/n*100:.1f}%")
    
    print(f"\nBinary (MAINTAINED / NOT_MAINTAINED):")
    print(f"  {n_binary}/{n} = {n_binary/n*100:.1f}%")

    print(f"\n{'=' * 60}")
    print("PER-CATEGORY AGREEMENT (Sonnet's category → your label)")
    print("=" * 60)
    
    for level_name, collapse_fn in [
        ("Four-way", None),
        ("Three-way", collapse_three),
        ("Binary", collapse_binary),
    ]:
        print(f"\n{level_name}:")
        cat_agreement = per_category_agreement(pairs, collapse_fn)
        for cat, (agree, total) in cat_agreement.items():
            print(f"  Sonnet={cat:<18s}: {agree}/{total} = {agree/total*100:.1f}%")

    print(f"\n{'=' * 60}")
    print("PER-MODEL AGREEMENT (binary)")
    print("=" * 60)
    
    by_model = defaultdict(list)
    for p in pairs:
        by_model[p["model"]].append(p)
    
    for model, ps in by_model.items():
        n_a, n_t = compute_agreement(ps, collapse_binary)
        print(f"  {model}: {n_a}/{n_t} = {n_a/n_t*100:.1f}%")


if __name__ == "__main__":
    main()