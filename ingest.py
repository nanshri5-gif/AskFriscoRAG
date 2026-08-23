from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DATA_DIR = Path("data")
files = sorted(DATA_DIR.glob("*.docx"))



def extract_docx_text(file_path: Path) -> str:
    with ZipFile(file_path) as docx_zip:
        xml_content = docx_zip.read("word/document.xml")

    root = ET.fromstring(xml_content)

    namespace = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    }

    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        texts = paragraph.findall(".//w:t", namespace)

        paragraph_text = "".join(
            text.text for text in texts if text.text
        ).strip()

        if paragraph_text:
            paragraphs.append(paragraph_text)

    return "\n".join(paragraphs)


def main():
    load_dotenv()

    pinecone_index = os.getenv("PINECONE_INDEX")

    if not pinecone_index:
        raise ValueError("PINECONE_INDEX is missing from .env")

    files = sorted(DATA_DIR.glob("*.docx"))

    if not files:
        raise ValueError("No DOCX files found in the data folder.")

    print(f"Found {len(files)} documents")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    all_chunks = []

    for file_path in files:

        print(f"\nProcessing: {file_path.name}")

        text = extract_docx_text(file_path)

        print(f"Extracted {len(text)} characters")

        document = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "city": "Frisco",
            },
        )

        chunks = text_splitter.split_documents([document])

        print(f"Created {len(chunks)} chunks")

        all_chunks.extend(chunks)

    print(f"\nTotal chunks created: {len(all_chunks)}")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        dimensions=1024,
    )

    PineconeVectorStore.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        index_name=pinecone_index,
    )

    print("\nIngestion completed successfully.")
    print(f"Stored {len(all_chunks)} chunks in Pinecone.")


if __name__ == "__main__":
    main()