# LinguaMind

**A Linguistic Complexity-Aware LLM Reading Assistant**

> *Analyze why the text is difficult, then adapt the explanation.*

LinguaMind is a human-centered NLP prototype that uses linguistic features to
diagnose why an English text may be difficult, and adapts LLM explanation
strategies accordingly.

## Motivation

LLMs can explain difficult English text, but their explanations are typically
generated without explicitly modeling *why* a sentence is difficult for a
particular reader. LinguaMind explores whether interpretable linguistic
features — syntactic complexity, lexical difficulty, and information-density
proxies — can serve as signals for selecting different explanation strategies.
The current system is an exploratory rule-based prototype rather than a
validated model of human reading difficulty.

## Research Question

```
linguistic complexity  →  estimated reading difficulty  →  explanation strategy
```

> **Can linguistic diagnostics help an LLM adapt how it explains difficult language?**

The pipeline deliberately treats linguistic complexity as an *estimate* of
reading difficulty (estimated reading load), not as a measurement of actual
human cognitive load. A computational proxy is not a psychological construct;
validating this estimate against human judgments is part of the planned
evaluation.

## Architecture

```
        English Text
              │
              ▼
┌─────────────────────────┐
│  Linguistic Analysis    │        spaCy (dependency parsing, POS)
│  ┌─────────┬─────────┐  │
│  Syntax   Lexicon   Density │
│  length   difficult  nouns │
│  depth    academic   terms │
│  clauses  ratio     ratio  │
│  conj.                     │
└─────────┬───────────────┘
          ▼
   Difficulty Diagnosis        difficulty_type: syntax / vocabulary /
          │                     information / balanced / low
          ▼
┌─────────────────────────┐
│  Explanation Strategy   │      Structure-first · Vocabulary-first
│  (difficulty × level)   │      Meaning-first · Direct
└─────────┬───────────────┘
          ▼
          LLM (OpenAI-compatible API)   →   adaptive explanation
          │
          ▼
   Simple / Deep / Grammar Points  (JSON, stable schema)
```

Rather than routing text directly to an LLM, the system inserts an explicit
interpretable layer: linguistic representation → difficulty diagnosis →
strategy routing → generation.

## Features

- **Explainable complexity score** — six leaf metrics (sentence length,
  syntactic depth, subordination, lexical difficulty, content-word density,
  structural complexity) aggregated into three weighted dimensions; every
  score is auditable (value + mapping rule + weight).
- **Difficulty diagnosis** — each sentence is labeled with its dominant
  difficulty source (`syntax` / `vocabulary` / `information` / `balanced`),
  plus a **difficulty profile** (per-dimension High/Medium/Low) and the
  **main drivers** (e.g. deep dependency structure, embedded clauses,
  proportion of difficult words).
- **Strategy routing** — the diagnosis selects the explanation strategy
  (Structure-first, Vocabulary-first, Meaning-first, Direct), which is then
  injected into the LLM prompt.
- **Reader-level adaptation** — undergrad / graduate / researcher profiles
  modulate explanation trade-offs jointly with text difficulty.
- **English-learning oriented output** — the LLM also emits grammar points
  (clause types, passive structures, collocations, domain vocabulary), like a
  teacher annotating a difficult sentence.

## Method Notes

- **Syntactic features** come from spaCy dependency parsing
  (tree depth, subordinate clauses, coordination, apposition).
- **Lexical difficulty** is currently a coarse heuristic (word length ≥ 8
  chars or academic suffixes). It is operationalized as a proxy, not yet as a
  validated measure; the primary next step replaces it with word frequency /
  CEFR levels / the Academic Word List.
- **Information-density proxies**: content-word ratio, noun density, and
  terminology density. These are operational proxies for the broader
  psycholinguistic construct of information density.
- **Complexity score** = 0.40 × syntactic + 0.35 × lexical + 0.25 ×
  information-density proxies (weights explicit and adjustable).
- The LLM output is forced to JSON (`response_format: json_object`) and parsed
  with a retry fallback.

## Pilot Evaluation (planned)

A small-scale human evaluation is planned to test the core research question.

- **Stimuli**: 10 complex English sentences covering syntax-dominant,
  vocabulary-dominant, and balanced difficulty profiles.
- **Conditions**:
  - *Baseline*: generic LLM explanation.
  - *LinguaMind*: explanation generated after linguistic analysis
    (difficulty diagnosis → strategy routing → adaptive prompt).
- **Measures**: perceived clarity (1–5 rating), comprehension accuracy
  (brief comprehension question per item), optional reading time.
- **Target**: 5–10 participants. Results will be reported after data
  collection.

Materials and scripts live in [`evaluation/`](evaluation/).

A future refinement will add a **structured-prompt control condition**
(explanation asked for syntax / vocabulary / meaning, but without linguistic
diagnosis) to separate the contribution of linguistic diagnosis from prompt
complexity itself.

## Limitations

- The complexity score is a rule-based heuristic; it has not been validated
  against human judgments or reading-time data.
- Lexical difficulty currently relies on word length and suffix patterns;
  word frequency / CEFR / academic-word-list resources are not yet integrated.
- Because long content words raise both the lexical and the information-density
  dimensions (feature overlap), an *information-dominant* label is rare in
  academic text under the current heuristic — the diagnosis mainly produces
  syntax / vocabulary / balanced.
- The pilot will test explanation quality, not the validity of the complexity
  score itself.

## Next Steps

- Replace heuristic lexical difficulty with frequency / CEFR-based measures.
- Validate difficulty estimates against human judgments.
- Conduct a controlled evaluation of adaptive vs. generic explanations, with
  a structured-prompt control condition.
- Explore learned difficulty prediction after sufficient human data are
  collected.

## Quick Start

```bash
# 1. Create an isolated environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Configure the LLM (any OpenAI-compatible API)
cp .env.example .env     # then fill in LLM_API_KEY

# 4. Run the analysis module (CLI demo)
python lingua_analysis.py
python lingua_explain.py

# 5. Run the interactive demo
streamlit run streamlit_app.py
# → http://localhost:8501
```

## Project Structure

```
lingua-mind/
├── lingua_analysis.py    # linguistic analysis: metrics, difficulty diagnosis
├── lingua_explain.py     # LLM layer: strategy routing, adaptive explanation
├── streamlit_app.py      # interactive demo UI
├── evaluation/           # pilot evaluation materials (planned study)
├── requirements.txt
└── LinguaMind-产品设计V1.html   # product design doc (architecture, data schema, PRD)
```

## License

MIT
