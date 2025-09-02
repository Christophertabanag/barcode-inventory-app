import streamlit as st
import pandas as pd
import os

MAIN_INVENTORY = os.path.join(os.path.dirname(__file__), "..", "inventory.xlsx")
SECONDARY_INVENTORY = os.path.join(os.path.dirname(__file__), "..", "secondary_inventory.xlsx")

def clean_barcode(val):
    if pd.isnull(val):
        return ""
    s = str(val).strip().replace('\u200b','').replace('\u00A0','')
    if '.' in s:
        int_part, dec_part = s.split('.', 1)
        if dec_part == '0':
            s = int_part
    return s

def ensure_secondary_inventory(main_file, secondary_file):
    main_df = pd.read_excel(main_file)
    # Create secondary inventory file if it doesn't exist, with same columns as main inventory
    if not os.path.exists(secondary_file):
        empty_df = pd.DataFrame(columns=main_df.columns)
        empty_df.to_excel(secondary_file, index=False)
    # Always reload after the creation step
    secondary_df = pd.read_excel(secondary_file)
    return main_df, secondary_df

st.title("Inventory Check / Product Transfer")

main_df, secondary_df = ensure_secondary_inventory(MAIN_INVENTORY, SECONDARY_INVENTORY)

search_barcode = st.text_input("Scan or enter barcode")
search_barcode_clean = clean_barcode(search_barcode)

main_df["BARCODE_CLEAN"] = main_df["BARCODE"].apply(clean_barcode)
result = main_df[main_df["BARCODE_CLEAN"] == search_barcode_clean]
product_row = result.iloc[0] if not result.empty else None

if search_barcode:
    if not result.empty:
        st.success("Product found!")
        st.write("**Product Details:**")
        st.write(result.drop(columns=["BARCODE_CLEAN"], errors="ignore"))
    else:
        st.warning("Product not found in main inventory.")

if product_row is not None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Product to Secondary Inventory"):
            secondary_df["BARCODE_CLEAN"] = secondary_df["BARCODE"].apply(clean_barcode)
            if not secondary_df[secondary_df["BARCODE_CLEAN"] == search_barcode_clean].empty:
                st.warning("Product already exists in secondary inventory!")
            else:
                # Prepend the new product
                secondary_df = pd.concat([result.drop(columns=["BARCODE_CLEAN"], errors="ignore"), secondary_df], ignore_index=True)
                secondary_df.to_excel(SECONDARY_INVENTORY, index=False)
                st.success("Product added to secondary inventory!")
    with col2:
        if st.button("Remove Product from Secondary Inventory"):
            secondary_df["BARCODE_CLEAN"] = secondary_df["BARCODE"].apply(clean_barcode)
            secondary_df = secondary_df[secondary_df["BARCODE_CLEAN"] != search_barcode_clean]
            secondary_df.to_excel(SECONDARY_INVENTORY, index=False)
            st.success("Product removed from secondary inventory!")

st.markdown("---")
st.subheader("Secondary Inventory Preview")
st.dataframe(secondary_df.drop(columns=["BARCODE_CLEAN"], errors="ignore"), use_container_width=True)
