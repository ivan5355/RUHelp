# Rutgers Course Catalog RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for answering questions about the Rutgers University catalog. It retrieves relevant catalog text (by page) from Pinecone and generates answers with Google Gemini. The UI is a simple Flask web app.

## Prerequisites
- Python 3.10+ recommended
- A Pinecone account and API key
- A Google Generative AI API key (Gemini)

## 1) Setup
1. Clone the repo and enter the project directory.
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   # .venv\Scripts\activate   # Windows PowerShell
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file at the project root with your keys:
   ```
   GOOGLE_API_KEY="your_google_api_key"
   PINECONE_API_KEY="your_pinecone_api_key"
   ```

## 2) Prepare catalog data (only if needed)
The app expects a catalog text file at `data/catalog.txt`.
- If `data/catalog.txt` already exists, skip to step 3.
- Otherwise, generate it by scraping the catalog pages (this may take a while):
  ```bash
  python scripts/scrape_catalog.py
  mkdir -p data && mv catalog.txt data/catalog.txt
  ```

## 3) Build embeddings in Pinecone
Create or update the Pinecone index and upload catalog text chunks with page numbers:
```bash
python database/generate_catalog_embeddings.py
```
You should see batches being uploaded and a final total vector count.

## 4) Run the web app
Start the Flask app (serves at port 5001 by default):
```bash
python app.py
```
Open your browser to:
- http://127.0.0.1:5001

Ask a question (e.g., “What are the requirements for a Computer Science major?”). The bot will answer and show a Sources list at the bottom linking to catalog pages.

## Troubleshooting
- ModuleNotFoundError: dotenv
  - Ensure you ran `pip install -r requirements.txt`.
- Port 5001 is in use
  - On macOS/Linux, find and kill the process:
    ```bash
    lsof -i :5001 | grep LISTEN
    kill -9 <PID>
    ```
  - Then re-run: `python app.py`
- Pinecone auth/index errors
  - Confirm `PINECONE_API_KEY` in `.env` and that the index name in `database/generate_catalog_embeddings.py` matches `catalog-text-embedding-004`.
- Google API errors
  - Confirm `GOOGLE_API_KEY` in `.env` and that you have access to the Gemini models used (`text-embedding-004` and `gemini-1.5-flash`).

## How it works (brief)
- `database/generate_catalog_embeddings.py`: reads `data/catalog.txt`, creates page-aware text chunks, embeds them, and uploads to Pinecone with `full_text` and `page_number` metadata.
- `catalog_chatbot.py`: embeds user query, retrieves top matches from Pinecone, builds a context by page, and asks Gemini to answer strictly from that context. Returns the answer plus a bottom Sources list.
- `app.py`: Flask server with `/` (UI) and `/chat` (API) endpoints.
- `templates/` + `static/`: simple chat UI, styles, and JS.

## Frontend creation using Claude Sonnet 4.0
The chat frontend (HTML/CSS/JS) was drafted and iterated with the help of Anthropic’s Claude Sonnet 4.0.
- Generated structure: `templates/catalog_chat.html` (layout, header, sample queries, chat area), `static/css/styles.css` (theme, chat bubbles, responsiveness), and `static/js/script.js` (message rendering, loading state, basic formatting, sources list).
- Interaction details: messages render as bubbles, example queries auto-fill the input, a loading indicator shows during requests, and sources are listed beneath bot replies.
- Customizing:
  - Styles: edit `static/css/styles.css` (colors, spacing, bubble widths, mobile breakpoints).
  - Message formatting: adjust `formatMessage` in `static/js/script.js`.
  - Layout/content: edit `templates/catalog_chat.html`.

Claude Sonnet 4.0 was used to rapidly prototype the UI, refine accessibility and readability, and keep the code minimal and framework-light so it works out of the box with Flask’s templating and static assets. 