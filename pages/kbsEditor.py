import streamlit as st
import pandas as pd
import pathlib

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

""", unsafe_allow_html=True)

dataset="courses.csv"

df = pd.read_csv(dataset)

st.markdown('<h1><i class="fa-solid fa-book-open" style="color: #f44747;"></i> Course Management System</h1>', unsafe_allow_html=True)
action = st.sidebar.radio("Choose Action", ["View Courses", "Add Course", "Edit Course", "Delete Course"])

def validate_course(codes_string, existing_codes):
    
    codes = [c.strip() for c in codes_string.split(",") if c.strip()]
    invalid = [c for c in codes if c not in existing_codes]
    return invalid

if action == "Add Course":
    st.markdown('### <i class="fa-solid fa-plus" style="color: #f44747;"></i> Add Course', unsafe_allow_html=True)

    with st.form("add_form", clear_on_submit=True):
        code = st.text_input("Course Code").strip().upper()
        name = st.text_input("Course Name")
        desc = st.text_input("Description")
        prereq = st.text_input("Prerequisites").strip().upper()
        coreq = st.text_input("Co-requisites").strip().upper()
        hours = st.number_input("Credit Hours", min_value=0, step=1)
        semester = st.text_input("Semester Offered").strip().upper()
        submit = st.form_submit_button("Add")

        if submit:
            existing_codes = df["Course Code"].tolist()
            invalid_prereq = validate_course(prereq, existing_codes)
            invalid_coreq = validate_course(coreq, existing_codes)
            if not code.strip() or not name.strip() or not desc.strip() or not semester.strip():

                st.error("All fields are required. Please fill in all fields.")
            elif code.strip() in df["Course Code"].values:
                st.error("Course code already exists. Please use a unique course code.")

            elif hours < 0:
                st.error("Credit hours must be a positive number.")
            else:
                if invalid_prereq or invalid_coreq:
                    if invalid_prereq:
                        st.error(f"Invalid prerequisites: {', '.join(invalid_prereq)}")
                    if invalid_coreq:
                        st.error(f"Invalid co-requisites: {', '.join(invalid_coreq)}")
                else:
                    new_course = {
                        "Course Code": code,
                        "Course Name": name,
                        "Description": desc,
                        "Prerequisites": prereq,
                        "Co-requisites": coreq,
                        "Credit Hours": int(hours),
                        "Semester Offered": semester
                    }
                    df.loc[len(df)] = new_course
                    df.to_csv(dataset, index=False)
                    st.success("Course added successfully!")

elif action == "Edit Course":
    st.markdown('### <i class="fa-solid fa-pen" style="color: #f44747;"></i> Edit Course', unsafe_allow_html=True)
    if df.empty:
        st.info("No courses available.")
    else:
        selected = st.selectbox("Select course to edit", df["Course Code"])
        course = df[df["Course Code"] == selected].iloc[0]

        prereq_val = "" if pd.isna(course["Prerequisites"]) else course["Prerequisites"]
        coreq_val = "" if pd.isna(course["Co-requisites"]) else course["Co-requisites"]
 

        with st.form("edit_form"):
            name = st.text_input("Course Name", course["Course Name"])
            desc = st.text_input("Description", course["Description"])
            prereq = st.text_input("Prerequisites",prereq_val).strip().upper()
            coreq = st.text_input("Co-requisites", coreq_val).strip().upper()
            hours = st.number_input("Credit Hours", min_value=0, value=int(course["Credit Hours"]))
            semester = st.text_input("Semester Offered", course["Semester Offered"]).strip().upper()
            submit = st.form_submit_button("Update")

            if submit:
                existing_codes = df["Course Code"].tolist()
                existing_codes.remove(selected)  
                invalid_prereq = validate_course(prereq, existing_codes)
                invalid_coreq = validate_course(coreq, existing_codes)

                if hours < 0:
                    st.error("Credit hours must be a positive number.")
                elif invalid_prereq or invalid_coreq:
                    if invalid_prereq:
                        st.error(f"Invalid prerequisites: {', '.join(invalid_prereq)}")
                    if invalid_coreq:
                        st.error(f"Invalid co-requisites: {', '.join(invalid_coreq)}")
                else:
                    df.loc[df["Course Code"] == selected, ["Course Name", "Description", "Prerequisites", "Co-requisites", "Credit Hours", "Semester Offered"]] = \
                        [name, desc, prereq, coreq, int(hours), semester]
                    df.to_csv(dataset, index=False)
                    st.success("Course updated successfully!")

elif action == "Delete Course":
    st.markdown('### <i class="fa-solid fa-trash-can" style="color: #f44747;"></i> Delete Course', unsafe_allow_html=True)
    if df.empty:
        st.info("No courses available.")
    else:
        selected = st.selectbox("Select course to delete", df["Course Code"])
        if st.button("Delete"):
                
                prereq_course = df["Prerequisites"].astype(str).str.contains(rf'\b{selected}\b').any()
                coreq_course = df["Co-requisites"].astype(str).str.contains(rf'\b{selected}\b').any()

                if prereq_course or coreq_course:
                    st.error(f"Cannot delete course '{selected}' because it is used as a prerequisite or co-requisite.")
                else:
                    df = df[df["Course Code"] != selected]
                    df.to_csv(dataset, index=False)
                    st.success(f"Course '{selected}' deleted.")

else:
    st.markdown('### <i class="fa-solid fa-list-ul" style="color: #f44747;"></i> Course List', unsafe_allow_html=True)
    st.dataframe(df)
