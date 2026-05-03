import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SiteManager Pro - Strutture", layout="wide")

# Connessione al Google Sheet (Assicurati di avere secrets.toml configurato)
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="5s")

st.title("🏗️ SiteManager Cloud - Edifici 1, 3 & Ponticello")

menu = ["Dashboard", "Inserimento Dati", "Maturazione Calcestruzzo", "Visualizza Registro"]
choice = st.sidebar.selectbox("Menu Principale", menu)

# --- MODULO 1: DASHBOARD ---
if choice == "Dashboard":
    st.subheader("Stato del Cantiere")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Eventi Registrati", len(df))
        c2.metric("Sopralluoghi", len(df[df['Categoria'] == 'Sopralluogo']))
        
        # Check scadenze provini nelle prossime 48 ore
        oggi = datetime.now().date()
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        scadenze = df[(df['Categoria'] == 'Prova') & (df['Data'] >= oggi) & (df['Data'] <= oggi + timedelta(days=2))]
        c3.metric("Scadenze Prove (48h)", len(scadenze))
        
        st.write("### Ultime Attività Loggate")
        st.dataframe(df.sort_values(by='Data', ascending=False).head(10), use_container_width=True)

# --- MODULO 2: INSERIMENTO DATI ---
elif choice == "Inserimento Dati":
    st.subheader("Nuova Registrazione")
    with st.form("main_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            cat = st.selectbox("Categoria", ["Sopralluogo", "Materiale", "Prova", "Variante"])
            data_ev = st.date_input("Data Evento", datetime.now())
            ambito = st.text_input("Ambito (es. Edificio 1, Solaio L1)")
        with col_b:
            sogg = st.text_input("Soggetto (Fornitore/Lab)")
            stato = st.selectbox("Stato", ["In corso", "Completato", "Accettato", "Approvato"])
        
        desc = st.text_input("Descrizione / Riferimento Documentale")
        note = st.text_area("Note Tecniche")
        
        if st.form_submit_button("Salva su Cloud"):
            new_row = pd.DataFrame([{"Categoria": cat, "Data": data_ev.strftime("%Y-%m-%d"), "Ambito_Tipo": ambito, 
                                     "Descrizione_DDT": desc, "Fornitore_Laboratorio": sogg, "Stato_Risultato": stato, "Note": note}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Dati sincronizzati!")

# --- MODULO 3: MATURAZIONE CALCESTRUZZO (NUOVO) ---
elif choice == "Maturazione Calcestruzzo":
    st.subheader("🧪 Calcolatore e Tracker Provini")
    
    with st.expander("Calcola Date di Scadenza Prelievo", expanded=True):
        data_getto = st.date_input("Data del Getto / Prelievo", datetime.now())
        sigla = st.text_input("Sigla Provini (es. Rck 30 - Lotto A)")
        
        d7 = data_getto + timedelta(days=7)
        d28 = data_getto + timedelta(days=28)
        
        c1, c2 = st.columns(2)
        c1.info(f"**Test 7 Giorni (Breve):** \n\n {d7.strftime('%d/%m/%Y')}")
        c2.success(f"**Test 28 Giorni (Finale):** \n\n {d28.strftime('%d/%m/%Y')}")
        
        if st.button("Registra Scadenze nel Database"):
            # Salviamo due record di tipo 'Prova' nel registro principale
            scad_7 = pd.DataFrame([{"Categoria": "Prova", "Data": d7.strftime("%Y-%m-%d"), "Ambito_Tipo": "Calcestruzzo", 
                                    "Descrizione_DDT": f"Schiacciamento 7gg - {sigla}", "Fornitore_Laboratorio": "Lab. Notificato", 
                                    "Stato_Risultato": "In attesa", "Note": f"Riferimento getto del {data_getto}"}])
            scad_28 = pd.DataFrame([{"Categoria": "Prova", "Data": d28.strftime("%Y-%m-%d"), "Ambito_Tipo": "Calcestruzzo", 
                                     "Descrizione_DDT": f"Schiacciamento 28gg - {sigla}", "Fornitore_Laboratorio": "Lab. Notificato", 
                                     "Stato_Risultato": "In attesa", "Note": f"Riferimento getto del {data_getto}"}])
            
            updated_df = pd.concat([df, scad_7, scad_28], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Scadenze salvate nel Registro Prove.")

# --- MODULO 4: VISUALIZZA REGISTRO ---
elif choice == "Visualizza Registro":
    st.subheader("Archivio Storico")
    st.dataframe(df, use_container_width=True)
    st.download_button("Esporta in CSV per Verbale", df.to_csv(), "registro_cantiere.csv")