import streamlit as st
import pymongo
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from bson import ObjectId
import json
import io
import time

# MongoDB Configuration
MONGO_URI = "mongodb+srv://codermishyt:tQk0U81QVvktb5s4@optilearn.vu626pu.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

# Initialize MongoDB connection
@st.cache_resource
def init_connection():
    try:
        # Add SSL configuration to handle certificate issues
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        # Test the connection
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

# Fetch companies data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_companies_data():
    client = init_connection()
    if client is None:
        return []
    
    try:
        # Based on test results, we know the structure
        databases_to_check = ['optilearn', 'otpilearn']
        all_companies_data = []
        
        for db_name in databases_to_check:
            try:
                db = client[db_name]
                collection = db['company']  # We know it's 'company' not 'companies'
                data_cursor = collection.find().sort([("last_updated", pymongo.DESCENDING)])
                data = list(data_cursor)

                if data:
                    st.success(f"✅ Loaded {len(data)} companies from {db_name}.company")
                    # Add database source info to each document
                    for doc in data:
                        doc['_source_db'] = db_name
                    all_companies_data.extend(data)
                    
            except Exception as db_error:
                st.warning(f"⚠️ Error accessing database '{db_name}': {db_error}")
                continue
        
        return all_companies_data
        
    except Exception as e:
        st.error(f"❌ Error fetching companies data: {e}")
        return []

# Helper function to get course field with fallbacks
def get_course_field(course, field_name, fallback_fields=None, default='N/A'):
    """Get course field with multiple fallback options"""
    if fallback_fields is None:
        fallback_fields = []
    
    # Primary field
    value = course.get(field_name)
    if value and str(value).strip():
        return str(value).strip()
    
    # Try fallback fields
    for fallback in fallback_fields:
        value = course.get(fallback)
        if value and str(value).strip():
            return str(value).strip()
    
    return default

# Helper function to get program field with fallbacks
def get_program_field(program, field_name, fallback_fields=None, default='N/A'):
    """Get program field with multiple fallback options"""
    if fallback_fields is None:
        fallback_fields = []
    
    # Primary field
    value = program.get(field_name)
    if value and str(value).strip():
        return str(value).strip()
    
    # Try fallback fields
    for fallback in fallback_fields:
        value = program.get(fallback)
        if value and str(value).strip():
            return str(value).strip()
    
    return default

# Helper function to parse MongoDB dates
def parse_mongo_date(date_obj):
    if isinstance(date_obj, dict) and '$date' in date_obj:
        if isinstance(date_obj['$date'], dict) and '$numberLong' in date_obj['$date']:
            timestamp = int(date_obj['$date']['$numberLong']) / 1000
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(date_obj['$date'])
    return str(date_obj)

# Helper function to get timestamp for sorting
def get_company_timestamp(company):
    """Extract timestamp from company data for sorting purposes"""
    # Try different timestamp fields in order of preference
    timestamp_fields = [
        'last_updated',
        'created_at',
        'updated_at',
        ('course_recommendations', 'generated_at'),
        ('certificate_recommendations', 'generated_at')
    ]
    
    for field in timestamp_fields:
        if isinstance(field, tuple):
            # Nested field
            value = company.get(field[0], {}).get(field[1])
        else:
            # Direct field
            value = company.get(field)
        
        if value:
            try:
                if isinstance(value, dict) and '$date' in value:
                    if isinstance(value['$date'], dict) and '$numberLong' in value['$date']:
                        return int(value['$date']['$numberLong']) / 1000
                    else:
                        return datetime.fromisoformat(str(value['$date']).replace('Z', '+00:00')).timestamp()
                elif isinstance(value, datetime):
                    return value.timestamp()
                elif isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
                    except:
                        continue
                elif isinstance(value, (int, float)):
                    return float(value)
            except:
                continue
    
    # If no timestamp found, return 0 (oldest)
    return 0

# Helper function to parse MongoDB ObjectId
def parse_mongo_id(id_obj):
    if isinstance(id_obj, dict) and '$oid' in id_obj:
        return id_obj['$oid']
    return str(id_obj)

# Helper function to parse MongoDB numbers
def parse_mongo_number(num_obj):
    if isinstance(num_obj, dict):
        if '$numberDouble' in num_obj:
            return float(num_obj['$numberDouble'])
        elif '$numberInt' in num_obj:
            return int(num_obj['$numberInt'])
        elif '$numberLong' in num_obj:
            return int(num_obj['$numberLong'])
    return float(num_obj) if num_obj else 0.0

# FIXED: Helper function to get course field with fallbacks
def get_course_field(course, field_name, fallback_fields=None, default='N/A'):
    """Get course field with multiple fallback options"""
    if fallback_fields is None:
        fallback_fields = []
    
    # Primary field
    value = course.get(field_name)
    if value and str(value).strip():
        return str(value).strip()
    
    # Try fallback fields
    for fallback in fallback_fields:
        value = course.get(fallback)
        if value and str(value).strip():
            return str(value).strip()
    
    return default

# FIXED: Helper function to get course description with intelligent fallbacks
def get_course_description(course):
    """Get course description with intelligent fallbacks"""
    # Try primary description fields
    description_fields = ['description', 'course_description', 'desc', 'summary', 'overview']
    
    for field in description_fields:
        desc = course.get(field)
        if desc and str(desc).strip() and len(str(desc).strip()) > 10:
            return str(desc).strip()
    
    # If no description found, try to construct one from available data
    course_name = get_course_field(course, 'course_name', ['name', 'title', 'course_title'])
    module_title = course.get('module_title', '')
    course_type = course.get('course_type', '')
    
    # Construct description based on available data
    if module_title and course_type:
        return f"A {course_type} course focusing on {module_title} concepts and practical applications."
    elif module_title:
        return f"Professional course covering {module_title} topics and methodologies."
    elif course_type:
        return f"A {course_type} course designed to enhance professional competencies."
    elif course_name != 'N/A':
        return f"Professional development course: {course_name}. Designed to build essential skills and knowledge."
    else:
        return "Comprehensive professional development course designed to enhance key competencies and practical skills."

# Helper function to clean course requirements
def parse_course_requirements(requirements):
    if isinstance(requirements, str):
        try:
            # Try to parse as JSON if it's a string
            import json
            parsed = json.loads(requirements)
            if isinstance(parsed, list):
                return [f"{req.get('course_code', 'N/A')}: {req.get('course_name', 'N/A')}" for req in parsed]
            return [requirements]
        except:
            return [requirements]
    elif isinstance(requirements, list):
        return [f"{req.get('course_code', 'N/A')}: {req.get('course_name', 'N/A')}" if isinstance(req, dict) else str(req) for req in requirements]
    return [str(requirements)]

# Initialize session state for proposal
def init_proposal_state():
    if 'selected_courses' not in st.session_state:
        st.session_state.selected_courses = set()
    if 'selected_certificates' not in st.session_state:
        st.session_state.selected_certificates = set()
    if 'total_credits' not in st.session_state:
        st.session_state.total_credits = 0

# Calculate total credits
def calculate_credits():
    return (len(st.session_state.selected_courses) + len(st.session_state.selected_certificates)) * 3

# Update credits in session state
def update_credits():
    st.session_state.total_credits = calculate_credits()

