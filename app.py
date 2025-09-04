import streamlit as st
import pandas as pd
import re
from io import BytesIO
from dateutil import parser as date_parser

st.title("Scraping fiches INHA - Historiens d’art")

# Étape 1 : nombre de fiches à parser
max_fiches = st.number_input("Nombre de fiches à parser", min_value=1, max_value=50, value=5, step=1)

# Étape 2 : saisie des fiches une par une
fiches_input = []
for i in range(max_fiches):
    fiche_text = st.text_area(f"Fiche {i+1}", key=f"fiche_{i}")
    if fiche_text.strip():
        fiches_input.append(fiche_text)

# --- Helpers -----------------------------------------------------------------
UPPER = "A-ZÉÈÀÙÂÊÎÔÛÄËÏÖÜÇŒÆ"

LABELS = [
    "Profession ou activité principale",
    "Autres activités",
    "Sujets d’étude",
    r"Auteur(?:\(s\))? de la notice"
]
LABELS_OR = "|".join(LABELS)
STOP_AT_NEXT_LABEL = rf"(?=\r?\n(?:{LABELS_OR})\b|$)"

def normalize_text(t: str) -> str:
    return t.replace("\r\n", "\n").replace("\r", "\n")

# Conversion des dates françaises et anglaises au format DD/MM/YYYY
def format_date(date_str: str) -> str:
    if not date_str:
        return ""
    # Nettoyage des espaces et tabulations
    clean_str = re.sub(r"[\t\s]+", " ", date_str.strip())
    try:
        # forcer dayfirst=True pour interpréter correctement les dates françaises
        dt = date_parser.parse(clean_str, dayfirst=True, fuzzy=True)
        return dt.strftime("%d/%m/%Y")
    except:
        return clean_str

def extract_author(text: str) -> str | None:
    text = normalize_text(text)
    m = re.search(r"^\s*(Auteur(?:\(s\))? de la notice)\s*:?[\t ]*(.+)$", text, flags=re.M)
    return m.group(2).strip() if m else None

def extract_section(label_regex: str, text: str, strict: bool = True) -> str | None:
    text = normalize_text(text)
    pattern = rf"{label_regex}\s*:?[\t ]*\n*\s*(.+?){STOP_AT_NEXT_LABEL}"
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return None
    val = m.group(1).strip()
    val = re.sub(r"\s+", " ", val)
    return val or None

def parse_fiche(text: str) -> dict:
    text = normalize_text(text)
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

    m = re.match(rf"^([{UPPER}\-\s']+,.*)$", text.strip())
    if m:
        data["Nom"] = m.group(1).strip()

    m = re.search(r"(?:Mis à jour le|Dernière mise à jour le)\s+(.+)", text)
    if m:
        data["Dernière mise à jour"] = format_date(m.group(1).strip())

    m = re.search(r"\((.*?)\s*[–-]\s*(.*?)\)", text)
    if m:
        naissance = m.group(1).strip()
        deces = m.group(2).strip()
        if "," in naissance:
            dn, ln = naissance.split(",", 1)
            data["Date Naissance"], data["Lieu Naissance"] = format_date(dn.strip()), ln.strip()
        else:
            data["Date Naissance"] = format_date(naissance)
        if "," in deces:
            dd, ld = deces.split(",", 1)
            data["Date Décès"], data["Lieu Décès"] = format_date(dd.strip()), ld.strip()
        else:
            data["Date Décès"] = format_date(deces)

    data["Auteur de la notice"] = extract_author(text)
    data["Profession ou activité principale"] = extract_section("Profession ou activité principale", text, strict=True)
    data["Autres activités"] = extract_section("Autres activités", text, strict=True)
    data["Sujets d’étude"] = extract_section("Sujets d’étude", text, strict=True)

    return data

# Étape 3 : Parser toutes les fiches
if st.button("Parser toutes les fiches"):
    parsed_list = [parse_fiche(fiche) for fiche in fiches_input]
    df = pd.DataFrame(parsed_list)
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Fiches")
    st.download_button(
        label="Télécharger toutes les fiches en XLSX",
        data=output.getvalue(),
        file_name="fiches_inha.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
