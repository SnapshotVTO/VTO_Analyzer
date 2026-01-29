import streamlit as st
from pypdf import PdfReader
import re
from PIL import Image
import pytesseract
from streamlit_paste_button import paste_image_button

# --- 1. Text Extraction Helper Functions ---
def get_text_from_image(image):
    """Handles text extraction from a PIL Image object (Screenshots/Paste)"""
    try:
        # Tesseract needs to be installed on the system for this to work
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"Error reading image: {e}"

def get_text_from_pdf(uploaded_file):
    """Handles text extraction from a PDF file"""
    text = ""
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return text

# --- 2. Parsing Logic (The Brain) ---
def parse_bid_text(text):
    """Parses raw text into a structured list of crew bids"""
    lines = text.split('\n')
    crew_data = []
    current_crew = None
    
    # Regex to find: Seniority (digits) -> CrewID (digits/text) -> Bids
    start_pattern = re.compile(r'^(\d+)\s+(\w+)\s+(.*)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = start_pattern.match(line)
        if match:
            # Save previous crew if exists
            if current_crew:
                crew_data.append(current_crew)
            
            sen = int(match.group(1))
            crew_id = match.group(2)
            bids_str = match.group(3)
            # Extract only numbers from the bid part
            bids = [int(x) for x in re.findall(r'\d+', bids_str)]
            
            current_crew = {'seniority': sen, 'crew_id': crew_id, 'bids': bids}
        else:
            # Handle multi-line bids (lines with only numbers)
            if current_crew:
                if re.match(r'^[\d\s]+$', line):
                     more_bids = [int(x) for x in re.findall(r'\d+', line)]
                     current_crew['bids'].extend(more_bids)
    
    # Append the last crew found
    if current_crew:
        crew_data.append(current_crew)
        
    return crew_data

def simulate_bidding(crew_data, my_seniority, total_lines):
    """Runs the simulation to see which lines are taken"""
    available_lines = set(range(1, total_lines + 1))
    assignments = []
    
    # Sort by seniority to ensure correct processing order
    crew_data.sort(key=lambda x: x['seniority'])
    
    my_rank_in_bid = 0
    found_me = False
    
    for index, crew in enumerate(crew_data):
        sen = crew['seniority']
        
        # Stop processing if we reach the user's seniority
        if sen >= my_seniority:
            my_rank_in_bid = index + 1
            found_me = True
            break
            
        assigned = None
        for bid in crew['bids']:
            if bid in available_lines:
                assigned = bid
                available_lines.remove(bid)
                break
        
        status = f"Line {assigned}" if assigned else "No Line Awarded"
        assignments.append({'Seniority': sen, 'Awarded': status})
    
    # If the user wasn't found (e.g. they are deeper in the list than the file goes)
    if not found_me:
        my_rank_in_bid = len(crew_data) + 1

    return sorted(list(available_lines)), assignments, my_rank_in_bid

# --- 3. The App Interface ---
st.set_page_config(page_title="Bid Analyzer", page_icon="✈️")

st.title("✈️ Schedule Bid Analyzer")

# --- INSTRUCTIONS & DISCLAIMER ---
with st.container():
    st.info("### 📋 How to use this tool")
    st.markdown("""
    1. **Enter Details:** Input your Seniority Number and the Total Lines.
    2. **Get Data:** Go to **"Schedule Bid Summary"** on the company site.
    3. **Save/Copy:** Download the **PDF** OR take a **Screenshot** (and copy it).
    4. **Input:** Use the tabs below to **Upload** or **Paste** your data.
    """)
    
    st.warning("⚠️ **Legal Disclaimer**")
    st.markdown("""
    * **Not Official:** This tool is private and **not affiliated with UPS or IPA.**
    * **No Liability:** Results are for informational purposes only. The developer is not responsible for bidding errors.
    * **Verify:** OCR (reading images) is not 100% perfect. **Always verify** results against official data.
    """)
    
    agree = st.checkbox("I understand the instructions and agree to the disclaimer.")

# --- MAIN APP LOGIC ---
if agree:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        my_sen = st.number_input("Enter Your Seniority Number:", min_value=1, value=1787, step=1)
    with col2:
        total_lines_count = st.number_input("Total Lines Available:", min_value=1, value=42)
    
    st.write("### Choose Input Method:")
    
    # Tabs for different input methods
    tab_upload, tab_paste = st.tabs(["📂 Upload File", "📋 Paste Screenshot"])
    
    final_text_to_process = None
    
    # --- TAB 1: UPLOAD ---
    with tab
