from flask import Flask, render_template, request  # ✅ request ajouté

app = Flask(__name__)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/traitement", methods=["POST"])  # ✅ déplacé avant app.run()
def traitement():
    donnees = request.form
    nom = donnees.get('nom')
    mdp = donnees.get('mdp')
    if nom == 'admin' and mdp == '1234':
        return render_template("traitement.html", nom_utilisateur=nom)
    else:
        return render_template("traitement.html")


if __name__ == '__main__':
    app.run(debug=True)  # ✅ toujours en dernier