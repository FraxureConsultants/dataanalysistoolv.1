from flask import Flask, request, render_template, jsonify
import pandas as pd
import os
import chardet
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

current_dataframe = None  # Global variable to store the uploaded dataframe

@app.route("/", methods=["GET", "POST"])
def index():
    global current_dataframe
    analysis_result = None
    error_message = None
    uploaded_filename = None
    summary_statistics = None
    visualization_image = None

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

                    # Store the dataframe for visualization
                    current_dataframe = df

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

        elif "visualize" in request.form and current_dataframe is not None:
            # Handle visualization generation
            x_column = request.form.get("x_column")
            y_column = request.form.get("y_column")
            chart_type = request.form.get("chart_type")
            chart_color = request.form.get("chart_color", "blue")
            show_percentage = request.form.get("show_percentage") == "on"

            if x_column and (y_column or chart_type == "pie"):
                try:
                    plt.figure(figsize=(10, 6))
                    if chart_type == "bar":
                        if show_percentage:
                            counts = current_dataframe[x_column].value_counts(normalize=True) * 100
                            sns.barplot(x=counts.index, y=counts.values, color=chart_color)
                            plt.ylabel("Percentage")
                        else:
                            sns.barplot(data=current_dataframe, x=x_column, y=y_column, color=chart_color)
                    elif chart_type == "line":
                        sns.lineplot(data=current_dataframe, x=x_column, y=y_column, color=chart_color)
                    elif chart_type == "pie":
                        pie_data = current_dataframe[x_column].value_counts(normalize=show_percentage)
                        pie_labels = pie_data.index
                        plt.pie(pie_data, labels=pie_labels, autopct='%1.1f%%' if show_percentage else None, colors=[chart_color])
                        plt.axis('equal')
                    plt.title(f"{chart_type.capitalize()} of {y_column} vs {x_column}" if y_column else f"{chart_type.capitalize()} of {x_column}")
                    plt.tight_layout()

                    # Save the plot to a BytesIO object
                    img = io.BytesIO()
                    plt.savefig(img, format="png")
                    img.seek(0)
                    visualization_image = base64.b64encode(img.getvalue()).decode("utf-8")
                    plt.close()
                except Exception as e:
                    error_message = f"Error generating visualization: {str(e)}"

    return render_template(
        "index.html",
        analysis_result=analysis_result,
        error_message=error_message,
        uploaded_filename=uploaded_filename,
        summary_statistics=summary_statistics,
        visualization_image=visualization_image,
    )


if __name__ == "__main__":
    app.run(debug=True)
