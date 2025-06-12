# langgraph_translator/nodes/load_text.py

from typing import Dict, List
import os
import re


def load_text(state: Dict) -> Dict:
    """
    從指定檔案路徑載入文字並進行分段。

    這個節點會從 state 字典中讀取 'source_file' 的路徑，
    讀取該檔案的內容，然後將其分割成段落。
    """
    print("--- 正在執行：載入與分段文字 ---")

    # 從 state 中獲取來源檔案路徑
    source_file = state.get("source_file")
    if not source_file or not os.path.exists(source_file):
        # 如果檔案路徑不存在或檔案不存在，可以拋出錯誤或回傳一個錯誤狀態
        raise FileNotFoundError(f"指定的來源檔案不存在或路徑錯誤: {source_file}")

    # 讀取檔案內容
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            article = f.read()
    except Exception as e:
        raise IOError(f"讀取檔案 {source_file} 時發生錯誤: {e}")

    # 1. 模擬分段：使用正則表達式來處理中英文的句號（. 和 。）
    # 這樣可以確保無論是中文還是英文文章都能被正確切分
    raw_segments: List[str] = [seg.strip() for seg in re.split(r'[.。]', article) if seg.strip()]

    # 2. 重新組合：將句子兩兩合併，控制每段的長度，避免過長
    segments: List[str] = []
    if raw_segments:
        # 如果只有一句話，也把它當成一個段落
        if len(raw_segments) == 1:
            segments.append(raw_segments[0] + '.')
        else:
            # 處理多句話的情況
            buffer: List[str] = []
            for i, sent in enumerate(raw_segments):
                buffer.append(sent + '.')  # 將句號加回去
                # 如果緩衝區有兩句話，或者已經是最後一句，就合併成一個段落
                if len(buffer) == 2 or i == len(raw_segments) - 1:
                    segments.append(" ".join(buffer))
                    buffer = []  # 清空緩衝區，準備下一段

    if not segments and article.strip():
        # 如果文章不為空，但沒有被成功分割（例如沒有句號），就把整篇文章當作一個段落
        segments.append(article.strip())

    # 3. 初始化並回傳整個工作流程共享的狀態 (state)
    # 我們只回傳這個節點負責更新的部分
    updated_state = {
        "segments": segments,
    }
    print(f"✅ 文字載入完成，共分成 {len(segments)} 段。")
    return updated_state
