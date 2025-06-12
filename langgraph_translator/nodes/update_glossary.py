import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser

# 初始化 LLM 模型
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

# 建立 JSON 解析器
parser = JsonOutputParser()

# 我們的處理鏈現在簡化為：LLM -> 解析器
# 我們將在函式內部手動建立完整的 prompt
chain = llm | parser

# 將 prompt 的完整結構定義為一個多行 f-string
# 這樣可以完全控制傳遞給 LLM 的內容，避免任何自動格式化問題
MANUAL_PROMPT_TEMPLATE = """
System:
You are a terminology expert responsible for maintaining a bilingual glossary.
Based on the translated English text provided, identify any new technical terms or proper nouns that are NOT already in the existing glossary.
For each new term found, provide a plausible Chinese translation.
Return the results as a standard JSON list of objects. If no new terms are found, return an empty list [].

---
Human:
**Translated English Text:**
The Falcon 9 rocket, developed by SpaceX, is partially reusable.

**Existing Glossary:**
{{
  "SpaceX": "Space Exploration Technologies Corp."
}}

---
AI:
[
  {{
    "term": "獵鷹九號",
    "translation": "Falcon 9"
  }}
]

---
Human:
**Translated English Text:**
{translations_str}

**Existing Glossary:**
{glossary_str}
"""


def update_glossary(state: Dict) -> Dict:
    """
    使用 LLM 驗證翻譯結果並擴充詞彙表（手動格式化 Prompt）。
    """
    print("--- 正在執行(LLM)：更新詞彙表 (手動 Prompt) ---")

    glossary = state.get("glossary", {})
    translated_segments = state.get("translated", [])
    if not translated_segments:
        return {}

    translations_str = "\n".join(translated_segments)
    # 這裡的 glossary_str 是為了填入 prompt，所以使用 json.dumps
    glossary_str = json.dumps(glossary, ensure_ascii=False, indent=2)

    # 手動填入 prompt 模板
    # 注意：在 f-string 中，要顯示大括號本身，需要使用雙大括號 {{ 和 }}
    # 但由於我們是用 .format()，所以不需要
    full_prompt = MANUAL_PROMPT_TEMPLATE.format(
        translations_str=translations_str,
        glossary_str=glossary_str
    )

    try:
        # 將格式化好的完整 prompt 包裝成 HumanMessage 傳給 invoke
        response = chain.invoke([HumanMessage(content=full_prompt)])

        if not response or not isinstance(response, list):
            print("--- 未發現新術語或回傳格式不符 ---")
            return {}

        updated_glossary = glossary.copy()
        new_terms_added = 0
        for item in response:
            term = item.get("term")
            translation = item.get("translation")
            if term and translation and term not in updated_glossary:
                print(f"--- 發現並新增術語：{term} -> {translation} ---")
                updated_glossary[term] = translation
                new_terms_added += 1

        if new_terms_added == 0:
            print("--- 未發現可新增的術語 ---")

        if new_terms_added > 0:
            return {"glossary": updated_glossary}
        else:
            return {}

    except Exception as e:
        print(f"--- 錯誤：執行術語更新鏈時發生問題 ---")
        print(f"錯誤訊息：{e}")
        return {}