# Company detail view - UPDATED with Company Requirements
def show_company_detail(company_data):
    st.markdown("""
    <style>
    .company-detail-header {
        background: linear-gradient(135deg, #800020, #a0002a);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(128, 0, 32, 0.3);
    }
    .company-detail-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
        color: white;
    }
    .company-detail-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
        color: white;
    }
    .detail-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #800020;
    }
    .requirements-section {
        background: #fff5f5;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 4px solid #800020;
        border: 2px solid #800020;
    }
    .requirements-list {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        border-left: 4px solid #800020;
    }
    .requirement-item {
        background: #f8f9fa;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        border-left: 3px solid #800020;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Dashboard", key="company_detail_back"):
        st.session_state.current_view = "dashboard"
        st.rerun()
    
    # Header
    company_name = company_data.get('company_name', 'Unknown Company')
    st.markdown(f"""
    <div class="company-detail-header">
        <h1> {company_name}</h1>
        <p>Learning recommendations and proposal generation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Company info and recommendations (existing layout)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="detail-section">
            <h3>Company Information</h3>
            <p><strong>Industry:</strong> {company_data.get('industry', 'N/A')}</p>
            <p><strong>Size:</strong> {company_data.get('company_size', 'N/A')}</p>
            <p><strong>Contact:</strong> {company_data.get('contact_email', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        course_recs = company_data.get('course_recommendations', {}).get('recommendations', [])
        cert_recs = company_data.get('certificate_recommendations', {}).get('recommendations', [])
        
        st.markdown(f"""
        <div class="detail-section">
            <h3>Available Recommendations</h3>
            <p><strong>Courses:</strong> {len(course_recs)}</p>
            <p><strong>Certificates:</strong> {len(cert_recs)}</p>
            <p><strong>Total Items:</strong> {len(course_recs) + len(cert_recs)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Company Requirements Section
    st.markdown("##  Company Requirements")
    
    # Try to get requirements from various possible fields
    requirements_data = (
        company_data.get('requirements') or 
        company_data.get('company_requirements') or 
        company_data.get('learning_requirements') or 
        company_data.get('training_needs') or
        company_data.get('skills_needed') or
        company_data.get('requirements_text') or
        []
    )
    
    # Also check if requirements are nested in other structures
    if not requirements_data:
        # Check if requirements are in course_recommendations metadata
        course_req_meta = company_data.get('course_recommendations', {})
        requirements_data = course_req_meta.get('requirements', [])
    
    if requirements_data:
        # Parse requirements data
        if isinstance(requirements_data, str):
            try:
                # Try to parse as JSON if it's a string
                import json
                parsed_reqs = json.loads(requirements_data)
                if isinstance(parsed_reqs, list):
                    requirements_list = parsed_reqs
                else:
                    requirements_list = [requirements_data]
            except:
                requirements_list = [requirements_data]
        elif isinstance(requirements_data, list):
            requirements_list = requirements_data
        else:
            requirements_list = [str(requirements_data)]
        
        # Display requirements in a nice format
        for i, req in enumerate(requirements_list):
            if isinstance(req, dict):
                # If requirement is a dict, extract relevant fields
                req_title = req.get('title', req.get('name', req.get('skill', f'Requirement {i+1}')))
                req_description = req.get('description', req.get('details', ''))
                req_priority = req.get('priority', req.get('importance', 'Medium'))
                req_category = req.get('category', req.get('type', 'General'))
                
                st.markdown(f"""
                <div class="requirement-item">
                    <h5 style="color: #800020; margin: 0 0 0.5rem 0;">{req_title}</h5>
                    {f'<p style="margin: 0.25rem 0;"><strong>Category:</strong> {req_category}</p>' if req_category != 'General' else ''}
                    {f'<p style="margin: 0.25rem 0;"><strong>Priority:</strong> {req_priority}</p>' if req_priority != 'Medium' else ''}
                    {f'<p style="margin: 0.25rem 0; color: #666;">{req_description}</p>' if req_description else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Simple string requirement
                st.markdown(f"""
                <div class="requirement-item">
                    <h5 style="color: #800020; margin: 0;"> {str(req)}</h5>
                </div>
                """, unsafe_allow_html=True)
    else:
        # No requirements found - show helpful message
        st.markdown(f"""
        <div class="requirements-section">
            <h3 style="color: #800020; margin-top: 0;">Company Requirements</h3>
            <div class="requirements-list">
                <p style="color: #666666; margin: 0; text-align: center;">
                    <strong>ℹ️ No specific requirements found</strong><br>
                    Requirements data not available in the current company profile.
                </p>
                <p style="color: #666666; margin: 1rem 0 0 0; font-size: 0.9rem;">
                    <strong>Available company fields:</strong><br>
                    {', '.join([key for key in company_data.keys() if not key.startswith('_')])}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if course_recs:
            if st.button(f"View Courses ({len(course_recs)})", key="view_courses"):
                st.session_state.current_view = "courses"
                st.rerun()
        else:
            st.button("No Courses Available", disabled=True)
    
    with col2:
        if cert_recs:
            if st.button(f"View Certificates ({len(cert_recs)})", key="view_certificates"):
                st.session_state.current_view = "certificates"
                st.rerun()
        else:
            st.button("No Certificates Available", disabled=True)
    
    with col3:
        if course_recs or cert_recs:
            if st.button(" Create Proposal", key="create_proposal"):
                st.session_state.current_view = "proposal"
                # Clear any existing selections
                st.session_state.selected_courses = set()
                st.session_state.selected_certificates = set()
                st.session_state.total_credits = 0
                st.rerun()
        else:
            st.button("📋 No Items for Proposal", disabled=True)
    
    # Quick preview of recommendations
    if course_recs or cert_recs:
        st.markdown("## Quick Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if course_recs:
                st.markdown("### Top Courses")
                for i, course in enumerate(course_recs[:3]):  # Show top 3
                    similarity = parse_mongo_number(course.get('similarity_score', 0))
                    course_name = get_course_field(course, 'course_name', ['name', 'title'])
                    st.markdown(f"""
                    **{course_name}**  
                    Match: {similarity:.1%} | Type: {course.get('course_type', 'N/A')}
                    """)
        
        with col2:
            if cert_recs:
                st.markdown("### Top Certificates")
                for i, cert in enumerate(cert_recs[:3]):  # Show top 3
                    similarity = parse_mongo_number(cert.get('similarity_score', 0))
                    cert_name = get_course_field(cert, 'course_name', ['name', 'title'])
                    st.markdown(f"""
                    **{cert_name}**  
                    Match: {similarity:.1%}
                    """)

# UPDATED Proposal Generator - More Professional and Clean
def show_proposal_generator(company_data):
    st.markdown("""
    <style>
    .proposal-header {
        background: linear-gradient(135deg, #800020, #a0002a);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(128, 0, 32, 0.3);
    }
    .proposal-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
        color: white;
    }
    .proposal-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
        color: white;
    }
    .credits-tracker {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #800020;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .credits-tracker h3 {
        margin: 0 0 1rem 0;
        color: #800020;
        font-size: 1.5rem;
    }
    .credits-display {
        font-size: 2rem;
        font-weight: bold;
        color: #800020;
        margin: 0.5rem 0;
    }
    .credits-bar {
        background: #f0f0f0;
        border-radius: 10px;
        height: 20px;
        margin: 1rem 0;
        overflow: hidden;
    }
    .credits-fill {
        height: 100%;
        background: linear-gradient(90deg, #800020, #a0002a);
        transition: width 0.3s ease;
        border-radius: 10px;
    }
    .warning-credits {
        color: #ff6b6b !important;
        background: #ffe0e0 !important;
        border-color: #ff6b6b !important;
    }
    .item-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .item-card:hover {
        border-color: #800020;
        box-shadow: 0 2px 8px rgba(128, 0, 32, 0.2);
    }
    .item-card.selected {
        border-color: #800020;
        background: #f8f9fa;
        border-width: 2px;
    }
    .proposal-summary {
        background: #f8f9fa;
        border: 2px solid #800020;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
    }
    .course-description {
        background: #f8f9fa;
        padding: 0.75rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        color: #555;
        border-left: 3px solid #800020;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize proposal state
    init_proposal_state()
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← Back to Company", key="proposal_back"):
            st.session_state.current_view = "company_detail"
            st.rerun()
    
    with col2:
        if st.button("🏠 Dashboard", key="proposal_home"):
            st.session_state.current_view = "dashboard"
            # Clear selection state when going back to dashboard
            st.session_state.selected_courses = set()
            st.session_state.selected_certificates = set()
            st.session_state.total_credits = 0
            st.rerun()
    
    # Header
    company_name = company_data.get('company_name', 'Unknown Company')
    st.markdown(f"""
    <div class="proposal-header">
        <h1>Create Professional Learning Proposal</h1>
        <p>Design a customized educational pathway for {company_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Credits tracker - Refresh current credits
    current_credits = calculate_credits()
    max_credits = 36
    credits_percentage = min((current_credits / max_credits) * 100, 100)
    credits_class = "warning-credits" if current_credits > max_credits else ""
    
    st.markdown(f"""
    <div class="credits-tracker {credits_class}">
        <h3>💳 Credit Tracker</h3>
        <div class="credits-display">{current_credits} / {max_credits} Credits</div>
        <div class="credits-bar">
            <div class="credits-fill" style="width: {credits_percentage}%"></div>
        </div>
        <p>Each course and certificate = 3 credits</p>
        {f'<p style="color: #ff6b6b; font-weight: bold;">⚠️ Exceeds maximum credits!</p>' if current_credits > max_credits else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Get courses and certificates
    course_recs = company_data.get('course_recommendations', {}).get('recommendations', [])
    cert_recs = company_data.get('certificate_recommendations', {}).get('recommendations', [])
    
    if not course_recs and not cert_recs:
        st.warning("⚠️ No recommendations available for this company.")
        return
    
    # Two column layout for selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##  Available Courses")
        if course_recs:
            for i, course in enumerate(course_recs):
                course_id = f"course_{i}"
                course_name = get_course_field(course, 'course_name', ['name', 'title', 'course_title'])
                course_code = get_course_field(course, 'course_code', ['code', 'course_id'])
                similarity = parse_mongo_number(course.get('similarity_score', 0))
                description = get_course_description(course)
                
                # Check if this course is selected
                is_selected = course_id in st.session_state.selected_courses
                card_class = "selected" if is_selected else ""
                
                # Course selection checkbox with proper credit tracking
                checkbox_key = f"course_check_{i}"
                
                # Get current credits before checkbox
                current_credits_before = calculate_credits()
                
                selected = st.checkbox(
                    f"**{course_name}** ({course_code})",
                    value=is_selected,
                    key=checkbox_key,
                    disabled=(current_credits_before >= max_credits and not is_selected)
                )
                
                # Update selection state immediately
                if selected and course_id not in st.session_state.selected_courses:
                    st.session_state.selected_courses.add(course_id)
                    update_credits()  # Update immediately
                    st.rerun()  # Refresh UI
                elif not selected and course_id in st.session_state.selected_courses:
                    st.session_state.selected_courses.remove(course_id)
                    update_credits()  # Update immediately
                    st.rerun()  # Refresh UI
                
                # Display course info with description
                with st.container():
                    st.markdown(f"""
                    <div class="item-card {card_class}">
                        <p><strong>Match:</strong> {similarity:.1%}</p>
                        <p><strong>Type:</strong> {course.get('course_type', 'N/A')}</p>
                        <p><strong>Credits:</strong> 3</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show description
                    st.markdown(f"""
                    <div class="course-description">
                        <strong>Description:</strong> {description[:150]}{'...' if len(description) > 150 else ''}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No courses available for this company.")
    
    with col2:
        st.markdown("##  Available Certificates")
        if cert_recs:
            for i, cert in enumerate(cert_recs):
                cert_id = f"cert_{i}"
                cert_name = get_course_field(cert, 'course_name', ['name', 'title', 'certificate_name'])
                similarity = parse_mongo_number(cert.get('similarity_score', 0))
                description = get_course_description(cert)
                
                # Check if this certificate is selected
                is_selected = cert_id in st.session_state.selected_certificates
                card_class = "selected" if is_selected else ""
                
                # Certificate selection checkbox with proper credit tracking
                checkbox_key = f"cert_check_{i}"
                
                # Get current credits before checkbox
                current_credits_before = calculate_credits()
                
                selected = st.checkbox(
                    f"**{cert_name}**",
                    value=is_selected,
                    key=checkbox_key,
                    disabled=(current_credits_before >= max_credits and not is_selected)
                )
                
                # Update selection state immediately
                if selected and cert_id not in st.session_state.selected_certificates:
                    st.session_state.selected_certificates.add(cert_id)
                    update_credits()  # Update immediately
                    st.rerun()  # Refresh UI
                elif not selected and cert_id in st.session_state.selected_certificates:
                    st.session_state.selected_certificates.remove(cert_id)
                    update_credits()  # Update immediately
                    st.rerun()  # Refresh UI
                
                # Display certificate info with description
                with st.container():
                    st.markdown(f"""
                    <div class="item-card {card_class}">
                        <p><strong>Match:</strong> {similarity:.1%}</p>
                        <p><strong>Credits:</strong> 3</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show description
                    st.markdown(f"""
                    <div class="course-description">
                        <strong>Description:</strong> {description[:150]}{'...' if len(description) > 150 else ''}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No certificates available for this company.")
    
    # Proposal Summary
    if st.session_state.selected_courses or st.session_state.selected_certificates:
        st.markdown("## 📋 Proposal Summary")
        
        # Refresh current credits for accurate display
        current_credits = calculate_credits()
        
        selected_course_details = []
        selected_cert_details = []
        
        # Get selected course details
        for i, course in enumerate(course_recs):
            if f"course_{i}" in st.session_state.selected_courses:
                selected_course_details.append(course)
        
        # Get selected certificate details
        for i, cert in enumerate(cert_recs):
            if f"cert_{i}" in st.session_state.selected_certificates:
                selected_cert_details.append(cert)
        
        total_items = len(selected_course_details) + len(selected_cert_details)
        
        st.markdown(f"""
        <div class="proposal-summary">
            <h3 style="color: #800020; margin-top: 0;">Proposal for {company_name}</h3>
            <p><strong>Total Items:</strong> {total_items}</p>
            <p><strong>Total Credits:</strong> {current_credits}</p>
            <p><strong>Courses Selected:</strong> {len(selected_course_details)}</p>
            <p><strong>Certificates Selected:</strong> {len(selected_cert_details)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display selected items with descriptions
        if selected_course_details:
            st.markdown("### Selected Courses:")
            for course in selected_course_details:
                course_name = get_course_field(course, 'course_name', ['name', 'title'])
                course_code = get_course_field(course, 'course_code', ['code', 'course_id'])
                description = get_course_description(course)
                st.markdown(f"• **{course_name}** ({course_code}) - 3 credits")
                st.markdown(f"  _{description[:100]}{'...' if len(description) > 100 else ''}_")
        
        if selected_cert_details:
            st.markdown("### Selected Certificates:")
            for cert in selected_cert_details:
                cert_name = get_course_field(cert, 'course_name', ['name', 'title', 'certificate_name'])
                description = get_course_description(cert)
                st.markdown(f"• **{cert_name}** - 3 credits")
                st.markdown(f"  _{description[:100]}{'...' if len(description) > 100 else ''}_")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All", key="clear_all"):
                st.session_state.selected_courses = set()
                st.session_state.selected_certificates = set()
                st.session_state.total_credits = 0
                update_credits()
                st.rerun()
        
        with col2:
            if current_credits <= max_credits:
                if st.button("📄 Generate Professional Proposal", key="generate_proposal"):
                    
                    # Show proposal preview with Stevens styling
                    st.markdown(f"""
                    <div style="background: white; padding: 2rem; border-radius: 15px; border: 2px solid #800020; margin: 1rem 0;">
                        <div style="text-align: center; margin-bottom: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; border: 2px solid #800020;">
                            <div style="font-size: 1.8rem; font-weight: bold; color: #800020; margin-bottom: 0.5rem;">🎓 STEVENS INSTITUTE OF TECHNOLOGY</div>
                            <div style="font-size: 1.2rem; color: #666666; margin-bottom: 1rem;">College of Professional Education</div>
                            <div style="font-size: 1.4rem; font-weight: bold; color: #800020;">Stevens Professional Education Partnership</div>
                            <div style="color: #666666; margin-top: 0.5rem;">Customized Learning Solutions for {company_name}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Generate PDF with professional structure
                    try:
                        import requests
                        from reportlab.lib.pagesizes import letter, A4
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                        from reportlab.lib.units import inch
                        from reportlab.lib import colors
                        from reportlab.lib.enums import TA_LEFT, TA_CENTER
                        
                        # Create PDF buffer
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                        
                        # Container for PDF elements
                        story = []
                        
                        # Define styles
                        styles = getSampleStyleSheet()
                        
                        # Custom Stevens styles
                        stevens_title = ParagraphStyle(
                            'StevensTitle',
                            parent=styles['Heading1'],
                            fontSize=22,
                            textColor=colors.Color(0.5, 0, 0.125),
                            spaceAfter=12,
                            alignment=TA_LEFT
                        )
                        
                        stevens_subtitle = ParagraphStyle(
                            'StevensSubtitle',
                            parent=styles['Normal'],
                            fontSize=14,
                            textColor=colors.grey,
                            spaceAfter=20,
                            alignment=TA_LEFT
                        )
                        
                        stevens_heading = ParagraphStyle(
                            'StevensHeading',
                            parent=styles['Heading2'],
                            fontSize=16,
                            textColor=colors.Color(0.5, 0, 0.125),
                            spaceBefore=20,
                            spaceAfter=12,
                            alignment=TA_LEFT
                        )
                        
                        stevens_subheading = ParagraphStyle(
                            'StevensSubheading',
                            parent=styles['Heading3'],
                            fontSize=14,
                            textColor=colors.Color(0.5, 0, 0.125),
                            spaceBefore=15,
                            spaceAfter=8,
                            alignment=TA_LEFT
                        )
                        
                        bullet_style = ParagraphStyle(
                            'BulletStyle',
                            parent=styles['Normal'],
                            fontSize=11,
                            leftIndent=20,
                            spaceAfter=6,
                            alignment=TA_LEFT
                        )
                        
                        course_detail_style = ParagraphStyle(
                            'CourseDetailStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            leftIndent=30,
                            spaceAfter=4,
                            textColor=colors.Color(0.3, 0.3, 0.3),
                            alignment=TA_LEFT
                        )
                        
                        highlight_style = ParagraphStyle(
                            'HighlightStyle',
                            parent=styles['Normal'],
                            fontSize=12,
                            textColor=colors.Color(0.5, 0, 0.125),
                            backColor=colors.Color(1, 0.98, 0.9),
                            borderColor=colors.Color(0.5, 0, 0.125),
                            borderWidth=1,
                            borderPadding=15,
                            spaceBefore=15,
                            spaceAfter=15,
                            alignment=TA_LEFT
                        )
                        
                        # Header
                        story.append(Paragraph("Stevens Professional Education Partnership", stevens_title))
                        story.append(Paragraph(f"Customized Learning Solutions for {company_name}", stevens_subtitle))
                        story.append(Spacer(1, 20))
                        
                        # Executive Summary
                        executive_summary = f"""Stevens Institute of Technology's College of Professional Education presents a tailored learning solution for {company_name}. This proposal outlines a comprehensive educational pathway designed to enhance your organization's capabilities through targeted skill development in key areas aligned with your industry requirements."""
                        story.append(Paragraph("Executive Summary", stevens_heading))
                        story.append(Paragraph(executive_summary, highlight_style))
                        story.append(Spacer(1, 20))
                        
                        # Recommended Learning Path
                        story.append(Paragraph("Recommended Learning Path", stevens_heading))
                        
                        # Selected Courses Section
                        if selected_course_details:
                            story.append(Paragraph("Professional Courses", stevens_subheading))
                            story.append(Paragraph("The following courses have been selected based on alignment with your organizational needs:", bullet_style))
                            story.append(Spacer(1, 10))
                            
                            for course in selected_course_details:
                                course_name = get_course_field(course, 'course_name', ['name', 'title'])
                                course_code = get_course_field(course, 'course_code', ['code', 'course_id'])
                                description = get_course_description(course)
                                similarity = parse_mongo_number(course.get('similarity_score', 0))
                                
                                if course_code != 'N/A':
                                    story.append(Paragraph(f"<b>{course_name} ({course_code})</b> - 3 Credits", bullet_style))
                                else:
                                    story.append(Paragraph(f"<b>{course_name}</b> - 3 Credits", bullet_style))
                                
                                story.append(Paragraph(f"Description: {description}", course_detail_style))
                                story.append(Paragraph(f"Organizational Match: {similarity:.1%}", course_detail_style))
                                story.append(Spacer(1, 8))
                        
                        # Selected Certificates Section
                        if selected_cert_details:
                            story.append(Paragraph("Professional Certificates", stevens_subheading))
                            story.append(Paragraph("The following certificates provide specialized expertise in targeted areas:", bullet_style))
                            story.append(Spacer(1, 10))
                            
                            for cert in selected_cert_details:
                                cert_name = get_course_field(cert, 'course_name', ['name', 'title'])
                                description = get_course_description(cert)
                                similarity = parse_mongo_number(cert.get('similarity_score', 0))
                                
                                story.append(Paragraph(f"<b>{cert_name}</b> - 3 Credits", bullet_style))
                                story.append(Paragraph(f"Description: {description}", course_detail_style))
                                story.append(Paragraph(f"Organizational Match: {similarity:.1%}", course_detail_style))
                                story.append(Spacer(1, 8))
                        
                        # Program Benefits
                        story.append(Paragraph("Program Benefits", stevens_heading))
                        
                        benefits = [
                            f"<b>Stackable Credits:</b> All {current_credits} credits can be applied toward relevant master's degree programs at Stevens.",
                            f"<b>Professional Recognition:</b> Industry-recognized credentials from a top-tier technological university.",
                            f"<b>Flexible Delivery:</b> Online and hybrid options to accommodate {company_name}'s scheduling needs.",
                            f"<b>Expert Faculty:</b> Learn from industry practitioners and academic thought leaders.",
                            f"<b>Networking Opportunities:</b> Connect with professionals across various industries and specializations."
                        ]
                        
                        for benefit in benefits:
                            story.append(Paragraph(f"• {benefit}", bullet_style))
                        
                        story.append(Spacer(1, 20))
                        
                        # Implementation Timeline
                        story.append(Paragraph("Implementation Timeline", stevens_heading))
                        
                        timeline_items = [
                            "Program customization and enrollment: 2-3 weeks",
                            f"Course delivery timeline: 9-12 months for {total_items} courses/certificates",
                            "Ongoing support and progress monitoring throughout the program",
                            "Certificate completion and credit documentation: Upon successful completion"
                        ]
                        
                        for item in timeline_items:
                            story.append(Paragraph(f"• {item}", bullet_style))
                        
                        story.append(Spacer(1, 30))
                        
                        # Proposal Summary Box
                        summary_data = [
                            ["Proposal Summary", ""],
                            ["Company:", company_data.get('company_name', 'N/A')],
                            ["Industry:", company_data.get('industry', 'N/A')],
                            ["Total Credits:", f"{current_credits}"],
                            ["Professional Courses:", str(len(selected_course_details))],
                            ["Professional Certificates:", str(len(selected_cert_details))],
                            ["Estimated Duration:", f"{total_items * 3}-{total_items * 4} months"],
                            ["Proposal Date:", datetime.now().strftime("%B %d, %Y")]
                        ]
                        
                        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
                        summary_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.5, 0, 0.125)),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 14),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 11),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.5, 0, 0.125)),
                            ('SPAN', (0, 0), (-1, 0)),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ]))
                        story.append(summary_table)
                        
                        # Next Steps
                        story.append(Spacer(1, 20))
                        story.append(Paragraph("Next Steps", stevens_heading))
                        
                        next_steps = [
                            "Review and approve this customized learning proposal",
                            "Schedule a consultation to discuss implementation details",
                            "Finalize enrollment and payment arrangements",
                            "Begin your professional development journey with Stevens"
                        ]
                        
                        for step in next_steps:
                            story.append(Paragraph(f"• {step}", bullet_style))
                        
                        # Footer
                        story.append(Spacer(1, 30))
                        footer_style = ParagraphStyle(
                            'FooterStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.grey,
                            alignment=TA_CENTER
                        )
                        story.append(Paragraph("Stevens Institute of Technology - College of Professional Education", footer_style))
                        story.append(Paragraph("Professional Development Partnerships", footer_style))
                        story.append(Paragraph(f"Prepared for: {company_name} | Generated: {datetime.now().strftime('%B %d, %Y')}", footer_style))
                        
                        # Build PDF
                        doc.build(story)
                        
                        # Get PDF data
                        pdf_data = buffer.getvalue()
                        buffer.close()
                        
                        # Download button for PDF
                        st.download_button(
                            label="📄 Download Professional Proposal (PDF)",
                            data=pdf_data,
                            file_name=f"Stevens_Professional_Learning_Proposal_{company_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                        
                    except ImportError:
                        st.error("📋 PDF generation requires reportlab library. Please install it: `pip install reportlab`")
                        
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        st.info("Please try again or contact support if the issue persists.")
            else:
                st.button("📄 Generate Professional Proposal", disabled=True, help="Reduce credits to 36 or less")

# FIXED: Course detail page with improved data handling
def show_course_recommendations(company_data):
    st.markdown("""
    <style>
    .course-header {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: #800020;
        border: 2px solid #800020;
    }
    .course-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
        color: #800020;
    }
    .course-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
        color: #800020;
    }
    .course-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #800020;
    }
    .course-details {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.5rem;
        border-left: 4px solid #800020;
    }
    .similarity-badge {
        background: #800020;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .debug-info {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Company", key="course_back"):
            st.session_state.current_view = "company_detail"
            st.rerun()
    with col2:
        if st.button("🏠 Dashboard", key="course_home"):
            st.session_state.current_view = "dashboard"
            st.rerun()
    
    # Header
    company_name = company_data.get('company_name', 'Unknown Company')
    st.markdown(f"""
    <div class="course-header">
        <h1> Course Recommendations</h1>
        <p>Build your foundation with these recommended courses for {company_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get course recommendations
    course_recs = company_data.get('course_recommendations', {}).get('recommendations', [])
    
    if not course_recs:
        st.warning("⚠️ No course recommendations available for this company.")
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #666666;">
            <h4>🚧 Missing Course Recommendations</h4>
            <p>This company profile doesn't contain course recommendations. The recommendations need to be generated and added to the database.</p>
            <p><strong>Available company data:</strong></p>
            <ul>
                <li>Company Name: {}</li>
                <li>Industry: {}</li>
                <li>Size: {}</li>
                <li>Contact: {}</li>
            </ul>
        </div>
        """.format(
            company_data.get('company_name', 'N/A'),
            company_data.get('industry', 'N/A'),
            company_data.get('company_size', 'N/A'),
            company_data.get('contact_email', 'N/A')
        ), unsafe_allow_html=True)
        return
    

    
    # Categorize courses more meaningfully
    technical_courses = [course for course in course_recs if course.get('course_type', '').lower() == 'technical']
    mixed_courses = [course for course in course_recs if course.get('course_type', '').lower() == 'mixed']
    other_courses = [course for course in course_recs if course.get('course_type', '').lower() not in ['technical', 'mixed']]
    
    # Combine mixed and other courses for "Advanced Courses"
    advanced_courses = mixed_courses + other_courses
    
    # Two column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="course-section">
            <h2> Technical Courses</h2>
            <p style="color: #666666; margin: 0.5rem 0;">Pure technical and programming courses</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not technical_courses:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #666666;">
                <p style="margin: 0; color: #333333;">
                    <strong>ℹ️ No Technical Courses Found</strong><br>
                    No courses with course_type = "technical" in the recommendations.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        for i, course in enumerate(technical_courses):
            # FIXED: Use improved field extraction
            course_name = get_course_field(course, 'course_name', ['name', 'title', 'course_title'])
            course_code = get_course_field(course, 'course_code', ['code', 'course_id'])
            description = get_course_description(course)
            similarity = parse_mongo_number(course.get('similarity_score', 0))
            best_week = course.get('best_week', 'N/A')
            module_title = course.get('module_title', 'N/A')
            rank = parse_mongo_number(course.get('rank', 0))
            
            # Create expandable course item
            with st.expander(f" {course_name}", expanded=False):
                # FIXED: Show data quality indicator
                missing_fields = []
                if course_code == 'N/A':
                    missing_fields.append('course_code')
                if len(description) < 50:
                    missing_fields.append('description')
                
                if missing_fields:
                    st.markdown(f"""
                    <div class="debug-info">
                        <strong>⚠️ Data Quality Note:</strong> Some fields are missing or incomplete: {', '.join(missing_fields)}<br>
                        <small>Using intelligent fallbacks to provide complete information.</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="course-details">
                    <p><strong>Course Code:</strong> {course_code}</p>
                    <p><strong>Description:</strong> {description}</p>
                    <p><strong>Type:</strong> {course.get('course_type', 'N/A')}</p>
                    <p><strong>Best Week:</strong> {best_week}</p>
                    <p><strong>Module:</strong> {module_title}</p>
                    <p><strong>Rank:</strong> #{rank}</p>
                    <p><strong>Credits:</strong> 3</p>
                    <div style="margin-top: 1rem;">
                        <span class="similarity-badge">Match: {similarity:.1%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Learning outcomes
                learning_outcomes = course.get('learning_outcomes', [])
                if learning_outcomes:
                    st.markdown("**Learning Outcomes:**")
                    for outcome in learning_outcomes:
                        st.markdown(f"• {outcome}")
                else:
                    st.info("Learning outcomes will be provided during course enrollment.")
    
    with col2:
        st.markdown("""
        <div class="course-section">
            <h2> Mixed Courses</h2>
            <p style="color: #666666; margin: 0.5rem 0;">Mixed and advanced courses</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not advanced_courses:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #666666;">
                <p style="margin: 0; color: #333333;">
                    <strong>ℹ️ No Mixed Courses Found</strong><br>
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        for i, course in enumerate(advanced_courses):
            # FIXED: Use improved field extraction
            course_name = get_course_field(course, 'course_name', ['name', 'title', 'course_title'])
            course_code = get_course_field(course, 'course_code', ['code', 'course_id'])
            description = get_course_description(course)
            similarity = parse_mongo_number(course.get('similarity_score', 0))
            best_week = course.get('best_week', 'N/A')
            module_title = course.get('module_title', 'N/A')
            rank = parse_mongo_number(course.get('rank', 0))
            course_type = course.get('course_type', 'N/A')
            
            # Use different icon based on course type
            icon = "🎯" if course_type == "mixed" else "📚"
            
            # Create expandable course item
            with st.expander(f" {course_name}", expanded=False):
                # FIXED: Show data quality indicator
                missing_fields = []
                if course_code == 'N/A':
                    missing_fields.append('course_code')
                if len(description) < 50:
                    missing_fields.append('description')
                
                if missing_fields:
                    st.markdown(f"""
                    <div class="debug-info">
                        <strong>⚠️ Data Quality Note:</strong> Some fields are missing or incomplete: {', '.join(missing_fields)}<br>
                        <small>Using intelligent fallbacks to provide complete information.</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="course-details">
                    <p><strong>Course Code:</strong> {course_code}</p>
                    <p><strong>Description:</strong> {description}</p>
                    <p><strong>Type:</strong> {course_type}</p>
                    <p><strong>Best Week:</strong> {best_week}</p>
                    <p><strong>Module:</strong> {module_title}</p>
                    <p><strong>Rank:</strong> #{rank}</p>
                    <p><strong>Credits:</strong> 3</p>
                    <div style="margin-top: 1rem;">
                        <span class="similarity-badge">Match: {similarity:.1%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Learning outcomes
                learning_outcomes = course.get('learning_outcomes', [])
                if learning_outcomes:
                    st.markdown("**Learning Outcomes:**")
                    for outcome in learning_outcomes:
                        st.markdown(f"• {outcome}")
                else:
                    st.info("Learning outcomes will be provided during course enrollment.")
    
    # Action button to create proposal
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(" Create Proposal with These Courses", key="courses_to_proposal"):
            st.session_state.current_view = "proposal"
            # Clear any existing selections
            st.session_state.selected_courses = set()
            st.session_state.selected_certificates = set()
            st.session_state.total_credits = 0
            st.rerun()

# FIXED: Certificate detail page with improved data handling
def show_certificate_recommendations(company_data):
    st.markdown("""
    <style>
    .cert-header {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: #800020;
        border: 2px solid #800020;
    }
    .cert-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
        color: #800020;
    }
    .cert-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
        color: #800020;
    }
    .cert-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #800020;
    }
    .cert-details {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.5rem;
        border-left: 4px solid #800020;
    }
    .cert-similarity-badge {
        background: #800020;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .debug-info {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Company", key="cert_back"):
            st.session_state.current_view = "company_detail"
            st.rerun()
    with col2:
        if st.button("Dashboard", key="cert_home"):
            st.session_state.current_view = "dashboard"
            st.rerun()
    
    # Header
    company_name = company_data.get('company_name', 'Unknown Company')
    st.markdown(f"""
    <div class="cert-header">
        <h1> Certificate Recommendations</h1>
        <p>Enhance your expertise with these specialized certificates for {company_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get certificate recommendations
    cert_recs = company_data.get('certificate_recommendations', {}).get('recommendations', [])
    
    if not cert_recs:
        st.warning("⚠️ No certificate recommendations available for this company.")
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #666666;">
            <h4>🚧 Missing Certificate Recommendations</h4>
            <p>This company profile doesn't contain certificate recommendations. The recommendations need to be generated and added to the database.</p>
            <p><strong>Available company data:</strong></p>
            <ul>
                <li>Company Name: {}</li>
                <li>Industry: {}</li>
                <li>Size: {}</li>
                <li>Contact: {}</li>
            </ul>
        </div>
        """.format(
            company_data.get('company_name', 'N/A'),
            company_data.get('industry', 'N/A'),
            company_data.get('company_size', 'N/A'),
            company_data.get('contact_email', 'N/A')
        ), unsafe_allow_html=True)
        return
    

    # Split certificates into two categories
    mid_point = len(cert_recs) // 2
    specialized_certs = cert_recs[:mid_point] if cert_recs else []
    professional_certs = cert_recs[mid_point:] if cert_recs else []
    
    # Two column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="cert-section">
            <h2> Specialized Certificates</h2>
        </div>
        """, unsafe_allow_html=True)
        
        for i, cert in enumerate(specialized_certs):
            # FIXED: Use improved field extraction
            cert_name = get_course_field(cert, 'course_name', ['name', 'title', 'certificate_name'])
            description = get_course_description(cert)
            requirements = cert.get('course_requirements', 'No requirements listed')
            similarity = parse_mongo_number(cert.get('similarity_score', 0))
            rank = parse_mongo_number(cert.get('rank', 0))
            
            # Parse requirements if they're in JSON format
            req_list = parse_course_requirements(requirements)
            
            # Create expandable certificate item
            with st.expander(f" {cert_name}", expanded=False):
                # FIXED: Show data quality indicator
                if len(description) < 50:
                    st.markdown(f"""
                    <div class="debug-info">
                        <strong>⚠️ Data Quality Note:</strong> Description was enhanced using available course data.<br>
                        <small>Original description may have been incomplete or missing.</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="cert-details">
                    <p><strong>Description:</strong> {description}</p>
                    <p><strong>Rank:</strong> #{rank}</p>
                    <p><strong>Credits:</strong> 3</p>
                    <div style="margin-top: 1rem;">
                        <span class="cert-similarity-badge">Match: {similarity:.1%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display requirements
                if req_list and req_list[0] != 'No requirements listed':
                    st.markdown("**Requirements:**")
                    for req in req_list:
                        st.markdown(f"• {req}")
                else:
                    st.info("Specific requirements will be provided during enrollment.")
                        
    with col2:
        st.markdown("""
        <div class="cert-section">
            <h2> Professional Certificates</h2>
        </div>
        """, unsafe_allow_html=True)
        
        for i, cert in enumerate(professional_certs):
            # FIXED: Use improved field extraction
            cert_name = get_course_field(cert, 'course_name', ['name', 'title', 'certificate_name'])
            description = get_course_description(cert)
            requirements = cert.get('course_requirements', 'No requirements listed')
            similarity = parse_mongo_number(cert.get('similarity_score', 0))
            rank = parse_mongo_number(cert.get('rank', 0))
            
            # Parse requirements if they're in JSON format
            req_list = parse_course_requirements(requirements)
            
            # Create expandable certificate item
            with st.expander(f" {cert_name}", expanded=False):
                # FIXED: Show data quality indicator
                if len(description) < 50:
                    st.markdown(f"""
                    <div class="debug-info">
                        <strong>⚠️ Data Quality Note:</strong> Description was enhanced using available course data.<br>
                        <small>Original description may have been incomplete or missing.</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="cert-details">
                    <p><strong>Description:</strong> {description}</p>
                    <p><strong>Rank:</strong> #{rank}</p>
                    <p><strong>Credits:</strong> 3</p>
                    <div style="margin-top: 1rem;">
                        <span class="cert-similarity-badge">Match: {similarity:.1%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display requirements
                if req_list and req_list[0] != 'No requirements listed':
                    st.markdown("**Requirements:**")
                    for req in req_list:
                        st.markdown(f"• {req}")
                else:
                    st.info("Specific requirements will be provided during enrollment.")
    
    # Action button to create proposal
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📋 Create Proposal with These Certificates", key="certs_to_proposal"):
            st.session_state.current_view = "proposal"
            # Clear any existing selections
            st.session_state.selected_courses = set()
            st.session_state.selected_certificates = set()
            st.session_state.total_credits = 0
            st.rerun()

# Main dashboard
def main():
    st.set_page_config(
        page_title="Stevens Institute of Technology - Learning Dashboard",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "dashboard"
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = None
    if 'show_data_status' not in st.session_state:
        st.session_state.show_data_status = False
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = 'desc'  # 'desc' for newest first, 'asc' for oldest first
    
    # Custom CSS for Stevens Professional Branding - Toned Down
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Stevens Color Palette - Toned Down */
    :root {
        --stevens-burgundy: #800020;
        --stevens-grey: #666666;
        --stevens-grey-light: #f8f9fa;
        --stevens-grey-dark: #333333;
        --stevens-white: #ffffff;
    }
    
    /* Global Styles */
    .main .block-container {
        padding-top: 2rem;
        font-family: 'Inter', sans-serif;
        max-width: 100%;
    }
    
    /* Hide sidebar completely */
    .css-1d391kg {
        display: none;
    }
    
    .css-1544g2n {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Main Header */
    .main-header {
        background: var(--stevens-burgundy);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(128, 0, 32, 0.3);
    }
    
    .main-header h1 {
        color: var(--stevens-white);
        text-align: center;
        margin: 0;
        font-weight: 700;
        font-size: 2.5rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .main-header .subtitle {
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        font-weight: 400;
    }
    
    /* Metric Cards */
    .metric-card {
        background: var(--stevens-white);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--stevens-burgundy);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
    }
    
    .metric-card h3 {
        color: var(--stevens-grey-dark);
        margin: 0 0 1rem 0;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card h2 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--stevens-burgundy);
    }
    
    .metric-card p {
        color: var(--stevens-grey);
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Section Headers */
    .section-header {
        background: var(--stevens-grey-light);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 5px solid var(--stevens-burgundy);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .section-header h2 {
        color: var(--stevens-burgundy);
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    /* Companies Overview Section - Burgundy Background */
    .companies-overview {
        background: var(--stevens-burgundy);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .companies-overview h2 {
        color: var(--stevens-white);
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    /* Company Cards */
    .company-card {
        background: var(--stevens-white);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid var(--stevens-burgundy);
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .company-card:hover {
        transform: translateX(5px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12);
    }
    
    .company-card h3 {
        color: var(--stevens-burgundy);
        margin: 0 0 1rem 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .company-card p {
        color: var(--stevens-grey-dark);
        margin: 0.5rem 0;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    .company-card strong {
        color: var(--stevens-burgundy);
        font-weight: 600;
    }
    
    /* Professional Buttons */
    .stButton > button {
        background: var(--stevens-burgundy) !important;
        color: var(--stevens-white) !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(128, 0, 32, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(128, 0, 32, 0.4) !important;
        background: #a0002a !important;
    }
    
    .stButton > button:disabled {
        background: var(--stevens-grey) !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label {
        font-weight: 600 !important;
        color: var(--stevens-burgundy) !important;
    }
    
    /* Progress Bars */
    .progress-bar {
        background: rgba(102, 102, 102, 0.2);
        border-radius: 10px;
        height: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: var(--stevens-burgundy);
        transition: width 0.6s ease;
        border-radius: 10px;
    }
    
    /* Similarity Badges */
    .similarity-badge {
        background: var(--stevens-burgundy);
        color: var(--stevens-white);
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(128, 0, 32, 0.3);
    }
    
    /* Sort Button Styling - UPDATED */
    .stButton > button[data-testid="sort_desc"],
    .stButton > button[data-testid="sort_asc"] {
        background: var(--stevens-white) !important;
        color: var(--stevens-burgundy) !important;
        border: 2px solid var(--stevens-burgundy) !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        box-shadow: 0 2px 8px rgba(128, 0, 32, 0.1) !important;
    }
    
    .stButton > button[data-testid="sort_desc"]:hover,
    .stButton > button[data-testid="sort_asc"]:hover {
        background: var(--stevens-burgundy) !important;
        color: var(--stevens-white) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(128, 0, 32, 0.3) !important;
    }
    
    /* Comprehensive Expander Styling */
    
    /* All possible expander header selectors */
    .streamlit-expanderHeader,
    div[data-testid="expander"] > div:first-child,
    .streamlit-expander > div[role="button"],
    .streamlit-expander summary,
    [data-testid="expander"] > div:first-child,
    .element-container > div > div > div[role="button"],
    .stExpander > div > div > div[role="button"],
    .stExpander summary,
    details > summary {
        background: var(--stevens-white) !important;
        border: 1px solid var(--stevens-burgundy) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        color: var(--stevens-burgundy) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        font-size: 1.1rem !important;
        letter-spacing: 0.3px !important;
    }
    
    /* Hover states for all expander headers */
    .streamlit-expanderHeader:hover,
    div[data-testid="expander"] > div:first-child:hover,
    .streamlit-expander > div[role="button"]:hover,
    .streamlit-expander summary:hover,
    [data-testid="expander"] > div:first-child:hover,
    .element-container > div > div > div[role="button"]:hover,
    .stExpander > div > div > div[role="button"]:hover,
    .stExpander summary:hover,
    details > summary:hover {
        background: var(--stevens-grey-light) !important;
        border-color: var(--stevens-burgundy) !important;
        color: var(--stevens-burgundy) !important;
    }
    
    /* All text inside expander headers */
    .streamlit-expanderHeader *,
    div[data-testid="expander"] > div:first-child *,
    .streamlit-expander > div[role="button"] *,
    .streamlit-expander summary *,
    [data-testid="expander"] > div:first-child *,
    .element-container > div > div > div[role="button"] *,
    .stExpander > div > div > div[role="button"] *,
    .stExpander summary *,
    details > summary * {
        color: var(--stevens-burgundy) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Expander Content */
    .streamlit-expanderContent,
    div[data-testid="expander"] > div:last-child,
    .streamlit-expander > div:last-child,
    .stExpander > div:last-child,
    details > div:last-child {
        background: var(--stevens-white) !important;
        border: 1px solid var(--stevens-burgundy) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* Professional Info Boxes */
    .info-box {
        background: var(--stevens-grey-light);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid var(--stevens-burgundy);
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
    }
    
    .warning-box {
        background: #f8f9fa;
        border-left-color: var(--stevens-grey);
    }
    
    .error-box {
        background: #f8f9fa;
        border-left-color: var(--stevens-grey);
    }
    
    .success-box {
        background: #f8f9fa;
        border-left-color: var(--stevens-burgundy);
    }
    
    /* Footer */
    .footer {
        background: var(--stevens-burgundy);
        color: var(--stevens-white);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 3rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(128, 0, 32, 0.3);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .metric-card {
            margin-bottom: 1rem;
        }
        
        .course-header h1, .cert-header h1 {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Route to different views - UPDATED routing
    if st.session_state.current_view == "company_detail":
        show_company_detail(st.session_state.selected_company)
        return
    elif st.session_state.current_view == "courses":
        show_course_recommendations(st.session_state.selected_company)
        return
    elif st.session_state.current_view == "certificates":
        show_certificate_recommendations(st.session_state.selected_company)
        return
    elif st.session_state.current_view == "proposal":
        show_proposal_generator(st.session_state.selected_company)
        return
    
    # Dashboard view
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Stevens ProEdge</h1>
        <p class="subtitle">Company Learning Recommendations Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load companies data
    companies_data = get_companies_data()
    
    if not companies_data:
        st.error("No companies data found. Please check your MongoDB connection.")
        return
    
    # Filters and controls row - UPDATED with recommendations filter
    col_filter1, col_filter2, col_filter3, col_sort, col_btn1, col_btn2 = st.columns(6)

    with col_filter1:
    # Industry filter
        industries = list(set([comp.get('industry', 'Unknown') for comp in companies_data]))
        selected_industry = st.selectbox("Industry", ["All"] + industries)

    with col_filter2:
        # Company size filter
        company_sizes = list(set([comp.get('company_size', 'Unknown') for comp in companies_data]))
        selected_size = st.selectbox(" Company Size", ["All"] + company_sizes)

    with col_filter3:
        # Recommendations filter - NEW FILTER
        recommendations_options = ["All", "With Recommendations", "Without Recommendations"]
        selected_recommendations = st.selectbox(" Recommendations", recommendations_options)

    with col_sort:
        # Sort button
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        current_sort_label = " Newest First" if st.session_state.sort_order == 'desc' else " Oldest First"
        if st.button(current_sort_label, key="sort_timestamp", help="Click to toggle sort order"):
            # Toggle sort order
            st.session_state.sort_order = 'asc' if st.session_state.sort_order == 'desc' else 'desc'
            st.rerun()

    with col_btn1:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    with col_btn2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        if st.button("🔍 Show Data Status"):
            st.session_state.show_data_status = not st.session_state.get('show_data_status', False)

    # Filter companies based on selections - UPDATED to include recommendations filter
    filtered_companies = companies_data
    if selected_industry != "All":
        filtered_companies = [comp for comp in filtered_companies if comp.get('industry') == selected_industry]
    if selected_size != "All":
        filtered_companies = [comp for comp in filtered_companies if comp.get('company_size') == selected_size]

    # NEW: Apply recommendations filter
    if selected_recommendations == "With Recommendations":
        filtered_companies = [comp for comp in filtered_companies if 'course_recommendations' in comp or 'certificate_recommendations' in comp]
    elif selected_recommendations == "Without Recommendations":
        filtered_companies = [comp for comp in filtered_companies if 'course_recommendations' not in comp and 'certificate_recommendations' not in comp]
    
    # Show data status if toggled
    if st.session_state.get('show_data_status', False):
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.markdown("""
            <div class="info-box">
                <h4 style="color: var(--stevens-burgundy); margin-top: 0;">✅ Data Status</h4>
                <p>Loaded {} companies</p>
                <p>Sort Order: {}</p>
            </div>
            """.format(len(companies_data), "Newest First" if st.session_state.sort_order == 'desc' else "Oldest First"), unsafe_allow_html=True)
        
        with col_status2:
            # Show database breakdown
            db_counts = {}
            for comp in companies_data:
                db = comp.get('_source_db', 'Unknown')
                db_counts[db] = db_counts.get(db, 0) + 1
            
            st.markdown("""
            <div class="info-box">
                <h4 style="color: var(--stevens-burgundy); margin-top: 0;">Database Distribution</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for db, count in db_counts.items():
                st.write(f"• {db}: {count} companies")
        
        with col_status3:
            # Show recommendation status
            companies_with_recs = len([comp for comp in companies_data if 'course_recommendations' in comp or 'certificate_recommendations' in comp])
            
            st.markdown("""
            <div class="info-box">
                <h4 style="color: var(--stevens-burgundy); margin-top: 0;">📋 Recommendation Status</h4>
                <p>• With recommendations: {}</p>
                <p>• Without recommendations: {}</p>
            </div>
            """.format(companies_with_recs, len(companies_data) - companies_with_recs), unsafe_allow_html=True)
    
    # Sort companies by timestamp - NEW FEATURE
    try:
        companies_data.sort(key=get_company_timestamp, reverse=(st.session_state.sort_order == 'desc'))
    except Exception as e:
        st.warning(f"⚠️ Warning: Could not sort companies by timestamp: {e}")
    
    # Filter companies based on selections
    filtered_companies = companies_data
    if selected_industry != "All":
        filtered_companies = [comp for comp in filtered_companies if comp.get('industry') == selected_industry]
    if selected_size != "All":
        filtered_companies = [comp for comp in filtered_companies if comp.get('company_size') == selected_size]
    
    # Apply recommendations filter
    if selected_recommendations == "With Recommendations":
        filtered_companies = [comp for comp in filtered_companies if 'course_recommendations' in comp or 'certificate_recommendations' in comp]
    elif selected_recommendations == "Without Recommendations":
        filtered_companies = [comp for comp in filtered_companies if 'course_recommendations' not in comp and 'certificate_recommendations' not in comp]
    
    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Total Companies</h3>
            <h2>{}</h2>
        </div>
        """.format(len(companies_data)), unsafe_allow_html=True)
    
    with col2:
        # Check if any companies have course recommendations
        companies_with_courses = [comp for comp in companies_data if 'course_recommendations' in comp and comp['course_recommendations']]
        total_courses = sum([len(comp.get('course_recommendations', {}).get('recommendations', [])) for comp in companies_with_courses])
        st.markdown("""
        <div class="metric-card">
            <h3> Course Recommendations</h3>
            <h2>{}</h2>
            <p>{} companies have courses</p>
        </div>
        """.format(total_courses, len(companies_with_courses)), unsafe_allow_html=True)
    
    with col3:
        # Check if any companies have certificate recommendations
        companies_with_certs = [comp for comp in companies_data if 'certificate_recommendations' in comp and comp['certificate_recommendations']]
        total_certificates = sum([len(comp.get('certificate_recommendations', {}).get('recommendations', [])) for comp in companies_with_certs])
        st.markdown("""
        <div class="metric-card">
            <h3> Certificate Recommendations</h3>
            <h2>{}</h2>
            <p>{} companies have certificates</p>
        </div>
        """.format(total_certificates, len(companies_with_certs)), unsafe_allow_html=True)
    
    with col4:
        unique_industries = len(set([comp.get('industry', 'Unknown') for comp in companies_data]))
        unique_dbs = len(set([comp.get('_source_db', 'Unknown') for comp in companies_data]))
        st.markdown("""
        <div class="metric-card">
            <h3> Industries</h3>
            <h2>{}</h2>
            <p>{} databases</p>
        </div>
        """.format(unique_industries, unique_dbs), unsafe_allow_html=True)
    
    # Analytics section
    st.markdown("""
    <div class="section-header">
        <h2>Analytics & Insights</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Define companies_with_recommendations before using it
    companies_with_recommendations = [comp for comp in companies_data if 'course_recommendations' in comp or 'certificate_recommendations' in comp]
    
    # Add recommendations status analysis
    if not companies_with_recommendations:
        st.markdown("""
        <div class="info-box">
            <h3 style="color: var(--stevens-burgundy); margin-top: 0;">🔧 Recommendation System Status</h3>
            <p><strong>Current Status:</strong> No recommendations found in database</p>
            <p><strong>Next Steps:</strong></p>
            <ul style="color: var(--stevens-grey-dark);">
                <li>Generate course and certificate recommendations for each company</li>
                <li>Update database documents with recommendation fields</li>
                <li>Ensure recommendations include similarity scores and metadata</li>
            </ul>
            <p><strong>Expected Document Structure:</strong></p>
            <div style="background: var(--stevens-grey-light); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <code style="color: var(--stevens-burgundy);">
                {<br>
                &nbsp;&nbsp;"company_name": "Company Name",<br>
                &nbsp;&nbsp;"industry": "Industry",<br>
                &nbsp;&nbsp;"course_recommendations": {<br>
                &nbsp;&nbsp;&nbsp;&nbsp;"recommendations": [/* course objects */],<br>
                &nbsp;&nbsp;&nbsp;&nbsp;"generated_at": "date"<br>
                &nbsp;&nbsp;},<br>
                &nbsp;&nbsp;"certificate_recommendations": {<br>
                &nbsp;&nbsp;&nbsp;&nbsp;"recommendations": [/* certificate objects */],<br>
                &nbsp;&nbsp;&nbsp;&nbsp;"generated_at": "date"<br>
                &nbsp;&nbsp;}<br>
                }
                </code>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Industry distribution chart and Popular Courses Analysis
    col1, col2, col3 = st.columns(3)
    
    with col1:
        industry_counts = {}
        for comp in companies_data:
            industry = comp.get('industry', 'Unknown')
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        fig_industry = px.pie(
            values=list(industry_counts.values()),
            names=list(industry_counts.keys()),
            title="Companies by Industry",
            color_discrete_sequence=['#800020', '#a0002a', '#666666', '#f8f9fa', '#333333']
        )
        st.plotly_chart(fig_industry, use_container_width=True)
    
    with col2:
        # Company size distribution
        size_counts = {}
        for comp in companies_data:
            size = comp.get('company_size', 'Unknown')
            size_counts[size] = size_counts.get(size, 0) + 1
        
        fig_size = px.bar(
            x=list(size_counts.keys()),
            y=list(size_counts.values()),
            title="Companies by Size",
            color_discrete_sequence=['#800020']
        )
        st.plotly_chart(fig_size, use_container_width=True)
    
    with col3:
        # Popular Courses Analysis - NEW FEATURE
        course_popularity = {}
        course_types = {}
        total_course_recommendations = 0
        
        # Analyze all course recommendations across companies
        for comp in companies_data:
            course_recs = comp.get('course_recommendations', {}).get('recommendations', [])
            for course in course_recs:
                course_name = get_course_field(course, 'course_name', ['name', 'title'])
                course_code = get_course_field(course, 'course_code', ['code'])
                course_type = course.get('course_type', 'Unknown')
                
                # Use course name as key, but display with code if available
                display_name = f"{course_name} ({course_code})" if course_code != 'N/A' else course_name
                course_popularity[display_name] = course_popularity.get(display_name, 0) + 1
                course_types[course_type] = course_types.get(course_type, 0) + 1
                total_course_recommendations += 1
        
        if course_popularity:
            # Get top 8 most popular courses (reduced from 10 for better display)
            top_courses = sorted(course_popularity.items(), key=lambda x: x[1], reverse=True)[:8]
            
            if top_courses:
                course_names = [name[:25] + "..." if len(name) > 25 else name for name, _ in top_courses]
                course_counts = [count for _, count in top_courses]
                
                fig_courses = px.bar(
                    x=course_counts,
                    y=course_names,
                    orientation='h',
                    title=f"Top {len(top_courses)} Popular Courses",
                    labels={'x': 'Times Recommended', 'y': 'Course Name'},
                    color_discrete_sequence=['#800020']
                )
                fig_courses.update_layout(
                    height=350,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_courses, use_container_width=True)
                
                # Add course statistics
                unique_courses = len(course_popularity)
                avg_recommendations = total_course_recommendations / len(companies_with_recommendations) if companies_with_recommendations else 0
                
                st.markdown(f"""
                <div class="info-box" style="margin-top: 1rem; padding: 1rem;">
                    <h5 style="color: var(--stevens-burgundy); margin: 0 0 0.5rem 0;">📈 Course Statistics</h5>
                    <p style="margin: 0.25rem 0; font-size: 0.9rem;"><strong>Unique Courses:</strong> {unique_courses}</p>
                    <p style="margin: 0.25rem 0; font-size: 0.9rem;"><strong>Total Recommendations:</strong> {total_course_recommendations}</p>
                    <p style="margin: 0.25rem 0; font-size: 0.9rem;"><strong>Avg per Company:</strong> {avg_recommendations:.1f}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No course recommendations found to analyze")
        else:
            st.info("No course recommendations available for popularity analysis")
    
    # Companies list - with burgundy background
    st.markdown("""
    <div class="companies-overview">
        <h2>Companies Overview</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Show sort information
    if filtered_companies:
        sort_info_text = f"Showing {len(filtered_companies)} companies sorted by timestamp ({'descending' if st.session_state.sort_order == 'desc' else 'ascending'} order)"
        if filtered_companies and len(filtered_companies) < len(companies_data):
            sort_info_text += f" - Filtered from {len(companies_data)} total companies"
        
        # Add active sort indicator
        active_sort = "Newest First (Active)" if st.session_state.sort_order == 'desc' else "Oldest First (Active)"
    
    # Add info about recommendations
    if not companies_with_recommendations:
        st.markdown("""
        <div class="info-box warning-box">
            <p style="margin: 0; color: var(--stevens-grey-dark);">
                <strong>ℹ️ Note:</strong> The companies in your database currently only have basic information (name, industry, size, contact). 
                Course and certificate recommendations are not present in the current data structure.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display companies - UPDATED with timestamp display
    for i, company in enumerate(filtered_companies):
        has_recommendations = 'course_recommendations' in company or 'certificate_recommendations' in company
        company_title = f"{company.get('company_name', 'Unknown Company')} - {company.get('industry', 'Unknown Industry')}"
        
        # Add timestamp to title if available
        timestamp = get_company_timestamp(company)
        if timestamp > 0:
            timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            company_title += f" |  {timestamp_str}"
        
        if not has_recommendations:
            company_title += " (No Recommendations)"
        
        with st.expander(company_title):
            
            # Company details
            col1, col2 = st.columns(2)
            
            with col1:
                source_db = company.get('_source_db', 'Unknown')
                # Display timestamp information
                timestamp_display = "N/A"
                if timestamp > 0:
                    timestamp_display = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                st.markdown(f"""
                <div class="company-card">
                    <h3> Company Information</h3>
                    <p><strong>Name:</strong> {company.get('company_name', 'N/A')}</p>
                    <p><strong>Industry:</strong> {company.get('industry', 'N/A')}</p>
                    <p><strong>Size:</strong> {company.get('company_size', 'N/A')}</p>
                    <p><strong>Contact:</strong> {company.get('contact_email', 'N/A')}</p>
                    <p><strong>Last Updated:</strong> {timestamp_display}</p>
                    <p><strong>Source DB:</strong> {source_db}</p>
                    <p><strong>Document ID:</strong> {parse_mongo_id(company.get('_id', {}))}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Recommendation summary
                course_recs = company.get('course_recommendations', {}).get('recommendations', [])
                cert_recs = company.get('certificate_recommendations', {}).get('recommendations', [])
                
                if has_recommendations:
                    # Parse the generated_at date properly
                    last_updated = company.get('course_recommendations', {}).get('generated_at', 'N/A')
                    if last_updated != 'N/A':
                        last_updated = parse_mongo_date(last_updated)
                    
                    st.markdown(f"""
                    <div class="company-card">
                        <h3>Recommendations Summary</h3>
                        <p><strong>Courses:</strong> {len(course_recs)}</p>
                        <p><strong>Certificates:</strong> {len(cert_recs)}</p>
                        <p><strong>Total Items:</strong> {len(course_recs) + len(cert_recs)}</p>
                        <p><strong>Max Proposal Credits:</strong> {min((len(course_recs) + len(cert_recs)) * 3, 36)}/36</p>
                        <p><strong>Last Updated:</strong> {last_updated}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="company-card">
                        <h3>⚠️ Recommendations Status</h3>
                        <p style="color: #666666;"><strong>Status:</strong> No recommendations available</p>
                        <p><strong>Available Fields:</strong> {', '.join(company.keys())}</p>
                        <p style="color: #666666; font-size: 0.9em;">
                            This company needs course and certificate recommendations to be generated.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Action buttons - UPDATED to include company detail view
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if has_recommendations:
                    if st.button(f" View Details", key=f"view_company_{i}"):
                        st.session_state.selected_company = company
                        st.session_state.current_view = "company_detail"
                        st.rerun()
                else:
                    st.button(f"No Details Available", key=f"view_company_{i}", disabled=True)
            
            with col2:
                if has_recommendations and course_recs:
                    if st.button(f"Courses ({len(course_recs)})", key=f"courses_{i}"):
                        st.session_state.selected_company = company
                        st.session_state.current_view = "courses"
                        st.rerun()
                else:
                    st.button(f"No Courses", key=f"courses_{i}", disabled=True)
            
            with col3:
                if has_recommendations and cert_recs:
                    if st.button(f"Certificates ({len(cert_recs)})", key=f"certificates_{i}"):
                        st.session_state.selected_company = company
                        st.session_state.current_view = "certificates"
                        st.rerun()
                else:
                    st.button(f"No Certificates", key=f"certificates_{i}", disabled=True)
            
            with col4:
                if has_recommendations and (course_recs or cert_recs):
                    if st.button(f"Create Proposal", key=f"proposal_{i}"):
                        st.session_state.selected_company = company
                        st.session_state.current_view = "proposal"
                        # Clear any existing selections
                        st.session_state.selected_courses = set()
                        st.session_state.selected_certificates = set()
                        st.session_state.total_credits = 0
                        st.rerun()
                else:
                    st.button(f"📋 No Proposal", key=f"proposal_{i}", disabled=True)
            
            # Quick stats
            if has_recommendations and course_recs:
                # Calculate average similarity
                course_similarities = [parse_mongo_number(r.get('similarity_score', 0)) for r in course_recs]
                avg_similarity = sum(course_similarities) / len(course_similarities) if course_similarities else 0
                max_possible_credits = min((len(course_recs) + len(cert_recs)) * 3, 36)
                st.markdown(f"**📈 Quick Stats:** Avg Similarity: {avg_similarity:.1%} | Max Credits: {max_possible_credits}/36")
            else:
                st.markdown("** Status:** Needs recommendations")

if __name__ == "__main__":
    main()
