import logging

from modules.vector_index.vector_implimentations import DocumentImpl


def test_recreate_vector_index():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Recreate the vector index
    vector_index = DocumentImpl.recreate_index()

    # Validate the vector index
    assert vector_index is not None, "Failed to recreate vector index"
    logging.info("Vector index recreated successfully")


if __name__ == "__main__":
    test_recreate_vector_index()
