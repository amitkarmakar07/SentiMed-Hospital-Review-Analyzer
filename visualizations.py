import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
from fpdf import FPDF

def create_bar_chart(aspect_df):
    df_plot = aspect_df.reset_index().melt(id_vars='index')
    df_plot.columns = ['Aspect', 'Sentiment', 'Count']
    return alt.Chart(df_plot).mark_bar().encode(
        x=alt.X('Aspect:N', title="Aspect", sort='-y'),
        y=alt.Y('Count:Q', title='Number of Reviews'),
        color=alt.Color('Sentiment:N', scale=alt.Scale(scheme='set1')),
        tooltip=["Aspect", "Sentiment", "Count"]
    ).properties(width=600, height=400)

def create_pie_chart(aspects):
    pie_data = Counter([a for a, _, _ in aspects])
    df_pie = pd.DataFrame({
        "aspect": list(pie_data.keys()),
        "count": list(pie_data.values())
    })
    base = alt.Chart(df_pie).encode(
        theta=alt.Theta("count:Q").stack(True),
        radius=alt.Radius("count:Q", scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
        color=alt.Color("aspect:N", legend=alt.Legend(title="Aspect"))
    )
    slices = base.mark_arc(innerRadius=20, stroke="#fff")
    labels = base.mark_text(radiusOffset=10).encode(text="count:Q")
    return slices + labels

def generate_wordcloud(text_blob):
    wc = WordCloud(width=800, height=400, background_color='white', colormap='plasma', max_words=200).generate(text_blob)
    return wc  # Return the WordCloud object directly for st.image

def generate_pdf_report(aspect_summary, aspects):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hospital Feedback Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt="Aspect-wise Sentiment Summary:", ln=True)
    for aspect, counts in aspect_summary.items():
        pdf.cell(200, 10, txt=f"{aspect.capitalize()} - Positive: {counts['Positive']}, Negative: {counts['Negative']}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Sample Comments:", ln=True)
    for a, s, line in aspects[:5]:
        pdf.multi_cell(0, 10, txt=f"[{a.capitalize()}] ({s}): {line.strip()}")
    return pdf.output(dest='S').encode('latin-1')