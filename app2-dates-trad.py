import streamlit as st
import pandas as pd
from io import BytesIO
from dateutil import parser

st.title("Convertisseur de dates XLSX (français → dd/mm/yyyy)")

# Dictionnaire mois FR → EN
months_fr_en = {
    "janvier": "January",
    "février": "February",
    "mars": "March",
    "avril": "April",
    "mai": "May",
    "juin": "June",
    "juillet": "July",
    "août": "August",
    "septembre": "September",
    "octobre": "October",
    "novembre": "November",
    "décembre": "December"
}

def parse_french_date(date_str):
    try:
        s = str(date_str).lower()
        for fr, en in months_fr_en.items():
            s = s.replace(fr, en)
        return parser.parse(s, dayfirst=True).strftime("%d/%m/%Y")
    except:
        return "DATE_INVALID"  # marque les dates non convertibles

# Upload du fichier
uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Aperçu des données :")
    st.dataframe(df.head())

    # Sélection de plusieurs colonnes
    columns = st.multiselect("Choisissez les colonnes contenant les dates", df.columns)

    if st.button("Convertir les dates"):
        if columns:
            for col in columns:
                df[col] = df[col].apply(parse_french_date)
            st.success("Conversion terminée ! Les dates invalides sont marquées DATE_INVALID.")
            st.dataframe(df.head())

            # Préparer le fichier à télécharger
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            buffer.seek(0)

            st.download_button(
                label="Télécharger le fichier modifié",
                data=buffer,
                file_name="dates_converties.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Veuillez sélectionner au moins une colonne.")
