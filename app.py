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

    if profil == "chercheur":
        cards = resultat
        return render_template("resultat.html",
                             cards=cards,
                             sujet=sujet,
                             profil=profil,
                             nb_articles=nb_articles)

    elif profil == "veille":
        # resultat est déjà un dictionnaire structuré (intro, sections, articles_notables)
        intro_veille = resultat.get("intro", "")
        sections_veille = resultat.get("sections", [])
        articles_notables = resultat.get("articles_notables", [])
        auteurs_actifs = resultat.get("auteurs_actifs",[])
        a_retenir = resultat.get("a_retenir", "")


        return render_template("resultat.html",
                             intro_veille=intro_veille,
                             sections_veille=sections_veille,
                             articles_notables=articles_notables,
                             auteurs_actifs=auteurs_actifs,
                            a_retenir=a_retenir,
                             sujet=sujet,
                             profil=profil,
                             nb_articles=nb_articles)
                        

    else:
    
        # Ancien flux pour étudiant
        resultat_propre = resultat.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(resultat_propre)
            solutions = data.get("solutions", [])
            contexte = data.get("contexte", "")
            recommandation = data.get("recommandation", "")
        except json.JSONDecodeError:
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