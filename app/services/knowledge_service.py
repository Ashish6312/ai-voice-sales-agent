from pathlib import Path
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class KnowledgeService:
    """
    Handles Retrieval-Augmented Generation (RAG).

    Responsibilities:
    - Load company knowledge
    - Split text into chunks
    - Generate embeddings
    - Build FAISS index
    - Load FAISS index
    - Search relevant chunks
    """

    _shared_embedding_model = None

    def __init__(self):

        self.knowledge_file = Path("app/knowledge/knowledge.txt")

        self.index_file = Path("app/knowledge/faiss.index")

        self.metadata_file = Path("app/knowledge/metadata.pkl")

        self.index = None

        self.chunks = []

    @property
    def embedding_model(self):
        """
        Lazily load the SentenceTransformer embedding model.
        """
        if KnowledgeService._shared_embedding_model is None:
            KnowledgeService._shared_embedding_model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )
        return KnowledgeService._shared_embedding_model

    # -------------------------------------------------

    def load_knowledge(self):

        if not self.knowledge_file.exists():
            raise FileNotFoundError(
                "knowledge.txt not found."
            )

        return self.knowledge_file.read_text(
            encoding="utf-8"
        )

    # -------------------------------------------------

    def split_into_chunks(
        self,
        text,
        chunk_size=300,
    ):

        chunks = []

        current_chunk = ""

        for line in text.splitlines():

            if len(current_chunk) + len(line) <= chunk_size:

                current_chunk += line + "\n"

            else:

                chunks.append(current_chunk.strip())

                current_chunk = line + "\n"

        if current_chunk:

            chunks.append(current_chunk.strip())

        return chunks

    # -------------------------------------------------

    def create_embeddings(self, chunks):

        embeddings = self.embedding_model.encode(
            chunks,
            convert_to_numpy=True,
        )

        return embeddings.astype(np.float32)

    # -------------------------------------------------

    def build_index(self):

        print("\nLoading knowledge file...")

        text = self.load_knowledge()

        print("Splitting into chunks...")

        self.chunks = self.split_into_chunks(text)

        print(f"Total Chunks: {len(self.chunks)}")

        embeddings = self.create_embeddings(
            self.chunks
        )

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(
            dimension
        )

        self.index.add(embeddings)

        faiss.write_index(
            self.index,
            str(self.index_file),
        )

        with open(
            self.metadata_file,
            "wb",
        ) as file:

            pickle.dump(
                self.chunks,
                file,
            )

        print("FAISS index created successfully!")

    # -------------------------------------------------

    def load_index(self):

        if not self.index_file.exists():

            raise FileNotFoundError(
                "faiss.index not found."
            )

        self.index = faiss.read_index(
            str(self.index_file)
        )

        with open(
            self.metadata_file,
            "rb",
        ) as file:

            self.chunks = pickle.load(file)

    # -------------------------------------------------

    def search(
        self,
        query,
        top_k=3,
    ):

        if self.index is None:

            raise RuntimeError(
                "Index is not loaded."
            )

        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
        ).astype(np.float32)

        distances, indices = self.index.search(
            query_embedding,
            top_k,
        )

        results = []

        for idx in indices[0]:

            if idx != -1:

                results.append(
                    self.chunks[idx]
                )

        return results