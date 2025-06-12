# AI_Trans 專案 Docker 部署指南

---

## 先決條件

1. 已安裝 Git
2. 已安裝 Docker
3. 具備 OpenAI API Key

---

## 安裝步驟

### 1. 克隆專案並切換分支

```bash
# 克隆指定分支
git clone --branch feat/all-recent-fixes https://github.com/YC815/ai_trans.git
# 進入專案資料夾
title
cd ai_trans
```

### 2. 建立環境變數檔案

在專案根目錄下建立 `.env` 檔案，並將你的 OpenAI API Key 寫入：

```bash
cat > .env <<EOF
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
EOF
```

> **提示**：請將 `sk-xxxxxxxxxxxxxxxxxxxx` 替換為你的實際 API Key。

### 3. 建構 Docker 映像檔

執行以下指令，將目前目錄下的內容打包成 Docker 映像：

```bash
docker build -t ai_trans_image .
```

### 4. 啟動 Docker 容器（方案 B：`--rm` 自動清理）

使用 `--rm` 選項，容器停止後會自動移除：

```bash
docker run -d --rm \
  --name ai_trans_container \
  -p 8000:8000 \
  -v "$(pwd)/.env:/app/.env" \
  ai_trans_image
```

- `-d`：以背景模式執行
- `--rm`：容器退出時自動清理
- `--name`：指定容器名稱
- `-p 8000:8000`：將本機 8000 端口對應到容器內的 8000 端口
- `-v`：掛載本地 `.env` 檔案到容器中

### 5. 檢查啟動日誌

```bash
docker logs -f ai_trans_container
```

預期看到：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 6. 驗證部署成功

在瀏覽器中開啟：

```
http://localhost:8000
```

如果畫面正常顯示，即表示部署完成！

---

## 常見問題

- **Q**：如何停止並移除容器？
  **A**：執行 `docker stop ai_trans_container`，由於使用了 `--rm`，停止後容器會自動刪除。

- **Q**：要修改 API Key 該怎麼做？
  **A**：編輯專案根目錄下的 `.env` 檔案，更新 `OPENAI_API_KEY`，然後重啟容器。

---
