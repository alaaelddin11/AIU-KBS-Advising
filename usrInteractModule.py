import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from Inference_engine_KBS import AdvisingEngine, StudentProfile

# Add the parent directory to sys.path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_courses():
    try:
        courses_df = pd.read_csv('courses.csv')
        return courses_df
    except Exception as e:
        st.error(f"Error loading courses: {str(e)}")
        return pd.DataFrame()

def validate_cgpa(cgpa):
    try:
        cgpa = float(cgpa)
        if 0.0 <= cgpa <= 4.0:
            return True, None
        return False, "CGPA must be between 0.0 and 4.0"
    except ValueError:
        return False, "CGPA must be a valid number"

def get_semester_options():
    current_year = datetime.now().year
    semesters = []
    for year in range(current_year, current_year + 2):
        semesters.extend([f"Fall {year}", f"Spring {year}"])
    return semesters

def main():
    st.set_page_config(
        page_title="Course Recommendation System",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("Course Recommendation System")

    # Create two columns for the buttons
    col1, col2 = st.columns([3, 1])  # 3:1 ratio to push the second button to the right

    courses_df = load_courses()
    if courses_df.empty:
        st.error("Unable to load courses.")
        return

    col1, col2 = st.columns(2)

    with col1:
        semester = st.selectbox(
            "Select Current Semester",
            options=get_semester_options(),
            help="Choose your current semester"
        )

        cgpa = st.number_input(
            "Enter CGPA",
            min_value=0.0,
            max_value=4.0,
            step=0.01,
            format="%.2f",
            help="Enter your CGPA (0.0-4.0)"
        )

        recommend_button = st.button("Get Course Recommendations", type="primary")


    with col2:
        passed_courses = st.multiselect(
            "Select Passed Courses",
            options=courses_df['Course Code'].tolist(),
            help="Select all courses you have passed"
        )

        failed_courses = st.multiselect(
            "Select Failed Courses",
            options=[course for course in courses_df['Course Code'].tolist() if course not in passed_courses],
            help="Select all courses you have failed"
        )
        
        manage_button = st.button("Go to Course Management System", type="primary")

    if manage_button:
        st.switch_page("pages/kbsEditor.py")

    is_valid_cgpa, cgpa_error = validate_cgpa(cgpa)
    if not is_valid_cgpa:
        st.error(cgpa_error)

    

    if recommend_button:
        if not is_valid_cgpa:
            st.error("Please fix the CGPA input before proceeding.")
            return


        with st.spinner("Processing your request..."):
            try:
                semester_type = semester.split()[0].upper()  
                student_input = {
                    "cgpa": float(cgpa),
                    "semester": semester_type,
                    "passed_courses": passed_courses,
                    "failed_courses": failed_courses
                }

                all_courses = []
                for _, course in courses_df.iterrows():
                    course_dict = {
                        "Course Code": str(course["Course Code"]).strip(),
                        "Course Name": str(course["Course Name"]).strip(),
                        "Credit Hours": int(course["Credit Hours"]),
                        "Semester Offered": str(course["Semester Offered"]).strip().upper(),
                        "Prerequisites": str(course["Prerequisites"]).strip() if pd.notna(course["Prerequisites"]) else "",
                        "Co-requisites": str(course["Co-requisites"]).strip() if pd.notna(course["Co-requisites"]) else ""
                    }
                    all_courses.append(course_dict)

                policies_df = pd.read_csv("policies.csv").fillna("")

                engine = AdvisingEngine(all_courses, student_input, policies_df)
                engine.reset()
                engine.declare(StudentProfile(**student_input))
                engine.run()

                if engine.recommended_courses:
                    st.success("Here are your recommended courses:")
                    
                    recommended_df = pd.DataFrame(engine.recommended_courses)[["Course Code", "Course Name", "Credit Hours"]]
                    recommended_df["Credit Hours"] = recommended_df["Credit Hours"].astype(int)
                    
                    total_credits = recommended_df["Credit Hours"].sum()
                    recommended_df.loc["Total"] = ["", "Total Credits", total_credits]
                    
                    st.dataframe(
                        recommended_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("### Explanation of Decisions")
                    for explanation in engine.explanations:
                        st.write(f"- {explanation}")
                else:
                    st.warning("No courses could be recommended based on your profile.")
                    st.write(f"Number of available courses: {len(all_courses)}")
                    st.write(f"Available courses in {semester_type}: {[c['Course Code'] for c in all_courses if semester_type in c['Semester Offered']]}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
