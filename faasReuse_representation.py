import os
import json
import re
import hashlib
import openai
import time
import pandas as pd
from openai import OpenAI
import asyncio
from anthropic import Anthropic # type: ignore
from sentence_transformers import SentenceTransformer 
from mapping import standardize_category

client = OpenAI(
    base_url='https://api.aimlapi.com/v1',
    api_key= 'your api_ke',
    )

# client = Anthropic(
#     base_url='https://api.aimlapi.com/',
#     auth_token='your api_ke',
# )
# chose_model = "claude-3-5-sonnet-20240620"

# chose_model = "gpt-4o"
# chose_model = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo" 
# chose_model = "google/gemini-2.5-pro-preview-05-06"
chose_model = "google/gemini-2.0-flash"
# chose_model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

# chose_model = "deepseek-chat"

# Initialize Sentence-BERT Model
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Load Excel Data
excel_path = "your function link dataset"
df = pd.read_excel(excel_path, sheet_name=0)

# Convert dataset function names to dictionary for lookup
dataset_links = df.set_index("folder_name")["link"].to_dict()


def create_prompt(data):
    """Generate the dynamic prompt for ChatGPT."""
    prompt = f"""{data}
    Please summarize its [task description], [used serverless platforms] (e.g., AWS Lambda and OpenWhisk), [used cloud services in functions] (e.g., AWS S3 and Google Firestore), and [used programming languages] (e.g., Python and JavaScript) according to the code of serverless function below.
    
    Important Notes:
    1.Serverless Framework is not a serverless platform and should not be listed under "Used Serverless Platforms".
    2.The use of specific cloud services and triggered handler function format may implicitly suggest the corresponding serverless platform.
    3.You don't need explanations of these information (include Serverless Platforms, Cloud Services and Programming Languages) and any summary sentence at the end.

    Returns 'None' if no serverless platforms, cloud servicess or programming language is identified.
    Answer Format (You MUST follow this):
    Task Description (at least 50 words):
    Serverless Platforms:
    Cloud Services:
    Programming Languages:
    """
    return prompt

def compute_folder_hash(folder_path):
    """Compute the hash of all files in a folder, regardless of file type."""
    hash_obj = hashlib.md5()
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):  # Keep consistent order
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                hash_obj.update(f.read())
    return hash_obj.hexdigest()

def summarize_folder(folder_path):
    """Summarize the contents of a folder using ChatGPT API."""
    folder_summary = ""
    allowed_extensions = {".py", ".js", ".go", ".rb", ".swift", ".rs", ".cs", ".ts", ".java", ".php", ".hh", ".cc", ".yaml", ".yml"}
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):
            # Skip README.md files
            ext = os.path.splitext(file)[1]
            if ext not in allowed_extensions:
                # print(f"Debug: Skipping file {file} due to extension {ext}")
                continue

            file_path = os.path.join(root, file)
            # print(f"Debug: Reading file {file_path}")  # Log the file being read
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    file_content = f.read()
                    folder_summary += f"\nFile: {file}\n{file_content}\n"
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    if not folder_summary.strip():
        print(f"Warning: No content found in folder {folder_path}")
        return ""
    
    prompt = create_prompt(folder_summary)
    try:
        # response = openai.chat.completions.create(
        response = client.chat.completions.create(
            model=chose_model,
            messages=[
                    # {"role": "system", "content": "You are an expert writing serverless functions."},
                    {"role": "assistant", "content": "You are an expert writing serverless functions."},
                    {"role": "user", "content": prompt},
                ], 
            temperature=0,
        )
        summary = response.choices[0].message.content
        
        # # for Sonnet model input
        # response = client.messages.create(
        #     model=chose_model,
        #     # max_tokens=4096,
        #     messages=[
        #         {"role": "assistant", "content": "You are an expert writing serverless functions."},
        #         {"role": "user", "content": prompt},
        #     ],
        #     temperature=0,
        # )
        # summary = response.content[0].text
        # summary = response.content
        # print(f"Debug: Generated summary for {folder_path}\n{summary}\n")  # Print summary to console
        return summary
    except Exception as e:
        print(f"Error: Failed to generate summary for folder {folder_path}: {e}")
        return ""

def save_datasets(code_vector_dataset_4o, output_path):
    """Save datasets to JSON files."""
    vector_output_path = os.path.join(output_path, "code_vector_dataset_4o.json")

    with open(vector_output_path, 'w', encoding='utf-8') as f:
        json.dump(code_vector_dataset_4o, f, indent=4, ensure_ascii=False)

    print(f"Datasets saved to {output_path}")
    print(f"Vector dataset saved at: {vector_output_path}")

