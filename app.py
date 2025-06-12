# app.py
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import os
import database

# Load env
load_dotenv()

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    database.init_db()

# "掛載" 一個靜態檔案目錄，讓 /static 路徑可以對應到 "static" 資料夾
# 這樣我們的 HTML 檔案才能讀取到 CSS 樣式
app.mount("/static", StaticFiles(directory="static"), name="static")
# 設定模板引擎，告訴它我們的 HTML 模板都放在 "templates" 資料夾
templates = Jinja2Templates(directory="templates")

# 初始化大型語言模型 (LLM)
# temperature=0.0 表示我們希望模型的回答盡量穩定、有確定性
# model="gpt-3.5-turbo" 指定了我們要使用的模型版本
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")

# --- Translation Chain ---


class TranslationResponse(BaseModel):
    detected_source_language: str = Field(description="The detected source language of the text, e.g., 'English', 'zh-CN'")
    translated_text: str = Field(description="The translated text")


translation_parser = JsonOutputParser(pydantic_object=TranslationResponse)

translation_prompt = PromptTemplate(
    input_variables=["tgt_lang", "text", "vocabulary_instructions"],
    template="""
You are a multilingual translation expert.
First, automatically detect the source language of the text below.
Then, translate the text into {tgt_lang}.

{vocabulary_instructions}

Respond with a JSON object containing 'detected_source_language' and 'translated_text' keys.

Text to translate:
{text}

{format_instructions}
""",
    partial_variables={"format_instructions": translation_parser.get_format_instructions()}
)
translation_chain = translation_prompt | llm | translation_parser


# --- Glossary Extraction Chain ---
class GlossaryTerm(BaseModel):
    source_term: str = Field(description="The key term or phrase from the source text")
    term: str = Field(description="The corresponding term in the target language")
    definition: str = Field(description="A concise definition or explanation of the term in the target language")


class Glossary(BaseModel):
    glossary: list[GlossaryTerm] = Field(description="A list of key terms and their definitions")


glossary_parser = JsonOutputParser(pydantic_object=Glossary)

glossary_prompt = PromptTemplate(
    input_variables=["source_text", "translation", "tgt_lang"],
    template="""
You are an expert in linguistics and terminology.
From the following source text and its translation into {tgt_lang}, please extract key terms or phrases.
For each term, provide the original source term, the translated term, and a concise definition in {tgt_lang}.
Respond with a JSON object containing a single key "glossary" which is a list of objects, where each object has "source_term", "term", and "definition" keys.

Source Text:
{source_text}

Translation ({tgt_lang}):
{translation}

{format_instructions}
""",
    partial_variables={"format_instructions": glossary_parser.get_format_instructions()}
)

glossary_chain = glossary_prompt | llm | glossary_parser


# --- API 路由 (Routes) ---
# 這裡定義了使用者在瀏覽器輸入不同網址時，我們的程式該如何回應

# @app.get("/") 定義了當使用者造訪網站根目錄 (例如 http://127.0.0.1:8000) 時的行為


@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    # 定義支援的語言列表，使用更精確的代碼並提供中文說明
    langs = {
        "zh-TW": "繁體中文", "zh-CN": "簡體中文", "en": "英文", "fr": "法文",
        "de": "德文", "es": "西班牙文", "ja": "日文", "ko": "韓文"
    }
    history = database.get_translation_history()
    # For now, vocabulary is handled on a separate page/modal, so we don't need to pass it here.
    return templates.TemplateResponse("index.html", {
        "request": request,
        "langs": langs,
        "history": history
    })

# --- Vocabulary Pydantic Models ---


class VocabItem(BaseModel):
    source_text: str
    language: str
    translated_text: str
    annotation: str | None = None


class VocabUpdateItem(BaseModel):
    translated_text: str
    annotation: str | None = None


# --- Vocabulary API Endpoints ---
@app.get("/vocabulary", response_class=JSONResponse)
async def get_all_vocabulary():
    vocab = database.get_vocabulary()
    return vocab


@app.post("/vocabulary", status_code=201, response_class=JSONResponse)
async def create_vocabulary_item(item: VocabItem):
    result = database.add_vocabulary_term(
        item.source_text, item.language, item.translated_text, item.annotation
    )
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return {**item.dict(), "id": result["id"]}


