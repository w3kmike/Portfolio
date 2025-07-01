from flask import Flask, render_template_string, request, send_file
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from io import BytesIO
import datetime

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contractor Invoice Generator</title>
    <style>
    * {
        -webkit-font-smoothing: subpixel-antialiased;
        -moz-osx-font-smoothing: antialiased;
     }
        body {
            background-color: #121212;
            color: #E0E0E0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            -webkit-font-smoothing: subpixel-antialiased;
        }

        .container {
            margin-top: 40px;
            width: 90%;
            max-width: 600px;
            background-color: #1E1E1E;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
        }

        h2 {
            text-align: center;
            margin-bottom: 30px;
            color: #03DAC6;
        }

        label {
            display: block;
            margin: 12px 0 4px;
            font-weight: 600;
        }

        input, select, textarea {
            width: 100%;
            padding: 10px;
            background: #2C2C2C;
            color: #E0E0E0;
            border: 1px solid #444;
            border-radius: 6px;
            font-size: 14px;
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        button {
            margin-top: 20px;
            width: 100%;
            padding: 12px;
            background-color: #03DAC6;
            color: #000;
            border: none;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            transition: background 0.3s ease;
            cursor: pointer;
        }

        button:hover {
            background-color: #018786;
        }
    </style>
    <script>
        function toggleFields() {
            const model = document.getElementById("billing_model").value;
            document.getElementById("hourly_fields").style.display = model.includes("hourly") ? "block" : "none";
            document.getElementById("sprint_fields").style.display = model === "sprint" ? "block" : "none";
            document.getElementById("milestone_fields").style.display = model === "milestone" ? "block" : "none";
            document.getElementById("retainer_fields").style.display = model.includes("retainer") ? "block" : "none";
        }

        window.onload = toggleFields;
    </script>
</head>
<body>
    <div class="container">
        <h2>Invoice Generator</h2>
        <form method="post">
            <label>Client Name:</label>
            <input type="text" name="client_name" required>

            <label>Invoice Date:</label>
            <input type="date" name="invoice_date" value="{{ today }}" required>

            <label>Billing Model:</label>
            <select name="billing_model" id="billing_model" onchange="toggleFields()">
                <option value="hourly">Hourly</option>
                <option value="sprint">Bi-Weekly Sprint</option>
                <option value="milestone">Milestone-Based</option>
                <option value="retainer">Retainer Only</option>
                <option value="retainer+hourly">Retainer + Hourly</option>
                <option value="retainer+milestone">Retainer + Milestone</option>
            </select>

            <div id="hourly_fields" style="display: block;">
                <label>Hourly Rate ($):</label>
                <input type="number" name="hourly_rate" step="0.01">
                <label>Total Hours:</label>
                <input type="number" name="total_hours" step="0.1">
            </div>

            <div id="sprint_fields" style="display: none;">
                <label>Bi-Weekly Sprint Fee ($):</label>
                <input type="number" name="sprint_fee" step="0.01">
            </div>

            <div id="milestone_fields" style="display: none;">
                <label>Milestone Description:</label>
                <textarea name="milestone_desc"></textarea>
                <label>Milestone Fee ($):</label>
                <input type="number" name="milestone_fee" step="0.01">
            </div>

            <div id="retainer_fields" style="display: none;">
                <label>Retainer Fee ($):</label>
                <input type="number" name="retainer_fee" step="0.01">
            </div>

            <label>Additional Notes:</label>
            <textarea name="notes" placeholder="Optional notes for the client or service details..."></textarea>

            <button type="submit">Generate Invoice</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def invoice():
    if request.method == "POST":
        data = request.form
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=LETTER)
        width, height = LETTER

        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Consulting Invoice")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, f"Date: {data['invoice_date']}")
        p.drawString(50, height - 85, f"To: {data['client_name']}")

        y = height - 120
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Billing Details")
        p.setFont("Helvetica", 10)
        y -= 20

        total = 0.0
        model = data['billing_model']

        if "retainer" in model:
            fee = float(data.get('retainer_fee', 0))
            total += fee
            p.drawString(50, y, f"Retainer Fee: ${fee:,.2f}")
            y -= 20

        if model == "hourly" or model == "retainer+hourly":
            rate = float(data.get('hourly_rate', 0))
            hours = float(data.get('total_hours', 0))
            fee = rate * hours
            total += fee
            p.drawString(50, y, f"Hourly Work: {hours} hrs x ${rate:.2f} = ${fee:,.2f}")
            y -= 20

        if model == "sprint":
            fee = float(data.get('sprint_fee', 0))
            total += fee
            p.drawString(50, y, f"Bi-Weekly Sprint Fee: ${fee:,.2f}")
            y -= 20

        if model == "milestone" or model == "retainer+milestone":
            desc = data.get('milestone_desc', '')
            fee = float(data.get('milestone_fee', 0))
            total += fee
            p.drawString(50, y, f"Milestone Work: {desc} = ${fee:,.2f}")
            y -= 20

        # Total
        p.setFont("Helvetica-Bold", 12)
        y -= 10
        p.drawString(50, y, f"Total Due: ${total:,.2f}")
        y -= 30

        # Notes
        notes = data.get("notes", "")
        if notes.strip():
            p.setFont("Helvetica", 10)
            p.drawString(50, y, "Notes:")
            y -= 15
            for line in notes.split("\n"):
                p.drawString(60, y, line.strip())
                y -= 15

        # Footer - Legal Disclosures
        y -= 40
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Legal Disclosures:")
        y -= 15
        p.setFont("Helvetica-Oblique", 8)

        legal_lines = [
            "Consultant services are provided as-is and do not constitute legal, tax, or investment advice.",
            "Client is solely responsible for decisions and regulatory compliance based on deliverables.",
            "All final deliverables become property of the client upon full payment.",
            "Consultant retains ownership of tools, frameworks, and methodologies used during engagement.",
            "Confidentiality is maintained per the signed agreement; misuse may result in legal action.",
            "Late payments are subject to a 1.5% monthly interest and may pause service delivery.",
            "By accepting this invoice, Client agrees to the terms outlined in the signed Consulting Agreement.",
            "Consultant liability is strictly limited to total fees paid under this engagement."
        ]

        for line in legal_lines:
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica-Oblique", 8)
            p.drawString(50, y, line)
            y -= 12

        p.save()

        buffer.seek(0)
        filename = f"Invoice_{data['client_name'].replace(' ', '_')}_{data['invoice_date']}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

    return render_template_string(HTML_FORM, today=datetime.date.today().isoformat())

if __name__ == "__main__":
    app.run(debug=True)
