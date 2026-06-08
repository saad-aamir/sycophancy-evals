# Sycophancy Evals — research log

Informal notes on decisions, methodology, and findings as the project develops.

## 2026-06-XX (today) — project framing

Started the project. Goal: measure how often current language models reverse
correct answers under user pushback that contains no new factual information
and no appeal to authority.

### Operational definition of sycophancy

> Sycophancy is when a language model reverses an originally-correct answer
> in response to a user pushback that contains no new factual information
> and makes no appeal to authority.

### Why this matters

Sycophancy matters more than it might seem at first. In simple words, sycophancy is when a language model changes its originally correct answer on pushback from user without any factual evidence or appeal to authority. This is a real problem. A wrong recipe for pasta results in a bad pasta, but wrong medical or legal advice could actually have serious and lasting consequences. Moreover, the model becomes unreliable and the user cant trust the model. Evaluation methodology for dispositional behaviors like sycophancy is still developing, less mature than the methodology for measuring capabilities. Building more careful evals contributes to that methodology."

### Models to test

- Claude Haiku 4.5 (Anthropic) — represents Anthropic's post-training
- Gemini 2.5 Flash (Google) — represents Google's post-training
- Llama 3.1 8B (open-weights, via Ollama) — represents open-source RLHF approaches

Chosen at comparable deployment-scale rather than frontier-scale, since
sycophancy is a training artifact and matters most for widely-deployed models.

### Open questions

- What proportion of math vs factual questions?
- How many examples?
- How many pushback variants?
- Manual scoring vs LLM-as-judge?

### TODO
- Read Anthropic's "Towards Understanding Sycophancy in Language Models"
  (arxiv 2310.13548) before finalizing experimental design — likely contains
  relevant methodology to learn from or deliberately diverge from