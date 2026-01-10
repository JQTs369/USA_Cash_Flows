import streamlit as st

# Page Config
st.set_page_config(page_title="Trauma Kit Checklist", page_icon="🚑")

st.title("Vehicle First Aid: Gunshot & Trauma Response Supplies")

# Disclaimer Expander
with st.expander("⚠️ Important Disclaimer"):
    st.write("""
    This is not medical advice. Please do your own research. 
    This is simply a list of items to consider and a video overview of how to use them. 
    No affiliation links are provided; these are just items I have purchased.
    """)

st.divider()

# The Action Section
st.subheader("Inventory Checklist")
st.write("Access the full Excel inventory and supplies list below:")

# Replace 'your_link_here' with your actual Google Sheets or Dropbox/Drive link
st.link_button("📥 Download/View Excel Sheet", "https://docs.google.com/spreadsheets/d/12ArmTNq-ifwUb_cfFn5CV9lnE9YCthL0kBbxrRugb7M/edit?usp=sharing", use_container_width=True)

st.divider()

# Video Section
st.subheader("Tutorial & Overview")
# Replace with the actual TikTok or YouTube URL
st.video("https://www.tiktok.com/@scotty.k.fitness/video/7593404458827107614")

st.info("Ensure you are trained in 'Stop the Bleed' protocols before attempting to use these items.")