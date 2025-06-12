import json
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# 初始化 LLM 模型
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

# 建立一個提示模板 (PromptTemplate)
# 我們在模板中加入了格式化指令，引導 LLM 輸出 JSON
prompt = PromptTemplate(
    template="""
From the following Chinese text, list all proper nouns or domain-specific terms
and provide their English translations.
Return the result in JSON format.

**Text:**
{text}

**JSON Output:**
""",
    input_variables=["text"],
)

# 建立一個解析器，它會自動處理 LLM 的輸出，確保其為合法的 JSON 格式
parser = JsonOutputParser()

# 使用 LangChain Expression Language (LCEL) 的管道語法來建立處理鏈
# 這是 LangChain 推薦的現代化寫法
# 流程：輸入的字典 -> 填入 prompt -> 傳給 LLM -> 透過 parser 解析輸出
chain = prompt | llm | parser


def extract_glossary(state: Dict) -> Dict:
    """
    使用大型語言模型 (LLM) 從目前的段落中提取術語詞彙。
    """
    print("--- 正在執行(LLM)：擷取術語詞彙 ---")

    segments = state.get("segments", [])
    if not segments:
        return {"glossary": {}}

    full_text = "\n".join(segments)

    try:
        response = chain.invoke({"text": full_text})

        # 首先檢查回傳的是否為字典，並且包含我們預期的鍵
        if isinstance(response, dict):
            # 兼容 LLM 可能回傳 {"proper_nouns": [...]} 或 {"terms": [...]} 的情況
            glossary_list = response.get("proper_nouns", response.get("terms", []))
        elif isinstance(response, list):
            # 如果直接回傳列表，也接受
            glossary_list = response
        else:
            glossary_list = []

        if not glossary_list or not isinstance(glossary_list, list):
            print(f"--- 警告：LLM 回傳的術語表格式非預期或為空 ---")
            print(f"LLM 原始回覆：{response}")
            return {"glossary": {}}

        glossary_dict = {}
        for item in glossary_list:
            # 處理兩種可能的格式: {"term": "...", "translation": "..."} 或 {"中文": "English"}
            if "term" in item and "translation" in item:
                glossary_dict[item["term"]] = item["translation"]
            else:
                # 假設是 {"中文": "English"} 格式
                for term, translation in item.items():
                    glossary_dict[term] = translation
                    break  # 處理完第一個鍵值對就跳出

        print(f"--- 產生的詞彙表：{glossary_dict} ---")
        return {"glossary": glossary_dict}

    except Exception as e:
        print(f"--- 錯誤：執行術語提取鏈時發生問題 ---")
        print(f"錯誤訊息：{e}")
        return {"glossary": {}}
