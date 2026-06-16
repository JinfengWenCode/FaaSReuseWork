import os
import json
import re
import hashlib
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Ensure NLTK resources are available
# nltk.download('stopwords')
# nltk.download('punkt')

# Global Configuration
EXT_LANG_MAP = {
    ".py": "Python", ".java": "Java", ".js": "JavaScript", ".cpp": "C++",
    ".c": "C", ".cs": "C#", ".rb": "Ruby", ".go": "Go",
    ".php": "PHP", ".rs": "Rust", ".swift": "Swift",  ".hh": "C++",
    ".cc": "C++", ".ts": "TypeScript",
}
allowed_extensions = set(EXT_LANG_MAP.keys())

# Stop Words and Stemmers
STOP_WORDS = set(stopwords.words('english'))
ps = PorterStemmer()

# Excel Path
excel_path = "Serverless_Function_Reuse.xlsx"
df = pd.read_excel(excel_path, sheet_name=0)
dataset_links = df.set_index("folder_name")["link"].to_dict()


def compute_folder_hash(folder_path):
    """Calculate MD5 hash for all file contents in the folder"""
    hash_obj = hashlib.md5()
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                hash_obj.update(f.read())
    return hash_obj.hexdigest()


def detect_languages(folder_path):
    """Detect the programming language used in the folder"""
    langs = set()
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in allowed_extensions:
                langs.add(EXT_LANG_MAP[ext])
    return sorted(langs)


def tokenize_and_extract_keywords(text):
    """Split camel hump and underline, remove stop words, stem, generate keyword list"""
    # Extract all words or identifiers
    tokens = re.findall(r'\b[A-Za-z][A-Za-z0-9_]*\b', text)
    processed = []
    for tok in tokens:
        # Split camel hump
        split_camel = re.sub('([a-z])([A-Z])', r'\1 \2', tok)
        # Replace underline with space
        split_all = split_camel.replace('_', ' ')
        for part in split_all.split():
            processed.append(part.lower())
    # Stop using words and stem them
    keywords = set()
    for word in processed:
        if len(word) <= 2 or word in STOP_WORDS:
            continue
        stem = ps.stem(word)
        keywords.add(stem)
    return sorted(keywords)


def load_existing_dataset(code_keywords_dataset_path):
    """Load existing code_keywords_dataset.json if it exists."""
    if os.path.exists(code_keywords_dataset_path):
        with open(code_keywords_dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_dataset_links(code_keywords_dataset):
    df = pd.read_excel(excel_path, sheet_name=0)
    new_links = df.set_index("folder_name")["link"].to_dict()
    """Ensure each entry has a link from the Excel mapping."""
    for function_name, link in new_links.items():
        if function_name in code_keywords_dataset and not code_keywords_dataset[function_name].get("link"):
            code_keywords_dataset[function_name]["link"] = link
    return code_keywords_dataset


def process_folders_incremental(base_path, output_path):
    existing = load_existing_dataset(output_path)
    code_keywords_dataset = existing.copy()

    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path):
            continue

        folder_hash = compute_folder_hash(folder_path)
        if folder_name in existing and existing[folder_name]["hash"] == folder_hash:
            continue

        print(f"Processing: {folder_name}")
        used_programming_languages = detect_languages(folder_path)
        code_texts = []
        for root, _, files in os.walk(folder_path):
            for file in sorted(files):
                if os.path.splitext(file)[1] in allowed_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code_texts.append(f.read())
                    except Exception as e:
                        print(f"Warning: Can not read {file_path}: {e}")
        if not code_texts:
            print(f"Skipping {folder_name}: no code files")
            continue

        content = "\n".join(code_texts)
        keywords = tokenize_and_extract_keywords(content)
        dataset_link = dataset_links.get(folder_name, "")

        code_keywords_dataset[folder_name] = {
            "used_programming_languages": used_programming_languages,
            "hash": folder_hash,
            "link": dataset_link,
            "keywords": keywords,
        }
        print(f"Processed {folder_name}")

    code_keywords_dataset = update_dataset_links(code_keywords_dataset)
    return code_keywords_dataset

def save_datasets(code_keywords_dataset, code_keywords_dataset_path):
    """Save the updated version code_keywords_dataset.json"""
    with open(code_keywords_dataset_path, "w", encoding="utf-8") as f:
        json.dump(code_keywords_dataset, f, indent=4, ensure_ascii=False)
    # print(f"Vector dataset updated at: {code_keywords_dataset}")


if __name__ == '__main__':
    base_path = "your function dataset file path"
    output_dir = "output path"
    os.makedirs(output_dir, exist_ok=True)
    code_keywords_dataset_path = os.path.join(output_dir, 'baseline1.json')

    if os.path.isdir(base_path) and os.listdir(base_path):
        try:
            code_keyword_dataset = process_folders_incremental(base_path, code_keywords_dataset_path)
            save_datasets(code_keyword_dataset, code_keywords_dataset_path)
            print(f"Dataset saved to {code_keywords_dataset_path}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Error: No valid folders found in {base_path}")

        
