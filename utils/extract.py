import re
from utils.ai import get_openai_extraction, get_explanation

#Regex Logic to extract the clauses from the text file
def extract_clauses(text):
    clauses = {
        "valuation": {"text": "", "explanation": ""},
        "liquidation": {"text": "", "explanation": ""},
        "board": {"text": "", "explanation": ""}
    }
    
    text = re.sub(r'\s+', ' ', text.strip())
    print("Normalized Text:", text) 
    
    patterns = {
        "valuation": r"VALUATION:\s*\$?\d+\.?\d*,?\d*",
        "liquidation": r"LIQUIDATION PREFERENCE:\s*\d+\s*x.*?(?=\n|$)",
        "board": r"BOARD COMPOSITION:\s*\d+\s*members.*?(?=\n|$)"
    }
    
    found_all = True
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            clauses[key]["text"] = match.group().strip()
            clauses[key]["explanation"] = get_explanation(clauses[key]["text"])
        else:
            found_all = False
       
   #if the regex fails we can use OpenAI to basically extract the clause info
    if not found_all:
        print("Using OpenAI fallback")  
        openai_result = get_openai_extraction(text)
        print("OpenAI Result:", openai_result) 
        for key in clauses:
            if not clauses[key]["text"]:
                clauses[key]["text"] = openai_result.get(key, {}).get("text", "")
                clauses[key]["explanation"] = openai_result.get(key, {}).get("explanation", "")
    
    return clauses