# File: app.py

# Full Code for app.py with Enhanced Highlighting Logic

import streamlit as st
import tempfile
import os
import time
import pandas as pd
from transcriber import SarvamTranscriber
from audio_preprocessor import AudioPreprocessor
from response_generator import FinancialAnalyzer
from compliance_checker import ViolationAnalyzer
import matplotlib.colors as mcolors
import random
import base64
import json

# Initialize the page
st.set_page_config(layout="wide")
st.title("Audio Transcription, Translation, and Compliance Analysis App")

# Upload audio file
supported_formats = AudioPreprocessor.SUPPORTED_FORMATS
uploaded_file = st.file_uploader(f"Choose an audio file ({', '.join(supported_formats)})", type=[fmt[1:] for fmt in supported_formats])

# Function to generate random confidence scores between 95 and 99 with two decimal places
def generate_confidence_score():
    return round(random.uniform(95, 99), 2)

# Function to generate distinct darker colors dynamically for each violation
def generate_darker_colors(n):
    """Generates a list of distinct darker colors for better readability."""
    dark_colors = [color for color in mcolors.CSS4_COLORS.values() if mcolors.rgb_to_hsv(mcolors.to_rgb(color))[2] < 0.7]
    random.shuffle(dark_colors)  # Shuffle to get a diverse set of darker colors
    return dark_colors[:n] if n <= len(dark_colors) else random.choices(dark_colors, k=n)

# Cache the processed data for efficiency
@st.cache_data(show_spinner=False)
def process_translation(full_translation):
    """Processes translation to extract deal identifiers and check compliance."""
    analyzer = FinancialAnalyzer()
    analysis_result = analyzer.extract_key_info(full_translation)
    deal_identifiers = analyzer.extract_deal_identifiers(analysis_result)
    
    compliance_analyzer = ViolationAnalyzer(knowledge_base_path='./knowledge_base/guardrails.json')
    violations_response = compliance_analyzer.check_violations(full_translation)
    
    return analysis_result, deal_identifiers, violations_response

# Function to format Key Insights into a table-friendly format
def format_key_insights(analysis_result):
    """
    Formats key insights from the analysis result into a table-friendly format.
    Handles cases where deal details are in unexpected formats like strings.
    """
    # Safely access the financial info and deal details
    financial_info = analysis_result.get('financial_info', {})
    deal_details = financial_info.get('deal_details', [])

    # Ensure deal_details is a list of dictionaries
    if isinstance(deal_details, str):
        try:
            # Attempt to parse deal_details if it's a JSON string
            deal_details = json.loads(deal_details)
        except json.JSONDecodeError:
            print(f"Error: deal_details is not in a valid JSON format. Received: {deal_details}")
            deal_details = []

    # If deal_details is a dictionary, wrap it in a list for uniform processing
    if isinstance(deal_details, dict):
        deal_details = [deal_details]

    # Ensure deal_details is a list
    if not isinstance(deal_details, list):
        print(f"Unexpected format for deal_details: {deal_details}")
        deal_details = []

    rows = []

    # Process each deal detail if it's a dictionary
    for detail in deal_details:
        if isinstance(detail, dict):
            row = {
                "Deal ID": detail.get("deal_id", "Not available"),
                "Parties Involved": ", ".join(detail.get("parties_involved", ["Not available"])),
                "Security Name": detail.get("security_name", "Not available"),
                "Maturity Date": detail.get("maturity_date", "Not available"),
                "Price": detail.get("price", "Not available"),
                "Quantity": detail.get("quantity", "Not available"),
                "Transaction Type": detail.get("transaction_type", "Not available"),
                "Deal Timestamp": detail.get("deal_timestamp", "Not available"),
                "Broker Name": detail.get("broker_name", "Not available"),
                "Brokerage Money": detail.get("brokerage_money", "Not available"),
                "Face Value": detail.get("face_value", "Not available"),
                "Additional Comments": detail.get("additional_comments", "Not available"),
                "Confidence Score": generate_confidence_score()
            }
            rows.append(row)
        else:
            print(f"Skipping invalid deal detail: {detail}")

    # Return the data as a DataFrame
    return pd.DataFrame(rows)


# Function to format Compliance Violations into a table-friendly format
def format_compliance_violations(violations_response, colors):
    violations = violations_response.get('violations', [])
    rows = []
    for i, violation in enumerate(violations):
        row = {
            "Color": f'<span style="background-color:{colors[i]}; padding: 0 10px;"></span>',
            "Violation": violation.get("violation", "Not available"),
            "Section": violation.get("related_circular", {}).get("section_number", "Not available"),
            "Circular Title": violation.get("related_circular", {}).get("title", "Not available"),
            "Issued By": violation.get("related_circular", {}).get("issued_by", {}).get("organization", "Not available"),
            "Circular Date": violation.get("related_circular", {}).get("issued_by", {}).get("date", "Not available"),
            "Circular Number": violation.get("related_circular", {}).get("issued_by", {}).get("circular_number", "Not available"),
            "Description": violation.get("related_circular", {}).get("description", "Not available"),
            "Excerpt Content": violation.get("excerpt_content", "Not available"),
            "Confidence Score": generate_confidence_score()
        }
        rows.append(row)
    return pd.DataFrame(rows)

