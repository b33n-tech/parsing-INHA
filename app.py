import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Scraping INHA – Extraction des notices d’historiens de l’art")

st.markdown("""
Collez ci-dessous **l'intégralité d'une notice (Ctrl+A → Ctrl+V)** depuis le dictionnaire de l’INHA.
Le script extraira uniquement les champs suivants :
- Dernière mise à jour (date)
- Date de naissance
- Lieu de naissance
- Date de décès
- Lieu de décès
- Auteur de la notice
- Profession ou activité principale
- Autres activités
- Sujets d’étude
""")

raw_text = st.text_area("Collez le contenu de la notice ici :", height=400)


def clean_value(text, label):
    """Retourne la valeur après un label, en ignorant espaces/sauts de ligne."""
    pattern = rf"{label}\s*\n*\s*(.*)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return ""


def parse_notice(text):
    data = {}

    # Nom (première ligne en majuscules généralement)
    first_line = text.strip().split("\n")[0]
    data["Nom"] = first_line.strip()

    # Dernière mise à jour
    m_update = re.search(r"Mis à jour le (.+)", text)
    data["Dernière mise à jour"] = m_update.group(1).strip() if m_update else ""

    # Dates et lieux (ligne entre parenthèses)
    m_dates = re.search(r"\((.*?)\)", text)
    if m_dates:
        life = m_dates.group(1)
        parts = [p.strip() for p in life.split("–")]
        if len(parts) == 2:
            birth, death = parts
            # Naissance
            b_date, b_place = birth.split(",", 1)
            data["Date naissance"] = b_date.strip()
            data["Lieu naissance"] = b_place.strip()
            # Décès
            if "," in death:
                d_date, d_place = death.split(",", 1)
                data["Date décès"] = d_date.strip()
                data["Lieu décès"] = d_place.strip()
            else:
                data["Date décès"] = death.strip()
                data["Lieu décès"] = ""

    # Auteur(s) de la notice
    m_author = re.search(r"Auteur(?:\(s\))? de la notice\s*:?\s*\n*\s*(.*)", text)
    data["Auteur de la notice"] = m_author.group(1).strip() if m_author else ""

    # Profession principale
    data["Profession ou activité principale"] = clean_value(text, "Profession ou activité principale")

    # Autres activités
    data["Autres activités"] = clean_value(text, "Autres activités")

    # Sujets d’étude (stricte)
    m_subjects = re.search(r"Sujets d’étude\s*:?\s*\n*\s*(.*)", text)
    data["Sujets d’étude"] = m_subjects.group(1).strip() if m_subjects else ""

    return data

if st.button("Extraire les informations"):
    if raw_text.strip():
        parsed = parse_notice(raw_text)
        df = pd.DataFrame([parsed])

        st.dataframe(df)

        # Export XLSX
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Notice")
        st.download_button(
            label="📥 Télécharger en XLSX",
            data=output.getvalue(),
            file_name="notice_inha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Veuillez coller une notice avant d’extraire.")
