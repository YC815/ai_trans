from typing import Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

# 初始化用於校驗的 LLM
llm_checker = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

# 建立字串解析器
parser = StrOutputParser()

# 使用 LCEL 管道語法建立處理鏈
chain_checker = llm_checker | parser

# 將 prompt 的完整結構定義為一個多行 f-string
MANUAL_PROMPT_TEMPLATE = """
Compare the meaning of the "Original Text" and the "Back-Translated Text" below.
If the core meaning is consistent, please return the single word "pass".
Otherwise, return the single word "fail". Do not provide any other explanation.

Original Text:
{original}

Back-Translated Text:
{back_translation}
"""


def validate_back_translation(state: Dict) -> Dict:
    """
    使用 LLM 校驗回譯結果與原文的語意一致性。
    並將校驗結果 ("pass" 或 "fail") 存入 state。
    """
    print("--- 正在執行：語意一致性校驗 ---")

    # 我們只校驗最後一個段落，作為整個批次的代表
    original_segment = state.get("segments", [])[-1]
    back_translation_segment = state.get("back_translations", [])[-1]

    # 手動格式化 prompt
    prompt = MANUAL_PROMPT_TEMPLATE.format(
        original=original_segment,
        back_translation=back_translation_segment
    )

    # 呼叫 LLM 進行判斷
    verdict = chain_checker.invoke([HumanMessage(content=prompt)]).strip().lower()

    print(f"--- 校驗結果: {verdict} ---")

    # 將校驗結果存入 state，供後續的條件邊使用
    result = "pass" if "pass" in verdict else "fail"
    return {"validation_result": result}
