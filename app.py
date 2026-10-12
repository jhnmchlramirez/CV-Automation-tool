import io
import os
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from google import genai
import reportlab
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Automated ATS CV Generator", page_icon="📄", layout="wide"
)

# Custom CSS for clean white background preview with universal text scoping
st.markdown(
    """
    <style>
    .cv-preview-container {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 40px;
        border-radius: 5px;
        border: 1px solid #d1d5db;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        font-family: Arial, sans-serif;
    }
    .cv-preview-container * {
        color: #000000 !important;
    }
    .creator-badge {
        font-size: 15px;
        color: #9ca3af;
        margin-bottom: 5px;
    }
    .creator-badge a {
        color: #38bdf8;
        text-decoration: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper function to clean URLs for compact header display
def clean_display_url(url_str):
  clean = url_str.strip()
  if clean.startswith("https://"):
    clean = clean[8:]
  elif clean.startswith("http://"):
    clean = clean[7:]
  if clean.startswith("www."):
    clean = clean[4:]
  return clean.rstrip("/")


# Helper function to open native OS "Save As" window
def open_save_dialog(default_extension, filetypes, initial_filename):
  root = tk.Tk()
  root.withdraw()
  root.attributes("-topmost", True)  # Bring dialog window to front
  file_path = filedialog.asksaveasfilename(
      defaultextension=default_extension,
      filetypes=filetypes,
      initialfile=initial_filename,
  )
  root.destroy()
  return file_path


# Helper function to open file across different operating systems
def open_saved_file(file_path):
  root = tk.Tk()
  root.withdraw()
  root.attributes("-topmost", True)
  should_open = messagebox.askyesno(
      "File Saved Successfully",
      f"File successfully saved to:\n{file_path}\n\nWould you like to open it"
      " now?",
  )
  root.destroy()

  if should_open:
    try:
      if platform.system() == "Darwin":  # macOS
        subprocess.call(("open", file_path))
      elif platform.system() == "Windows":  # Windows
        os.startfile(file_path)
      else:  # Linux
        subprocess.call(("xdg-open", file_path))
    except Exception as e:
      st.error(f"Could not open file automatically: {e}")


# Function to generate an ATS-compliant PDF in memory using ReportLab
def generate_pdf_cv(
    full_name,
    position_title,
    address,
    contact,
    email,
    linkedin,
    website,
    include_linkedin,
    include_website,
    prof_summary,
    skills_list,
    experience_list,
    education_list,
    licenses_list,
    certificates_list,
    include_licenses,
    include_certificates,
):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )

  styles = getSampleStyleSheet()

  title_style = ParagraphStyle(
      "DocTitle",
      parent=styles["Heading1"],
      fontName="Helvetica-Bold",
      fontSize=18,
      leading=22,
      textColor="black",
      alignment=TA_CENTER,
      spaceAfter=2,
  )
  subtitle_style = ParagraphStyle(
      "DocSubtitle",
      parent=styles["Normal"],
      fontName="Helvetica-Bold",
      fontSize=11,
      leading=14,
      textColor="#333333",
      alignment=TA_CENTER,
      spaceAfter=4,
  )
  contact_style = ParagraphStyle(
      "ContactInfo",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=9,
      leading=13,
      textColor="#333333",
      alignment=TA_CENTER,
      spaceAfter=8,
  )
  section_heading = ParagraphStyle(
      "SectionHeading",
      parent=styles["Heading2"],
      fontName="Helvetica-Bold",
      fontSize=11,
      leading=14,
      textColor="black",
      spaceBefore=10,
      spaceAfter=4,
  )
  body_style = ParagraphStyle(
      "Body",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=9.5,
      leading=13,
      textColor="black",
      spaceAfter=4,
  )
  exp_subtitle_style = ParagraphStyle(
      "ExpSubtitle",
      parent=styles["Normal"],
      fontName="Helvetica-Oblique",
      fontSize=9,
      leading=12,
      textColor="#333333",
      spaceAfter=2,
  )
  bullet_style = ParagraphStyle(
      "Bullet",
      parent=styles["Normal"],
      fontName="Helvetica",
      fontSize=9.5,
      leading=13,
      textColor="black",
      leftIndent=15,
      spaceAfter=2,
  )

  story = []

  # Header
  story.append(Paragraph(full_name.upper(), title_style))
  story.append(Paragraph(position_title.upper(), subtitle_style))

  line1_parts = [address, contact, email]
  line1_str = " &nbsp;|&nbsp; ".join([p for p in line1_parts if p.strip()])

  line2_parts = []
  if include_linkedin and linkedin.strip():
    disp_li = clean_display_url(linkedin)
    line2_parts.append(f'<a href="{linkedin}">LinkedIn: {disp_li}</a>')
  if include_website and website.strip():
    disp_web = clean_display_url(website)
    full_web = (
        website if website.startswith("http") else f"https://{website}"
    )
    line2_parts.append(f'<a href="{full_web}">Portfolio: {disp_web}</a>')
  line2_str = " &nbsp;|&nbsp; ".join(line2_parts)

  contact_block = (
      f"{line1_str}<br/>{line2_str}" if line2_str else line1_str
  )

  story.append(Paragraph(contact_block, contact_style))
  story.append(HRFlowable(width="100%", thickness=1, color="black", spaceAfter=8))

  # Summary
  story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
  story.append(Paragraph(prof_summary, body_style))
  story.append(
      HRFlowable(width="100%", thickness=0.5, color="black", spaceAfter=8)
  )

  # Skills
  story.append(Paragraph("TECHNICAL & CORE SKILLS", section_heading))
  for s in skills_list:
    if s["category"].strip():
      skill_text = f"<b>{s['category']}:</b> {s['items']}"
      story.append(Paragraph(skill_text, body_style))
  story.append(
      HRFlowable(width="100%", thickness=0.5, color="black", spaceAfter=8)
  )

  # Experience
  story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_heading))
  for exp in experience_list:
    end_str = "Present" if exp.get("is_current") else exp["end_date"]
    exp_line1 = f"<b>{exp['role']}</b> — <i>{exp['company']}</i>"
    exp_line2 = f"<i>{exp['location']} &nbsp;|&nbsp; {exp['start_date']} – {end_str}</i>"

    story.append(Paragraph(exp_line1, body_style))
    story.append(Paragraph(exp_line2, exp_subtitle_style))

    for b in exp["bullets"]:
      if b.strip():
        story.append(Paragraph(f"• {b.strip()}", bullet_style))
    story.append(Spacer(1, 4))
  story.append(
      HRFlowable(width="100%", thickness=0.5, color="black", spaceAfter=8)
  )

  # Education
  story.append(Paragraph("EDUCATION", section_heading))
  for edu in education_list:
    edu_text = (
        f"<b>{edu['degree']}</b> - <i>{edu['institution']} ({edu['start_year']} –"
        f" {edu['end_year']})</i>"
    )
    story.append(Paragraph(edu_text, body_style))

  # Licenses
  if include_licenses and licenses_list:
    story.append(
        HRFlowable(width="100%", thickness=0.5, color="black", spaceAfter=8)
    )
    story.append(
        Paragraph("PROFESSIONAL LICENSES & AFFILIATIONS", section_heading)
    )
    for lic in licenses_list:
      if lic["item"].strip():
        story.append(Paragraph(f"• {lic['item']}", bullet_style))

  # Certificates
  if include_certificates and certificates_list:
    story.append(
        HRFlowable(width="100%", thickness=0.5, color="black", spaceAfter=8)
    )
    story.append(
        Paragraph("SEMINARS, WORKSHOPS & TECHNICAL TRAININGS", section_heading)
    )
    for cert in certificates_list:
      if cert["item"].strip():
        story.append(Paragraph(f"• {cert['item']}", bullet_style))

  doc.build(story)
  buffer.seek(0)
  return buffer.getvalue()


# Creator Banner at the Top
st.markdown(
    '<div class="creator-badge">🛠️ Tool Created by <b>John Michael C. Ramirez</b>'
    " | <a href='https://www.linkedin.com/in/john-michael-ramirez-56ab46197/'"
    " target='_blank'>LinkedIn Profile</a></div>",
    unsafe_allow_html=True,
)

st.title("📄 Automated ATS CV Tailor & Builder")
st.markdown(
    "Manage all your CV sections using clean, dynamic row entries with date"
    " toggles and add/delete controls."
)

# Initialize Session State
if "skills_list" not in st.session_state:
  st.session_state.skills_list = [
      {
          "category": "BIM Modeling",
          "items": (
              "Autodesk Revit, Structural BIM Modeling, Structural Framing,"
              " Reinforced Concrete & Steel Modeling, Construction Documentation,"
              " Structural Detailing"
          ),
      },
      {
          "category": "BIM Automation",
          "items": (
              "Dynamo, Python, Revit Automation, CAD Automation (Computational"
              " Engineering, Automation Scripts, AI Integration, Dynamo scripting)"
          ),
      },
      {
          "category": "Drafting & Documentation",
          "items": (
              "AutoCAD, ZWCAD, Bluebeam Revu, Structural Drawings, Rebar"
              " Detailing"
          ),
      },
      {
          "category": "Codes & Standards",
          "items": (
              "National Structural Code of the Philippines (NSCP), American"
              " Concrete Institute (ACI), American Institute of Steel Construction"
              " (AISC), American Society of Civil Engineers (ASCE 7), AS/NZS"
              " Standards."
          ),
      },
  ]

if "experience_list" not in st.session_state:
  st.session_state.experience_list = [
      {
          "role": "Structural Engineer II",
          "company": "Abinales Associates Engineers + Consultants",
          "location": "Kapitolyo, Pasig City, Philippines",
          "start_date": "July 2020",
          "end_date": "July 2026",
          "is_current": True,
          "bullets": [
              (
                  "Develop and maintain structural BIM models in Autodesk Revit"
                  " for reinforced concrete and steel building projects,"
                  " translating structural design intent into coordinated,"
                  " constructible models and documentation."
              ),
              (
                  "Produce structural construction drawings, details,"
                  " schedules, and permit documentation using Revit and AutoCAD,"
                  " ensuring consistency between the structural model and"
                  " drawing deliverables."
              ),
              (
                  "Develop and implement Dynamo and Python automation workflows"
                  " within Revit to automate repetitive modeling, detailing,"
                  " and documentation tasks, reducing production turnaround"
                  " time by 25%."
              ),
              (
                  "Coordinate structural models and drawings with architectural"
                  " and other project requirements, identifying"
                  " constructability issues and minimizing design and"
                  " documentation revisions."
              ),
          ],
      },
      {
          "role": "Structural Engineer",
          "company": "Independent Design Consultant (Contract / Project-Based)",
          "location": "Manila, NCR, Philippines",
          "start_date": "June 2022",
          "end_date": "January 2026",
          "is_current": False,
          "bullets": [
              (
                  "Delivered structural design, modeling, detailing, and"
                  " construction documentation for 25 residential and"
                  " commercial projects."
              ),
              (
                  "Served as Structural Engineer of Record (SEOR) for 3"
                  " projects, coordinating structural calculations and"
                  " regulatory documentation."
              ),
          ],
      },
      {
          "role": "Site Engineer & Cost Estimator",
          "company": "Firmbuilders, Inc.",
          "location": "Boni Avenue, Mandaluyong City, Philippines",
          "start_date": "November 2019",
          "end_date": "May 2020",
          "is_current": False,
          "bullets": [
              (
                  "Prepared structural and architectural quantity take-offs"
                  " (QTO) and cost estimates."
              ),
              (
                  "Supervised multidisciplinary construction activities to"
                  " ensure compliance with approved structural designs."
              ),
          ],
      },
  ]

if "education_list" not in st.session_state:
  st.session_state.education_list = [
      {
          "degree": "Bachelor of Science in Civil Engineering",
          "institution": "Rizal Technological University, Mandaluyong City",
          "start_year": "2015",
          "end_year": "2019",
      },
      {
          "degree": "Civil Engineering Technology Diploma",
          "institution": "Rizal Technological University, Mandaluyong City",
          "start_year": "2014",
          "end_year": "2017",
      },
  ]

if "licenses_list" not in st.session_state:
  st.session_state.licenses_list = [
      {
          "item": (
              "Professional Regulatory Commission (PRC) | Licensed Civil Engineer,"
              " Reg No. 0174546"
          )
      },
      {
          "item": (
              "Philippine Institute of Civil Engineers (PICE) | Regular Member"
          )
      },
      {
          "item": (
              "Association of Structural Engineers of the Philippines (ASEP) |"
              " Active Member"
          )
      },
  ]

if "certificates_list" not in st.session_state:
  st.session_state.certificates_list = [
      {
          "item": (
              "Comprehensive Training in Building Modeling, Analysis and Design"
              " using Midas Gen – MIDAS IT Philippines (January 2026)"
          )
      },
      {
          "item": (
              "Influence of Cracked Concrete to Post-Installed Anchor Design"
              " – HILTI Philippines (June 2025)"
          )
      },
  ]

if "prof_summary" not in st.session_state:
  st.session_state.prof_summary = (
      "Licensed Civil Engineer with over 6 years of structural engineering"
      " experience, including 4 years of hands-on structural BIM modeling"
      " using Autodesk Revit. Experienced in developing structural models"
      " and construction documentation for reinforced concrete and steel"
      " structures, with a strong understanding of structural design intent,"
      " detailing, and constructability. Proficient in Revit, AutoCAD, and"
      " structural analysis software, with experience using Dynamo and Python"
      " to automate repetitive BIM and documentation workflows."
  )

with st.sidebar:
  st.header("1. Personal Details")
  full_name = st.text_input("Full Name", "ENGR. JOHN MICHAEL C. RAMIREZ")
  position_title = st.text_input("Target Job Title", "REVIT STRUCTURAL MODELER")
  address = st.text_input("Home Address", "Santa Ana, Manila, Philippines")
  contact = st.text_input("Contact Number", "+63 956 053 5570")
  email = st.text_input("E-mail", "jhnmchiramirez@gmail.com")

  include_linkedin = st.checkbox("Include LinkedIn Profile", value=True)
  linkedin = st.text_input(
      "LinkedIn Live URL",
      "https://www.linkedin.com/in/john-michael-ramirez-56ab46197/",
  )

  include_website = st.checkbox("Include Website / Portfolio", value=True)
  website = st.text_input("Website / Portfolio Live URL", "jhnmchiramirez.github.io")

  st.markdown("---")
  st.header("🔑 AI Settings")
  gemini_api_key = st.text_input(
      "Gemini API Key", type="password", placeholder="Enter Free Gemini API Key..."
  )

# Main Layout
col1, col2 = st.columns([1, 1])

with col1:
  st.subheader("2. Target Job Description & Key Qualifications")
  job_description = st.text_area(
      "Paste Job Description / Requirements here:",
      placeholder=(
          "Paste the job description here to tailor your CV summary and"
          " keywords..."
      ),
      height=140,
  )

  # AI Tailoring Trigger Button
  if st.button(
      "✨ AI Tailor CV to Job Description", use_container_width=True
  ):
    if not gemini_api_key.strip():
      st.error(
          "Please enter your free Gemini API Key in the sidebar (get one from"
          " aistudio.google.com)."
      )
    elif not job_description.strip():
      st.warning(
          "Please paste a job description in the text box above before"
          " tailoring."
      )
    else:
      with st.spinner("Analyzing job requirements and tailoring CV..."):
        try:
          client = genai.Client(api_key=gemini_api_key)
          prompt = f"""
                    You are an expert ATS resume optimization consultant. 
                    Analyze the following Job Description and the candidate's current Professional Summary.
                    
                    Target Job Description:
                    {job_description}
                    
                    Current Professional Summary:
                    {st.session_state.prof_summary}
                    
                    Task:
                    1. Rewrite and optimize the Professional Summary to seamlessly target this job description, incorporating key terminology and priorities while maintaining strict factual accuracy for a Licensed Civil Engineer and Structural BIM Modeler.
                    2. Provide 3-5 critical ATS keywords/skills found in the job description that should be emphasized.
                    
                    Format your response cleanly with markdown:
                    ### Optimized Summary:
                    [Rewritten summary paragraph]
                    
                    ### Key ATS Keywords to Include:
                    [Comma-separated list of keywords]
                    """
          # Updated model name to gemini-3.8-flash
          response = client.models.generate_content(
              model="gemini-3.8-flash", contents=prompt
          )
          st.session_state.ai_tailored_result = response.text
          st.success("CV successfully analyzed and tailored!")
        except Exception as e:
          st.error(f"Error connecting to Gemini API: {e}")

  # Display AI Suggestions if available
  if "ai_tailored_result" in st.session_state:
    st.info(st.session_state.ai_tailored_result)
    if st.button("📥 Apply Optimized Summary to CV"):
      text = st.session_state.ai_tailored_result
      if "### Optimized Summary:" in text and "### Key ATS Keywords" in text:
        summary_part = text.split("### Optimized Summary:")[1]
        optimized_text = summary_part.split("### Key ATS Keywords")[0].strip()
        st.session_state.prof_summary = optimized_text
        st.success("Professional summary updated successfully!")
        st.rerun()

  st.subheader("3. Professional Summary (Factual)")
  prof_summary = st.text_area(
      "Summary Text", value=st.session_state.prof_summary, height=110
  )
  st.session_state.prof_summary = prof_summary

  # --- TECHNICAL SKILLS SECTION ---
  st.subheader("4. Technical & Core Skills")
  for i, skill_item in enumerate(st.session_state.skills_list):
    col_cat, col_vals, col_del = st.columns([2, 4, 1])
    with col_cat:
      skill_item["category"] = st.text_input(
          f"Sub-Category #{i+1}",
          value=skill_item["category"],
          key=f"cat_{i}",
      )
    with col_vals:
      skill_item["items"] = st.text_input(
          f"Skills / Keywords #{i+1}",
          value=skill_item["items"],
          key=f"val_{i}",
      )
    with col_del:
      st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
      if st.button("🗑️", key=f"del_skill_{i}", help="Delete this category"):
        st.session_state.skills_list.pop(i)
        st.rerun()

  if st.button("➕ Add Skill Sub-Category"):
    st.session_state.skills_list.append(
        {"category": "New Category", "items": "Keyword 1, Keyword 2"}
    )
    st.rerun()

  # --- PROFESSIONAL EXPERIENCE SECTION ---
  st.subheader("5. Professional Experience")
  for i, exp in enumerate(st.session_state.experience_list):
    c_main, c_del = st.columns([6, 1])

    with c_main:
      st.markdown(f"**Experience Entry #{i+1}**")

      r1_c1, r1_c2 = st.columns(2)
      with r1_c1:
        exp["role"] = st.text_input(
            f"Job Title #{i+1}", value=exp["role"], key=f"exp_role_{i}"
        )
      with r1_c2:
        exp["company"] = st.text_input(
            f"Company #{i+1}", value=exp["company"], key=f"exp_comp_{i}"
        )

      exp["location"] = st.text_input(
          f"Location #{i+1} (City, Country)",
          value=exp["location"],
          key=f"exp_loc_{i}",
      )

      r3_c1, r3_c2, r3_c3 = st.columns([2, 2, 2])
      with r3_c1:
        exp["start_date"] = st.text_input(
            f"Start Date #{i+1}", value=exp["start_date"], key=f"exp_sd_{i}"
        )
      with r3_c2:
        exp["is_current"] = st.checkbox(
            "Currently Employed",
            value=exp.get("is_current", False),
            key=f"exp_curr_{i}",
        )
      with r3_c3:
        if exp["is_current"]:
          exp["end_date"] = "Present"
          st.text_input(
              f"End Date #{i+1}",
              value="Present",
              disabled=True,
              key=f"exp_ed_dis_{i}",
          )
        else:
          exp["end_date"] = st.text_input(
              f"End Date #{i+1}", value=exp["end_date"], key=f"exp_ed_{i}"
          )

      st.markdown(f"**Key Responsibilities / Bullet Points #{i+1}**")
      for b_idx, bullet_str in enumerate(exp["bullets"]):
        col_b_input, col_b_del = st.columns([6, 1])
        with col_b_input:
          exp["bullets"][b_idx] = st.text_input(
              f"Bullet #{b_idx+1}",
              value=bullet_str,
              key=f"exp_{i}_bullet_{b_idx}",
              label_visibility="collapsed",
          )
        with col_b_del:
          if st.button("🗑️", key=f"del_b_{i}_{b_idx}", help="Delete bullet"):
            exp["bullets"].pop(b_idx)
            st.rerun()

      if st.button("➕ Add Bullet Point", key=f"add_b_{i}"):
        exp["bullets"].append("New responsibility / bullet point detail...")
        st.rerun()

    with c_del:
      st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
      if st.button("🗑️", key=f"del_exp_{i}", help="Delete this experience entry"):
        st.session_state.experience_list.pop(i)
        st.rerun()

    st.markdown("---")

  if st.button("➕ Add Experience Entry"):
    st.session_state.experience_list.append(
        {
            "role": "Position Title",
            "company": "Company Name",
            "location": "City, Country",
            "start_date": "MM/YYYY",
            "end_date": "MM/YYYY",
            "is_current": False,
            "bullets": ["Key responsibility bullet 1"],
        }
    )
    st.rerun()

  st.markdown("---")

  # --- EDUCATION SECTION ---
  st.subheader("6. Education")
  for i, edu in enumerate(st.session_state.education_list):
    c_main, c_del = st.columns([6, 1])
    with c_main:
      st.markdown(f"**Education Entry #{i+1}**")
      edu["degree"] = st.text_input(
          f"Degree / Program #{i+1}",
          value=edu["degree"],
          key=f"edu_deg_{i}",
      )
      edu["institution"] = st.text_input(
          f"Institution / School #{i+1}",
          value=edu["institution"],
          key=f"edu_inst_{i}",
      )

      e_c1, e_c2 = st.columns(2)
      with e_c1:
        edu["start_year"] = st.text_input(
            f"Start Year #{i+1}", value=edu["start_year"], key=f"edu_sy_{i}"
        )
      with e_c2:
        edu["end_year"] = st.text_input(
            f"End Year #{i+1}", value=edu["end_year"], key=f"edu_ey_{i}"
        )
    with c_del:
      st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
      if st.button("🗑️", key=f"del_edu_{i}", help="Delete education entry"):
        st.session_state.education_list.pop(i)
        st.rerun()
    st.markdown("---")

  if st.button("➕ Add Education Entry"):
    st.session_state.education_list.append(
        {
            "degree": "Degree Title",
            "institution": "School Name",
            "start_year": "YYYY",
            "end_year": "YYYY",
        }
    )
    st.rerun()

  st.markdown("---")

  # --- LICENSES & AFFILIATIONS SECTION ---
  st.subheader("7. Professional Licenses & Affiliations")
  include_licenses = st.checkbox(
      "Include Professional Licenses & Affiliations Section", value=True
  )
  if include_licenses:
    for i, lic in enumerate(st.session_state.licenses_list):
      c1, c_del = st.columns([5, 1])
      with c1:
        lic["item"] = st.text_input(
            f"License / Affiliation #{i+1}",
            value=lic["item"],
            key=f"lic_item_{i}",
        )
      with c_del:
        st.markdown(
            "<div style='padding-top: 28px;'></div>", unsafe_allow_html=True
        )
        if st.button("🗑️", key=f"del_lic_{i}", help="Delete license entry"):
          st.session_state.licenses_list.pop(i)
          st.rerun()
    if st.button("➕ Add License / Affiliation"):
      st.session_state.licenses_list.append(
          {"item": "New License or Organization"}
      )
      st.rerun()

  st.markdown("---")

  # --- CERTIFICATES & TRAININGS SECTION ---
  st.subheader("8. Seminars, Workshops & Technical Trainings")
  include_certificates = st.checkbox(
      "Include Certificates & Trainings Section", value=True
  )
  if include_certificates:
    for i, cert in enumerate(st.session_state.certificates_list):
      c1, c_del = st.columns([5, 1])
      with c1:
        cert["item"] = st.text_input(
            f"Training / Certificate #{i+1}",
            value=cert["item"],
            key=f"cert_item_{i}",
        )
      with c_del:
        st.markdown(
            "<div style='padding-top: 28px;'></div>", unsafe_allow_html=True
        )
        if st.button("🗑️", key=f"del_cert_{i}", help="Delete training entry"):
          st.session_state.certificates_list.pop(i)
          st.rerun()
    if st.button("➕ Add Training / Certificate"):
      st.session_state.certificates_list.append(
          {"item": "Training Name - Issuer (Year)"}
      )
      st.rerun()

with col2:
  st.subheader("9. Generated ATS Output & Preview")

  if st.button(
      "🚀 Compile & Format ATS CV", type="primary", use_container_width=True
  ):
    st.success("Your ATS-friendly CV has been compiled successfully!")

  # Structured 2-Line Header Block (Markdown)
  line1_parts = [address, contact, email]
  line1_md = " | ".join([p for p in line1_parts if p.strip()])

  line2_parts = []
  if include_linkedin and linkedin.strip():
    disp_li = clean_display_url(linkedin)
    line2_parts.append(f"LinkedIn: [{disp_li}]({linkedin})")
  if include_website and website.strip():
    disp_web = clean_display_url(website)
    full_web = (
        website if website.startswith("http") else f"https://{website}"
    )
    line2_parts.append(f"Portfolio: [{disp_web}]({full_web})")
  line2_md = " | ".join(line2_parts)

  header_contact_block = (
      f"{line1_md}  \n{line2_md}" if line2_md else line1_md
  )

  # Compile Skills
  skills_markdown = ""
  for s in st.session_state.skills_list:
    if s["category"].strip():
      skills_markdown += f"**{s['category']}**\n* {s['items']}\n\n"

  # Compile Experience
  experience_markdown = ""
  for exp in st.session_state.experience_list:
    end_str = "Present" if exp.get("is_current") else exp["end_date"]
    experience_markdown += f"**{exp['role']}** — *{exp['company']}*\n"
    experience_markdown += (
        f"*{exp['location']} | {exp['start_date']} – {end_str}*\n\n"
    )
    for b in exp["bullets"]:
      if b.strip():
        experience_markdown += f"- {b.strip()}\n"
    experience_markdown += "\n"

  # Compile Education
  education_markdown = "## EDUCATION\n\n"
  for edu in st.session_state.education_list:
    education_markdown += f"**{edu['degree']}**\n"
    education_markdown += (
        f"*{edu['institution']} ({edu['start_year']} – {edu['end_year']})*\n\n"
    )

  # Compile Licenses
  licenses_markdown = ""
  if include_licenses and st.session_state.licenses_list:
    licenses_markdown = "## PROFESSIONAL LICENSES & AFFILIATIONS\n\n"
    for lic in st.session_state.licenses_list:
      if lic["item"].strip():
        licenses_markdown += f"- {lic['item']}\n"
    licenses_markdown += "\n"

  # Compile Certificates
  certificates_markdown = ""
  if include_certificates and st.session_state.certificates_list:
    certificates_markdown = "## SEMINARS, WORKSHOPS & TECHNICAL TRAININGS\n\n"
    for cert in st.session_state.certificates_list:
      if cert["item"].strip():
        certificates_markdown += f"- {cert['item']}\n"
    certificates_markdown += "\n"

  # Final ATS Document Assembly (Center Aligned Header)
  ats_cv_output = f"""<div style="text-align: center;">

# {full_name}
### {position_title}
{header_contact_block}

</div>

---

## PROFESSIONAL SUMMARY
{st.session_state.prof_summary}

---

## TECHNICAL & CORE SKILLS
{skills_markdown}
---

## PROFESSIONAL EXPERIENCE
{experience_markdown}
---

{education_markdown}
{licenses_markdown}
{certificates_markdown}
"""

  preview_tab, raw_tab = st.tabs(
      ["👁️ White-Paper Visual Preview", "📝 Markdown Source"]
  )

  with preview_tab:
    st.markdown('<div class="cv-preview-container">', unsafe_allow_html=True)
    st.markdown(ats_cv_output, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

  with raw_tab:
    st.text_area("Raw Output", value=ats_cv_output, height=400)

  # Generate PDF Bytes
  pdf_bytes = generate_pdf_cv(
      full_name,
      position_title,
      address,
      contact,
      email,
      linkedin,
      website,
      include_linkedin,
      include_website,
      st.session_state.prof_summary,
      st.session_state.skills_list,
      st.session_state.experience_list,
      st.session_state.education_list,
      st.session_state.licenses_list,
      st.session_state.certificates_list,
      include_licenses,
      include_certificates,
  )

  dl_col1, dl_col2 = st.columns(2)

  with dl_col1:
    if st.button("💾 Save ATS CV (.md)", use_container_width=True):
      file_path = open_save_dialog(
          ".md", [("Markdown Files", "*.md"), ("All Files", "*.*")], "ATS_Friendly_CV.md"
      )
      if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
          f.write(ats_cv_output)
        open_saved_file(file_path)

  with dl_col2:
    if st.button("💾 Save ATS CV (.pdf)", use_container_width=True):
      file_path = open_save_dialog(
          ".pdf", [("PDF Files", "*.pdf"), ("All Files", "*.*")], "ATS_Friendly_CV.pdf"
      )
      if file_path:
        with open(file_path, "wb") as f:
          f.write(pdf_bytes)
        open_saved_file(file_path)