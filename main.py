import os
import json
import argparse
from src.parsers     import extract_text
from src.extractors  import extract_all

def process_resume(file_path: str, output_dir: str):
    """Processes a single resume and saves the extracted JSON."""
    print(f"Processing: {file_path}")
    
    # 1. Extract raw text AND embedded hyperlinks
    text, embedded_uris = extract_text(file_path)
    if not text and not embedded_uris:
        print(f"Failed to extract any content from {file_path}")
        return

    # 2. Extract structured data (text layer + embedded URI layer)
    extracted_data = extract_all(text, embedded_uris)
    
    # 3. Save to JSON
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    output_path = os.path.join(output_dir, f"{name_without_ext}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        
    print(f"Saved extracted data to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Resume Information Extraction System")
    parser.add_argument("--input_dir", type=str, default="data/sample_resumes", help="Directory containing resumes")
    parser.add_argument("--output_dir", type=str, default="data/outputs", help="Directory to save JSON outputs")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    if not os.path.exists(args.input_dir):
        print(f"Input directory '{args.input_dir}' not found.")
        return
        
    for filename in os.listdir(args.input_dir):
        if filename.endswith(".pdf") or filename.endswith(".docx"):
            file_path = os.path.join(args.input_dir, filename)
            process_resume(file_path, args.output_dir)

if __name__ == "__main__":
    main()
