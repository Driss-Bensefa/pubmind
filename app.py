from flask import Flask, render_template, request
import pubmind 
import markdown
import json

app= Flask(__name__)
@app.route("/")
def accueil():
    return render_template("index.html")


@app.route("/recherche", methods=["POST"])
def recherche():
    sujet = request.form["sujet"]
    nb_articles = int(request.form["nb_articles"])
    profil = request.form["profil"]

    resultat = pubmind.lancer_recherche(sujet, nb_articles, profil)

    # Enlever les backticks markdown
    resultat = resultat.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(resultat)
        solutions = data.get("solutions", [])
        contexte = data.get("contexte", "")
        recommandation = data.get("recommandation", "")
        print(f"✅ Nombre de solutions: {len(solutions)}")
    except json.JSONDecodeError as e:
        print(f"❌ ERREUR JSON: {e}")
        solutions = []
        contexte = resultat
        recommandation = ""

    return render_template("resultat.html",
                         contexte=contexte,
                         solutions=solutions,
                         recommandation=recommandation,
                         sujet=sujet,
                         profil=profil,
                         nb_articles=nb_articles)


if __name__ == "__main__":
    app.run(debug=True)