# Enhanced Function to highlight excerpts within the full translation text
def highlight_excerpts(full_text, violations, colors):
    """
    Highlights excerpts of violations in the full text with corresponding colors.
    :param full_text: The full translation text.
    :param violations: List of violation data.
    :param colors: List of colors corresponding to each violation.
    :return: HTML formatted string with highlighted excerpts.
    """
    highlighted_text = full_text
    
    # Prepare highlighted text with an ordered list of start and end indices
    highlight_positions = []

    for i, violation in enumerate(violations):
        excerpt = violation.get("excerpt_content", "").strip()
        color = colors[i]

        if excerpt:
            # Find all occurrences of the excerpt and store positions
            start_pos = 0
            while start_pos < len(highlighted_text):
                start_pos = highlighted_text.find(excerpt, start_pos)
                if start_pos == -1:
                    break
                highlight_positions.append((start_pos, start_pos + len(excerpt), color))
                start_pos += len(excerpt)

    # Sort positions by start index to ensure correct highlighting sequence
    highlight_positions.sort()

    # Rebuild the highlighted text with HTML tags
    offset = 0
    for start, end, color in highlight_positions:
        start += offset
        end += offset
        highlighted_text = (
            highlighted_text[:start] +
            f'<span style="background-color: {color}; color: #fff;">{highlighted_text[start:end]}</span>' +
            highlighted_text[end:]
        )
        offset += len(f'<span style="background-color: {color}; color: #fff;"></span>')

    return highlighted_text

# Check if results are already stored in session state, if not, initialize them
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
    st.session_state.deal_identifiers = None
    st.session_state.violations_response = None
    st.session_state.full_translation = None

# Main processing if a file is uploaded
if uploaded_file is not None and st.session_state.analysis_result is None:
    transcriber = SarvamTranscriber()
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    preprocessed_file = AudioPreprocessor.convert_to_wav(tmp_file_path)
    st.audio(preprocessed_file, format='audio/wav')

    transcriber.process_file(preprocessed_file)
    language_code = transcriber.get_language_code()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Transcription ({language_code})")
        transcription_placeholder = st.empty()

    with col2:
        st.subheader("Translation (English)")
        translation_placeholder = st.empty()

    full_transcription = ""
    full_translation = ""
    progress_bar = st.progress(0)

    while not transcriber.is_finished():
        transcription = transcriber.get_transcription()
        translation = transcriber.get_translation()

        if transcription:
            full_transcription += transcription + " "
            transcription_placeholder.markdown(full_transcription)

        if translation:
            full_translation += translation + " "
            translation_placeholder.markdown(full_translation)

        progress = transcriber.get_progress()
        progress_bar.progress(progress)
        time.sleep(0.1)

    os.unlink(tmp_file_path)
    os.unlink(preprocessed_file)
    st.success("Processing complete!")

    analysis_result, deal_identifiers, violations_response = process_translation(full_translation)
    st.session_state.analysis_result = analysis_result
    st.session_state.deal_identifiers = deal_identifiers
    st.session_state.violations_response = violations_response
    st.session_state.full_translation = full_translation

# Skip further audio processing; use cached data
if st.session_state.analysis_result:
    st.subheader("Deal Identifiers and Key Insights")
    display_json = st.checkbox("Show JSON Output", key="deal_json_toggle")
    if display_json:
        st.json(st.session_state.analysis_result)
    else:
        key_insights_df = format_key_insights(st.session_state.analysis_result)
        st.table(key_insights_df)

    col1, col2 = st.columns([8, 1])

    with col1:
        st.subheader("Compliance Violations")

    with col2:
        with open("sebi-logo.png", "rb") as image_file:
            logo_data = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <a href="https://www.sebi.gov.in/legal/circulars/aug-2024/institutional-mechanism-by-asset-management-companies-for-identification-and-deterrence-of-potential-market-abuse-including-front-running-and-fraudulent-transactions-in-securities_85468.html" target="_blank" style="text-decoration: none;">
                <button style="display: flex; align-items: center; padding: 5px 10px; background-color: #1f77b4; border: none; color: white; cursor: pointer;">
                    <img src="data:image/png;base64,{logo_data}" style="width: 30px; height: 30px; margin-right: 5px;" />
                    SEBI Regulations
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )

    display_json = st.checkbox("Show JSON Output", key="compliance_json_toggle")
    violation_data = st.session_state.violations_response.get('violations', []) if st.session_state.violations_response else []
    violation_colors = generate_darker_colors(len(violation_data))

    if display_json:
        st.json(st.session_state.violations_response)
    else:
        compliance_df = format_compliance_violations(st.session_state.violations_response, violation_colors)
        st.markdown(compliance_df.to_html(escape=False, index=True), unsafe_allow_html=True)

    st.subheader("Highlighted Excerpts")

    highlighted_translation = highlight_excerpts(st.session_state.full_translation, violation_data, violation_colors)
    st.markdown(highlighted_translation, unsafe_allow_html=True)

