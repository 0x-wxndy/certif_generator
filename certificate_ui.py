#!/usr/bin/env python3
"""Interface web Streamlit — Ministère de la Justice (certificats officiels)."""

from __future__ import annotations

import base64
import io
import zipfile
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from certificate_generator import (
    BASE_DIR,
    BULK_DIR,
    OUTPUT_DIR,
    TEMPLATES_DIR,
    build_excel_template_bytes,
    document_to_png_bytes,
    docx_to_pdf_bytes,
    generate_certificate,
    generate_from_spreadsheet,
    get_template,
    list_templates,
    write_bulk_excel_templates,
)

ASSETS_DIR = BASE_DIR / "assets"
EMBLEM_PATH = ASSETS_DIR / "Peoples-Democratic-Republic-of-Algeria.png"
FLAG_PATH = ASSETS_DIR / "algerie_flag.png"
MINISTRY_SVG = ASSETS_DIR / "وزارة_العدل_الجزائر.svg"

st.set_page_config(
    page_title="وزارة العدل — Générateur de certificats",
    page_icon=str(EMBLEM_PATH) if EMBLEM_PATH.exists() else "📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _img_b64(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


FLAG_B64 = _img_b64(FLAG_PATH)
EMBLEM_B64 = _img_b64(EMBLEM_PATH)
MINISTRY_B64 = _img_b64(MINISTRY_SVG)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Source+Sans+3:wght@400;500;600;700&display=swap');

    :root {{
        --green-deep: #0A3D2C;
        --green: #146B4A;
        --green-mid: #1F8A5C;
        --green-soft: #E7F2EC;
        --gold: #B89C34;
        --gold-bright: #D4BC5A;
        --bg: #F3F6F4;
        --panel: #FFFFFF;
        --panel-soft: #F7FAF8;
        --border: #C9D8CF;
        --text: #14241C;
        --text-muted: #5A6B62;
        --danger: #B42318;
        --success-bg: rgba(20, 107, 74, 0.10);
        --success-border: rgba(20, 107, 74, 0.35);
    }}

    .stApp {{
        background:
            radial-gradient(ellipse 80% 50% at 50% -10%, rgba(184, 156, 52, 0.14), transparent 55%),
            linear-gradient(180deg, #E8F0EB 0%, var(--bg) 28%, #EEF3F0 100%);
        color: var(--text);
        font-family: "Source Sans 3", "Segoe UI", sans-serif;
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}
    [data-testid="stToolbar"], footer {{
        visibility: hidden;
        height: 0;
    }}

    .block-container {{
        padding-top: 0.75rem;
        padding-bottom: 2.5rem;
        max-width: 1280px;
    }}

    /* —— Hero —— */
    .hero {{
        position: relative;
        overflow: hidden;
        border-radius: 18px;
        margin-bottom: 1.35rem;
        padding: 1.6rem 1.5rem 1.45rem;
        background:
            linear-gradient(135deg, var(--green-deep) 0%, #0F4F38 48%, #145C42 100%);
        box-shadow: 0 18px 40px rgba(10, 61, 44, 0.22);
        animation: heroIn 0.7s ease-out both;
    }}
    .hero::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 12% 20%, rgba(212, 188, 90, 0.18), transparent 42%),
            radial-gradient(circle at 88% 80%, rgba(255,255,255,0.06), transparent 40%);
        pointer-events: none;
    }}
    .hero::after {{
        content: "";
        position: absolute;
        left: 8%;
        right: 8%;
        bottom: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--gold-bright), var(--gold), transparent);
        animation: goldLine 2.4s ease-in-out infinite alternate;
    }}
    .hero-inner {{
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.85rem;
        text-align: center;
    }}
    .hero-logos {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.6rem;
        flex-wrap: wrap;
    }}
    .hero-logos img {{
        height: 88px;
        width: auto;
        object-fit: contain;
        filter: drop-shadow(0 6px 14px rgba(0,0,0,0.25));
        animation: logoFloat 3.2s ease-in-out infinite;
    }}
    .hero-logos img:nth-child(2) {{
        height: 102px;
        animation-delay: 0.35s;
    }}
    .hero-logos img:nth-child(3) {{
        height: 86px;
        animation-delay: 0.7s;
    }}
    .hero-titles {{
        color: #F7F3E6;
    }}
    .hero-titles .republic {{
        font-family: "Amiri", "Traditional Arabic", serif;
        font-size: clamp(1.35rem, 2.6vw, 1.85rem);
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.02em;
        background: linear-gradient(180deg, #F8E7A0 0%, var(--gold) 55%, #8F7420 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        filter: drop-shadow(0 1px 0 rgba(0,0,0,0.35));
    }}
    .hero-titles .ministry {{
        font-family: "Amiri", "Traditional Arabic", serif;
        font-size: clamp(1.55rem, 3vw, 2.15rem);
        font-weight: 700;
        margin: 0.15rem 0 0;
        color: #FFF8E7;
    }}
    .hero-titles .tagline {{
        margin: 0.55rem 0 0;
        font-size: 0.95rem;
        font-weight: 500;
        color: rgba(247, 243, 230, 0.82);
        letter-spacing: 0.04em;
    }}

    @keyframes heroIn {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes logoFloat {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-4px); }}
    }}
    @keyframes goldLine {{
        from {{ opacity: 0.55; transform: scaleX(0.92); }}
        to {{ opacity: 1; transform: scaleX(1); }}
    }}

    /* —— Panels / tabs —— */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 24px rgba(10, 61, 44, 0.06);
    }}

    div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 0.35rem;
        background: var(--green-soft);
        padding: 0.35rem;
        border-radius: 12px;
        border: 1px solid var(--border);
    }}
    div[data-testid="stTabs"] button {{
        font-family: "Source Sans 3", sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: var(--text-muted) !important;
        border-radius: 9px !important;
    }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--green-deep) !important;
        background: #fff !important;
    }}
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
        background-color: var(--gold) !important;
    }}
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {{
        display: none;
    }}

    .section-label {{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--green);
        margin: 1rem 0 0.45rem;
    }}
    .section-label:first-of-type {{
        margin-top: 0.2rem;
    }}

    .file-card, .template-card, .generated-card {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
        background: var(--panel-soft);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin: 0.45rem 0;
        transition: border-color 0.2s ease, transform 0.2s ease;
    }}
    .template-card:hover, .generated-card:hover {{
        border-color: var(--gold);
        transform: translateY(-1px);
    }}
    .file-icon, .tpl-badge {{
        width: 44px;
        height: 44px;
        border-radius: 10px;
        background: linear-gradient(145deg, var(--green-soft), #fff);
        border: 1px solid var(--border);
        color: var(--green-deep);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        flex-shrink: 0;
    }}
    .file-card-title, .tpl-title {{
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text);
        margin: 0;
        word-break: break-word;
    }}
    .file-card-meta, .tpl-meta {{
        font-size: 0.8rem;
        color: var(--text-muted);
        margin: 0.15rem 0 0;
    }}
    .tpl-ar {{
        font-family: "Amiri", serif;
        font-size: 1.05rem;
        color: var(--green-deep);
        margin: 0 0 0.15rem;
        direction: rtl;
    }}

    .preview-toolbar h3 {{
        margin: 0 0 0.75rem;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--green-deep);
    }}

    .status-badge {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        background: var(--success-bg);
        border: 1px solid var(--success-border);
        border-radius: 10px;
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.85rem;
    }}
    .status-icon {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: rgba(20, 107, 74, 0.18);
        color: var(--green);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        flex-shrink: 0;
    }}
    .status-label {{
        font-size: 0.78rem;
        color: var(--green);
        margin: 0;
    }}
    .status-file {{
        font-family: ui-monospace, monospace;
        font-size: 0.82rem;
        color: var(--text);
        margin: 0.1rem 0 0;
    }}

    .preview-empty {{
        border: 1px dashed var(--border);
        border-radius: 12px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        color: var(--text-muted);
        min-height: 380px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: var(--panel-soft);
    }}
    .preview-empty strong {{
        color: var(--green-deep);
        font-size: 0.98rem;
    }}

    [data-testid="stImage"] {{
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.55rem;
    }}

    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label {{
        font-size: 0.82rem !important;
        color: var(--text-muted) !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stTextInput"] input {{
        background: var(--panel-soft) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
    }}

    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stBaseButton-secondary"] button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stFormSubmitButton"] button {{
        background: linear-gradient(180deg, var(--green-mid), var(--green)) !important;
        color: #fff !important;
        border: 1px solid var(--green-deep) !important;
    }}
    div[data-testid="stFormSubmitButton"] button:hover {{
        filter: brightness(1.05);
    }}

    .stDownloadButton button {{
        background: linear-gradient(180deg, var(--gold-bright), var(--gold)) !important;
        color: #1A1608 !important;
        border: 1px solid #8F7420 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }}

    .hint-list {{
        font-size: 0.86rem;
        color: var(--text-muted);
        line-height: 1.55;
    }}
    .about-block {{
        background: var(--panel-soft);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
    }}
    .about-block h3 {{
        margin: 0 0 0.55rem;
        color: var(--green-deep);
        font-size: 1.1rem;
    }}
    .about-block h3.ar {{
        font-family: "Amiri", serif;
        font-size: 1.35rem;
        direction: rtl;
        text-align: right;
    }}
    .about-block p, .about-block li {{
        color: var(--text);
        font-size: 0.92rem;
        line-height: 1.6;
    }}
    .about-block.ar {{
        direction: rtl;
        text-align: right;
        font-family: "Amiri", serif;
    }}
    .about-block.ar p, .about-block.ar li {{
        font-size: 1.05rem;
    }}
    .footer-note {{
        margin-top: 1.25rem;
        text-align: center;
        color: var(--text-muted);
        font-size: 0.8rem;
    }}

    @media (max-width: 768px) {{
        .hero-logos img {{ height: 64px !important; }}
        .hero-logos img:nth-child(2) {{ height: 74px !important; }}
        .hero {{ padding: 1.2rem 1rem; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

templates = list_templates()
template_labels = {f"{t.name_fr} ({t.output_format.upper()})": t.id for t in templates}

# Ensure Excel lot templates exist and stay in sync with field definitions.
try:
    write_bulk_excel_templates(BULK_DIR)
except Exception:
    BULK_DIR.mkdir(parents=True, exist_ok=True)

if "preview_zoom" not in st.session_state:
    st.session_state.preview_zoom = 1.0
if "last_result" not in st.session_state:
    st.session_state.last_result = None


def _field_label(field) -> str:
    return field.label_fr or field.label_en


def _default_value(field) -> str:
    if field.default:
        return field.default
    if field.id == "issue_date":
        return date.today().strftime("%d/%m/%Y")
    return ""


def _format_fr_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _should_show_field(template, field) -> bool:
    return not (template.output_format == "pdf" and field.id == "title")


def _section_label(text: str) -> None:
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)


def _file_card(filename: str, output_format: str) -> None:
    st.markdown(
        f"""
        <div class="file-card">
            <div class="file-icon">{output_format.upper()}</div>
            <div>
                <p class="file-card-title">{filename}</p>
                <p class="file-card-meta">Format de sortie : {output_format.upper()}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _status_badge(filename: str) -> None:
    st.markdown(
        f"""
        <div class="status-badge">
            <div class="status-icon">✓</div>
            <div>
                <p class="status-label">Certificat créé avec succès</p>
                <p class="status-file">{filename}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _field_placeholder(field_id: str) -> str:
    examples = {
        "recipient_name": "ex. أحمد بن محمد",
        "recipient_title": "ex. أحمد بن محمد | السيد",
        "council_location": "ex. الجزائر العاصمة",
        "training_field": "ex. التحول الرقمي",
        "date_from": "ex. 01/03/2026",
        "date_to": "ex. 15/03/2026",
        "coordinating_orgs": "ex. وزارة العدل, المديرية العامة",
        "rank_workplace": "ex. قاضية - مجلس قضاء الجزائر",
        "deceased_name": "ex. محمد الأمين",
        "family_name": "ex. عائلة بن علي",
        "rank": "ex. مستشار",
        "job": "ex. رئيس قسم",
        "issue_date": "ex. 11/07/2026",
        "title": "ex. السيد(ة)",
    }
    return examples.get(field_id, "ex. …")


def _render_form_fields(template, form_data: dict) -> None:
    field_tips = {
        "coordinating_orgs": "Vous pouvez saisir plusieurs organismes, séparés par une virgule (,).",
        "recipient_title": "Saisissez le nom complet et le titre, séparés par |",
    }
    fields = [f for f in template.fields if _should_show_field(template, f)]
    index = 0
    while index < len(fields):
        field = fields[index]
        next_field = fields[index + 1] if index + 1 < len(fields) else None

        if field.id == "rank" and next_field and next_field.id == "job":
            col_rank, col_job = st.columns(2)
            with col_rank:
                form_data["rank"] = st.text_input(
                    _field_label(field),
                    value=_default_value(field),
                    key=f"field_v3_{template.id}_rank",
                    placeholder=_field_placeholder("rank"),
                )
            with col_job:
                form_data["job"] = st.text_input(
                    _field_label(next_field),
                    value=_default_value(next_field),
                    key=f"field_v3_{template.id}_job",
                    placeholder=_field_placeholder("job"),
                )
            index += 2
            continue

        if field.id == "date_from" and next_field and next_field.id == "date_to":
            col_from, col_to = st.columns(2)
            with col_from:
                start = st.date_input(
                    _field_label(field),
                    value=date.today().replace(month=1, day=1),
                    key=f"field_v3_{template.id}_date_from",
                    format="DD/MM/YYYY",
                )
            with col_to:
                end = st.date_input(
                    _field_label(next_field),
                    value=date.today(),
                    key=f"field_v3_{template.id}_date_to",
                    format="DD/MM/YYYY",
                )
            form_data["date_from"] = _format_fr_date(start)
            form_data["date_to"] = _format_fr_date(end)
            index += 2
            continue

        if field.id in {"date_from", "date_to", "issue_date"}:
            picked = st.date_input(
                _field_label(field),
                value=date.today(),
                key=f"field_v3_{template.id}_{field.id}",
                format="DD/MM/YYYY",
            )
            form_data[field.id] = _format_fr_date(picked)
            index += 1
            continue

        form_data[field.id] = st.text_input(
            _field_label(field),
            value=_default_value(field),
            key=f"field_v3_{template.id}_{field.id}",
            help=field_tips.get(field.id),
            placeholder=_field_placeholder(field.id),
        )
        index += 1


def _download_zip(outputs: list[Path], zip_name: str) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in outputs:
            path = Path(path)
            if path.suffix.lower() == ".pdf":
                archive.write(path, arcname=path.name)
                continue
            if path.suffix.lower() == ".docx":
                pdf_name = path.with_suffix(".pdf").name
                pdf_bytes = docx_to_pdf_bytes(path)
                pdf_path = path.with_suffix(".pdf")
                pdf_path.write_bytes(pdf_bytes)
                archive.writestr(pdf_name, pdf_bytes)
                continue
            archive.write(path, arcname=path.name)
    buffer.seek(0)
    st.download_button(
        label="Télécharger le ZIP (PDF)",
        data=buffer.getvalue(),
        file_name=zip_name,
        mime="application/zip",
        use_container_width=True,
        key=f"zip_{zip_name}",
    )


def _store_result(path: Path, output_format: str) -> None:
    st.session_state.last_result = {
        "path": path,
        "name": path.name,
        "format": output_format,
        "bytes": path.read_bytes(),
    }


def _render_hero() -> None:
    logos = []
    if FLAG_B64:
        logos.append(f'<img src="{FLAG_B64}" alt="Drapeau" />')
    if EMBLEM_B64:
        logos.append(f'<img src="{EMBLEM_B64}" alt="Emblème" />')
    if MINISTRY_B64:
        logos.append(f'<img src="{MINISTRY_B64}" alt="وزارة العدل" />')

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-inner">
            <div class="hero-logos">{''.join(logos)}</div>
            <div class="hero-titles">
              <p class="republic">الجمهورية الجزائرية الديمقراطية الشعبية</p>
              <p class="ministry">وزارة العدل</p>
              <p class="tagline">Générateur de certificats officiels · مولّد الشهادات الرسمية</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_preview_panel() -> None:
    st.markdown('<div class="preview-toolbar"><h3>Aperçu</h3></div>', unsafe_allow_html=True)

    result = st.session_state.last_result
    tool_col1, tool_col2, tool_col3 = st.columns([2, 2, 3])
    with tool_col1:
        st.caption("Zoom")
        st.session_state.preview_zoom = st.slider(
            "Zoom",
            min_value=0.6,
            max_value=1.8,
            value=float(st.session_state.preview_zoom),
            step=0.1,
            label_visibility="collapsed",
        )
    if result:
        pdf_name = Path(result["name"]).with_suffix(".pdf").name
        if result["format"] == "pdf":
            with tool_col3:
                st.download_button(
                    "Télécharger PDF",
                    data=result["bytes"],
                    file_name=result["name"],
                    mime="application/pdf",
                    use_container_width=True,
                    key="preview_download_pdf",
                )
        else:
            with tool_col2:
                st.download_button(
                    "DOCX",
                    data=result["bytes"],
                    file_name=result["name"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="preview_download_docx",
                )
            with tool_col3:
                try:
                    if "pdf_bytes" not in result or result.get("pdf_name") != pdf_name:
                        with st.spinner("Conversion PDF…"):
                            result["pdf_bytes"] = docx_to_pdf_bytes(result["path"])
                            result["pdf_name"] = pdf_name
                            st.session_state.last_result = result
                    st.download_button(
                        "Télécharger PDF",
                        data=result["pdf_bytes"],
                        file_name=pdf_name,
                        mime="application/pdf",
                        use_container_width=True,
                        key="preview_download_pdf",
                    )
                except Exception as exc:
                    st.caption(f"PDF indisponible : {exc}")

    if not result:
        st.markdown(
            """
            <div class="preview-empty">
                <strong>Aucun certificat généré</strong>
                <p style="margin-top:0.5rem;">Remplissez le formulaire puis cliquez sur<br><em>Générer le certificat</em></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    _status_badge(result["name"])
    try:
        with st.spinner("Préparation de l'aperçu…"):
            preview_png = document_to_png_bytes(
                result["path"],
                zoom=st.session_state.preview_zoom,
            )
        st.image(preview_png, use_container_width=True)
    except Exception as exc:
        st.warning(f"Aperçu image indisponible : {exc}")
        st.caption("Vous pouvez toujours télécharger le fichier généré.")


def _render_generate_tab() -> None:
    col_left, col_right = st.columns([5, 7], gap="large")

    with col_left:
        with st.container(border=True):
            tab_single, tab_batch = st.tabs(["Certificat unique", "Génération en lot"])

            with tab_single:
                _section_label("Modèle")
                selected = st.selectbox(
                    "Modèle",
                    options=list(template_labels.keys()),
                    label_visibility="collapsed",
                    key="single_template_select",
                )
                template_id = template_labels[selected]
                template = get_template(template_id)

                _section_label("Fichier source")
                _file_card(template.source_file, template.output_format)

                _section_label("Informations du bénéficiaire")
                with st.form("single_certificate_form"):
                    form_data: dict[str, str] = {}
                    _render_form_fields(template, form_data)
                    submitted = st.form_submit_button("Générer le certificat", use_container_width=True)

                if submitted:
                    try:
                        output_path = generate_certificate(template_id, form_data)
                        _store_result(output_path, template.output_format)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Erreur : {exc}")

            with tab_batch:
                _section_label("Modèle")
                batch_selected = st.selectbox(
                    "Modèle lot",
                    options=list(template_labels.keys()),
                    key="batch_template_select",
                    label_visibility="collapsed",
                )
                batch_template_id = template_labels[batch_selected]
                batch_template = get_template(batch_template_id)

                _section_label("Fichier source")
                _file_card(batch_template.source_file, batch_template.output_format)

                _section_label("Import Excel / CSV")
                st.download_button(
                    label="Télécharger le modèle Excel",
                    data=build_excel_template_bytes(batch_template_id),
                    file_name=f"modele_{batch_template_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="excel_template_download",
                )
                uploaded = st.file_uploader(
                    "Importer votre fichier",
                    type=["xlsx", "xlsm", "csv"],
                    label_visibility="collapsed",
                )
                if st.button("Générer tous les certificats", use_container_width=True, key="batch_run"):
                    if not uploaded:
                        st.warning("Veuillez importer un fichier Excel ou CSV.")
                    else:
                        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                        upload_path = OUTPUT_DIR / f"_upload_{uploaded.name}"
                        upload_path.write_bytes(uploaded.getvalue())
                        try:
                            with st.spinner("Génération et conversion PDF en cours…"):
                                outputs = generate_from_spreadsheet(batch_template_id, upload_path)
                                st.success(f"{len(outputs)} certificat(s) généré(s) en PDF.")
                                _download_zip(outputs, f"{batch_template_id}_certificats.zip")
                        except Exception as exc:
                            st.error(f"Erreur : {exc}")
                        finally:
                            upload_path.unlink(missing_ok=True)

                _section_label("Colonnes attendues")
                hints = []
                for field in batch_template.fields:
                    if not _should_show_field(batch_template, field):
                        continue
                    aliases = {
                        "recipient_name": "Nom, Nom complet",
                        "rank": "Grade",
                        "job": "Poste, Fonction",
                        "issue_date": "Date",
                        "recipient_title": "Nom complet | Titre",
                        "council_location": "Lieu du conseil",
                        "family_name": "Nom de la famille",
                        "rank_workplace": "Grade et lieu de travail",
                        "deceased_name": "Nom du défunt",
                        "training_field": "Domaine de formation",
                        "date_from": "Date de début (JJ/MM/AAAA)",
                        "date_to": "Date de fin (JJ/MM/AAAA)",
                        "coordinating_orgs": "Organismes coordinateurs (séparés par ,)",
                    }
                    hints.append(
                        f"<li><strong>{_field_label(field)}</strong> — {aliases.get(field.id, field.label_en)}</li>"
                    )
                st.markdown(f'<ul class="hint-list">{"".join(hints)}</ul>', unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            _render_preview_panel()


def _render_templates_tab() -> None:
    st.markdown(
        "Parcourez les modèles officiels et téléchargez les fichiers Excel pour l’import en lot "
        "(en-têtes + lignes d’exemple à remplacer)."
    )
    xlsx_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    for template in templates:
        source = TEMPLATES_DIR / template.source_file
        size_kb = source.stat().st_size / 1024 if source.exists() else 0
        fields = ", ".join(_field_label(f) for f in template.fields if _should_show_field(template, f))
        excel_path = BULK_DIR / f"modele_{template.id}.xlsx"
        excel_bytes = build_excel_template_bytes(template.id, with_examples=True)
        excel_path.write_bytes(excel_bytes)

        st.markdown(
            f"""
            <div class="template-card">
              <div class="tpl-badge">{template.output_format.upper()}</div>
              <div>
                <p class="tpl-ar">{template.name_ar}</p>
                <p class="tpl-title">{template.name_fr}</p>
                <p class="tpl-meta">{template.source_file} · {size_kb:.0f} Ko · Champs : {fields}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns([1, 1, 1])
        with cols[0]:
            if source.exists():
                mime = (
                    "application/pdf"
                    if source.suffix.lower() == ".pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                st.download_button(
                    "Modèle Word/PDF",
                    data=source.read_bytes(),
                    file_name=source.name,
                    mime=mime,
                    key=f"dl_tpl_{template.id}",
                    use_container_width=True,
                )
        with cols[1]:
            st.download_button(
                "Excel lot",
                data=excel_bytes,
                file_name=excel_path.name,
                mime=xlsx_mime,
                key=f"dl_xlsx_{template.id}",
                use_container_width=True,
                help="Modèle Excel avec colonnes et lignes d'exemple (remplacez-les par vos données)",
            )
        with cols[2]:
            if st.button("Aperçu", key=f"prev_tpl_{template.id}", use_container_width=True):
                try:
                    with st.spinner("Aperçu…"):
                        png = document_to_png_bytes(source, zoom=1.1)
                    st.session_state[f"tpl_preview_{template.id}"] = png
                except Exception as exc:
                    st.warning(f"Aperçu indisponible : {exc}")
        if f"tpl_preview_{template.id}" in st.session_state:
            st.image(st.session_state[f"tpl_preview_{template.id}"], use_container_width=True)


def _list_generated_files() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        p
        for p in OUTPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".docx", ".pdf"} and not p.name.startswith("_")
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def _render_generated_tab() -> None:
    files = _list_generated_files()
    top = st.columns([3, 1])
    with top[0]:
        st.caption(f"Dossier : `{OUTPUT_DIR}` — {len(files)} fichier(s)")
    with top[1]:
        if st.button("Actualiser", use_container_width=True, key="refresh_generated"):
            st.rerun()

    if not files:
        st.info("Aucun certificat généré pour le moment.")
        return

    filter_fmt = st.selectbox("Filtrer", ["Tous", "PDF", "DOCX"], key="gen_filter")
    for path in files:
        if filter_fmt == "PDF" and path.suffix.lower() != ".pdf":
            continue
        if filter_fmt == "DOCX" and path.suffix.lower() != ".docx":
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        st.markdown(
            f"""
            <div class="generated-card">
              <div class="tpl-badge">{path.suffix[1:].upper()}</div>
              <div>
                <p class="tpl-title">{path.name}</p>
                <p class="tpl-meta">{path.stat().st_size / 1024:.1f} Ko · {mtime}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            mime = (
                "application/pdf"
                if path.suffix.lower() == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.download_button(
                "Télécharger",
                data=path.read_bytes(),
                file_name=path.name,
                mime=mime,
                key=f"dl_gen_{path.name}",
                use_container_width=True,
            )
        with c2:
            if st.button("Aperçu", key=f"prev_gen_{path.name}", use_container_width=True):
                try:
                    with st.spinner("Aperçu…"):
                        st.session_state[f"gen_preview_{path.name}"] = document_to_png_bytes(path, zoom=1.1)
                except Exception as exc:
                    st.warning(f"Aperçu indisponible : {exc}")
        if f"gen_preview_{path.name}" in st.session_state:
            st.image(st.session_state[f"gen_preview_{path.name}"], use_container_width=True)


def _render_about_tab() -> None:
    lang = st.radio("Langue / اللغة", ["Français", "العربية"], horizontal=True, key="about_lang")

    if lang == "Français":
        st.markdown(
            """
            <div class="about-block">
              <h3>À propos</h3>
              <p>
                Application interne du <strong>Ministère de la Justice</strong> pour remplir
                automatiquement les modèles officiels : certificat de remerciement, condoléances,
                lettre de félicitations et certificat honorifique.
              </p>
              <p>
                Générez un certificat unique ou un lot via Excel, prévisualisez le résultat,
                puis téléchargez en DOCX et/ou PDF.
              </p>
            </div>
            <div class="about-block">
              <h3>Guide d’utilisation</h3>
              <ol>
                <li>Onglet <strong>Générer</strong> : choisissez le modèle et saisissez les informations.</li>
                <li>Pour les dates (remerciement), utilisez le calendrier.</li>
                <li>Cliquez sur <strong>Générer le certificat</strong> puis téléchargez DOCX/PDF.</li>
                <li>Pour un lot : téléchargez le modèle Excel, remplissez-le, importez-le — le ZIP contient les PDF.</li>
                <li>Onglet <strong>Modèles</strong> : consultez et téléchargez les fichiers sources.</li>
                <li>Onglet <strong>Certificats générés</strong> : retrouvez l’historique local.</li>
              </ol>
              <p><strong>Windows :</strong> double-cliquez sur <code>lancer_app.bat</code>,
              ou construisez un EXE avec <code>build_exe.bat</code>
              (Python 3.10+ et LibreOffice recommandés pour l’aperçu PDF).</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="about-block ar">
              <h3 class="ar">حول التطبيق</h3>
              <p>
                تطبيق داخلي لـ<strong>وزارة العدل</strong> لملء النماذج الرسمية تلقائياً:
                شهادة شكر وتقدير، تعزية، تهنئة، وشهادة شرفية.
              </p>
              <p>
                يمكن إنشاء شهادة واحدة أو دفعة عبر Excel، مع معاينة النتيجة وتحميلها بصيغتي DOCX وPDF.
              </p>
            </div>
            <div class="about-block ar">
              <h3 class="ar">دليل الاستخدام</h3>
              <ol>
                <li>تبويب <strong>إنشاء</strong>: اختر النموذج وأدخل البيانات.</li>
                <li>للتواريخ (شهادة الشكر) استخدم التقويم.</li>
                <li>اضغط <strong>إنشاء الشهادة</strong> ثم حمّل DOCX/PDF.</li>
                <li>للدفعة: حمّل نموذج Excel، املأه، ثم استورده — ملف ZIP يحتوي على ملفات PDF.</li>
                <li>تبويب <strong>النماذج</strong>: عرض وتحميل ملفات المصدر.</li>
                <li>تبويب <strong>الشهادات المُنشأة</strong>: سجل الملفات المحلية.</li>
              </ol>
              <p><strong>ويندوز:</strong> شغّل <code>lancer_app.bat</code>
              أو أنشئ ملف EXE عبر <code>build_exe.bat</code>
              (يُفضّل Python 3.10+ وLibreOffice للمعاينة).</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# —— Page layout ——
_render_hero()

tab_generate, tab_templates, tab_generated, tab_about = st.tabs(
    [
        "Générer un certificat",
        "Voir les modèles",
        "Certificats générés",
        "À propos",
    ]
)

with tab_generate:
    _render_generate_tab()

with tab_templates:
    with st.container(border=True):
        _render_templates_tab()

with tab_generated:
    with st.container(border=True):
        _render_generated_tab()

with tab_about:
    with st.container(border=True):
        _render_about_tab()

st.markdown(
    f'<p class="footer-note">وزارة العدل · Ministère de la Justice · {date.today().year}</p>',
    unsafe_allow_html=True,
)
