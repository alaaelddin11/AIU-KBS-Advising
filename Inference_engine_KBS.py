import pandas as pd
from experta import *
import re

courses_df = pd.read_csv("coruse.csv").fillna("")
policies_df = pd.read_csv("policies.csv").fillna("")

# Student input
student_input = {
     "cgpa": 3.1,                      # Credit limit = 22
    "semester": "FALL",
    "passed_courses": ["UC1"],       # Only 1 course passed
    "failed_courses": []
}

# Convert course list to dict
all_courses = courses_df.to_dict(orient="records")

# Define Fact model
class StudentProfile(Fact):
    pass

# Inference engine
class AdvisingEngine(KnowledgeEngine):
    def __init__(self, courses, student_data, policies_df):
        super().__init__()
        self.courses = courses
        self.student_data = student_data
        self.policies_df = policies_df
        self.recommended_courses = []
        self.total_credits = 0
        self.explanations = []
        self.credit_limit = self.get_dynamic_credit_limit()

    def get_dynamic_credit_limit(self):
        credit_policies = self.policies_df[self.policies_df["Category"].str.strip() == "Credit Limit"]
        rules = []

        for _, row in credit_policies.iterrows():
            condition = str(row["Condition"])
            max_credit = int(row["max"])
            match = re.findall(r'(\d+\.\d+)', condition)

            if "≥" in condition or ">=" in condition:
                rules.append((lambda cgpa, val=float(match[0]): cgpa >= val, max_credit))
            elif "≤" in condition and len(match) == 2:
                l, u = float(match[0]), float(match[1])
                rules.append((lambda cgpa, l=l, u=u: l <= cgpa < u, max_credit))
            elif "<" in condition:
                rules.append((lambda cgpa, val=float(match[0]): cgpa < val, max_credit))

        for rule, limit in rules:
            if rule(self.student_data["cgpa"]):
                return limit
        return 12  # Default fallback

    @Rule(StudentProfile())
    def recommend_courses(self):
        already_added = set()
        passed = [c.strip() for c in self.student_data["passed_courses"]]
        failed = [c.strip() for c in self.student_data["failed_courses"]]

        # Step 1: Prioritize failed courses
        for course in self.courses:
            code = str(course["Course Code"]).strip()
            offered = str(course["Semester Offered"]).strip().upper()
            prereqs = [p.strip() for p in str(course["Prerequisites"]).split(",") if p.strip()]
            credits = int(course["Credit Hours"])

            if code not in failed:
                continue
            if code in passed:
                self.explanations.append(f"{code} is not recommended because it was already passed.")
                continue
            if self.student_data["semester"].upper() not in offered and offered != "BOTH":
                self.explanations.append(f"{code} is unavailable this semester.")
                continue
            if any(pr not in passed for pr in prereqs):
                self.explanations.append(f"{code} is not recommended due to unmet prerequisite(s): {', '.join([pr for pr in prereqs if pr not in passed])}.")
                continue
            if self.total_credits + credits > self.credit_limit:
                self.explanations.append(f"{code} is not added because it would exceed the credit limit.")
                continue
            self.recommended_courses.append(course)
            already_added.add(code)
            self.total_credits += credits
            self.explanations.append(f"{code} is prioritized because you failed it previously and met its prerequisites.")

        # Recommend other eligible courses
        for course in self.courses:
            code = str(course["Course Code"]).strip()
            name = str(course["Course Name"]).strip()
            offered = str(course["Semester Offered"]).strip().upper()
            prereqs = [p.strip() for p in str(course["Prerequisites"]).split(",") if p.strip()]
            coreqs = [c.strip() for c in str(course["Co-requisites"]).split(",") if c.strip()]
            credits = int(course["Credit Hours"])

            if code in passed or code in already_added:
                continue
            if self.student_data["semester"].upper() not in offered and offered != "BOTH":
                self.explanations.append(f"{code} is not offered in the {self.student_data['semester']} semester.")
                continue
            if any(pr not in passed for pr in prereqs):
                self.explanations.append(f"{code} is not recommended due to unmet prerequisite(s): {', '.join([pr for pr in prereqs if pr not in passed])}.")
                continue
            if any(cr not in passed and cr not in [c["Course Code"].strip() for c in self.recommended_courses] for cr in coreqs):
                self.explanations.append(f"{code} is not recommended due to unmet co-requisite(s): {', '.join([cr for cr in coreqs if cr not in passed])}.")
                continue
            if self.total_credits + credits > self.credit_limit:
                self.explanations.append(f"{code} is not added because it would exceed the credit limit.")
                continue
            self.recommended_courses.append(course)
            already_added.add(code)
            self.total_credits += credits
            if prereqs:
                self.explanations.append(f"{code} is recommended because you passed {', '.join(prereqs)}, its prerequisite(s).")
            else:
                self.explanations.append(f"{code} is recommended because it has no prerequisites.")

# Run the engine
engine = AdvisingEngine(all_courses, student_input, policies_df)
engine.reset()
engine.declare(StudentProfile(**student_input))
engine.run()

# Show output
recommended_df = pd.DataFrame(engine.recommended_courses)[["Course Code", "Course Name", "Credit Hours"]]
if not recommended_df.empty:
    recommended_df["Credit Hours"] = recommended_df["Credit Hours"].astype(int)
    recommended_df.loc["Total"] = ["", "Total Credits", recommended_df["Credit Hours"].sum()]
    print("Recommended Courses:")
    print(recommended_df)
else:
    print("No courses could be recommended based on your profile.")

# Show explanations
print("\n--- Explanation of Decisions ---")
for explanation in engine.explanations:
    print("- " + explanation)
