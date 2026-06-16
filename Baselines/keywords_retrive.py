import os
import json
import re
import time
import numpy as np
import pandas as pd

# Keyword matching dependencies
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

porter = PorterStemmer()

excel_path = "Serverless_Function_Reuse.xlsx"
df = pd.read_excel(excel_path, sheet_name=0)
dataset_links = df.set_index("folder_name")["link"].to_dict()

# Ensure NLTK resources are available
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

ps = PorterStemmer()

def generate_keywords(text):
    """
    Tokenize text, remove stopwords and non-alphabetic tokens,
    apply Porter stemming, and return a set of stems.
    """
    tokens = re.findall(r"\b\w+\b", text.lower())
    words = [w for w in tokens if w.isalpha() and w not in stop_words]
    stems = [ps.stem(w) for w in words]
    return set(stems)

def find_top_matches(user_input, keywords_dataset, target_folder_name, top_n=20):
    """
    Find the top N folder matches based on keyword overlap.
    Other structure and variable names remain unchanged.
    """
    # 1) Generate keyword set from user input
    K = generate_keywords(user_input)
    total_keywords = len(K)
    # print(f"Task description keywords: {K}")
    # print(f"[DEBUG] total_keywords={total_keywords}, dataset size={len(keywords_dataset)}")

    if total_keywords == 0:
        print("keywords is None")
        return [], None, [], 0.0

    start_time = time.time()
    matches = []
    target_matched_keywords = []
    match_count = 0
    # 2) Iterate over dataset entries and count keyword hits
    for folder_name, data in keywords_dataset.items():
        # Assume data['keywords'] is a list of raw keywords for each folder
        dataset_keywords = data.get('keywords', [])
        # Stem dataset keywords
        dataset_stems = set(ps.stem(w.lower()) for w in dataset_keywords if w.isalpha())
        # Count hits of K in dataset_stems
        target_matched_keywords = [kw for kw in dataset_stems if kw in K]
        match_count = len(target_matched_keywords)
        # match_count = sum(1 for kw in dataset_stems if kw in K)
        if match_count > 0:
            match_ratio = round(match_count / total_keywords, 4)
            matches.append({
                'folder_name': folder_name,
                'match_count': match_count,
                'similarity': match_ratio,  # reuse 'similarity' field to store match count
                'link': data.get('link', ''),
                'target_matched_keywords': target_matched_keywords
            })

    # 3) Sort matches by match count (previously 'similarity') descending
    matches = sorted(matches, key=lambda x: x['similarity'], reverse=True)

    end_time = time.time()
    latency = end_time - start_time
    if not matches:
        print("Warning: No matches found.")
        return [], None, [], latency, []
    
    # print(f"Available folders in dataset: {[match['folder_name'] for match in matches]}")

    # 4) Determine the rank of the target folder
    target_rank = None
    for i, match in enumerate(matches):
        if match['folder_name'] == target_folder_name:
            target_rank = i + 1
            break
    # print(f"Target rank found: {target_rank}")
    return matches[:top_n], target_rank, matches, latency, target_matched_keywords

def process_excel_file(file_path, keywords_dataset, output_path="output.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    results = []

    # The first column as target_folder_name, the third column as user_input
    for index, row in df.iterrows():
        target_folder_name = str(row.iloc[0]).strip()
        user_input = str(row.iloc[2]).strip()

        tokens = re.findall(r"\b\w+\b", user_input.lower())
        filtered = [porter.stem(tok) for tok in tokens if tok not in stop_words]
        K = set(filtered)

        if len(K) == 0:
            print("keywords is None")

        top_matches, target_rank, all_matches,latency, target_matched_keywords = find_top_matches(user_input, keywords_dataset, target_folder_name, top_n=20)
        
        # Extract the similarity of the target folder (formatted to 4 decimal places)
        target_similarity = None
        if target_rank and target_rank <= len(all_matches):
            target_match_count = f"{all_matches[target_rank - 1]['match_count']}"
            target_similarity = f"{all_matches[target_rank - 1]['similarity']:.4f}"
            target_matched_keywords = all_matches[target_rank-1]['target_matched_keywords']
        else:
            target_similarity = ""
        
        # Extract a list of folder names for all matching items
        folder_names = [match["folder_name"] for match in all_matches]

        result_row = {
            "function": row["function ID"],
            "task_description": row["request description"],
            "task_keywords": K,
            "target_matched_keywords": target_matched_keywords,
            "target_match_count": target_match_count,
            "target_similarity": target_similarity,
            "target_rank": target_rank if target_rank is not None else "",
            # "all_folder_names": ", ".join(folder_names)
            "latency": latency
        }

        results.append(result_row)
        # time.sleep(5)

    if results:
        results_df = pd.DataFrame(results)
        try:
            results_df.to_excel(output_path, index=False)
            print(f"Results successfully saved to {output_path}")
        except Exception as e:
            print(f"Error saving results to Excel: {e}")
    else:
        print("No results to save.")

if __name__ == "__main__":
    # Load keywords_dataset from previous code's output、
    keywords_dataset_path = "/Users/sunyuehan/Desktop/code/all_result/baseline1.json"
    try:
        with open(keywords_dataset_path, 'r', encoding='utf-8') as f:
            keywords_dataset = json.load(f)
    except FileNotFoundError:
        print(f"Error: Vector dataset file not found at {keywords_dataset_path}")
        keywords_dataset = {}
    
    mode = input("Please select the processing mode (1: single input, 2: batch processing of Excel files):")
    if mode.strip() == "2":
        file_path = input("input the Excel path: ")
        output_path = input("input the output path: ")
        if not output_path:
            output_path = "output.xlsx"
        process_excel_file(file_path, keywords_dataset, output_path)
    else:
        user_input = input("Enter a description of the function: ")
        target_folder_name = input("Enter the target folder name: ")
        top_matches, target_rank, all_matches = find_top_matches(user_input, keywords_dataset, target_folder_name, top_n=20)
        
        print("Top matches:")
        for i, match in enumerate(top_matches, start=1):
            print(f"{i}. Folder: {match['folder_name']}, Match account:{match['match_count']}, Similarity: {match['similarity']:.4f}, Link: {match['link']}")
        
        if target_rank and target_rank > 10:
            print(f"Target folder '{target_folder_name}' found at rank {target_rank} with similarity {all_matches[target_rank - 1]['similarity']:.4f}, Match account:{match['match_count']}, Link: {all_matches[target_rank - 1]['link']}")
