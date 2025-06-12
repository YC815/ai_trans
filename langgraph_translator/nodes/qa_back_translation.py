# nodes/qa_back_translation.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

# 初始化 LLM 模型
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

# 建立字串解析器
parser = StrOutputParser()

# 使用 LCEL 管道語法建立處理鏈
chain = llm | parser

# 將 prompt 的完整結構定義為一個多行 f-string
# 避免使用 PromptTemplate 來規避潛在的格式化問題
MANUAL_PROMPT_TEMPLATE = """
As a literal translator, please translate the target language text back to the source language as word-for-word as possible.
Provide only the translated text without any extra explanation.

Source Text (for context, do not translate this):
{orig}

Target Text (to be translated back):
{translation}

Back-translation to Source Language:
"""


def qa_back_translation(state):
    """
    對已翻譯的段落進行反向翻譯，以進行品質校驗。
    """
    print("--- 正在執行：反向翻譯校驗 ---")

    segments = state.get("segments", [])
    translations = state.get("translated", [])

    back_texts = []
    for orig, trans in zip(segments, translations):
        # 手動格式化 prompt
        prompt = MANUAL_PROMPT_TEMPLATE.format(orig=orig, translation=trans)

        # 將格式化好的 prompt 包裝成 HumanMessage
        response = chain.invoke([HumanMessage(content=prompt)])
        back_texts.append(response.strip())

    state["back_translations"] = back_texts
    print("--- 反向翻譯校驗完成 ---")
    return state
