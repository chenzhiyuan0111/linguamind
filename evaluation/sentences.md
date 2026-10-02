# Pilot Evaluation — Stimuli

10 English sentences selected to cover three dominant difficulty profiles
(syntax-dominant / vocabulary-dominant / balanced).

> **Note on information-dominant**: under the current heuristic, an
> information-dominant label is rare in academic text, because long content
> words simultaneously raise both the lexical and the information-density
> dimensions (feature overlap). This is a known limitation of the v0.5
> heuristic and a motivation for better lexical difficulty features
> (frequency / CEFR / Academic Word List) in a later version.

Each participant will read the same sentences twice:
- **Version A** — baseline LLM explanation
- **Version B** — LinguaMind adaptive explanation

Order is counterbalanced across participants (half see A first, half see B first).

## Stimuli

| # | Sentence | difficulty_type | score |
|---|----------|-----------------|-------|
| 1 | The interaction between semantic interference and syntactic complexity places a heavy burden on the reader's working memory. | vocabulary | 7.5 |
| 2 | The utilization of sophisticated methodologies in contemporary pedagogical contexts facilitates efficacious learning outcomes across diverse learner populations. | vocabulary | 7.9 |
| 3 | The acquisition of proficiency in a second language is contingent upon the consolidation of vocabulary knowledge and the automatization of syntactic processing. | vocabulary | 8.1 |
| 4 | The boy who was chased by the dog that belonged to the man who lived next door ran into the street that crossed the old bridge. | syntax | 4.1 |
| 5 | Although she tried to finish the report that her boss had asked her to write before the meeting that was scheduled for Friday, she failed because the power went out. | syntax | 4.8 |
| 6 | It was the kind of sentence that, although it looked simple at first, turned out to be much harder than anyone had expected when they tried to explain it. | syntax | 5.1 |
| 7 | Despite the fact that the underlying mechanisms of semantic interference remain poorly understood, the present findings provide compelling evidence that working memory capacity is significantly constrained by the simultaneous processing of multiple sources of linguistic information. | balanced | 8.7 |
| 8 | Although the results of the second experiment contradicted the predictions derived from the computational model, the authors attributed the discrepancy to measurement error rather than to a fundamental flaw in the theoretical framework. | balanced | 8.8 |
| 9 | Results show that training improves speed, that practice reduces errors, and that feedback changes strategy use in most learners. | balanced | 7.4 |
| 10 | Data from three studies on memory in children with learning difficulties suggest that both the amount of practice and the type of feedback matter for progress. | balanced | 6.9 |

*(difficulty_type / score computed by `lingua_analysis.py` v0.5, 2026-10-02)*
