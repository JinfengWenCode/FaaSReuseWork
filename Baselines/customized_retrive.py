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
from mapping import standardize_category

# Set OpenAI API Key
openai.api_key = "your api_key"
# client = OpenAI(
#     api_key="your api_key", 
#     base_url="https://api.deepseek.com/v1"
#     )

# Initialize Sentence-BERT Model
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')


def create_prompt(data):
    """Generate the dynamic prompt for ChatGPT."""
    prompt = f"""
    Please summarize its [request functionality description] (e.g., this request aims to implement a video processing task.), [used serverless platforms] (e.g., AWS Lambda and OpenWhisk), [used cloud services in functions] (e.g., AWS S3, Google Firestore and Twilio), and [used programming languages] (e.g., Python and JavaScript) according to the text of serverless function description below. You don't need explanations for this information or a summary sentence at the end.

    Important Notes:
    1.Serverless Framework is not a serverless platform and should not be listed under "Used Serverless Platforms".
    2.The use of specific cloud services may implicitly suggest the corresponding serverless platform.

    Please output exactly in this format (You MUST follow this). If a value is not found, return "None" and there is no need for any explanation.:
    Task Description (at least 50 words):

    The following is task request:
    {data}
    """
    return prompt

def summarize_user_input(user_input):
    """Summarize user input using ChatGPT API."""
    prompt = create_prompt(user_input)
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
        # response = client.chat.completions.create(
        #     model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert in extracting request intend about writing serverless functions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        summary = response.choices[0].message.content
        # print(f"Debug: Summary generated:\n{summary}\n")
        return summary
    except Exception as e:
        print(f"Error: Failed to summarize user input: {e}")
        return ""
    
def parse_summary(summary):
    """Parse the structured summary into individual fields."""
    field_names = [
        "Task Description (at least 50 words):"
    ]
    
    summary_data = {
        "task_description": "",
    }
    # Traverse field names and extract the content between them and the next field name
    for i, field in enumerate(field_names):
        next_field = field_names[i + 1] if i + 1 < len(field_names) else None
        #regex = rf"(?<={re.escape(field)})(.*?)(?={re.escape(next_field)}|$)"
        if next_field:
             # Dynamically generate regular expressions for non last fields
            regex = rf"(?<={re.escape(field)})(.*?)(?=\n{re.escape(next_field)}|$)"
            match = re.search(regex, summary, re.DOTALL)
        else:
            # Process the last field separately and match it to the end of the document
            regex = rf"(?<={re.escape(field)})(.*)"
            match = re.search(regex, summary, re.DOTALL)

        if match:
            # Clean up the extracted content, remove spaces and symbols
            cleaned_content = re.sub(r"-", "", match.group(1)).strip()
            #print(f"Matched content for {field}: {cleaned_content}") 

            # Call the standardization function in the mapping module for processing (please ensure that standardize_category is imported at the beginning of the file)
            # Store the corresponding dictionary key according to the field name
            if "Task Description (at least 50 words):" in field:
                summary_data["task_description"] = cleaned_content
        else:
            print(f"No match found for {field}")  # Debug Output      
   
    # print(f"Prase summary: \n{summary_data}\n")          
    return summary_data

def parse_summary_extended(summary):
    """
    Parse summary to extract both raw and parsed fields.
    Return two dictionaries:
      raw_fields: key "Task Description (at least 50 words):", "Serverless Platforms:", "Cloud Services:", "Programming Languages:"
      parsed_fields: key task_description, used_serverless_platforms, used_cloud_services, used_programming_languages
    """
    field_definitions = [
        ("Task Description (at least 50 words):", "task_description"),
    ]
    raw_fields = {}
    parsed_fields = {}
    for idx, (raw_key, parsed_key) in enumerate(field_definitions):
        # If it is not the last field, match it before the next field; Otherwise, match to the end of the string
        if idx < len(field_definitions) - 1:
            next_raw = field_definitions[idx+1][0]
            pattern = rf"(?<={re.escape(raw_key)})(.*?)(?=\n{re.escape(next_raw)}|$)"
        else:
            pattern = rf"(?<={re.escape(raw_key)})(.*)"
        match = re.search(pattern, summary, re.DOTALL)
        if match:
            extracted = re.sub(r"-", "", match.group(1)).strip()
        else:
            extracted = "None"
            print(f"No match found for {raw_key}")
        raw_fields[raw_key] = extracted
        if parsed_key == "task_description":
            parsed_fields[parsed_key] = extracted
        else:
            parsed_fields[parsed_key] = standardize_category(extracted, parsed_key)
    return raw_fields, parsed_fields