def load_existing_dataset(code_vector_dataset_4o_path):
    """load exiisting code_vector_dataset_4o.json"""
    if os.path.exists(code_vector_dataset_4o_path):
        with open(code_vector_dataset_4o_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def update_dataset_links(excel_path, code_vector_dataset_4o):
    df = pd.read_excel(excel_path, sheet_name=0)
    new_links = df.set_index("folder_name")["link"].to_dict()
    
    # Only update the dataset with new links
    for function_name, link in new_links.items():
        if function_name in code_vector_dataset_4o and not code_vector_dataset_4o[function_name].get("link"):
            code_vector_dataset_4o[function_name]["link"] = link
    return code_vector_dataset_4o

def process_folders_incremental(base_path, code_vector_dataset_4o_path):
    """Only handle newly added or changed folders"""
    existing_data = load_existing_dataset(code_vector_dataset_4o_path)  
    code_vector_dataset_4o = existing_data.copy()

    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path):
            continue  # only handle folders

        # Calculate the hash value of the current folder
        folder_hash = compute_folder_hash(folder_path)

        # Check if it has been processed and the content has not changed
        if folder_name in existing_data and existing_data[folder_name].get("hash") == folder_hash:
            # print(f"Skipping {folder_name}, no changes detected.")
            continue  # Skip unchanged folders

        # Handle folders with new or changed content
        # print(f"Processing folder: {folder_name}")
        summary = summarize_folder(folder_path)
        if not summary:
            print(f"Warning: No valid summary for folder {folder_name}")
            continue

        try:
        # Define field names and initial data structures
            field_names = [
                "Task Description (at least 50 words):",
                "Task Description:",
                "Serverless Platforms:",
                "Cloud Services:",
                "Programming Languages:"
            ]

            summary_data = {
                "task_description": "",
                "used_serverless_platforms": "",
                "used_cloud_services": "",
                "used_programming_languages": "",
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
                    # regex = rf"(?<={re.escape(field)})(.*?)(?=')"
                    regex = rf"(?<={re.escape(field)})(.*)"
                    match = re.search(regex, summary, re.DOTALL)

                if match:
                    # Clean up the extracted content, remove spaces and symbols
                    # cleaned_content = re.sub(r"-", "", match.group(1)).strip()
                    #print(f"Matched content for {field}: {cleaned_content}")  
                    
                    # for Claude input
                    # raw = match.group(1).replace("-", "")
                    # lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                    # cleaned_content = ",".join(lines)

                    raw = match.group(1)
                    # Remove all parentheses and their contents, and then remove all hyphens
                    cleaned = re.sub(r"\([^)]*\)", "", raw).replace("-", "")
                    # Split by line, remove blank spaces and empty lines
                    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
                    # Use commas to spell directly (without spaces)
                    cleaned_content = ",".join(lines)


                    # Store the corresponding dictionary key according to the field name
                    if field.startswith("Task Description"):
                        summary_data["task_description"] = cleaned_content
                    elif "Serverless Platforms:" in field:
                        summary_data["used_serverless_platforms"] = cleaned_content
                    elif "Cloud Services:" in field:
                        summary_data["used_cloud_services"] = cleaned_content
                    elif "Programming Languages:" in field:
                        summary_data["used_programming_languages"] = cleaned_content
                else:
                    print(f"No match found for {field} for folder {folder_name}")  
            # print(f"{summary_data}")
            # Standardization
            summary_data["used_serverless_platforms"] = standardize_category(
                summary_data["used_serverless_platforms"], "used_serverless_platforms"
            )
            summary_data["used_cloud_services"] = standardize_category(
                summary_data["used_cloud_services"], "used_cloud_services"
            )
            summary_data["used_programming_languages"] = standardize_category(
                summary_data["used_programming_languages"], "used_programming_languages"
            ) 

            # print(f"Debug: Parsed summary data for folder {folder_name}: {summary_data}")

            # Vectorize Task Description
            if summary_data["task_description"]:
                task_vector = sbert_model.encode(summary_data["task_description"]).tolist()
                dataset_link = dataset_links.get(folder_name, "")
                #print(f"Debug: Vector for folder {folder_name}: {task_vector}\n")  # Print vector to console"""

                code_vector_dataset_4o[folder_name] = {
                    "task_description": summary_data["task_description"],
                    "used_serverless_platforms": summary_data["used_serverless_platforms"],
                    "used_cloud_services": summary_data["used_cloud_services"],
                    "used_programming_languages": summary_data["used_programming_languages"],
                    "link": dataset_link,
                    "hash": folder_hash,
                    "vector": task_vector,
                }
        except Exception as e:
            print(f"Error processing summary for {folder_name}: {e}")
    code_vector_dataset_4o = update_dataset_links(excel_path, code_vector_dataset_4o)
    time.sleep(5)
    return code_vector_dataset_4o

def save_datasets(code_vector_dataset_4o, code_vector_dataset_4o_path):
    """Save the updated code_vector_dataset_4o.json"""
    with open(code_vector_dataset_4o_path, "w", encoding="utf-8") as f:
        json.dump(code_vector_dataset_4o, f, indent=4, ensure_ascii=False)
    #print(f"Vector dataset updated at: {code_vector_dataset_4o_path}")


if __name__ == "__main__":
    base_path = input("input your function dataset path: ")  # Path to the dataset
    output_path = input("input the output path: ")      # Path to save output files
    code_vector_dataset_4o_path = os.path.join(output_path, "Gemini_dataset_5.json")

    os.makedirs(output_path, exist_ok=True)

    # Debugging information
    if os.path.exists(base_path) and os.listdir(base_path):
        try:
            code_vector_dataset_4o = process_folders_incremental(base_path, code_vector_dataset_4o_path)
            save_datasets(code_vector_dataset_4o, code_vector_dataset_4o_path)
        except Exception as e:
            print(f"Unhandled exception: {e}")
    else:
        print(f"Error: No valid folders found in {base_path}")


