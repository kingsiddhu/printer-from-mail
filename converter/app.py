import os
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "no file provided"}), 400

    upload = request.files["file"]
    filename = upload.filename
    if not filename:
        return jsonify({"error": "empty filename"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, filename)
        upload.save(in_path)

        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, in_path],
            capture_output=True,
            text=True,
        )

        out_path = str(Path(in_path).with_suffix(".pdf"))

        if result.returncode != 0 or not os.path.exists(out_path):
            return jsonify({"error": "conversion failed", "stderr": result.stderr}), 500

        return send_file(
            out_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=Path(out_path).name,
        )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)