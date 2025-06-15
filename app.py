import streamlit as st
import requests
import json
from io import BytesIO

st.set_page_config(page_title="Clause Intel", layout="wide")

# Importing the css from style dir
with open("style/style.css", "r") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

st.title("Clause Intel: Your AI Friend for all your legal needs.")
st.write("One Stop for all your legal queries")

# extract the session state 
if "clauses" not in st.session_state:
    st.session_state.clauses = None
if "full_text" not in st.session_state:
    st.session_state.full_text = ""  
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""  
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "is_sample_file" not in st.session_state:
    st.session_state.is_sample_file = False
if "editing_clause" not in st.session_state:
    st.session_state.editing_clause = None
if "success_shown" not in st.session_state:
    st.session_state.success_shown = False

# Logic to check if user has added a file
uploaded_file = st.file_uploader("Upload Term Sheet (PDF/Text)", type=["pdf", "txt"])
st.write("Sample Text File Use it to see the demo")
if st.button("Sample Term Sheet"):
    st.session_state.uploaded_file = BytesIO("".encode("utf-8"))
    st.session_state.uploaded_file.name = "sample1.txt"
    st.session_state.is_sample_file = True
    st.success("Sample term sheet loaded. Click 'Generate' to process.")

if st.session_state.uploaded_file and not uploaded_file:
    uploaded_file = st.session_state.uploaded_file

# generate button will handle the processing of file
st.write("Click the button given below to extract clauses")
if st.button("Generate"):
    st.session_state.success_shown = False
    if uploaded_file:
        if not st.session_state.is_sample_file and uploaded_file.type not in ["application/pdf", "text/plain"]:
            st.error("Please upload a PDF or text file.")
        else:
            files = {"file": (getattr(uploaded_file, "name", "uploaded_file"), uploaded_file)}
            try:
                response = requests.post("http://localhost:5000/upload", files=files)
                if response.status_code == 200:
                    response_data = response.json()
                    st.session_state.full_text = response_data["text"]  
                    st.session_state.raw_text = response_data["raw_text"]  
                    st.session_state.clauses = response_data["clauses"]  
                    st.session_state.summary = ""  
                    print("Upload Response:", response_data)
                    # Save clauses to a JSON file
                    with open("clauses_output.json", "w") as f:
                        json.dump(st.session_state.clauses, f, indent=4)
                else:
                    st.error(f"Error processing file: {response.status_code}")
            except Exception as e:
                st.error(f"Backend server error: {str(e)}")
    else:
        st.error("Please upload a file.")

# Display the full input text
if st.session_state.raw_text:
    st.write("YOUR TERM SHEET CLAUSES")

# method to show the data of clauses in subsection with an edit button
if st.session_state.clauses:
    for clause_type, data in st.session_state.clauses.items():
        st.subheader(clause_type.capitalize())
        if data["text"]:
            st.markdown(f"Raw: {data['text'].replace('\n', '<br>')}", unsafe_allow_html=True)
            st.markdown(f"AI Explanation: {data['explanation']}")
        else:
            st.write("Not found in document.")
      
        with st.form(key=f"edit_form_{clause_type}"):
            if st.form_submit_button(f"Edit {clause_type.capitalize()}"):
                st.session_state.editing_clause = clause_type
       # form will be saved after edit is made and we can actually see the updated clause in subsections
        if st.session_state.editing_clause == clause_type:
            with st.form(key=f"save_form_{clause_type}"):  
                new_text = st.text_input(f"Edit {clause_type.capitalize()} Text", value=data["text"], key=f"input_{clause_type}")
                if st.form_submit_button(f"Save {clause_type.capitalize()}"):
                    response = requests.post("http://localhost:5000/explain", json={"text": new_text})
                    if response.status_code == 200:
                        response_data = response.json()
                        st.session_state.clauses[clause_type] = {
                            "text": response_data["text"],
                            "explanation": response_data["explanation"]
                        }
                        print("Updated Clause:", st.session_state.clauses[clause_type])
                        st.session_state.summary = ""
                        st.session_state.editing_clause = None
                        st.success(f"{clause_type.capitalize()} updated!")
                        st.rerun()
                    else:
                        st.error("Error updating clause.")

# Summary section logic for handling the clauses and generating summary
if st.session_state.clauses:
    if st.button("Generate Summary"):
        response = requests.post("http://localhost:5000/summarize", json=st.session_state.clauses)
        print("Summarize Response:", response.json())
        if response.status_code == 200:
            st.session_state.summary = response.json().get("summary", "No summary available.")
            print("Summary set in session state:", st.session_state.summary)
            st.success("Summary generated successfully!")
            st.rerun()
        else:
            st.error("Error generating summary.")
    
    if st.session_state.summary:
        st.subheader("Summary")
        summary_html = f"""
        <div class="summary-box">
            <h2>Executive Summary</h2>
            {"".join(f"<p>{paragraph.strip()}</p>" for paragraph in st.session_state.summary.split("\n") if paragraph.strip())}
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)
    else:
        st.write("Click 'Generate Summary' to create one.")