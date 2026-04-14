import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # type: ignore
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns  # type: ignore
import streamlit as st
from scipy.stats import pearsonr  # type: ignore

# Page configuration
st.set_page_config(
    page_title="EduPro Instructor Performance Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .insight-box {
        background-color: #f0f8ff;
        border-left: 5px solid #3498db;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Load data function with caching
@st.cache_data
def load_data():
    """Load all required datasets"""
    try:
        teachers_df = pd.read_csv('teachers.csv')
        courses_df = pd.read_csv('courses.csv')
        transactions_df = pd.read_csv('transactions.csv')
        
        # Merge datasets
        merged_df = transactions_df.merge(courses_df, on='CourseID', how='left')
        merged_df = merged_df.merge(teachers_df, on='TeacherID', how='left')
        
        # Create instructor profile
        instructor_profile = teachers_df.copy()
        enrollment_counts = merged_df.groupby('TeacherID').size().reset_index(name='TotalEnrollments')
        instructor_profile = instructor_profile.merge(enrollment_counts, on='TeacherID', how='left')
        instructor_profile['TotalEnrollments'].fillna(0, inplace=True)
        
        avg_course_rating = merged_df.groupby('TeacherID')['CourseRating'].mean().reset_index(name='AvgCourseRating')
        instructor_profile = instructor_profile.merge(avg_course_rating, on='TeacherID', how='left')
        
        # Rating tiers
        instructor_profile['RatingTier'] = pd.cut(
            instructor_profile['TeacherRating'], 
            bins=[0, 3.5, 4.0, 5.0], 
            labels=['Low-Rated (≤3.5)', 'Mid-Rated (3.5-4.0)', 'High-Rated (>4.0)']
        )
        
        merged_df = merged_df.merge(
            instructor_profile[['TeacherID', 'RatingTier']], 
            on='TeacherID', 
            how='left'
        )
        
        return teachers_df, courses_df, transactions_df, merged_df, instructor_profile
    except FileNotFoundError as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# Load all data
teachers_df, courses_df, transactions_df, merged_df, instructor_profile = load_data()

# Sidebar
st.sidebar.image("https://via.placeholder.com/300x100/667eea/ffffff?text=EduPro+Analytics", use_container_width=True)
st.sidebar.markdown("## 🎯 Navigation")
page = st.sidebar.radio(
    "Select Analysis View:",
    ["🏠 Overview Dashboard", "👨‍🏫 Instructor Performance", "📚 Course Quality", 
     "🎓 Expertise Analysis", "📊 Detailed Analytics", "💡 Insights & Recommendations"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

# Global filters
selected_expertise = st.sidebar.multiselect(
    "Filter by Expertise:",
    options=sorted(instructor_profile['Expertise'].dropna().unique()),
    default=None
)

selected_category = st.sidebar.multiselect(
    "Filter by Course Category:",
    options=sorted(merged_df['CourseCategory'].dropna().unique()),
    default=None
)

selected_level = st.sidebar.multiselect(
    "Filter by Course Level:",
    options=sorted(merged_df['CourseLevel'].dropna().unique()),
    default=None
)

rating_range = st.sidebar.slider(
    "Instructor Rating Range:",
    min_value=float(instructor_profile['TeacherRating'].min()),
    max_value=float(instructor_profile['TeacherRating'].max()),
    value=(float(instructor_profile['TeacherRating'].min()), 
           float(instructor_profile['TeacherRating'].max())),
    step=0.1
)

# Apply filters
filtered_instructors = instructor_profile.copy()
filtered_merged = merged_df.copy()

if selected_expertise:
    filtered_instructors = filtered_instructors[filtered_instructors['Expertise'].isin(selected_expertise)]
    filtered_merged = filtered_merged[filtered_merged['Expertise'].isin(selected_expertise)]

if selected_category:
    filtered_merged = filtered_merged[filtered_merged['CourseCategory'].isin(selected_category)]

if selected_level:
    filtered_merged = filtered_merged[filtered_merged['CourseLevel'].isin(selected_level)]

filtered_instructors = filtered_instructors[
    (filtered_instructors['TeacherRating'] >= rating_range[0]) & 
    (filtered_instructors['TeacherRating'] <= rating_range[1])
]

filtered_merged = filtered_merged[
    (filtered_merged['TeacherRating'] >= rating_range[0]) & 
    (filtered_merged['TeacherRating'] <= rating_range[1])
]

# Main content
st.markdown('<h1 class="main-header">📚 EduPro Instructor Performance & Course Quality Dashboard</h1>', unsafe_allow_html=True)

# ============================================================================
# PAGE 1: OVERVIEW DASHBOARD
# ============================================================================
if page == "🏠 Overview Dashboard":
    st.markdown('<h2 class="sub-header">Executive Summary</h2>', unsafe_allow_html=True)
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        avg_teacher_rating = filtered_instructors['TeacherRating'].mean()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_teacher_rating:.2f}</div>
                <div class="metric-label">Avg Teacher Rating</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_course_rating = filtered_merged['CourseRating'].mean()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_course_rating:.2f}</div>
                <div class="metric-label">Avg Course Rating</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_instructors = filtered_instructors['TeacherID'].nunique()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_instructors}</div>
                <div class="metric-label">Total Instructors</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_courses = filtered_merged['CourseID'].nunique()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_courses}</div>
                <div class="metric-label">Total Courses</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        total_enrollments = filtered_merged['TransactionID'].count()
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_enrollments:,}</div>
                <div class="metric-label">Total Enrollments</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two-column layout for visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Instructor Rating Distribution
        fig1 = go.Figure()
        fig1.add_trace(go.Histogram(
            x=filtered_instructors['TeacherRating'],
            nbinsx=20,
            marker_color='#3498db',
            name='Frequency',
            opacity=0.7
        ))
        fig1.add_vline(x=avg_teacher_rating, line_dash="dash", line_color="red", 
                      annotation_text=f"Mean: {avg_teacher_rating:.2f}")
        fig1.update_layout(
            title="📊 Instructor Rating Distribution",
            xaxis_title="Teacher Rating",
            yaxis_title="Frequency",
            showlegend=False,
            height=400,
            template="plotly_white"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Rating Tier Distribution
        tier_counts = filtered_instructors['RatingTier'].value_counts()
        fig2 = go.Figure(data=[go.Pie(
            labels=tier_counts.index,
            values=tier_counts.values,
            marker_colors=['#e74c3c', '#f39c12', '#2ecc71'],
            hole=0.4
        )])
        fig2.update_layout(
            title="🎯 Instructor Rating Tier Distribution",
            height=400,
            template="plotly_white"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Experience vs Performance
    col1, col2 = st.columns(2)
    
    with col1:
        # Experience vs Teacher Rating
        fig3 = px.scatter(
            filtered_instructors,
            x='YearsOfExperience',
            y='TeacherRating',
            color='Gender',
            size='TotalEnrollments',
            hover_data=['TeacherName', 'Expertise'],
            title="📈 Experience vs Teacher Rating",
            trendline="ols",
            color_discrete_map={'Male': '#3498db', 'Female': '#e74c3c'}
        )
        fig3.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Course Quality by Level
        level_stats = filtered_merged.groupby('CourseLevel')['CourseRating'].mean().reset_index()
        fig4 = px.bar(
            level_stats,
            x='CourseLevel',
            y='CourseRating',
            title="📚 Average Course Rating by Level",
            color='CourseRating',
            color_continuous_scale='Blues',
            text='CourseRating'
        )
        fig4.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig4.update_layout(height=400, template="plotly_white", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Enrollment Analysis
    st.markdown('<h2 class="sub-header">Enrollment Insights</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 Categories by Enrollment
        category_enrollments = filtered_merged.groupby('CourseCategory').size().nlargest(10).reset_index(name='Enrollments')
        fig5 = px.bar(
            category_enrollments,
            y='CourseCategory',
            x='Enrollments',
            orientation='h',
            title="🔥 Top 10 Course Categories by Enrollment",
            color='Enrollments',
            color_continuous_scale='Viridis'
        )
        fig5.update_layout(height=400, template="plotly_white", showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)
    
    with col2:
        # Instructor Impact on Enrollments
        tier_enrollments = filtered_merged.groupby('RatingTier').size().reset_index(name='Enrollments')
        fig6 = px.bar(
            tier_enrollments,
            x='RatingTier',
            y='Enrollments',
            title="⭐ Enrollments by Instructor Quality Tier",
            color='Enrollments',
            color_continuous_scale='RdYlGn',
            text='Enrollments'
        )
        fig6.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig6.update_layout(height=400, template="plotly_white", showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)

# ============================================================================
# PAGE 2: INSTRUCTOR PERFORMANCE
# ============================================================================
elif page == "👨‍🏫 Instructor Performance":
    st.markdown('<h2 class="sub-header">Instructor Performance Leaderboard</h2>', unsafe_allow_html=True)
    
    # Leaderboard selector
    leaderboard_type = st.radio(
        "Select Leaderboard Type:",
        ["🏆 Top Performers", "⚠️ Needs Improvement", "📊 All Instructors"],
        horizontal=True
    )
    
    if leaderboard_type == "🏆 Top Performers":
        display_df = filtered_instructors.nlargest(20, 'TeacherRating')
        st.success(f"**Showing Top 20 Instructors** (Total: {len(filtered_instructors)})")
    elif leaderboard_type == "⚠️ Needs Improvement":
        display_df = filtered_instructors.nsmallest(20, 'TeacherRating')
        st.warning(f"**Showing Bottom 20 Instructors** (Total: {len(filtered_instructors)})")
    else:
        display_df = filtered_instructors.sort_values('TeacherRating', ascending=False)
        st.info(f"**Showing All {len(filtered_instructors)} Instructors**")
    
    # Display formatted table
    st.dataframe(
        display_df[['TeacherName', 'TeacherRating', 'YearsOfExperience', 'Expertise', 
                   'Gender', 'Age', 'TotalEnrollments', 'AvgCourseRating']].style.format({
            'TeacherRating': '{:.2f}',
            'YearsOfExperience': '{:.0f}',
            'Age': '{:.0f}',
            'TotalEnrollments': '{:.0f}',
            'AvgCourseRating': '{:.2f}'
        }).background_gradient(subset=['TeacherRating'], cmap='RdYlGn'),
        use_container_width=True,
        height=500
    )
    
    st.markdown("---")
    
    # Performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Age distribution
        fig1 = px.histogram(
            filtered_instructors,
            x='Age',
            nbins=15,
            title="👥 Instructor Age Distribution",
            color_discrete_sequence=['#9b59b6'],
            marginal="box"
        )
        fig1.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Experience distribution
        fig2 = px.histogram(
            filtered_instructors,
            x='YearsOfExperience',
            nbins=20,
            title="📅 Teaching Experience Distribution",
            color_discrete_sequence=['#2ecc71'],
            marginal="box"
        )
        fig2.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Correlation Analysis
    st.markdown('<h2 class="sub-header">Performance Correlation Analysis</h2>', unsafe_allow_html=True)
    
    # Calculate correlations
    valid_instructors = filtered_instructors.dropna(subset=['AvgCourseRating'])
    if len(valid_instructors) > 1:
        corr_exp_teacher, _ = pearsonr(valid_instructors['YearsOfExperience'], valid_instructors['TeacherRating'])
        corr_exp_course, _ = pearsonr(valid_instructors['YearsOfExperience'], valid_instructors['AvgCourseRating'])
        corr_teacher_course, _ = pearsonr(valid_instructors['TeacherRating'], valid_instructors['AvgCourseRating'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Experience ↔ Teacher Rating",
                f"{corr_exp_teacher:.3f}",
                delta="Correlation Strength"
            )
        
        with col2:
            st.metric(
                "Experience ↔ Course Rating",
                f"{corr_exp_course:.3f}",
                delta="Correlation Strength"
            )
        
        with col3:
            st.metric(
                "Teacher ↔ Course Rating",
                f"{corr_teacher_course:.3f}",
                delta="Correlation Strength"
            )
        
        # Correlation heatmap
        correlation_data = valid_instructors[['Age', 'YearsOfExperience', 'TeacherRating', 
                                             'TotalEnrollments', 'AvgCourseRating']].corr()
        
        fig = px.imshow(
            correlation_data,
            text_auto='.3f',
            aspect="auto",
            title="🔗 Instructor Metrics Correlation Matrix",
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1
        )
        fig.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 3: COURSE QUALITY
# ============================================================================
elif page == "📚 Course Quality":
    st.markdown('<h2 class="sub-header">Course Quality Evaluation</h2>', unsafe_allow_html=True)
    
    # Category performance
    col1, col2 = st.columns(2)
    
    with col1:
        # Average rating by category
        category_stats = filtered_merged.groupby('CourseCategory').agg({
            'CourseRating': 'mean',
            'TransactionID': 'count'
        }).reset_index()
        category_stats.columns = ['CourseCategory', 'AvgRating', 'Enrollments']
        category_stats = category_stats.sort_values('AvgRating', ascending=False)
        
        fig1 = px.bar(
            category_stats,
            y='CourseCategory',
            x='AvgRating',
            orientation='h',
            title="📊 Average Course Rating by Category",
            color='AvgRating',
            color_continuous_scale='Blues',
            text='AvgRating'
        )
        fig1.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig1.update_layout(height=500, template="plotly_white", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Bubble chart: Category performance
        fig2 = px.scatter(
            category_stats,
            x='Enrollments',
            y='AvgRating',
            size='Enrollments',
            color='AvgRating',
            text='CourseCategory',
            title="🎯 Category Performance: Quality vs Popularity",
            color_continuous_scale='Viridis',
            size_max=60
        )
        fig2.update_traces(textposition='top center')
        fig2.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Level analysis
    st.markdown('<h2 class="sub-header">Course Level Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating by level
        level_stats = filtered_merged.groupby('CourseLevel')['CourseRating'].mean().reset_index()
        fig3 = px.bar(
            level_stats,
            x='CourseLevel',
            y='CourseRating',
            title="📈 Average Rating by Course Level",
            color='CourseRating',
            color_continuous_scale='RdYlGn',
            text='CourseRating'
        )
        fig3.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig3.update_layout(height=400, template="plotly_white", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Enrollment by level
        level_enrollments = filtered_merged.groupby('CourseLevel').size().reset_index(name='Enrollments')
        fig4 = px.pie(
            level_enrollments,
            values='Enrollments',
            names='CourseLevel',
            title="🎓 Enrollment Distribution by Level",
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig4.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
    
    # Detailed course table
    st.markdown('<h2 class="sub-header">Course Performance Details</h2>', unsafe_allow_html=True)
    
    course_details = filtered_merged.groupby(['CourseID', 'CourseName', 'CourseCategory', 'CourseLevel']).agg({
        'CourseRating': 'mean',
        'TransactionID': 'count',
        'TeacherRating': 'mean'
    }).reset_index()
    course_details.columns = ['CourseID', 'CourseName', 'Category', 'Level', 
                              'CourseRating', 'Enrollments', 'AvgInstructorRating']
    course_details = course_details.sort_values('CourseRating', ascending=False)
    
    st.dataframe(
        course_details.head(50).style.format({
            'CourseRating': '{:.2f}',
            'Enrollments': '{:.0f}',
            'AvgInstructorRating': '{:.2f}'
        }).background_gradient(subset=['CourseRating'], cmap='RdYlGn'),
        use_container_width=True,
        height=400
    )

# ============================================================================
# PAGE 4: EXPERTISE ANALYSIS
# ============================================================================
elif page == "🎓 Expertise Analysis":
    st.markdown('<h2 class="sub-header">Expertise Performance Overview</h2>', unsafe_allow_html=True)
    
    # Expertise statistics
    expertise_stats = filtered_instructors.groupby('Expertise').agg({
        'TeacherRating': ['mean', 'median', 'std', 'count'],
        'TotalEnrollments': 'sum',
        'AvgCourseRating': 'mean'
    }).round(3)
    expertise_stats.columns = ['Avg_Teacher_Rating', 'Median_Teacher_Rating', 
                               'Std_Teacher_Rating', 'Num_Instructors', 
                               'Total_Enrollments', 'Avg_Course_Rating']
    expertise_stats = expertise_stats.reset_index()
    expertise_stats = expertise_stats.sort_values('Avg_Teacher_Rating', ascending=False)
    
    # Top performing expertise areas
    col1, col2 = st.columns(2)
    
    with col1:
        top_expertise = expertise_stats.nlargest(10, 'Avg_Teacher_Rating')
        fig1 = px.bar(
            top_expertise,
            y='Expertise',
            x='Avg_Teacher_Rating',
            orientation='h',
            title="🏆 Top 10 Expertise Areas by Instructor Quality",
            color='Avg_Teacher_Rating',
            color_continuous_scale='Blues',
            text='Avg_Teacher_Rating'
        )
        fig1.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig1.update_layout(height=500, template="plotly_white", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        popular_expertise = expertise_stats.nlargest(10, 'Total_Enrollments')
        fig2 = px.bar(
            popular_expertise,
            x='Expertise',
            y='Total_Enrollments',
            title="📈 Top 10 Most Popular Expertise Areas",
            color='Total_Enrollments',
            color_continuous_scale='Viridis',
            text='Total_Enrollments'
        )
        fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig2.update_layout(height=500, template="plotly_white", showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Instructor count by expertise
    st.markdown('<h2 class="sub-header">Expertise Distribution</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        instructor_count = expertise_stats.nlargest(15, 'Num_Instructors')
        fig3 = px.bar(
            instructor_count,
            x='Expertise',
            y='Num_Instructors',
            title="👥 Instructor Count by Expertise",
            color='Num_Instructors',
            color_continuous_scale='Reds',
            text='Num_Instructors'
        )
        fig3.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig3.update_layout(height=400, template="plotly_white", showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Expertise quality vs popularity
        fig4 = px.scatter(
            expertise_stats,
            x='Total_Enrollments',
            y='Avg_Teacher_Rating',
            size='Num_Instructors',
            color='Avg_Course_Rating',
            text='Expertise',
            title="🎯 Expertise Performance Matrix",
            color_continuous_scale='RdYlGn',
            size_max=40
        )
        fig4.update_traces(textposition='top center', textfont_size=8)
        fig4.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
    
    # Detailed expertise table
    st.markdown('<h2 class="sub-header">Detailed Expertise Statistics</h2>', unsafe_allow_html=True)
    
    st.dataframe(
        expertise_stats.style.format({
            'Avg_Teacher_Rating': '{:.2f}',
            'Median_Teacher_Rating': '{:.2f}',
            'Std_Teacher_Rating': '{:.2f}',
            'Num_Instructors': '{:.0f}',
            'Total_Enrollments': '{:.0f}',
            'Avg_Course_Rating': '{:.2f}'
        }).background_gradient(subset=['Avg_Teacher_Rating'], cmap='RdYlGn'),
        use_container_width=True,
        height=400
    )

# ============================================================================
# PAGE 5: DETAILED ANALYTICS
# ============================================================================
elif page == "📊 Detailed Analytics":
    st.markdown('<h2 class="sub-header">Advanced Statistical Analysis</h2>', unsafe_allow_html=True)
    
    # Instructor tier analysis
    tier_analysis = filtered_merged.groupby('RatingTier').agg({
        'CourseRating': ['mean', 'median', 'std'],
        'TransactionID': 'count',
        'TeacherID': 'nunique'
    }).round(3)
    tier_analysis.columns = ['Avg_Course_Rating', 'Median_Course_Rating', 
                            'Std_Course_Rating', 'Total_Enrollments', 'Num_Instructors']
    
    st.markdown("### 🎯 Instructor Impact by Rating Tier")
    st.dataframe(tier_analysis, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Course rating by instructor tier (Box plot)
        fig1 = px.box(
            filtered_merged[filtered_merged['RatingTier'].notna()],
            x='RatingTier',
            y='CourseRating',
            title="📦 Course Quality Distribution by Instructor Tier",
            color='RatingTier',
            color_discrete_map={
                'Low-Rated (≤3.5)': '#e74c3c',
                'Mid-Rated (3.5-4.0)': '#f39c12',
                'High-Rated (>4.0)': '#2ecc71'
            }
        )
        fig1.update_layout(height=450, template="plotly_white", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Enrollment volume by tier
        tier_enrollments = tier_analysis.reset_index()
        fig2 = px.bar(
            tier_enrollments,
            x='RatingTier',
            y='Total_Enrollments',
            title="📊 Enrollment Volume by Instructor Quality",
            color='Total_Enrollments',
            color_continuous_scale='Viridis',
            text='Total_Enrollments'
        )
        fig2.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig2.update_layout(height=450, template="plotly_white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Gender analysis
    st.markdown('<h2 class="sub-header">Gender-Based Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gender distribution
        gender_counts = filtered_instructors['Gender'].value_counts()
        fig3 = px.pie(
            values=gender_counts.values,
            names=gender_counts.index,
            title="👥 Gender Distribution of Instructors",
            color_discrete_sequence=['#3498db', '#e74c3c']
        )
        fig3.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Gender vs rating comparison
        gender_ratings = filtered_instructors.groupby('Gender')['TeacherRating'].mean().reset_index()
        fig4 = px.bar(
            gender_ratings,
            x='Gender',
            y='TeacherRating',
            title="⭐ Average Rating by Gender",
            color='TeacherRating',
            color_continuous_scale='RdYlGn',
            text='TeacherRating'
        )
        fig4.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig4.update_layout(height=400, template="plotly_white", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Gender by course level
    gender_level = filtered_merged.groupby(['Gender', 'CourseLevel']).size().reset_index(name='Count')
    fig5 = px.bar(
        gender_level,
        x='Gender',
        y='Count',
        color='CourseLevel',
        title="📚 Gender Distribution by Course Level",
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig5.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig5, use_container_width=True)
    
    # Statistical summary
    st.markdown('<h2 class="sub-header">Statistical Summary</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Instructor Statistics")
        st.dataframe(
            filtered_instructors[['Age', 'YearsOfExperience', 'TeacherRating', 
                                 'TotalEnrollments']].describe().T.style.format('{:.2f}'),
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### 📋 Course Statistics")
        st.dataframe(
            filtered_merged[['CourseRating']].describe().T.style.format('{:.2f}'),
            use_container_width=True
        )

# ============================================================================
# PAGE 6: INSIGHTS & RECOMMENDATIONS
# ============================================================================
elif page == "💡 Insights & Recommendations":
    st.markdown('<h2 class="sub-header">Key Insights & Strategic Recommendations</h2>', unsafe_allow_html=True)
    
    # Calculate KPIs
    avg_teacher_rating = filtered_instructors['TeacherRating'].mean()
    avg_course_rating = filtered_merged['CourseRating'].mean()
    teacher_rating_std = filtered_instructors['TeacherRating'].std()
    rating_consistency_index = 1 / (1 + teacher_rating_std)
    
    valid_instructors = filtered_instructors.dropna(subset=['AvgCourseRating'])
    if len(valid_instructors) > 1:
        corr_exp_teacher, _ = pearsonr(valid_instructors['YearsOfExperience'], valid_instructors['TeacherRating'])
        corr_teacher_course, _ = pearsonr(valid_instructors['TeacherRating'], valid_instructors['AvgCourseRating'])
    else:
        corr_exp_teacher = 0
        corr_teacher_course = 0
    
    high_rated_enrollments = filtered_merged[filtered_merged['RatingTier'] == 'High-Rated (>4.0)']['TransactionID'].count()
    total_enrollments = filtered_merged['TransactionID'].count()
    enrollment_influence_ratio = high_rated_enrollments / total_enrollments if total_enrollments > 0 else 0
    
    # KPI Cards
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Teacher Rating", f"{avg_teacher_rating:.2f}/5.0", 
                 delta=f"{avg_teacher_rating - 3.5:.2f} above baseline")
    
    with col2:
        st.metric("Avg Course Rating", f"{avg_course_rating:.2f}/5.0",
                 delta=f"{avg_course_rating - 3.5:.2f} above baseline")
    
    with col3:
        st.metric("Consistency Index", f"{rating_consistency_index:.3f}",
                 delta="Higher = More Consistent")
    
    with col4:
        st.metric("High-Rated Share", f"{enrollment_influence_ratio:.1%}",
                 delta="Enrollments with top instructors")
    
    st.markdown("---")
    
    # Key Insights
    st.markdown("### 🔍 Key Insights")
    
    insights = [
        {
            "title": "📈 Instructor Performance Distribution",
            "content": f"""
            - Average instructor rating is **{avg_teacher_rating:.2f}/5.0**, indicating {'strong' if avg_teacher_rating > 4.0 else 'moderate' if avg_teacher_rating > 3.5 else 'concerning'} overall quality
            - Rating consistency index of **{rating_consistency_index:.3f}** shows {'high' if rating_consistency_index > 0.7 else 'moderate' if rating_consistency_index > 0.5 else 'low'} reliability across instructors
            - **{len(filtered_instructors[filtered_instructors['TeacherRating'] > 4.0])}** instructors ({len(filtered_instructors[filtered_instructors['TeacherRating'] > 4.0])/len(filtered_instructors)*100:.1f}%) are rated above 4.0
            """,
            "color": "#3498db"
        },
        {
            "title": "🎓 Experience vs Performance",
            "content": f"""
            - Experience-Rating correlation: **{corr_exp_teacher:.3f}** ({'Positive' if corr_exp_teacher > 0 else 'Negative'} relationship)
            - Average teaching experience: **{filtered_instructors['YearsOfExperience'].mean():.1f} years**
            - {'Experience positively correlates with instructor quality' if corr_exp_teacher > 0.2 else 'Experience has limited impact on instructor quality' if corr_exp_teacher > 0 else 'Experience shows inverse relationship with quality'}
            """,
            "color": "#2ecc71"
        },
        {
            "title": "📚 Course Quality Alignment",
            "content": f"""
            - Teacher-Course rating correlation: **{corr_teacher_course:.3f}**
            - Average course rating: **{avg_course_rating:.2f}/5.0**
            - {'Strong alignment' if corr_teacher_course > 0.6 else 'Moderate alignment' if corr_teacher_course > 0.3 else 'Weak alignment'} between instructor and course quality
            """,
            "color": "#9b59b6"
        },
        {
            "title": "🎯 Enrollment Patterns",
            "content": f"""
            - High-rated instructors drive **{enrollment_influence_ratio:.1%}** of total enrollments
            - Total platform enrollments: **{total_enrollments:,}**
            - Enrollments per instructor (avg): **{total_enrollments / len(filtered_instructors):.1f}**
            """,
            "color": "#e74c3c"
        }
    ]
    
    for insight in insights:
        st.markdown(f"""
            <div class="insight-box" style="border-left-color: {insight['color']}">
                <h4 style="color: {insight['color']}; margin-bottom: 0.5rem;">{insight['title']}</h4>
                {insight['content']}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Top Performers
    st.markdown("### 🏆 Top Performing Areas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📚 Best Course Categories")
        category_stats = filtered_merged.groupby('CourseCategory').agg({
            'CourseRating': 'mean',
            'TransactionID': 'count'
        }).reset_index()
        category_stats.columns = ['Category', 'Avg_Rating', 'Enrollments']
        top_categories = category_stats.nlargest(5, 'Avg_Rating')
        
        for idx, row in top_categories.iterrows():
            st.markdown(f"**{row['Category']}** - Rating: {row['Avg_Rating']:.2f}, Enrollments: {int(row['Enrollments']):,}")
    
    with col2:
        st.markdown("#### 🎓 Best Expertise Areas")
        expertise_stats = filtered_instructors.groupby('Expertise').agg({
            'TeacherRating': 'mean',
            'TeacherID': 'count'
        }).reset_index()
        expertise_stats.columns = ['Expertise', 'Avg_Rating', 'Num_Instructors']
        top_expertise = expertise_stats.nlargest(5, 'Avg_Rating')
        
        for idx, row in top_expertise.iterrows():
            st.markdown(f"**{row['Expertise']}** - Rating: {row['Avg_Rating']:.2f}, Instructors: {int(row['Num_Instructors'])}")
    
    st.markdown("---")
    
    # Recommendations
    st.markdown("### 💡 Strategic Recommendations")
    
    recommendations = [
        {
            "priority": "🔴 High Priority",
            "title": "Instructor Development Program",
            "description": "Focus professional development on instructors with ratings below 3.5. Implement mentorship programs pairing low-rated instructors with top performers.",
            "action": "Create quarterly training workshops and one-on-one coaching sessions"
        },
        {
            "priority": "🟡 Medium Priority",
            "title": "Quality Recognition System",
            "description": "Establish recognition and reward system for consistently high-rated instructors to motivate excellence and reduce turnover.",
            "action": "Implement monthly 'Instructor of the Month' awards and performance bonuses"
        },
        {
            "priority": "🟡 Medium Priority",
            "title": "Course Quality Standards",
            "description": "Develop quality standards based on characteristics of top-performing courses and instructors. Ensure alignment between instructor expertise and course content.",
            "action": "Create quality rubric and implement peer review process"
        },
        {
            "priority": "🟢 Low Priority",
            "title": "Expertise Gap Analysis",
            "description": "Investigate why certain expertise areas consistently outperform others. Consider recruiting or training instructors in high-demand, low-supply expertise areas.",
            "action": "Conduct quarterly expertise market analysis and recruitment drives"
        },
        {
            "priority": "🟢 Low Priority",
            "title": "Continuous Monitoring",
            "description": "Implement real-time monitoring of instructor and course performance metrics. Set up automated alerts for performance drops.",
            "action": "Deploy analytics dashboard for leadership team with weekly reports"
        }
    ]
    
    for rec in recommendations:
        with st.expander(f"{rec['priority']} - {rec['title']}"):
            st.markdown(f"**Description:** {rec['description']}")
            st.markdown(f"**Recommended Action:** {rec['action']}")
    
    st.markdown("---")
    
    # Export data
    st.markdown("### 📥 Export Analysis Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_instructors.to_csv(index=False)
        st.download_button(
            label="📊 Download Instructor Data",
            data=csv,
            file_name="instructor_analysis.csv",
            mime="text/csv"
        )
    
    with col2:
        csv2 = filtered_merged.to_csv(index=False)
        st.download_button(
            label="📚 Download Course Data",
            data=csv2,
            file_name="course_analysis.csv",
            mime="text/csv"
        )
    
    with col3:
        # Create summary report
        summary_data = {
            'Metric': ['Avg Teacher Rating', 'Avg Course Rating', 'Total Instructors', 
                      'Total Courses', 'Total Enrollments', 'Consistency Index',
                      'Experience-Rating Correlation', 'Enrollment Influence Ratio'],
            'Value': [f"{avg_teacher_rating:.2f}", f"{avg_course_rating:.2f}", 
                     len(filtered_instructors), filtered_merged['CourseID'].nunique(),
                     total_enrollments, f"{rating_consistency_index:.3f}",
                     f"{corr_exp_teacher:.3f}", f"{enrollment_influence_ratio:.1%}"]
        }
        summary_df = pd.DataFrame(summary_data)
        csv3 = summary_df.to_csv(index=False)
        st.download_button(
            label="📋 Download Summary Report",
            data=csv3,
            file_name="executive_summary.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #7f8c8d; padding: 2rem 0;'>
        <p><strong>EduPro Instructor Performance Dashboard</strong></p>
        <p>Powered by Streamlit | Data-Driven Education Analytics</p>
        <p style='font-size: 0.8rem;'>© 2024 Unified Mentor Data Analytics Program</p>
    </div>
""", unsafe_allow_html=True)
