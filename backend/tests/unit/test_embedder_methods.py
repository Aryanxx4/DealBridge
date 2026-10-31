from fastembed import TextEmbedding


def test_embedder_methods_exist():
    # The wrapper relies on these two methods (documents vs. queries).
    assert hasattr(TextEmbedding, "passage_embed")
    assert hasattr(TextEmbedding, "query_embed")
