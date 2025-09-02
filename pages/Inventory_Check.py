import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Paths for files
MAIN_INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "inventory.xlsx")
SECONDARY_INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "secondary_inventory.xlsx")
UNFOUND_BARCODES_FILE = os.path.join(os.path.dirname(__file__), "unfound_barcodes.xlsx")

def clean_barcode(val):
    """Standardize barcodes for comparison."""
    if pd.isnull(val):
        return ""
    s = str(val).strip().replace('\u200b','').replace('\u00A0','')
    if '.' in s:
        int_part, dec_part = s.split('.', 1)
        if dec_part == '0':
            s = int_part
    return s

# Load main inventory
def load_inventory():
    if os.path.exists(MAIN_INVENTORY_FILE):
        df = pd.read_excel(MAIN_INVENTORY_FILE)
        return df
    else:
        st.error("Main inventory file not found.")
        st.stop()

# Load secondary inventory
def load_secondary_inventory():
    if os.path.exists(SECONDARY_INVENTORY_FILE):
        df = pd.read_excel(SECONDARY_INVENTORY_FILE)
        return df
    else:
        return pd.DataFrame(columns=["BARCODE", "Timestamp"])

# Load unfound barcodes
def load_unfound_barcodes():
    if os.path.exists(UNFOUND_BARCODES_FILE):
        df = pd.read_excel(UNFOUND_BARCODES_FILE)
        return df
    else:
        return pd.DataFrame(columns=["BARCODE", "Timestamp"])

def add_to_secondary(barcode, secondary_df):
    cleaned = clean_barcode(barcode)
    if cleaned not in secondary_df["BARCODE"].astype(str).map(clean_barcode).values:
        new_row = {"BARCODE": cleaned, "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        secondary_df = pd.concat([secondary_df, pd.DataFrame([new_row])], ignore_index=True)
        secondary_df.to_excel(SECONDARY_INVENTORY_FILE, index=False)
    return secondary_df

def add_to_unfound(barcode, unfound_df):
    cleaned = clean_barcode(barcode)
    if cleaned not in unfound_df["BARCODE"].astype(str).map(clean_barcode).values:
        new_row = {"BARCODE": cleaned, "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        unfound_df = pd.concat([unfound_df, pd.DataFrame([new_row])], ignore_index=True)
        unfound_df.to_excel(UNFOUND_BARCODES_FILE, index=False)
    return unfound_df

st.set_page_config(page_title="Inventory Check", layout="wide")
st.title("🔎 Inventory Check")

main_df = load_inventory()
secondary_df = load_secondary_inventory()
unfound_df = load_unfound_barcodes()

barcode_col = "BARCODE" if "BARCODE" in main_df.columns else main_df.columns[0]

st.markdown("### Scan or Enter Barcode")

scanned_barcode = st.text_input("Scan Barcode for Inventory Check", key="scan_barcode")
if scanned_barcode:
    cleaned = clean_barcode(scanned_barcode)
    matches = main_df[main_df[barcode_col].map(clean_barcode) == cleaned]
    if not matches.empty:
        st.success("✅ Product found in main inventory!")
        st.dataframe(matches)
        # Option to add to secondary inventory
        if st.button("Add Product to Secondary Inventory"):
            secondary_df = add_to_secondary(cleaned, secondary_df)
            st.success(f"Product {cleaned} added to secondary inventory.")
            st.dataframe(secondary_df)
    else:
        st.error("❌ Product not found in main inventory.")
        # Option to add to unfound barcodes
        if st.button("Add Barcode to Unfound List"):
            unfound_df = add_to_unfound(cleaned, unfound_df)
            st.success(f"Barcode {cleaned} added to unfound barcodes list.")
            st.dataframe(unfound_df)

st.markdown("### Secondary Inventory Preview")
st.dataframe(secondary_df)

st.markdown("### Unfound Barcodes List")
st.dataframe(unfound_df)
