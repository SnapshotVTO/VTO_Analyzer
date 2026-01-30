import streamlit as st
from pypdf import PdfReader
import re
from PIL import Image
import pytesseract
from streamlit_paste_button import paste_image_button

# --- 1. Text Extraction Helper Functions ---
def get_text_from_image(image):
    """Handles text extraction from a PIL Image object"""
    try:
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

# --- 2. Parsing Logic ---
def parse_bid_text(text):
    """Parses raw text into a structured list of crew bids"""
    lines = text.split('\n')
    crew_data = []
    current_crew = None
    
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
            bids = [int(x) for x in re.findall(r'\d+', bids_str)]
            current_crew = {'seniority': sen, 'crew_id': crew_id, 'bids': bids}
        else:
            if current_crew:
                if re.match(r'^[\d\s]+$', line):
                     more_bids = [int(x) for x in re.findall(r'\d+', line)]
                     current_crew['bids'].extend(more_bids)
    
    if current_crew:
        crew_data.append(current_crew)
        
    return crew_data

def simulate_bidding(crew_data, my_seniority, total_lines):
    available_lines = set(range(1, total_lines + 1))
    assignments = []
    
    crew_data.sort(key=lambda x: x['seniority'])
    
    my_rank_in_bid = 0
    found_me = False
    
    for index, crew in enumerate(crew_data):
        sen = crew['seniority']
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
    
    if not found_me:
        my_rank_in_bid = len(crew_data) + 1

    return sorted(list(available_lines)), assignments, my_rank_in_bid

# --- 3. The App Interface ---
st.set_page_config(page_title="VTO Bid Analyzer", page_icon="✈️")
st.title("✈️ VTO / Schedule Bid Analyzer")

# --- INSTRUCTIONS ---
with st.container():
    st.info("### 📋 How to use this tool")
    st.markdown("""
    1. **Enter Details:** Input your Seniority Number and the total lines available.
    2. **Get Data:** Go to **"Schedule Bid Summary"** (VTO/VTOR list).
    3. **Save/Copy:** Download the **PDF** OR take a **Screenshot** (and copy it).
    4. **Input:** Use the tabs below to **Upload** or **Paste** your data.
    """)
    
    st.warning("⚠️ **Legal Disclaimer**")
    st.markdown("""
    * **Not Official:** This tool is private and **not affiliated with UPS or IPA.**
    * **No Liability:** Results are for informational purposes only.
    * **Verify:** OCR (reading images) is not 100% perfect. **Always verify** results.
    """)
    
    agree = st.checkbox("I understand the instructions and agree to the disclaimer.")

# --- MAIN APP LOGIC ---
if agree:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        my_sen = st.number_input("Enter Your Seniority Number:", min_value=1, value=1787, step=1)
    with col2:
        total_lines_count = st.number_input("Total Lines Available:", min_value=1, value=50)
    
    st.write("### Choose Input Method:")
    
    # Initialize Session State for the image if it doesn't exist
    if 'pasted_image' not in st.session_state:
        st.session_state.pasted_image = None
    
    tab_upload, tab_paste = st.tabs(["📂 Upload File", "📋 Paste Screenshot"])
    
    final_text_to_process = None
    
    # --- TAB 1: UPLOAD ---
    with tab_upload:
        uploaded_file = st.file_uploader("Drop PDF or Image here", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded_file is not None:
            # Clear pasted image if user uploads a new file
            st.session_state.pasted_image = None 
            with st.spinner("Reading file..."):
                if uploaded_file.type == "application/pdf":
                    final_text_to_process = get_text_from_pdf(uploaded_file)
                else:
                    image = Image.open(uploaded_file)
                    final_text_to_process = get_text_from_image(image)

    # --- TAB 2: PASTE ---
    with tab_paste:
        st.write("Click the button below. If a popup asks for permission, click **Allow**.")
        
        # The Paste Button
        paste_result = paste_image_button(
            label="📋 Click to Paste Image",
            background_color="#FF4B4B",
            hover_background_color="#FF0000",
            errors="ignore" # Helps prevent crashes on browser denial
        )
        
        # LOGIC FIX: Save to Session State immediately
        if paste_result.image_data is not None:
            st.session_state.pasted_image = paste_result.image_data
            
        # If we have an image in memory, display and process it
        if st.session_state.pasted_image is not None:
            st.success("Image received!")
            st.image(st.session_state.pasted_image, caption="Pasted Screenshot", width=300)
            
            # Add a clear button in case they want to paste a different one
            if st.button("Clear Pasted Image"):
                st.session_state.pasted_image = None
                st.rerun()
                
            with st.spinner("Reading pasted image..."):
                final_text_to_process = get_text_from_image(st.session_state.pasted_image)

    # --- PROCESSING & RESULTS ---
    if final_text_to_process:
        st.divider()
        try:
            crew_data = parse_bid_text(final_text_to_process)
            
            if not crew_data:
                st.error("Could not find any bid data. Please ensure the 'Seniority' column is visible.")
            else:
                available, assignment_log, my_rank = simulate_bidding(crew_data, my_sen, total_lines_count)
                
                st.success(f"Analysis Complete!")
                m1, m2, m3 = st.columns(3)
                m1.metric("Your Seniority", my_sen)
                m2.metric("Your Rank in this Bid", f"#{my_rank}")
                m3.metric("Lines Remaining", len(available))
                
                st.subheader(f"✅ Available Lines for You")
                if len(available) > 0:
                    st.markdown(" ".join([f"`Line {line}`" for line in available]))
                else:
                    st.error("No lines appear to be available.")
                
                with st.expander("Show Audit Log (Who took what?)"):
                    st.dataframe(assignment_log, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error processing data: {e}")