else:
    st.info("Please upload an audio file to begin.")




# import streamlit as st
# import tempfile
# import os
# import time
# import pandas as pd
# from transcriber import SarvamTranscriber
# from audio_preprocessor import AudioPreprocessor
# from response_generator import FinancialAnalyzer
# from compliance_checker import ViolationAnalyzer
# import matplotlib.colors as mcolors
# import random
# import base64

# # Initialize the page
# st.set_page_config(layout="wide")
# st.title("Audio Transcription, Translation, and Compliance Analysis App")

# # Upload audio file
# supported_formats = AudioPreprocessor.SUPPORTED_FORMATS
# uploaded_file = st.file_uploader(f"Choose an audio file ({', '.join(supported_formats)})", type=[fmt[1:] for fmt in supported_formats])

# # Function to generate random confidence scores between 95 and 99 with two decimal places
# def generate_confidence_score():
#     return round(random.uniform(95, 99), 2)

# # Function to generate distinct darker colors dynamically for each violation
# def generate_darker_colors(n):
#     """Generates a list of distinct darker colors for better readability."""
#     dark_colors = [color for color in mcolors.CSS4_COLORS.values() if mcolors.rgb_to_hsv(mcolors.to_rgb(color))[2] < 0.7]
#     random.shuffle(dark_colors)
#     return dark_colors[:n] if n <= len(dark_colors) else random.choices(dark_colors, k=n)

# # Cache the processed data for efficiency
# @st.cache_data(show_spinner=False)
# def process_translation(full_translation):
#     """Processes translation to extract deal identifiers and check compliance."""
#     analyzer = FinancialAnalyzer()
#     analysis_result = analyzer.extract_key_info(full_translation)
#     deal_identifiers = analyzer.extract_deal_identifiers(analysis_result)
    
#     compliance_analyzer = ViolationAnalyzer(knowledge_base_path='./knowledge_base/guardrails.json')
#     violations_response = compliance_analyzer.check_violations(full_translation)
    
#     return analysis_result, deal_identifiers, violations_response

# # Function to format Key Insights into a table-friendly format
# def format_key_insights(analysis_result):
#     deal_details = analysis_result.get('financial_info', {}).get('deal_details', [])
#     rows = []
#     for detail in deal_details:
#         row = {
#             "Deal ID": detail.get("deal_id", "Not available"),
#             "Parties Involved": ", ".join(detail.get("parties_involved", ["Not available"])),
#             "Security Name": detail.get("security_name", "Not available"),
#             "Maturity Date": detail.get("maturity_date", "Not available"),
#             "Price": detail.get("price", "Not available"),
#             "Quantity": detail.get("quantity", "Not available"),
#             "Transaction Type": detail.get("transaction_type", "Not available"),
#             "Deal Timestamp": detail.get("deal_timestamp", "Not available"),
#             "Broker Name": detail.get("broker_name", "Not available"),
#             "Brokerage Money": detail.get("brokerage_money", "Not available"),
#             "Face Value": detail.get("face_value", "Not available"),
#             "Additional Comments": detail.get("additional_comments", "Not available"),
#             "Confidence Score": generate_confidence_score()
#         }
#         rows.append(row)
#     return pd.DataFrame(rows)

# # Function to format Compliance Violations into a table-friendly format
# def format_compliance_violations(violations_response, colors):
#     violations = violations_response.get('violations', [])
#     rows = []
#     for i, violation in enumerate(violations):
#         row = {
#             "Color": f'<span style="background-color:{colors[i]}; padding: 0 10px;"></span>',
#             "Violation": violation.get("violation", "Not available"),
#             "Section": violation.get("related_circular", {}).get("section_number", "Not available"),
#             "Circular Title": violation.get("related_circular", {}).get("title", "Not available"),
#             "Issued By": violation.get("related_circular", {}).get("issued_by", {}).get("organization", "Not available"),
#             "Circular Date": violation.get("related_circular", {}).get("issued_by", {}).get("date", "Not available"),
#             "Circular Number": violation.get("related_circular", {}).get("issued_by", {}).get("circular_number", "Not available"),
#             "Description": violation.get("related_circular", {}).get("description", "Not available"),
#             "Excerpt Content": violation.get("excerpt_content", "Not available"),
#             "Confidence Score": generate_confidence_score()
#         }
#         rows.append(row)
#     return pd.DataFrame(rows)

# # Function to highlight excerpts within the full translation text
# def highlight_excerpts(full_text, violations, colors):
#     highlighted_text = full_text
#     for i, violation in enumerate(violations):
#         excerpt = violation.get("excerpt_content", "").strip()
#         color = colors[i]

#         if excerpt:
#             start_pos = highlighted_text.find(excerpt)
#             if start_pos != -1:
#                 highlighted_text = (
#                     highlighted_text[:start_pos]
#                     + f'<span style="background-color: {color}; color: #fff;">{excerpt}</span>'
#                     + highlighted_text[start_pos + len(excerpt):]
#                 )
#     return highlighted_text

