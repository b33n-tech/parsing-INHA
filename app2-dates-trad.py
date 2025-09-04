import streamlit as st
import pandas as pd
from io import BytesIO
from dateutil import parser

st.title("Convertisseur de dates XLSX")

# Upload du fichier
uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Aperçu des données :")
    st.dataframe(df.head())

    # Sélection de la colonne
    column = st.selectbox("Choisissez la colonne contenant les dates", df.columns)

    if st.button("Convertir les dates"):
        try:
            # Conversion des dates
            df[column] = df[column].apply(lambda x: parser.parse(str(x), dayfirst=True).strftime("%d/%m/%Y"))
            
            st.success("Conversion réussie !")
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
        except Exception as e:
            st.error(f"Erreur lors de la conversion : {e}")
