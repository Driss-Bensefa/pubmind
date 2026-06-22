# -*- coding: utf-8 -*-
# PubMind - Agent de veille scientifique
# Créé par Driss Bensefa
# Module 1 : Recherche PubMed

from Bio import Entrez
import os
from anthropic import Anthropic

client = Anthropic()

# Ton email pour identifier tes requêtes auprès du NCBI
Entrez.email = "driss.bensefa@gmail.com"

def rechercher_articles(sujet, nb_articles=5):
    print("recherche en cours pour : " + sujet, end="\r")
    handle = Entrez.esearch(db="pubmed", term= sujet, retmax=nb_articles)
    resultats = Entrez.read(handle)
    handle.close()
    print(" " * 50, end="\r")

    ids = resultats["IdList"]
    print("Articles trouvés : " + str(len(ids)))

    return ids 



def telecharger_articles(ids) : 
    print("telechargement des articles ...", end="\r")

    #on appel d'abord medline  
    handle_medline = Entrez.efetch(db="pubmed", id=ids, rettype="medline", retmode="text")
    medline = handle_medline.read()
    handle_medline.close()


    #on appel ensuite l'abstract 
    handle_abstract = Entrez.efetch(db="pubmed", id=ids,rettype="abstract", retmode="text")
    abstracts = handle_abstract.read()
    handle_abstract.close()

    contenu = "===METADONNEES ===\n" + medline +"\n\n===ABSTRACTS===\n"+abstracts
   
    print(" " * 50, end="\r")
    return contenu 



def synthese_ia(contenu, sujet, profil="chercheur", nb_articles=10):
    print("Analyse IA en cours...", end="\r")
    tokens_max = min(4000 + nb_articles * 150, 16000)

    mots_question = ["comment", "quel", "quels", "quelle", "quelles", "pourquoi", "est-ce que", "est-ce qu'"]
    est_question = profil == "chercheur" and any(mot in sujet.lower() for mot in mots_question)


