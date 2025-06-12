# langgraph_translator/workflow.py

from typing import List, Dict, TypedDict, Optional
from langgraph.graph import StateGraph, END
from nodes.load_text import load_text
from nodes.extract_glossary import extract_glossary
from nodes.translate_segments import translate_segments
from nodes.update_glossary import update_glossary
from nodes.qa_back_translation import qa_back_translation
from nodes.validate_back_translate import validate_back_translation

# 新增：定義整個工作流程共享的「狀態」結構
# 這就像一張藍圖，告訴 LangGraph 在節點之間傳遞的資料包含哪些欄位和類型
# 使用 TypedDict 可以讓程式碼更清晰，也方便 LangGraph 進行管理


class GraphState(TypedDict):
    """
    代表我們工作流程圖的狀態。

    Attributes:
        source_file: Optional[str] - 要處理的來源檔案路徑。
        segments: List[str] - 從原始文章分割出來的段落列表。
        glossary: Dict[str, str] - 專有名詞及其翻譯的詞彙表。
        translated: List[str] - 已完成翻譯的段落列表。
        back_translations: List[str] - 反向翻譯的校驗結果列表。
        validation_result: Optional[str] - 用於儲存校驗結果 ('pass' or 'fail')
    """
    source_file: Optional[str]
    segments: List[str]
    # current_index: int
    glossary: Dict[str, str]
    translated: List[str]
    back_translations: List[str]
    validation_result: Optional[str]


def build_graph():
    """
    建立並設定 LangGraph 的工作流程圖。
    此版本包含條件邊，用於實現重試迴圈。
    """
    # 初始化一個狀態圖 (StateGraph)，並傳入我們定義好的狀態結構
    graph = StateGraph(GraphState)

    # 註冊流程中的所有節點
    # 每個節點都是一個工作單元，對應一個 Python 函式
    graph.add_node("load_text", load_text)
    graph.add_node("extract_glossary", extract_glossary)
    graph.add_node("translate_segments", translate_segments)
    graph.add_node("qa_back_translation", qa_back_translation)
    graph.add_node("validate_translation", validate_back_translation)
    graph.add_node("update_glossary", update_glossary)

    # 設定工作流程的「路徑」
    graph.set_entry_point("load_text")
    graph.add_edge("load_text", "extract_glossary")
    graph.add_edge("extract_glossary", "translate_segments")
    graph.add_edge("translate_segments", "qa_back_translation")
    graph.add_edge("qa_back_translation", "validate_translation")

    # 以 validate_translation 節點作為條件分支的起點
    graph.add_conditional_edges(
        "validate_translation",
        # 判斷函式：讀取 state 中的 validation_result
        lambda state: state.get("validation_result"),
        {
            "pass": "update_glossary",
            "fail": "translate_segments"
        }
    )

    graph.add_edge("update_glossary", END)

    # 編譯工作流程圖
    return graph.compile()
