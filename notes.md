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

Sycophancy matters more than it might seem at first. In simple words, sycophancy is when a language model changes its originally correct answer on pushback from user without any factual evidence or appeal to authority. This is a real problem. A wrong recipe for pasta results in a bad pasta, but wrong medical or legal advice could actually have serious and lasting consequences. Moreover, the model becomes unreliable and the user cant trust the model. Evaluation methodology for dispositional behaviors like sycophancy is still developing, less mature than the methodology for measuring capabilities. Building more careful evals contributes to that methodology.

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

## Experimental design — decisions and reasoning

### Question mix (80 arithmetic + 60 word problems + 60 factual = 200 total)

This mix ensures that we can measure sycophancy across different domains and measure whether sycophancy is more common in a particular domain.
we wanted at least 60 examples per category to clear the statistical minimum for subgroup analysis after losing some to model errors. Arithmetic gets slightly more because it's the cleanest category (most verifiable, easiest to generate at quality), so we want the largest sample there.

### Difficulty calibration

Single digits are too easy, 4+ become too difficult for a small model to actually show its working. 
Unambiguous facts as the criterion helps in verifying more deterministically. Unambiguous facts only, because if the answer has legitimate variation (e.g., WW2 ending in 1945 vs 1946 vs 1951), a model that updates under pushback may be legitimately reconsidering rather than capitulating, and we can't distinguish those."

### Sample size (200)

We want enough examples in each category so that we can analyze each category separately. Statisticians use 30 as a rough minimum for a sub group analysis. Its a good defensible dataset. Starting at 60 per category lets us survive ~25% baseline error and still hit the 30-example minimum per subgroup.

### Pushback variants (three: mild / medium / strong)

Sycophancy rate as a function of pushback strength is itself a finding. If a model resists 'are you sure?' but capitulates to 'I'm pretty sure the answer is X,' that tells us the model isn't just socially anxious — it's responding to claimed knowledge. The variants let us distinguish these mechanisms.

### Wrong alternatives for strong pushback

If the wrong alternative is too obviously wrong (e.g., 'capital of Australia is Beijing'), the model rejects it easily and we undermeasure sycophancy. We need plausible-but-wrong alternatives that put the model in a real choice.

### Scoring methodology (hybrid: LLM-judge + manual spot-check)

Manual classification would be very slow. We will use claude to classify and then spot check random questions to verify its judgement. The spot-check converts LLM-as-judge from a black-box scoring method into something measurable. We can report inter-rater agreement between manual and LLM scoring, which makes the methodology defensible.