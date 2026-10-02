"""
LinguaMind · Streamlit 演示界面 v0.5
====================================
把「语言复杂度分析 -> 难度诊断 -> AI 自适应讲解」串成可交互 demo。

v0.5 改进
---------
- 严谨化：字段 cognitive_load_level 更名为 reading_difficulty_level
- 新增难度画像 Difficulty profile：三个维度 High/Medium/Low + Main drivers，
  从"一个分数"升级为"可解释的语言诊断"
- 文案："先分析这段文字为什么难，再决定怎么讲。"

运行（独立环境）：
    cd /Users/chenzhiyuan/Doubao/chats/2026-09-28/new-chat/lingua-mind
    .venv/bin/streamlit run streamlit_app.py
"""
import streamlit as st

from lingua_analysis import analyze_sentence, _NLP
from lingua_explain import explain, API_KEY

st.set_page_config(
    page_title="LinguaMind · Linguistic-Aware Reading Assistant",
    layout="wide",
)

LEVELS = {
    "undergrad": "本科生（多讲背景概念）",
    "graduate": "研究生（重结构逻辑与术语）",
    "researcher": "科研人员（直击学术内涵）",
}
LEVEL_TO_KEY = {v: k for k, v in LEVELS.items()}

LOAD_TAG = {"low": ":green[低难度]", "medium": ":orange[中难度]", "high": ":red[高难度]"}

METRIC_CN = {
    "sentence_length": "句子长度",
    "syntactic_depth": "句法深度",
    "subordination": "从属结构",
    "lexical_difficulty": "词汇难度",
    "content_word_density": "实词密度",
    "structural_complexity": "结构复杂度",
}
DIM_CN = {
    "syntactic_complexity": "句法复杂度",
    "lexical_difficulty": "词汇难度",
    "information_density": "信息密度",
}

DIFF_TYPE_CN = {
    "syntax": "句法结构",
    "vocabulary": "词汇难度",
    "information": "信息密度/语义",
    "balanced": "整体均衡",
    "low": "无明显困难",
}
STRATEGY_CN = {
    "syntax": "Structure-first · 先抽主干拆从句",
    "vocabulary": "Vocabulary-first · 先讲关键术语",
    "information": "Meaning-first · 先讲意义关系与背景",
    "balanced": "Direct · 直接讲解",
    "low": "Direct · 直接讲解",
}

# 维度水平分档（与难度等级阈值一致）
def _level_of(score: float) -> str:
    return "High" if score >= 6.5 else ("Medium" if score >= 3.5 else "Low")

# 叶子指标 -> 人类可读的驱动因素描述（用于 Main drivers）
DRIVER_TEXT = {
    "sentence_length": lambda v: f"长句（{v['value']}词）",
    "syntactic_depth": lambda v: f"深依存结构（深度{v['value']}）",
    "subordination": lambda v: f"{v['value']}个嵌入从句",
    "lexical_difficulty": lambda v: f"{round(v['value'] * 100)}%难词",
    "content_word_density": lambda v: "高实词密度",
    "structural_complexity": lambda v: f"{v['value']}处并列/插入结构",
}

# ---------- 侧边栏：读者设置 ----------
with st.sidebar:
    st.title("LinguaMind")
    st.caption("A linguistic-aware LLM application")
    st.divider()
    st.subheader("读者设置")
    level_label = st.selectbox("你的水平", list(LEVELS.values()))
    user_level = LEVEL_TO_KEY[level_label]
    st.caption("读者等级会影响讲解深度：本科生多讲背景，研究生重理论。")
    st.divider()
    if API_KEY:
        st.success("LLM 已配置，讲解功能可用")
    else:
        st.warning("未配置 LLM_API_KEY，只能做语言分析")

st.title("AI 英语阅读助手")
st.caption("先分析这段文字为什么难，再决定怎么讲。")

# ---------- 输入 ----------
st.subheader("输入英文文本")
text = st.text_area(
    "可粘贴单句或整段",
    height=140,
    placeholder="The interaction between semantic interference and syntactic complexity places a heavy burden on the reader's working memory.",
)

if st.button("开始分析", type="primary"):
    if not text.strip():
        st.warning("先粘贴一段英文文本再点分析。")
        st.stop()
    sents = [s.text.strip() for s in _NLP(text).sents if s.text.strip()]
    rows = [(s, analyze_sentence(s)) for s in sents]
    st.session_state["rows"] = rows

