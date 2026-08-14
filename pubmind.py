# -*- coding: utf-8 -*-
# PubMind - Agent de veille scientifique
# Créé par Driss Bensefa
# Module 1 : Recherche PubMed

from Bio import Entrez
import os
import json
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


def parser_articles(contenu):
    morceaux = contenu.split("\nPMID-")   # découpe en morceaux
    morceaux = morceaux[1:]               # jette le parasite

    liste_articles = []                         # panier vide

    for morceau in morceaux:              
        lignes = morceau.split("\n")      
        pmid = lignes[0].strip()          
        titre = ""                        
        dans_titre = False 
        type_article = "ARTICLE"        
        date = ""   
        journal = ""   
        doi = "" 
        auteurs_liste = []
        abstract = ""
        dans_abstract = False

        for ligne in lignes:    

            if ligne.startswith("TI  -"): 
                titre = ligne[6:]             
                dans_titre = True
            elif dans_titre and ligne.startswith("      "):
                titre = titre + " " + ligne.strip()          
            elif dans_titre :
                dans_titre = False

            if ligne.startswith("PT  - Review"):
                type_article = "REVIEW"
            
            if ligne.startswith("DP  -"):
                date = ligne[6:].split()[0]
            
            if ligne.startswith("TA  - "):
                journal = ligne[6:]
            
            if ligne.startswith("LID -") and "[doi]" in ligne : 
                doi = ligne[6:].replace(" [doi]","")
            
            if ligne.startswith("FAU -") : 
                auteurs_liste.append(ligne[6:].strip())
            
            if ligne.startswith("AB  -") : 
                abstract = ligne[6:]
                dans_abstract = True 
            elif dans_abstract and ligne.startswith("      "): 
                abstract = abstract + " " + ligne.strip()
            elif dans_abstract :
                dans_abstract = False

            
        abstract = " ".join(abstract.split())    
        auteurs = " & ".join(auteurs_liste[:2])
        journal = " ".join(journal.split())
        titre = " ".join(titre.split())   # ← nettoie les espaces multiples
        
        article = {
            "pmid": pmid,
            "titre": titre,
            "type": type_article,
            "annee": date,
            "journal": journal,
            "abstract" : abstract,
            "doi": doi,
            "auteurs": auteurs
        }
        liste_articles.append(article)
      
    return liste_articles 
    


def extraire_mots_cles(question):
    """Demande à Claude les mots-clés importants d'une question"""
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": f"""Extrais MAXIMUM 4 mots-clés scientifiques ESSENTIELS de cette question:
"{question}"

Choisis uniquement les concepts les plus importants. Retourne UNIQUEMENT les mots-clés EN ANGLAIS séparés par des espaces, rien d'autre.
Exemple: "CRISPR organoid differentiation"""
            }
        ]
    )
    
    return message.content[0].text.strip()









def synthese_article(article, sujet):
    """Génère un résumé pour UN article, basé uniquement sur son abstract"""
    
    prompt = f"""Tu es un expert en bioinformatique et biologie moléculaire.

Un chercheur pose cette question: {sujet}

Voici UN SEUL article scientifique à analyser. Réponds en JSON strict.

RÈGLES ABSOLUES:
1. Le résumé doit provenir UNIQUEMENT de cet abstract, développé (contexte, méthode, résultat principal, conclusion)
2. Les résultats clés chiffrés (pourcentages, durées, taux...) doivent être des valeurs EXACTES présentes dans l'abstract, jamais calculées ou déduites
3. Si aucun résultat chiffré n'est présent, laisse la liste vide
4. N'invente RIEN qui ne figure pas dans cet abstract

Titre de l'article: {article['titre']}
Abstract: {article['abstract']}

Réponds en JSON valide, uniquement:
{{
  "resume": "résumé développé basé uniquement sur l'abstract",
  "resultats_cles": ["résultat chiffré 1 si présent"],
  "pertinence_texte": "1-2 lignes sur pourquoi cet article répond ou non à la question du chercheur",
  "pertinence_niveau": "haute, moyenne, faible ou hors_sujet - choisis EXACTEMENT un de ces 4 mots"
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=850,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return message.content[0].text








def synthese_ia(contenu, sujet, profil="chercheur", nb_articles=10):
    print("Analyse IA en cours...", end="\r")
    tokens_max = min(4000 + nb_articles * 200, 16000)

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


    prompt_chercheur_question = f"""Tu es un expert en bioinformatique et biologie moléculaire.