def calculate_similarity(task_vector, dataset_vector):
    """Calculate cosine similarity between two vectors."""
    return cosine_similarity([task_vector], [dataset_vector])[0][0]

def find_top_matches(user_summary, vector_dataset, target_folder_name, top_n=20):
    """Find the top N matches and ensure target_folder_name is included."""
    start_time = time.time()
    # Generate task vectors based on user requests
    user_task_vector = sbert_model.encode(user_summary["task_description"]).tolist()
    matches = []

    for folder_name, data in vector_dataset.items():
        # Calculate task description similarity
        dataset_vector = np.array(data["vector"])
        task_similarity = calculate_similarity(user_task_vector, dataset_vector)
        matches.append({
            "folder_name": folder_name,
            "similarity": task_similarity,
            "link": data.get("link", "No link available")
        })
    
    matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)
    
    # print(f"Available folders in dataset: {[match['folder_name'] for match in matches]}")
    end_time = time.time()
    latency = end_time - start_time
    # Debug: If there are no matches, print a warning message
    if not matches:
        print("Warning: No matches found.")
        return [], None, [], latency
    
    target_rank = None
    for i, match in enumerate(matches):
        if match["folder_name"] == target_folder_name:
            target_rank = i + 1
            break
    print(f"Target rank found: {target_rank}")
    
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
        user_input = str(row.iloc[2]).strip()
        # print(f"Processing row {index+1}: target_folder_name={target_folder_name}, user_input={user_input}")
        
        summary = summarize_user_input(user_input)
        if not summary:
            print("Skipping row due to empty summary.")
            continue
        
        # Simultaneously parse the original fields and standardized structured content
        parsed_fields = parse_summary(summary)
        raw_fields, parsed_fields = parse_summary_extended(summary)
        
        # Call find_top_matches to use the parsed structured content
        top_matches, target_rank, all_matches, latency = find_top_matches(parsed_fields, vector_dataset, target_folder_name, top_n=20)
        
        # Extract the similarity of the target folder (formatted to 4 decimal places)
        if target_rank and target_rank <= len(all_matches):
            target_similarity = f"{all_matches[target_rank - 1]['similarity']:.4f}"
        else:
            target_similarity = ""
        
        # Extract a list of folder names for all matching items
        folder_names = [match["folder_name"] for match in all_matches]
        
        result_row = {
            # "Task Description (at least 50 words)": raw_fields.get("Task Description (at least 50 words):", ""),
            "task_description": parsed_fields.get("task_description", ""),
            "target_similarity": target_similarity,
            "target_rank": target_rank if target_rank is not None else "",
            "all_folder_names": ", ".join(folder_names),
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
    vector_dataset_path = "your vector dataset"
    try:
        with open(vector_dataset_path, 'r', encoding='utf-8') as f:
            vector_dataset = json.load(f)
    except FileNotFoundError:
        print(f"Error: Vector dataset file not found at {vector_dataset_path}")
        vector_dataset = {}
    
    mode = input("Please select the processing mode (1: single input, 2: batch processing of Excel files):")
    if mode.strip() == "2":
        file_path = input("input the Excel path: ")
        output_path = input("input the output path (default output.xlsx):").strip()
        if not output_path:
            output_path = "output.xlsx"
        process_excel_file(file_path, vector_dataset, output_path)
    else:
        user_input = input("Enter a description of the function: ")
        target_folder_name = input("Enter the target folder name: ")
        summary = summarize_user_input(user_input)
        parsed_summary = parse_summary(summary)
        parsed_summary["target_folder_name"] = target_folder_name
        top_matches, target_rank, all_matches = find_top_matches(parsed_summary, vector_dataset, target_folder_name, top_n=20)
        
        print("Top matches:")
        for i, match in enumerate(top_matches, start=1):
            print(f"{i}. Folder: {match['folder_name']}, Similarity: {match['similarity']:.4f}, Platform: {match['platform']}, Language: {match['language']}, Cloud Service: {match['cloud_service']}, Link: {match['link']}")
        
        if target_rank and target_rank > 10:
            print(f"Target folder '{target_folder_name}' found at rank {target_rank} with similarity {all_matches[target_rank - 1]['similarity']:.4f}, Platform: {all_matches[target_rank - 1]['platform']}, Language: {all_matches[target_rank - 1]['language']}, Cloud Service: {all_matches[target_rank - 1]['cloud_service']}, Link: {all_matches[target_rank - 1]['link']}")


