# Title: Main Inventory

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import random
import uuid
import barcode
from barcode.writer import ImageWriter
import io

INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "inventory.xlsx")
st.set_page_config(page_title="Inventory Manager", layout="wide")

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        df = pd.read_excel(INVENTORY_FILE)
        return df
    else:
        st.error("Inventory file not found. Please place 'inventory.xlsx' in the app directory.")
        st.stop()

def clean_barcode(val):
    if pd.isnull(val):
        return ""
    s = str(val).strip().replace('\u200b','').replace('\u00A0','')
    if '.' in s:
        int_part, dec_part = s.split('.', 1)
        if dec_part == '0':
            s = int_part
    return s

def generate_unique_barcode(df):
    while True:
        barcode_val = str(random.randint(1, 11000))
        if clean_barcode(barcode_val) not in df["BARCODE"].map(clean_barcode).values:
            return barcode_val

def generate_unique_framecode(df):
    while True:
        framecode_val = "FRM" + uuid.uuid4().hex[-8:].upper()
        if clean_barcode(framecode_val) not in df["FRAME NO."].map(clean_barcode).values:
            return framecode_val

def generate_barcode_image(code):
    try:
        CODE128 = barcode.get_barcode_class('code128')
        code = str(code)
        if not code:
            st.error("Barcode value cannot be empty.")
            return None
        my_code = CODE128(code, writer=ImageWriter())
        buffer = io.BytesIO()
        my_code.write(buffer, options={"write_text": False})
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error generating barcode image: {e}")
        return None

def get_smart_default(header, df):
    if header in df.columns and not df[header].dropna().empty:
        recent = df[header].dropna().iloc[-1]
        if recent: return str(recent)
    if header in df.columns and not df[header].dropna().empty:
        most_common = df[header].dropna().mode()
        if not most_common.empty: return str(most_common.iloc[0])
    if header == "MANUFACT":
        return "Ray-Ban"
    if header == "SUPPLIER":
        return "Default Supplier"
    if header == "FRAMETYPE":
        return "Full Rim"
    if header == "RRP":
        return "120.00"
    if header == "EXCOSTPRICE":
        return "60.00"
    if header == "COSTPRICE":
        return "70.00"
    if header == "TAXPC":
        return "12"
    if header == "AVAILFROM":
        return datetime.now().strftime("%Y-%m-%d")
    if header == "FRSTATUS":
        return "Active"
    if header == "NOTE":
        return ""
    return ""