# 1. Vérification sujet trop vague → on sort immédiatement
    if profil == "veille" and len(sujet.split()) < 2:
        return ("⚠️ Sujet trop large — précise ton domaine.\n"
                "Exemple : 'CRISPR base editing cancer 2024' au lieu de 'CRISPR'")
    prompts_veille_detail = f"""Tu es un expert en veille scientifique.
Effectue une veille détaillée sur : {sujet}

📅 PUBLICATIONS RÉCENTES
Pour chaque article, du plus récent au plus ancien :
- Numéro · Titre — Auteurs — Journal — Date
- Résumé en 4-5 phrases fluides expliquant contexte, méthode et impact
- 🔗 https://pubmed.ncbi.nlm.nih.gov/[PMID]

🚀 NOUVELLES TECHNIQUES ÉMERGENTES
- Techniques récentes dans ce domaine
- Comparaison avec anciennes approches

📈 TENDANCES DU DOMAINE
- Ce qui monte · Ce qui descend · Ce qui explose

🔮 PERSPECTIVES 2-3 ANS

💡 RÉSUMÉ VEILLE — 3 CHOSES À RETENIR

Articles à analyser :
{contenu}"""

    prompts_veille_moyen = f"""Tu es un expert en veille scientifique.
Effectue une veille sur : {sujet}

📌 5 ARTICLES INCONTOURNABLES
Sélectionne les 5 plus importants parmi tous les articles.
Pour chacun :
- Titre — Auteurs — Année
- Pourquoi incontournable : [1-2 phrases basées sur l'abstract]
- 🔗 lien

📅 PUBLICATIONS RÉCENTES
Pour chaque article, du plus récent au plus ancien :
- Numéro · Titre — Auteurs — Journal — Date
- Résumé en 1-2 phrases : résultat principal uniquement
- 🔗 https://pubmed.ncbi.nlm.nih.gov/[PMID]


🚀 NOUVELLES TECHNIQUES ÉMERGENTES

📈 TENDANCES DU DOMAINE
- Ce qui monte · Ce qui descend · Ce qui explose

🔮 PERSPECTIVES 2-3 ANS

💡 RÉSUMÉ VEILLE — 3 CHOSES À RETENIR

Articles à analyser :
{contenu}"""

    prompts_veille_agrege = f"""Tu es un expert en veille scientifique et bibliométrie.
Effectue une veille macro sur : {sujet}
Tu as analysé {nb_articles} articles — ne résume pas chaque article individuellement.
Identifie uniquement les patterns qui reviennent dans plusieurs articles.

📈 TENDANCES MAJEURES DU DOMAINE
- Ce qui monte · Ce qui descend · Ce qui explose

🚀 TECHNIQUES ÉMERGENTES
- Techniques apparues récemment
- Ce qu'elles remplacent et pourquoi

👥 GROUPES DE RECHERCHE ACTIFS
- Équipes/institutions qui publient le plus
- Pays les plus actifs
- Auteurs clés à suivre

📌 10 ARTICLES REPRÉSENTATIFS
Les 10 articles qui illustrent le mieux les tendances :
- Numéro · Titre — Auteurs — Année
- 🔗 https://pubmed.ncbi.nlm.nih.gov/[PMID]

🔮 PERSPECTIVES 2-3 ANS

💡 RÉSUMÉ MACRO — 3 CHOSES À RETENIR

Articles à analyser :
{contenu}"""

    prompt_veille = ""

    if profil == "veille":
        if nb_articles <= 10:
            prompt_veille = prompts_veille_detail
        elif nb_articles <= 50:
            prompt_veille = prompts_veille_moyen
        else:
            prompt_veille = prompts_veille_agrege



    prompt_chercheur_sujet = f"""Tu es un expert en bioinformatique et biologie moléculaire.
Analyse ces articles sur : {sujet}

Réponds EXACTEMENT dans ce format :

🔬 SYNTHÈSE DU DOMAINE (4-5 lignes niveau expert)
Synthèse approfondie des grandes tendances, consensus actuels et enjeux du domaine.

🧬 GÈNES, PROTÉINES & VOIES MOLÉCULAIRES
Pour chaque élément : nom, fonction, voie de signalisation, interactions clés, contexte pathologique si pertinent.

⚙️ MÉTHODOLOGIES DÉTAILLÉES
Pour chaque méthode :
- Protocole step-by-step
- Conditions expérimentales (température, durée, concentrations)
- Matériel requis
- Paramètres critiques à maîtriser

📊 RÉSULTATS CLÉS & DONNÉES CHIFFRÉES
Statistiques, valeurs numériques, p-values, fold-change, comparaisons quantitatives entre études.

🔄 REPRODUCTIBILITÉ EN LABO
- Ce qui est faisable dans un labo standard équipé
- Ce qui nécessite du matériel spécialisé (listez lequel)
- Points de vigilance pour la reproductibilité

❓ QUESTIONS OUVERTES DU DOMAINE
Ce qui n'est pas encore résolu, les contradictions dans la littérature, les lacunes méthodologiques.

📚 ARTICLES CLÉS
Pour chaque article important :
- Auteurs — Journal — Année
- 📍 Section clé : [Introduction / Methods / Results / Discussion]
- "[Citation exacte de la phrase clé de l'article]"
- 🔗 https://pubmed.ncbi.nlm.nih.gov/[PMID]

💡 CONSEIL PRATIQUE EXPERT
"Si tu veux reproduire/implémenter ceci, voilà par où commencer concrètement : [étapes, ressources, pièges à éviter]"

Articles à analyser :
{contenu}"""

    prompt_chercheur_question = f"""Tu es un expert en bioinformatique et biologie moléculaire.
Un chercheur te pose cette question précise : {sujet}

Analyse ces articles scientifiques et identifie les 3 meilleures solutions/réponses.

Réponds EXACTEMENT dans ce format :

🌍 CONTEXTE EXPERT (2-3 lignes)
État de l'art actuel sur cette question précise, consensus et controverses dans la littérature.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP 3 SOLUTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🥇 SOLUTION 1 : [Nom de la solution/méthode]

⭐ SCORE DE PERTINENCE : XX/100
Justification du score :
- [Critère 1 en lien direct avec la question] ✅ ou ❌
- [Critère 2] ✅ ou ❌
- [Critère 3] ✅ ou ❌

📄 CONTEXTE DE L'ARTICLE
"[Décris en 3-4 lignes comment cet article utilise cette approche, dans quel contexte expérimental, sur quel modèle, avec quels résultats principaux et données chiffrées]"

📍 LOCALISATION DANS L'ARTICLE
- Section : [Introduction / Methods / Results / Discussion]
- Sous-section : [Nom exact de la sous-section]
- "[Citation exacte de la phrase clé de l'article]"

⚙️ PROTOCOLE DÉTAILLÉ
- Étape 1 : [description précise]
- Étape 2 : [description précise]
- Paramètres critiques : [valeurs, concentrations, durées]
- Matériel requis : [liste]

✅ AVANTAGES
- [Avantage 1 avec données chiffrées si disponibles]
- [Avantage 2]
- [Avantage 3]

❌ INCONVÉNIENTS
- [Inconvénient 1]
- [Inconvénient 2]

🎯 CONSEIL PERSONNALISÉ EXPERT
"Pour ton cas précis — [reformule la question du chercheur] —
[conseil concret et actionnable, adapté exactement à la question posée, basé sur les données de l'article]"

🔗 [Auteurs] — [Journal] [Année]
https://pubmed.ncbi.nlm.nih.gov/[PMID]

───────────────────────────────

🥈 SOLUTION 2 : [Nom de la solution/méthode]
[Même structure que Solution 1]

───────────────────────────────

🥉 SOLUTION 3 : [Nom de la solution/méthode]
[Même structure que Solution 1]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️ COMPARAISON DES 3 SOLUTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Critère          | Solution 1 | Solution 2 | Solution 3 |
|------------------|------------|------------|------------|
| Efficacité       |    ⭐⭐⭐    |    ⭐⭐      |    ⭐⭐⭐    |
| Coût             |    💰💰     |    💰      |    💰💰💰   |
| Difficulté       |    🔴       |    🟡      |    🟢      |
| Délai résultat   |    3 sem    |    1 sem   |    2 sem   |
| Reproductibilité |    ⭐⭐⭐    |    ⭐⭐      |    ⭐       |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 RECOMMANDATION FINALE EXPERTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Pour ton cas précis — [reformule la question] —
nous recommandons [Solution X] avec un score de XX/100 car :
- [Raison 1 avec données chiffrées]
- [Raison 2]
- [Raison 3]

Point de vigilance : [conseil important à ne pas oublier]"

Articles à analyser :
{contenu}"""

   
   
   
   
   
   
   
   
    prompts = {
        "chercheur": prompt_chercheur_question if est_question else prompt_chercheur_sujet,

     "etudiant": f"""Tu es un tuteur en bioinformatique et en biologie.
Explique ces articles sur : {sujet} de façon pédagogique pour un étudiant en licence/master.
Utilise un langage simple, explique les termes techniques.

Réponds EXACTEMENT dans ce format :

📚 RÉSUMÉ SIMPLIFIÉ (3-4 lignes)
Explique comme si j'avais 20 ans et peu d'expérience.

🧬 GÈNES & PROTÉINES (avec explication simple)
Ex: BRCA1 = gène suppresseur de tumeur impliqué dans le cancer du sein

🦠 MALADIES ÉTUDIÉES
Liste et explique brièvement chaque maladie.

⚙️ TECHNIQUES UTILISÉES (avec explication)
Ex: CRISPR = outil qui permet de couper et modifier l'ADN

📖 CE QUE DISENT LES ARTICLES
Pour chaque article important :
- Auteurs — Journal — Année
- 💬 En langage simple : ce que les chercheurs ont découvert
- 📍 Où dans l'article : Introduction / Résultats / Discussion
- 🔗 https://pubmed.ncbi.nlm.nih.gov/[PMID]

💡 CE QUE JE DOIS RETENIR
Une phrase simple et claire.

Articles à analyser :
{contenu}""",












     "reviewer": f"""Tu es un reviewer scientifique de haut niveau
pour un journal international (Nature, Cell, Science).
Effectue une évaluation critique et rigoureuse de ces articles sur : {sujet}

Réponds EXACTEMENT dans ce format :

🌍 CONTEXTE DE L'ÉVALUATION
- Importance de ce sujet dans la recherche actuelle
- Nombre d'articles évalués
- Qualité globale du corpus (1-2 lignes)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ÉVALUATION DE CHAQUE ARTICLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pour CHAQUE article, réponds dans ce format :

📄 ARTICLE : [Titre court]
Auteurs — Journal — Année

⭐ SCORE GLOBAL : X/10

1️⃣ PERTINENCE DE LA QUESTION SCIENTIFIQUE : X/10
→ [La question est-elle originale et importante pour le domaine ?]

2️⃣ QUALITÉ MÉTHODOLOGIQUE : X/10
→ [Les expériences sont-elles bien conçues ? Les contrôles sont-ils présents ?]
→ [L'échantillon est-il suffisant ?]

3️⃣ SOLIDITÉ DES RÉSULTATS & STATISTIQUES : X/10
→ [Les données supportent-elles les conclusions ?]
→ [Les tests statistiques sont-ils appropriés ?]

4️⃣ REPRODUCTIBILITÉ : X/10
→ [Peut-on refaire l'expérience avec ce qui est décrit ?]
→ [Les données brutes sont-elles disponibles ?]

5️⃣ CONFLITS D'INTÉRÊTS : ✅ Aucun / ⚠️ Déclaré / 🚩 Problématique
→ [Qui finance l'étude ? Biais possible ?]

6️⃣ IMPACT SUR LE DOMAINE : X/10
→ [Est-ce que ça avance vraiment le domaine ?]
→ [Citations potentielles, applications cliniques ?]

💬 VERDICT FINAL
✅ ACCEPTER / ⚠️ RÉVISIONS MAJEURES / ❌ REJETER
→ [Justification en 2-3 lignes]

🔗 https://pubmed.ncbi.nlm.nih.gov/[PMID]

───────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 BILAN GLOBAL DU CORPUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Critère                    | Score moyen |
|----------------------------|-------------|
| Pertinence scientifique    |    X/10     |
| Qualité méthodologique     |    X/10     |
| Solidité des résultats     |    X/10     |
| Reproductibilité           |    X/10     |
| Impact sur le domaine      |    X/10     |
| SCORE GLOBAL               |    X/10     |

⭐ TOP ARTICLE DU CORPUS
→ [Titre] — Score X/10
→ [Pourquoi c'est le meilleur]
→ 🔗 lien

🗑️ ARTICLE LE PLUS FAIBLE
→ [Titre] — Score X/10
→ [Pourquoi il est le plus faible]
→ 🔗 lien

💡 RECOMMANDATION FINALE
→ [Synthèse critique du domaine en 3-4 lignes]
→ [Quelles questions restent ouvertes ?]
→ [Quelles expériences manquent dans la littérature ?]

Articles à analyser :
{contenu}""",











     "veille": prompt_veille,
    }


    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=tokens_max,
        messages=[
            {
                "role": "user",
                "content": prompts[profil]
            }
        ]
    )

    print(" " * 50, end="\r")
    return message.content[0].text

