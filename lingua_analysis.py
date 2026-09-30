"""
LinguaMind · 语言分析模块 v0.2（可解释指标体系）
=================================================
输入英文句子 -> 输出结构化分析 JSON

v0.2 改进
---------
- 复杂度拆分为明确的叶子指标（Sentence Length / Syntactic Depth /
  Subordination / Lexical Difficulty / Content-word Density /
  Structural Complexity），每项给出 0-10 分与依据值
- 三个维度加权合成总复杂度，权重完全透明、可审计：
      Complexity Score = w1*syntactic + w2*lexical + w3*information
- 附加 syntax_clues（被动 / 从句类型 / 并列等），供 LLM 讲解英语语法点

运行方式（独立环境）:
    .venv/bin/python lingua_analysis.py
"""
import json
import spacy

# 模型全局只加载一次
_NLP = spacy.load("en_core_web_sm")

# ---------- 启发式规则（v0.2，后续可换真实词表） ----------
ACADEMIC_SUFFIXES = ("tion", "ity", "ence", "ance", "ive", "al", "ism",
                     "ment", "ology", "graphy", "able", "ible", "ical", "ize", "ise")
FUNCTION_POS = {"DET", "ADP", "CCONJ", "SCONJ", "PRON", "PART", "AUX", "PUNCT", "SPACE"}

# 从属从句标记
CLAUSE_DEPS = {"advcl", "relcl", "ccomp", "xcomp", "acl", "csubj"}

