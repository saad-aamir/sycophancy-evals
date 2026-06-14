
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import match
from inspect_ai.solver import generate

@task
def hello_inspect():

    return Task(
        dataset=[
            Sample(input = "What is 2 + 2? Respond with just a number.", target = "4"),
            Sample(input = "What is 10 + 5? Respond with just a number.", target = "15"),
            Sample(input="What is 100 - 50? Respond with just the number.", target="50"),
        ],
        solver = generate(),
        scorer = match(),
    )