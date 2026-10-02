"""
LinguaMind · Pilot Evaluation Runner
====================================
For each stimulus sentence, generate two explanations:
  - baseline  : generic LLM explanation (plain prompt)
  - adaptive  : LinguaMind (linguistic analysis → strategy routing → prompt)

Usage (from the lingua-mind directory, with .env configured):
    .venv/bin/python evaluation/run_comparison.py
    .venv/bin/python evaluation/run_comparison.py --limit 2

Output: evaluation/results/comparison.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from lingua_analysis import analyze_sentence
from lingua_explain import explain, API_KEY, BASE_URL, MODEL

# 10 stimuli covering three dominant difficulty profiles
# (vocabulary ×3 / syntax ×3 / balanced ×4); information-dominant is rare
# under the current heuristic — see README Method Notes.
STIMULI = [
    # vocabulary-dominant
    "The interaction between semantic interference and syntactic complexity places a heavy burden on the reader's working memory.",
    "The utilization of sophisticated methodologies in contemporary pedagogical contexts facilitates efficacious learning outcomes across diverse learner populations.",
    "The acquisition of proficiency in a second language is contingent upon the consolidation of vocabulary knowledge and the automatization of syntactic processing.",
    # syntax-dominant (simple words, nested structures)
    "The boy who was chased by the dog that belonged to the man who lived next door ran into the street that crossed the old bridge.",
    "Although she tried to finish the report that her boss had asked her to write before the meeting that was scheduled for Friday, she failed because the power went out.",
    "It was the kind of sentence that, although it looked simple at first, turned out to be much harder than anyone had expected when they tried to explain it.",
    # balanced
    "Despite the fact that the underlying mechanisms of semantic interference remain poorly understood, the present findings provide compelling evidence that working memory capacity is significantly constrained by the simultaneous processing of multiple sources of linguistic information.",
    "Although the results of the second experiment contradicted the predictions derived from the computational model, the authors attributed the discrepancy to measurement error rather than to a fundamental flaw in the theoretical framework.",
    "Results show that training improves speed, that practice reduces errors, and that feedback changes strategy use in most learners.",
    "Data from three studies on memory in children with learning difficulties suggest that both the amount of practice and the type of feedback matter for progress.",
]

BASELINE_SYSTEM = "You are an English reading assistant. Answer in Chinese."
BASELINE_USER = (
    "Please explain the following English sentence in simple Chinese. "
    "Make it clear and easy to understand.\n\nSentence: {sentence}"
)


def call_plain_llm(sentence: str) -> str:
    """Baseline: plain LLM call without linguistic analysis or JSON constraints."""
    if not API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，请在 .env 中写入。")
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": BASELINE_SYSTEM},
                {"role": "user", "content": BASELINE_USER.format(sentence=sentence)},
            ],
            "temperature": 0.3,
            "max_tokens": 600,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=len(STIMULI), help="只跑前 N 句（试跑用）")
    args = parser.parse_args()

    results = []
    for i, sentence in enumerate(STIMULI[: args.limit], 1):
        print(f"[{i}/{args.limit}] analyzing...")
        analysis = analyze_sentence(sentence)
        print(f"  difficulty_type={analysis['difficulty_type']} "
              f"score={analysis['complexity_score']}")
        print("  baseline...")
        baseline = call_plain_llm(sentence)
        print("  adaptive...")
        adaptive = explain(sentence, analysis, user_level="graduate")
        results.append({
            "id": i,
            "sentence": sentence,
            "difficulty_type": analysis["difficulty_type"],
            "complexity_score": analysis["complexity_score"],
            "baseline": baseline,
            "adaptive": adaptive,
        })
        print("  done.\n")

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "comparison.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