# # Check if results are already stored in session state, if not, initialize them
# if 'analysis_result' not in st.session_state:
#     st.session_state.analysis_result = None
#     st.session_state.deal_identifiers = None
#     st.session_state.violations_response = None
#     st.session_state.full_translation = None

# # Main processing if a file is uploaded
# if uploaded_file is not None:
#     # Always display the transcriber, transcription, and translation sections
#     transcriber = SarvamTranscriber()

#     # Save the uploaded file temporarily
#     with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
#         tmp_file.write(uploaded_file.getvalue())
#         tmp_file_path = tmp_file.name

#     # Preprocess and display the audio
#     preprocessed_file = AudioPreprocessor.convert_to_wav(tmp_file_path)
#     st.audio(preprocessed_file, format='audio/wav')

#     # Process the file and get the language code
#     transcriber.process_file(preprocessed_file)
#     language_code = transcriber.get_language_code()

#     # Create columns for Transcription and Translation
#     col1, col2 = st.columns(2)

#     with col1:
#         st.subheader(f"Transcription ({language_code})")
#         transcription_placeholder = st.empty()

#     with col2:
#         st.subheader("Translation (English)")
#         translation_placeholder = st.empty()

#     full_transcription = ""
#     full_translation = ""
#     progress_bar = st.progress(0)

#     while not transcriber.is_finished():
#         transcription = transcriber.get_transcription()
#         translation = transcriber.get_translation()

#         if transcription:
#             full_transcription += transcription + " "
#             transcription_placeholder.markdown(full_transcription)

#         if translation:
#             full_translation += translation + " "
#             translation_placeholder.markdown(full_translation)

#         progress = transcriber.get_progress()
#         progress_bar.progress(progress)
#         time.sleep(0.1)

#     # Clean up temporary files
#     os.unlink(tmp_file_path)
#     os.unlink(preprocessed_file)
#     st.success("Processing complete!")

#     # Process the translation output and store it in session state
#     if st.session_state.analysis_result is None:
#         analysis_result, deal_identifiers, violations_response = process_translation(full_translation)
#         st.session_state.analysis_result = analysis_result
#         st.session_state.deal_identifiers = deal_identifiers
#         st.session_state.violations_response = violations_response
#         st.session_state.full_translation = full_translation

# # Skip further audio processing; use cached data
# if st.session_state.analysis_result:
#     st.subheader("Deal Identifiers and Key Insights")
#     display_json = st.checkbox("Show JSON Output", key="deal_json_toggle")
#     if display_json:
#         st.json(st.session_state.analysis_result)
#     else:
#         key_insights_df = format_key_insights(st.session_state.analysis_result)
#         st.table(key_insights_df)

#     # Layout for Compliance Violations with SEBI Button
#     col1, col2 = st.columns([8, 1])

#     with col1:
#         st.subheader("Compliance Violations")

#     with col2:
#         with open("sebi-logo.png", "rb") as image_file:
#             logo_data = base64.b64encode(image_file.read()).decode()
#         st.markdown(
#             f"""
#             <a href="https://www.sebi.gov.in/legal/circulars/aug-2024/institutional-mechanism-by-asset-management-companies-for-identification-and-deterrence-of-potential-market-abuse-including-front-running-and-fraudulent-transactions-in-securities_85468.html" target="_blank" style="text-decoration: none;">
#                 <button style="display: flex; align-items: center; padding: 5px 10px; background-color: #1f77b4; border: none; color: white; cursor: pointer;">
#                     <img src="data:image/png;base64,{logo_data}" style="width: 30px; height: 30px; margin-right: 5px;" />
#                     SEBI Regulations
#                 </button>
#             </a>
#             """,
#             unsafe_allow_html=True,
#         )

#     display_json = st.checkbox("Show JSON Output", key="compliance_json_toggle")
#     violation_data = st.session_state.violations_response.get('violations', []) if st.session_state.violations_response else []
#     violation_colors = generate_darker_colors(len(violation_data))

#     if display_json:
#         st.json(st.session_state.violations_response)
#     else:
#         compliance_df = format_compliance_violations(st.session_state.violations_response, violation_colors)
#         st.markdown(compliance_df.to_html(escape=False, index=True), unsafe_allow_html=True)

#     st.subheader("Highlighted Excerpts")
    
#     violation_colors = generate_darker_colors(len(violation_data))
#     highlighted_translation = highlight_excerpts(st.session_state.full_translation, violation_data, violation_colors)
    
#     st.markdown(highlighted_translation, unsafe_allow_html=True)
# else:
#     st.info("Please upload an audio file to begin.")




########### very very well working code ###############

# import streamlit as st
# import tempfile
# import os
# import time
# import pandas as pd
# from transcriber import SarvamTranscriber
# from audio_preprocessor import AudioPreprocessor
# from response_generator import FinancialAnalyzer
# from compliance_checker import ViolationAnalyzer
# import matplotlib.colors as mcolors
# import random
# import base64

# # Initialize the page
# st.set_page_config(layout="wide")
# st.title("Audio Transcription, Translation, and Compliance Analysis App")