@app.put("/vocabulary/{item_id}", response_class=JSONResponse)
async def update_vocabulary_item_endpoint(item_id: int, item: VocabUpdateItem):
    database.update_vocabulary_term(
        item_id, item.translated_text, item.annotation
    )
    return {"status": "success", "id": item_id}


@app.delete("/vocabulary/{item_id}", status_code=200, response_class=JSONResponse)
async def delete_vocabulary_item(item_id: int):
    database.delete_vocabulary_term(item_id)
    return {"status": "success"}

# @app.post("/translate") 定義了當使用者在網頁上點擊 "翻譯" 按鈕後的行為


@app.post("/translate", response_class=JSONResponse)
async def translate(request: Request,
                    # 從表單中獲取名為 "tgt_lang" 的資料
                    tgt_lang: str = Form(...),
                    # 從表單中獲取名為 "text" 的資料
                    text: str = Form(...)):

    # --- Phase 2: Vocabulary Application ---
    # 1. Get vocabulary from DB for the target language
    vocabulary = database.get_vocabulary_for_lang(tgt_lang)

    # 2. Prepare vocabulary instructions for the prompt
    vocab_instructions = ""
    if vocabulary:
        # Sort by length of source_text descending to handle substrings correctly
        vocabulary.sort(key=lambda x: len(x['source_text']), reverse=True)

        # Format for prompt
        vocab_list_str = "\n".join([f'- "{term["source_text"]}" must be translated as "{term["translated_text"]}"' for term in vocabulary])
        vocab_instructions = f"You are required to use the following translations for the terms below:\n{vocab_list_str}"

        # Debug message as requested
        print("\n--- Applying Vocabulary ---")
        print(f"Target Language: {tgt_lang}")
        print("Terms applied:")
        for term in vocabulary:
            print(f"  - {term['source_text']} -> {term['translated_text']}")
        print("--------------------------\n")

    # 3. Get translation and detected source language
    translation_response = translation_chain.invoke({
        "tgt_lang": tgt_lang,
        "text": text,
        "vocabulary_instructions": vocab_instructions
    })

    translated_text = translation_response['translated_text']
    from_lang = translation_response['detected_source_language']

    # --- Glossary Application (Post-translation) ---
    # The glossary logic below is now secondary to the prompt-based vocabulary.
    # We can keep it as a fallback or for a different purpose if needed.
    # For now, we will rely on the prompt to have handled the vocabulary.
    final_text = translated_text

    # 4. Get glossary (for display, not for replacement)
    try:
        glossary_result = glossary_chain.invoke({
            "source_text": text,
            "translation": final_text,
            "tgt_lang": tgt_lang
        })
    except Exception as e:
        # If glossary extraction fails, return an empty list
        print(f"Glossary extraction failed: {e}")
        glossary_result = {"glossary": []}

    # --- Phase 3.1: Auto-save glossary to vocabulary ---
    if glossary_result.get("glossary"):
        # The `term` from glossary is the translated text, and `source_term` is the original.
        for term in glossary_result["glossary"]:
            # We need to map glossary fields to vocabulary fields.
            # source_term -> source_text
            # term -> translated_text
            # We don't have annotation from this process, so we'll pass None.
            # The language is the target language of the translation.
            try:
                database.add_vocabulary_term(
                    source_text=term["source_term"],
                    language=tgt_lang,
                    translated_text=term["term"],
                    annotation=term.get("definition")  # Use definition as annotation
                )
                print(f"Auto-saved to vocabulary: {term['source_term']} -> {term['term']}")
            except Exception as e:
                # This might fail if the term already exists (due to UNIQUE constraint), which is fine.
                print(f"Could not auto-save term '{term['source_term']}': {e}")

    # 5. Save to history and get the new item
    new_history_item = database.add_translation_to_history(
        source_text=text,
        from_lang=from_lang,
        to_lang=tgt_lang,
        translated_text=final_text
    )

    return JSONResponse({
        "translation": final_text,
        "glossary": glossary_result.get("glossary", []),
        "history_item": new_history_item
    })

# --- History Deletion Endpoint ---


@app.delete("/history/{item_id}", status_code=200)
async def delete_history_item(item_id: int):
    database.delete_translation_history(item_id)
    return {"status": "success", "id": item_id}
