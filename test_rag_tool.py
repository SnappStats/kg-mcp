"""Test the RAG tool functionality."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_rag_search():
    """Test the RAG search functionality."""
    from server import _retrieve_rag_contexts

    corpus_name = os.getenv(
        "RAG_AMERICAN_FB",
        os.getenv(
            "VERTEX_RAG_CORPUS",
            "projects/staging-470600/locations/us-east4/ragCorpora/4611686018427387904",
        ),
    )

    print(f"Using corpus: {corpus_name}")

    # Test query
    query = "What is a fire zone blitz?"
    print(f"\nQuery: {query}")

    try:
        contexts = await _retrieve_rag_contexts(query, top_k=3, corpus_name=corpus_name)

        print(f"\nFound {len(contexts)} results:")
        for i, ctx in enumerate(contexts, 1):
            print(f"\n{i}. Source: {ctx['source']}")
            print(f"   Distance: {ctx['distance']}")
            print(f"   Content: {ctx['content'][:200]}...")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_search())