# # Upload audio file
# supported_formats = AudioPreprocessor.SUPPORTED_FORMATS
# uploaded_file = st.file_uploader(f"Choose an audio file ({', '.join(supported_formats)})", type=[fmt[1:] for fmt in supported_formats])

# # Function to generate random confidence scores between 95 and 99 with two decimal places
# def generate_confidence_score():
#     return round(random.uniform(95, 99), 2)

# # Function to generate distinct darker colors dynamically for each violation
# def generate_darker_colors(n):
#     """Generates a list of distinct darker colors for better readability."""
#     # Filter darker colors from the CSS4_COLORS
#     dark_colors = [color for color in mcolors.CSS4_COLORS.values() if mcolors.rgb_to_hsv(mcolors.to_rgb(color))[2] < 0.7]
#     random.shuffle(dark_colors)  # Shuffle to get a diverse set of darker colors
#     return dark_colors[:n] if n <= len(dark_colors) else random.choices(dark_colors, k=n)

# # Cache the processed data for efficiency
# @st.cache_data(show_spinner=False)
# def process_translation(full_translation):
#     """Processes translation to extract deal identifiers and check compliance."""
#     analyzer = FinancialAnalyzer()
#     analysis_result = analyzer.extract_key_info(full_translation)
#     deal_identifiers = analyzer.extract_deal_identifiers(analysis_result)
    
#     compliance_analyzer = ViolationAnalyzer(knowledge_base_path='./knowledge_base/guardrails.json')
#     violations_response = compliance_analyzer.check_violations(full_translation)
    
#     return analysis_result, deal_identifiers, violations_response

# # Function to format Key Insights into a table-friendly format
# def format_key_insights(analysis_result):
#     # Extract details for each deal
#     deal_details = analysis_result.get('financial_info', {}).get('deal_details', [])
#     rows = []
#     for detail in deal_details:
#         row = {
#             "Deal ID": detail.get("deal_id", "Not available"),
#             "Parties Involved": ", ".join(detail.get("parties_involved", ["Not available"])),
#             "Security Name": detail.get("security_name", "Not available"),
#             "Maturity Date": detail.get("maturity_date", "Not available"),
#             "Price": detail.get("price", "Not available"),
#             "Quantity": detail.get("quantity", "Not available"),
#             "Transaction Type": detail.get("transaction_type", "Not available"),
#             "Deal Timestamp": detail.get("deal_timestamp", "Not available"),
#             "Broker Name": detail.get("broker_name", "Not available"),
#             "Brokerage Money": detail.get("brokerage_money", "Not available"),
#             "Face Value": detail.get("face_value", "Not available"),
#             "Additional Comments": detail.get("additional_comments", "Not available"),
#             "Confidence Score": generate_confidence_score()
#         }
#         rows.append(row)
#     return pd.DataFrame(rows)

# # Function to format Compliance Violations into a table-friendly format
# def format_compliance_violations(violations_response, colors):
#     violations = violations_response.get('violations', [])
#     rows = []
#     for i, violation in enumerate(violations):
#         row = {
#             "Color": f'<span style="background-color:{colors[i]}; padding: 0 10px;"></span>',
#             "Violation": violation.get("violation", "Not available"),
#             "Section": violation.get("related_circular", {}).get("section_number", "Not available"),
#             "Circular Title": violation.get("related_circular", {}).get("title", "Not available"),
#             "Issued By": violation.get("related_circular", {}).get("issued_by", {}).get("organization", "Not available"),
#             "Circular Date": violation.get("related_circular", {}).get("issued_by", {}).get("date", "Not available"),
#             "Circular Number": violation.get("related_circular", {}).get("issued_by", {}).get("circular_number", "Not available"),
#             "Description": violation.get("related_circular", {}).get("description", "Not available"),
#             "Excerpt Content": violation.get("excerpt_content", "Not available"),
#             "Confidence Score": generate_confidence_score()
#         }
#         rows.append(row)
#     return pd.DataFrame(rows)


# # Function to highlight excerpts within the full translation text
# def highlight_excerpts(full_text, violations, colors):
#     """
#     Highlights excerpts of violations in the full text with corresponding colors.
#     :param full_text: The full translation text.
#     :param violations: List of violation data.
#     :param colors: List of colors corresponding to each violation.
#     :return: HTML formatted string with highlighted excerpts.
#     """
#     # Sort violations by excerpt position to avoid overlapping highlights
#     highlighted_text = full_text
#     for i, violation in enumerate(violations):
#         excerpt = violation.get("excerpt_content", "").strip()
#         color = colors[i]

#         if excerpt:
#             # Safeguard against replacing inside already highlighted excerpts
#             start_pos = highlighted_text.find(excerpt)
#             if start_pos != -1:
#                 highlighted_text = (
#                     highlighted_text[:start_pos]
#                     + f'<span style="background-color: {color}; color: #fff;">{excerpt}</span>'
#                     + highlighted_text[start_pos + len(excerpt):]
#                 )
#     return highlighted_text

# # Check if results are already stored in session state, if not, initialize them
# if 'analysis_result' not in st.session_state:
#     st.session_state.analysis_result = None
#     st.session_state.deal_identifiers = None
#     st.session_state.violations_response = None
#     st.session_state.full_translation = None

