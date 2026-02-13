from flask import Flask, request, jsonify, send_file, render_template
@app.route("/analyze", methods=["POST"])
def analyze():
file = request.files.get("file")


if not file:
return jsonify({"error": "No file uploaded"}), 400


job_id = str(uuid.uuid4())


input_path = os.path.join(UPLOAD_FOLDER, f"{job_id}.xlsx")
file.save(input_path)


evidence, pathways, output_excel = run_full_analysis(
input_path,
RESULT_FOLDER,
job_id
)


JOBS[job_id] = {
"evidence": evidence,
"pathways": pathways,
"excel": output_excel
}


return jsonify({"job_id": job_id})




@app.route("/evidence/<job_id>")
def evidence(job_id):
return jsonify(JOBS[job_id]["evidence"])




@app.route("/pathways/<job_id>")
def pathways(job_id):
return jsonify(JOBS[job_id]["pathways"])




@app.route("/download/<job_id>")
def download(job_id):
return send_file(JOBS[job_id]["excel"], as_attachment=True)




if __name__ == "__main__":
app.run(host="0.0.0.0", port=10000)
