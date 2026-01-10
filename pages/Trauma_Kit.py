import streamlit as st
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="Trauma Kit Checklist", page_icon="🚑", layout="centered")

# 2. Professional Title
st.title("Vehicle First Aid: Gunshot & Trauma Response Supplies")

# 3. Disclaimer Expander
with st.expander("⚠️ Important Disclaimer"):
    st.write("""
    This is not medical advice. Please do your own research; this is just a list of items to consider. 
    Below is a video overview from another creator on how to use these tools. 
    No affiliation links are provided; these are just items I have purchased for my own kit.
    """)

st.divider()

# 4. The Excel Link (Optimized for Mobile)
st.subheader("Inventory Checklist")
st.write("Access the full Excel inventory and supplies list below:")

st.link_button(
    "📂 View Excel Inventory List",
    "https://docs.google.com/spreadsheets/d/12ArmTNq-ifwUb_cfFn5CV9lnE9YCthL0kBbxrRugb7M/edit?usp=sharing",
    use_container_width=True
)

st.divider()

# 5. TikTok Embed
st.subheader("How to Use These Items")

tiktok_embed_code = """
<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@scotty.k.fitness/video/7593404458827107614" data-video-id="7593404458827107614" style="max-width: 605px;min-width: 325px;" > 
    <section> 
        <a target="_blank" title="@scotty.k.fitness" href="https://www.tiktok.com/@scotty.k.fitness?refer=embed">@scotty.k.fitness</a> Just in case 💙 
        <a title="help" target="_blank" href="https://www.tiktok.com/tag/help?refer=embed">#help</a> 
        <a title="trauma" target="_blank" href="https://www.tiktok.com/tag/trauma?refer=embed">#trauma</a> 
        <a title="medicine" target="_blank" href="https://www.tiktok.com/tag/medicine?refer=embed">#medicine</a> 
        <a title="emt" target="_blank" href="https://www.tiktok.com/tag/emt?refer=embed">#emt</a> 
        <a title="firstaid" target="_blank" href="https://www.tiktok.com/tag/firstaid?refer=embed">#firstaid</a> 
        <a target="_blank" title="♬ original sound scottykfitness" href="https://www.tiktok.com/music/original-sound-scottykfitness-0?refer=embed">♬ original sound scottykfitness</a> 
    </section> 
</blockquote> 
<script async src="https://www.tiktok.com/embed.js"></script>
"""

# make component bigger and allow scrolling for phones
components.html(tiktok_embed_code, height=800, scrolling=True)

st.info("Tip: If the video above doesn't load, ensure your browser isn't blocking scripts.")