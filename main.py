import openai
import streamlit as st
import json
from openai import OpenAI
from datetime import datetime
from pymongo import MongoClient
import re
import os
import certifi
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

# Page setup
st.set_page_config(page_title="Stevens OptiLearn", layout="wide", initial_sidebar_state="collapsed")

# Handle OpenAI key for local vs cloud
if os.path.exists('.streamlit/secrets.toml'):
    OPENAI_KEY = st.secrets["openai"]["api_key"]
else:
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_KEY:
        OPENAI_KEY = "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"
    if not OPENAI_KEY:
        st.error("OpenAI API key not found")
        st.stop()

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_KEY)
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = OPENAI_KEY

# Enhanced CSS Styling with Stevens Institute of Technology branding
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&family=Roboto+Slab:wght@300;400;500;700&display=swap');

/* Disable all transitions and animations to remove fade effects */
*, *::before, *::after {
    transition: none !important;
    animation: none !important;
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
}
/* Additional CSS for Course Type Badges */
.technical-badge {
    background: rgba(0, 123, 255, 0.2) !important;
    border-color: rgba(0, 123, 255, 0.3) !important;
    color: #007bff !important;
}

.business-badge {
    background: rgba(40, 167, 69, 0.2) !important;
    border-color: rgba(40, 167, 69, 0.3) !important;
    color: #28a745 !important;
}

.mixed-badge {
    background: rgba(108, 117, 125, 0.2) !important;
    border-color: rgba(108, 117, 125, 0.3) !important;
    color: #6c757d !important;
}

/* Enhanced Grid Layout for Courses */
@media (max-width: 1200px) {
    .similarity-section-pro {
        grid-template-columns: 1fr !important;
        gap: 1rem !important;
    }
}

