from flashrank import Ranker, RerankRequest

# Load once when FastAPI starts
ranker = Ranker(
    model_name="ms-marco-MiniLM-L-12-v2",
    cache_dir="./flashrank_cache"
)


def rerank(
    question,
    documents,
    top_k=5
):

    if not documents:
        return []

    passages = []

    for index, document in enumerate(documents):

        passages.append({
            "id": str(index),
            "text": document
        })

    request = RerankRequest(
        query=question,
        passages=passages
    )

    results = ranker.rerank(request)

    return results[:top_k]
