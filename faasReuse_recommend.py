import os
import json
import re
import openai
import time
import numpy as np
import pandas as pd
from openai import OpenAI
import asyncio
from anthropic import Anthropic
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from mapping import standardize_category
from pareto import Function, pareto_single_function_selection


client = OpenAI(
    base_url='https://api.aimlapi.com/v1',
    api_key= 'your api_key',
    )

# chose_model = "gpt-4o"
# chose_model = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo" #开源的
# chose_model = "google/gemini-2.5-pro-preview-05-06"
# chose_model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
# chose_model = "deepseek-chat"
chose_model = "google/gemini-2.0-flash"

# client = Anthropic(
#     base_url='https://api.aimlapi.com/',
#     auth_token='your api_key',
# )
# chose_model = "claude-3-5-sonnet-20240620"


# Initialize Sentence-BERT Model
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def create_prompt(user_input):
    """Generate the dynamic prompt for ChatGPT."""
    prompt = f"""
    Please summarize its [request functionality description] (e.g., this request aims to implement a video processing task.), [used serverless platforms] (e.g., AWS Lambda and OpenWhisk), [used cloud services in functions] (e.g., AWS S3, Google Firestore and Twilio), and [used programming languages] (e.g., Python and JavaScript) according to the text of serverless function description below. You don't need explanations for this information or a summary sentence at the end.

    Important Notes:
    1.Serverless Framework is not a serverless platform and should not be listed under "Used Serverless Platforms".
    2.The use of specific cloud services may implicitly suggest the corresponding serverless platform.

    Please output exactly in this format (You MUST follow this). If a value is not found, return "None" and there is no need for any explanation.:
    Task Description (at least 50 words):
    Serverless Platforms:
    Cloud Services:
    Programming Languages:

    The following is task request:
    {user_input}
    """
    return prompt

