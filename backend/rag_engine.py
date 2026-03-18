import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Using the updated HuggingFace import
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# Initialize the free local embedding model
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vector_store(file_paths: list):
    """Reads multiple PDFs, chunks them, and builds a combined local FAISS database."""
    
    all_splits = []
    # Initialize the chunker once
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    # 1. Loop through every file path provided by the user
    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        # Chunk the current document
        splits = text_splitter.split_documents(docs)
        
        # Add these chunks to our master list
        all_splits.extend(splits)
    
    # 2. Create and return the FAISS vector database containing ALL documents
    vectorstore = FAISS.from_documents(all_splits, embedding_model)
    return vectorstore


def get_insurance_answer(client_name, client_age, claim_factors, api_key, vectorstore):
    """Searches the database and asks Llama 3 for the insurance clause."""
    if not api_key:
        raise ValueError("Groq API Key is required.")
    
    # Connect to Groq using the user's API key
    llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="llama-3.1-8b-instant")
    
    # The strict guardrails and instructions for the AI
    system_prompt = (
        "You are a strict, factual insurance claims assistant. "
        "Your ONLY source of knowledge is the provided Context. You have no outside memory or general knowledge.\n\n"
        "You must strictly follow these rules:\n"
        "1. NO HALLUCINATION: You must NEVER invent, guess, or make up clause numbers (e.g., 'Clause 3.2'), coverage amounts, or justifications. If it is not explicitly written in the Context, it does not exist.\n"
        "2. MISSING INFO (CRITICAL): If the Context is from an irrelevant document (like a project plan or manual) or simply does not contain the answer to the claim, you MUST reply EXACTLY with: 'I cannot find the answer to this claim in the uploaded document.' Do NOT generate a fake response.\n"
        "3. NO JSON: Do NOT output your response in JSON format. Provide standard, conversational text.\n"
        "4. NAVIGATION & PURPOSE: If the user asks who you are or what you do, explain briefly that you analyze uploaded insurance PDFs to find policy rules.\n"
        "5. CONCISENESS: Provide incredibly brief, direct answers (1-3 sentences maximum).\n\n"
        "Context: {context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    # Retrieve the top 4 most relevant chunks
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    # Connect the pieces together
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # Format the dynamic query
    query = f"Client: {client_name}, Age: {client_age}. Claim factors: {claim_factors}. Based on the policy, which clause applies and what are the rules?"
    
    # Ask the AI
    response = rag_chain.invoke({"input": query})
    
    return response["answer"]