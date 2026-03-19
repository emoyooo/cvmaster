import streamlit as st
from utils.document_processor import extract_text_from_pdf
from utils.ai import generate_ai_response

st.set_page_config(page_title="AI Career Coach", layout="wide", initial_sidebar_state="collapsed")

# --- ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if "cv_text" not in st.session_state:
    st.session_state.cv_text = None
if "detected_job" not in st.session_state:
    st.session_state.detected_job = None
if "user_name" not in st.session_state:
    st.session_state.user_name = "Candidate"

st.title("welcome to CVmaster!!")
st.write("upload your cv once to unlock ai analysis and mock interview preparation.")

st.divider()

uploaded_file = st.file_uploader("First, upload your CV (PDF)", type="pdf")

if uploaded_file:
    if st.session_state.cv_text is None: 
        with st.spinner("Processing your resume..."):
            text = extract_text_from_pdf(uploaded_file)
            st.session_state.cv_text = text
            
            basics = generate_ai_response(
                f"Extract Candidate Name and Target Job Title from this CV. Return ONLY JSON: {{'name': '...', 'job': '...'}}. CV: {text[:1000]}",
                system_prompt="Return pure JSON."
            )
            try:
                import json, re
                data = json.loads(re.search(r'\{.*\}', basics, re.DOTALL).group(0))
                st.session_state.user_name = data.get('name', 'Candidate')
                st.session_state.detected_job = data.get('job', 'Specialist')
            except:
                st.session_state.detected_job = "Specialist"

    st.success(f"CV Loaded! Welcome, {st.session_state.user_name}. Target Role: {st.session_state.detected_job}")
    
    st.write("### Choose your path:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("analyze cv", use_container_width=True):
            st.switch_page("pages/1_CV_Analyzer.py")
            
    with col2:
        if st.button("start interview", use_container_width=True):
            st.switch_page("pages/2_Interview_Prep.py")

else:
    st.info("Please upload your CV to proceed.")
    st.session_state.cv_text = None 