# 维度权重（可调，面试可讲：句法负荷权重最高，符合语言加工研究）
WEIGHTS = {
    "syntactic_complexity": 0.40,
    "lexical_difficulty": 0.35,
    "information_density": 0.25,
}
# 句法维度内部的叶子权重
_SYN_WEIGHTS = {"length": 0.30, "depth": 0.30, "subordination": 0.25, "structural": 0.15}
# 信息密度维度内部的叶子权重
_INF_WEIGHTS = {"content_density": 0.50, "technical_ratio": 0.50}


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def analyze_sentence(text: str) -> dict:
    """对单个英文句子做多维语言分析，返回可解释的指标 JSON。"""
    doc = _NLP(text)
    tokens = [t for t in doc if not t.is_space]
    n = len(tokens)
    content_words = [t for t in tokens if t.pos_ not in FUNCTION_POS]

    if not tokens:
        return {
            "text": text,
            "metrics": {},
            "dimensions": {},
            "weights": WEIGHTS,
            "complexity_score": 0.0,
            "cognitive_load_level": "low",
            "difficulty_type": "low",
            "dimension_contributions": {},
            "vocabulary": {"difficult_words": [], "academic_word_ratio": 0.0},
            "info_density": {"noun_count": 0, "technical_terms": []},
            "syntax_clues": {"passive_voice": False, "clause_types": [],
                             "coordination_count": 0, "apposition_count": 0},
            "sentence_analysis": {"structure": "empty", "difficulty_reason": "empty input"},
        }

    # ---------- 基础测量值 ----------
    head_idx = {t.i: t.head.i for t in tokens}

    def depth(i):
        d, guard = 0, 0
        while head_idx.get(i, i) != i and guard < 50:
            i = head_idx[i]
            d += 1
            guard += 1
        return d

    max_depth = max(depth(t.i) for t in tokens)

    clause_deps = sorted({t.dep_ for t in tokens if t.dep_ in CLAUSE_DEPS})
    nested = len(clause_deps)
    conj_count = sum(1 for t in tokens if t.dep_ == "conj")
    appos = sum(1 for t in tokens if t.dep_ in ("appos", "parataxis"))

    # 词汇难度（难词：长词 >=8 或学术后缀；只统计实词）
    difficult = []
    for t in content_words:
        base = t.lemma_.lower()
        is_long = len(base) >= 8
        is_acad = base.endswith(ACADEMIC_SUFFIXES)
        if is_long or is_acad:
            difficult.append({
                "word": t.text,
                "lemma": base,
                "is_academic": bool(is_acad),
                "hint": "long" if is_long else "academic_suffix",
            })
    seen, uniq = set(), []
    for w in difficult:
        if w["lemma"] not in seen:
            seen.add(w["lemma"])
            uniq.append(w)

    content_ratio = len(content_words) / max(n, 1)
    difficult_ratio = len(uniq) / max(len(content_words), 1)
    academic_ratio = len([w for w in uniq if w["is_academic"]]) / max(len(content_words), 1)

    noun_count = sum(1 for t in tokens if t.pos_ in ("NOUN", "PROPN"))
    technical_terms = [
        t.text for t in tokens
        if t.pos_ in ("NOUN", "PROPN")
        and (len(t.text) >= 8 or t.lemma_.lower().endswith(ACADEMIC_SUFFIXES))
    ]
    technical_ratio = len(technical_terms) / max(len(content_words), 1)

    # ---------- 叶子指标评分（0-10，依据值 + 映射规则） ----------
    metrics = {
        "sentence_length": {
            "value": n, "score": round(_clamp01(n / 30) * 10, 1),
            "rule": "词数/30，满分 10"},
        "syntactic_depth": {
            "value": max_depth, "score": round(_clamp01(max_depth / 6) * 10, 1),
            "rule": "依存深度/6，满分 10"},
        "subordination": {
            "value": nested, "score": round(_clamp01(nested / 3) * 10, 1),
            "rule": "从句嵌套数/3，满分 10"},
        "lexical_difficulty": {
            "value": round(difficult_ratio, 2), "score": round(_clamp01(difficult_ratio / 0.5) * 10, 1),
            "rule": "难词占实词比例/0.5，满分 10"},
        "content_word_density": {
            "value": round(content_ratio, 2), "score": round(_clamp01(content_ratio / 0.6) * 10, 1),
            "rule": "实词占比/0.6，满分 10"},
        "structural_complexity": {
            "value": conj_count + appos, "score": round(_clamp01((conj_count + appos) / 3) * 10, 1),
            "rule": "(并列+插入)数/3，满分 10"},
    }

    # ---------- 维度聚合 ----------
    syn = (_SYN_WEIGHTS["length"] * metrics["sentence_length"]["score"]
           + _SYN_WEIGHTS["depth"] * metrics["syntactic_depth"]["score"]
           + _SYN_WEIGHTS["subordination"] * metrics["subordination"]["score"]
           + _SYN_WEIGHTS["structural"] * metrics["structural_complexity"]["score"])
    lex = metrics["lexical_difficulty"]["score"]
    inf = (_INF_WEIGHTS["content_density"] * metrics["content_word_density"]["score"]
           + _INF_WEIGHTS["technical_ratio"] * _clamp01(technical_ratio / 0.3) * 10)

    dimensions = {
        "syntactic_complexity": {"score": round(syn, 1), "weight": WEIGHTS["syntactic_complexity"]},
        "lexical_difficulty": {"score": round(lex, 1), "weight": WEIGHTS["lexical_difficulty"]},
        "information_density": {"score": round(inf, 1), "weight": WEIGHTS["information_density"]},
    }

    complexity_score = round(
        WEIGHTS["syntactic_complexity"] * syn
        + WEIGHTS["lexical_difficulty"] * lex
        + WEIGHTS["information_density"] * inf, 1)

    if complexity_score < 3.5:
        level = "low"
    elif complexity_score <= 6.5:
        level = "medium"
    else:
        level = "high"

    # ---------- 困难诊断：哪个维度贡献最大 ----------
    tot = complexity_score if complexity_score > 0 else 0.01
    dimension_contributions = {
        "syntactic_complexity": round(syn * WEIGHTS["syntactic_complexity"] / tot, 2),
        "lexical_difficulty": round(lex * WEIGHTS["lexical_difficulty"] / tot, 2),
        "information_density": round(inf * WEIGHTS["information_density"] / tot, 2),
    }
    _DIM_TYPE = {
        "syntactic_complexity": "syntax",
        "lexical_difficulty": "vocabulary",
        "information_density": "information",
    }
    top_dim = max(dimension_contributions, key=dimension_contributions.get)
    if complexity_score < 3.5:
        difficulty_type = "low"
    else:
        top_score = {
            "syntactic_complexity": syn,
            "lexical_difficulty": lex,
            "information_density": inf,
        }[top_dim]
        if dimension_contributions[top_dim] >= 0.36 and top_score >= 5:
            difficulty_type = _DIM_TYPE[top_dim]
        else:
            difficulty_type = "balanced"

    # ---------- 语法线索（供 LLM 讲英语语法点） ----------
    passive = any(t.dep_ == "auxpass" or t.dep_ == "nsubjpass" for t in tokens)
    syntax_clues = {
        "passive_voice": passive,
        "clause_types": clause_deps,
        "coordination_count": conj_count,
        "apposition_count": appos,
    }

    # ---------- 主干提取（索引比较） ----------
    root = next((t for t in tokens if t.dep_ == "ROOT"), None)
    if root is not None:
        subj = next((t.text for t in tokens if t.head.i == root.i and t.dep_ in ("nsubj", "nsubjpass")), None)
        obj = next((t.text for t in tokens if t.head.i == root.i and t.dep_ in ("dobj", "attr", "ccomp")), None)
        structure = f"{subj or '...'} {root.text} {obj or '...'}"
    else:
        structure = "unparsed"

    return {
        "text": text,
        "metrics": metrics,
        "dimensions": dimensions,
        "weights": WEIGHTS,
        "complexity_score": complexity_score,
        "cognitive_load_level": level,
        "difficulty_type": difficulty_type,
        "dimension_contributions": dimension_contributions,
        "vocabulary": {
            "difficult_words": uniq,
            "academic_word_ratio": round(academic_ratio, 2),
        },
        "info_density": {
            "noun_count": noun_count,
            "technical_terms": technical_terms,
        },
        "syntax_clues": syntax_clues,
        "sentence_analysis": {
            "structure": structure,
            "difficulty_reason": (
                "high syntactic load" if nested >= 2 else
                "long sentence" if n >= 25 else
                "dense vocabulary" if len(uniq) >= 4 else "moderate"),
        },
    }


if __name__ == "__main__":
    sample = ("The interaction between semantic interference and syntactic "
              "complexity places a heavy burden on the reader's working memory.")
    print(json.dumps(analyze_sentence(sample), ensure_ascii=False, indent=2))
