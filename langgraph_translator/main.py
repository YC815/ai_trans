# langgraph_translator/main.py

from workflow import build_graph


def main():
    """
    主函式，負責設定、執行並顯示翻譯工作流程的結果。
    """
    # 建立工作流程圖
    app = build_graph()

    # 定義輸入，除了指定要翻譯的檔案路徑，
    # 也初始化狀態中其他必要的欄位，確保流程穩定。
    inputs = {
        "source_file": "sample.txt",
        "glossary": {},
        "translated": [],
        "back_translations": [],
        "validation_result": None,
    }

    # 執行工作流程
    # .invoke() 會啟動整個流程，並等待它完成
    final_state = app.invoke(inputs)

    # 顯示結果
    print("\n\n✅ 翻譯流程完成")
    print("---" * 10)
    print(f"最終校驗結果: {final_state.get('validation_result', 'N/A').upper()}")
    print("---" * 10)

    print("📖 翻譯與校驗結果比對：")
    if final_state.get("translated"):
        for i, (orig, trans, back) in enumerate(zip(
            final_state.get("segments", []),
            final_state.get("translated", []),
            final_state.get("back_translations", [])
        )):
            print(f"  - [段落 {i+1}]")
            print(f"    - 原文: {orig}")
            print(f"    - 譯文: {trans}")
            print(f"    - 回譯: {back}\n")
    else:
        print("  - (沒有翻譯結果)")

    print("---" * 10)
    print("\n📚 更新後的術語表：")
    if final_state.get("glossary"):
        for term, definition in final_state["glossary"].items():
            print(f"  - {term}: {definition}")
    else:
        print("  - (術語表為空)")
    print("---" * 10)


if __name__ == "__main__":
    main()
