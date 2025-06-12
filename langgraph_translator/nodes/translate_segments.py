import json
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tenacity import retry, stop_after_attempt, wait_fixed

# 初始化 LLM (開啟流式輸出)
# streaming=True 允許我們在將來實現即時的 token 回饋
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo", streaming=True)

# 建立一個提示模板
prompt = PromptTemplate.from_template(
    """
You are a professional translator.
Translate the following Chinese text to English.
You **MUST** strictly adhere to the glossary provided below for terminology.

**Glossary:**
{glossary_str}

**Chinese Original:**
{segment}

**English Translation:**
"""
)

# 建立一個字串解析器
parser = StrOutputParser()

# 使用 LCEL 管道語法建立處理鏈
chain = prompt | llm | parser

# 使用 tenacity 加入重試機制：最多重試 3 次，每次失敗後等待 2 秒
# 這確保了即使 LLM API 暫時出錯，我們的流程也能夠嘗試恢復


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_translation_with_retry(segment: str, glossary_str: str) -> str:
    """
    帶有重試機制的翻譯呼叫函式。
    """
    print(f"--- 嘗試翻譯段落... ---")
    response = chain.invoke({
        "segment": segment,
        "glossary_str": glossary_str
    })
    return response.strip()


def translate_segments(state: Dict) -> Dict:
    """
    使用大型語言模型 (LLM) 翻譯所有段落，並遵循術語表。
    此版本加入了重試機制。
    """
    print("--- 正在執行(LLM)：翻譯段落 (帶重試機制) ---")

    segments = state.get("segments", [])
    glossary = state.get("glossary", {})

    # 為了讓 LLM 能清晰讀懂，我們將術語表字典轉換成更易讀的字串格式
    # 例如：- 人工智慧 (rén gōng zhì néng): Artificial Intelligence
    glossary_str = "\n".join(
        [f"- {term}: {translation}" for term, translation in glossary.items()]
    )
    if not glossary_str:
        glossary_str = "N/A"  # 如果沒有術語，明確告知 LLM

    translated_segments = []
    for i, segment in enumerate(segments):
        try:
            # 呼叫有重試機制的翻譯函式
            translation = call_translation_with_retry(
                segment=segment,
                glossary_str=glossary_str
            )
            print(f"--- 段落 {i+1} 翻譯成功 ---")
            # 在此處，streaming=True 的效果是讓 invoke 的過程更快回傳第一個 token
            # 完整的流式處理需要在呼叫端使用 .stream() 而非 .invoke()
            # 為了流程簡潔，我們這裡仍然使用 invoke，但保留了流式輸出的能力
            print(f"翻譯結果: {translation}")
            translated_segments.append(translation)
        except Exception as e:
            # 如果重試 3 次後仍然失敗，則記錄錯誤並跳過該段落
            print(f"--- 錯誤：翻譯段落 {i+1} 失敗，已達最大重試次數 ---")
            print(f"最終錯誤訊息: {e}")
            # 可以選擇加入一個錯誤標記，或是一個空的翻譯
            translated_segments.append(f"[翻譯失敗: {e}]")

    return {"translated": translated_segments}
