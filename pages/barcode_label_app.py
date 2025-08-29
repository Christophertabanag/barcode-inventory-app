import streamlit as st
import pandas as pd
import os
import barcode
from barcode.writer import ImageWriter
import io
import base64

INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "inventory.xlsx")

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_excel(INVENTORY_FILE)
    else:
        st.error("No inventory.xlsx found.")
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

def barcode_image_base64(code):
    CODE128 = barcode.get_barcode_class('code128')
    my_code = CODE128(str(code), writer=ImageWriter())
    buffer = io.BytesIO()
    my_code.write(buffer, options={"write_text": False})
    buffer.seek(0)
    img_bytes = buffer.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode()
    return img_b64

st.set_page_config(page_title="Barcode Label Printer", layout="wide")
st.title("Barcode Label Printer")

# Print CSS for label
st.markdown("""
<style>
.print-label-block {
    background: #fff;
    padding: 32px 16px;
    border-radius: 8px;
    width: 300px;
    margin: auto;
    box-shadow: 0px 0px 6px #eee;
}
@media print {
    body * { visibility: hidden !important; }
    .print-label-block, .print-label-block * { visibility: visible !important; }
    .print-label-block { position: absolute; left: 0; top: 0; width: 100%; }
    button, header, footer, .stAlert, .stMarkdown { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

df = load_inventory()

if len(df) == 0:
    st.info("No products found in inventory.")
else:
    product_options = df.apply(lambda row: f"{clean_barcode(row.get('BARCODE', ''))} - {row.get('MODEL', '')}", axis=1)
    selected_idx = st.selectbox(
        "Choose product",
        options=df.index.tolist(),
        format_func=lambda i: product_options[i]
    )
    product = df.loc[selected_idx]
    barcode_value = product.get("BARCODE", "")
    barcode_b64 = barcode_image_base64(barcode_value)
    rrp = str(product.get("RRP", ""))
    try:
        rrp_display = f"${float(rrp):.2f}"
    except:
        rrp_display = rrp
    framecode = str(product.get("FRAME NO.", ""))
    model = str(product.get("MODEL", ""))
    manufact = str(product.get("MANUFACTURER", ""))
    fcolour = str(product.get("F COLOUR", ""))
    size = str(product.get("SIZE", ""))

    # Print label block with all details
    st.markdown(f"""
<div class="print-label-block">
    <img src="data:image/png;base64,{barcode_b64}" width="220" />
    <div style="text-align:center;font-size:18px;margin-bottom:10px;">{clean_barcode(barcode_value)}</div>
    <div style="font-size:32px;font-weight:bold;text-align:center;">{rrp_display}</div>
    <div style="text-align:center;font-size:18px;margin-bottom:10px;">Inc GST</div>
    <div style="font-size:18px;margin-top:10px;margin-bottom:0;text-align:left;line-height:1.3;">
        Framecode: {framecode}<br>
        Model: {model}<br>
        Manufacturer: {manufact}<br>
        Frame Colour: {fcolour}<br>
        Size: {size}
    </div>
</div>
""", unsafe_allow_html=True)

    # Print button
    st.markdown("""
    <button onclick="window.print()" style="font-size:18px;margin:16px 0;">Print Label</button>
    """, unsafe_allow_html=True)

st.markdown("---")
st.write("For best results, use landscape mode and set margins to minimum when printing.")

with st.expander("Show inventory table"):
    st.dataframe(df, use_container_width=True)
