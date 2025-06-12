# LangGraph 翻譯器

這是一個使用 LangGraph、FastAPI 和 OpenAI API 建構的翻譯應用程式。它不僅可以翻譯文字，還能自動擷取詞彙表並應用於未來的翻譯中，以確保術語的一致性。

## 功能

- 支援多種語言的雙向翻譯。
- 自動偵測來源語言。
- 儲存翻譯歷史記錄。
- 建立自訂詞彙表，強制特定術語的翻譯。
- 自動從翻譯結果中建議新的詞彙。

## Docker 安裝與啟動

使用 Docker 是在本機執行此應用程式最簡單快速的方式。

### 前提條件

- 您必須已安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

### 安裝步驟

1.  **複製 (Clone) 專案**

    ```bash
    [git clone https://github.com/your-username/langgraph_translator.git](https://github.com/YC815/ai_trans.git)
    cd ai_trans
    ```

2.  **建立 `.env` 檔案**

    應用程式需要存取 OpenAI API，因此您需要在專案的根目錄下建立一個名為 `.env` 的檔案。此檔案應包含您的 OpenAI API 金鑰。

    ```
    OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ```

    > **重要**: `.env` 檔案已被加入 `.gitignore` 和 `.dockerignore` 中，確保您的金鑰不會被意外上傳到版本控制或打包到 Docker 映像檔中。

3.  **建置 Docker 映像檔 (Build the Docker Image)**

    在專案根目錄（即 `Dockerfile` 所在的目錄）中執行以下指令來建置 Docker 映像檔。我們給它取一個好記的名字，例如 `langgraph-translator`。

    ```bash
    docker build -t langgraph-translator .
    ```

4.  **執行 Docker 容器 (Run the Docker Container)**

    建置完成後，使用以下指令來啟動容器：

    ```bash
    docker run -d -p 8000:8000 --env-file .env -v $(pwd)/translator.db:/app/translator.db --name langgraph-translator-container langgraph-translator
    ```

    讓我們來分解這個指令：

    - `-d`: 在背景模式 (detached mode) 執行容器。
    - `-p 8000:8000`: 將主機的 8000 連接埠映射到容器的 8000 連接埠。
    - `--env-file .env`: 讀取 `.env` 檔案中的環境變數並將其傳遞給容器。
    - `-v $(pwd)/translator.db:/app/translator.db`: 這是一個非常重要的部分。它會將您本機專案目錄下的 `translator.db` 檔案（如果不存在，Docker 會為您建立一個空的）掛載到容器內的 `/app/translator.db`。這樣可以確保即使容器停止或被刪除，您的翻譯歷史和詞彙表資料也能**永久保存**在您的主機上。
    - `--name langgraph-translator-container`: 為您的容器指定一個名稱，方便管理。
    - `langgraph-translator`: 您在 `build` 步驟中為映像檔指定的名稱。

5.  **開啟應用程式**

    現在，您可以在瀏覽器中開啟 `http://localhost:8000` 來使用此應用程式。

### 管理容器

- **查看日誌 (Logs)**:

  ```bash
  docker logs langgraph-translator-container
  ```

- **停止容器**:

  ```bash
  docker stop langgraph-translator-container
  ```

- **重新啟動已停止的容器**:

  ```bash
  docker start langgraph-translator-container
  ```

- **移除容器 (移除前請先停止)**:
  ```bash
  docker rm langgraph-translator-container
  ```
