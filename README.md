# LinguaMind

**A Linguistic-Aware AI Reading Assistant**

> *Analyze why the text is difficult, then adapt the explanation.*

LinguaMind is not another translation or summarization wrapper. It is a
human-centered NLP prototype that first **measures the linguistic complexity**
of an English text, then **decides how to explain it** based on the estimated
reading difficulty and the reader's proficiency level.

## Research Hypothesis

```
linguistic complexity  →  estimated reading difficulty  →  explanation strategy
```

This is the core question the project explores:

> **Can linguistic features help an LLM explain language better?**

The project deliberately treats the pipeline as an *estimation* of reading
difficulty (estimated reading load), not a measurement of actual human
cognitive load — that distinction would require experimental validation.

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

## Features

- **Explainable complexity score** — six leaf metrics
  (sentence length, syntactic depth, subordination, lexical difficulty,
  content-word density, structural complexity) aggregated into three weighted
  dimensions; every score is auditable (value + mapping rule + weight).
- **Difficulty diagnosis** — each sentence is labeled with its dominant
  difficulty source (`syntax` / `vocabulary` / `information` / `balanced`).
- **Strategy routing** — the diagnosis selects the explanation strategy
  (Structure-first, Vocabulary-first, Meaning-first, Direct), which is then
  injected into the LLM prompt.
- **Reader-level adaptation** — undergrad / graduate / researcher profiles
  modulate explanation trade-offs jointly with text difficulty.
- **English-learning oriented output** — the LLM also emits grammar points
  (clause types, passive structures, collocations, domain vocabulary),
  like a teacher annotating a difficult sentence.
- **Feedback logging hooks** — simple UI buttons ready for a small-scale
  human evaluation (comprehension accuracy / perceived difficulty).

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
├── requirements.txt
└── LinguaMind-产品设计V1.html   # product design doc (architecture, data schema, PRD)
```

## Method Notes

- **Syntactic features** come from spaCy dependency parsing
  (tree depth, subordinate clauses, coordination, apposition).
- **Lexical difficulty** is currently a heuristic (word length ≥ 8 chars or
  academic suffixes). The roadmap replaces it with word frequency / CEFR
  levels / the Academic Word List.
- **Complexity score** = 0.40 × syntactic + 0.35 × lexical + 0.25 × information
  density (weights explicit and adjustable).
- The LLM output is forced to JSON (`response_format: json_object`) and parsed
  with a retry fallback.

## Roadmap

- **V1** — single sentences / paragraphs *(current)*
- **V1.1** — interpretable language diagnosis ✅ *(implemented)*
- **V1.2** — adaptive explanation strategy ✅ *(implemented)*
- **V1.3** — small-scale human evaluation (10–20 participants:
  comprehension accuracy, perceived difficulty, reading time)
- **V2** — PDF / long documents + RAG
- **V3** — personalized long-term reading profile

## License

MIT