# ---------- 分析结果 ----------
if "rows" in st.session_state:
    rows = st.session_state["rows"]
    st.divider()
    st.subheader(f"分析结果 · 共 {len(rows)} 句")

    if rows:
        avg = sum(r["complexity_score"] for _, r in rows) / len(rows)
        hardest = max(rows, key=lambda x: x[1]["complexity_score"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("句子数", len(rows))
        c2.metric("平均复杂度", round(avg, 1))
        c3.metric("最高复杂度", round(hardest[1]["complexity_score"], 1))
        c4.metric("最难句", LOAD_TAG[hardest[1]["reading_difficulty_level"]].replace("难度", ""))

        st.markdown("#### 逐句分析")
        for i, (s, r) in enumerate(rows):
            lv = r["reading_difficulty_level"]
            with st.expander(f"句 {i + 1} · 复杂度 {r['complexity_score']} · {LOAD_TAG[lv]}"):
                st.write(s)

                # 困难诊断：主要来源 + 讲解策略
                dt = r.get("difficulty_type", "balanced")
                st.markdown(
                    f"**主要困难：{DIFF_TYPE_CN[dt]}** → 讲解策略：**{STRATEGY_CN[dt]}**"
                )

                # 难度画像：三维度水平
                prof = " · ".join(
                    f"{DIM_CN[k]} **{_level_of(v['score'])}**"
                    for k, v in r["dimensions"].items()
                )
                st.markdown(f"**难度画像：** {prof}")

                # 主要驱动因素（高分叶子指标）
                drivers = [
                    DRIVER_TEXT[k](v)
                    for k, v in r["metrics"].items()
                    if v.get("score", 0) >= 5
                ]
                if drivers:
                    st.markdown("**主要驱动因素：** " + " · ".join(drivers))
                else:
                    st.markdown("**主要驱动因素：** 无（句子结构简单）")

                # 叶子指标明细 + 加权公式（可审计）
                leaf = "  ·  ".join(
                    f"{METRIC_CN[k]} {v['value']}→{v['score']}分" for k, v in r["metrics"].items()
                )
                st.caption(f"**明细指标：** {leaf}")
                dim = " + ".join(
                    f"{DIM_CN[k]} {v['score']}×{v['weight']}" for k, v in r["dimensions"].items()
                )
                st.caption(f"**总分公式：** 复杂度 = {dim} = **{r['complexity_score']}**")

                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("查看完整分析数据"):
                        st.json(r)
                with col2:
                    st.caption(f"主干：{r['sentence_analysis']['structure']}")
                    st.caption(f"难词 {len(r['vocabulary']['difficult_words'])} 个 · "
                               f"名词 {r['info_density']['noun_count']} 个 · "
                               f"术语 {len(r['info_density']['technical_terms'])} 个")

        # ---------- LLM 自适应讲解 ----------
        st.divider()
        st.subheader("AI 自适应讲解")
        if not API_KEY:
            st.info("在 .env 中配置 LLM_API_KEY 后即可生成讲解。")
            st.stop()

        st.caption("默认选中全篇最难的一句，也可手动换句。")
        sel_index = st.selectbox(
            "选择要讲解的句子",
            range(len(rows)),
            format_func=lambda i: f"句 {i + 1}（复杂度 {rows[i][1]['complexity_score']}）",
        )
        sel_s, sel_r = rows[sel_index]

        with st.spinner("AI 正在根据语言复杂度生成讲解…"):
            exp = explain(sel_s, sel_r, user_level)

        tab_simple, tab_deep, tab_grammar = st.tabs(["简化模式", "深度模式", "语法点讲解"])
        with tab_simple:
            st.markdown(exp["simple_explanation"])
        with tab_deep:
            st.markdown(exp["deep_explanation"])
        with tab_grammar:
            for g in exp.get("grammar_points", []):
                st.markdown(f"**{g['point']}** — {g['detail']}")

        st.markdown(f"**建议模式：** `{exp['recommended_mode']}`")
        with st.expander("难点词解释"):
            for d in exp["key_difficulties"]:
                st.markdown(f"**{d['term']}** — {d['plain']}")

        # ---------- 反馈埋点（评价指标） ----------
        st.divider()
        st.caption("这个讲解对你理解有帮助吗？反馈用于改进讲解效果。")
        c1, c2 = st.columns(2)
        if c1.button("有帮助", use_container_width=True):
            st.session_state["fb_pos"] = st.session_state.get("fb_pos", 0) + 1
            st.success(f"已记录 · 累计 {st.session_state['fb_pos']} 次正面反馈")
        if c2.button("没帮助", use_container_width=True):
            st.session_state["fb_neg"] = st.session_state.get("fb_neg", 0) + 1
            st.info(f"已记录 · 累计 {st.session_state['fb_neg']} 次负面反馈")
