import streamlit as st

# Page setup
st.set_page_config(
    page_title="Stevens Corporate Training Program Matcher",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Text:wght@400;600;700&display=swap');

/* ENHANCED SLIDER STYLING - COMPLETE REPLACEMENT */
.stSlider {
    padding: 2rem 0 !important;
}

.stSlider > div > div > div {
    background: linear-gradient(90deg, #e5e7eb 0%, #d1d5db 100%) !important;
    height: 14px !important;
    border-radius: 7px !important;
    position: relative !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
}

.stSlider > div > div > div > div {
    background: linear-gradient(90deg, #8B1538 0%, #a61e42 100%) !important;
    height: 14px !important;
    border-radius: 7px !important;
    position: relative !important;
    box-shadow: 0 2px 12px rgba(139, 21, 56, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stSlider > div > div > div > div > div {
    background: white !important;
    border: 4px solid #8B1538 !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    box-shadow: 0 6px 20px rgba(139, 21, 56, 0.4), 0 2px 8px rgba(0,0,0,0.1) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: grab !important;
    position: relative !important;
    top: -9px !important;
}

.stSlider > div > div > div > div > div:hover {
    transform: scale(1.2) !important;
    box-shadow: 0 8px 30px rgba(139, 21, 56, 0.5), 0 4px 12px rgba(0,0,0,0.15) !important;
    border-width: 5px !important;
}

.stSlider > div > div > div > div > div:active {
    cursor: grabbing !important;
    transform: scale(1.25) !important;
    box-shadow: 0 10px 35px rgba(139, 21, 56, 0.6), 0 6px 16px rgba(0,0,0,0.2) !important;
}

/* Enhanced ratio display */
.ratio-display {
    display: flex;
    justify-content: space-between;
    margin: 2rem 0;
    padding: 2rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    position: relative;
    overflow: hidden;
}

.ratio-display::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, #8B1538 0%, #a61e42 100%);
}

.ratio-item {
    text-align: center;
    flex: 1;
    position: relative;
}

.ratio-item:not(:last-child)::after {
    content: '';
    position: absolute;
    right: -1px;
    top: 50%;
    transform: translateY(-50%);
    height: 50px;
    width: 2px;
    background: #cbd5e1;
}

.ratio-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #8B1538;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 4px rgba(139, 21, 56, 0.1);
    transition: all 0.3s ease;
}

.ratio-label {
    font-size: 1rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

.element-container {
    margin-left: 1rem !important;
    margin-right: 1rem !important;
}

/* Reset and base styles */
.stApp {
    background-color: #fafafa;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1a1a1a;
}

/* Remove default Streamlit margins and padding */
.main .block-container {
    padding: 0 !important;
    max-width: none !important;
    margin: 0 !important;
}

.stApp > div:first-child {
    margin: 0 !important;
    padding: 0 !important;
}

/* Header section above video */
.header-section {
    background: linear-gradient(135deg, #8B1538 0%, #a61e42 100%);
    padding: 3rem 1rem;
    text-align: center;
    color: white;
    margin: 1rem;
    width: calc(100vw - 2rem);
    position: relative;
    left: 50%;
    right: 50%;
    margin-left: calc(-50vw + 1rem);
    margin-right: calc(-50vw + 1rem);
    border-radius: 8px;
}

.header-title {
    font-family: 'Crimson Text', serif;
    font-size: 3rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    color: white;
}

.header-subtitle {
    font-size: 1.1rem;
    font-weight: 300;
    margin-top: 0.5rem;
    opacity: 0.95;
    letter-spacing: 0.5px;
}

/* Video banner */
.video-banner-container {
    position: relative;
    width: calc(100vw - 2rem);
    height: 70vh;
    overflow: hidden;
    left: 50%;
    right: 50%;
    margin-left: calc(-50vw + 1rem);
    margin-right: calc(-50vw + 1rem);
    border-radius: 8px;
}

.video-banner-container video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.video-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(rgba(139, 21, 56, 0.3), rgba(139, 21, 56, 0.1));
    z-index: 1;
}

.video-text {
    position: absolute;
    bottom: 2rem;
    left: 2rem;
    color: white;
    z-index: 2;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}

.video-text h2 {
    font-family: 'Crimson Text', serif;
    font-size: 2.5rem;
    font-weight: 600;
    margin: 0;
    line-height: 1.2;
}

.video-text p {
    font-size: 1.1rem;
    font-weight: 400;
    margin-top: 0.5rem;
    opacity: 0.95;
}

/* Form styling */
.form-wrapper {
    max-width: 900px;
    margin: 4rem auto 2rem auto;
    padding: 3rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-top: 4px solid #8B1538;
}

.section-title {
    font-family: 'Crimson Text', serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: #8B1538;
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #f0f0f0;
    margin-left: 10px;
    margin-right: 10px;
    margin: 1rem;
}

/* Progress bar */
.progress-container {
    max-width: 900px;
    margin: 2rem auto 0 auto;
    padding: 1rem 3rem;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background-color: #e8e8e8;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 1rem;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #8B1538, #FF6B35);
    transition: width 0.4s ease-in-out;
    border-radius: 4px;
}

.step-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.5rem;
}

/* Form inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
    background-color: #fbfbfb !important;
    border: 1px solid #d1d5db !important;
    border-radius: 4px !important;
    padding: 0.75rem !important;
    font-size: 1rem !important;
    transition: border-color 0.2s ease-in-out !important;
}

.stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within > div, .stTextArea textarea:focus {
    border-color: #8B1538 !important;
    box-shadow: 0 0 0 3px rgba(139, 21, 56, 0.1) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #8B1538, #a61e42) !important;
    color: white !important;
    font-weight: 500 !important;
    padding: 0.75rem 2rem !important;
    border: none !important;
    border-radius: 4px !important;
    transition: all 0.2s ease-in-out !important;
    letter-spacing: 0.3px !important;
    font-size: 1rem !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #a61e42, #8B1538) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(139, 21, 56, 0.3) !important;
}

/* Secondary button */
.secondary-button {
    background: transparent !important;
    color: #8B1538 !important;
    border: 1px solid #8B1538 !important;
}

.secondary-button:hover {
    background: #8B1538 !important;
    color: white !important;
}

            
/* Error and success messages */
.stError {
    background-color: #fef2f2 !important;
    border: 1px solid #fecaca !important;
    color: #dc2626 !important;
}

.stSuccess {
    background-color: #8B1538 !important;
    border: 1px solid #A91B47 !important;
    color: #white !important;
}
            
.stAlert > div {
        background-color: #8B1538 !important;
        border: 1px solid #A91B47 !important;
        color: white !important;
    }
.stAlert > div > div {
        color: white !important;
 }

/* Remove Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Responsive design */
@media (max-width: 768px) {
    .header-title {
        font-size: 2rem;
    }
    
    .form-wrapper {
        margin: 2rem 1rem;
        padding: 2rem;
    }
    
    .progress-container {
        padding: 0 1rem;
    }
    
    .video-text h2 {
        font-size: 1.8rem;
    }
    
    .ratio-display {
        flex-direction: column;
        gap: 1rem;
        padding: 1.5rem;
    }
    
    .ratio-item:not(:last-child)::after {
        display: none;
    }
    
    .ratio-value {
        font-size: 2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="header-section">
    <h1 class="header-title">Stevens Corporate Training Program Matcher</h1>
    <p class="header-subtitle">Find the perfect professional development solution for your organization</p>
</div>
""", unsafe_allow_html=True)

# Video Banner
st.markdown("""
<div class="video-banner-container">
    <video autoplay muted loop playsinline>
        <source src="https://assets.stevens.edu/mviowpldu823/5LkHIMp8z2Rumo4A44zg1r/d478cdc681558a3bd48185988224ad39/Home_Page_F24_v4.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
    <div class="video-overlay"></div>
    <div class="video-text">
        <h2>Stevens Institute of Technology</h2>
        <p>Excellence in Innovation and Technology Education</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Session state initialization
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

# Navigation functions
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# Step 1: Company Information
if st.session_state.step == 1:
    st.markdown('<div class="section-title" style="align: center";>Company Information</div>', unsafe_allow_html=True) 
    st.markdown('<div style="margin: 1rem;">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="margin: 1rem;">', unsafe_allow_html=True)
        company_name = st.text_input("Company Name *", 
                                   value=st.session_state.form_data.get("company_name", ""))
        industry = st.selectbox("Industry *", 
                              ["", "Technology", "Finance", "Healthcare", "Manufacturing", 
                               "Retail", "Consulting", "Education", "Government", "Other"],
                              index=0 if not st.session_state.form_data.get("industry") else 
                              ["", "Technology", "Finance", "Healthcare", "Manufacturing", 
                               "Retail", "Consulting", "Education", "Government", "Other"].index(st.session_state.form_data.get("industry")))
    
    with col2:
        st.markdown('<div style="margin: 1rem;">', unsafe_allow_html=True)
        company_size = st.selectbox("Company Size *",
                                  ["", "1-50 employees", "51-200 employees", "201-1000 employees", 
                                   "1001-5000 employees", "5000+ employees"],
                                  index=0 if not st.session_state.form_data.get("company_size") else
                                  ["", "1-50 employees", "51-200 employees", "201-1000 employees", 
                                   "1001-5000 employees", "5000+ employees"].index(st.session_state.form_data.get("company_size")))
        
        contact_email = st.text_input("Contact Email *",
                                    value=st.session_state.form_data.get("contact_email", ""))
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Continue →", key="step1_continue"):
        if company_name and industry and company_size and contact_email:
            st.session_state.form_data.update({
                "company_name": company_name,
                "industry": industry,
                "company_size": company_size,
                "contact_email": contact_email
            })
            next_step()
            st.rerun()
        else:
            st.error("Please fill in all required fields before continuing.")

# Step 2: Skill Focus
elif st.session_state.step == 2:
    st.markdown('<div class="section-title" style="margin: 1rem;">Training Focus Areas</div>', unsafe_allow_html=True)

    st.markdown("""
<div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 1rem;">
    <label style="font-weight: 700; font-size: 1.3rem; color: #1e293b; display: block; text-align: center; margin-bottom: 1rem;">
        Proportion of Technical vs. Business Skill Development
    </label>
</div>
""", unsafe_allow_html=True)

    tech_ratio = st.slider(
        label="",
        min_value=0,
        max_value=100,
        value=st.session_state.form_data.get("tech_ratio", 50),
        key="tech_ratio_slider"
    )
    
    business_ratio = 100 - tech_ratio
    
    # Enhanced ratio display
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

    st.write("**Primary training objectives (select all that apply):**")
    objectives = st.multiselect("Training Objectives",
                              ["Upskill existing workforce", "Leadership development", 
                               "Digital transformation", "Innovation and R&D", 
                               "Compliance and certifications", "Team building",
                               "Process improvement", "Customer service excellence"],
                              default=st.session_state.form_data.get("objectives", []))
    
    st.session_state.form_data.update({
        "tech_ratio": tech_ratio,
        "business_ratio": business_ratio,
        "objectives": objectives
    })

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back", key="step2_back"):
            prev_step()
            st.rerun()
    with col2:
        if st.button("Continue →", key="step2_continue"):
            next_step()
            st.rerun()

# Step 3: Technical Needs
elif st.session_state.step == 3:
    st.markdown('<div class="section-title" style="margin: 1rem;">💻 Technical Skills & Technologies</div>', unsafe_allow_html=True)
    
    if st.session_state.form_data.get("tech_ratio", 0) > 0:
        st.write("**Select the technical areas of interest:**")
        
        col1, col2 = st.columns(2)
        with col1:
            programming = st.multiselect("Programming & Development",
                                       ["Python", "Java", "JavaScript", "C++", "C", "C#", "R", "SQL", "Web Development",  "SpringBoot","Algorithms"],
                                       default=st.session_state.form_data.get("programming", []))
            
            data_analytics = st.multiselect("Data & Analytics",
                                          ["Data Science", "Machine Learning", "AI/Deep Learning", 
                                           "Business Intelligence", "Data Visualization", "Statistics"],
                                          default=st.session_state.form_data.get("data_analytics", []))
        
        with col2:
            cybersecurity = st.multiselect("Cybersecurity",
                                         ["Network Security", "Ethical Hacking", "Risk Assessment", 
                                          "Compliance", "Incident Response"],
                                         default=st.session_state.form_data.get("cybersecurity", []))
            
            other_tech = st.multiselect("Other Technologies",
                                      ["Cloud Computing (AWS/Azure)", "DevOps", "IoT", "Blockchain", 
                                       "Project Management", "Systems Engineering"],
                                      default=st.session_state.form_data.get("other_tech", []))
    else:
        st.info("Since your focus is primarily on business skills, you can skip the technical selections.")
        programming = data_analytics = cybersecurity = other_tech = []

    current_tech_level = st.selectbox("Current Technical Skill Level of Your Team",
                                    ["Beginner", "Intermediate", "Advanced", "Mixed levels"],
                                    index=["Beginner", "Intermediate", "Advanced", "Mixed levels"].index(
                                        st.session_state.form_data.get("current_tech_level", "Beginner")))

    st.session_state.form_data.update({
        "programming": programming,
        "data_analytics": data_analytics,
        "cybersecurity": cybersecurity,
        "other_tech": other_tech,
        "current_tech_level": current_tech_level
    })

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back", key="step3_back"):
            prev_step()
            st.rerun()
    with col2:
        if st.button("Continue →", key="step3_continue"):
            next_step()
            st.rerun()

# Step 4: Logistics
elif st.session_state.step == 4:
    st.markdown('<div class="section-title" style="margin: 1rem;">Training Logistics</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        duration = st.selectbox("Training Duration",
                              ["1-2 days", "1 week", "2-4 weeks", "1-3 months", "3+ months", "Flexible"],
                              index=["1-2 days", "1 week", "2-4 weeks", "1-3 months", "3+ months", "Flexible"].index(
                                  st.session_state.form_data.get("duration", "Flexible")))
    
    with col2:
        budget_range = st.selectbox("Budget Range (per participant)",
                                  ["Under $1,000", "$1,000-$5,000", "$5,000-$10,000", "$10,000-$25,000", "$25,000+", "Need consultation"],
                                  index=["Under $1,000", "$1,000-$5,000", "$5,000-$10,000", "$10,000-$25,000", "$25,000+", "Need consultation"].index(
                                      st.session_state.form_data.get("budget_range", "Need consultation")))

    additional_notes = st.text_area("Additional Requirements or Notes",
                                  value=st.session_state.form_data.get("additional_notes", ""),
                                  height=100)

    st.session_state.form_data.update({
        "duration": duration,
        "budget_range": budget_range,
        "additional_notes": additional_notes
    })

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back", key="step4_back"):
            prev_step()
            st.rerun()
    with col2:
        if st.button("Continue →", key="step4_continue"):
            next_step()
            st.rerun()

# Step 5: Summary
elif st.session_state.step == 5:
    st.markdown('<div class="section-title" style="margin: 1rem;">Training Profile Summary</div>', unsafe_allow_html=True)
    
    # Display summary
    data = st.session_state.form_data
        
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Company Information:**")
        st.write(f"• Company: {data.get('company_name', 'N/A')}")
        st.write(f"• Industry: {data.get('industry', 'N/A')}")
        st.write(f"• Size: {data.get('company_size', 'N/A')}")
        st.write(f"• Contact: {data.get('contact_email', 'N/A')}")
        
        st.write("**Training Focus:**")
        st.write(f"• Technical Skills: {data.get('tech_ratio', 0)}%")
        st.write(f"• Business Skills: {data.get('business_ratio', 0)}%")
    
    with col2:
        st.write("**Logistics:**")
        st.write(f"• Duration: {data.get('duration', 'N/A')}")
        st.write(f"• Budget: {data.get('budget_range', 'N/A')}")

    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", key="step5_back"):
            prev_step()
            st.rerun()
    
    with col3:
        if st.button("View Recommended Courses", key="submit"):
            st.success("Loadingggg!")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #666; font-size: 0.9rem; border-top: 1px solid #eee; margin-top: 3rem;">
    <p>Stevens Institute of Technology | Corporate Training & Professional Development</p>
    <p>📧 corporate.training@stevens.edu | 📞 (201) 216-5000</p>
</div>
""", unsafe_allow_html=True)
