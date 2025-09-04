import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Scraping fiches INHA - Historiens d’art")

st.write("Collez le contenu brut d’une page complète (Ctrl+A > Ctrl+V) ci-dessous :")

raw_text = st.text_area("Page INHA")

# Fonction pour isoler le bloc fiche biographique
def extract_fiche_block(text):
    # On cherche une ligne avec NOM en majuscules, jusqu'à "Sujets d’étude" inclus
    m = re.search(r"([A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ\-\s']+,.*?Sujets d’étude.*?)(\n|$)", text, flags=re.S)
    if m:
        return m.group(1).strip()
    return text  # fallback : si on ne trouve pas, on renvoie tout

# Fonction de parsing robuste
def parse_fiche(text):
    data = {
        "Nom": None,
        "Dernière mise à jour": None,
        "Date Naissance": None,
        "Lieu Naissance": None,
        "Date Décès": None,
        "Lieu Décès": None,
        "Auteur de la notice": None,
        "Profession ou activité principale": None,
        "Autres activités": None,
        "Sujets d’étude": None
    }

    # Nom : première ligne en majuscules
    m = re.match(r"^([A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ\-\s']+),?", text.strip())
    if m:
        data["Nom"] = m.group(1).strip()

    # Dernière mise à jour
    m = re.search(r"Mis à jour le (.*)", text)
    if m:
        data["Dernière mise à jour"] = m.group(1).strip()

    # Naissance + Décès + Lieux
    m = re.search(r"\((.*) – (.*)\)", text)
    if m:
        naissance = m.group(1)
        décès = m.group(2)

        # Naissance : date + lieu
        if "," in naissance:
            dn, ln = naissance.split(",", 1)
            data["Date Naissance"] = dn.strip()
            data["Lieu Naissance"] = ln.strip()
        else:
            data["Date Naissance"] = naissance.strip()

        # Décès : date + lieu
        if "," in décès:
            dd, ld = décès.split(",", 1)
            data["Date Décès"] = dd.strip()
            data["Lieu Décès"] = ld.strip()
        else:
            data["Date Décès"] = décès.strip()

    # Auteur de la notice
    m = re.search(r"Auteur de la notice *: *(.*)", text)
    if m:
        data["Auteur de la notice"] = m.group(1).strip()

    # Fonction pour capturer après un intitulé
    def extract_after(label, text, strict=False):
        if strict:
            # Cherche le premier caractère non espace/non saut de ligne après le label
            pattern = rf"{label}\s*([\S\s]*?)(?=\n[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ].*?:|\nAutres activités|\nSujets d’étude|\nAuteur de la notice|$)"
        else:
            pattern = rf"{label}\s*\n*(.+?)(?=\n[A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇ].*?:|\nAutres activités|\nSujets d’étude|\nAuteur de la notice|$)"
        m = re.search(pattern, text, flags=re.S)
        if m:
            return m.group(1).strip().replace("\n", " ")
        return None

    # Profession ou activité principale
    data["Profession ou activité principale"] = extract_after("Profession ou activité principale", text)

    # Autres activités
    data["Autres activités"] = extract_after("Autres activités", text)

    # Sujets d’étude (mode strict : prend dès le premier caractère non espace)
    data["Sujets d’étude"] = extract_after("Sujets d’étude", text, strict=True)

    return data

if st.button("Parser la fiche"):
    fiche_text = extract_fiche_block(raw_text)
    parsed = parse_fiche(fiche_text)
    df = pd.DataFrame([parsed])
    st.dataframe(df)

    # Export Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Fiche")
    st.download_button(
        label="Télécharger en XLSX",
        data=output.getvalue(),
        file_name="fiche_inha.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