Un chercheur pose cette question précise: {sujet}

RÈGLES ABSOLUES:
1. Chaque solution DOIT avoir des sources: DOI + auteurs + année
2. Si tu ne peux pas sourcer → OMETS-LA
3. Output JSON uniquement, pas de markdown

Réponds en JSON valide:

{{
  "contexte": "2-3 lignes sur l'état de l'art pour cette question",
  "solutions": [
    {{
      "rang": 1,
      "nom": "Nom de la solution",
      "description": "4-5 lignes",
      "avantages": ["avantage 1", "avantage 2"],
      "inconvenients": ["inconvenient 1"],
      "sources": [{{"doi": "10.1038/...", "auteurs": "X et al.", "year": 2024}}]
    }},
    {{
      "rang": 2,
      "nom": "Solution 2",
      "description": "...",
      "avantages": [],
      "inconvenients": [],
      "sources": []
    }}
  ],
  "recommandation": "Quelle solution choisir pour ce cas précis et pourquoi"
}}

Articles à analyser:
{contenu}"""

   
    prompts = {
        "chercheur": prompt_chercheur_question,



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



def lancer_recherche(sujet, nb_articles=5, profil="chercheur"):
    print("=== PubMind ===")
    print("sujet : " + sujet)
    print("profil : " + profil)
    print("================")

    mots_cles = extraire_mots_cles(sujet)
    print("Mots-clés extraits : " + mots_cles)

    ids = rechercher_articles(mots_cles, nb_articles)
    if len(ids) == 0:
        return ("⚠️ Aucun article trouvé pour cette recherche.\n"
                "Essaie une requête plus large ou reformule ta question.")

    contenu = telecharger_articles(ids)
    articles = parser_articles(contenu)

    if profil == "chercheur":
        cards = []
        for article in articles:
            resultat_brut = synthese_article(article, sujet)
            resultat_propre = resultat_brut.replace("```json", "").replace("```", "").strip()

            try:
                data = json.loads(resultat_propre)
                article["resume"] = data["resume"]
                article["resultats_cles"] = data["resultats_cles"]
                article["pertinence_texte"] = data["pertinence_texte"]
                article["pertinence_niveau"] = data["pertinence_niveau"]
            except json.JSONDecodeError:
                article["resume"] = "Erreur de traitement pour cet article"
                article["resultats_cles"] = []
                article["pertinence_texte"] = ""
                article["pertinence_niveau"] = "faible"
            cards.append(article)

        ordre_pertinence = {"haute": 1, "moyenne": 2, "faible": 3, "hors_sujet": 4}
        cards.sort(key=lambda c: ordre_pertinence.get(c["pertinence_niveau"], 5))

        return cards
        
    else:
        # Ancien flux pour les autres profils (étudiant, veille) — non encore migré
        synthese = synthese_ia(contenu, sujet, profil, nb_articles)
        return synthese
    

#different type de profil ( reponse adaptée en fonction du profil)

# Pour un chercheur (défaut, détecte auto sujet général vs question précise)
# Pour un étudiant  --> ("CRISPR cancer", 3, profil="etudiant")
# Pour un reviewer  --> ("CRISPR cancer", 3, profil="reviewer")
# Question précise  --> ("comment optimiser le CRISPR dans les cellules souches ?", 10, profil="chercheur")
# Veille            --> ("CRISPR base editing cancer 2024", 20, profil="veille")



if __name__ == "__main__":
    resultat = lancer_recherche("comment optimiser CRISPR dans les organoids", 5, "chercheur")
    print("Nombre de cards :", len(resultat))
    for card in resultat:
        print(card["titre"])
        print("Pertinence :", card["pertinence_texte"], "-", card["pertinence_niveau"])
        print("---")