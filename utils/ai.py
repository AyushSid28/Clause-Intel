from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#I have used gpt-4o-mini as it doesnt cost much money and is pretty fast.

#This function takes the text and actually getting a json response involving clauses.
def get_openai_extraction(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract Valuation, Liquidation Preference, and Board Composition from the text. Return a JSON object in this exact format: {\"valuation\": {\"text\": \"Valuation: $10M\", \"explanation\": \"Explanation here\"}, \"liquidation\": {\"text\": \"Liquidation Preference: 1x\", \"explanation\": \"Explanation here\"}, \"board\": {\"text\": \"Board Composition: 3 seats\", \"explanation\": \"Explanation here\"}}. If a clause is not found, set its text to an empty string. Provide a 50-word explanation for each clause, highlighting risks. Do not include any code in the response."
                },
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content.strip()
        print("Raw OpenAI Extraction Response:", result) 
        try:
            parsed_result = json.loads(result)
            expected_keys = ["valuation", "liquidation", "board"]
            for key in expected_keys:
                if key not in parsed_result or "text" not in parsed_result[key] or "explanation" not in parsed_result[key]:
                    raise ValueError(f"Invalid structure for {key}")
            return parsed_result
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "valuation": {"text": "", "explanation": "Could not extract Valuation clause."},
                "liquidation": {"text": "", "explanation": "Could not extract Liquidation Preference clause."},
                "board": {"text": "", "explanation": "Could not extract Board Composition clause."}
            }
    except Exception as e:
        return {
            "valuation": {"text": "", "explanation": "Error extracting Valuation clause."},
            "liquidation": {"text": "", "explanation": "Error extracting Liquidation Preference clause."},
            "board": {"text": "", "explanation": "Error extracting Board Composition clause."}
        }

#this logic will handle how the explanation is being generated witht the help of OpenAI's API
def get_explanation(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful legal assistant. You have to explain the given clauses in 160-190 words,explain the pros and cons of the clause, highlighting risks. Return only the explanation as a string, no JSON or code."},
                {"role": "user", "content": f"Explain this clause: {text}"}
            ]
        )
        explanation = response.choices[0].message.content.strip()
        return explanation
    except Exception as e:
        return "Error generating explanation."

#This method is used for generating the summary of the clauses with the help of OpenAI's API
def get_summary(clauses):
    try:
        clause_text = "\n".join(f"{key.capitalize()}: {data['text']}" for key, data in clauses.items())
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize the given clauses in 200-300 words.Keep your tone friendly for the user.Explain the pros and cons of the combined clauses.You can also hint the user about further improvements he can do  for betterment in future.You can use pointers but dont use (#**) these symbols keep it professional use numbers to show the depth and you can also use numbers to highlight a potenial growth for the summary"},
                {"role": "user", "content": f"Summarize these clauses:\n{clause_text}"}
            ]
        )
        summary = response.choices[0].message.content.strip()
        print("Summary:", summary) 
        return summary
    except Exception as e:
        print("Error in get_summary:", str(e)) 
        return "Error generating summary."