import pandas as pd


return "\n".join(text_data)




# -------- MAIN ANALYSIS --------


def run_full_analysis(input_excel, result_folder, job_id):


df = pd.read_excel(input_excel)


metabolites = df.iloc[:, 0].dropna().tolist()


evidence_rows = []
pathway_rows = []


# ---- Simulated analysis ----
# Replace with PubMed / NLP / pathway DB later


for met in metabolites:


evidence_rows.append({
"Metabolite": met,
"Evidence": "Detected in placenta",
"PMID": "Auto-linked"
})


pathway_rows.append({
"Metabolite": met,
"Pathway": "Metabolic pathway example"
})


evidence_df = pd.DataFrame(evidence_rows)
pathway_df = pd.DataFrame(pathway_rows)


# ---- Remove unwanted columns if present ----
drop_cols = [
"metabolic_process",
"evidence_type",
"pathway_placenta_evidence"
]


evidence_df = evidence_df.drop(columns=[c for c in drop_cols if c in evidence_df.columns], errors="ignore")
pathway_df = pathway_df.drop(columns=[c for c in drop_cols if c in pathway_df.columns], errors="ignore")


# ---- Save Excel ----
output_path = os.path.join(result_folder, f"{job_id}_results.xlsx")


with pd.ExcelWriter(output_path) as writer:
evidence_df.to_excel(writer, sheet_name="Evidence", index=False)
pathway_df.to_excel(writer, sheet_name="Pathways", index=False)


return (
evidence_df.to_dict(orient="records"),
pathway_df.to_dict(orient="records"),
output_path
)
