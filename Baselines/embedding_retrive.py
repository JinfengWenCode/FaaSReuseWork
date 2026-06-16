import os
import json
import re
import hashlib
import openai
import pandas as pd
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from mapping import standardize_category

EXT_LANG_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".go": "Go",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".rs": "Rust",
    ".cs": "C#",
    ".ts": "TypeScript",
    ".java": "Java",
    ".php": "PHP",
    ".hh": "C++",
    ".cc": "C++",
}

# Initialize SBERT model and load dataset links
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
excel_path = "Serverless_Function_Reuse.xlsx"
df = pd.read_excel(excel_path, sheet_name=0)
dataset_links = df.set_index("folder_name")["link"].to_dict()
allowed_extensions = set(EXT_LANG_MAP.keys())

def compute_folder_hash(folder_path):
    """Compute the hash of all files in a folder, regardless of file type."""
    hash_obj = hashlib.md5()
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):  # Keep consistent order
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                hash_obj.update(f.read())
    return hash_obj.hexdigest()

def detect_languages(folder_path):
    """Detect programming languages based on file extensions in a folder."""
    langs = set()
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in allowed_extensions:
                langs.add(EXT_LANG_MAP.get(ext, ext))
    return sorted(langs)


def load_existing_dataset(code_vector_dataset_path):
    """Load existing code_vector_dataset.json if it exists."""
    if os.path.exists(code_vector_dataset_path):
        with open(code_vector_dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_dataset_links(code_vector_dataset):
    df = pd.read_excel(excel_path, sheet_name=0)
    new_links = df.set_index("folder_name")["link"].to_dict()
    """Ensure each entry has a link from the Excel mapping."""
    for function_name, link in new_links.items():
        if function_name in code_vector_dataset and not code_vector_dataset[function_name].get("link"):
            code_vector_dataset[function_name]["link"] = link
    return code_vector_dataset


def process_folders_incremental(base_path, code_vector_dataset_path):
    """Process only new or changed folders: vectorize code and detect languages."""
    existing_data = load_existing_dataset(code_vector_dataset_path)
    code_vector_dataset = existing_data.copy()

    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path):
            continue

        # Compute folder hash and skip if unchanged
        folder_hash = compute_folder_hash(folder_path)
        if folder_name in existing_data and existing_data[folder_name].get("hash") == folder_hash:
            continue
        
        # print(f"Processing folder: {folder_name}")
        # Detect programming languages
        used_programming_languages = detect_languages(folder_path)

        # Read and concatenate code files
        code_texts = []
        for root, _, files in os.walk(folder_path):
            for file in sorted(files):
                if os.path.splitext(file)[1] in allowed_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code_texts.append(f.read())
                    except Exception as e:
                        print(f"Warning: Failed to read {file_path}: {e}")
        if not code_texts:
            print(f"Skipping {folder_name}: no code files found")
            continue

        # Vectorize concatenated code
        task_vector = sbert_model.encode("\n".join(code_texts)).tolist()
        dataset_link = dataset_links.get(folder_name, "")

        # Build dataset entry
        code_vector_dataset[folder_name] = {
            "used_programming_languages": used_programming_languages,
            "link": dataset_link,
            "hash": folder_hash,
            "vector": task_vector,
        }
        print(f"Processed {folder_name}")

    # Update missing links and return
    code_vector_dataset = update_dataset_links(code_vector_dataset)
    return code_vector_dataset

def save_datasets(code_vector_dataset, code_vector_dataset_path):
    """Save the updated version code_vector_dataset.json"""
    with open(code_vector_dataset_path, "w", encoding="utf-8") as f:
        json.dump(code_vector_dataset, f, indent=4, ensure_ascii=False)
    # print(f"Vector dataset updated at: {code_vector_dataset}")


if __name__ == "__main__":
    base_path = "your function dataset file path"
    output_dir = "output path"
    code_vector_dataset_path = os.path.join(output_dir, "baseline2.json")

    os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(base_path) and os.listdir(base_path):
        try:
            code_vector_dataset = process_folders_incremental(base_path, code_vector_dataset_path)
            save_datasets(code_vector_dataset, code_vector_dataset_path)
        except Exception as e:
            print(f"Unhandled exception: {e}")
    else:
        print(f"Error: No valid folders found in {base_path}")