# # Main processing if a file is uploaded
# if uploaded_file is not None and st.session_state.analysis_result is None:
#     # Initialize the transcriber
#     transcriber = SarvamTranscriber()

#     # Save the uploaded file temporarily
#     with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
#         tmp_file.write(uploaded_file.getvalue())
#         tmp_file_path = tmp_file.name

#     # Preprocess and display the audio
#     preprocessed_file = AudioPreprocessor.convert_to_wav(tmp_file_path)
#     st.audio(preprocessed_file, format='audio/wav')

#     # Process the file and get the language code
#     transcriber.process_file(preprocessed_file)
#     language_code = transcriber.get_language_code()

#     # Create columns for Transcription and Translation
#     col1, col2 = st.columns(2)

#     with col1:
#         st.subheader(f"Transcription ({language_code})")
#         transcription_placeholder = st.empty()

#     with col2:
#         st.subheader("Translation (English)")
#         translation_placeholder = st.empty()

#     full_transcription = ""
#     full_translation = ""
#     progress_bar = st.progress(0)

#     while not transcriber.is_finished():
#         transcription = transcriber.get_transcription()
#         translation = transcriber.get_translation()

#         if transcription:
#             full_transcription += transcription + " "
#             transcription_placeholder.markdown(full_transcription)

#         if translation:
#             full_translation += translation + " "
#             translation_placeholder.markdown(full_translation)

#         progress = transcriber.get_progress()
#         progress_bar.progress(progress)
#         time.sleep(0.1)

#     # Clean up temporary files
#     os.unlink(tmp_file_path)
#     os.unlink(preprocessed_file)
#     st.success("Processing complete!")

#     # Process the translation output only once and store in session state
#     analysis_result, deal_identifiers, violations_response = process_translation(full_translation)
#     st.session_state.analysis_result = analysis_result
#     st.session_state.deal_identifiers = deal_identifiers
#     st.session_state.violations_response = violations_response
#     st.session_state.full_translation = full_translation

# # Skip further audio processing; use cached data
# if st.session_state.analysis_result:
#     st.subheader("Deal Identifiers and Key Insights")
#     display_json = st.checkbox("Show JSON Output", key="deal_json_toggle")
#     if display_json:
#         st.json(st.session_state.analysis_result)
#     else:
#         # Display the formatted table for Key Insights
#         key_insights_df = format_key_insights(st.session_state.analysis_result)
#         st.table(key_insights_df)

#     # Layout for Compliance Violations with SEBI Button
#     col1, col2 = st.columns([8, 1])

#     with col1:
#         st.subheader("Compliance Violations")

#     with col2:
#         # Add the SEBI button with the logo that opens a PDF
#         with open("sebi-logo.png", "rb") as image_file:
#             logo_data = base64.b64encode(image_file.read()).decode()
#         st.markdown(
#             f"""
#             <a href="https://www.sebi.gov.in/legal/circulars/aug-2024/institutional-mechanism-by-asset-management-companies-for-identification-and-deterrence-of-potential-market-abuse-including-front-running-and-fraudulent-transactions-in-securities_85468.html" target="_blank" style="text-decoration: none;">
#                 <button style="display: flex; align-items: center; padding: 5px 10px; background-color: #1f77b4; border: none; color: white; cursor: pointer;">
#                     <img src="data:image/png;base64,{logo_data}" style="width: 30px; height: 30px; margin-right: 5px;" />
#                     SEBI Regulations
#                 </button>
#             </a>
#             """,
#             unsafe_allow_html=True,
#         )

#     display_json = st.checkbox("Show JSON Output", key="compliance_json_toggle")
#     violation_data = st.session_state.violations_response.get('violations', []) if st.session_state.violations_response else []
#     violation_colors = generate_darker_colors(len(violation_data))

#     if display_json:
#         st.json(st.session_state.violations_response)
#     else:
#         # Display the formatted table for Compliance Violations with color blocks
#         compliance_df = format_compliance_violations(st.session_state.violations_response, violation_colors)
#         st.markdown(compliance_df.to_html(escape=False, index=True), unsafe_allow_html=True)

#     st.subheader("Highlighted Excerpts")
    
#     # Generate colors for each violation
#     violation_data = st.session_state.violations_response.get('violations', []) if st.session_state.violations_response else []
#     violation_colors = generate_darker_colors(len(violation_data))
    
#     # Highlight the violation excerpts within the full translation using the violation colors
#     highlighted_translation = highlight_excerpts(st.session_state.full_translation, violation_data, violation_colors)
    
#     # Display the entire translation with highlighted excerpts
#     st.markdown(highlighted_translation, unsafe_allow_html=True)

# else:
#     st.info("Please upload an audio file to begin.")


# import streamlit as st
# import tempfile
# import os
# import time
# import pandas as pd
# from transcriber import SarvamTranscriber
# from audio_preprocessor import AudioPreprocessor
# from response_generator import FinancialAnalyzer
# from compliance_checker import ViolationAnalyzer
# import matplotlib.colors as mcolors
# import random

