# 使用官方 Python 映像檔作為基礎
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 將 requirements.txt 複製到工作目錄
COPY requirements.txt .

# 安裝 uvicorn 和其他必要的套件
# uvicorn 是啟動 FastAPI 應用程式的伺服器
RUN pip install --no-cache-dir -r requirements.txt uvicorn

# 將應用程式的其餘原始碼複製到工作目錄
COPY . .

# 開放容器的 8000 連接埠，讓外部可以存取
EXPOSE 8000

# 設定容器啟動時要執行的指令
# --host 0.0.0.0 讓容器可以從外部存取
# --port 8000 指定服務運行的連接埠
# app:app 指的是 "app.py" 檔案中的 "app" 物件
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 