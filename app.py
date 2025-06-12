# app.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

# Load env
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# "掛載" 一個靜態檔案目錄，讓 /static 路徑可以對應到 "static" 資料夾
# 這樣我們的 HTML 檔案才能讀取到 CSS 樣式
app.mount("/static", StaticFiles(directory="static"), name="static")
# 設定模板引擎，告訴它我們的 HTML 模板都放在 "templates" 資料夾
templates = Jinja2Templates(directory="templates")

# 初始化大型語言模型 (LLM)
# temperature=0.0 表示我們希望模型的回答盡量穩定、有確定性
# model="gpt-3.5-turbo" 指定了我們要使用的模型版本
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

# --- Few-Shot Prompt 範本 ---
# "Few-Shot" 指的是我們給模型一些範例，讓它能更精準地理解我們的任務
# 這裡我們提供兩個中翻英的範例
few_shot_examples = [
    {"src": "你好，世界！", "tgt": "Hello, world!"},
    {"src": "今天天气很好。", "tgt": "The weather is nice today."}
]
# 將範例列表轉換成一個純文字字串，方便稍後插入到主要提示中
example_str = "\n".join(
    f"示例：\n源语言: {ex['src']}\n目标翻译: {ex['tgt']}\n"
    for ex in few_shot_examples
)

# 建立一個提示模板 (Prompt Template)
# 這就像是給模型的一份填空題問卷
prompt = PromptTemplate(
    # 定義這份問卷需要填寫的欄位
    input_variables=["src_lang", "tgt_lang", "text", "examples"],
    # 這是問卷的內容，{ } 中的是待填寫的欄位
    template="""
你是一位多语种翻译专家。
以下是 Few-Shot 示例，提高上下文准确度：
{examples}

现在，请将下面内容从 {src_lang} 翻译成 {tgt_lang}：
{text}
"""
)
# 建立一個 LLMChain，它會把我們的模型 (llm) 和提示 (prompt) 串在一起
# 這樣我們之後只要提供資料，它就會自動完成填空並問模型問題
chain = LLMChain(llm=llm, prompt=prompt)

# --- API 路由 (Routes) ---
# 這裡定義了使用者在瀏覽器輸入不同網址時，我們的程式該如何回應

# @app.get("/") 定義了當使用者造訪網站根目錄 (例如 http://127.0.0.1:8000) 時的行為


@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    # 定義支援的語言列表
    langs = ["zh", "en", "fr", "de", "es", "ja", "ko"]
    # 使用模板引擎回傳 index.html 這個網頁
    # 並把請求物件(request)和語言列表(langs)傳遞給模板
    return templates.TemplateResponse("index.html", {"request": request, "langs": langs})

# @app.post("/translate") 定義了當使用者在網頁上點擊 "翻譯" 按鈕後的行為


@app.post("/translate", response_class=HTMLResponse)
async def translate(request: Request,
                    # 從表單中獲取名為 "src_lang" 的資料
                    src_lang: str = Form(...),
                    # 從表單中獲取名為 "tgt_lang" 的資料
                    tgt_lang: str = Form(...),
                    # 從表單中獲取名為 "text" 的資料
                    text: str = Form(...)):
    # 準備 few-shot 範例
    examples = example_str
    # 執行我們之前建立好的 chain，並填入從表單收到的資料
    result = chain.run(src_lang=src_lang, tgt_lang=tgt_lang, text=text, examples=examples)
    # 再次回傳 index.html 網頁，但這次會包含翻譯結果(output)和使用者原本輸入的內容(input)
    # 這樣使用者就能在同一個頁面看到結果
    return templates.TemplateResponse("index.html", {
        "request": request,
        "output": result,
        "input": text,
        "langs": ["zh", "en", "fr", "de", "es", "ja", "ko"],
        "selected_src": src_lang,
        "selected_tgt": tgt_lang
    })