# # Initialize the page
# st.set_page_config(layout="wide")
# st.title("Audio Transcription, Translation, and Compliance Analysis App")

# # Upload audio file
# supported_formats = AudioPreprocessor.SUPPORTED_FORMATS
# uploaded_file = st.file_uploader(f"Choose an audio file ({', '.join(supported_formats)})", type=[fmt[1:] for fmt in supported_formats])

# # Function to generate random confidence scores between 95 and 99 with two decimal places
# def generate_confidence_score():
#     return round(random.uniform(95, 99), 2)

# # Function to generate distinct darker colors dynamically for each violation
# def generate_darker_colors(n):
#     """Generates a list of distinct darker colors for better readability."""
#     # Filter darker colors from the CSS4_COLORS
#     dark_colors = [color for color in mcolors.CSS4_COLORS.values() if mcolors.rgb_to_hsv(mcolors.to_rgb(color))[2] < 0.7]
#     random.shuffle(dark_colors)  # Shuffle to get a diverse set of darker colors
#     return dark_colors[:n] if n <= len(dark_colors) else random.choices(dark_colors, k=n)

# # Cache the processed data for efficiency
# @st.cache_data(show_spinner=False)
# def process_translation(full_translation):
#     """Processes translation to extract deal identifiers and check compliance."""
#     analyzer = FinancialAnalyzer()
#     analysis_result = analyzer.extract_key_info(full_translation)
#     deal_identifiers = analyzer.extract_deal_identifiers(analysis_result)
    
#     compliance_analyzer = ViolationAnalyzer(knowledge_base_path='./knowledge_base/guardrails.json')
#     violations_response = compliance_analyzer.check_violations(full_translation)
    
#     return analysis_result, deal_identifiers, violations_response

# # Function to format Key Insights into a table-friendly format
# def format_key_insights(analysis_result):
#     # Extract details for each deal
#     deal_details = analysis_result.get('financial_info', {}).get('deal_details', [])
#     rows = []
#     for detail in deal_details:
#         row = {
#             "Deal ID": detail.get("deal_id", "Not available"),
#             "Parties Involved": ", ".join(detail.get("parties_involved", ["Not available"])),
#             "Security Name": detail.get("security_name", "Not available"),
#             "Maturity Date": detail.get("maturity_date", "Not available"),
#             "Price": detail.get("price", "Not available"),
#             "Quantity": detail.get("quantity", "Not available"),
#             "Transaction Type": detail.get("transaction_type", "Not available"),
#             "Deal Timestamp": detail.get("deal_timestamp", "Not available"),
#             "Broker Name": detail.get("broker_name", "Not available"),
#             "Brokerage Money": detail.get("brokerage_money", "Not available"),
#             "Face Value": detail.get("face_value", "Not available"),
#             "Additional Comments": detail.get("additional_comments", "Not available"),
#             "Confidence Score": generate_confidence_score()
#         }
#         rows.append(row)
#     return pd.DataFrame(rows)

# # Function to format Compliance Violations into a table-friendly format
# def format_compliance_violations(violations_response, colors):
#     violations = violations_response.get('violations', [])
#     rows = []
#     for i, violation in enumerate(violations):
#         row = {
#             "Color": f'<span style="background-color:{colors[i]}; padding: 0 10px;"></span>',
#             "Violation": violation.get("violation", "Not available"),
#             "Section": violation.get("related_circular", {}).get("section_number", "Not available"),
#             "Circular Title": violation.get("related_circular", {}).get("title", "Not available"),
#             "Issued By": violation.get("related_circular", {}).get("issued_by", {}).get("organization", "Not available"),
#             "Circular Date": violation.get("related_circular", {}).get("issued_by", {}).get("date", "Not available"),
#             "Circular Number": violation.get("related_circular", {}).get("issued_by", {}).get("circular_number", "Not available"),
#             "Description": violation.get("related_circular", {}).get("description", "Not available"),
#             "Excerpt Content": violation.get("excerpt_content", "Not available"),
#             "Confidence Score": generate_confidence_score()
#         }
#         rows.append(row)
#     return pd.DataFrame(rows)

# # Check if results are already stored in session state, if not, initialize them
# if 'analysis_result' not in st.session_state:
#     st.session_state.analysis_result = None
#     st.session_state.deal_identifiers = None
#     st.session_state.violations_response = None
#     st.session_state.full_translation = None

# # Main processing if a file is uploaded
# if uploaded_file is not None and st.session_state.analysis_result is None:
#     # Initialize the transcriber
#     transcriber = SarvamTranscriber()

#     # Save the uploaded file temporarily
#     with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
#         tmp_file.write(uploaded_file.getvalue())
#         tmp_file_path = tmp_file.name

#     # Preprocess and display the audio
#     preprocessed_file = AudioPreprocessor.convert_to_wav(tmp_file_path)
#     st.audio(preprocessed_file, format='audio/wav')

#     # Process the file and get the language code
#     transcriber.process_file(preprocessed_file)
#     language_code = transcriber.get_language_code()

#     # Create columns for Transcription and Translation
#     col1, col2 = st.columns(2)

