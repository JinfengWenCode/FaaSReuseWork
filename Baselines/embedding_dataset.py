import os
import json
import re
import openai
import time
import numpy as np
import pandas as pd
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize SBERT model and load dataset links
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
excel_path = "Serverless_Function_Reuse.xlsx"
df = pd.read_excel(excel_path, sheet_name=0)
dataset_links = df.set_index("folder_name")["link"].to_dict()

def calculate_similarity(task_vector, dataset_vector):
    """Calculate cosine similarity between two vectors."""
    return cosine_similarity([task_vector], [dataset_vector])[0][0]

def find_top_matches(user_input, vector_dataset, target_folder_name, top_n=20):
    """Find the top N matches and ensure target_folder_name is included."""
    start_time = time.time()
    matches = []

    # Generate task description embedding for user input
    user_task_vector = sbert_model.encode(user_input).tolist()

    for folder_name, data in vector_dataset.items():
        dataset_vector = np.array(data["vector"])
        task_similarity = calculate_similarity(user_task_vector, dataset_vector)
        matches.append({
            "folder_name": folder_name,
            "similarity": task_similarity,
            "link": data.get("link", "No link available")
        })
    
    matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)

    end_time = time.time()
    latency = end_time - start_time 

    if not matches:
        print("Warning: No matches found.")
        return [], None, [], latency
    
    # print(f"Available folders in dataset: {[match['folder_name'] for match in matches]}")
    
    target_rank = None
    for i, match in enumerate(matches):
        if match["folder_name"] == target_folder_name:
            target_rank = i + 1
            break
    # print(f"Target rank found: {target_rank}")
    return matches[:top_n], target_rank, matches, latency
    
def process_excel_file(file_path, vector_dataset, output_path="output.xlsx"):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    results = []

    # The first column as target_folder_name, the third column as user_input
    for index, row in df.iterrows():
        target_folder_name = str(row.iloc[0]).strip()
        user_input = str(row.iloc[1]).strip()

        top_matches, target_rank, all_matches, latency = find_top_matches(user_input, vector_dataset, target_folder_name, top_n=20)
        
        # Extract the similarity of the target folder (formatted to 4 decimal places)
        if target_rank and target_rank <= len(all_matches):
            target_similarity = f"{all_matches[target_rank - 1]['similarity']:.4f}"
        else:
            target_similarity = ""
        
        # Extract a list of folder names for all matching items
        folder_names = [match["folder_name"] for match in all_matches]
        count = len(folder_names)

        result_row = {
            "function": row["function"],
            "task_description": row["task_description"],
            "target_similarity": target_similarity,
            "target_rank": target_rank if target_rank is not None else "",
            "all_folder_names": ", ".join(folder_names),
            "count_folder": count,
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
    # Load vector_dataset from previous code's output
    vector_dataset_path = "your vector_dataset_path"
    try:
        with open(vector_dataset_path, 'r', encoding='utf-8') as f:
            vector_dataset = json.load(f)
    except FileNotFoundError:
        print(f"Error: Vector dataset file not found at {vector_dataset_path}")
        vector_dataset = {}
    
    mode = input("Please select the processing mode (1: single input, 2: batch processing of Excel files):")
    if mode.strip() == "2":
        file_path = input("input the Excel path：")
        output_path = input("input the output path：")
    if not output_path:
        output_path = "output.xlsx"
    process_excel_file(file_path, vector_dataset, output_path)
    



        