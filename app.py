import streamlit as st
import os
import numpy as np
import cv2
import fitz  # PyMuPDF
from PIL import Image, ImageChops, ImageEnhance

# --- Helper Function to Save Uploaded Files ---
def save_uploaded_file(uploaded_file, save_path):
    """Saves an uploaded file to a specified path."""
    try:
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False

# --- Core Analysis Functions (from previous logic) ---

def pdf_to_image(pdf_path, output_path):
    """Converts the first page of a PDF to a PNG image."""
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # Load the first page
        pix = page.get_pixmap()
        pix.save(output_path)
        doc.close()
        return True
    except Exception as e:
        st.error(f"Error converting PDF to image: {e}")
        return False

def analyze_metadata(image_path):
    """Analyzes the metadata of an image file for suspicious information."""
    st.subheader("1. Metadata Analysis")
    suspicion_points = 0
    try:
        image = Image.open(image_path)
        metadata = image.info

        if not metadata:
            st.info("No metadata found in the image.")
            return 0

        st.write("Found Metadata:", metadata)
        suspicious_software = ['photoshop', 'gimp', 'adobe']
        for key, value in metadata.items():
            if isinstance(value, str):
                for software in suspicious_software:
                    if software in value.lower():
                        st.warning(f"Alert: Found suspicious software tag - {value}")
                        suspicion_points += 1
        
        if suspicion_points == 0:
            st.success("No suspicious software tags found in metadata.")
    except Exception as e:
        st.error(f"An error occurred during metadata analysis: {e}")
    return suspicion_points

def perform_error_level_analysis(image_path, output_path):
    """Performs Error Level Analysis (ELA) to detect image manipulation."""
    st.subheader("2. Pixel-Level Analysis (ELA)")
    suspicion_points = 0
    try:
        original_image = Image.open(image_path).convert('RGB')
        resaved_path = 'temp_resaved.jpg'
        original_image.save(resaved_path, 'JPEG', quality=95)
        resaved_image = Image.open(resaved_path)
        ela_image = ImageChops.difference(original_image, resaved_image)
        extrema = ela_image.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0: max_diff = 1
        scale = 255.0 / max_diff
        brightened_ela = ImageEnhance.Brightness(ela_image).enhance(scale)
        brightened_ela.save(output_path)
        
        st.write("ELA image generated. Brighter areas may indicate manipulation.")
        st.image(output_path, caption="Error Level Analysis Result")
        
        ela_array = np.array(brightened_ela)
        if np.mean(ela_array) > 20:
            suspicion_points += 2 # ELA is a strong indicator
            st.warning("Alert: High variance detected in ELA result, suggesting possible editing.")
        else:
            st.success("ELA result appears consistent.")
    except Exception as e:
        st.error(f"An error occurred during ELA: {e}")
    return suspicion_points

