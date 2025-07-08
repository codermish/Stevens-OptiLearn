import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import hashlib
import json
from bson import ObjectId
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Stevens Course Proposal System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Stevens branding
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #8B0000 0%, #DC143C 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stevens-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .sidebar .sidebar-content {
        background: #f1f3f4;
    }
    
    .stButton > button {
        background: #8B0000;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button:hover {
        background: #A52A2A;
    }
    
    .proposal-status {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-pending { background: #fff3cd; color: #856404; }
    .status-approved { background: #d4edda; color: #155724; }
    .status-rejected { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# MongoDB Connection
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb+srv://mkunchal:gvL1yK8iNrIL3DX3@otpilearn.hjnl2ii.mongodb.net/")
        return client.otpilearn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Authentication functions
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_password):
    return make_hash(password) == hashed_password

# Admin credentials (in production, store in database)
ADMIN_CREDENTIALS = {
    "admin": make_hash("stevens2024"),
    "faculty": make_hash("faculty123"),
    "coordinator": make_hash("coord456")
}

def login_user():
    st.sidebar.markdown("### 🔐 Authentication")
    
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
        st.session_state['username'] = None
    
    if st.session_state['authentication_status'] != True:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            if username in ADMIN_CREDENTIALS:
                if check_password(password, ADMIN_CREDENTIALS[username]):
                    st.session_state['authentication_status'] = True
                    st.session_state['username'] = username
                    st.sidebar.success(f"Welcome {username}!")
                    st.rerun()
                else:
                    st.sidebar.error("Incorrect password")
            else:
                st.sidebar.error("Username not found")
    else:
        st.sidebar.success(f"Logged in as: {st.session_state['username']}")
        if st.sidebar.button("Logout"):
            st.session_state['authentication_status'] = None
            st.session_state['username'] = None
            st.rerun()

def main_app():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Stevens Institute of Technology</h1>
        <h3>Course Proposal Management System</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    db = init_connection()
    if not db:
        st.error("Unable to connect to database. Please check your connection.")
        return
    
    collection = db.company
    
    # Sidebar navigation
    st.sidebar.markdown("### 📋 Navigation")
    
    if st.session_state.get('username') == 'admin':
        menu_options = ["Dashboard", "View All Data", "Manage Proposals", "Analytics", "System Settings"]
    elif st.session_state.get('username') in ['faculty', 'coordinator']:
        menu_options = ["Dashboard", "View Data", "Submit Proposal", "My Proposals"]
    else:
        menu_options = ["Dashboard", "Public View"]
    
    choice = st.sidebar.selectbox("Select Page", menu_options)
    
    # Main content based on selection
    if choice == "Dashboard":
        show_dashboard(collection)
    elif choice == "View All Data" and st.session_state.get('username') == 'admin':
        show_all_data(collection)
    elif choice == "View Data":
        show_public_data(collection)
    elif choice == "Manage Proposals":
        manage_proposals(collection)
    elif choice == "Submit Proposal":
        submit_proposal(collection)
    elif choice == "My Proposals":
        show_my_proposals(collection)
    elif choice == "Analytics":
        show_analytics(collection)
    elif choice == "System Settings":
        show_system_settings()
    else:
        show_public_view(collection)

def show_dashboard(collection):
    st.markdown("## 📊 Dashboard Overview")
    
    try:
        # Get basic statistics
        total_docs = collection.count_documents({})
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>{}</h3>
                <p>Total Records</p>
            </div>
            """.format(total_docs), unsafe_allow_html=True)
        
        with col2:
            proposals_count = collection.count_documents({"proposal": {"$exists": True}})
            st.markdown("""
            <div class="metric-card">
                <h3>{}</h3>
                <p>With Proposals</p>
            </div>
            """.format(proposals_count), unsafe_allow_html=True)
        
        with col3:
            recent_count = collection.count_documents({
                "date": {"$gte": datetime(2024, 1, 1).isoformat()}
            })
            st.markdown("""
            <div class="metric-card">
                <h3>{}</h3>
                <p>Recent Entries</p>
            </div>
            """.format(recent_count), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>Active</h3>
                <p>System Status</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent activity
        st.markdown("### 📈 Recent Activity")
        recent_docs = list(collection.find().sort("date", -1).limit(5))
        
        if recent_docs:
            for doc in recent_docs:
                with st.expander(f"📄 {doc.get('name', 'Unknown')} - {doc.get('email', 'No email')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {doc.get('date', 'N/A')}")
                        st.write(f"**Movie ID:** {doc.get('movie_id', 'N/A')}")
                    with col2:
                        if doc.get('proposal'):
                            st.success("✅ Has Proposal")
                        else:
                            st.warning("⏳ No Proposal")
                    
                    if doc.get('text'):
                        st.write(f"**Text:** {doc['text'][:200]}...")
        else:
            st.info("No recent activity found.")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def show_all_data(collection):
    st.markdown("## 📋 All Database Records")
    
    try:
        # Fetch all documents
        documents = list(collection.find())
        
        if documents:
            st.success(f"Found {len(documents)} records")
            
            # Search and filter options
            col1, col2 = st.columns(2)
            with col1:
                search_term = st.text_input("🔍 Search by name or email")
            with col2:
                show_with_proposals = st.checkbox("Show only records with proposals")
            
            # Filter documents
            filtered_docs = documents
            if search_term:
                filtered_docs = [doc for doc in filtered_docs 
                               if search_term.lower() in doc.get('name', '').lower() 
                               or search_term.lower() in doc.get('email', '').lower()]
            
            if show_with_proposals:
                filtered_docs = [doc for doc in filtered_docs if doc.get('proposal')]
            
            # Display documents
            for i, doc in enumerate(filtered_docs):
                with st.expander(f"Record {i+1}: {doc.get('name', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {doc.get('_id')}")
                        st.write(f"**Name:** {doc.get('name', 'N/A')}")
                        st.write(f"**Email:** {doc.get('email', 'N/A')}")
                        st.write(f"**Date:** {doc.get('date', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Movie ID:** {doc.get('movie_id', 'N/A')}")
                        if doc.get('proposal'):
                            st.success("✅ Has Proposal")
                            proposal = doc['proposal']
                            st.write(f"**Course:** {proposal.get('course_name', 'N/A')}")
                            st.write(f"**Status:** {proposal.get('status', 'Pending')}")
                        else:
                            st.warning("⏳ No Proposal")
                    
                    if doc.get('text'):
                        st.write(f"**Text:** {doc['text']}")
                    
                    # Admin actions
                    if st.session_state.get('username') == 'admin':
                        if st.button(f"Add Proposal to Record {i+1}", key=f"add_proposal_{i}"):
                            st.session_state[f'adding_proposal_{i}'] = True
                        
                        if st.session_state.get(f'adding_proposal_{i}'):
                            add_proposal_form(collection, doc['_id'], i)
        else:
            st.info("No records found in the database.")
            
    except Exception as e:
        st.error(f"Error fetching data: {e}")

def add_proposal_form(collection, doc_id, index):
    st.markdown("### ➕ Add Course Proposal")
    
    with st.form(f"proposal_form_{index}"):
        col1, col2 = st.columns(2)
        
        with col1:
            course_name = st.text_input("Course Name")
            course_id = st.text_input("Course ID")
            description = st.text_area("Course Description")
        
        with col2:
            outcome = st.text_area("Learning Outcomes")
            best_module = st.text_input("Best Module/Week")
            status = st.selectbox("Status", ["Pending", "Approved", "Rejected"])
        
        submitted = st.form_submit_button("Add Proposal")
        
        if submitted and course_name and course_id:
            proposal_data = {
                "course_name": course_name,
                "id": course_id,
                "description": description,
                "outcome": outcome,
                "best_module": best_module,
                "status": status,
                "created_date": datetime.now().isoformat(),
                "created_by": st.session_state.get('username')
            }
            
            try:
                collection.update_one(
                    {"_id": doc_id},
                    {"$set": {"proposal": proposal_data}}
                )
                st.success("Proposal added successfully!")
                st.session_state[f'adding_proposal_{index}'] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error adding proposal: {e}")

def submit_proposal(collection):
    st.markdown("## 📝 Submit New Course Proposal")
    
    with st.form("new_proposal_form"):
        st.markdown("### Course Information")
        col1, col2 = st.columns(2)
        
        with col1:
            course_name = st.text_input("Course Name *")
            course_id = st.text_input("Course ID *")
            instructor_name = st.text_input("Instructor Name *")
            instructor_email = st.text_input("Instructor Email *")
        
        with col2:
            department = st.selectbox("Department", 
                ["Computer Science", "Engineering", "Business", "Mathematics", "Physics", "Other"])
            credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
            semester = st.selectbox("Proposed Semester", 
                ["Fall 2024", "Spring 2025", "Summer 2025", "Fall 2025"])
            level = st.selectbox("Course Level", ["Undergraduate", "Graduate"])
        
        st.markdown("### Course Details")
        description = st.text_area("Course Description *", height=150)
        outcome = st.text_area("Learning Outcomes *", height=150)
        prerequisites = st.text_area("Prerequisites")
        best_module = st.text_input("Best Module/Week Focus")
        
        submitted = st.form_submit_button("Submit Proposal")
        
        if submitted:
            if course_name and course_id and instructor_name and instructor_email and description and outcome:
                proposal_data = {
                    "course_name": course_name,
                    "id": course_id,
                    "description": description,
                    "outcome": outcome,
                    "best_module": best_module,
                    "instructor_name": instructor_name,
                    "instructor_email": instructor_email,
                    "department": department,
                    "credits": credits,
                    "semester": semester,
                    "level": level,
                    "prerequisites": prerequisites,
                    "status": "Pending",
                    "created_date": datetime.now().isoformat(),
                    "created_by": st.session_state.get('username')
                }
                
                # Create new document with proposal
                new_doc = {
                    "name": instructor_name,
                    "email": instructor_email,
                    "movie_id": ObjectId(),  # Placeholder
                    "text": f"Course proposal for {course_name}",
                    "date": datetime.now().isoformat(),
                    "proposal": proposal_data
                }
                
                try:
                    result = collection.insert_one(new_doc)
                    st.success(f"Proposal submitted successfully! ID: {result.inserted_id}")
                except Exception as e:
                    st.error(f"Error submitting proposal: {e}")
            else:
                st.error("Please fill in all required fields marked with *")

def show_analytics(collection):
    st.markdown("## 📊 Analytics Dashboard")
    
    try:
        # Get all documents with proposals
        docs_with_proposals = list(collection.find({"proposal": {"$exists": True}}))
        
        if docs_with_proposals:
            # Status distribution
            status_counts = {}
            department_counts = {}
            level_counts = {}
            
            for doc in docs_with_proposals:
                proposal = doc['proposal']
                status = proposal.get('status', 'Unknown')
                dept = proposal.get('department', 'Unknown')
                level = proposal.get('level', 'Unknown')
                
                status_counts[status] = status_counts.get(status, 0) + 1
                department_counts[dept] = department_counts.get(dept, 0) + 1
                level_counts[level] = level_counts.get(level, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Status pie chart
                fig_status = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="Proposal Status Distribution"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Department bar chart
                fig_dept = px.bar(
                    x=list(department_counts.keys()),
                    y=list(department_counts.values()),
                    title="Proposals by Department"
                )
                st.plotly_chart(fig_dept, use_container_width=True)
            
            # Level distribution
            fig_level = px.pie(
                values=list(level_counts.values()),
                names=list(level_counts.keys()),
                title="Course Level Distribution"
            )
            st.plotly_chart(fig_level, use_container_width=True)
            
        else:
            st.info("No proposals found for analytics.")
            
    except Exception as e:
        st.error(f"Error generating analytics: {e}")

def manage_proposals(collection):
    st.markdown("## 🔧 Manage Proposals")
    
    try:
        proposals = list(collection.find({"proposal": {"$exists": True}}))
        
        if proposals:
            for i, doc in enumerate(proposals):
                proposal = doc['proposal']
                
                with st.expander(f"📋 {proposal.get('course_name', 'Unknown Course')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Instructor:** {proposal.get('instructor_name', 'N/A')}")
                        st.write(f"**Department:** {proposal.get('department', 'N/A')}")
                        st.write(f"**Credits:** {proposal.get('credits', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Course ID:** {proposal.get('id', 'N/A')}")
                        st.write(f"**Level:** {proposal.get('level', 'N/A')}")
                        st.write(f"**Semester:** {proposal.get('semester', 'N/A')}")
                    
                    with col3:
                        current_status = proposal.get('status', 'Pending')
                        st.write(f"**Current Status:** {current_status}")
                        
                        new_status = st.selectbox(
                            "Update Status",
                            ["Pending", "Approved", "Rejected"],
                            index=["Pending", "Approved", "Rejected"].index(current_status),
                            key=f"status_{i}"
                        )
                        
                        if st.button(f"Update Status", key=f"update_{i}"):
                            collection.update_one(
                                {"_id": doc["_id"]},
                                {"$set": {"proposal.status": new_status}}
                            )
                            st.success("Status updated!")
                            st.rerun()
                    
                    st.write(f"**Description:** {proposal.get('description', 'N/A')}")
                    st.write(f"**Learning Outcomes:** {proposal.get('outcome', 'N/A')}")
        else:
            st.info("No proposals found.")
            
    except Exception as e:
        st.error(f"Error managing proposals: {e}")

def show_my_proposals(collection):
    st.markdown("## 📄 My Proposals")
    
    user_email = st.text_input("Enter your email to view your proposals:")
    
    if user_email:
        try:
            user_proposals = list(collection.find({
                "proposal.instructor_email": user_email
            }))
            
            if user_proposals:
                for doc in user_proposals:
                    proposal = doc['proposal']
                    
                    with st.expander(f"📋 {proposal.get('course_name', 'Unknown Course')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Course ID:** {proposal.get('id', 'N/A')}")
                            st.write(f"**Department:** {proposal.get('department', 'N/A')}")
                            st.write(f"**Credits:** {proposal.get('credits', 'N/A')}")
                            st.write(f"**Level:** {proposal.get('level', 'N/A')}")
                        
                        with col2:
                            status = proposal.get('status', 'Pending')
                            if status == 'Approved':
                                st.success(f"✅ Status: {status}")
                            elif status == 'Rejected':
                                st.error(f"❌ Status: {status}")
                            else:
                                st.warning(f"⏳ Status: {status}")
                            
                            st.write(f"**Submitted:** {proposal.get('created_date', 'N/A')[:10]}")
                        
                        st.write(f"**Description:** {proposal.get('description', 'N/A')}")
                        st.write(f"**Learning Outcomes:** {proposal.get('outcome', 'N/A')}")
            else:
                st.info("No proposals found for this email address.")
                
        except Exception as e:
            st.error(f"Error fetching proposals: {e}")

def show_system_settings():
    st.markdown("## ⚙️ System Settings")
    
    st.markdown("### 👥 User Management")
    st.info("User management features would be implemented here.")
    
    st.markdown("### 🔧 Database Settings")
    st.info("Database configuration options would be available here.")
    
    st.markdown("### 📧 Email Configuration")
    st.info("Email notification settings would be configured here.")

def show_public_view(collection):
    st.markdown("## 🌐 Public Course Catalog")
    
    try:
        approved_proposals = list(collection.find({
            "proposal.status": "Approved"
        }))
        
        if approved_proposals:
            st.success(f"Found {len(approved_proposals)} approved courses")
            
            for doc in approved_proposals:
                proposal = doc['proposal']
                
                with st.expander(f"📚 {proposal.get('course_name', 'Unknown Course')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Course ID:** {proposal.get('id', 'N/A')}")
                        st.write(f"**Instructor:** {proposal.get('instructor_name', 'N/A')}")
                        st.write(f"**Department:** {proposal.get('department', 'N/A')}")
                        st.write(f"**Credits:** {proposal.get('credits', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Level:** {proposal.get('level', 'N/A')}")
                        st.write(f"**Semester:** {proposal.get('semester', 'N/A')}")
                        if proposal.get('prerequisites'):
                            st.write(f"**Prerequisites:** {proposal.get('prerequisites')}")
                    
                    st.write(f"**Description:** {proposal.get('description', 'N/A')}")
                    st.write(f"**Learning Outcomes:** {proposal.get('outcome', 'N/A')}")
        else:
            st.info("No approved courses available yet.")
            
    except Exception as e:
        st.error(f"Error loading public catalog: {e}")

def show_public_data(collection):
    st.markdown("## 📊 Database Overview")
    
    try:
        total_records = collection.count_documents({})
        total_proposals = collection.count_documents({"proposal": {"$exists": True}})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Records", total_records)
        with col2:
            st.metric("Total Proposals", total_proposals)
            
        # Show sample data (limited view)
        st.markdown("### Recent Activity")
        recent_docs = list(collection.find().sort("date", -1).limit(3))
        
        for doc in recent_docs:
            with st.expander(f"Record from {doc.get('date', 'Unknown date')[:10]}"):
                st.write(f"**Name:** {doc.get('name', 'N/A')}")
                if doc.get('proposal'):
                    st.write(f"**Course:** {doc['proposal'].get('course_name', 'N/A')}")
                    st.write(f"**Status:** {doc['proposal'].get('status', 'N/A')}")
                
    except Exception as e:
        st.error(f"Error loading data overview: {e}")

# Main execution
def main():
    # Authentication
    login_user()
    
    if st.session_state.get('authentication_status') == True:
        main_app()
    else:
        st.markdown("""
        <div class="main-header">
            <h1>🎓 Stevens Institute of Technology</h1>
            <h3>Course Proposal Management System</h3>
            <p>Please login to access the system</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🔐 System Access
        
        **Available User Roles:**
        - **Admin**: Full system access and management
        - **Faculty**: Submit and view proposals
        - **Coordinator**: Review and manage department proposals
        
        **Demo Credentials:**
        - Username: `admin` / Password: `stevens2024`
        - Username: `faculty` / Password: `faculty123`
        - Username: `coordinator` / Password: `coord456`
        
        ### 📋 System Features
        - Course proposal submission and management
        - Multi-role authentication system
        - Real-time analytics and reporting
        - MongoDB integration for data persistence
        - Stevens Institute branding and guidelines
        """)

if __name__ == "__main__":
    main()