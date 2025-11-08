import streamlit as st
import pandas as pd
import random
from loguru import logger
# openpyxl è necessario a pandas per leggere i file .xlsx

# --- Configurazione della Pagina ---
# Usiamo il layout "wide" per dare più spazio alle tabelle affiancate
st.set_page_config(layout="wide", page_title="Gioco a Squadre")

# --- Funzioni Principali ---

def initialize_state():
    """Inizializza lo stato della sessione per le due squadre e gli imprevisti."""
    
    # Crea il DataFrame di default per una squadra
    default_data = {
        "Fattore": ["👤 Popolazione", "🥫 Cibo", "💰 Finanze","🚑 Ospedali","🎒 Scuole","🔋 Centrali Elettriche","⛪ Luoghi di Culto","🫂 Solidarietà"],
        "Valore": [100] * 8,
        "Barra": [100] * 8  # Questa colonna sarà usata per la visualizzazione
    }
    
    # Inizializza lo stato per la Squadra 1 se non esiste
    if 'team1_df' not in st.session_state:
        st.session_state.team1_df = pd.DataFrame(default_data)
        
    # Inizializza lo stato per la Squadra 2 se non esiste
    if 'team2_df' not in st.session_state:
        st.session_state.team2_df = pd.DataFrame(default_data)
        
    # Inizializza il contenitore per gli imprevisti
    if 'imprevisti_df' not in st.session_state:
        st.session_state.imprevisti_df = None

@st.cache_data(ttl=600) # Cache per 10 minuti per evitare di scaricare troppo spesso
def load_data_from_gdrive(url: str) -> pd.DataFrame | None:
    """
    Carica un file Excel da un link condivisibile di Google Drive.
    Il link deve essere pubblico ("Chiunque abbia il link").
    """
    try:
        # Trasforma l'URL di condivisione in un URL di download diretto .xlsx
        # Formato standard: https://docs.google.com/spreadsheets/d/FILE_ID/edit?usp=sharing
        if 'google.com' not in url:
            st.error("URL non valido. Assicurati sia un link Google Sheet.")
            return None
            
        file_id = url.split('/d/')[1].split('/')[0]
        export_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
        
        # Legge il file Excel usando openpyxl (richiesto per .xlsx)
        logger.debug(f"Scaricando file da: {export_url}")
        df = pd.read_excel(export_url, engine='openpyxl')
        
        # Controlla che la colonna richiesta esista
        if 'imprevisto' not in df.columns:
            st.error("Errore: Il file Excel DEVE avere una colonna chiamata 'imprevisto'.")
            return None
            
        return df
        
    except Exception as e:
        st.error(f"Errore nel caricamento o lettura del file: {e}")
        st.info("Assicurati che il link di condivisione sia impostato su 'Chiunque abbia il link' -> 'Visualizzatore'.")
        return None

def sync_team1():
    """
    Callback per sincronizzare i dati della Squadra 1 dopo la modifica.
    Questo viene chiamato da on_change in st.data_editor.
    """
    # Il dataframe modificato è salvato da Streamlit nella chiave dell'editor
    edited_dict = st.session_state.editor_team1.get('edited_rows', {})
    # Sincronizza la barra
    for row, edit in edited_dict.items():
        st.session_state.team1_df.loc[row, 'Valore'] = edit['Valore']
        st.session_state.team1_df.loc[row, 'Barra'] = edit['Valore']


def sync_team2():
    """
    Callback per sincronizzare i dati della Squadra 2 dopo la modifica.
    Questo viene chiamato da on_change in st.data_editor.
    """
    # Il dataframe modificato è salvato da Streamlit nella chiave dell'editor
    edited_dict = st.session_state.editor_team2.get('edited_rows', {})
    # Sincronizza la barra
    for row, edit in edited_dict.items():
        st.session_state.team2_df.loc[row, 'Valore'] = edit['Valore']
        st.session_state.team2_df.loc[row, 'Barra'] = edit['Valore']

# --- Inizializzazione ---
initialize_state()

# --- Interfaccia Utente (UI) ---

st.title("🎲 The War Games 🎲")
st.caption("Un gioco di sopravvivenza dove ogni scelta conta!")

# --- Sezione 1: Caricamento Dati ---
st.header("1. Configurazione del Gioco")
st.markdown("""
Incolla qui sotto il link di condivisione del tuo file Google Sheet. 
Il file deve:
1.  Essere accessibile a **"Chiunque abbia il link"** (almeno come 'Visualizzatore').
2.  Contenere un foglio con una colonna chiamata esattamente `imprevisto`.
""")

gdrive_url = st.text_input(
    "URL Google Sheet:", 
    placeholder="https://docs.google.com/spreadsheets/d/1aBcD_...",
    value='https://docs.google.com/spreadsheets/d/1soXeIAa-XoHsTfAE8hXIQ8lT711k9GFuuAL_gkFTUQs/edit?gid=0#gid=0',
)

