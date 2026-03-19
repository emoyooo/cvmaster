import sys
import os
import re
import json
import streamlit as st
import random
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.ai import get_embedding, generate_ai_response
from utils.db import supabase, search_knowledge_base

st.set_page_config(page_title="Interview!", layout="wide")

if "interview_stage" not in st.session_state:
    st.session_state.update({
        "interview_stage": "setup",
        "messages": [],           
        "interview_data": [],     
        "question_pool": [],      
        "current_question": None,
        "is_follow_up": False,    
        "job_title": st.session_state.get("detected_job", "Specialist"),
        "user_name": st.session_state.get("user_name", "Candidate"),
        "start_time": None
    })

if not st.session_state.get("cv_text"):
    st.warning("⚠️ No CV found. Please upload it on the Home page first.")
    st.stop()



def prepare_db_pool():
    job = st.session_state.job_title
    pool = []

    try:
        hr_res = supabase.table("behavioral_questions").select("question_template").execute()
        if hr_res.data:
            count_hr = min(len(hr_res.data), 5)
            hr_templates = random.sample(hr_res.data, count_hr)
            for r in hr_templates:
                q = generate_ai_response(
                    f"Adapt this template: '{r['question_template']}' for {job}. One sentence.",
                    system_prompt="Return only the question."
                )
                pool.append({"part": "HR", "text": q})
    except Exception as e:
        st.error(f"Error loading HR questions: {e}")

    try:
        job_vector = get_embedding(job)
        tech_res = search_knowledge_base('match_technical_questions', job_vector, match_count=50)
        if tech_res:
            count_tech = min(len(tech_res), 5)
            selected_tech = random.sample(tech_res, count_tech)
            for r in selected_tech:
                pool.append({"part": "Technical", "text": r['question_text']})
    except Exception as e:
        st.error(f"Error loading Tech questions: {e}")

    random.shuffle(pool) 
    st.session_state.question_pool = pool


def get_next_step(user_answer):
    skip_keywords = ["don't know", "skip", "next", "не знаю", "пропусти", "дальше"]
    user_wants_to_skip = any(word in user_answer.lower() for word in skip_keywords)

    if user_wants_to_skip or st.session_state.is_follow_up:
        st.session_state.is_follow_up = False
        if st.session_state.question_pool:
            next_q = st.session_state.question_pool.pop(0)
            return next_q["text"]
        return None 

    check_prompt = f"Question: {st.session_state.current_question}. Answer: {user_answer}. If the answer is too short or vague, ask ONE brief follow-up question. Otherwise, reply 'ENOUGH'."
    decision = generate_ai_response(check_prompt, system_prompt="You are a professional recruiter.")
    
    if "ENOUGH" not in decision.upper() and len(user_answer) < 300:
        st.session_state.is_follow_up = True
        return decision

    if st.session_state.question_pool:
        next_q = st.session_state.question_pool.pop(0)
        return next_q["text"]
    
    return None


if st.sidebar.button("← Back to Home"):
    st.switch_page("app.py")

st.title("interview prep")

if st.session_state.interview_stage == "setup":
    st.info(f"Ready to start the session, **{st.session_state.user_name}**? We will discuss your background and technical skills for the **{st.session_state.job_title}** role.")
    if st.button("start interview"):
        with st.spinner("Initializing AI Interviewer..."):
            prepare_db_pool()
            st.session_state.start_time = datetime.now()
            st.session_state.interview_stage = "active"
            
            welcome_msg = f"Hello {st.session_state.user_name}! I'm your AI Interviewer. We'll spend the next 10-15 minutes discussing your experience. Let's start!"
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            
            first_q = st.session_state.question_pool.pop(0)
            st.session_state.current_question = first_q["text"]
            st.session_state.messages.append({"role": "assistant", "content": first_q["text"]})
            st.rerun()

if st.session_state.interview_stage == "active":
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_answer := st.chat_input("Your answer..."):
        st.session_state.messages.append({"role": "user", "content": user_answer})
        
        with st.spinner("Analyzing..."):
            eval_prompt = f"Rate (Good/Fair/Poor). Q: {st.session_state.current_question}. A: {user_answer}. JSON: {{'rating': '...', 'red_flags': []}}"
            eval_resp = generate_ai_response(eval_prompt)
            try:
                eval_data = json.loads(re.search(r'\{.*\}', eval_resp, re.DOTALL).group(0))
            except:
                eval_data = {"rating": "Fair", "red_flags": []}

            st.session_state.interview_data.append({
                "q": st.session_state.current_question,
                "a": user_answer,
                "eval": eval_data
            })

            if any(w in user_answer.lower() for w in ["finish", "завершить", "stop"]):
                st.session_state.interview_stage = "finished"
                st.rerun()

            next_step = get_next_step(user_answer)
            
            if next_step:
                st.session_state.current_question = next_step
                st.session_state.messages.append({"role": "assistant", "content": next_step})
                st.rerun()
            else:
                st.session_state.interview_stage = "finished"
                st.rerun()

if st.session_state.interview_stage == "finished":
    st.divider()
    st.header("your results")
    
    data = st.session_state.interview_data
    total_q = len(data)
    
    good_ans = sum(1 for d in data if d['eval'].get('rating') == "Good")
    perf_score = int((good_ans / total_q) * 100) if total_q > 0 else 0
    duration = (datetime.now() - st.session_state.start_time).seconds // 60
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Questions Answered", total_q)
    col2.metric("Performance Score", f"{perf_score}%")
    col3.metric("Duration", f"{duration} min")

    if perf_score >= 85:
        st.success(" **Red Flags Audit:** No critical red flags detected. You demonstrated excellent communication and technical maturity.")
    else:
        all_flags = [f for d in data for f in d['eval'].get('red_flags', [])]
        if all_flags:
            st.error(f"**detected red flags:** {', '.join(set(all_flags))}")
        else:
            st.warning("No major red flags detected, but consider providing more detailed examples in your answers.")

    with st.spinner("Generating expert feedback..."):
        summary_prompt = f"""
        Act as a Lead Recruiter. Review this interview data for a {st.session_state.job_title}:
        {data}
        
        Provide:
        1. Key strengths shown.
        2. Technical or behavioral gaps.
        3. Final Verdict: Ready for real interview / Needs more practice.
        """
        summary = generate_ai_response(summary_prompt)
        st.markdown("### expert feedback")
        st.markdown(summary)

    if st.button("start new interview"):
        st.session_state.interview_stage = "setup"
        st.session_state.messages = []
        st.session_state.interview_data = []
        st.rerun()