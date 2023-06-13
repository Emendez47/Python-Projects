import os
import PyPDF2
import openai
from PyPDF2 import PdfReader
import requests
import json
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Initialize the sentence transformer model
model = SentenceTransformer('paraphrase-distilroberta-base-v1')


def create_vector_database(text, chunk_size=500):
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    embeddings = model.encode(chunks)
    return list(zip(chunks, embeddings))


def find_most_relevant_chunks(question, vector_database, top_k=3):
    question_embedding = model.encode([question])[0]
    similarities = [(chunk, embedding, np.inner(question_embedding, embedding))
                    for chunk, embedding in vector_database]
    sorted_similarities = sorted(
        similarities, key=lambda x: x[2], reverse=True)
    return [chunk for chunk, _, _ in sorted_similarities[:top_k]]


# Replace with your OpenAI API key
openai.api_key = ""


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()

    # Split the text into paragraphs
    paragraphs = text.split('\n\n')

    # Return the first paragraph if there are any paragraphs, otherwise return an empty string
    return paragraphs[0] if paragraphs else ""


def find_page_number(document_text, answer):
    with open(document_text, 'rb') as file:
        reader = PdfReader(file)
        for page_num in range(len(reader.pages)):
            page_text = reader.pages[page_num].extract_text()
            if answer in page_text:
                return page_num + 1  # Add 1 to the page number since the index starts at 0
    return "Not found"


def ask_chatgpt(prompt, model="gpt-4", max_input_length=2048, max_output_length=6144):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }

    # Truncate the input text if it exceeds the maximum input length
    if len(prompt) > max_input_length:
        prompt = prompt[:max_input_length]

    data = {
        "model": model,
        "messages": [{"role": "system", "content": "Document: " + prompt}],
        "max_tokens": max_output_length,
        "temperature": 0.5,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(data),
    )

    response_json = response.json()

    if response.status_code == 200:
        answer = response_json["choices"][0]["message"]["content"].strip()
        # Find the page number where the answer is found
        page_number = find_page_number(prompt, answer)
        return f"Page: {page_number}\nAnswer: {answer}"
    else:
        raise Exception(
            f"Error {response.status_code}: {response_json['error']['message']}")


def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    pdf_folder = os.path.join(current_directory, "pdfs")
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    for pdf_file in tqdm(pdf_files, desc="Processing PDF files"):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        pdf_text = extract_text_from_pdf(pdf_path)

        while True:
            question = input(f"Ask a question about {pdf_file}: ")
            prompt = f"Document: {pdf_text}\nQuestion: {question}\nAnswer:"
            answer = ask_chatgpt(prompt)

            print(f"Answer: {answer}\n")

            user_action = input(
                "Type 'explain' for further explanation, 'new' for a new question, or 'next' to move to the next document: ").lower()

            if user_action == 'explain':
                prompt = f"Document: {pdf_text}\nQuestion: Please explain the answer to the previous question in more detail.\nAnswer:"
                detailed_answer = ask_chatgpt(prompt)
                print(f"Detailed Answer: {detailed_answer}\n")
            elif user_action == 'new':
                continue
            elif user_action == 'next':
                break
            else:
                print("Invalid input. Please try again.")
