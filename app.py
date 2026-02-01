import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Novità Libri", layout="wide")
st.title("📚 Novità Saggistica")

# --- CARICAMENTO DATI (DAL CSV) ---
# Il CSV è molto più affidabile per le App rispetto all'Excel con immagini
file_name = "dati_per_app.csv"

if not os.path.exists(file_name):
    st.error(f"⚠️ File '{file_name}' non trovato! Esegui prima lo script di scraping aggiornato.")
    st.stop()

try:
    df = pd.read_csv(file_name)
except Exception as e:
    st.error(f"Errore lettura CSV: {e}")
    st.stop()

# --- SIDEBAR FILTRI ---
st.sidebar.header("Filtri")

# Filtro Editore
if 'Editore' in df.columns:
    # dropna() rimuove i vuoti, astype(str) assicura che siano stringhe
    editori = sorted(df['Editore'].dropna().astype(str).unique())
    sel_editore = st.sidebar.multiselect("Editore", editori)
    if sel_editore:
        df = df[df['Editore'].isin(sel_editore)]

# Filtro Testo
search = st.sidebar.text_input("Cerca libro o autore")
if search:
    # Cerca in tutte le colonne testuali
    mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
    df = df[mask]

# --- VISUALIZZAZIONE ---
st.write(f"Trovati {len(df)} libri.")

for _, row in df.iterrows():
    with st.container():
        c1, c2 = st.columns([1, 4])
        
        with c1:
            # Nel CSV il link è testo puro, quindi lo legge sicuro
            url = row['Copertina']
            # Controllo base se è un url valido
            if pd.notna(url) and str(url).startswith('http'):
                st.image(str(url), width=110)
            else:
                st.write("🖼️ No Img")
        
        with c2:
            st.subheader(row['Titolo'])
            st.markdown(f"**{row.get('Autore', 'N/D')}** | {row.get('Editore', 'N/D')} ({row.get('Anno', '')})")
            
            desc = str(row.get('Descrizione', ''))
            if len(desc) > 5 and desc != "nan":
                with st.expander("Leggi trama"):
                    st.write(desc)
            
            link = row.get('Link')
            if pd.notna(link) and str(link).startswith('http'):
                st.markdown(f"[➡️ Vedi su IBS]({link})")
        
        st.divider()
