from flask import Flask, render_template, request, redirect, url_for
import re
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

SUBMISSIONS_DIR = Path("submissions")
SUBMISSIONS_DIR.mkdir(exist_ok=True)

@app.route("/form", methods=["GET", "POST"])
def form():
    data = {"full_name": "", "email": "", "age": "", "city": ""}
    errors = {}

    if request.method == "POST":
        data["full_name"] = request.form.get("full_name", "").strip()
        data["email"] = request.form.get("email", "").strip()
        data["age"] = request.form.get("age", "").strip()
        data["city"] = request.form.get("city", "").strip()

        for field, value in data.items():
            if not value:
                errors[field] = "Поле обов’язкове для заповнення."

        if data["email"] and not EMAIL_RE.match(data["email"]):
            errors["email"] = "Некоректний формат електронної адреси."

        if data["age"] and not data["age"].isdigit():
            errors["age"] = "Вік має містити лише цифри."

        if not errors:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"submission_{ts}.txt"
            filepath = SUBMISSIONS_DIR / filename

            with filepath.open("w", encoding="utf-8") as f:
                f.write(f"full_name: {data['full_name']}\n")
                f.write(f"email: {data['email']}\n")
                f.write(f"age: {data['age']}\n")
                f.write(f"city: {data['city']}\n")

            return redirect(url_for("result", **data, saved_file=filename))

    return render_template("form.html", data=data, errors=errors)

@app.route("/result")
def result():
    data = {
        "full_name": request.args.get("full_name", ""),
        "email": request.args.get("email", ""),
        "age": request.args.get("age", ""),
        "city": request.args.get("city", "")
    }
    saved_file = request.args.get("saved_file", "")
    return render_template("result.html", data=data, saved_file=saved_file)

if __name__ == "__main__":
    app.run(debug=True)
