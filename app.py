import streamlit as st
import pandas as pd
from model_utils import load_model, predict, sentiment_map, aspect_map
from geo_utils import get_coordinates, fetch_hospitals, get_google_distance
from review_analysis import analyze_reviews, score_hospital
from visualizations import create_bar_chart, create_pie_chart, generate_wordcloud, generate_pdf_report
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from streamlit_js_eval import get_geolocation

# Streamlit app starts here
st.title("🏥 SentiMed : Aspect-Based Hospital Review Analyzer")

# Sidebar with option_menu
with st.sidebar:
    selected = option_menu(
        menu_title="Choose Mode",
        options=["Location-Based Search", "Upload CSV Feedback"],
        icons=["geo-alt-fill", "file-earmark-arrow-up"],
        menu_icon="hospital",
        default_index=0,
        styles={
            "container": {
                "background-color": "#ff0000",  
                "padding": "10px",
                "border-radius": "10px"
            },
            "menu-title": {
                "color": "white",
                "font-size": "20px",
                "font-weight": "bold",
                "text-align": "center",
                "margin-bottom": "15px"
            },
            "nav-link": {
                "font-size": "18px",
                "color": "white",
                "background-color": "#cc0000",  
                "padding": "10px",
                "border-radius": "5px",
                "margin": "5px 0",
                "text-align": "left",
                "--hover-color": "#e60000"  
            },
            "nav-link-selected": {
                "background-color": "#990000",  
                "color": "white",
                "font-weight": "bold"
            },
            "icon": {
                "color": "white",
                "font-size": "18px"
            }
        }
    )

if selected == "Location-Based Search":
    st.subheader("📍 Give Location Input")
    use_auto = st.checkbox("Use my current location (auto-detect)")
    lat, lon = None, None

    if use_auto:
        loc = get_geolocation()
        if loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            st.success(f"Detected Location: {lat:.4f}, {lon:.4f}")
    else:
        location_input = st.text_input("Enter your location : ")
        if location_input:
            lat, lon = get_coordinates(location_input)
            if lat and lon:
                st.success(f"Location set to: {lat:.4f}, {lon:.4f}")

    if lat and lon:
        hospitals = fetch_hospitals(lat, lon)[:10]  
        st.map(pd.DataFrame([{"lat": h["lat"], "lon": h["lon"]} for h in hospitals[:10]]))  

        valid_hospitals = []
        for h in hospitals[:10]:  
            try:
                aspects, sentiment_count = analyze_reviews(h["reviews"])
                h["positive_ratio"] = sentiment_count["Positive"] / (sentiment_count["Positive"] + sentiment_count["Negative"] + 1e-5)
                h["aspect_summary"] = {a: {"Positive": sum(1 for x, s, _ in aspects if x == a and s == "Positive"),
                                      "Negative": sum(1 for x, s, _ in aspects if x == a and s == "Negative")}
                                      for a in set(x for x, _, _ in aspects)}
                h["aspects"] = aspects
                valid_hospitals.append(h)

                st.markdown(f"### 🏥 {h['name']}")
                st.write(
                    f"⭐ Rating: {h['rating']}, 📝 Total Reviews: {h['total_reviews']}, 😊 Positive Ratio: {h['positive_ratio']:.2%}, 🚗 Distance: {h['distance_text']}"
                )

                aspect_df = pd.DataFrame(h['aspect_summary']).T.fillna(0).astype(int)
                if not aspect_df.empty:
                    st.subheader("📊 Sentiment Distribution by Aspect")
                    st.altair_chart(create_bar_chart(aspect_df), use_container_width=True)

                text_blob = " ".join([line for _, _, line in h['aspects']])
                if text_blob.strip():
                    wc = generate_wordcloud(text_blob)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)

                shown = set()
                st.subheader("📝 Sample Reviews by Aspect")
                for asp, sent, line in h['aspects']:
                    if asp not in shown:
                        st.markdown(f"**{asp.capitalize()}**")
                        for s, l in [(sent, l) for a, s, l in h['aspects'] if a == asp][:2]:
                            st.write(f"- ({s}) {l.strip()}")
                        shown.add(asp)
            except Exception as e:
                st.warning(f" Skipping hospital due to error: {str(e)}")
                continue

        st.subheader("🏥 Recommended Hospitals")
        if valid_hospitals:
            top_hospitals = sorted(valid_hospitals, key=score_hospital, reverse=True)[:5]  
            for h in top_hospitals:
                score = score_hospital(h)
                st.success(f"{h['name']} (Score: {score:.2f})")
        else:
            st.warning("No valid hospitals to recommend based on available review data.")

elif selected == "Upload CSV Feedback":
    st.subheader("Upload Feedback CSV (with 'review' column)")
    uploaded = st.file_uploader("Upload CSV", type=['csv'])

    if uploaded:
        df = pd.read_csv(uploaded)
        if "review" not in df.columns:
            st.error("CSV must contain a 'review' column")
        else:
            aspects, sentiment_count = analyze_reviews(df['review'].dropna().tolist(), include_general=True)

            aspect_summary = {a: {"Positive": sum(1 for x, s, _ in aspects if x == a and s == "Positive"), 
                                 "Negative": sum(1 for x, s, _ in aspects if x == a and s == "Negative")} 
                             for a in set(x for x, _, _ in aspects)}

            aspect_df = pd.DataFrame(aspect_summary).T.fillna(0).astype(int)
            st.subheader("📊 Sentiment Distribution by Aspect")
            st.altair_chart(create_bar_chart(aspect_df), use_container_width=True)

            st.subheader("🥧 Aspect Frequency Pie Chart")
            st.altair_chart(create_pie_chart(aspects), use_container_width=True)

            text_blob = " ".join([line for _, _, line in aspects])
            if text_blob.strip():
                st.image(generate_wordcloud(text_blob).to_array(), caption="WordCloud of Reviews", use_container_width=True)

            st.download_button(
                label="📄 Download PDF Report",
                data=generate_pdf_report(aspect_summary, aspects),
                file_name="hospital_feedback.pdf",
                mime="application/pdf"
            )

