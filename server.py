from flask import Flask, request, jsonify
from utils.extract import extract_clauses
from utils.ai import get_explanation, get_summary
import PyPDF2
import re
from dotenv import load_dotenv

#basically loading the env variables from.env
load_dotenv()
app = Flask(__name__)

#logic to check the uploaded file and extract the text from file if it exists
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    raw_text = ""
    if file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        raw_text = "".join(page.extract_text() for page in reader.pages)
    else:
        raw_text = file.read().decode("utf-8")
    
    # Filter raw_text to include only clauses starting from "1. VALUATION:"
    clause_match = re.search(r"(?i)1\.\s*VALUATION:.*?(?=\n\s*Other terms and conditions|\Z)", raw_text, re.DOTALL)
    if clause_match:
        raw_text = clause_match.group().strip()
    else:
        raw_text = ""  # Return empty if no clauses found
    
    clauses_text = ""
    patterns = {
        "valuation": r"(?i)1\.\s*VALUATION:.*?(?=\n\s*2\.|\Z)",
        "liquidation": r"(?i)2\.\s*LIQUIDATION PREFERENCE:.*?(?=\n\s*3\.|\Z)",
        "board": r"(?i)3\.\s*BOARD COMPOSITION:.*?(?=\n\s*Other terms|\Z)"
    }
    
    # Use the original raw_text for clause extraction to ensure we don't miss clauses
    original_text = raw_text if raw_text else file.read().decode("utf-8") if not file.filename.endswith(".pdf") else "".join(page.extract_text() for page in PyPDF2.PdfReader(file).pages)
    
    for key, pattern in patterns.items():
        match = re.search(pattern, original_text, re.DOTALL)
        if match:
            clause = match.group().strip()
            if key == "valuation":
                clause = clause.replace("VALUATION:", "VALUATION:", 1).replace("M", ",000,000")
            elif key == "liquidation":
                clause = clause.replace("LIQUIDATION PREFERENCE:", "LIQUIDATION PREFERENCE:", 1)
            elif key == "board":
                clause = clause.replace("BOARD COMPOSITION:", "BOARD COMPOSITION:", 1).replace("seats", "members")
            clauses_text += clause + "\n\n"
    
    text = clauses_text.strip() if clauses_text else ""
    
    clauses = extract_clauses(text)
    return jsonify({"text": text, "raw_text": raw_text, "clauses": clauses})  

#logic to explain the text and get the summary
@app.route("/explain", methods=["POST"])
def explain():
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    explanation = get_explanation(data["text"])
    response = {"text": data["text"], "explanation": explanation}
    return jsonify(response)

#logic to actully summarize the whole subsection of different clauses
@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    if not data:
        return jsonify({"error": "No clauses provided"}), 400
    summary = get_summary(data)
    return jsonify({"summary": summary})

if __name__ == "__main__":
    app.run(debug=True)