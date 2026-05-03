import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="SiteManager Pro - Edifici 1, 3 & Ponticello",
    page_icon="🏗️",
    layout="wide"
)

# --- CONNESSIONE AL DATABASE (Google Sheets) ---
# Il codice cercherà le credenziali nel file .streamlit/secrets.toml
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="5s")
except Exception as e:
    st.error("Errore di connessione al database. Verifica i 'Secrets' su Streamlit Cloud.")
    st.stop()

# --- SIDEBAR NAVIGAZIONE ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4342/4342728.png", width=100)
st.sidebar.title("SiteManager Pro")
menu = ["📊 Dashboard", "📝 Registro & Foto", "🧪 Maturazione CLS", "📂 Archivio Completo"]
choice = st.sidebar.selectbox("Naviga nei Moduli", menu)

st.title("🏗️ Gestione Cantieri: Edifici 1, 3 & Ponticello")

# --- MODULO 1: DASHBOARD ---
if choice == "📊 Dashboard":
    st.subheader("Stato dell'Opera e Scadenze")
    
    if not df.empty:
        # Calcolo Metriche
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Totale Record", len(df))
        col2.metric("Sopralluoghi", len(df[df['Categoria'] == 'Sopralluogo']))
        col3.metric("Materiali Accettati", len(df[df['Categoria'] == 'Materiale']))
        
        # Alert Prove (Scadenze nei prossimi 3 giorni)
        oggi = datetime.now().date()
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        alert_prove = df[(df['Categoria'] == 'Prova') & (df['Data'] >= oggi) & (df['Data'] <= oggi + timedelta(days=3))]
        col4.metric("Scadenze Prove (72h)", len(alert_prove), delta_color="inverse")

        # Visualizzazione rapida scadenze
        if not alert_prove.empty:
            st.warning("⚠️ PROVE IN SCADENZA: Contattare il laboratorio per i test imminenti.")
            st.table(alert_prove[['Data', 'Ambito_Tipo', 'Descrizione_DDT']])

        st.write("### Ultimi aggiornamenti dal campo")
        st.dataframe(df.sort_values(by='Data', ascending=False).head(10), use_container_width=True)
    else:
        st.info("Il database è vuoto. Inizia inserendo dei dati dal modulo Registro.")

# --- MODULO 2: REGISTRO & FOTO ---
elif choice == "📝 Registro & Foto":
    st.subheader("Registrazione Attività e Acquisizione Foto")
    
    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            categoria = st.selectbox("Categoria Evento", ["Sopralluogo", "Materiale", "Prova", "Variante"])
            data_ev = st.date_input("Data", datetime.now())
            ambito = st.text_input("Ambito (es. Edificio 1, Pilastri L1, Ponticello)")
        with c2:
            soggetto = st.text_input("Soggetto (Fornitore, Lab, Impresa)")
            stato = st.selectbox("Stato/Esito", ["In corso", "Completato", "Accettato", "Approvato", "Da Verificare"])
            descr = st.text_input("Descrizione sintetica / N. DDT")
        
        note = st.text_area("Note Tecniche Dettagliate")
        
        st.write("---")
        st.write("### 📸 Documentazione Fotografica")
        img_file = st.camera_input("Scatta foto ora (per sopralluoghi/prove)")
        upload_file = st.file_uploader("Oppure carica file (PDF certificati, foto gallery)", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if st.form_submit_button("Salva nel Database Cloud"):
            # Gestione riferimento foto
            ref_foto = "FOTO/FILE PRESENTE" if (img_file or upload_file) else "Nessun allegato"
            
            new_data = pd.DataFrame([{
                "Categoria": categoria,
                "Data": data_ev.strftime("%Y-%m-%d"),
                "Ambito_Tipo": ambito,
                "Descrizione_DDT": descr,
                "Fornitore_Laboratorio": soggetto,
                "Stato_Risultato": stato,
                "Note": note,
                "Link_Foto": ref_foto
            }])
            
            # Aggiornamento Google Sheets
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            st.success(f"Registrazione effettuata con successo! Foto contrassegnata come: {ref_foto}")

# --- MODULO 3: MATURAZIONE CLS ---
elif choice == "🧪 Maturazione CLS":
    st.subheader("Calcolatore Scadenze Provini Calcestruzzo")
    st.info("Inserisci la data del getto per generare automaticamente i promemoria per i test a 7 e 28 giorni.")
    
    with st.form("form_cls"):
        d_getto = st.date_input("Data del Getto", datetime.now())
        sigla_lotto = st.text_input("Identificativo Lotto (es. Rck 30 - Solaio Edificio 3)")
        lab_rif = st.text_input("Laboratorio incaricato")
        
        scad_7 = d_getto + timedelta(days=7)
        scad_28 = d_getto + timedelta(days=28)
        
        col_x, col_y = st.columns(2)
        col_x.info(f"📅 **Test 7gg:** {scad_7.strftime('%d/%m/%Y')}")
        col_y.success(f"📅 **Test 28gg:** {scad_28.strftime('%d/%m/%Y')}")
        
        if st.form_submit_button("Registra scadenze in Calendario Prove"):
            # Generazione record per il registro
            r7 = pd.DataFrame([{"Categoria": "Prova", "Data": scad_7.strftime("%Y-%m-%d"), "Ambito_Tipo": "Calcestruzzo", 
                                "Descrizione_DDT": f"Schiacciamento 7gg - {sigla_lotto}", "Fornitore_Laboratorio": lab_rif, 
                                "Stato_Risultato": "In attesa", "Note": "Maturazione breve", "Link_Foto": "N/A"}])
            r28 = pd.DataFrame([{"Categoria": "Prova", "Data": scad_28.strftime("%Y-%m-%d"), "Ambito_Tipo": "Calcestruzzo", 
                                 "Descrizione_DDT": f"Schiacciamento 28gg - {sigla_lotto}", "Fornitore_Laboratorio": lab_rif, 
                                 "Stato_Risultato": "In attesa", "Note": "Maturazione finale", "Link_Foto": "N/A"}])
            
            updated_df = pd.concat([df, r7, r28], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Scadenze aggiunte al registro globale!")

# --- MODULO 4: ARCHIVIO COMPLETO ---
elif choice == "📂 Archivio Completo":
    st.subheader("Consultazione ed Esportazione Dati")
    
    # Filtri di ricerca
    search = st.text_input("Cerca parola chiave (es. 'Edificio 1', 'Acciaio', 'Saggio')")
    if search:
        display_df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
    else:
        display_df = df
        
    st.dataframe(display_df, use_container_width=True)
    
    # Esportazione
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Registro in CSV (per Excel)",
        data=csv,
        file_name=f"registro_cantiere_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )