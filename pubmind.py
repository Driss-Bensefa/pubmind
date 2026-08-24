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

def rechercher_articles(sujet, nb_articles=5, tri="pertinence"):
    print("recherche en cours pour : " + sujet, end="\r")
    
    if tri == "date":
        handle = Entrez.esearch(db="pubmed", term=sujet, retmax=nb_articles, sort="pub date")
    else:
        handle = Entrez.esearch(db="pubmed", term=sujet, retmax=nb_articles)
    

    
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
                parties_date = ligne[6:].split()
                if len(parties_date) >= 2:
                    date = parties_date[0] + " " + parties_date[1]
                else:
                    date = parties_date[0]
            
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
        max_tokens=1200,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return message.content[0].text






def synthese_veille(articles, sujet):
    """Génère une synthèse de veille structurée à partir d'un lot d'articles (abstracts complets)"""
    
    liste_articles = ""
    for i, article in enumerate(articles):
        liste_articles += f"\n--- Article {i} ---\nTitre: {article['titre']}\nAnnée: {article['annee']}\nAbstract: {article['abstract']}\n"
    
    prompt = f"""Tu fais une veille scientifique sur : {sujet}

Voici {len(articles)} articles récents avec leur abstract complet :
{liste_articles}

Réponds en JSON strict avec cette structure exacte :

{{
  "intro": "2-4 phrases présentant le domaine et son contexte actuel",
  "sections": [
    {{
      "titre": "Nom de l'axe de recherche",
      "texte": "Au moins 5 lignes détaillées. Mentionne les données chiffrées EXACTES présentes dans les abstracts (pourcentages, tailles d'échantillon, durées, taux de réussite...) quand elles existent. N'invente JAMAIS un chiffre qui n'est pas dans les abstracts fournis."
    }}
  ],
  "articles_notables": [
    {{
      "index": 12,
      "classification": "innovant",
      "raison": "Pourquoi cet article se distingue, avec un chiffre clé si présent dans son abstract"
    }}
  ]
}}

Consignes :
- Identifie 10 axes de recherche maximum, les plus représentés dans le corpus
- Dans "articles_notables", inclus OBLIGATOIREMENT les deux catégories :
- 10 articles  maximum classés "innovant" : ceux avec l'approche la plus rare ou différente du corpus
- 10 articles  maximum  classés "courant" : ceux qui illustrent bien l'approche la PLUS RÉPANDUE et représentative du corpus
- Chaque section doit faire au minimum 5 lignes, avec des détails précis (pas de généralités vagues)
- Utilise les données chiffrées réelles des abstracts autant que possible, jamais inventées ou déduites
- Réponds uniquement en JSON valide, sans texte avant ou après
- N'invente jamais rien, base-toi uniquement sur les informations des abstracts"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=12000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text




def synthese_ia(contenu, sujet, profil="etudiant", nb_articles=10):
    print("Analyse IA en cours...", end="\r")
    tokens_max = min(4000 + nb_articles * 200, 16000)

    prompt_etudiant = f"""Tu es un tuteur en bioinformatique et en biologie.
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
{contenu}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=tokens_max,
        messages=[
            {
                "role": "user",
                "content": prompt_etudiant
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

    tri = "date" if profil == "veille" else "pertinence"
    ids = rechercher_articles(mots_cles, nb_articles, tri=tri)
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

    elif profil == "veille":
        resultat_brut = synthese_veille(articles, sujet)
        resultat_propre = resultat_brut.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(resultat_propre)
        except json.JSONDecodeError:
            data = {
                "intro": "Erreur lors du traitement de la veille. Réessayez.",
                "sections": [],
                "articles_notables": []
            }

        # On relie chaque article notable à ses vraies métadonnées (titre, doi, lien...)
        for notable in data.get("articles_notables", []):
            idx = notable["index"]
            if 0 <= idx < len(articles):
                notable["article"] = articles[idx]

        return data

    else:
        # Ancien flux pour étudiant — non encore migré
        synthese = synthese_ia(contenu, sujet, profil, nb_articles)
        return synthese
      

#different type de profil ( reponse adaptée en fonction du profil)

# Pour un chercheur (défaut, détecte auto sujet général vs question précise)
# Pour un étudiant  --> ("CRISPR cancer", 3, profil="etudiant")
# Pour un reviewer  --> ("CRISPR cancer", 3, profil="reviewer")
# Question précise  --> ("comment optimiser le CRISPR dans les cellules souches ?", 10, profil="chercheur")
# Veille            --> ("CRISPR base editing cancer 2024", 20, profil="veille")



if __name__ == "__main__":
    resultat = lancer_recherche("CRISPR base editing", 100, profil="veille")
    print("INTRO:", resultat["intro"])
    print("\nNombre de sections:", len(resultat["sections"]))
    print("Nombre d'articles notables:", len(resultat["articles_notables"]))
    
    print("\n--- Vérification du lien article ---")
    premier_notable = resultat["articles_notables"][0]
    print("Index:", premier_notable["index"])
    print("Classification:", premier_notable["classification"])
    print("Titre relié:", premier_notable["article"]["titre"])
    print("DOI relié:", premier_notable["article"]["doi"])