@media (max-width: 768px) {
    .recommendations-summary h2 {
        font-size: 2rem !important;
    }
    
    .recommendations-summary h3 {
        font-size: 1.2rem !important;
    }
    
    .summary-grid {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    
    .course-name-pro {
        font-size: 1.3rem !important;
    }
}

/* Improved Certificate Section */
.cert-requirements h5 {
    font-family: 'Roboto Slab', serif !important;
    font-weight: 600 !important;
}

.cert-requirements ul li {
    color: #495057 !important;
    line-height: 1.5 !important;
}
/* Prevent Streamlit's default fade effects */
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > div,
.main,
.main > div {
    transition: none !important;
    animation: none !important;
}

/* Override any Streamlit internal transitions */
.element-container,
.stMarkdown,
.stText,
.stTextInput,
.stSelectbox,
.stSlider,
.stTextArea {
    transition: none !important;
}

/* Remove rerun fade effects */
[data-testid="stApp"] {
    transition: none !important;
}

/* Compact tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    justify-content: flex-start;
}

.stTabs [data-baseweb="tab"] {
    height: 40px;
    white-space: nowrap;
    background-color: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    padding: 0 16px;
    min-width: auto;
    width: auto;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #800020 0%, #a61e42 100%);
    color: white;
}

/* Academic Footer */
.academic-footer {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    color: white;
    text-align: center;
    padding: 3rem 2rem;
    margin-top: 4rem;
}

.footer-content {
    max-width: 1200px;
    margin: 0 auto;
}

.footer-title {
    font-family: 'Crimson Text', serif;
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #d4af37;
}

.footer-details {
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 1.5rem;
    color: rgba(255, 255, 255, 0.9);
}

.footer-meta {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 1.5rem;
}

/* Disable any opacity transitions */
.stSpinner > div {
    transition: none !important;
}

button, button * {
  color: white !important;
}

button {
  background: linear-gradient(135deg, #8B1538 0%, #A91B47 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 0.75rem 1.5rem !important;
  font-weight: 600 !important;
  transition: none !important;
  box-shadow: 0 2px 8px rgba(139, 21, 56, 0.2) !important;
}

button:hover {
  background: linear-gradient(135deg, #A91B47 0%, #8B1538 100%) !important;
  transform: none !important;
  box-shadow: 0 4px 15px rgba(139, 21, 56, 0.4) !important;
}

.stButton > button:active {
    transform: none !important;
}

html, body, [class*="css"] { 
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
    color: #212529;
    line-height: 1.6;
}

/* Slider marks styling */
.rc-slider-mark-text {
  background: linear-gradient(135deg, #8B1538 0%, #A91B47 100%) !important;
  color: white !important;
  padding: 0.25rem 0.5rem !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  transform: translateY(-50%) !important;
}

.rc-slider-mark-text-active {
  background: linear-gradient(135deg, #A91B47 0%, #8B1538 100%) !important;
  color: white !important;
}

.main .block-container { 
    padding: 1rem !important; 
    max-width: none !important; 
    margin: 0 !important; 
}

/* Header Section - Stevens Branding */
.header-section { 
    background: linear-gradient(135deg,#800020 0%, #a61e42 100%); 
    padding: 3.5rem 2rem;
    text-align: center;
    color: white;
    margin: 0;
    border-radius: 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    position: relative;
    overflow: hidden;
}

.header-section::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 60%;
    height: 200%;
    background: rgba(255, 255, 255, 0.05);
    transform: rotate(45deg);
}

.header-title { font-family: 'Crimson Text', serif; font-size: 3rem; font-weight: 700; margin: 0; color: white; }
.header-subtitle { font-size: 1.1rem; font-weight: 300; margin-top: 0.5rem; opacity: 0.95; color: white;}

/* Form Wrapper */
.form-wrapper { 
    max-width: 1000px;
    margin: 2rem auto;
    padding: 3rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(0, 0, 0, 0.05);
    position: relative;
}

.form-wrapper::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #C8102E 0%, #F7941E 50%, #C8102E 100%);
    border-radius: 12px 12px 0 0;
}

.section-title { 
    font-family: 'Roboto Slab', serif;
    font-size: 2rem;
    font-weight: 600;
    color: #800020;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 3px solid #f0f0f0;
    position: relative;
}

.section-title::after {
    content: '';
    position: absolute;
    bottom: -3px;
    left: 0;
    width: 60px;
    height: 3px;
    background: #C8102E;
}

/* AI Chat Container */
.ai-chat-container { 
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    margin: 2rem auto;
    max-width: 1000px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
    border: 1px solid #e9ecef;
}

.ai-message { 
    background: #f8f9fa;
    padding: 1.75rem;
    border-radius: 12px;
    border-left: 4px solid #C8102E;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
    position: relative;
    transition: none !important;
}

.ai-message:hover {
    transform: none !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

/* User Message */
.user-message { 
    background: linear-gradient(135deg, #C8102E 0%, #9B0E23 100%);
    color: white;
    padding: 1.25rem 1.75rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    margin-left: 3rem;
    box-shadow: 0 4px 16px rgba(200, 16, 46, 0.2);
    position: relative;
}

.ai-label { 
    font-size: 0.95rem;
    font-weight: 600;
    color: #C8102E;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ai-label::before { 
    content: "🎓";
    font-size: 1.4rem;
}

/* Ratio Display */
.ratio-display { 
    display: flex;
    justify-content: space-around;
    margin: 3rem 0;
    gap: 2rem;
}

.ratio-item { 
    flex: 1;
    text-align: center;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    border: 2px solid #e9ecef;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    transition: none !important;
    position: relative;
    overflow: hidden;
}

.ratio-item:hover {
    transform: none !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
    border-color: #C8102E;
}

.ratio-value { 
    font-size: 3rem;
    font-weight: 700;
    color: #C8102E;
    font-family: 'Roboto Slab', serif;
}

.ratio-label { 
    font-size: 1.1rem;
    font-weight: 500;
    color: #495057;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Progress Indicator */
.progress-indicator { 
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin: 2rem auto;
    padding: 1.5rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    max-width: 1000px;
    flex-wrap: wrap;
}

.progress-step { 
    padding: 0.75rem 1.5rem;
    background: #e9ecef;
    border-radius: 25px;
    font-size: 0.95rem;
    font-weight: 500;
    color: #6c757d;
    transition: none !important;
    border: 2px solid transparent;
}

.progress-step.active { 
    background: linear-gradient(135deg,#800020 0%, #a61e42 100%); 
    color: white;
    transform: none !important;
    box-shadow: 0 4px 16px rgba(200, 16, 46, 0.3);
}

.progress-step.completed { 
    background: #28a745;
    color: white;
    border-color: #28a745;
}

/* Professional Course Card */
.professional-course-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 6px 30px rgba(0,0,0,0.08);
    border: 1px solid #e9ecef;
    overflow: hidden;
    transition: none !important;
    position: relative;
    margin-bottom: 2rem;
}

.professional-course-card:hover {
    transform: none !important;
    box-shadow: 0 12px 50px rgba(200, 16, 46, 0.15);
    border-color: #C8102E;
}

.professional-course-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, #C8102E 0%, #F7941E 50%, #C8102E 100%);
}

.course-header-pro {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    color: white;
    padding: 2.5rem 2rem;
    position: relative;
}

.course-rank-pro {
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
    background: linear-gradient(135deg, #C8102E 0%, #9B0E23 100%);
    color: white;
    padding: 0.5rem 1.25rem;
    border-radius: 25px;
    font-size: 0.95rem;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(200, 16, 46, 0.4);
}

.course-code-pro {
    font-size: 1rem;
    opacity: 0.85;
    margin-bottom: 0.5rem;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.course-name-pro {
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.3;
    margin: 0;
    font-family: 'Roboto Slab', serif;
    color: white;
}

.course-type-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 1rem;
    border: 1px solid rgba(255,255,255,0.3);
}

.certificate-badge {
    background: rgba(212, 175, 55, 0.2);
    border-color: rgba(212, 175, 55, 0.3);
}

.course-body-pro {
    padding: 2.5rem;
}

.similarity-section-pro {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.similarity-metric {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #e9ecef;
    position: relative;
    transition: none !important;
}

.similarity-metric:hover {
    background: #fff;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.similarity-metric::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #C8102E 0%, #F7941E 100%);
    border-radius: 12px 12px 0 0;
}

.similarity-value-pro {
    font-size: 2rem;
    font-weight: 800;
    color: #C8102E;
    margin-bottom: 0.25rem;
    font-family: 'Roboto Slab', serif;
}

.similarity-label-pro {
    font-size: 0.9rem;
    color: #6c757d;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.course-description-pro {
    background: #f8f9fa;
    padding: 1.75rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    font-size: 1rem;
    color: #495057;
    line-height: 1.7;
    border-left: 4px solid #C8102E;
}

.cert-requirements {
    margin-top: 1rem;
    padding: 1rem;
    background: #fff5f5;
    border-radius: 8px;
    border: 1px solid #ffdddd;
}

.cert-requirements ul {
    margin: 0.5rem 0 0 0;
    padding-left: 1.5rem;
}

.cert-requirements li {
    margin-bottom: 0.25rem;
    font-size: 0.9rem;
}

/* Recommendations Summary */
.recommendations-summary {
    background: linear-gradient(135deg,#800020 0%, #a61e42 100%); 
    color: white;
    padding: 3rem;
    border-radius: 16px;
    margin: 3rem auto;
    box-shadow: 0 12px 50px rgba(0,0,0,0.15);
    max-width: 1200px;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.summary-metric {
    text-align: center;
    padding: 1.5rem;
    background: #808080;
    border-radius: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.15);
    transition: none !important;
}

.summary-metric:hover {
    background: #808080;
    transform: none !important;
}

.summary-metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.5rem;
    font-family: 'Roboto Slab', serif;
}

.summary-metric-label {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.9);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}

/* Email Error */
.email-error {
    color: #dc3545;
    font-size: 0.9rem;
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}


/* Buttons */
.stButton > button { 
    background: linear-gradient(135deg,#800020 0%, #a61e42 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.875rem 2.5rem !important;
    border: none !important;
    border-radius: 30px !important;
    transition: none !important;
    font-size: 1rem !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 16px rgba(200, 16, 46, 0.2) !important;
}

.stButton > button:hover { 
    background: linear-gradient(135deg,#800020 0%, #a61e42 100%) !important;
    transform: none !important;
    box-shadow: 0 6px 24px rgba(200, 16, 46, 0.3) !important;
    color: white;
}

.stButton > button:disabled {
  color: white !important;
  opacity: 1 !important;
}

/* Input Fields */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    border: 2px solid #e9ecef !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    font-size: 1rem !important;
    transition: none !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #C8102E !important;
    box-shadow: 0 0 0 0.2rem rgba(200, 16, 46, 0.15) !important;
}

/* Slider */
.stSlider > div > div > div {
    background: #C8102E !important;
}

.stSlider > div > div > div > div {
    background: #C8102E !important;
    box-shadow: 0 2px 8px rgba(200, 16, 46, 0.3) !important;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;} 
header {visibility: hidden;}
.stDeployButton {display: none;}

/* No Results State */
.no-results {
    text-align: center;
    padding: 3rem;
    background: #fff5f5;
    border-radius: 16px;
    border: 2px solid #ffdddd;
    margin: 2rem auto;
    max-width: 600px;
}

.no-results h3 {
    color: #C8102E;
    font-family: 'Roboto Slab', serif;
    margin-bottom: 1rem;
}

.no-results p {
    color: #666;
    line-height: 1.6;
}

.stApp {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) fixed no-repeat !important;
  background-attachment: fixed !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .header-title { font-size: 2.5rem; }
    .header-subtitle { font-size: 1rem; }
    .form-wrapper { padding: 2rem 1.5rem; }
    .section-title { font-size: 1.6rem; }
    .progress-indicator { gap: 0.5rem; }
    .progress-step { padding: 0.5rem 1rem; font-size: 0.85rem; }
    .ratio-display { flex-direction: column; gap: 1rem; }
    .similarity-section-pro { grid-template-columns: 1fr; }
    .summary-grid { grid-template-columns: repeat(2, 1fr); gap: 1rem; }
}

/* Professional Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Roboto Slab', serif;
    color: #212529;
}

p {
    line-height: 1.8;
    color: #495057;
}
            
            /* Smaller Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    justify-content: flex-start !important;
    margin-bottom: 1rem !important;
}

.stTabs [data-baseweb="tab"] {
    height: 32px !important;
    white-space: nowrap !important;
    background-color: #f8f9fa !important;
    border-radius: 6px !important;
    border: 1px solid #e9ecef !important;
    padding: 0 12px !important;
    min-width: auto !important;
    width: auto !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #800020 0%, #a61e42 100%) !important;
    color: white !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: #e9ecef !important;
}

.stTabs [aria-selected="true"]:hover {
    background: linear-gradient(135deg, #a61e42 0%, #800020 100%) !important;
}

/* Additional CSS for Course Type Badges */
.technical-badge {
    background: rgba(0, 123, 255, 0.2) !important;
    border-color: rgba(0, 123, 255, 0.3) !important;
    color: #007bff !important;
}

.business-badge {
    background: rgba(40, 167, 69, 0.2) !important;
    border-color: rgba(40, 167, 69, 0.3) !important;
    color: #28a745 !important;
}

.mixed-badge {
    background: rgba(108, 117, 125, 0.2) !important;
    border-color: rgba(108, 117, 125, 0.3) !important;
    color: #6c757d !important;
}

/* Enhanced Grid Layout for Courses */
@media (max-width: 1200px) {
    .similarity-section-pro {
        grid-template-columns: 1fr !important;
        gap: 1rem !important;
    }
}

@media (max-width: 768px) {
    .recommendations-summary h2 {
        font-size: 2rem !important;
    }
    
    .recommendations-summary h3 {
        font-size: 1.2rem !important;
    }
    
    .summary-grid {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    
    .course-name-pro {
        font-size: 1.3rem !important;
    }
}

/* Improved Certificate Section */
.cert-requirements h5 {
    font-family: 'Roboto Slab', serif !important;
    font-weight: 600 !important;
}

.cert-requirements ul li {
    color: #495057 !important;
    line-height: 1.5 !important;
}

</style>
""", unsafe_allow_html=True)

# Initialize session state
session_defaults = {
    'logged_in': False, 'current_step': 1, 'form_data': {}, 'initial_req': None,
    'conversation_history': [], 'question_count': 0, 'requirements_data': {},
    'ai_analysis': {}, 'course_recommendations': [], 'grad_certificate_recommendations': [],
    'current_ai_question': None
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

USER_CREDENTIALS = {"stevens_org": "admin", "admin": "admin"}

# Utility Functions
def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def next_step(): 
    st.session_state.current_step += 1

def prev_step(): 
    st.session_state.current_step -= 1

def convert_similarity_to_percentage(similarity_score):
    return int(max(0, similarity_score) * 100)

# Database Connection
URI = "mongodb+srv://codermishyt:tQk0U81QVvktb5s4@optilearn.vu626pu.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(URI, tls=True, tlsCAFile=certifi.where())
db = client.optilearn
collection = db.company

# Data Loading Functions
def load_embeddings_data(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "embeddings" in data:
            raw = data["embeddings"]
        elif isinstance(data, list):
            raw = data
        else:
            st.error(f"Unexpected format: top‐level is {type(data)}")
            return []

        items = []
        for entry in raw:
            if isinstance(entry, dict):
                items.append(entry)
        return items

    except FileNotFoundError:
        st.error(f"Embeddings file not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Error parsing embeddings file: {e}")
        return []
    except Exception as e:
        st.error(f"Error loading embeddings: {str(e)}")
        return []

def load_grad_cert_embeddings(filename='grad_cert_embedding.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        course_embeddings = data.get('course_embeddings', [])
        grad_certs = []
        
        for item in course_embeddings:
            course_name = item.get('course_name', '').lower()
            if 'certificate' in course_name:
                embeddings = item.get('embeddings', {})
                name_emb = embeddings.get('course_name_embedding', [])
                desc_emb = embeddings.get('course_description_embedding', [])
                req_emb = embeddings.get('course_requirements_embedding', [])
                
                if name_emb and desc_emb and req_emb:
                    combined_embedding = np.mean([name_emb, desc_emb, req_emb], axis=0).tolist()
                    
                    grad_certs.append({
                        'index': item.get('index'),
                        'course_name': item.get('course_name'),
                        'course_description': item.get('course_description'),
                        'course_requirements': item.get('course_requirements'),
                        'vector': combined_embedding,
                        'individual_embeddings': embeddings
                    })
        
        return grad_certs
        
    except FileNotFoundError:
        st.error(f"File {filename} not found!")
        return []
    except Exception as e:
        st.error(f"Error loading graduate certificate embeddings: {e}")
        return []

# AI and Embedding Functions
def get_text_embedding(text, client, model="text-embedding-3-small"):
    try:
        cleaned_text = ' '.join(text.split())
        response = client.embeddings.create(model=model, input=cleaned_text)
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Error generating embedding: {str(e)}")
        return None

def calculate_similarity_with_requirements(user_embedding, course_embedding):
    try:
        if not user_embedding or not course_embedding:
            return 0.0
        
        user_vec = np.array(user_embedding).reshape(1, -1)
        course_vec = np.array(course_embedding).reshape(1, -1)
        similarity = cosine_similarity(user_vec, course_vec)[0][0]
        return float(similarity)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

def calculate_cosine_similarity(embedding1, embedding2):
    try:
        emb1 = np.array(embedding1).reshape(1, -1)
        emb2 = np.array(embedding2).reshape(1, -1)
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return similarity
    except Exception as e:
        st.error(f"Error calculating cosine similarity: {e}")
        return 0.0

def generate_smart_question(requirements_data, conversation_history, question_count, current_tech_business_ratio=None):
    try:
        if st.session_state.openai_api_key:
            client = OpenAI(api_key=st.session_state.openai_api_key)
            context = f"Initial Requirements: {st.session_state.initial_req}\n\n"
            
            if current_tech_business_ratio is not None:
                context += f"Current Tech/Business Ratio: {current_tech_business_ratio} "
                context += f"({'Technical focus' if current_tech_business_ratio > 0.6 else 'Business focus' if current_tech_business_ratio < 0.4 else 'Balanced'})\n\n"
            
            if conversation_history:
                context += "Previous conversation:\n"
                for msg in conversation_history[-4:]:
                    if msg['type'] == 'user':
                        context += f"User response: {msg['content']}\n"
            
            prompt = f"""You are a corporate training consultant. Based on the conversation, generate ONE specific follow-up question to understand training needs better.

Focus on areas like:
- Technical vs business skill balance
- Specific skill gaps
- Training objectives
- Timeline and constraints
- Success metrics
- Team composition

{context}

Generate only the question:"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100, temperature=0.7
            )
            return response.choices[0].message.content.strip()
        else:
            raise Exception("No API key")
    except:
        fallback_questions = [
            "What's the ideal balance between technical and business skills for your team?",
            "What specific technical or business challenges are you facing?",
            "How would you measure the success of this training program?",
            "What's your timeline for implementing this training?",
            "Which skills would have the most immediate impact on your team's performance?",
            "Are there any specific tools or technologies your team needs to learn?"
        ]
        return fallback_questions[min(question_count, len(fallback_questions)-1)]

def extract_key_insights(text):
    insights = {'industry_focus': [], 'training_type': [], 'participant_count': '', 'timeline': '', 'delivery_method': [], 'objectives': []}
    text_lower = text.lower()
    
    for industry in ['technology', 'healthcare', 'finance', 'manufacturing', 'education', 'retail']:
        if industry in text_lower: insights['industry_focus'].append(industry)
    
    for t_type in ['leadership', 'technical', 'compliance', 'soft skills', 'project management']:
        if t_type.replace(' ', '') in text_lower.replace(' ', ''): insights['training_type'].append(t_type)
    
    numbers = re.findall(r'\d+', text)
    if numbers: insights['participant_count'] = numbers[0]
    
    return insights

def update_requirements_data(requirements_data, new_insights):
    for key, value in new_insights.items():
        if isinstance(value, list):
            if key not in requirements_data: requirements_data[key] = []
            requirements_data[key].extend(value)
            requirements_data[key] = list(set(requirements_data[key]))
        elif value and value.strip():
            requirements_data[key] = value
    return requirements_data

# Classification Functions
def classify_course_type(course_data):
    technical_keywords = [
        'programming', 'algorithm', 'data structure', 'machine learning', 'ai', 'artificial intelligence',
        'database', 'software', 'computer', 'coding', 'python', 'java', 'javascript', 'web development',
        'cybersecurity', 'network', 'cloud', 'devops', 'api', 'backend', 'frontend', 'mobile app',
        'data science', 'analytics', 'statistics', 'mathematical', 'engineering', 'technical',
        'system design', 'architecture', 'framework', 'library', 'debugging', 'testing'
    ]
    
    business_keywords = [
        'management', 'leadership', 'strategy', 'marketing', 'finance', 'accounting', 'business',
        'entrepreneurship', 'operations', 'project management', 'communication', 'negotiation',
        'sales', 'customer', 'organization', 'team building', 'hr', 'human resources',
        'economics', 'consulting', 'planning', 'decision making', 'process improvement',
        'change management', 'innovation', 'corporate', 'executive', 'administration'
    ]
    
    content = f"{course_data.get('course_name', '')} {course_data.get('course_description', '')} {course_data.get('embedding_text', '')}"
    content = content.lower()
    
    tech_count = sum(1 for keyword in technical_keywords if keyword in content)
    business_count = sum(1 for keyword in business_keywords if keyword in content)
    
    if tech_count > business_count * 1.5:
        return 'technical'
    elif business_count > tech_count * 1.5:
        return 'business'
    else:
        return 'mixed'

def filter_by_tech_business_ratio(courses, tech_ratio):
    filtered_courses = []
    
    for course in courses:
        course_type = classify_course_type(course)
        
        if tech_ratio >= 70:  # Heavy technical focus
            if course_type == 'technical':
                course['type_match_score'] = 1.0
            elif course_type == 'mixed':
                course['type_match_score'] = 0.7
            else:  # business
                course['type_match_score'] = 0.3
        elif tech_ratio <= 30:  # Heavy business focus
            if course_type == 'business':
                course['type_match_score'] = 1.0
            elif course_type == 'mixed':
                course['type_match_score'] = 0.7
            else:  # technical
                course['type_match_score'] = 0.3
        else:  # Balanced approach (30-70%)
            if course_type == 'mixed':
                course['type_match_score'] = 1.0
            else:
                course['type_match_score'] = 0.8
        
        course['adjusted_similarity'] = course['similarity_score'] * course['type_match_score']
        course['course_type'] = course_type
        filtered_courses.append(course)
    
    return filtered_courses

def filter_certificates_by_ratio(cert_sims, tech_ratio):
    for cert in cert_sims:
        cert['adjusted_similarity'] = cert['similarity_score']
        cert['course_type'] = 'mixed'  # Default to mixed for certificates
    return cert_sims

# Recommendation Generation Functions
def generate_course_recommendations(user_requirements_text):
    try:
        embeddings_data = load_embeddings_data('all_course_embeddings.json')
        if not embeddings_data:
            st.error("No course embeddings data found!")
            return []

        if not st.session_state.openai_api_key:
            st.error("OpenAI API key not found!")
            return []
        client = OpenAI(api_key=st.session_state.openai_api_key)

        user_embedding = get_text_embedding(user_requirements_text, client)
        if not user_embedding:
            st.error("Failed to generate embedding for user requirements!")
            return []

        module_sims = []
        for course_data in embeddings_data:
            vector = course_data.get('vector')
            if not vector:
                continue
            sim = calculate_similarity_with_requirements(user_embedding, vector)
            if sim >= 0.2:
                module_sims.append({
                    'course_code': course_data.get('course_code', 'N/A'),
                    'course_name': course_data.get('course_name', 'N/A'),
                    'description': course_data.get('course_description', ''),
                    'similarity_score': sim,
                    'best_week': course_data.get('module_display_name', 'overview'),
                    'module_title': ', '.join(course_data.get('topics', [])),
                    'learning_outcomes': course_data.get('learning_outcomes', []),
                    'raw_data': course_data
                })

        # Dedupe by course_code—keep only the module with max similarity
        best_per_course = {}
        for info in module_sims:
            code = info['course_code']
            if code not in best_per_course or info['similarity_score'] > best_per_course[code]['similarity_score']:
                best_per_course[code] = info
        course_similarities = list(best_per_course.values())

        tech_ratio = st.session_state.form_data.get('tech_ratio', 50)
        filtered = filter_by_tech_business_ratio(course_similarities, tech_ratio)

        filtered.sort(key=lambda x: x['adjusted_similarity'], reverse=True)
        top_recs = filtered[:10]
        for idx, course in enumerate(top_recs, start=1):
            course['rank'] = idx

        st.write("📊 **Recommendation Stats:**")
        st.write(f"- Unique courses after dedupe: {len(course_similarities)}")
        st.write(f"- Final recommendations: {len(top_recs)}")
        st.write(f"- Tech/Business ratio: {tech_ratio}%/{100-tech_ratio}%")
        if top_recs:
            top = top_recs[0]
            pct = convert_similarity_to_percentage(top['adjusted_similarity'])
            st.write(f"- Top match: {top['course_name']} ({pct}%)")

        return top_recs

    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []
def save_all_recommendations(company_name, courses, certificates, user_requirements_text=None):
    """
    Write both `courses` and `certificates` into the company document.
    """
    try:
        company = collection.find_one({"company_name": company_name})
        if not company:
            st.error(f"Company '{company_name}' not found!")
            return False

        payload = {
            "course_recommendations": {
                "generated_at": datetime.utcnow(),
                "recommendations": courses,
                "total_courses": len(courses),
            },
            "certificate_recommendations": {
                "generated_at": datetime.utcnow(),
                "recommendations": certificates,
                "total_certificates": len(certificates),
            },
            "requirements_text": user_requirements_text or "",
            "last_updated": datetime.utcnow()
        }

        result = collection.update_one(
            {"company_name": company_name},
            {"$set": payload}
        )
        if result.modified_count:
            st.success(f"✅ Saved {len(courses)} courses & {len(certificates)} certificates for {company_name}")
            return True
        else:
            st.info("ℹ️ No changes detected in recommendations.")
            return True
    except Exception as e:
        st.error(f"❌ Error saving all recommendations: {e}")
        return False

def get_top_grad_certificates(user_requirements_text, top_k=3):
    try:
        grad_cert_embeddings = load_grad_cert_embeddings('grad_cert_embedding.json')
        if not grad_cert_embeddings:
            st.error("No graduate certificate embeddings data found!")
            return []

        # Use existing company requirements embeddings from session state
        user_embedding = None
        
        if hasattr(st.session_state, 'company_requirements_embedding') and st.session_state.company_requirements_embedding:
            user_embedding = st.session_state.company_requirements_embedding
        elif hasattr(st.session_state, 'user_requirements_embedding') and st.session_state.user_requirements_embedding:
            user_embedding = st.session_state.user_requirements_embedding
        else:
            if not st.session_state.openai_api_key:
                st.error("OpenAI API key not found and no cached embeddings available!")
                return []
            client = OpenAI(api_key=st.session_state.openai_api_key)
            user_embedding = get_text_embedding(user_requirements_text, client)
            
        if not user_embedding:
            st.error("Failed to get user requirements embedding!")
            return []

        cert_sims = []
        for cert_data in grad_cert_embeddings:
            vector = cert_data.get('vector')
            if not vector:
                continue
                
            sim = calculate_cosine_similarity(user_embedding, vector)
            
            if sim >= 0.2:
                cert_sims.append({
                    'course_name': cert_data.get('course_name', 'N/A'),
                    'course_description': cert_data.get('course_description', ''),
                    'course_requirements': cert_data.get('course_requirements', []),
                    'similarity_score': sim,
                    'raw_data': cert_data
                })

        tech_ratio = st.session_state.form_data.get('tech_ratio', 50)
        filtered_certs = filter_certificates_by_ratio(cert_sims, tech_ratio)

        filtered_certs.sort(key=lambda x: x.get('adjusted_similarity', x['similarity_score']), reverse=True)
        top_certs = filtered_certs[:top_k]
        
        for idx, cert in enumerate(top_certs, start=1):
            cert['rank'] = idx

        st.write("🎓 **Graduate Certificate Stats:**")
        st.write(f"- Total certificates in DB: {len(grad_cert_embeddings)}")
        st.write(f"- Certificates above threshold: {len(cert_sims)}")
        st.write(f"- Final certificate recommendations: {len(top_certs)}")
        if top_certs:
            top = top_certs[0]
            pct = convert_similarity_to_percentage(top.get('adjusted_similarity', top['similarity_score']))
            st.write(f"- Top certificate match: {top['course_name']} ({pct}%)")

        return top_certs

    except Exception as e:
        st.error(f"Error generating certificate recommendations: {e}")
        return []

# PDF Generation
def generate_pdf(recommendations, grad_certificates=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    story = []
    
    title = Paragraph("Course Recommendations Report", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    date_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    date_para = Paragraph(date_text, normal_style)
    story.append(date_para)
    story.append(Spacer(1, 0.2*inch))
    
    # Course recommendations
    if recommendations:
        course_header = Paragraph("Course Recommendations", heading_style)
        story.append(course_header)
        story.append(Spacer(1, 0.2*inch))
        
        for i, course in enumerate(recommendations, 1):
            code = course.get('course_code', 'N/A')
            name = course.get('course_name', 'Untitled Course')
            desc = course.get('description', 'No description available.')
            outcomes = course.get('learning_outcomes', []) or course.get('outcomes', [])
            
            similarity = course.get('adjusted_similarity', 0)
            try:
                sim_percentage = convert_similarity_to_percentage(similarity)
                sim_text = f"{sim_percentage}%"
            except:
                sim_text = "N/A"
            
            header_text = f"{i}. {code} - {name} (Match: {sim_text})"
            header_para = Paragraph(header_text, heading_style)
            story.append(header_para)
            story.append(Spacer(1, 0.1*inch))
            
            desc_text = f"<b>Description:</b> {desc}"
            desc_para = Paragraph(desc_text, normal_style)
            story.append(desc_para)
            story.append(Spacer(1, 0.1*inch))
            
            if outcomes and len(outcomes) > 0:
                outcomes_text = "<b>Learning Outcomes:</b><br/>"
                for outcome in outcomes:
                    outcome_clean = str(outcome).strip()
                    if outcome_clean:
                        outcomes_text += f"• {outcome_clean}<br/>"
                
                outcomes_para = Paragraph(outcomes_text, normal_style)
                story.append(outcomes_para)
            
            story.append(Spacer(1, 0.3*inch))
    
    # Graduate certificate recommendations
    if grad_certificates:
        cert_header = Paragraph("Graduate Certificate Recommendations", heading_style)
        story.append(cert_header)
        story.append(Spacer(1, 0.2*inch))
        
        for i, cert in enumerate(grad_certificates, 1):
            name = cert.get('course_name', 'Untitled Certificate')
            desc = cert.get('course_description', 'No description available.')
            
            similarity = cert.get('similarity_score', 0)
            try:
                sim_percentage = convert_similarity_to_percentage(similarity)
                sim_text = f"{sim_percentage}%"
            except:
                sim_text = "N/A"
            
            header_text = f"{i}. {name} (Match: {sim_text})"
            header_para = Paragraph(header_text, heading_style)
            story.append(header_para)
            story.append(Spacer(1, 0.1*inch))
            
            desc_text = f"<b>Description:</b> {desc}"
            desc_para = Paragraph(desc_text, normal_style)
            story.append(desc_para)
            story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Header
st.markdown("""
<div class="header-section">
    <h1 class="header-title">Stevens OptiLearn</h1>
    <p class="header-subtitle">Intelligent Corporate Training Solutions powered by Stevens Institute of Technology</p>
</div>
""", unsafe_allow_html=True)

# Login System
if not st.session_state.logged_in:
    st.markdown('<div class="form-wrapper"><div class="section-title" style="text-align: center;">Corporate Access Portal</div></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_id = st.text_input("User ID", placeholder="Enter your Stevens corporate ID")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login"):
            if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == password:
                st.session_state.logged_in = True
                st.session_state.current_step = 2
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
    st.stop()

# Progress Indicator
if st.session_state.logged_in:
    steps = ["Company Info", "Training Focus", "Requirements", "AI Consultation", "Recommendations"]
    progress_html = '<div class="progress-indicator">'
    for i, step in enumerate(steps, 2):
        status = "completed" if st.session_state.current_step > i else "active" if st.session_state.current_step == i else ""
        progress_html += f'<div class="progress-step {status}">{step}</div>'
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

# Step 2: Company Information
if st.session_state.logged_in and st.session_state.current_step == 2:
    st.markdown('<div class="form-wrapper"><div class="section-title">Company Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name *", value=st.session_state.form_data.get("company_name", ""))
        industry = st.selectbox("Industry *", ["", "Technology", "Finance", "Healthcare", "Manufacturing", "Retail", "Consulting", "Education", "Government", "Other"], 
                              index=["", "Technology", "Finance", "Healthcare", "Manufacturing", "Retail", "Consulting", "Education", "Government", "Other"].index(st.session_state.form_data.get("industry", "")))
    
    with col2:
        company_size = st.selectbox("Company Size *", ["", "1-50 employees", "51-200 employees", "201-1000 employees", "1001-5000 employees", "5000+ employees"],
                                  index=["", "1-50 employees", "51-200 employees", "201-1000 employees", "1001-5000 employees", "5000+ employees"].index(st.session_state.form_data.get("company_size", "")))
        contact_email = st.text_input("Contact Email *", value=st.session_state.form_data.get("contact_email", ""))
        
        if contact_email and not is_valid_email(contact_email):
            st.markdown('<div class="email-error">⚠️ Please enter a valid email address</div>', unsafe_allow_html=True)
    
    if st.button("Continue →"):
        if all([company_name, industry, company_size, contact_email]):
            if is_valid_email(contact_email):
                st.session_state.form_data.update({"company_name": company_name, "industry": industry, "company_size": company_size, "contact_email": contact_email})
                company={"company_name": company_name, "industry": industry, "company_size": company_size, "contact_email": contact_email}
                collection.insert_one(company)
                st.success("Company information saved successfully!")
                next_step()
                st.rerun()
            else:
                st.error("Please enter a valid email address.")
        else:
            st.error("Please fill in all required fields.")
    st.markdown('</div>', unsafe_allow_html=True)

# Step 3: Training Focus (Tech vs Business Ratio)
elif st.session_state.logged_in and st.session_state.current_step == 3:
    st.markdown('<div class="form-wrapper"><div class="section-title">Training Focus Areas</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; margin: 2rem 0;"><h3 style="font-family: \'Roboto Slab\', serif; color: #2c3e50;">Technical vs. Business Skills Distribution</h3></div>', unsafe_allow_html=True)
    
    tech_ratio = st.slider(
        "Technical Skills Percentage", 
        min_value=0, 
        max_value=100, 
        value=st.session_state.form_data.get("tech_ratio", 50),
        help="Slide to adjust the balance between technical and business skills",
        label_visibility="hidden"
    )
    business_ratio = 100 - tech_ratio
    
    st.markdown(f"""
    <div class="ratio-display">
        <div class="ratio-item">
            <div class="ratio-value">{business_ratio}%</div>
            <div class="ratio-label">Business Skills</div>
        </div>
        <div class="ratio-item">
            <div class="ratio-value">{tech_ratio}%</div>
            <div class="ratio-label">Technical Skills</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
   
    st.session_state.form_data.update({
        "tech_ratio": tech_ratio, 
        "business_ratio": business_ratio, 
    })
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="step3_back"): 
            prev_step()
            st.rerun()
    with col2:
        if st.button("Continue →", key="step3_continue"): 
            st.session_state.form_data.update({
                "tech_ratio": tech_ratio, 
                "business_ratio": business_ratio, 
            })
            next_step()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
# Step 4: Requirements Gathering
elif st.session_state.logged_in and st.session_state.current_step == 4:
    st.markdown('<div class="form-wrapper"><div class="section-title">Training Requirements</div>', unsafe_allow_html=True)
    
    if 'input_method' not in st.session_state:
        st.session_state.input_method = None
    
    st.markdown("**Choose your preferred input method:**")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Write Text Description", 
                    key="text_option", 
                    help="Describe your requirements in text",
                    use_container_width=True):
            st.session_state.input_method = 'text'
            st.rerun()
    
    with col2:
        if st.button("Upload Document", 
                    key="file_option", 
                    help="Upload PDF, DOC, or PPT file",
                    use_container_width=True):
            st.session_state.input_method = 'file'
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    requirements_text = ""
    
    if st.session_state.input_method == 'text':
        initial_req = st.text_area(
            "Describe your training requirements:", 
            height=200, 
            placeholder="Tell us about your training goals, target audience, specific skills needed, preferred delivery format, timeline, and desired outcomes...",
            value=st.session_state.get('initial_req', '') or ""
        )
        requirements_text = initial_req
    
    elif st.session_state.input_method == 'file':
        st.markdown("### 📄 Document Upload")
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'],
            help="Supported formats: PDF, DOC, DOCX, PPT, PPTX, TXT"
        )
        
        if uploaded_file is not None:
            try:
                with st.spinner("📖 Extracting text from your document..."):
                    if uploaded_file.type == "application/pdf":
                        try:
                            import PyPDF2
                            pdf_reader = PyPDF2.PdfReader(uploaded_file)
                            text_content = ""
                            for page in pdf_reader.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text_content += page_text + "\n"
                            requirements_text = text_content.strip()
                            
                            if not requirements_text:
                                st.error("❌ Could not extract text from PDF.")
                                
                        except Exception as e:
                            st.error(f"❌ Error processing PDF: {str(e)}")
                            requirements_text = ""
                    
                    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                              "application/msword"]:
                        try:
                            import docx
                            doc = docx.Document(uploaded_file)
                            text_content = ""
                            for paragraph in doc.paragraphs:
                                text_content += paragraph.text + "\n"
                            requirements_text = text_content.strip()
                        except ImportError:
                            st.error("python-docx library not available.")
                            requirements_text = ""
                    
                    elif uploaded_file.type == "text/plain":
                        requirements_text = str(uploaded_file.read(), "utf-8")
                    
                    else:
                        st.error("Unsupported file type.")
                        requirements_text = ""
                
                if requirements_text:
                    st.success(f"✅ Successfully extracted text from {uploaded_file.name}")
                    
                    with st.expander("📋 Preview Extracted Content", expanded=False):
                        preview_text = requirements_text[:1000] + ("..." if len(requirements_text) > 1000 else "")
                        st.text_area("Extracted Text:", value=preview_text, height=150, disabled=True)
                        if len(requirements_text) > 1000:
                            st.info(f"Showing first 1000 characters of {len(requirements_text)} total characters")
                    
                    st.markdown("**Review and edit the extracted text if needed:**")
                    requirements_text = st.text_area("Edit requirements:", value=requirements_text, height=150)
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
        
        else:
            st.info("Please upload a document containing your training requirements")
    
    else:
        st.info("Please select an input method above to get started")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back", use_container_width=True): 
            prev_step()
            st.rerun()
    
    with col3:
        if st.button("Start AI Consultation", use_container_width=True):
            if requirements_text and requirements_text.strip():
                st.session_state.initial_req = requirements_text
                
                if 'conversation_history' not in st.session_state:
                    st.session_state.conversation_history = []
                
                st.session_state.conversation_history.append({
                    "type": "user", 
                    "content": requirements_text, 
                    "timestamp": datetime.now().isoformat()
                })
                
                try:
                    initial_insights = extract_key_insights(requirements_text)
                    if 'requirements_data' not in st.session_state:
                        st.session_state.requirements_data = {}
                    st.session_state.requirements_data = update_requirements_data(
                        st.session_state.requirements_data, 
                        initial_insights
                    )
                    
                    if 'question_count' not in st.session_state:
                        st.session_state.question_count = 0
                        
                    st.session_state.current_ai_question = generate_smart_question(
                        st.session_state.requirements_data, 
                        st.session_state.conversation_history, 
                        st.session_state.question_count
                    )
                    
                    next_step()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing requirements: {str(e)}")
            else:
                if st.session_state.input_method == 'text':
                    st.error("Please provide your training requirements in the text area above.")
                elif st.session_state.input_method == 'file':
                    st.error("Please upload a document or switch to text input.")
                else:
                    st.error("Please select an input method and provide your requirements.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Step 5: AI Consultation
elif st.session_state.logged_in and st.session_state.current_step == 5:
    st.markdown('<div class="ai-chat-container"><div class="section-title" style="margin: 0 0 2rem 0; text-align: center;">AI Training Consultant</div>', unsafe_allow_html=True)
    
    if st.session_state.question_count < 7:
        if st.session_state.current_ai_question:
            st.markdown(f'<div class="ai-message"><div class="ai-label">Stevens AI Consultant</div>{st.session_state.current_ai_question}</div>', unsafe_allow_html=True)
        
        user_response = st.text_area("Your response:", height=80, placeholder="Please share your thoughts...", key=f"response_{st.session_state.question_count}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Submit Response"):
                if user_response.strip():
                    st.session_state.conversation_history.append({"type": "user", "content": user_response, "timestamp": datetime.now().isoformat()})
                    insights = extract_key_insights(user_response)
                    st.session_state.requirements_data = update_requirements_data(st.session_state.requirements_data, insights)
                    st.session_state.question_count += 1
                    if st.session_state.question_count < 7:
                        st.session_state.current_ai_question = generate_smart_question(st.session_state.requirements_data, st.session_state.conversation_history, st.session_state.question_count)
                    else:
                        st.session_state.current_ai_question = None
                    st.rerun()
        with col2:
            if st.button("Skip Question"): 
                st.session_state.conversation_history.append({"type": "user", "content": "[Question Skipped]", "timestamp": datetime.now().isoformat()})
                st.session_state.question_count += 1
                if st.session_state.question_count < 7:
                    st.session_state.current_ai_question = generate_smart_question(st.session_state.requirements_data, st.session_state.conversation_history, st.session_state.question_count)
                else:
                    st.session_state.current_ai_question = None
                st.rerun()
        with col3:
            if st.button("Finish Consultation"): 
                full_requirements = st.session_state.initial_req
                for msg in st.session_state.conversation_history:
                    if msg["type"] == "user" and msg["content"] != "[Question Skipped]":
                        full_requirements += " " + msg["content"]
                
                with st.spinner("🔍 Analyzing requirements and generating personalized recommendations..."):
                    st.session_state.course_recommendations = generate_course_recommendations(full_requirements)
                    st.session_state.grad_certificate_recommendations = get_top_grad_certificates(full_requirements, top_k=3)

                company_name = st.session_state.form_data.get("company_name")
                # save both lists into MongoDB
                save_all_recommendations(
                company_name,
                st.session_state.course_recommendations,
                st.session_state.grad_certificate_recommendations,
                full_requirements
)



                next_step()
                st.rerun()
    else:
        st.markdown('<div class="ai-message"><div class="ai-label">Stevens AI Consultant</div>Thank you for providing detailed information about your training needs. Let\'s generate your personalized course recommendations.</div>', unsafe_allow_html=True)
        if st.button("Generate Recommendations"): 
            full_requirements = st.session_state.initial_req
            for msg in st.session_state.conversation_history:
                if msg["type"] == "user" and msg["content"] != "[Question Skipped]":
                    full_requirements += " " + msg["content"]
            
            with st.spinner("🔍 Analyzing requirements and generating personalized recommendations..."):
                st.session_state.course_recommendations = generate_course_recommendations(full_requirements)
                st.session_state.grad_certificate_recommendations = get_top_grad_certificates(full_requirements, top_k=3)
            
            next_step()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


    
# Step 6: Display Recommendations - STREAMLIT NATIVE VERSION
elif st.session_state.logged_in and st.session_state.current_step == 6:
    st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
    
    # Header Section with Summary and Girl Image
    tech_ratio = st.session_state.form_data.get('tech_ratio', 50)
    business_ratio = 100 - tech_ratio
    
    st.markdown(f"""
    <div class="recommendations-summary">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
            <div style="flex: 1;">
                <h2 style="margin: 0 0 1rem 0; font-family: 'Roboto Slab', serif; font-size: 2.5rem; color: white;">
                    RECOMMENDED COURSES
                </h2>
                <h3 style="margin: 0; font-size: 1.5rem; opacity: 0.9; color: white;">
                    SUMMARY: TECHNICAL {tech_ratio}% VS BUSINESS RATIO {business_ratio}%
                </h3>
            </div>
            <div style="flex: 0 0 300px; text-align: right;">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDMwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIiBmaWxsPSJub25lIi8+CjxjaXJjbGUgY3g9IjE1MCIgY3k9IjEwMCIgcj0iNDAiIGZpbGw9IiNGRkRCQkYiLz4KPHBhdGggZD0iTTEzMCAxMDBDMTMwIDkwIDEzNSA4NSAxNDUgODVDMTU1IDg1IDE2MCA5MDE2MCA5MEMxNjUgOTAgMTcwIDk1IDE3MCA5NUM0NzAgMTA1IDE2NSAxMTAgMTU1IDExMEMxNDUgMTEwIDEzNSAxMDUgMTMwIDEwMFoiIGZpbGw9IiMyMzI5MkYiLz4KPGVsbGlwc2UgY3g9IjE0MCIgY3k9Ijk1IiByeD0iMyIgcnk9IjIiIGZpbGw9IiMzMzMiLz4KPGVsbGlwc2UgY3g9IjE2MCIgY3k9Ijk1IiByeD0iMyIgcnk9IjIiIGZpbGw9IiMzMzMiLz4KPHBhdGggZD0iTTE0NSAxMDVDMTQ1IDEwNSAxNDggMTA4IDE1MiAxMDUiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPHJlY3QgeD0iMTIwIiB5PSIxNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI4MCIgcng9IjEwIiBmaWxsPSJ3aGl0ZSIvPgo8Y2lyY2xlIGN4PSIxMDAiIGN5PSIxNjAiIHI9IjE1IiBmaWxsPSIjRkZEQkJGIi8+CjxjaXJjbGUgY3g9IjIwMCIgY3k9IjE2MCIgcj0iMTUiIGZpbGw9IiNGRkRCQkYiLz4KPHJlY3QgeD0iOTAiIHk9IjE3NSIgd2lkdGg9IjIwIiBoZWlnaHQ9IjQ1IiByeD0iMTAiIGZpbGw9IndoaXRlIi8+CjxyZWN0IHg9IjE5MCIgeT0iMTc1IiB3aWR0aD0iMjAiIGhlaWdodD0iNDUiIHJ4PSIxMCIgZmlsbD0id2hpdGUiLz4KPHJlY3QgeD0iMTEwIiB5PSIyMjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIzMCIgcng9IjEwIiBmaWxsPSIjRkZEQkJGIi8+CjxyZWN0IHg9IjE3MCIgeT0iMjIwIiB3aWR0aD0iMjAiIGhlaWdodD0iMzAiIHJ4PSIxMCIgZmlsbD0iI0ZGREJCRiIvPgo8cGF0aCBkPSJNMTkwIDEzMEwxOTAgMTgwIiBzdHJva2U9IiNGRkRCQkYiIHN0cm9rZS13aWR0aD0iMTAiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8dGV4dCB4PSIyMDAiIHk9IjE5MCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2Ij7wn5GJPC90ZXh0Pgo8L3N2Zz4K" 
                     alt="Professional Woman" 
                     style="max-width: 200px; height: auto; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));">
            </div>
        </div>
          </div>
        <div class="summary-grid">
            <div class="summary-metric">
                <div class="summary-metric-value">{len(st.session_state.course_recommendations)}</div>
                <div class="summary-metric-label">Course Matches</div>
            </div>
            <div class="summary-metric">
                <div class="summary-metric-value">{len(st.session_state.grad_certificate_recommendations)}</div>
                <div class="summary-metric-label">Certificates</div>
            </div>
            <div class="summary-metric">
                <div class="summary-metric-value">{tech_ratio}%</div>
                <div class="summary-metric-label">Technical Focus</div>
            </div>
            <div class="summary-metric">
                <div class="summary-metric-value">{business_ratio}%</div>
                <div class="summary-metric-label">Business Focus</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Course Recommendations Section
    if st.session_state.course_recommendations:
        st.markdown('<div class="section-title" style="margin-top: 3rem;">📚 Course Recommendations</div>', unsafe_allow_html=True)
        
        # Display courses in a grid layout
        for i in range(0, len(st.session_state.course_recommendations), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(st.session_state.course_recommendations):
                    course = st.session_state.course_recommendations[i + j]
                    
                    with col:
                        # Determine course type for styling
                        course_type = course.get('course_type', 'mixed')
                        type_badge_class = 'technical-badge' if course_type == 'technical' else 'business-badge' if course_type == 'business' else 'mixed-badge'
                        
                        # Calculate match percentage
                        match_percentage = convert_similarity_to_percentage(course.get('adjusted_similarity', course.get('similarity_score', 0)))
                        
                        # Course card with fixed content
                        st.markdown(f"""
                        <div class="professional-course-card">
                            <div class="course-header-pro">
                                <div class="course-rank-pro">#{course.get('rank', i+j+1)}</div>
                                <div class="course-code-pro">{course.get('course_code', 'N/A')}</div>
                                <div class="course-name-pro">{course.get('course_name', 'Untitled Course')}</div>
                                <div class="course-type-badge {type_badge_class}">
                                    {'🔧' if course_type == 'technical' else '💼' if course_type == 'business' else '⚖️'} {course_type.title()}
                                </div>
                            </div>
                            <div class="course-body-pro">
                                <div class="similarity-section-pro" style="display: flex; justify-content: center; margin-bottom: 2rem;">
                                    <div class="similarity-metric">
                                        <div class="similarity-value-pro">{match_percentage}%</div>
                                        <div class="similarity-label-pro">MATCH</div>
                                    </div>
                                </div>
                                <div class="course-description-pro">
                                    {course.get('description', 'No description available.')[:200]}{'...' if len(course.get('description', '')) > 200 else ''}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add Streamlit expander for outcomes
                        outcomes = course.get('learning_outcomes', []) or course.get('outcomes', [])
                        if outcomes:
                            with st.expander("View Learning Outcomes", expanded=False):
                                for idx, outcome in enumerate(outcomes, 1):
                                    st.write(f"**{idx}.** {outcome}")
    
    # Graduate Certificate Recommendations Section
    if st.session_state.grad_certificate_recommendations:
        st.markdown('<div class="section-title" style="margin-top: 3rem;">🎓 Graduate Certificate Recommendations</div>', unsafe_allow_html=True)
        
        # Display certificates
        for i, cert in enumerate(st.session_state.grad_certificate_recommendations):
            match_percentage = convert_similarity_to_percentage(cert.get('adjusted_similarity', cert.get('similarity_score', 0)))
            
            st.markdown(f"""
            <div class="professional-course-card">
                <div class="course-header-pro">
                    <div class="course-rank-pro">#{i+1}</div>
                    <div class="course-code-pro">CERTIFICATE</div>
                    <div class="course-name-pro">{cert.get('course_name', 'Untitled Certificate')}</div>
                    <div class="course-type-badge certificate-badge">
                        🎓 Graduate Certificate
                    </div>
                </div>
                <div class="course-body-pro">
                    <div class="similarity-section-pro" style="display: flex; justify-content: center; margin-bottom: 2rem;">
                        <div class="similarity-metric">
                            <div class="similarity-value-pro">{match_percentage}%</div>
                            <div class="similarity-label-pro">MATCH</div>
                        </div>
                    </div>
                    <div class="course-description-pro">
                        {cert.get('course_description', 'No description available.')[:300]}{'...' if len(cert.get('course_description', '')) > 300 else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add Streamlit expander for requirements
            requirements = cert.get('course_requirements', [])
            if requirements:
                with st.expander("📋 View Certificate Requirements", expanded=False):
                    for idx, req in enumerate(requirements, 1):
                        st.write(f"**{idx}.** {req}")
    
    # Action Buttons
    st.markdown('<br><br>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Back to Consultation", use_container_width=True):
            prev_step()
            st.rerun()
    
    with col2:
        # Generate PDF Report
        if st.button("📄 Download PDF Report", use_container_width=True):
            try:
                pdf_buffer = generate_pdf(
                    st.session_state.course_recommendations, 
                    st.session_state.grad_certificate_recommendations
                )
                
                st.download_button(
                    label="📥 Download Report",
                    data=pdf_buffer,
                    file_name=f"Stevens_Training_Recommendations_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    
    with col3:
        if st.button("🔄 New Analysis", use_container_width=True):
            # Reset session state for new analysis
            for key in ['current_step', 'form_data', 'initial_req', 'conversation_history', 
                       'question_count', 'requirements_data', 'ai_analysis', 
                       'course_recommendations', 'grad_certificate_recommendations', 'current_ai_question']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Initialize defaults
            st.session_state.current_step = 2
            st.session_state.form_data = {}
            st.session_state.conversation_history = []
            st.session_state.question_count = 0
            st.session_state.requirements_data = {}
            st.session_state.course_recommendations = []
            st.session_state.grad_certificate_recommendations = []
            
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Academic Footer
if st.session_state.get('logged_in', False):
    current_step = st.session_state.get('current_step', 1)
    st.markdown(f"""
    <div class="academic-footer">
        <div class="footer-content">
            <div class="footer-title">Stevens Institute of Technology</div>
            <div class="footer-details">
                <strong>College of Professional Education</strong><br>
                📧 cpe@stevens.edu &nbsp;|&nbsp; 📞 (201) 216-5000 &nbsp;|&nbsp; 🌐 stevens.edu/cpe
            </div>
            <div class="footer-meta">
                Session ID: SIT_{datetime.now().strftime('%Y%m%d_%H%M%S')} &nbsp;|&nbsp; 
                Analysis Progress: Step {current_step-1} of 5 &nbsp;|&nbsp; 
                Powered by Stevens OptiLearn AI
            </div>
        </div>
    </div>
        """, unsafe_allow_html=True)