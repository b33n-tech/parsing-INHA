import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Scraping fiches INHA - Historiens d’art")
st.write("Collez le contenu **complet** d’une page (Ctrl+A > Ctrl+V) ci-dessous :")
raw_text = st.text_area("Page INHA")

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

ndef normalize_text(t: str) -> str:
    return t.replace("\r\n", "\n").replace("\r", "\n")

ndef extract_fiche_block(text: str) -> str:
    text = normalize_text(text)
    m = re.search(rf"(^[{UPPER}\-\s']+,.*?)(?:\n\n|$)", text, flags=re.S | re.M)
    start_idx = m.start(1) if m else 0
    return text[start_idx:]

ndef extract_author(text: str) -> str | None:
    text = normalize_text(text)
    m = re.search(r"^\s*(Auteur(?:\(s\))? de la notice)\s*:?[\t ]*(.+)$", text, flags=re.M)
    return m.group(2).strip() if m else None

ndef extract_section(label_regex: str, text: str, strict: bool = True) -> str | None:
    text = normalize_text(text)
    pattern = rf"{label_regex}\s*:?[\t ]*\n*\s*(.+?){STOP_AT_NEXT_LABEL}"
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return None
    val = m.group(1).strip()
    val = re.sub(r"\s+", " ", val)
    return val or None

ndef parse_fiche(text: str) -> dict:
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
        "Sujets d’étude": None,
    }

    m = re.match(rf"^([{UPPER}\-\s']+,.*)$", text.strip())
    if m:
        data["Nom"] = m.group(1).strip()

    m = re.search(r"(?:Mis à jour le|Dernière mise à jour le)\s+(.+)", text)
    if m:
        data["Dernière mise à jour"] = m.group(1).strip()

    # Dates / lieux: line like "(26 février 1781, Paris – 12 juillet 1863, Versailles)"
    m = re.search(r"\((.*?)\s*[–-]\s*(.*?)\)", text)
    if m:
        naissance = m.group(1).strip()
        deces = m.group(2).strip()
        if "," in naissance:
            dn, ln = naissance.split(",", 1)
            data["Date Naissance"], data["Lieu Naissance"] = dn.strip(), ln.strip()
        else:
            data["Date Naissance"] = naissance
        if "," in deces:
            dd, ld = deces.split(",", 1)
            data["Date Décès"], data["Lieu Décès"] = dd.strip(), ld.strip()
        else:
            data["Date Décès"] = deces

    data["Auteur de la notice"] = extract_author(text)
    data["Profession ou activité principale"] = extract_section("Profession ou activité principale", text, strict=True)
    data["Autres activités"] = extract_section("Autres activités", text, strict=True)
    data["Sujets d’étude"] = extract_section("Sujets d’étude", text, strict=True)

    return data

# --- UI ----------------------------------------------------------------------
if st.button("Parser la fiche"):
    fiche_text = extract_fiche_block(raw_text)
    parsed = parse_fiche(fiche_text)
    df = pd.DataFrame([parsed])
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Fiche")
    st.download_button(
        label="Télécharger en XLSX",
        data=output.getvalue(),
        file_name="fiche_inha.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