def verify_document_elements(document_image_path, template_path):
    """
    Verifies embedded elements using template matching.
    This version automatically handles swapped inputs and resizes the template if necessary.
    """
    st.subheader("3. Element Verification (Template Matching)")
    suspicion_points = 0
    try:
        # Load both images
        img1 = cv2.imread(document_image_path)
        img2 = cv2.imread(template_path)

        if img1 is None or img2 is None:
            st.error("Could not load one or both images. Please ensure they are valid files.")
            return 1

        # --- NEW LOGIC: Automatically determine which is the document and which is the template ---
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]

        # Assume the image with the larger area is the document
        if (h1 * w1) >= (h2 * w2):
            document_img_cv = img1
            template_img_cv = img2
            st.info("Auto-detection: Larger image assigned as document, smaller as template.")
        else:
            document_img_cv = img2
            template_img_cv = img1
            st.warning("Auto-correction: Inputs appear to be swapped. Correcting automatically.")

        # Convert to grayscale for matching
        document_img_gray = cv2.cvtColor(document_img_cv, cv2.COLOR_BGR2GRAY)
        template_img = cv2.cvtColor(template_img_cv, cv2.COLOR_BGR2GRAY)
        
        template_h, template_w = template_img.shape[:2]
        document_h, document_w = document_img_gray.shape[:2]

        # --- NEW LOGIC: If template is still too big, resize it ---
        if template_h > document_h or template_w > document_w:
            st.warning("Template is larger than the document. Resizing template to fit...")
            # Calculate a new width that is 90% of the document's width
            new_w = int(document_w * 0.9)
            # Maintain aspect ratio
            ratio = new_w / template_w
            new_h = int(template_h * ratio)
            
            # Ensure the new height is also smaller
            if new_h > document_h * 0.9:
                new_h = int(document_h * 0.9)
                ratio = new_h / template_h
                new_w = int(template_w * ratio)

            template_img = cv2.resize(template_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            st.write(f"Template resized to {new_w}x{new_h} pixels.")

        # --- Proceed with template matching ---
        w, h = template_img.shape[::-1]
        res = cv2.matchTemplate(document_img_gray, template_img, cv2.TM_CCOEFF_NORMED)
        threshold = 0.7
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            st.success(f"Template matched with high confidence: {max_val:.2f}.")
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            cv2.rectangle(document_img_cv, top_left, bottom_right, (0, 255, 0), 3)
            st.image(cv2.cvtColor(document_img_cv, cv2.COLOR_BGR2RGB), caption="Matched Element")
        else:
            suspicion_points += 1
            st.warning(f"Template match confidence is low ({max_val:.2f}). Element may be forged or inconsistent.")
            
    except Exception as e:
        st.error(f"An unexpected error occurred during element verification: {e}")
        suspicion_points += 1
        
    return suspicion_points

def calculate_anomaly_score(scores_dict, threshold=2):
    """Calculates a final anomaly score and displays the verdict."""
    st.subheader("Final Verdict")
    total_score = sum(scores_dict.values())
    
    st.write(f"**Individual Scores:** `{scores_dict}`")
    st.write(f"**Total Anomaly Score:** `{total_score}`")

    if total_score >= threshold:
        st.error(f"DOCUMENT FAILED: Score ({total_score}) exceeds threshold ({threshold}). High probability of forgery. Escalating for human review.")
    else:
        st.success(f"DOCUMENT PASSED: Score ({total_score}) is within acceptable limits.")

# --- Streamlit App UI ---

st.set_page_config(layout="wide")
st.title("📄 Document Forgery Detection System")

# Create a temporary directory for file storage
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# UI layout
col1, col2 = st.columns(2)

with col1:
    st.info("Upload the document and a template element (e.g., a genuine seal or signature) to begin the analysis.")
    doc_uploaded = st.file_uploader("Upload Document (PDF)", type=["pdf"])
    template_uploaded = st.file_uploader("Upload Template Image (PNG, JPG)", type=["png", "jpg", "jpeg"])

if doc_uploaded and template_uploaded:
    doc_path = os.path.join(TEMP_DIR, doc_uploaded.name)
    template_path = os.path.join(TEMP_DIR, template_uploaded.name)
    
    # Save files
    save_uploaded_file(doc_uploaded, doc_path)
    save_uploaded_file(template_uploaded, template_path)

    if st.button("Start Analysis", type="primary"):
        with col2:
            st.header("Analysis Results")
            with st.spinner("Processing document... Please wait."):
                
                # 1. Convert PDF to Image
                image_path = os.path.join(TEMP_DIR, "page_0.png")
                ela_path = os.path.join(TEMP_DIR, "ela_result.png")
                
                if not pdf_to_image(doc_path, image_path):
                    st.stop() # Stop execution if conversion fails
                
                st.image(image_path, caption="First Page of Uploaded Document")

                # 2. Run all analysis modules
                scores = {}
                scores['metadata'] = analyze_metadata(image_path)
                scores['pixel_level'] = perform_error_level_analysis(image_path, ela_path)
                scores['element_verification'] = verify_document_elements(image_path, template_path)
                
                # 3. Calculate final score and make a decision
                calculate_anomaly_score(scores)