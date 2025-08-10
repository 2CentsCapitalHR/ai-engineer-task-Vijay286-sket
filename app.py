import io
import os
import json
import time
import zipfile
from typing import List, Dict, Any

import streamlit as st

from src.document_parser import extract_text
from src.analyzer import identify_document_type, basic_issue_scan
from src.checklist import infer_process, required_for_process
from src.comment_inserter import annotate_visible_notes
from src.report_generator import build_report
from src.rag_store import RAGStore, RAGConfig
from src.ingest import discover_and_read
from src.fetch_refs import download_refs
from src.llm_groq import analyze_doc_with_citations as groq_analyze, DEFAULT_MODEL as GROQ_DEFAULT
from src.llm_gemini import analyze_doc_with_citations as gemini_analyze, DEFAULT_MODEL as GEMINI_DEFAULT
from src.demo_samples import generate_samples


def main() -> None:
    st.set_page_config(page_title="ADGM Corporate Agent (Preview)")
    st.title("ADGM-Compliant Corporate Agent – Preview")
    st.caption("Upload .docx files to get a quick checklist and basic red-flag scan. This is a minimal scaffold.")

    with st.sidebar:
        st.header("References")
        ref_dir = st.text_input("Reference folder (PDF/HTML/TXT)", value="refs")
        k_results = st.slider("Citations per issue", min_value=0, max_value=5, value=2)
        ingest_clicked = st.button("Ingest/Refresh references")
        st.caption("Index PDFs/HTML/TXT from the folder for RAG citations.")
        if st.button("Quick add official links"):
            added = download_refs(ref_dir or "refs")
            st.toast(f"Downloaded {added} pages into {ref_dir or 'refs'}")
            st.caption("Fetch official ADGM pages into the reference folder.")

        st.header("LLM Provider")
        provider = st.selectbox("Provider", options=["None", "Groq", "Gemini"], index=0)
        if provider == "Groq":
            groq_models = list(dict.fromkeys([
                GROQ_DEFAULT,
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
                "llama-guard-3-8b",
            ]))
            model_name = st.selectbox("Groq model", options=groq_models, index=0)
            groq_key = st.text_input("GROQ_API_KEY", type="password")
        elif provider == "Gemini":
            gemini_models = list(dict.fromkeys([
                GEMINI_DEFAULT,
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-8b",
            ]))
            model_name = st.selectbox("Gemini model", options=gemini_models, index=0)
            gemini_key = st.text_input("GEMINI_API_KEY", type="password")
        else:
            model_name = ""
        temperature = st.slider("LLM temperature", 0.0, 1.0, 0.2)

        st.header("Demo")
        if st.button("Generate sample .docx files"):
            paths = generate_samples()
            st.toast(f"Generated {len(paths)} sample files in 'sample_docs/'")
        st.caption("Create example documents in sample_docs/ for quick testing.")

    # Initialize RAG store in session
    if "rag" not in st.session_state:
        st.session_state["rag"] = RAGStore(RAGConfig())
    rag: RAGStore = st.session_state["rag"]

    if ingest_clicked:
        docs = discover_and_read(ref_dir) if ref_dir else []
        if not docs:
            st.sidebar.warning("No readable files found. Supported: .pdf, .html, .txt")
        else:
            texts = [t[1] for t in docs]
            metas = [{"path": t[0]} for t in docs]
            ids = [f"ref_{i}" for i in range(len(docs))]
            rag.add_texts(texts, metas, ids)
            st.sidebar.success(f"Indexed {len(texts)} chunks")

    uploaded_files = st.file_uploader("Upload .docx documents", type=["docx"], accept_multiple_files=True)

    if not uploaded_files:
        st.info("Upload one or more .docx files to begin.")
        return

    doc_entries = []
    for f in uploaded_files:
        content = f.read()
        text = extract_text(content)
        doc_type = identify_document_type(text)
        issues = basic_issue_scan(text)
        # attach citations for heuristic issues
        if issues:
            for issue in issues:
                prompt = issue.get("issue", "") + " " + issue.get("suggestion", "")
                hits = rag.search(prompt, k=k_results) if k_results > 0 else []
                if hits:
                    issue["citations"] = [
                        {"snippet": h["text"][:240], "source": h["metadata"].get("path", "")}
                        for h in hits
                    ]

        # optional Groq LLM pass with RAG context
        if provider in ("Groq", "Gemini"):
            seed_ctx = []
            if k_results > 0:
                hits = rag.search(doc_type + " " + (issues[0]["issue"] if issues else ""), k=k_results)
                seed_ctx = [
                    {"snippet": h["text"][:400], "source": h["metadata"].get("path", "")}
                    for h in hits
                ]
            try:
                if provider == "Groq":
                    llm_issues = groq_analyze(text, seed_ctx, model=model_name, temperature=temperature, api_key=groq_key)
                else:
                    llm_issues = gemini_analyze(text, seed_ctx, model=model_name, temperature=temperature, api_key=gemini_key)
                # Merge unique issues
                existing = {(i.get("issue"), i.get("suggestion")) for i in issues}
                for li in llm_issues:
                    key = (li.get("issue"), li.get("suggestion"))
                    if key not in existing:
                        issues.append({
                            "issue": li.get("issue", ""),
                            "severity": li.get("severity", "Medium"),
                            "suggestion": li.get("suggestion", ""),
                            "section": li.get("section"),
                            "citations": seed_ctx,
                        })
            except Exception as e:
                st.warning(f"LLM analysis skipped: {e}")
        doc_entries.append({
            "name": f.name,
            "bytes": content,
            "type": doc_type,
            "issues": issues,
        })

    process = infer_process([d["type"] for d in doc_entries])
    required = required_for_process(process)

    present_types = set(d["type"] for d in doc_entries)
    missing = [r for r in required if r not in present_types]

    st.subheader("Process Inference")
    st.write(process if process != "Unknown" else "Unknown – upload more formation documents for better inference.")

    st.subheader("Checklist Verification")
    st.write({
        "documents_uploaded": len(doc_entries),
        "required_documents": len(required),
        "missing_documents": missing,
    })

    st.subheader("Per-Document Issues")
    for d in doc_entries:
        with st.expander(f"{d['name']} – {d['type']}"):
            if not d["issues"]:
                st.write("No basic issues found by the scaffold.")
            else:
                st.json(d["issues"])

    # Build a consolidated report
    report = build_report(process, doc_entries, required)

    st.subheader("Structured Report")
    st.json(report)

    # Provide annotated downloads for each doc
    st.subheader("Reviewed Documents (.docx)")
    for d in doc_entries:
        comment_texts = [f"{i['severity']}: {i['issue']} – {i['suggestion']}" for i in d["issues"]]
        reviewed_bytes = annotate_visible_notes(d["bytes"], comment_texts)
        st.download_button(
            label=f"Download reviewed – {d['name']}",
            data=reviewed_bytes,
            file_name=d["name"].replace(".docx", "_reviewed.docx"),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # Issue overview (simple counts)
    st.subheader("Issue Overview")
    severity_counts: Dict[str, int] = {}
    for d in doc_entries:
        for i in d["issues"]:
            sev = i.get("severity", "Unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
    if severity_counts:
        st.write(severity_counts)
    else:
        st.write("No issues detected by the scaffold.")

    # Export options
    st.subheader("Export")
    report_bytes = json.dumps(report, indent=2).encode("utf-8")
    st.download_button(
        label="Download JSON report",
        data=report_bytes,
        file_name="report.json",
        mime="application/json",
    )

    # Build ZIP with report + reviewed docs
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.json", report_bytes)
        for d in doc_entries:
            comment_texts = [f"{i['severity']}: {i['issue']} – {i['suggestion']}" for i in d["issues"]]
            reviewed_bytes = annotate_visible_notes(d["bytes"], comment_texts)
            zf.writestr(d["name"].replace(".docx", "_reviewed.docx"), reviewed_bytes)
    st.download_button(
        label="Download ZIP (report + reviewed docs)",
        data=zip_buffer.getvalue(),
        file_name="reviewed_outputs.zip",
        mime="application/zip",
    )

    # Save to outputs/ on disk
    if st.button("Save outputs to disk"):
        ts = time.strftime("%Y%m%d-%H%M%S")
        out_dir = os.path.join("outputs", f"session-{ts}")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "report.json"), "wb") as f:
            f.write(report_bytes)
        for d in doc_entries:
            comment_texts = [f"{i['severity']}: {i['issue']} – {i['suggestion']}" for i in d["issues"]]
            reviewed_bytes = annotate_visible_notes(d["bytes"], comment_texts)
            with open(os.path.join(out_dir, d["name"].replace(".docx", "_reviewed.docx")), "wb") as f:
                f.write(reviewed_bytes)
        st.success(f"Saved to {out_dir}")


if __name__ == "__main__":
    main()


