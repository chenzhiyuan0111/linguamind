"""
LinguaMind · LLM 解释层 v0.5
===============================
输入：英文原文 + 语言分析模块输出的 JSON
输出：自适应双模式解释（简化 / 深度 + 语法点）JSON

设计要点
--------
- 不翻译，而是"先判断哪里难，再决定怎么讲"（estimated reading load 驱动）
- 困难类型 -> 解释策略路由：Structure-first / Vocabulary-first /
  Meaning-first / Direct（策略由分析结果决定，注入 Prompt 强制执行）
- 用户等级参与决策：文本难度 × 用户水平 -> 讲解取舍
- 支持 OpenAI 兼容接口（DeepSeek / 智谱 / 通义等），强制 JSON 输出
- API Key 从 .env 读取，绝不写死在代码里

配置（项目目录下建 .env 文件）
--------------------------------
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.deepseek.com        # 默认 DeepSeek，可换其他
LLM_MODEL=deepseek-chat                      # 默认 DeepSeek 模型，可换
"""
import json
import os
from pathlib import Path

import requests

# ---------- .env 读取（不依赖第三方库） ----------
def _load_env(env_path: str = ".env") -> None:
    p = Path(env_path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

_load_env(Path(__file__).parent / ".env")

API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# 解释策略路由：困难类型 -> 讲解策略（v0.4：让语言诊断决定解释方式）
STRATEGY = {
    "syntax": (
        "Structure-first",
        "主要困难在句法结构：先抽主干、拆从句、重组语序，再解释意义；"
        "简化模式给出一句话主干，深度模式给出结构拆解。"),
    "vocabulary": (
        "Vocabulary-first",
        "主要困难在词汇：先挑出关键术语并给出简洁释义，再解释整句；"
        "简化模式用大白话解释术语，深度模式给出术语的学术含义。"),
    "information": (
        "Meaning-first",
        "主要困难在信息密度与语义关系：先提取核心命题（propositions），"
        "再讲清命题之间的关系与必要背景，最后解释整句。"),
    "balanced": (
        "Direct",
        "各维度较均衡：直接按整体难度讲解即可，不必强调某一类策略。"),
    "low": (
        "Direct",
        "句子本身不复杂：直接解释即可，不必展开结构与术语。"),
}

# 用户等级规则：文本难度 × 用户水平 -> 讲解取舍（v0.4 真正参与决策）
LEVEL_RULE = {
    "undergrad": "读者为本科生：优先保证看懂大意；术语先解释再用；补充必要背景。",
    "graduate": "读者为研究生：保留术语与结构分析，讲清句法逻辑，可引用句子结构作支撑。",
    "researcher": "读者为科研人员：直接讨论学术内涵与理论语境，结构讲解从简。",
}


def build_messages(text: str, analysis: dict, user_level: str = "graduate") -> list:
    """构造 LLM 消息：困难诊断决定解释策略，用户等级决定讲解取舍。"""
    level_rule = LEVEL_RULE.get(user_level, LEVEL_RULE["graduate"])
    dtype = analysis.get("difficulty_type", "balanced")
    strategy_name, strategy_hint = STRATEGY.get(dtype, STRATEGY["balanced"])

    system = (
        "你是一位基于语言复杂度研究设计的英语阅读助教 LinguaMind。"
        "你会收到一段英文文本及其语言分析数据（句子长度、句法深度、从属结构、词汇难度、"
        "信息密度、困难诊断），这些数据用于估计文本对读者的理解难度（estimated reading load），"
        "而非实验测得的认知负荷。"
        "你的任务不是翻译，而是先判断这段文本哪里难，再决定怎么解释："
        "先让读者看懂'这段话在说什么'，再视需要深入结构、术语、语法点与学术背景。"
        "你必须严格执行给定的解释策略与用户水平规则。"
        "输出时请结合英语教学视角点出具体语法点（如从句类型、被动结构、搭配、领域词汇），"
        "帮助读者不仅读懂，还学到语言点。"
        "你只能用简体中文输出，并且必须严格输出 JSON 对象（不要输出任何其他文字）。"
    )

    user = (
        "请基于下面的文本与分析数据，生成解释。\n\n"
        f"【用户水平规则】{level_rule}\n\n"
        f"【困难诊断】主要困难来源：{dtype}（策略：{strategy_name}）\n"
        f"【解释策略】{strategy_hint}\n\n"
        f"【英文原文】\n{text}\n\n"
        f"【语言分析数据】\n{json.dumps(analysis, ensure_ascii=False)}\n\n"
        "【输出要求】严格输出如下结构的 JSON：\n"
        "{\n"
        '  "simple_explanation": "一句话大白话，讲清楚这段话说的是什么（不是逐词翻译；若句子嵌套，先讲主干再补细节）",\n'
        '  "deep_explanation": "学术级解释：说明句法结构（如嵌套从句/并列/插入语）、关键术语的学术含义、以及这句话在学术语境中的意义",\n'
        '  "key_difficulties": [{"term": "最难理解的词或短语", "plain": "给这个读者的通俗解释"}],\n'
        '  "grammar_points": [{"point": "语法点名称，如 When 引导时间状语从句 / 主句使用被动结构 / \\"transformed into\\"构成动词+介词搭配", "detail": "结合本句实例的一句话讲解，帮助读者学到语言点"}],\n'
        '  "recommended_mode": "根据 estimated reading load 建议：high 建议 simple，low 建议 deep，medium 按用户等级折中" \n'
        "}\n"
        "key_difficulties 只挑真正影响理解的 2-4 项，术语优先取自分析数据中的 difficult_words。\n"
        "grammar_points 输出 2-4 条，优先结合语法线索（clause_types 从句类型、passive_voice 被动结构、"
        "coordination_count 并列）与 technical_terms 领域词汇，像英语老师在长难句讲解中标注语法点那样。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_llm(messages: list) -> dict:
    """调用 OpenAI 兼容 /chat/completions 接口，返回解析后的 JSON dict。"""
    if not API_KEY:
        raise RuntimeError(
            "未配置 LLM API Key：请在 lingua-mind/.env 中写入 LLM_API_KEY=sk-xxx"
        )
    url = f"{BASE_URL}/chat/completions"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 1000,
        },
        timeout=90,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def explain(text: str, analysis: dict, user_level: str = "graduate") -> dict:
    """主入口：原文 + 分析 -> 自适应双模式解释。LLM 返回异常时自动重试一次。"""
    messages = build_messages(text, analysis, user_level)
    try:
        return call_llm(messages)
    except (json.JSONDecodeError, KeyError):
        # 偶发非 JSON 返回，重试一次
        return call_llm(messages)


if __name__ == "__main__":
    # Demo：跑通「语言分析 -> LLM 解释」完整链路
    from lingua_analysis import analyze_sentence

    sample = (
        "The interaction between semantic interference and syntactic complexity "
        "places a heavy burden on the reader's working memory."
    )
    analysis = analyze_sentence(sample)

    print("== 语言分析 ==")
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    print("\n== LLM 解释 ==")
    try:
        result = explain(sample, analysis, user_level="graduate")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except RuntimeError as e:
        print(f"[提示] {e}")
        print("拿到 API Key 后：在 lingua-mind/.env 里写一行 LLM_API_KEY=sk-xxx 再运行即可。")
    except Exception as e:  # noqa: BLE001
        print(f"[调用失败] {type(e).__name__}: {e}")
