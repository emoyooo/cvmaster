import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from utils.document_processor import extract_text_from_pdf
from utils.ai import get_embedding, generate_ai_response
from utils.db import supabase, search_knowledge_base

st.set_page_config(page_title="CV Auditor", layout="wide")

if not st.session_state.get("cv_text"):
    st.warning("No CV found. Please go to the Home page and upload your resume.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Custom CSS для карточек (чтобы выглядели современно)
st.markdown("""
<style>
    .metric-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .status-pass { color: #28a745; font-weight: bold; font-size: 1.2rem; }
    .status-borderline { color: #ffc107; font-weight: bold; font-size: 1.2rem; }
    .status-reject { color: #dc3545; font-weight: bold; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

if st.button("← back to main"):
    st.switch_page("app.py")

st.title("analyze cv")
st.write(f"analysis for: **{st.session_state.detected_job}**")

cv_text = st.session_state.cv_text
    
if cv_text:
    if st.button("analyze cv"):
        with st.spinner("Recruiter AI is reviewing your application..."):
                
            cv_vector = get_embedding(cv_text[:1000])
            best_practices = search_knowledge_base('match_cv_best_practices', cv_vector)
                
            detected_job = st.session_state.detected_job or "Specialist"
                
            keywords_data = supabase.table("ats_keywords").select("keyword").execute()
            keywords_str = ", ".join([k['keyword'] for k in keywords_data.data[:20]])

            final_prompt = f"""                Act as a Senior Tech Recruiter. Perform a deep audit of this CV for the position of '{detected_job}'.

                KNOWLEDGE BASE GUIDELINES:
                {best_practices}

                REQUIRED ATS KEYWORDS:
                {keywords_str}

                CV CONTENT:
                {cv_text[:4000]}

                ---
                EVALUATION CRITERIA:
                1. MANDATORY SECTIONS: Check for (Contact Info, Job Title, Experience, Hard/Soft Skills, Education).
                2. ADDITIONAL SECTIONS: Check for (Summary, Certifications, Languages, Portfolio/Projects, Achievements, Volunteering).
                3. CRITICAL ISSUES: High-risk factors (e.g., job hopping, lack of measurable results, poor formatting).
                4. MEDIUM ISSUES: Things that reduce competitiveness (e.g., weak action verbs, lack of summary).
                5. SKILL GAPS: Compare CV content vs expected skills for {detected_job}.
                6. RECRUITER RISKS: Explain why a human recruiter might doubt this candidate.

                ---
                OUTPUT FORMAT:
                You MUST return the response in two parts:
                PART 1: A JSON block with these exact keys: "screening_status" (Likely Pass / Borderline / Likely Rejected), "overall_score" (1-10), "missing_mandatory_sections" (list), "weak_sections" (list).
                PART 2: A detailed Markdown report including:
                - Overall Quality Assessment
                - Critical Issues (Rejection risks)
                - Medium Issues
                - Strengths
                - Skill Gap Analysis
                - Recruiter Risk Explanation
                - Concrete Improvement Actions
                """

            full_response = generate_ai_response(final_prompt)
                
            try:
                json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
                if json_match:
                    json_part = json_match.group(0)
                    metrics = json.loads(json_part)
                        
                    if "PART 2:" in full_response:
                        report_part = full_response.split("PART 2:")[1].strip()
                    else:
                        report_part = full_response[json_match.end():].strip()
                else:
                    raise ValueError("JSON not found in response")
                        
            except Exception as e:
                st.error(f"Error parsing metrics. Displaying raw report.")
                st.markdown(full_response)
                st.stop()

            st.divider()
            st.subheader("analysis results")
                
            m_col1, m_col2, m_col3 = st.columns(3)
                
            status = str(metrics.get('screening_status', 'Unknown'))
            score = metrics.get('overall_score', 0)
            missing_list = metrics.get('missing_mandatory_sections', [])
            weak_list = metrics.get('weak_sections', [])

            with m_col1:
                status_class = "status-pass" if "Pass" in status else ("status-borderline" if "Borderline" in status else "status-reject")
                st.markdown(f"""<div class="metric-card">
                    <p style="margin-bottom:0;">Pass Screening</p>
                    <p class="{status_class}" style="margin-top:0;">{status}</p>
                </div>""", unsafe_allow_html=True)
                
            with m_col2:
                st.markdown(f"""<div class="metric-card">
                    <p style="margin-bottom:0;">Overall Quality</p>
                    <p style="font-size: 1.5rem; font-weight: bold; margin-top:0;">{score} / 10</p>
                </div>""", unsafe_allow_html=True)
                
            with m_col3:
                missed_count = len(missing_list)
                st.markdown(f"""<div class="metric-card">
                    <p style="margin-bottom:0;">Missing Sections</p>
                    <p style="color: {'#dc3545' if missed_count > 0 else '#28a745'}; font-size: 1.5rem; font-weight: bold; margin-top:0;">{missed_count}</p>
                </div>""", unsafe_allow_html=True)

            if missing_list or weak_list:
                st.write("") 
                with st.container():
                    if missing_list:
                        st.error(f"**Missing Mandatory Sections:** {', '.join(missing_list)}")
                    if weak_list:
                        st.warning(f"**Weak Sections:** {', '.join(weak_list)}")

            st.markdown(report_part)