# Tests unitaires de PubMind
# Lancer depuis la racine du projet avec : pytest -v

from pubmind import retirer_preambule, inserer_metadonnees


# --- retirer_preambule ---

def test_preambule_supprime():
    texte = "Voici une analyse...\n\n## 🎓 Comprendre le domaine"
    assert retirer_preambule(texte, "## 🎓") == "## 🎓 Comprendre le domaine"


def test_texte_sans_preambule_inchange():
    texte = "## 🎓 Comprendre le domaine"
    assert retirer_preambule(texte, "## 🎓") == texte


def test_marqueur_absent_texte_inchange():
    texte = "texte sans marqueur"
    assert retirer_preambule(texte, "## 🎓") == texte


# --- inserer_metadonnees ---

ARTICLES_TEST = [{
    "pmid": "111",
    "titre": "Titre test",
    "auteurs": "Dupont, A & Martin, B",
    "journal": "Nature",
    "annee": "2026 Jan",
}]


def test_pmid_connu_donne_titre_et_lien():
    resultat = inserer_metadonnees("[ARTICLE: 111]\n[LIEN: 111]", ARTICLES_TEST)
    assert "### Titre test" in resultat
    assert "Dupont, A & Martin, B" in resultat
    assert "https://pubmed.ncbi.nlm.nih.gov/111" in resultat


def test_pmid_invente_donne_avertissement_et_pas_de_lien():
    resultat = inserer_metadonnees("[LIEN: 999]", ARTICLES_TEST)
    assert "absent des articles téléchargés" in resultat
    assert "pubmed.ncbi.nlm.nih.gov" not in resultat


from pubmind import parser_articles 

MEDLINE_TEST = "\nPMID- 1\nTI  - Titre\nAB  - abstract "

def  test_extraction_exacte_parser_articles():
    resultat =parser_articles(MEDLINE_TEST)
    assert resultat[0]['pmid'] == "1"
    assert resultat[0]['titre'] == "Titre"
    assert resultat[0]['abstract'] == "abstract"