import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO

# Configuration
st.set_page_config(page_title="Analyse Électricité Lemba", layout="wide")

st.title("⚡ Analyse de Consommation d'Électricité - Lemba")

# Sidebar
st.sidebar.header("⚙️ Paramètres")
periode = st.sidebar.selectbox("Intervalle de temps", ["Horaire", "Quotidien", "Mensuel"])
secteurs = st.sidebar.multiselect("Secteurs", ["Centre-ville", "Résidentiel", "Commercial", "Industriel"], default=["Centre-ville"])

# Upload CSV
uploaded_file = st.sidebar.file_uploader("Charger un fichier CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
else:
    try:
        df = pd.read_csv("sample_data.csv")
        st.sidebar.info("📊 Utilisation des données d'exemple")
    except:
        st.error("Aucun fichier fourni")
        st.stop()

# Vérifier colonnes
required_cols = ["Date", "Heure", "Consommation(kWh)", "Secteur"]
if not all(col in df.columns for col in required_cols):
    st.error(f"Colonnes requises: {required_cols}")
    st.stop()

# Traiter données
df["Date"] = pd.to_datetime(df["Date"])
df["DateTime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Heure"].astype(str))

# Filtrer
df_filtered = df[df["Secteur"].isin(secteurs)]

# Agrégation
if periode == "Horaire":
    df_agg = df_filtered.sort_values("DateTime")
    time_col = "DateTime"
elif periode == "Quotidien":
    df_agg = df_filtered.groupby(df_filtered["Date"].dt.date).agg({"Consommation(kWh)": "sum", "Secteur": "first"}).reset_index()
    df_agg.columns = ["Date", "Consommation(kWh)", "Secteur"]
    time_col = "Date"
else:
    df_agg = df_filtered.groupby(df_filtered["Date"].dt.to_period("M")).agg({"Consommation(kWh)": "sum", "Secteur": "first"}).reset_index()
    df_agg.columns = ["Période", "Consommation(kWh)", "Secteur"]
    time_col = "Période"

# Onglets
tab1, tab2, tab3 = st.tabs(["📈 Graphiques", "📋 Données", "📄 Rapports"])

with tab1:
    st.subheader(f"📊 Consommation - {periode}")
    
    if len(df_agg) > 0:
        fig = px.line(df_agg, x=time_col, y="Consommation(kWh)", color="Secteur", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total (kWh)", f"{df_agg['Consommation(kWh)'].sum():.2f}")
        with col2:
            st.metric("Moyenne (kWh)", f"{df_agg['Consommation(kWh)'].mean():.2f}")
        with col3:
            st.metric("Max (kWh)", f"{df_agg['Consommation(kWh)'].max():.2f}")
        with col4:
            st.metric("Min (kWh)", f"{df_agg['Consommation(kWh)'].min():.2f}")

with tab2:
    st.subheader("📋 Données brutes")
    st.dataframe(df_agg, use_container_width=True)
    
    csv = df_agg.to_csv(index=False)
    st.download_button(label="📥 Télécharger CSV", data=csv, file_name=f"consommation_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

with tab3:
    st.subheader("📄 Rapport PDF")
    
    if st.button("Générer PDF"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        title = Paragraph("<b>Rapport d'Analyse - Consommation d'Électricité Lemba</b>", styles['Heading1'])
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        info = Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/><b>Période:</b> {periode}<br/><b>Total:</b> {df_agg['Consommation(kWh)'].sum():.2f} kWh", styles['Normal'])
        story.append(info)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        
        st.download_button(label="📥 PDF", data=pdf_bytes, file_name=f"rapport_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        st.success("✅ PDF généré!")

st.sidebar.markdown("---")
st.sidebar.markdown("⚡ Analyse consommation électrique - Lemba")