if st.button("Carica Imprevisti e Inizia Gioco"):
    if gdrive_url:
        with st.spinner("Connessione a Google Drive e caricamento imprevisti..."):
            data = load_data_from_gdrive(gdrive_url)
            if data is not None:
                st.session_state.imprevisti_df = data
                st.success(f"Caricati con successo {len(data)} imprevisti!")
            else:
                st.session_state.imprevisti_df = None # Resetta in caso di fallimento
    else:
        st.warning("Per favore, inserisci un URL valido.")

# --- Sezione 2: Gioco (Mostra solo se i dati sono stati caricati) ---
if st.session_state.imprevisti_df is not None:
    st.divider()
    st.header("2. Pannello di Gioco")
    
    game_over = False

    # Definizione della configurazione delle colonne (identica per entrambe le tabelle)
    col_config_1 = {
        "Fattore": st.column_config.TextColumn("Fattore", width="medium", disabled=True),
        "Valore": st.column_config.NumberColumn(
            "Valore (0-100)",
            min_value=0,
            max_value=100,
            step=1,
            help="Modifica questo valore. Il gioco finisce se arriva a 0.",
            width="small"
        ),
        "Barra": st.column_config.ProgressColumn(
            "Salute",
            min_value=0,
            max_value=100,
            format="%d%%",
            help="Rappresentazione visuale del valore.",
            width="large"
        )
    }
    col_config_2 = {
        "Fattore": st.column_config.TextColumn("Fattore", width="medium", disabled=True),
        "Valore": st.column_config.NumberColumn(
            "Valore (0-100)",
            min_value=0,
            max_value=100,
            step=1,
            help="Modifica questo valore. Il gioco finisce se arriva a 0.",
            width="small"
        ),
        "Barra": st.column_config.ProgressColumn(
            "Salute",
            min_value=0,
            max_value=100,
            format="%d%%",
            help="Rappresentazione visuale del valore.",
            color="blue",
            width="large"
        )
    }
    
    # Creazione delle colonne per il layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🟥 Squadra 1")
        # Disegna l'editor dati. Qualsiasi modifica qui viene salvata e ricarica lo script.
        # Rimuoviamo l'assegnazione a edited_df1
        st.data_editor(
            st.session_state.team1_df,
            column_config=col_config_1,
            use_container_width=True,
            num_rows="fixed",
            key="editor_team1",
            hide_index=True,
            on_change=sync_team1  # <-- QUESTA È LA MODIFICA CHIAVE
        )
        
        # QUESTE RIGHE VENGONO RIMOSSE
        # # Sincronizza la colonna 'Barra' con la colonna 'Valore' dopo l'eventuale modifica
        # edited_df1['Barra'] = edited_df1['Valore']
        # st.session_state.team1_df = edited_df1 # Salva lo stato aggiornato

    with col2:
        st.subheader("🟦 Squadra 2")
        # Rimuoviamo l'assegnazione a edited_df2
        st.data_editor(
            st.session_state.team2_df,
            column_config=col_config_2,
            use_container_width=True,
            num_rows="fixed",
            key="editor_team2",
            hide_index=True,
            on_change=sync_team2  # <-- QUESTA È LA MODIFICA CHIAVE
        )
        
    st.divider()

    # --- Sezione 3: Controllo Vincitore/Perdente ---
    if (st.session_state.team1_df['Valore'] <= 0).any():
        st.error("☠️ GIOCO FINITO! La Squadra 1 ha esaurito completamente un fattore! ☠️", icon="🟥")
        st.balloons()
        game_over = True
    
    if (st.session_state.team2_df['Valore'] <= 0).any():
        st.error("☠️ GIOCO FINITO! La Squadra 2 ha esaurito completamente un fattore! ☠️", icon="🟦")
        st.balloons()
        game_over = True
        
    # --- Sezione 4: Azione di Gioco ---
    st.header("3. Pesca Imprevisto")
    st.caption("Dopo aver pescato l'imprevisto, modifica manualmente i valori nelle tabelle qui sopra.")
    
    event_list = st.session_state.imprevisti_df['imprevisto'].dropna().tolist()
    
    if not event_list:
        st.warning("Nessun imprevisto valido trovato nella colonna 'imprevisto' del file Excel.")
        st.stop()
    
    event_number = len(event_list)
    
    selected_event = st.number_input(
        "Scegli un numero di 1 a " + str(event_number) + " per pescare un imprevisto",
        min_value=1,
        max_value=event_number,
        value=1,
        step=1
    )
    logger.debug(f"Numero imprevisto selezionato: {selected_event}")
    
    chosen_event = event_list[selected_event - 1]  # -1 perché la lista è 0-indexed
    st.warning(f"**Imprevisto Pescato:**\n\n {chosen_event}")
            
    if game_over:
        st.warning("Il gioco è terminato. Per ricominciare, ricarica la pagina (F5).")

else:
    st.info("Inserisci l'URL del tuo Google Sheet e clicca 'Carica' per iniziare.")
