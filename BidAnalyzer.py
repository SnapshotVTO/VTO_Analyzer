import streamlit as st
from pypdf import PdfReader
import re
from PIL import Image
import pytesseract
import io

# --- 1. Text Extraction (The Eyes) ---
def get_text_from_file(uploaded_file):
    text = ""
    # If it's a PDF
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
    # If it's an Image (png, jpg, jpeg)
    else:
        try:
            image = Image.open(uploaded_file)
            # Extract text using Tesseract OCR
            text = pytesseract.image_to_string(image)
        except Exception as e:
            st.error(f"Error reading image: {e}")
    return text

# --- 2. Parsing Logic (The Brain) ---
def parse_bid_text(text):
    lines = text.split('\n')
    crew_data = []
    current_crew = None
    
    # Regex to find: Seniority (digits) -> CrewID (digits) -> Bids
    start_pattern = re.compile(r'^(\d+)\s+(\w+)\s+(.*)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = start_pattern.match(line)
        if match:
            if current_crew:
                crew_data.append(current_crew)
            
            sen = int(match.group(1))
            crew_id = match.group(2)
            bids_str = match.group(3)
            # Extract numbers from the bid string
            bids = [int(x) for x in re.findall(r'\d+', bids_str)]
            
            current_crew = {'seniority': sen, 'crew_id': crew_id, 'bids': bids}
        else:
            if current_crew:
                # If line has digits and spaces, append to previous crew
                if re.match(r'^[\d\s]+$', line):
                     more_bids = [int(x) for x in re.findall(r'\d+', line)]
                     current_crew['bids'].extend(more_bids)
    
    if current_crew:
        crew_data.append(current_crew)
        
    return crew_data

def simulate_bidding(crew_data, my_seniority, total_lines=42):
    available_lines = set(range(1, total_lines + 1))
    assignments = []
    
    crew_data.sort(key=lambda x: x['seniority'])
    
    for crew in crew_data:
        sen = crew['seniority']
        if sen >= my_seniority:
            break
            
        assigned = None
        for bid in crew['bids']:
            if bid in available_lines:
                assigned = bid
                available_lines.remove(bid)
                break
        
        status = f"Line {assigned}" if assigned else "No Line Awarded"
        assignments.append({'Seniority': sen, 'Awarded': status})
        
    return sorted(list(available_lines)), assignments

# --- 3. The App Interface ---
st.set_page_config(page_title="Bid Analyzer", page_icon="✈️")

st.title("✈️ Schedule Bid Analyzer")

# --- INSTRUCTIONS & DISCLAIMER ---
with st.container():
    st.info("### 📋 How to use this tool")
    st.markdown("""
    1. **Enter Details:** Input your Seniority Number and the Total Lines in the bid package.
    2. **Get Data:** Go to **"Schedule Bid Summary"**.
    3. **Save File:** Download the Summary as a **PDF** or take a **Screenshot** of the list.
    4. **Upload:** Drop that file below to see which lines are still available for you.
    """)
    
    st.warning("⚠️ **Legal Disclaimer**")
    st.markdown("""
    * **Not Official:** This tool is private and **not affiliated with UPS or IPA.**
    * **No Liability:** Results are for informational purposes only.
    * **Verify:** OCR (reading screenshots) is not perfect. **Always verify** results against official data.
    """)
    
    agree = st.checkbox("I understand the instructions and agree to the disclaimer.")

# --- MAIN APP ---
if agree:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        my_sen = st.number_input("Enter Your Seniority Number:", min_value=1, value=1787, step=1)
    with col2:
        total_lines_count = st.number_input("Total Lines Available:", min_value=1, value=42)
    
    uploaded_file = st.file_uploader("Upload Bid Summary (PDF or Screenshot)", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        st.divider()
        with st.spinner("Analyzing fleet seniority..."):
            try:
                # 1. Get Text
                raw_text = get_text_from_file(uploaded_file)
                
                # 2. Parse Data
                crew_data = parse_bid_text(raw_text)
                
                if not crew_data:
                    st.error("Could not find any bid data. If using a screenshot, make sure the image is clear and includes the 'Seniority' column.")
                else:
                    # 3. Simulate
                    available, assignment_log = simulate_bidding(crew_data, my_sen, total_lines_count)
                    
                    st.success(f"Success! Analyzed {len(crew_data)} senior bids.")
                    st.subheader(f"✅ {len(available)} Lines Still Available")
                    st.markdown(" ".join([f"`Line {line}`" for line in available]))
                    
                    with st.expander("Show Audit Log (Who took what?)"):
                        st.dataframe(assignment_log, use_container_width=True)
            except Exception as e:
                st.error(f"Error processing file: {e}")
