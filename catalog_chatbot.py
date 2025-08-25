import os
 
 
import dotenv
from pinecone import Pinecone
import google.generativeai as genai
# Flask endpoints moved to app.py

# Load environment variables
dotenv.load_dotenv()
 
# Application constants
INDEX_NAME = "catalog-text-embedding-004"
BASE_CATALOG_URL = "https://catalogs.rutgers.edu/generated/nb-ug_2224/"

#default top k is the number of results to return from the search
TOP_K = 10

#default relevance threshold is the minimum score for a result to be considered relevant
RELEVANCE_THRESHOLD = 0.6

#default max context sources is the maximum number of sources to include in the context
MAX_CONTEXT_SOURCES = 10

# Initialize Google Gemini client
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

# Initialize Pinecone client
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_client = Pinecone(api_key=pinecone_api_key)

# Access the catalog index
catalog_index = pinecone_client.Index(INDEX_NAME)


class CatalogChatbot:
    """RAG chatbot for querying the Rutgers catalog via Pinecone + Gemini."""

    def __init__(self):
        """Initialize the underlying LLM model."""
        self.model = genai.GenerativeModel('gemini-1.5-flash')


    def generate_query_embedding(self, query):
        """Generate an embedding vector for the user query.

        Returns None if the embedding service fails.
        """
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query",
            )
            return result['embedding']
        except Exception:
            return None

    def _query_index(self, vector, top_k):
        """Query Pinecone index and return raw matches with metadata."""
        search_results = catalog_index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )
        return search_results.get('matches', [])

    def _build_content_items(self, matches, threshold):
        """Convert raw matches into normalized content items, filtering by score threshold.
        Only keep text (from 'full_text'), page_number, and score.
        """
        items = []
        for match in matches:
            if match.get('score', 0.0) <= threshold:
                continue
            metadata = match.get('metadata', {})
            page_raw = metadata.get('page_number', 0)
            try:
                page_num = int(float(page_raw))
            except Exception:
                page_num = 0
            content_info = {
                'score': match.get('score', 0.0),
                'text': metadata.get('full_text', ''),
                'page_number': page_num,
            }
            items.append(content_info)
        return items

    #fall through search and retrieve maximum number of relevant items
    def search_catalog(self, query, top_k = TOP_K):
        """Search the Pinecone index for content relevant to the query with a fallback pass."""
        query_embedding = self.generate_query_embedding(query)
        if not query_embedding:
            return []

        try:
            # First pass
            matches = self._query_index(query_embedding, top_k=top_k)
            relevant_content = self._build_content_items(matches, threshold=RELEVANCE_THRESHOLD)

            return relevant_content

        except Exception:
            return []

    def generate_response(self, query, context_content):
        """Construct a prompt from the most relevant items and ask the LLM to answer."""
        max_items = min(MAX_CONTEXT_SOURCES, len(context_content))
        combined_text = ""

        for i, item in enumerate(context_content[:max_items]):
            text = item.get('text') or ""
            page_raw = item.get('page_number', 'Unknown')
            try:
                page = int(float(page_raw))
            except Exception:
                page = page_raw
            combined_text += f"\n--- Source {i + 1} (Page {page}) ---\n{text}\n"

        prompt = f"""You are a Rutgers catalog assistant. Your ONLY source of information is the CATALOG CONTEXT below. You MUST answer exclusively based on this context. Do not use any external knowledge or make up information.

IMPORTANT RULES:
1. Base your answer STRICTLY on the provided sources. If certain information isn't in the sources, say "I don't have that information in the provided sources."
2. If the query can't be fully answered from the sources, answer what you can and explain what's missing.
3. Don't include in-text citations or sources in your response. The system will attach sources separately.


CATALOG CONTEXT:
{combined_text}

USER QUESTION: {query}

Now, provide your answer based ONLY on the above context:"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text or ""
            return result_text.strip()
        except Exception:
            return (
                "I encountered an error while generating the response. Please try again."
            )

    def chat(self, user_query):
        """Handle a user query end-to-end: retrieve, synthesize, and format sources."""
        relevant_content = self.search_catalog(user_query, top_k = TOP_K)
        if not relevant_content:
            return {
                "response": (
                    "I couldn't find relevant information in the course catalog for your "
                    "query. Please try rephrasing your question or check the official "
                    "Rutgers website for more information."
                ),
                "sources": [],
            }

        response_text = self.generate_response(user_query, relevant_content)

        # Build bottom sources list from the pages used in context
        max_items = min(MAX_CONTEXT_SOURCES, len(relevant_content))
        seen_pages = set()
        sources_list = []
        
        for item in relevant_content[:max_items]:
            page_raw = item.get('page_number', 0)
            try:
                page_num = int(float(page_raw))
            except Exception:
                continue
            if page_num in seen_pages:
                continue
            seen_pages.add(page_num)
            link = f"{BASE_CATALOG_URL}pg{page_num}.html"
            title = f"Catalog Page {page_num}"
            sources_list.append({"title": title, "link": link})

        return {"response": response_text, "sources": sources_list}
