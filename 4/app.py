from flask import Flask, render_template
app = Flask(__name__)

@app.route("/hello/<name>")
def hello(name):
    return render_template("hello.html.j2", name=name)

@app.route("/")
def index():
    return "<h1>Привіт із Flask!</h1>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
