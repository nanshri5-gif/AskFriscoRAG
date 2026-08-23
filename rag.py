import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages import SystemMessage, HumanMessage


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1024


load_dotenv()

pinecone_index = os.getenv("PINECONE_INDEX")

embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    dimensions=EMBEDDING_DIMENSIONS,
)

vector_store = PineconeVectorStore(
    index_name=pinecone_index,
    embedding=embeddings,
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)


SYSTEM_PROMPT = """
You are Frisco City Assistant.

Answer the user's question using only the retrieved context.

You may summarize, paraphrase, or restate facts that are directly
supported by the retrieved context.

Do not use general knowledge to fill in missing information.

Do not invent policies, dates, fees, procedures, requirements,
or facts not supported by the retrieved context.

If the retrieved context does not contain enough information to
answer the question, respond exactly:

I don't have that info available.

Keep answers concise and clear.
"""


def ask_frisco(question, chat_history=None):

    if chat_history is None:
        chat_history = []

    # Retrieve using MMR
    results = vector_store.max_marginal_relevance_search(
        query=question,
        k=4,
        fetch_k=10,
    )

    context = "\n\n".join(
        doc.page_content for doc in results
    )

    user_prompt = f"""
Retrieved context:

{context}

Question:

{question}
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *chat_history,
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)

    return response.content