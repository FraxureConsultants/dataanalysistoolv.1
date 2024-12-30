from flask import Flask, request, render_template, jsonify
import pandas as pd
import os
import chardet

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    analysis_result = None
    error_message = None
    uploaded_filename = None
    summary_statistics = None

    if request.method == "POST":
        if "file" in request.files:
            # Handle file upload
            file = request.files["file"]
            if file.filename == "":
                error_message = "No file selected."
            else:
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(file_path)
                uploaded_filename = file.filename
                try:
                    # Check file extension and read accordingly
                    if file.filename.endswith(".csv"):
                        try:
                            # Try reading CSV with default UTF-8 encoding
                            df = pd.read_csv(file_path)
                        except UnicodeDecodeError:
                            # Detect encoding as fallback
                            with open(file_path, "rb") as f:
                                raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]
                            df = pd.read_csv(file_path, encoding=detected_encoding)
                    elif file.filename.endswith((".xls", ".xlsx")):
                        # Read Excel file
                        df = pd.read_excel(file_path)
                    else:
                        raise ValueError("Unsupported file format. Please upload a .csv or .xlsx file.")

                    # Process file for column names and preview
                    analysis_result = {
                        "columns": df.columns.tolist(),
                        "preview": df.head().to_dict(orient="records"),
                    }

                    # Calculate summary statistics for numerical columns
                    summary_stats = df.describe().transpose().to_dict(orient="index")
                    summary_statistics = {
                        col: {stat: round(value, 2) for stat, value in stats.items()}
                        for col, stats in summary_stats.items()
                    }

                except Exception as e:
                    error_message = f"Error analyzing file: {str(e)}"

    return render_template(
        "index.html",
        analysis_result=analysis_result,
        error_message=error_message,
        uploaded_filename=uploaded_filename,
        summary_statistics=summary_statistics,
    )

if __name__ == "__main__":
    app.run(debug=True)
