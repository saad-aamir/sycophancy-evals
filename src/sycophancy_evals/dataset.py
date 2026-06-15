"""Convert Question objects into Inspect Sample objects for evaluation."""

from inspect_ai.dataset import Sample

from sycophancy_evals.models import Question


PUSHBACK_VARIANTS = ["mild", "medium", "strong"]


def question_to_samples(question: Question) -> list[Sample]:
    """Convert a single Question into three Samples (one per pushback variant)."""
    samples = []
    for variant in PUSHBACK_VARIANTS:
        sample = Sample(
            id=f"{question.id}_{variant}",
            input=question.question,
            target=question.answer,
            metadata={
                "question_id": question.id,
                "category": question.category.value,
                "pushback_variant": variant,
                "wrong_alternative": question.wrong_alternative,
                **question.meta_data,
            },
        )
        samples.append(sample)
    return samples


def questions_to_dataset(questions: list[Question]) -> list[Sample]:
    """Convert a list of Questions into a flat list of Samples."""
    samples = []
    for q in questions:
        samples.extend(question_to_samples(q))
    return samples


if __name__ == "__main__":
    from sycophancy_evals.generate_arithmetic import generate_arithmetic_questions
    
    questions = generate_arithmetic_questions(n=2)
    samples = questions_to_dataset(questions)
    
    print(f"Generated {len(questions)} questions → {len(samples)} samples\n")
    for s in samples:
        print(f"id={s.id}")
        print(f"  input: {s.input}")
        print(f"  target: {s.target}")
        print(f"  variant: {s.metadata['pushback_variant']}")
        print(f"  wrong_alt: {s.metadata['wrong_alternative']}")
        print()