import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="AI Task Management System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .project-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .project-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .team-member-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .team-member-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-done { background-color: #d4edda; color: #155724; }
    .status-progress { background-color: #fff3cd; color: #856404; }
    .status-review { background-color: #cce5ff; color: #004085; }
    .status-todo { background: #ffc107; color: #000; }
    .status-in-progress { background: #17a2b8; color: white; }
    .status-blocked { background: #dc3545; color: white; }
    
    .priority-high { color: #dc3545; font-weight: bold; }
    .priority-medium { color: #ffc107; font-weight: bold; }
    .priority-low { color: #28a745; font-weight: bold; }
    .priority-critical { color: #6f42c1; font-weight: bold; }
    
    .performance-indicator {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .performance-excellent { background: #28a745; color: white; }
    .performance-good { background: #ffc107; color: #000; }
    .performance-needs-support { background: #dc3545; color: white; }
    
    .task-list-item {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #667eea;
        transition: all 0.2s ease;
    }
    
    .task-list-item:hover {
        background: #e9ecef;
        transform: translateX(5px);
    }
    
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .stat-item {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #667eea;
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 5px;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Load dataset for workload analysis with better error handling
try:
    df = pd.read_csv('cleaned_jira_dataset.csv')
    
    # Clean the dataset by removing NaN values from text columns
    if 'clean_summary' in df.columns:
        df = df.dropna(subset=['clean_summary'])
        df['clean_summary'] = df['clean_summary'].astype(str)
    
    # Convert 'task_deadline' to pandas datetime objects, handling errors more gracefully
    if 'task_deadline' in df.columns:
        # Replace invalid date strings with NaT (Not a Time)
        invalid_dates = ['tow days', 'five days', 'one days', 'for days', 'three days', 'two days']
        df['task_deadline'] = df['task_deadline'].replace(invalid_dates, pd.NaT)
        df['task_deadline'] = pd.to_datetime(df['task_deadline'], errors='coerce')
    else:
        # If column doesn't exist, create it with NaT values
        df['task_deadline'] = pd.NaT
        
except Exception as e:
    st.error(f"Error loading dataset: {str(e)}")
    df = pd.DataFrame()

# Load models and encoders with error handling
@st.cache_resource
def load_models():
    """Load all ML models and encoders with error handling and performance optimization"""
    try:
        print("Loading models and encoders...")
        
        # Load task classification model
        task_bundle = joblib.load('task_classifier.pkl')
        
        # Load priority prediction model
        priority_bundle = joblib.load('priority_predictor.pkl')
        
        # Load TF-IDF vectorizers
        task_tfidf = joblib.load('tfidf_vectorizer.pkl')
        priority_tfidf = joblib.load('priority_tfidf_vectorizer.pkl')
        
        # Load BERT model with performance optimization
        try:
            # Set environment variables to prevent thread pool issues
            import os
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            # Load BERT model with specific settings for better performance
            bert_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Test the model with a simple encoding to ensure it works
            test_embedding = bert_model.encode(['test'], show_progress_bar=False, convert_to_numpy=True)
            
        except Exception as bert_error:
            print(f"BERT model loading failed: {bert_error}")
            # Create a dummy BERT model that returns zeros
            class DummyBERT:
                def encode(self, texts, **kwargs):
                    return np.zeros((len(texts), 384))
            bert_model = DummyBERT()
        
        print("Models loaded successfully!")
        return task_bundle, priority_bundle, task_tfidf, priority_tfidf, bert_model
        
    except Exception as e:
        print(f"Error loading models: {e}")
        st.error(f"Failed to load models: {str(e)}")
        return None, None, None, None, None

# Load models
task_bundle, priority_bundle, task_tfidf, priority_tfidf, bert_model = load_models()

# Function to get project statistics
def get_project_stats():
    if df.empty:
        return pd.DataFrame(), {}, {}
    
    # Project statistics
    project_stats = df.groupby('project_name').agg({
        'clean_summary': 'count',
        'status': lambda x: (x == 'done').sum(),
        'priority': lambda x: (x == 'critical').sum()
    }).rename(columns={
        'clean_summary': 'total_tasks',
        'status': 'completed_tasks',
        'priority': 'critical_tasks'
    })
    
    project_stats['completion_rate'] = (project_stats['completed_tasks'] / project_stats['total_tasks'] * 100).round(1)
    
    # Team member statistics
    team_stats = df.groupby('task_assignee').agg({
        'clean_summary': 'count',
        'status': lambda x: (x == 'done').sum(),
        'project_name': 'nunique'
    }).rename(columns={
        'clean_summary': 'total_tasks',
        'status': 'completed_tasks',
        'project_name': 'projects_involved'
    })
    
    team_stats['completion_rate'] = (team_stats['completed_tasks'] / team_stats['total_tasks'] * 100).round(1)
    
    return project_stats, team_stats

# Main app
def main():
    # Header with gradient
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI-Powered Task Management System</h1>
        <p>Intelligent project tracking and team collaboration platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if models loaded successfully
    if task_bundle is None or priority_bundle is None:
        st.error("Failed to load required models. Please check if all model files are present.")
        return
    
    # Sidebar navigation
    st.sidebar.markdown("## 🧭 Navigation")
    page = st.sidebar.radio('Go to', ['📊 Dashboard', '🆕 New Task', '📋 Recent Tasks', '👥 Team Projects', '📎 Alerts', '📤 Data Export'])

    if page == '📊 Dashboard':
        show_dashboard()
    elif page == '🆕 New Task':
        show_new_task()
    elif page == '📋 Recent Tasks':
        show_recent_tasks()
    elif page == '👥 Team Projects':
        show_team_projects()
    elif page == '📎 Alerts':
        show_alerts()
    elif page == '📤 Data Export':
        show_data_export()

def show_dashboard():
    st.header('📊 Live Dashboard')
    
    if df.empty:
        st.warning('No data available for visualization.')
        return
    
    # Get statistics
    project_stats, team_stats = get_project_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📋 Total Tasks</h3>
            <h2>{len(df)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        completed_tasks = len(df[df['status'] == 'done'])
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ Completed</h3>
            <h2>{completed_tasks}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        active_projects = df['project_name'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <h3>🚀 Active Projects</h3>
            <h2>{active_projects}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        team_members = df['task_assignee'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Team Members</h3>
            <h2>{team_members}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('📈 Task Status Distribution')
        status_counts = df['status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index, 
                    title="Task Status Overview")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader('🎯 Priority Distribution')
        priority_counts = df['priority'].value_counts()
        fig = px.bar(x=priority_counts.index, y=priority_counts.values,
                    title="Tasks by Priority Level")
        st.plotly_chart(fig, use_container_width=True)
    
    # Team workload
    st.subheader('👥 Team Workload')
    if not team_stats.empty:
        workload = df['task_assignee'].value_counts()
        fig = px.bar(x=workload.index, y=workload.values,
                    title="Tasks per Team Member")
        st.plotly_chart(fig, use_container_width=True)

def show_new_task():
    st.header('🆕 Submit New Task')
    
    with st.form(key='task_form'):
        task_summary = st.text_area('Task Summary', height=150, 
                                  placeholder="Describe the task in detail...",
                                  help="Enter a detailed description of the task")
        
        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input('Deadline (Optional)', value=None, 
                                   help="Select a deadline date")
        with col2:
            # Handle assignee selection with better error handling
            assignee_options = ['']  # Start with empty option
            if not df.empty and 'task_assignee' in df.columns:
                unique_assignees = df['task_assignee'].dropna().unique()
                assignee_options.extend(list(unique_assignees))
            
            assignee = st.selectbox('Assignee (Optional)', options=assignee_options, 
                                  help="Select an assignee or leave empty for smart assignment")
        
        submit_button = st.form_submit_button(label='🚀 Submit Task', 
                                            use_container_width=True)

    if submit_button:
        if task_summary and task_summary.strip():
            try:
                # Predict issue type
                issue_type, issue_confidence = predict_issue_type(task_summary)
                
                # Predict priority
                priority, priority_confidence = predict_priority(task_summary)

                # Smart assignment system
                if not assignee:
                    recommended_assignee, assignment_reason = smart_assign_task(task_summary, issue_type, priority)
                    st.success('✅ Task submitted successfully!')
                    
                    # Display smart assignment results
                    st.markdown("### 🤖 Smart Assignment Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="project-card">
                            <h4>👤 Recommended Assignee</h4>
                            <h3>{recommended_assignee}</h3>
                            <p><strong>Reason:</strong> {assignment_reason}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Show assignee stats
                        assignee_stats = get_assignee_stats(recommended_assignee)
                        st.markdown(f"""
                        <div class="project-card">
                            <h4>📊 Assignee Stats</h4>
                            <p><strong>Current Tasks:</strong> {assignee_stats['current_tasks']}</p>
                            <p><strong>Completion Rate:</strong> {assignee_stats['completion_rate']}%</p>
                            <p><strong>Projects:</strong> {assignee_stats['projects']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    final_assignee = recommended_assignee
                else:
                    st.success('✅ Task submitted successfully!')
                    st.info(f'👤 Manual Assignment: **{assignee}**')
                    final_assignee = assignee

                # Display predictions in a nice format
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="project-card">
                        <h4>🎯 Issue Type</h4>
                        <h3>{issue_type.title()}</h3>
                        <p>Confidence: {issue_confidence.max():.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    priority_class = f"priority-{priority.lower()}"
                    st.markdown(f"""
                    <div class="project-card">
                        <h4>⚡ Priority</h4>
                        <h3 class="{priority_class}">{priority.title()}</h3>
                        <p>Confidence: {priority_confidence.max():.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Display deadline if provided
                if deadline:
                    st.info(f'📅 Deadline: **{deadline}**')

                # Find and display similar tasks
                try:
                    similar_tasks, similarities = find_similar_tasks(task_summary)
                    if not similar_tasks.empty:
                        st.subheader('🔍 Similar Tasks')
                        for i, (_, task) in enumerate(similar_tasks.iterrows()):
                            status_class = f"status-{task['status']}"
                            st.markdown(f"""
                            <div class="project-card">
                                <h4>Task {i+1}: {task["clean_summary"]}</h4>
                                <p>Similarity: {similarities[i]:.2f} | 
                                <span class="status-badge {status_class}">{task['status'].title()}</span> | 
                                Priority: {task['priority'].title()}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info('No similar tasks found.')
                except Exception as e:
                    st.warning(f'Could not find similar tasks: {str(e)}')

                # Save new task to CSV with better error handling
                try:
                    # Add timestamp for tracking when task was added
                    current_time = datetime.now()
                    
                    new_task = pd.DataFrame({
                        'clean_summary': [task_summary],
                        'issue_type': [issue_type],
                        'priority': [priority],
                        'task_assignee': [final_assignee],
                        'task_deadline': [deadline if deadline else pd.NaT],
                        'status': ['progress'],  # New tasks start as in progress
                        'project_name': ['New Project'],  # Default project
                        'project_type': ['software'],  # Default type
                        'project_lead': ['AI System'],  # Default lead
                        'project_description': ['AI-generated task'],  # Default description
                        'resolution': ['unresolved'],  # Default resolution
                        'text_length': [len(task_summary)],  # Text length
                        'date_added': [current_time.strftime('%Y-%m-%d %H:%M:%S')]  # Timestamp
                    })
                    
                    # Check if new_tasks.csv exists and has the correct structure
                    if os.path.exists('new_tasks.csv'):
                        try:
                            # Try to read existing file to check structure
                            existing_df = pd.read_csv('new_tasks.csv')
                            expected_columns = new_task.columns.tolist()
                            
                            # If columns don't match, create a new file with correct structure
                            if list(existing_df.columns) != expected_columns:
                                st.warning("Updating tasks file structure...")
                                # Backup old file
                                import shutil
                                shutil.copy('new_tasks.csv', 'new_tasks_old.csv')
                                # Create new file with correct structure
                                new_task.to_csv('new_tasks.csv', index=False)
                                st.success("Tasks file updated successfully!")
                            else:
                                # Append to existing file
                                new_task.to_csv('new_tasks.csv', mode='a', header=False, index=False)
                        except Exception as csv_error:
                            st.warning("Tasks file corrupted. Creating new file...")
                            # Create new file with correct structure
                            new_task.to_csv('new_tasks.csv', index=False)
                    else:
                        # Create new file with headers
                        new_task.to_csv('new_tasks.csv', index=False)
                    
                    # Show task added confirmation with assigned team member
                    st.markdown("### 📝 Task Details Added")
                    st.markdown(f"""
                    <div class="project-card">
                        <h4>✅ Task Successfully Added</h4>
                        <p><strong>Summary:</strong> {task_summary}</p>
                        <p><strong>Type:</strong> {issue_type.title()} | <strong>Priority:</strong> {priority.title()}</p>
                        <p><strong>👤 Assigned to:</strong> <span style="color: #667eea; font-weight: bold;">{final_assignee}</span></p>
                        <p><strong>Status:</strong> In Progress | <strong>Added:</strong> {current_time.strftime('%Y-%m-%d %H:%M')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f'Error saving task: {str(e)}')
                    
            except Exception as e:
                st.error(f'Error processing task: {str(e)}')
                st.info('Please try again with a different task description.')
        else:
            st.error('Please enter a task summary.')

def show_team_projects():
    st.header('👥 Team Projects & Assignments')
    
    if df.empty:
        st.warning('No data available.')
        return
    
    # Get statistics
    project_stats, team_stats = get_project_stats()
    
    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["📊 Project Overview", "👤 Team Members", "📈 Analytics"])
    
    with tab1:
        st.subheader('🚀 Active Projects')
        
        if not project_stats.empty:
            # Display project cards using Streamlit components
            for i, (project_name, stats) in enumerate(project_stats.iterrows()):
                completion_rate = stats['completion_rate']
                total_tasks = int(stats['total_tasks'])
                completed_tasks = int(stats['completed_tasks'])
                critical_tasks = int(stats['critical_tasks'])
                
                # Color coding based on completion rate
                if completion_rate >= 80:
                    progress_color = "#28a745"  # Green
                    status_text = "On Track"
                elif completion_rate >= 60:
                    progress_color = "#ffc107"  # Yellow
                    status_text = "In Progress"
                else:
                    progress_color = "#dc3545"  # Red
                    status_text = "Needs Attention"
                
                # Create project card using columns
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border-radius: 15px; padding: 20px; margin: 15px 0; 
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border: 1px solid #e9ecef;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="margin: 0; color: #667eea;">🚀 {project_name}</h3>
                            <span style="background: {progress_color}; color: white; padding: 5px 15px; 
                                         border-radius: 20px; font-size: 0.8rem; font-weight: bold;">
                                {status_text}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Statistics in columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Tasks", total_tasks, delta=None)
                    with col2:
                        st.metric("Completed", completed_tasks, delta=None)
                    with col3:
                        st.metric("Critical", critical_tasks, delta=None)
                    
                    # Progress bar
                    st.markdown(f"**Progress: {completion_rate}%**")
                    st.progress(completion_rate / 100)
                    
                    st.divider()
        else:
            st.info("No project data available.")
    
    with tab2:
        st.subheader('👥 Team Member Overview')
        
        if not team_stats.empty:
            # Display team member cards using Streamlit components
            for member, stats in team_stats.iterrows():
                completion_rate = stats['completion_rate']
                total_tasks = int(stats['total_tasks'])
                completed_tasks = int(stats['completed_tasks'])
                projects_involved = int(stats['projects_involved'])
                
                # Get member's current tasks
                member_tasks = df[df['task_assignee'] == member]
                current_tasks = member_tasks[member_tasks['status'] != 'done']
                
                # Performance indicator
                if completion_rate >= 80:
                    performance_class = "performance-excellent"
                    performance_text = "Excellent"
                    progress_color = "#28a745"
                elif completion_rate >= 60:
                    performance_class = "performance-good"
                    performance_text = "Good"
                    progress_color = "#ffc107"
                else:
                    performance_class = "performance-needs-support"
                    performance_text = "Needs Support"
                    progress_color = "#dc3545"
                
                # Create team member card
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border-radius: 15px; padding: 20px; margin: 15px 0; 
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-left: 4px solid #667eea;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="margin: 0; color: #667eea;">👤 {member}</h3>
                            <span class="performance-indicator {performance_class}">
                                {performance_text}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Statistics in columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Tasks", total_tasks, delta=None)
                    with col2:
                        st.metric("Completed", completed_tasks, delta=None)
                    with col3:
                        st.metric("Projects", projects_involved, delta=None)
                    
                    # Completion rate
                    st.markdown(f"**Completion Rate: {completion_rate}%**")
                    st.progress(completion_rate / 100)
                    
                    # Current tasks summary
                    st.info(f"📋 **Current Tasks**: {len(current_tasks)} active tasks • {completion_rate}% completion rate")
                    
                    # Show current tasks for this member in an expandable section
                    if not current_tasks.empty:
                        with st.expander(f"📋 View {member}'s Current Tasks ({len(current_tasks)})"):
                            for _, task in current_tasks.head(5).iterrows():  # Show max 5 tasks
                                status_class = f"status-{task['status']}"
                                priority_class = f"priority-{task['priority'].lower()}"
                                st.markdown(f"""
                                <div style="margin: 5px 0; padding: 10px; background: #f8f9fa; border-radius: 8px; 
                                            border-left: 3px solid #667eea;">
                                    <div style="font-weight: bold; margin-bottom: 5px;">{task['clean_summary']}</div>
                                    <div style="font-size: 0.8rem; color: #666;">
                                        <span class="status-badge {status_class}">{task['status'].title()}</span> | 
                                        <span class="{priority_class}">{task['priority'].title()}</span> | 
                                        Project: {task['project_name']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            if len(current_tasks) > 5:
                                st.info(f"... and {len(current_tasks) - 5} more tasks")
                    
                    st.divider()
        else:
            st.info("No team member data available.")
    
    with tab3:
        st.subheader('📈 Project Analytics')
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Project completion rates chart
            if not project_stats.empty:
                st.markdown("### 📊 Project Completion Rates")
                fig = px.bar(
                    x=project_stats.index,
                    y=project_stats['completion_rate'],
                    title="Completion Rate by Project",
                    color=project_stats['completion_rate'],
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(xaxis_title="Projects", yaxis_title="Completion Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Team member workload chart
            if not team_stats.empty:
                st.markdown("### 👥 Team Workload Distribution")
                fig = px.pie(
                    values=team_stats['total_tasks'],
                    names=team_stats.index,
                    title="Tasks Distribution by Team Member"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Project assignment matrix
        if not df.empty:
            st.markdown("### 📋 Project Assignment Matrix")
            
            # Create assignment matrix
            assignment_matrix = df.groupby(['project_name', 'task_assignee']).size().unstack(fill_value=0)
            
            # Create heatmap
            fig = px.imshow(
                assignment_matrix, 
                title="Task Assignments by Project and Team Member",
                color_continuous_scale='Blues',
                aspect="auto"
            )
            fig.update_layout(
                xaxis_title="Team Members",
                yaxis_title="Projects"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.markdown("### 📊 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Projects", len(project_stats) if not project_stats.empty else 0)
        
        with col2:
            st.metric("Team Members", len(team_stats) if not team_stats.empty else 0)
        
        with col3:
            avg_completion = project_stats['completion_rate'].mean() if not project_stats.empty else 0
            st.metric("Avg Completion", f"{avg_completion:.1f}%")
        
        with col4:
            total_critical = project_stats['critical_tasks'].sum() if not project_stats.empty else 0
            st.metric("Critical Tasks", total_critical)

def show_alerts():
    st.header('🚨 Smart Alerts & Monitoring')
    
    if df.empty:
        st.warning('No data available for alerts.')
        return
    
    # Quick summary dashboard
    st.markdown("### 📊 Alert Summary Dashboard")
    
    # Get current date for deadline calculations
    current_date = pd.Timestamp.now().normalize()
    today = current_date
    tomorrow = current_date + pd.Timedelta(days=1)
    three_days = current_date + pd.Timedelta(days=3)
    
    # Calculate critical metrics
    if 'task_deadline' in df.columns:
        mask_overdue = (df['task_deadline'] < today) & (df['task_deadline'].notna())
        mask_due_today = (df['task_deadline'] == today) & (df['task_deadline'].notna())
        mask_due_soon = (df['task_deadline'] > today) & (df['task_deadline'] <= three_days) & (df['task_deadline'].notna())
        
        overdue_count = len(df[mask_overdue])
        due_today_count = len(df[mask_due_today])
        due_soon_count = len(df[mask_due_soon])
    else:
        overdue_count = due_today_count = due_soon_count = 0
    
    # Get project and team stats
    project_stats, team_stats = get_project_stats()
    
    # Calculate performance metrics
    critical_tasks = len(df[df['priority'] == 'critical'])
    low_completion_projects = len(project_stats[project_stats['completion_rate'] < 50]) if not project_stats.empty else 0
    low_performers = len(team_stats[team_stats['completion_rate'] < 60]) if not team_stats.empty else 0
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if overdue_count > 0:
            st.error(f"🚨 **{overdue_count}** Overdue Tasks")
        else:
            st.success("✅ No Overdue Tasks")
    
    with col2:
        if due_today_count > 0:
            st.warning(f"⚠️ **{due_today_count}** Due Today")
        else:
            st.info("📅 No Tasks Due Today")
    
    with col3:
        if critical_tasks > 5:
            st.error(f"🚨 **{critical_tasks}** Critical Tasks")
        elif critical_tasks > 0:
            st.warning(f"⚠️ **{critical_tasks}** Critical Tasks")
        else:
            st.success("✅ No Critical Tasks")
    
    with col4:
        if low_completion_projects > 0 or low_performers > 0:
            st.error(f"📊 **{low_completion_projects + low_performers}** Performance Issues")
        else:
            st.success("📊 All Systems Healthy")
    
    # Overall health indicator
    total_issues = overdue_count + due_today_count + (critical_tasks if critical_tasks > 5 else 0) + low_completion_projects + low_performers
    
    if total_issues == 0:
        st.success("🎉 **All systems are running smoothly!** No critical alerts at this time.")
    elif total_issues <= 3:
        st.info(f"ℹ️ **{total_issues} minor issues** detected. Review the tabs below for details.")
    elif total_issues <= 8:
        st.warning(f"⚠️ **{total_issues} issues** require attention. Please review the alerts below.")
    else:
        st.error(f"🚨 **{total_issues} critical issues** detected! Immediate action required.")
    
    st.divider()
    
    # Create tabs for different types of alerts
    tab1, tab2, tab3, tab4 = st.tabs(["⏰ Deadlines", "📊 Performance", "👥 Team Health", "📈 Project Status"])
    
    with tab1:
        st.subheader('⏰ Deadline Management')
        
        if 'task_deadline' not in df.columns:
            st.warning('No deadline data available.')
        else:
            # Get current date and date ranges
            current_date = pd.Timestamp.now().normalize()
            today = current_date
            tomorrow = current_date + pd.Timedelta(days=1)
            week_end = current_date + pd.Timedelta(days=7)
            three_days = current_date + pd.Timedelta(days=3)
            
            # Filter tasks with proper null handling
            mask_due_today = (df['task_deadline'] == today) & (df['task_deadline'].notna())
            mask_due_tomorrow = (df['task_deadline'] == tomorrow) & (df['task_deadline'].notna())
            mask_due_soon = (df['task_deadline'] > today) & (df['task_deadline'] <= three_days) & (df['task_deadline'].notna())
            mask_overdue = (df['task_deadline'] < today) & (df['task_deadline'].notna())
            mask_due_this_week = (df['task_deadline'] > today) & (df['task_deadline'] <= week_end) & (df['task_deadline'].notna())
            
            due_today = df[mask_due_today].sort_values('task_deadline')
            due_tomorrow = df[mask_due_tomorrow].sort_values('task_deadline')
            due_soon = df[mask_due_soon].sort_values('task_deadline')
            overdue = df[mask_overdue].sort_values('task_deadline')
            due_this_week = df[mask_due_this_week].sort_values('task_deadline')
            
            # Alert summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🚨 Overdue", len(overdue), delta=None)
            with col2:
                st.metric("⚠️ Due Today", len(due_today), delta=None)
            with col3:
                st.metric("📅 Due Tomorrow", len(due_tomorrow), delta=None)
            with col4:
                st.metric("📋 Due This Week", len(due_this_week), delta=None)
            
            # Overdue tasks (highest priority)
            if len(overdue) > 0:
                st.markdown("### 🚨 **CRITICAL: Overdue Tasks**")
                for _, task in overdue.iterrows():
                    try:
                        deadline_str = task['task_deadline'].strftime('%Y-%m-%d')
                        days_overdue = (today - task['task_deadline']).days
                        priority_class = f"priority-{task['priority'].lower()}"
                        
                        # Color based on how overdue
                        if days_overdue > 7:
                            bg_color = "#dc3545"
                            border_color = "#721c24"
                        elif days_overdue > 3:
                            bg_color = "#fd7e14"
                            border_color = "#d63384"
                        else:
                            bg_color = "#ffc107"
                            border_color = "#856404"
                        
                        st.markdown(f"""
                        <div style='background-color: {bg_color}20; padding: 15px; border-radius: 10px; 
                                    margin: 10px 0; border-left: 4px solid {border_color};'>
                            <h4 style="color: {border_color}; margin-bottom: 10px;">{task['clean_summary']}</h4>
                            <p><strong>🚨 {days_overdue} days overdue</strong> | 
                            <strong>Due:</strong> {deadline_str} | 
                            <strong>Assignee:</strong> {task['task_assignee']} | 
                            <strong>Project:</strong> {task['project_name']} | 
                            <span class="{priority_class}">{task['priority'].title()}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f'Error displaying task: {str(e)}')
            else:
                st.success('✅ **No overdue tasks!** Great job!')
            
            # Due today
            if len(due_today) > 0:
                st.markdown("### ⚠️ **Due Today**")
                for _, task in due_today.iterrows():
                    try:
                        priority_class = f"priority-{task['priority'].lower()}"
                        st.markdown(f"""
                        <div style='background-color: #fff3cd; padding: 15px; border-radius: 10px; 
                                    margin: 10px 0; border-left: 4px solid #ffc107;'>
                            <h4>{task['clean_summary']}</h4>
                            <p><strong>Due:</strong> Today | 
                            <strong>Assignee:</strong> {task['task_assignee']} | 
                            <strong>Project:</strong> {task['project_name']} | 
                            <span class="{priority_class}">{task['priority'].title()}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f'Error displaying task: {str(e)}')
            
            # Due tomorrow
            if len(due_tomorrow) > 0:
                st.markdown("### 📅 **Due Tomorrow**")
                for _, task in due_tomorrow.iterrows():
                    try:
                        priority_class = f"priority-{task['priority'].lower()}"
                        st.markdown(f"""
                        <div style='background-color: #d1ecf1; padding: 15px; border-radius: 10px; 
                                    margin: 10px 0; border-left: 4px solid #17a2b8;'>
                            <h4>{task['clean_summary']}</h4>
                            <p><strong>Due:</strong> Tomorrow | 
                            <strong>Assignee:</strong> {task['task_assignee']} | 
                            <strong>Project:</strong> {task['project_name']} | 
                            <span class="{priority_class}">{task['priority'].title()}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f'Error displaying task: {str(e)}')
            
            # Due in next 3 days
            if len(due_soon) > 0:
                with st.expander(f"📋 Due in Next 3 Days ({len(due_soon)})"):
                    for _, task in due_soon.iterrows():
                        try:
                            deadline_str = task['task_deadline'].strftime('%Y-%m-%d')
                            priority_class = f"priority-{task['priority'].lower()}"
                            st.markdown(f"""
                            <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px; 
                                        margin: 5px 0; border-left: 3px solid #6c757d;'>
                                <div style="font-weight: bold;">{task['clean_summary']}</div>
                                <div style="font-size: 0.9rem; color: #666;">
                                    Due: {deadline_str} | {task['task_assignee']} | 
                                    <span class="{priority_class}">{task['priority'].title()}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.warning(f'Error displaying task: {str(e)}')
    
    with tab2:
        st.subheader('📊 Performance Alerts')
        
        # Get project and team stats
        project_stats, team_stats = get_project_stats()
        
        # Project performance alerts
        st.markdown("### 🚀 Project Performance")
        
        if not project_stats.empty:
            # Projects with low completion rates
            low_completion = project_stats[project_stats['completion_rate'] < 50]
            if len(low_completion) > 0:
                st.warning(f"⚠️ **{len(low_completion)} projects have completion rates below 50%**")
                for project, stats in low_completion.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #fff3cd; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                        <strong>{project}</strong>: {stats['completion_rate']}% completion 
                        ({stats['completed_tasks']}/{stats['total_tasks']} tasks)
                    </div>
                    """, unsafe_allow_html=True)
            
            # Projects with many critical tasks
            high_critical = project_stats[project_stats['critical_tasks'] > 5]
            if len(high_critical) > 0:
                st.error(f"🚨 **{len(high_critical)} projects have more than 5 critical tasks**")
                for project, stats in high_critical.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #f8d7da; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                        <strong>{project}</strong>: {stats['critical_tasks']} critical tasks
                    </div>
                    """, unsafe_allow_html=True)
            
            # Best performing projects
            best_projects = project_stats[project_stats['completion_rate'] > 80].head(3)
            if len(best_projects) > 0:
                st.success(f"🏆 **Top Performing Projects**")
                for project, stats in best_projects.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #d4edda; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                        <strong>{project}</strong>: {stats['completion_rate']}% completion 
                        ({stats['completed_tasks']}/{stats['total_tasks']} tasks)
                    </div>
                    """, unsafe_allow_html=True)
        
        # Team performance alerts
        st.markdown("### 👥 Team Performance")
        
        if not team_stats.empty:
            # Team members with low completion rates
            low_performers = team_stats[team_stats['completion_rate'] < 60]
            if len(low_performers) > 0:
                st.warning(f"⚠️ **{len(low_performers)} team members have completion rates below 60%**")
                for member, stats in low_performers.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #fff3cd; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                        <strong>{member}</strong>: {stats['completion_rate']}% completion 
                        ({stats['completed_tasks']}/{stats['total_tasks']} tasks)
                    </div>
                    """, unsafe_allow_html=True)
            
            # Overloaded team members
            overloaded = team_stats[team_stats['total_tasks'] > 20]
            if len(overloaded) > 0:
                st.error(f"🚨 **{len(overloaded)} team members are overloaded (20+ tasks)**")
                for member, stats in overloaded.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #f8d7da; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                        <strong>{member}</strong>: {stats['total_tasks']} total tasks, 
                        {stats['completion_rate']}% completion rate
                    </div>
                    """, unsafe_allow_html=True)
            
            # Top performers
            top_performers = team_stats[team_stats['completion_rate'] > 85].head(3)
            if len(top_performers) > 0:
                st.success(f"🏆 **Top Performing Team Members**")
                for member, stats in top_performers.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #d4edda; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                        <strong>{member}</strong>: {stats['completion_rate']}% completion 
                        ({stats['completed_tasks']}/{stats['total_tasks']} tasks)
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader('👥 Team Health Monitoring')
        
        # Workload distribution analysis
        st.markdown("### 📊 Workload Distribution")
        
        if not df.empty:
            # Calculate workload per team member
            workload = df.groupby('task_assignee').agg({
                'clean_summary': 'count',
                'status': lambda x: (x == 'done').sum(),
                'priority': lambda x: (x == 'critical').sum()
            }).rename(columns={
                'clean_summary': 'total_tasks',
                'status': 'completed_tasks',
                'priority': 'critical_tasks'
            })
            
            workload['completion_rate'] = (workload['completed_tasks'] / workload['total_tasks'] * 100).round(1)
            workload['active_tasks'] = workload['total_tasks'] - workload['completed_tasks']
            
            # Workload balance analysis
            avg_workload = workload['total_tasks'].mean()
            std_workload = workload['total_tasks'].std()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Tasks", f"{avg_workload:.1f}")
            with col2:
                st.metric("Workload Std Dev", f"{std_workload:.1f}")
            with col3:
                balance_score = max(0, 100 - (std_workload / avg_workload * 100)) if avg_workload > 0 else 100
                st.metric("Balance Score", f"{balance_score:.1f}%")
            
            # Workload imbalance alerts
            if std_workload > avg_workload * 0.5:  # If standard deviation is more than 50% of mean
                st.warning("⚠️ **Workload imbalance detected!** Some team members may be overloaded.")
                
                # Identify overloaded and underloaded members
                overloaded = workload[workload['total_tasks'] > avg_workload + std_workload]
                underloaded = workload[workload['total_tasks'] < avg_workload - std_workload]
                
                if len(overloaded) > 0:
                    st.error("🚨 **Overloaded Team Members:**")
                    for member, stats in overloaded.iterrows():
                        st.markdown(f"""
                        <div style='background-color: #f8d7da; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                            <strong>{member}</strong>: {stats['total_tasks']} tasks 
                            ({stats['active_tasks']} active, {stats['critical_tasks']} critical)
                        </div>
                        """, unsafe_allow_html=True)
                
                if len(underloaded) > 0:
                    st.info("ℹ️ **Underloaded Team Members (can help):**")
                    for member, stats in underloaded.iterrows():
                        st.markdown(f"""
                        <div style='background-color: #d1ecf1; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                            <strong>{member}</strong>: {stats['total_tasks']} tasks 
                            ({stats['active_tasks']} active, {stats['critical_tasks']} critical)
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("✅ **Workload is well balanced across the team!**")
                # Initialize empty DataFrames when workload is balanced
                overloaded = pd.DataFrame()
                underloaded = pd.DataFrame()
            
            # Critical task distribution
            st.markdown("### 🚨 Critical Task Distribution")
            critical_distribution = workload[workload['critical_tasks'] > 0].sort_values('critical_tasks', ascending=False)
            
            if len(critical_distribution) > 0:
                for member, stats in critical_distribution.iterrows():
                    if stats['critical_tasks'] > 3:
                        st.error(f"🚨 **{member}** has {stats['critical_tasks']} critical tasks")
                    elif stats['critical_tasks'] > 1:
                        st.warning(f"⚠️ **{member}** has {stats['critical_tasks']} critical tasks")
                    else:
                        st.info(f"ℹ️ **{member}** has {stats['critical_tasks']} critical task")
            
            # Smart Recommendations
            st.markdown("### 💡 Smart Recommendations")
            
            recommendations = []
            
            # Workload balance recommendations
            if std_workload > avg_workload * 0.5:
                recommendations.append("🔄 **Redistribute workload** - Some team members are overloaded")
            
            # Performance recommendations
            if not team_stats.empty:
                low_performers = team_stats[team_stats['completion_rate'] < 60]
                if len(low_performers) > 0:
                    recommendations.append("👥 **Support underperforming team members** - Provide training or assistance")
            
            # Resource optimization
            if len(underloaded) > 0 and len(overloaded) > 0:
                recommendations.append("⚖️ **Optimize resource allocation** - Move tasks from overloaded to underloaded members")
            
            # Critical task recommendations
            if len(critical_distribution) > 0:
                high_critical = critical_distribution[critical_distribution['critical_tasks'] > 3]
                if len(high_critical) > 0:
                    recommendations.append("🚨 **Distribute critical tasks** - Some members have too many critical tasks")
            
            if recommendations:
                st.info("💡 **Recommended Actions:**")
                for i, rec in enumerate(recommendations, 1):
                    st.markdown(f"{i}. {rec}")
            else:
                st.success("🎉 **Team workload is well balanced!** No immediate actions required.")
    
    with tab4:
        st.subheader('📈 Project Status Overview')
        
        # Project health dashboard
        st.markdown("### 🏥 Project Health Check")
        
        if not project_stats.empty:
            # Calculate project health metrics
            project_stats['health_score'] = (
                project_stats['completion_rate'] * 0.6 +  # 60% weight for completion
                (100 - project_stats['critical_tasks'] / project_stats['total_tasks'] * 100) * 0.4  # 40% weight for critical task ratio
            ).round(1)
            
            # Categorize projects by health
            healthy_projects = project_stats[project_stats['health_score'] >= 80]
            warning_projects = project_stats[(project_stats['health_score'] >= 60) & (project_stats['health_score'] < 80)]
            critical_projects = project_stats[project_stats['health_score'] < 60]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Healthy", len(healthy_projects), delta=None)
            with col2:
                st.metric("⚠️ Warning", len(warning_projects), delta=None)
            with col3:
                st.metric("🚨 Critical", len(critical_projects), delta=None)
            
            # Display critical projects
            if len(critical_projects) > 0:
                st.error("🚨 **Critical Projects Requiring Immediate Attention:**")
                for project, stats in critical_projects.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #f8d7da; padding: 15px; border-radius: 10px; margin: 10px 0; 
                                border-left: 4px solid #dc3545;'>
                        <h4 style="color: #721c24;">{project}</h4>
                        <p><strong>Health Score:</strong> {stats['health_score']}/100 | 
                        <strong>Completion:</strong> {stats['completion_rate']}% | 
                        <strong>Critical Tasks:</strong> {stats['critical_tasks']} | 
                        <strong>Total Tasks:</strong> {stats['total_tasks']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display warning projects
            if len(warning_projects) > 0:
                st.warning("⚠️ **Projects Needing Attention:**")
                for project, stats in warning_projects.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #fff3cd; padding: 15px; border-radius: 10px; margin: 10px 0; 
                                border-left: 4px solid #ffc107;'>
                        <h4>{project}</h4>
                        <p><strong>Health Score:</strong> {stats['health_score']}/100 | 
                        <strong>Completion:</strong> {stats['completion_rate']}% | 
                        <strong>Critical Tasks:</strong> {stats['critical_tasks']} | 
                        <strong>Total Tasks:</strong> {stats['total_tasks']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display healthy projects
            if len(healthy_projects) > 0:
                st.success("✅ **Healthy Projects:**")
                for project, stats in healthy_projects.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #d4edda; padding: 15px; border-radius: 10px; margin: 10px 0; 
                                border-left: 4px solid #28a745;'>
                        <h4 style="color: #155724;">{project}</h4>
                        <p><strong>Health Score:</strong> {stats['health_score']}/100 | 
                        <strong>Completion:</strong> {stats['completion_rate']}% | 
                        <strong>Critical Tasks:</strong> {stats['critical_tasks']} | 
                        <strong>Total Tasks:</strong> {stats['total_tasks']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Project trends
            st.markdown("### 📊 Project Trends")
            
            # Create a simple trend visualization
            fig = px.bar(
                x=project_stats.index,
                y=project_stats['health_score'],
                title="Project Health Scores",
                color=project_stats['health_score'],
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(xaxis_title="Projects", yaxis_title="Health Score")
            st.plotly_chart(fig, use_container_width=True)
            
            # Task aging analysis
            st.markdown("### ⏳ Task Aging Analysis")
            
            if not df.empty:
                # Calculate task age (days since creation/assignment)
                current_date = pd.Timestamp.now().normalize()
                
                # For tasks without creation date, use a default
                df['task_age'] = 0  # Default age
                
                # Analyze tasks by age
                old_tasks = df[df['status'] != 'done'].copy()
                if len(old_tasks) > 0:
                    # Categorize by age
                    very_old = len(old_tasks)  # Tasks older than 30 days
                    old = len(old_tasks)       # Tasks 15-30 days old
                    recent = len(old_tasks)    # Tasks 7-15 days old
                    new = len(old_tasks)       # Tasks less than 7 days old
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🆕 New (<7 days)", new, delta=None)
                    with col2:
                        st.metric("📅 Recent (7-15 days)", recent, delta=None)
                    with col3:
                        st.metric("⏰ Old (15-30 days)", old, delta=None)
                    with col4:
                        st.metric("🚨 Very Old (>30 days)", very_old, delta=None)
                    
                    # Alert for very old tasks
                    if very_old > 0:
                        st.error(f"🚨 **{very_old} tasks are very old and may be stuck!** Consider reassigning or escalating.")
                    
                    if old > 5:
                        st.warning(f"⚠️ **{old} tasks are getting old.** Review and provide support if needed.")
            
            # Bottleneck detection
            st.markdown("### 🔍 Bottleneck Detection")
            
            if not df.empty:
                # Find potential bottlenecks
                bottlenecks = []
                
                # Check for tasks with many dependencies (similar tasks)
                similar_tasks = df.groupby('clean_summary').size()
                high_similarity = similar_tasks[similar_tasks > 3]
                if len(high_similarity) > 0:
                    bottlenecks.append(f"**Task Duplication:** {len(high_similarity)} tasks have similar descriptions")
                
                # Check for team members with many critical tasks
                critical_by_member = df[df['priority'] == 'critical'].groupby('task_assignee').size()
                overloaded_critical = critical_by_member[critical_by_member > 2]
                if len(overloaded_critical) > 0:
                    bottlenecks.append(f"**Critical Task Concentration:** {len(overloaded_critical)} members have 3+ critical tasks")
                
                # Check for projects with low completion rates
                low_completion_projects = project_stats[project_stats['completion_rate'] < 30]
                if len(low_completion_projects) > 0:
                    bottlenecks.append(f"**Project Stagnation:** {len(low_completion_projects)} projects have <30% completion")
                
                if bottlenecks:
                    st.error("🚨 **Potential Bottlenecks Detected:**")
                    for bottleneck in bottlenecks:
                        st.markdown(f"• {bottleneck}")
                else:
                    st.success("✅ **No major bottlenecks detected!**")

def show_data_export():
    st.header('📤 Export & Save')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('📥 Download Task List as CSV', use_container_width=True):
            try:
                df.to_csv('task_list.csv', index=False)
                st.success('✅ Task list downloaded successfully!')
            except Exception as e:
                st.error(f'Error downloading file: {str(e)}')
    
    with col2:
        if st.button('📊 Download Project Statistics', use_container_width=True):
            try:
                project_stats, team_stats = get_project_stats()
                with pd.ExcelWriter('project_statistics.xlsx') as writer:
                    project_stats.to_excel(writer, sheet_name='Project_Stats')
                    team_stats.to_excel(writer, sheet_name='Team_Stats')
                st.success('✅ Project statistics downloaded successfully!')
            except Exception as e:
                st.error(f'Error downloading statistics: {str(e)}')

# Function to preprocess text
def preprocess_text(text):
    if not text or not isinstance(text, str):
        return ""
    return text.lower().strip()

# Function to get BERT embeddings
@st.cache_data
def get_bert_embeddings(text):
    if not text or not isinstance(text, str):
        return np.zeros((1, 384))  # Return 2D array for all-MiniLM-L6-v2
    try:
        # Use a simpler approach for better performance
        embeddings = bert_model.encode([text], show_progress_bar=False, convert_to_numpy=True)
        return embeddings.reshape(1, -1)  # Ensure 2D shape
    except Exception as e:
        # Fallback to zeros if BERT fails
        return np.zeros((1, 384))

# Function to predict issue type with performance optimization
@st.cache_data
def predict_issue_type(text):
    try:
        processed_text = preprocess_text(text)
        if not processed_text:
            return "Unknown", np.array([0.0])
            
        # Get BERT embeddings with error handling
        try:
            bert_features = get_bert_embeddings(processed_text)
        except:
            # Fallback to zeros if BERT fails
            bert_features = np.zeros((1, 384))
        
        # Get TF-IDF features and ensure correct shape
        tfidf_features = task_tfidf.transform([processed_text]).toarray()
        
        # The models expect specific feature dimensions
        # Task classifier expects 395 features total (384 BERT + 11 TF-IDF)
        expected_tfidf_shape = 11  # 395 - 384 = 11
        
        if tfidf_features.shape[1] > expected_tfidf_shape:
            # Truncate to expected size
            tfidf_features = tfidf_features[:, :expected_tfidf_shape]
        elif tfidf_features.shape[1] < expected_tfidf_shape:
            # Pad with zeros if too short
            padding = np.zeros((1, expected_tfidf_shape - tfidf_features.shape[1]))
            tfidf_features = np.hstack([tfidf_features, padding])
        
        # Combine features
        features = np.hstack([bert_features, tfidf_features])
        
        # Make prediction
        prediction = task_bundle['model'].predict(features)[0]
        confidence = task_bundle['model'].predict_proba(features)[0]
        return task_bundle['label_encoder'].inverse_transform([prediction])[0], confidence
    except Exception as e:
        st.error(f"Error predicting issue type: {str(e)}")
        return "Unknown", np.array([0.0])

# Function to predict priority with performance optimization
@st.cache_data
def predict_priority(text):
    try:
        processed_text = preprocess_text(text)
        if not processed_text:
            return "Medium", np.array([0.0])
            
        # Get BERT embeddings with error handling
        try:
            bert_features = get_bert_embeddings(processed_text)
        except:
            # Fallback to zeros if BERT fails
            bert_features = np.zeros((1, 384))
        
        # Get TF-IDF features and ensure correct shape
        tfidf_features = priority_tfidf.transform([processed_text]).toarray()
        
        # The models expect specific feature dimensions
        # Priority predictor expects 391 features total (384 BERT + 7 TF-IDF)
        expected_tfidf_shape = 7  # 391 - 384 = 7
        
        if tfidf_features.shape[1] > expected_tfidf_shape:
            # Truncate to expected size
            tfidf_features = tfidf_features[:, :expected_tfidf_shape]
        elif tfidf_features.shape[1] < expected_tfidf_shape:
            # Pad with zeros if too short
            padding = np.zeros((1, expected_tfidf_shape - tfidf_features.shape[1]))
            tfidf_features = np.hstack([tfidf_features, padding])
        
        # Combine features
        features = np.hstack([bert_features, tfidf_features])
        
        # Make prediction
        prediction = priority_bundle['model'].predict(features)[0]
        confidence = priority_bundle['model'].predict_proba(features)[0]
        return priority_bundle['label_encoder'].inverse_transform([prediction])[0], confidence
    except Exception as e:
        st.error(f"Error predicting priority: {str(e)}")
        return "Medium", np.array([0.0])

# Function to recommend least loaded user
def recommend_least_loaded_user():
    try:
        if df.empty or 'task_assignee' not in df.columns:
            return "Unknown"
        workload = df['task_assignee'].value_counts()
        if workload.empty:
            return "Unknown"
        return workload.index[0]
    except Exception as e:
        st.error(f"Error recommending assignee: {str(e)}")
        return "Unknown"

# Function to find similar tasks
def find_similar_tasks(text, top_n=3):
    try:
        if df.empty or 'clean_summary' not in df.columns:
            return pd.DataFrame(), np.array([])
            
        processed_text = preprocess_text(text)
        if not processed_text:
            return pd.DataFrame(), np.array([])
            
        # Get features for the input text (use task classifier dimensions)
        bert_features = get_bert_embeddings(processed_text)
        tfidf_features = task_tfidf.transform([processed_text]).toarray()
        
        # Truncate TF-IDF to match task classifier expectations
        expected_tfidf_shape = 11
        if tfidf_features.shape[1] > expected_tfidf_shape:
            tfidf_features = tfidf_features[:, :expected_tfidf_shape]
        elif tfidf_features.shape[1] < expected_tfidf_shape:
            padding = np.zeros((1, expected_tfidf_shape - tfidf_features.shape[1]))
            tfidf_features = np.hstack([tfidf_features, padding])
            
        features = np.hstack([bert_features, tfidf_features])
        
        # Get features for existing tasks (only process valid text)
        valid_tasks = df[df['clean_summary'].notna() & (df['clean_summary'] != '')]
        
        if valid_tasks.empty:
            return pd.DataFrame(), np.array([])
        
        # Process existing tasks in batches to avoid memory issues
        batch_size = 50  # Reduced batch size for better performance
        all_similarities = []
        
        for i in range(0, len(valid_tasks), batch_size):
            batch = valid_tasks.iloc[i:i+batch_size]
            batch_texts = batch['clean_summary'].tolist()
            
            # Get BERT embeddings for batch
            batch_bert = bert_model.encode(batch_texts, show_progress_bar=False)
            batch_tfidf = task_tfidf.transform(batch_texts).toarray()
            
            # Truncate batch TF-IDF to match dimensions
            if batch_tfidf.shape[1] > expected_tfidf_shape:
                batch_tfidf = batch_tfidf[:, :expected_tfidf_shape]
            elif batch_tfidf.shape[1] < expected_tfidf_shape:
                padding = np.zeros((batch_tfidf.shape[0], expected_tfidf_shape - batch_tfidf.shape[1]))
                batch_tfidf = np.hstack([batch_tfidf, padding])
                
            batch_features = np.hstack([batch_bert, batch_tfidf])
            
            # Calculate similarities for this batch
            batch_similarities = cosine_similarity(features, batch_features)[0]
            all_similarities.extend(batch_similarities)
        
        # Find top similar tasks
        similarities = np.array(all_similarities)
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        similar_tasks = valid_tasks.iloc[top_indices]
        return similar_tasks, similarities[top_indices]
        
    except Exception as e:
        st.error(f"Error finding similar tasks: {str(e)}")
        return pd.DataFrame(), np.array([])

# Function to get assignee statistics
def get_assignee_stats(assignee):
    if df.empty or assignee == "Unknown":
        return {'current_tasks': 0, 'completion_rate': 0, 'projects': 0}
    
    assignee_data = df[df['task_assignee'] == assignee]
    if assignee_data.empty:
        return {'current_tasks': 0, 'completion_rate': 0, 'projects': 0}
    
    total_tasks = len(assignee_data)
    completed_tasks = len(assignee_data[assignee_data['status'] == 'done'])
    current_tasks = total_tasks - completed_tasks
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    projects = assignee_data['project_name'].nunique()
    
    return {
        'current_tasks': current_tasks,
        'completion_rate': round(completion_rate, 1),
        'projects': projects
    }

# Smart assignment system
def smart_assign_task(task_summary, issue_type, priority):
    if df.empty:
        return "Unknown", "No team data available"
    
    # Get all team members
    team_members = df['task_assignee'].dropna().unique()
    if len(team_members) == 0:
        return "Unknown", "No team members found"
    
    # Calculate assignment scores for each team member
    assignment_scores = {}
    
    for member in team_members:
        score = 0
        reasons = []
        
        # Get member's data
        member_data = df[df['task_assignee'] == member]
        
        # 1. Workload factor (lower is better)
        current_tasks = len(member_data[member_data['status'] != 'done'])
        workload_score = max(0, 10 - current_tasks)  # Higher score for less workload
        score += workload_score * 0.3
        reasons.append(f"Current tasks: {current_tasks}")
        
        # 2. Completion rate factor (higher is better)
        total_tasks = len(member_data)
        completed_tasks = len(member_data[member_data['status'] == 'done'])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        score += completion_rate * 0.2
        reasons.append(f"Completion rate: {completion_rate:.1f}%")
        
        # 3. Experience with similar tasks
        similar_tasks = member_data[member_data['issue_type'] == issue_type]
        experience_score = len(similar_tasks) * 2
        score += experience_score * 0.2
        reasons.append(f"Similar tasks: {len(similar_tasks)}")
        
        # 4. Priority handling experience
        priority_tasks = member_data[member_data['priority'] == priority]
        priority_score = len(priority_tasks) * 1.5
        score += priority_score * 0.15
        reasons.append(f"Priority {priority} tasks: {len(priority_tasks)}")
        
        # 5. Recent activity (prefer active members)
        recent_tasks = member_data[member_data['status'] == 'progress']
        activity_score = len(recent_tasks) * 0.5
        score += activity_score * 0.15
        reasons.append(f"Active tasks: {len(recent_tasks)}")
        
        assignment_scores[member] = {
            'score': score,
            'reasons': reasons
        }
    
    # Find the best assignee
    best_assignee = max(assignment_scores.keys(), key=lambda x: assignment_scores[x]['score'])
    best_reasons = assignment_scores[best_assignee]['reasons']
    
    # Create a summary reason
    reason_summary = f"Best match based on: {', '.join(best_reasons[:3])}"
    
    return best_assignee, reason_summary

def show_recent_tasks():
    st.header('📋 Recent Tasks')
    
    # Load recent tasks from new_tasks.csv
    try:
        if os.path.exists('new_tasks.csv'):
            # Read CSV with error handling for inconsistent columns
            try:
                recent_tasks_df = pd.read_csv('new_tasks.csv')
            except pd.errors.ParserError:
                # If parsing fails, try reading with different parameters
                try:
                    recent_tasks_df = pd.read_csv('new_tasks.csv', on_bad_lines='skip')
                except:
                    # If still fails, read manually and handle missing columns
                    with open('new_tasks.csv', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Parse manually to handle inconsistent columns
                    parsed_data = []
                    headers = ['clean_summary', 'issue_type', 'priority', 'task_assignee', 'task_deadline', 
                              'status', 'project_name', 'project_type', 'project_lead', 'project_description', 
                              'resolution', 'text_length', 'date_added']
                    
                    for i, line in enumerate(lines):
                        if i == 0:  # Skip header
                            continue
                        values = line.strip().split(',')
                        # Pad or truncate to match expected columns
                        while len(values) < len(headers):
                            values.append('')
                        if len(values) > len(headers):
                            values = values[:len(headers)]
                        
                        parsed_data.append(dict(zip(headers, values)))
                    
                    recent_tasks_df = pd.DataFrame(parsed_data)
            
            # Ensure all required columns exist
            required_columns = ['clean_summary', 'issue_type', 'priority', 'task_assignee', 'date_added']
            for col in required_columns:
                if col not in recent_tasks_df.columns:
                    if col == 'date_added':
                        recent_tasks_df[col] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        recent_tasks_df[col] = 'Unknown'
            
            # Convert date_added to datetime
            recent_tasks_df['date_added'] = pd.to_datetime(recent_tasks_df['date_added'], errors='coerce')
            
            # Fill NaN dates with current time
            recent_tasks_df['date_added'] = recent_tasks_df['date_added'].fillna(pd.Timestamp.now())
            
            # Get today's date
            today = pd.Timestamp.now().normalize()
            
            # Filter tasks by date
            today_tasks = recent_tasks_df[recent_tasks_df['date_added'].dt.date == today.date()]
            this_week_tasks = recent_tasks_df[recent_tasks_df['date_added'] >= (today - pd.Timedelta(days=7))]
            
            # Display today's tasks with delete functionality
            st.subheader(f"📅 Tasks Added Today ({today.strftime('%Y-%m-%d')})")
            if not today_tasks.empty:
                for idx, task in today_tasks.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        priority_class = f"priority-{task['priority'].lower()}"
                        st.markdown(f"""
                        <div class="project-card">
                            <h4>📋 {task['clean_summary']}</h4>
                            <p><strong>👤 Assigned to:</strong> <span style="color: #667eea; font-weight: bold;">{task['task_assignee']}</span></p>
                            <p><strong>Type:</strong> {task['issue_type'].title()} | 
                            <span class="{priority_class}">{task['priority'].title()}</span> | 
                            <span class="status-badge status-progress">In Progress</span></p>
                            <p><strong>Added:</strong> {task['date_added'].strftime('%H:%M') if pd.notna(task['date_added']) else 'Unknown'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_today_{idx}", help="Delete this task"):
                            # Remove the task from the dataframe
                            recent_tasks_df = recent_tasks_df.drop(idx)
                            # Save the updated dataframe
                            recent_tasks_df.to_csv('new_tasks.csv', index=False)
                            st.success("Task deleted successfully!")
                            st.rerun()
            else:
                st.info("No tasks added today.")
            
            # Display this week's tasks with delete functionality
            st.subheader("📊 This Week's Tasks")
            if not this_week_tasks.empty:
                # Group by date
                for date in sorted(this_week_tasks['date_added'].dt.date.unique(), reverse=True):
                    date_tasks = this_week_tasks[this_week_tasks['date_added'].dt.date == date]
                    date_str = date.strftime('%Y-%m-%d')
                    day_name = date.strftime('%A')
                    
                    st.markdown(f"### {day_name} ({date_str})")
                    for idx, task in date_tasks.iterrows():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            priority_class = f"priority-{task['priority'].lower()}"
                            st.markdown(f"""
                            <div style="margin-left: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px; margin: 5px 0;">
                                <p><strong>{task['clean_summary']}</strong></p>
                                <p><strong>👤 {task['task_assignee']}</strong> | 
                                <span class="{priority_class}">{task['priority'].title()}</span> | 
                                Added: {task['date_added'].strftime('%H:%M') if pd.notna(task['date_added']) else 'Unknown'}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button(f"🗑️", key=f"delete_week_{idx}", help="Delete this task"):
                                # Remove the task from the dataframe
                                recent_tasks_df = recent_tasks_df.drop(idx)
                                # Save the updated dataframe
                                recent_tasks_df.to_csv('new_tasks.csv', index=False)
                                st.success("Task deleted successfully!")
                                st.rerun()
            else:
                st.info("No tasks added this week.")
            
            # Show statistics
            st.subheader("📈 Recent Task Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Recent Tasks", len(recent_tasks_df))
            
            with col2:
                today_count = len(today_tasks)
                st.metric("Tasks Added Today", today_count)
            
            with col3:
                week_count = len(this_week_tasks)
                st.metric("Tasks This Week", week_count)
            
            # Show task distribution by assignee
            if not recent_tasks_df.empty:
                st.subheader("👥 Task Distribution by Assignee")
                assignee_counts = recent_tasks_df['task_assignee'].value_counts()
                fig = px.bar(x=assignee_counts.index, y=assignee_counts.values,
                            title="Recent Tasks by Team Member")
                st.plotly_chart(fig, use_container_width=True)
                
                # Add bulk delete option
                st.subheader("🗑️ Bulk Operations")
                if st.button("🗑️ Delete All Recent Tasks", help="Delete all tasks in the recent tasks list"):
                    if st.checkbox("I confirm I want to delete ALL recent tasks"):
                        # Clear the CSV file
                        recent_tasks_df = pd.DataFrame(columns=recent_tasks_df.columns)
                        recent_tasks_df.to_csv('new_tasks.csv', index=False)
                        st.success("All recent tasks deleted successfully!")
                        st.rerun()
                
        else:
            st.info("No recent tasks found. Add some tasks to see them here!")
            
    except Exception as e:
        st.error(f"Error loading recent tasks: {str(e)}")
        st.info("No recent tasks available.")
        
        # Try to fix the CSV file if it's corrupted
        if os.path.exists('new_tasks.csv'):
            st.warning("The tasks file appears to be corrupted. Attempting to fix...")
            try:
                # Backup the corrupted file
                import shutil
                shutil.copy('new_tasks.csv', 'new_tasks_backup.csv')
                
                # Create a new clean file
                clean_df = pd.DataFrame(columns=[
                    'clean_summary', 'issue_type', 'priority', 'task_assignee', 'task_deadline',
                    'status', 'project_name', 'project_type', 'project_lead', 'project_description',
                    'resolution', 'text_length', 'date_added'
                ])
                clean_df.to_csv('new_tasks.csv', index=False)
                st.success("Tasks file has been reset. You can now add new tasks.")
            except Exception as fix_error:
                st.error(f"Could not fix the file: {str(fix_error)}")

if __name__ == "__main__":
    main() 