def optimiser_requete(sujet):

    print("Optimisation de la requête en cours...", end="\r")
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Tu es un expert en recherche bibliographique PubMed. Transforme ce texte en une requête PubMed optimisée en utilisant la syntaxe avancée : opérateurs booléens AND/OR/NOT, guillemets pour les expressions exactes, filtres de champs [gene], [author], [journal], [tiab], [pt]. Maximum 1 requête concise et précise, sans explication. Texte à transformer : " + sujet
            }
        ]
    )

    print(" " * 50, end="\r")
    requete_optimisee = message.content[0].text.replace("```", "").strip()
    print("Requête optimisée : " + requete_optimisee)
    return requete_optimisee







def lancer_recherche(sujet, nb_articles=5, profil="chercheur"):
    print("=== PubMind ===")
    print("sujet : " + sujet)
    print("profil : " + profil)
    print("================")

    requete = optimiser_requete(sujet)
    ids = rechercher_articles(requete, nb_articles)

    if len(ids) == 0:
        return ("⚠️ Aucun article trouvé pour cette recherche.\n"
                "Essaie une requête plus large ou reformule ta question.")

    contenu = telecharger_articles(ids)
    synthese = synthese_ia(contenu, sujet, profil,nb_articles)


    return(synthese)
    

#different type de profil ( reponse adaptée en fonction du profil)

# Pour un chercheur (défaut, détecte auto sujet général vs question précise)
# Pour un étudiant  --> ("CRISPR cancer", 3, profil="etudiant")
# Pour un reviewer  --> ("CRISPR cancer", 3, profil="reviewer")
# Question précise  --> ("comment optimiser le CRISPR dans les cellules souches ?", 10, profil="chercheur")
# Veille            --> ("CRISPR base editing cancer 2024", 20, profil="veille")

if __name__ == "__main__":
    lancer_recherche("CRISPR cancer 2024", 5, profil="veille")