st.markdown("""
    <style>
    div[data-testid="column"] {
        padding-right: 4px !important;
        padding-left: 0px !important;
        margin: 0 !important;
    }
    .compact-form input, .compact-form select, .compact-form textarea {
        font-size: 11px !important;
        height: 22px !important;
        padding: 1px 4px !important;
        margin-bottom: 0px !important;
        margin-top: 0px !important;
    }
    .compact-form label {
        font-size: 11px !important;
        margin-bottom: 0px !important;
        margin-top: 0px !important;
    }
    .stForm {
        padding-top: 0;
        padding-bottom: 0;
        margin-top: 0;
        margin-bottom: 0;
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    div[data-testid="stForm"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

if "add_product_expanded" not in st.session_state:
    st.session_state["add_product_expanded"] = False
if "barcode" not in st.session_state:
    st.session_state["barcode"] = ""
if "framecode" not in st.session_state:
    st.session_state["framecode"] = ""
if "edit_product_index" not in st.session_state:
    st.session_state["edit_product_index"] = None
if "edit_delete_expanded" not in st.session_state:
    st.session_state["edit_delete_expanded"] = False
if "pending_delete_index" not in st.session_state:
    st.session_state["pending_delete_index"] = None
if "pending_delete_confirmed" not in st.session_state:
    st.session_state["pending_delete_confirmed"] = False

df = load_inventory()
columns = list(df.columns)
barcode_col = "BARCODE"
framecode_col = "FRAME NO."

if barcode_col not in columns or framecode_col not in columns:
    st.error(f"Couldn't find '{barcode_col}' or '{framecode_col}' columns in your inventory file.")
    st.write("Found columns:", columns)
    st.stop()

headers = [h for h in columns if h.lower() != "timestamp"]

st.title("Inventory Manager")

# Add icon/button to go to Barcode Label Printer (same multipage app)
if st.button("🏷️ Go to Barcode Label Printer"):
    st.switch_page("pages/barcode_label_app.py")

st.markdown("#### Generate Unique Barcodes")
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("Generate Barcode"):
        st.session_state["barcode"] = generate_unique_barcode(df)
        st.session_state["add_product_expanded"] = True
with btn_col2:
    if st.button("Generate Framecode"):
        st.session_state["framecode"] = generate_unique_framecode(df)
        st.session_state["add_product_expanded"] = True

if st.session_state["barcode"]:
    st.markdown("#### Barcode Image")
    img_buffer = generate_barcode_image(st.session_state["barcode"])
    if img_buffer:
        st.image(img_buffer, width=220)

with st.expander("➕ Add a New Product", expanded=st.session_state["add_product_expanded"]):
    input_values = {}
    n_cols = 3
    header_rows = [headers[i:i+n_cols] for i in range(0, len(headers), n_cols)]
    st.markdown("**Enter New Product Details:**")
    for row in header_rows:
        cols = st.columns(len(row), gap="small")
        for idx, header in enumerate(row):
            with cols[idx]:
                st.markdown('<div class="compact-form">', unsafe_allow_html=True)
                unique_key = f"textinput_{header}"
                smart_suggestion = get_smart_default(header, df)
                if header == barcode_col:
                    input_values[header] = st.text_input(header, value=st.session_state["barcode"], key=unique_key)
                elif header == framecode_col:
                    input_values[header] = st.text_input(header, value=st.session_state["framecode"], key=unique_key)
                elif header.lower() == "quantity":
                    try:
                        default_qty = int(smart_suggestion) if smart_suggestion.isdigit() else 1
                    except:
                        default_qty = 1
                    input_values[header] = st.number_input(header, min_value=0, value=default_qty, key=unique_key)
                else:
                    options_from_inventory = sorted([str(opt) for opt in df[header].dropna().unique() if str(opt).strip() != ""])
                    options = []
                    if smart_suggestion and smart_suggestion not in options_from_inventory:
                        options = [smart_suggestion] + options_from_inventory
                    else:
                        options = options_from_inventory
                    options = [""] + options if options else ["", smart_suggestion] if smart_suggestion else ["", "Option 1", "Option 2", "Option 3"]
                    index_to_select = options.index(smart_suggestion) if smart_suggestion in options else 0
                    input_values[header] = st.selectbox(header, options, index=index_to_select, key=unique_key)
                st.markdown('</div>', unsafe_allow_html=True)

    with st.form(key="add_product_form"):
        st.markdown("Click 'Add Product' to submit the details above.")
        submit = st.form_submit_button("Add Product")
        if submit:
            required_fields = [barcode_col, framecode_col]
            missing = [field for field in required_fields if field in headers and not input_values.get(field)]
            barcode_cleaned = clean_barcode(input_values[barcode_col])
            framecode_cleaned = clean_barcode(input_values[framecode_col])
            df_barcodes_cleaned = df[barcode_col].map(clean_barcode)
            df_framecodes_cleaned = df[framecode_col].map(clean_barcode)
            if missing:
                st.warning(f"{', '.join(missing)} are required.")
            elif barcode_cleaned in df_barcodes_cleaned.values:
                st.error("This barcode already exists in inventory!")
            elif framecode_cleaned in df_framecodes_cleaned.values:
                st.error("This framecode already exists in inventory!")
            else:
                new_row = {h: input_values.get(h, "") for h in headers}
                if "Timestamp" in df.columns:
                    new_row["Timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_excel(INVENTORY_FILE, index=False)
                st.success(f"Product added successfully!")
                st.session_state["barcode"] = ""
                st.session_state["framecode"] = ""
                st.session_state["add_product_expanded"] = False
                st.rerun()

st.markdown('### Current Inventory')

with st.expander("✏️ Edit or 🗑 Delete Products", expanded=st.session_state["edit_delete_expanded"]):
    if len(df) > 0:
        selected_row = st.selectbox(
            "Select a product to edit or delete",
            options=df.index.tolist(),
            format_func=lambda i: f"{clean_barcode(df.at[i, barcode_col])} - {clean_barcode(df.at[i, framecode_col])}",
            key="selected_product"
        )
        if selected_row is not None:
            st.session_state["edit_product_index"] = selected_row
            product = df.loc[selected_row]
            edit_values = {}
            n_cols = 3
            header_rows = [headers[i:i+n_cols] for i in range(0, len(headers), n_cols)]
            st.markdown("**Edit Product Details**")
            for row in header_rows:
                cols = st.columns(len(row), gap="small")
                for idx, header in enumerate(row):
                    with cols[idx]:
                        st.markdown('<div class="compact-form">', unsafe_allow_html=True)
                        value = product[header] if header in product else ""
                        show_value = clean_barcode(value) if header in [barcode_col, framecode_col] else value
                        unique_key = f"edit_textinput_{header}_{selected_row}"
                        smart_suggestion = get_smart_default(header, df)
                        if header == barcode_col or header == framecode_col:
                            edit_values[header] = st.text_input(header, value=str(show_value), key=unique_key)
                        elif header.lower() == "quantity":
                            try:
                                default_qty = int(smart_suggestion) if smart_suggestion.isdigit() else 1
                            except:
                                default_qty = 1
                            edit_values[header] = st.number_input(header, min_value=0, value=int(value) if str(value).isdigit() else default_qty, key=unique_key)
                        else:
                            options_from_inventory = sorted([str(opt) for opt in df[header].dropna().unique() if str(opt).strip() != ""])
                            options = []
                            if smart_suggestion and smart_suggestion not in options_from_inventory:
                                options = [smart_suggestion] + options_from_inventory
                            else:
                                options = options_from_inventory
                            options = [""] + options if options else ["", smart_suggestion] if smart_suggestion else ["", "Option 1", "Option 2", "Option 3"]
                            index_to_select = options.index(str(value)) if str(value) in options else 0
                            edit_values[header] = st.selectbox(header, options, index=index_to_select, key=unique_key)
                        st.markdown('</div>', unsafe_allow_html=True)
            with st.form(key=f"edit_form_{selected_row}"):
                col1, col2 = st.columns(2)
                submit_edit = col1.form_submit_button("Save Changes")
                submit_delete = col2.form_submit_button("Delete Product")
                if submit_edit:
                    edit_barcode_cleaned = clean_barcode(edit_values[barcode_col])
                    edit_framecode_cleaned = clean_barcode(edit_values[framecode_col])
                    df_barcodes_cleaned = df[barcode_col].map(clean_barcode)
                    df_framecodes_cleaned = df[framecode_col].map(clean_barcode)
                    duplicate_barcode = (df_barcodes_cleaned == edit_barcode_cleaned) & (df.index != selected_row)
                    duplicate_framecode = (df_framecodes_cleaned == edit_framecode_cleaned) & (df.index != selected_row)
                    if duplicate_barcode.any():
                        st.error("Another product with this barcode already exists!")
                    elif duplicate_framecode.any():
                        st.error("Another product with this framecode already exists!")
                    else:
                        for h in headers:
                            df.at[selected_row, h] = edit_values.get(h, "")
                        if "Timestamp" in df.columns:
                            df.at[selected_row, "Timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        df.to_excel(INVENTORY_FILE, index=False)
                        st.success("Product updated successfully!")
                        st.session_state["edit_delete_expanded"] = True
                        st.rerun()
                if submit_delete:
                    st.session_state["pending_delete_index"] = selected_row

    else:
        st.info("No products in inventory yet.")

if st.session_state.get("pending_delete_index") is not None:
    st.warning(f"Are you sure you want to delete product with barcode '{clean_barcode(df.at[st.session_state['pending_delete_index'], barcode_col])}' and framecode '{clean_barcode(df.at[st.session_state['pending_delete_index'], framecode_col])}'?")
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Confirm Delete", key="confirm_delete_btn"):
            df = df.drop(st.session_state["pending_delete_index"]).reset_index(drop=True)
            df.to_excel(INVENTORY_FILE, index=False)
            st.success("Product deleted successfully!")
            st.session_state["edit_product_index"] = None
            st.session_state["edit_delete_expanded"] = True
            st.session_state["pending_delete_index"] = None
            st.rerun()
    with cancel_col:
        if st.button("Cancel", key="cancel_delete_btn"):
            st.session_state["pending_delete_index"] = None

st.dataframe(df, use_container_width=True)

with st.expander("📦 Stock Count"):
    st.write("Upload a file (CSV, Excel, or TXT) of scanned barcodes from your stock count.")
    uploaded_file = st.file_uploader("Upload scanned barcodes", type=["csv", "xlsx", "txt"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                scanned_df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                scanned_df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith(".txt"):
                scanned_df = pd.read_csv(uploaded_file)
            else:
                st.error("Unsupported file type.")
                scanned_df = None
        except Exception as e:
            st.error(f"Error reading file: {e}")
            scanned_df = None
        if scanned_df is not None:
            barcode_column = st.selectbox(
                "Select the column containing barcodes", scanned_df.columns.tolist()
            )
            inventory_barcodes = set(df[barcode_col].map(clean_barcode))
            scanned_barcodes = set(scanned_df[barcode_column].map(clean_barcode))
            matched = inventory_barcodes & scanned_barcodes
            missing = inventory_barcodes - scanned_barcodes
            unexpected = scanned_barcodes - inventory_barcodes
            st.success(f"Matched items: {len(matched)}")
            st.warning(f"Missing items: {len(missing)}")
            st.error(f"Unexpected items: {len(unexpected)}")
            if matched:
                st.write("✅ Present items:")
                st.dataframe(df[df[barcode_col].map(clean_barcode).isin(matched)])
            if missing:
                st.write("❌ Missing items:")
                st.dataframe(df[df[barcode_col].map(clean_barcode).isin(missing)])
            if unexpected:
                st.write("⚠️ Unexpected items (not in system):")
                st.write(list(unexpected))

with st.expander("🔍 Quick Stock Check (Scan Barcode)"):
    st.write("Place your cursor below, scan a barcode, and instantly see product details!")
    scanned_barcode = st.text_input("Scan Barcode", value="", key="stock_check_barcode_input")
    if scanned_barcode:
        cleaned_input = clean_barcode(scanned_barcode)
        matches = df[df[barcode_col].map(clean_barcode) == cleaned_input]
        if not matches.empty:
            st.success("Product found:")
            st.dataframe(matches)
            product = matches.iloc[0]

            barcode_value = product[barcode_col]
            barcode_img_buffer = generate_barcode_image(barcode_value)
            rrp = str(product.get("RRP", ""))
            if not rrp:
                rrp = "0"
            try:
                rrp_float = float(rrp)
                rrp_display = f"${rrp_float:.2f}"
            except:
                rrp_display = f"${rrp}.00"
            framecode = str(product.get("FRAME NO.", ""))
            model = str(product.get("MODEL", ""))
            manufact = str(product.get("MANUFACTURER", ""))
            fcolour = str(product.get("F COLOUR", ""))
            size = str(product.get("SIZE", ""))

            st.markdown('<div class="print-label-block">', unsafe_allow_html=True)
            if barcode_img_buffer:
                st.image(barcode_img_buffer, width=220)
            st.markdown(f'<div class="print-label-barcode-num">{clean_barcode(barcode_value)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="print-label-price">{rrp_display}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="print-label-gst">Inc GST</div>', unsafe_allow_html=True)
            st.markdown('<div class="print-label-details">', unsafe_allow_html=True)
            st.markdown(f'Framecode: {framecode}', unsafe_allow_html=True)
            st.markdown(f'Model: {model}', unsafe_allow_html=True)
            st.markdown(f'Manufacturer: {manufact}', unsafe_allow_html=True)
            st.markdown(f'Frame Colour: {fcolour}', unsafe_allow_html=True)
            st.markdown(f'Size: {size}', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)
        else:
            st.error("Barcode not found in inventory.")
