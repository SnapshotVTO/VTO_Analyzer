import streamlit as st
from pypdf import PdfReader
import re

# --- 1. Parsing Logic (The Engine) ---
def parse_bid_file(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    lines = text.split('\n')
    crew_data = []
    current_crew = None
    
    # Pattern: Seniority (digits) space CrewID (digits) space Bids...
    start_pattern = re.compile(r'^(\d+)\s+(\d+)\s+(.*)')
    
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
        
        # Stop processing if we reach your seniority number
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

# --- 2. The App Interface (The Front End) ---

st.set_page_config(page_title="Bid Analyzer", page_icon="✈️")

st.title("✈️ Schedule Bid Analyzer")

# --- DISCLAIMER SECTION ---
with st.container():
    st.warning("⚠️ **Legal Disclaimer & Terms of Use**")
    st.markdown("""
    1. **Not Official:** This tool is a private project and is **not affiliated with, endorsed by, or approved by UPS or the Independent Pilots Association (IPA).**
    2. **No Liability:** The results provided are for **informational purposes only**. The developer assumes no responsibility for errors, omissions, or bidding mistakes resulting from the use of this tool.
    3. **Verify Data:** Always verify your final bid choices against the official company bidding package and seniority list.
    """)
    
    agree = st.checkbox("I understand and agree to these terms.")

# --- MAIN APP ---
if agree:
    st.divider()
    st.markdown("### 🛠️ Configure Your Bid")
    
    col1, col2 = st.columns(2)
    with col1:
        my_sen = st.number_input("Enter Your Seniority Number:", min_value=1, value=1787, step=1)
    with col2:
        total_lines_count = st.number_input("Total Lines Available:", min_value=1, value=42)
    
    uploaded_file = st.file_uploader("Upload your 'Schedule Bid Summary' PDF", type="pdf")

    if uploaded_file is not None:
        st.divider()
        with st.spinner("Analyzing fleet seniority..."):
            try:
                # Run the logic
                crew_data = parse_bid_file(uploaded_file)
                available, assignment_log = simulate_bidding(crew_data, my_sen, total_lines_count)
                
                # Show Stats
                st.success(f"Analysis Complete! Processed {len(crew_data)} senior bids.")
                
                # Main Result
                st.subheader(f"✅ {len(available)} Lines Still Available")
                st.write("Based on the current senior bids, you can secure one of these lines:")
                
                # Display lines as visually distinct "chips"
                st.markdown(
                    " ".join([f"`Line {line}`" for line in available])
                )
                
                # Detailed Logs (Hidden by default to keep it clean)
                with st.expander("Show Detailed Senior Awards (Audit Log)"):
                    st.dataframe(assignment_log, use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.info("Please ensure you are uploading the correct 'Schedule Bid Summary' PDF.")

else:
    # If they haven't agreed, show a "Stop" state
    st.info("Please accept the terms above to unlock the analyzer.")