def summarize_user_input(user_input):
    """Summarize user input using ChatGPT API."""
    prompt = create_prompt(user_input)
    try:
        # response = openai.chat.completions.create(
        #     model="gpt-4o",
        response = client.chat.completions.create(
            model=chose_model,
            messages=[
                # {"role": "system", "content": "You are an expert in extracting request intend about writing serverless functions."},
                {"role": "assistant", "content": "You are an expert writing serverless functions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        summary = response.choices[0].message.content

        # for Sonnet model input
        # response = client.messages.create(
        #     model=chose_model,
        #     max_tokens=4096,
        #     messages=[
        #         {"role": "assistant", "content": "You are an expert writing serverless functions."},
        #         {"role": "user", "content": prompt},
        #     ],
        #     temperature=0,
        # )
        # summary = response.content[0].text

        # print(f"Debug: Summary generated:\n{summary}\n")
        return summary
    except Exception as e:
        print(f"Error: Failed to summarize user input: {e}")
        return ""

def parse_summary(summary):
    """Parse the structured summary into individual fields."""
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
            regex = rf"(?<={re.escape(field)})(.*)"
            match = re.search(regex, summary, re.DOTALL)

        if match:
            # Clean up the extracted content, remove spaces and symbols
            cleaned_content = re.sub(r"-", "", match.group(1)).strip()
            #print(f"Matched content for {field}: {cleaned_content}") 

            # for Claude input
            # raw = match.group(1).replace("-", "")
            # lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            # cleaned_content = ",".join(lines)

            # Call the standardization function in the mapping module for processing (please ensure that standardize_category is imported at the beginning of the file)
            # Store the corresponding dictionary key according to the field name
            if field.startswith("Task Description"):
                summary_data["task_description"] = cleaned_content
            elif "Serverless Platforms:" in field:
                summary_data["used_serverless_platforms"] = standardize_category(cleaned_content, "used_serverless_platforms")
            elif "Cloud Services:" in field:
                summary_data["used_cloud_services"] = standardize_category(cleaned_content, "used_cloud_services")
            elif "Programming Languages:" in field:
                summary_data["used_programming_languages"] = standardize_category(cleaned_content, "used_programming_languages")
        else:
            print(f"No match found for {field}")  # Debug Output      
   
    # print(f"Prase summary: \n{summary_data}\n")          
    return summary_data

def parse_summary_extended(summary):
    """
    Parse summary to extract both raw and parsed fields.
    Return two dictionaries:
      raw_fields: key "Task Description:"、"Serverless Platforms:", "Cloud Services:", "Programming Languages:"
      parsed_fields: key task_description, used_serverless_platforms, used_cloud_services, used_programming_languages
    """
    field_definitions = [
        ("Task Description:", "task_description"),
        ("Serverless Platforms:", "used_serverless_platforms"),
        ("Cloud Services:", "used_cloud_services"),
        ("Programming Languages:", "used_programming_languages")
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
            # extracted = re.sub(r"-", "", match.group(1)).strip()

            # for Claude input
            raw = match.group(1).replace("-", "")
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            extracted = ",".join(lines)
        else:
            extracted = "None"
            # print(f"No match found for {raw_key}")
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
    """
    By combining nested for loops with Pareto optimization, candidate options are filtered sequentially for platform, language, and cloud service attributes, obtain the final non dominated candidate and ensure that target_folder_name is included in the result.
    """
    # Define the attributes that need to be filtered and the corresponding set of user targets
    attributes = [
        "used_serverless_platforms",
        "used_programming_languages",
        "used_cloud_services"
    ]
    user_targets = {
        "used_serverless_platforms": (user_summary["used_serverless_platforms"]),
        "used_programming_languages": (user_summary["used_programming_languages"]),
        "used_cloud_services": (user_summary["used_cloud_services"])
    }
    
    # Initial candidate set: All candidate items, construct a Function object based on the first attribute
    candidates = [
        Function(name=folder_name, services=data[attributes[0]])
        for folder_name, data in vector_dataset.items()
    ]
    final_pareto = None  # save the results of the last Pareto filter

    # Perform Pareto filtering on each attribute sequentially (using nested for loops)
    for attr in attributes:
        new_candidates = []
        # Update the service properties of each candidate based on the current attributes
        for candidate in candidates:
            # Extract the attribute set corresponding to the current candidate from the raw data
            services = vector_dataset[candidate.name][attr]
            new_candidates.append(Function(name=candidate.name, services=services))
        
        # Use Pareto method to filter out non dominated candidates under the current attribute
        pareto_results = pareto_single_function_selection(user_targets[attr], new_candidates)
        
        # Debug:Check the values of Jacquard distance and coverage
        # print(f"Pareto filtering results for attribute '{attr}':")
        # for func_obj, jd, cov in pareto_results:
        #     print(f" Function: {func_obj.name}, Jaccard distance: {jd:.4f}, coverage: {cov:.4f}")
        
        final_pareto = pareto_results
        # Retain the Function object in the filtering results of each stage (the elements in Pareto-results are (Function, jd, cov))
        candidates = [item[0] for item in final_pareto]

    # Output the metrics for the final screening results
    # if final_pareto is not None:
    #     print("\n Final screening results:")
    #     for func_obj, jd, cov in final_pareto:
    #         print(f"Function: {func_obj.name}, Jaccard distance: {jd:.4f}, coverage: {cov:.4f}")
    
    # Construct the final selected candidate items into a result dictionary
    filtered_items = {candidate.name: vector_dataset[candidate.name] for candidate in candidates}

     # Ensure that target_folder_name is always included in the results
    # if target_folder_name not in filtered_items and target_folder_name in vector_dataset:
    #     filtered_items[target_folder_name] = vector_dataset[target_folder_name]
    # fifth_time = time.time()
    # latency4 = fifth_time - fourth_time  

    for candidate_name, candidate_info in filtered_items.items():
        # Calculate task description similarity
        dataset_vector = np.array(candidate_info["vector"])
        task_similarity = calculate_similarity(user_task_vector, dataset_vector)
        matches.append({
            "folder_name": candidate_name,
            "similarity": task_similarity,
            "platform": candidate_info["used_serverless_platforms"],
            "language": candidate_info["used_programming_languages"],
            "cloud_service": candidate_info["used_cloud_services"],
            "link": candidate_info.get("link", "No link available")
        })

    # Sort the matching results in descending order based on similarity
    matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)

    end_time = time.time()
    latency = end_time - start_time
    # Debug: If there are no matches, print a warning message
    if not matches:
        print("Warning: No matches found.")
        # return [], None, [], latency1, latency2, latency3, latency4, latency5
        return [], None, [], latency
    
    # print(f"Available folders in dataset: {[match['folder_name'] for match in matches]}")

    # Check if target_folder_name is among the top n matches, otherwise continue searching
    target_rank = None
    for i, match in enumerate(matches):
        if match["folder_name"] == target_folder_name:
            target_rank = i + 1
            break
    # print(f"Target rank found: {target_rank}")
    
    
    # return matches[:top_n], target_rank, matches,latency1, latency2, latency3, latency4, latency5
    return matches[:top_n], target_rank, matches,latency

def process_excel_file(file_path, vector_dataset, output_path="output.xlsx"):
    """
    Processing Excel files:
      - Traverse each row: the first column is target_folder_name, and the third column is user_input.
      - Call summaze_user_input ->generate summary for each line, and then use parse_stummary_detented to obtain the original and parsed content.
      - Call find_top_matches to obtain matching results, extract the similarity, ranking, and list of all matching folder names of the target folder.
      - Save the above information in a new Excel file.
    """
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
        # print(f"Processing row {index+1}: target_folder_name={target_folder_name}")

        summary = summarize_user_input(user_input)
        if not summary:
            print("Skipping row due to empty summary.")
            continue
        
        # Parse the original fields and standardized structured content
        parsed_fields = parse_summary(summary)
        # raw_fields, parsed_fields = parse_summary_extended(summary)
        
        # Call find_top_matches to use the parsed structured content
        top_matches, target_rank, all_matches, latency = find_top_matches(parsed_fields, vector_dataset, target_folder_name, top_n=20)
    
        # Extract the similarity of the target folder (formatted to 4 decimal places)
        if target_rank and target_rank <= len(all_matches):
            target_similarity = f"{all_matches[target_rank - 1]['similarity']:.4f}"
        else:
            target_similarity = ""
        
        # Extract a list of folder names for all matching items
        folder_names = [match["folder_name"] for match in all_matches]
        count = len(folder_names)
        
        result_row = {
            "function": row["function ID"],
            "Task Description": row["request description"],
            # "task_description": raw_fields.get("Task Description (at least 50 words):", ""),
            # "Serverless Platforms": raw_fields.get("Serverless Platforms:", ""),
            # "Cloud Services": raw_fields.get("Cloud Services:", ""),
            # "Programming Languages": raw_fields.get("Programming Languages:", ""),
            "task_description": parsed_fields.get("task_description", ""),
            "used_serverless_platforms": parsed_fields.get("used_serverless_platforms", ""),
            "used_cloud_services": parsed_fields.get("used_cloud_services", ""),
            "used_programming_languages": parsed_fields.get("used_programming_languages", ""),
            "target_similarity": target_similarity,
            "target_rank": target_rank if target_rank is not None else "",
            "all_folder_names": ", ".join(folder_names),
            "count_folder": count,
            "latency": latency,
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
    vector_dataset_path = "Gemini/Gemini_dataset_5.json"
    # vector_dataset_path = "temperature=0.5/dataset_0.5_2.json"
    try:
        with open(vector_dataset_path, 'r', encoding='utf-8') as f:
            vector_dataset = json.load(f)
    except FileNotFoundError:
        print(f"Error: Vector dataset file not found at {vector_dataset_path}")
        vector_dataset = {}

    mode = input("Please select the processing mode (1: single input, 2: batch processing of Excel files):")
    if mode.strip() == "2":
        file_path = input("input the Excel path: ")
        output_path = input("input the output path (default output.xlsx): ").strip()
        if not output_path:
            output_path = "output.xlsx"
        process_excel_file(file_path, vector_dataset, output_path)
    else:
        user_input = input("Enter a description of the function: ")
        target_folder_name = input("Enter the target folder name: ")
        summary = summarize_user_input(user_input)
        parsed_summary = parse_summary(summary)
        top_matches, target_rank, all_matches = find_top_matches(parsed_summary, vector_dataset, target_folder_name, top_n=20)
        
        print("Top matches:")
        for i, match in enumerate(top_matches, start=1):
            print(f"{i}. Folder: {match['folder_name']}, Similarity: {match['similarity']:.4f}, Platform: {match['platform']}, Language: {match['language']}, Cloud Service: {match['cloud_service']}, Link: {match['link']}")
        
        if target_rank and target_rank > 10:
            print(f"Target folder '{target_folder_name}' found at rank {target_rank} with similarity {all_matches[target_rank - 1]['similarity']:.4f}, Platform: {all_matches[target_rank - 1]['platform']}, Language: {all_matches[target_rank - 1]['language']}, Cloud Service: {all_matches[target_rank - 1]['cloud_service']}, Link: {all_matches[target_rank - 1]['link']}")