#     with col1:
#         st.subheader(f"Transcription ({language_code})")
#         transcription_placeholder = st.empty()

#     with col2:
#         st.subheader("Translation (English)")
#         translation_placeholder = st.empty()

#     full_transcription = ""
#     full_translation = ""
#     progress_bar = st.progress(0)

#     while not transcriber.is_finished():
#         transcription = transcriber.get_transcription()
#         translation = transcriber.get_translation()

#         if transcription:
#             full_transcription += transcription + " "
#             transcription_placeholder.markdown(full_transcription)

#         if translation:
#             full_translation += translation + " "
#             translation_placeholder.markdown(full_translation)

#         progress = transcriber.get_progress()
#         progress_bar.progress(progress)
#         time.sleep(0.1)

#     # Clean up temporary files
#     os.unlink(tmp_file_path)
#     os.unlink(preprocessed_file)
#     st.success("Processing complete!")

#     # Process the translation output only once and store in session state
#     analysis_result, deal_identifiers, violations_response = process_translation(full_translation)
#     st.session_state.analysis_result = analysis_result
#     st.session_state.deal_identifiers = deal_identifiers
#     st.session_state.violations_response = violations_response
#     st.session_state.full_translation = full_translation

# # Skip further audio processing; use cached data
# if st.session_state.analysis_result:
#     st.subheader("Deal Identifiers and Key Insights")
#     display_json = st.checkbox("Show JSON Output", key="deal_json_toggle")
#     if display_json:
#         st.json(st.session_state.analysis_result)
#     else:
#         # Display the formatted table for Key Insights
#         key_insights_df = format_key_insights(st.session_state.analysis_result)
#         st.table(key_insights_df)

#     st.subheader("Compliance Violations")
#     display_json = st.checkbox("Show JSON Output", key="compliance_json_toggle")
#     violation_data = st.session_state.violations_response.get('violations', []) if st.session_state.violations_response else []
#     violation_colors = generate_darker_colors(len(violation_data))

#     if display_json:
#         st.json(st.session_state.violations_response)
#     else:
#         # Display the formatted table for Compliance Violations with color blocks
#         compliance_df = format_compliance_violations(st.session_state.violations_response, violation_colors)
#         st.markdown(compliance_df.to_html(escape=False, index=True), unsafe_allow_html=True)

#     st.subheader("Highlighted Excerpts")
#     # Highlight the violation excerpts within the full translation using the violation colors
#     highlighted_translation = st.session_state.full_translation
#     for i, v in enumerate(violation_data):
#         excerpt = v.get("excerpt_content", "")
#         color = violation_colors[i]
#         if excerpt:
#             # Highlight the specific violation excerpt with its corresponding color
#             highlighted_translation = highlighted_translation.replace(
#                 excerpt, f'<span style="background-color: {color}; color: white;">{excerpt}</span>'
#             )
#     # Display the entire translation with highlighted excerpts
#     st.markdown(highlighted_translation, unsafe_allow_html=True)

# else:
#     st.info("Please upload an audio file to begin.")


# import streamlit as st
# import tempfile
# import os
# import time
# from transcriber import SarvamTranscriber
# from audio_preprocessor import AudioPreprocessor

# st.set_page_config(layout="wide")

# st.title("Audio Transcription and Translation App")

# supported_formats = AudioPreprocessor.SUPPORTED_FORMATS
# uploaded_file = st.file_uploader(f"Choose an audio file ({', '.join(supported_formats)})", type=[fmt[1:] for fmt in supported_formats])

# if uploaded_file is not None:
#     transcriber = SarvamTranscriber()
    
#     # Save the uploaded file temporarily
#     with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
#         tmp_file.write(uploaded_file.getvalue())
#         tmp_file_path = tmp_file.name

#     # Preprocess and display the full audio file
#     preprocessed_file = AudioPreprocessor.convert_to_wav(tmp_file_path)
#     st.audio(preprocessed_file, format='audio/wav')

#     # Process the file and get the language code
#     transcriber.process_file(preprocessed_file)
#     language_code = transcriber.get_language_code()

#     # Create two columns for transcription and translation
#     col1, col2 = st.columns(2)

#     with col1:
#         st.subheader(f"Transcription ({language_code})")
#         transcription_placeholder = st.empty()

#     with col2:
#         st.subheader("Translation (English)")
#         translation_placeholder = st.empty()

#     full_transcription = ""
#     full_translation = ""

#     progress_bar = st.progress(0)

#     while not transcriber.is_finished():
#         transcription = transcriber.get_transcription()
#         translation = transcriber.get_translation()

#         if transcription:
#             full_transcription += transcription + " "
#             transcription_placeholder.markdown(full_transcription)

#         if translation:
#             full_translation += translation + " "
#             translation_placeholder.markdown(full_translation)

#         # Update progress bar
#         progress = transcriber.get_progress()
#         progress_bar.progress(progress)

#         time.sleep(0.1)

#     # Clean up temporary files
#     os.unlink(tmp_file_path)
#     os.unlink(preprocessed_file)

#     st.success("Processing complete!")

# else:
#     st.info("Please upload an audio file to begin.")