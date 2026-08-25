import os
import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_data():
    # create or get the path for the folder of the colection
    client_db = chromadb.PersistentClient(path="./vector_database")
    colection = client_db.get_or_create_collection(name="articles")

    #indicate, and create if it not exists, the path to the pdfs' folder
    pdfs_docs = "./docs"
    if not os.path.exists(pdfs_docs):
        os.makedirs(pdfs_docs)
        return f"Folder '{pdfs_docs}' created. Enter articles there."

    # the splittler of langchain that increase the efficiency of the search
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    # for each file(pdf) ond the folder mentioned earlier...
    files = os.listdir(pdfs_docs)
    for file in files:
        if file.endswith(".pdf"):
            # get the path
            complete_path = os.path.join(pdfs_docs, file)
            # send it to the PDFReader who get the text of it...
            reader = PdfReader(complete_path)

            # get all the text
            complete_text = ""
            for page in reader.pages:
                complete_text += page.extract_text() + "\n"

            # split it efficiently
            pieces = splitter.split_text(complete_text)

            # send each piece of the splition to the collection, indicating the piece itself, its source and an unique id
            for i, piece in enumerate(pieces):
                id = f"{file}_parte_{i}"
                colection.upsert(
                    documents=[piece],
                    metadatas=[{"source": file}],
                    ids=[id]
                )
                    
    return "All update"