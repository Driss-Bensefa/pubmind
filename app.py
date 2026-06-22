from flask import Flask, render_template, request
import pubmind 
import markdown

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
    resultat = markdown.markdown(resultat, extensions=["tables"])

    return render_template("resultat.html",resultat=resultat,sujet=sujet,profil=profil,nb_articles=nb_articles)  

if __name__ == "__main__":
    app.run(debug=True)