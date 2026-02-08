import streamlit as st
import pandas as pd
import os

# Configurazione Pagina
st.set_page_config(page_title="Novità Libri", page_icon="📚", layout="wide")
st.title("📚 Novità Saggistica")

# --- CARICAMENTO DATI ---
file_name = "dati_per_app.csv"

if not os.path.exists(file_name):
    st.error(f"⚠️ File '{file_name}' non trovato! Esegui prima lo script di scraping.")
    st.stop()

try:
    df = pd.read_csv(file_name)
    # Assicuriamoci che non ci siano valori nulli nei campi chiave per evitare crash
    df['Titolo'] = df['Titolo'].fillna("Senza Titolo")
    df['Editore'] = df['Editore'].fillna("N/D")
except Exception as e:
    st.error(f"Errore lettura CSV: {e}")
    st.stop()

# --- SEPARAZIONE DATI ---
# Creiamo due dataset separati in base alla categoria assegnata dallo scraper
df_vip = df[df['Categoria_App'] == 'Editori Selezionati'].copy()
df_altri = df[df['Categoria_App'] != 'Editori Selezionati'].copy()

# --- SIDEBAR: FILTRI E ORDINAMENTO (Solo per VIP) ---
st.sidebar.header("🛠️ Strumenti")

# 1. BARRA DI RICERCA (Globale)
search_query = st.sidebar.text_input("🔍 Cerca libro o autore", help="Cerca in entrambe le liste")

# 2. FILTRO EDITORE (Solo per i Selezionati)
st.sidebar.subheader("Filtra Selezionati")
editori_disponibili = sorted(df_vip['Editore'].unique())
sel_editore = st.sidebar.multiselect("Seleziona Editore", editori_disponibili)

# 3. ORDINAMENTO (Solo per i Selezionati)
st.sidebar.subheader("Ordina Selezionati")
sort_mode = st.sidebar.selectbox(
    "Criterio di ordinamento:",
    ["Titolo (A-Z)", "Titolo (Z-A)", "Editore (A-Z)", "Editore (Z-A)"]
)

# --- APPLICAZIONE LOGICA AI DATI ---

# A. Filtro Ricerca (Globale su entrambi)
if search_query:
    mask_vip = df_vip.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    df_vip = df_vip[mask_vip]
    
    mask_altri = df_altri.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    df_altri = df_altri[mask_altri]

# B. Filtro Editore (Solo VIP)
if sel_editore:
    df_vip = df_vip[df_vip['Editore'].isin(sel_editore)]

# C. Ordinamento (Solo VIP)
if sort_mode == "Titolo (A-Z)":
    df_vip = df_vip.sort_values(by='Titolo', ascending=True)
elif sort_mode == "Titolo (Z-A)":
    df_vip = df_vip.sort_values(by='Titolo', ascending=False)
elif sort_mode == "Editore (A-Z)":
    df_vip = df_vip.sort_values(by='Editore', ascending=True)
elif sort_mode == "Editore (Z-A)":
    df_vip = df_vip.sort_values(by='Editore', ascending=False)

# --- INTERFACCIA A TAB ---
tab1, tab2 = st.tabs([f"⭐ Editori Selezionati ({len(df_vip)})", f"📂 Altri Editori ({len(df_altri)})"])

# === TAB 1: EDITORI SELEZIONATI (Ricchi di dettagli) ===
with tab1:
    if df_vip.empty:
        st.info("Nessun libro trovato con i filtri attuali.")
    
    for _, row in df_vip.iterrows():
        with st.container():
            c1, c2 = st.columns([1, 5])
            
            with c1:
                url = row['Copertina']
                if pd.notna(url) and str(url).startswith('http'):
                    st.image(str(url), width=120)
                else:
                    st.text("🖼️ No Img")
            
            with c2:
                st.subheader(row['Titolo'])
                st.markdown(f"**{row.get('Autore', 'N/D')}** | *{row.get('Editore', 'N/D')}* ({row.get('Anno', '')})")
                
                # Descrizione (Expandable)
                desc = str(row.get('Descrizione', ''))
                if len(desc) > 10 and desc.lower() != "nan":
                    with st.expander("📖 Leggi trama"):
                        st.write(desc)
                
                # Link IBS
                link = row.get('Link')
                if pd.notna(link) and str(link).startswith('http'):
                    st.markdown(f"[➡️ Vedi su IBS]({link})")
            
            st.divider()

# === TAB 2: ALTRI EDITORI (Lista compatta, niente descrizioni/filtri editore) ===
with tab2:
    st.caption("Questi libri appartengono a editori non presenti nella tua lista prioritaria. Vengono mostrati in ordine standard.")
    
    if df_altri.empty:
        st.info("Nessun libro in questa categoria.")

    # Usiamo una visualizzazione più compatta (Tabella o lista semplice)
    for _, row in df_altri.iterrows():
        with st.container():
            # Layout più stretto: Immagine piccola | Info essenziali
            c_img, c_info = st.columns([0.5, 5])
            
            with c_img:
                url = row['Copertina']
                if pd.notna(url) and str(url).startswith('http'):
                    st.image(str(url), width=60)
            
            with c_info:
                st.markdown(f"**{row['Titolo']}**")
                st.markdown(f"{row.get('Autore', 'N/D')} - *{row.get('Editore', 'N/D')}*")
                
                link = row.get('Link')
                if pd.notna(link) and str(link).startswith('http'):
                    st.markdown(f"[Link]({link})")
            
            st.markdown("---")
