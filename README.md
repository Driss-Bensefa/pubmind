# PubMind — AI-Powered Biomedical Literature Agent

> Analyze hundreds of PubMed articles in seconds. Get structured, sourced syntheses adapted to your research profile.

Built by **Driss Bensefa** — Bioinformatics & Genomics, BIMS Master (Rouen)

---

## What is PubMind?

PubMind is an AI agent that connects directly to the **NCBI/PubMed database** (35 million scientific articles) and generates expert-level syntheses automatically.

Instead of spending hours reading articles manually, you type a subject or question — PubMind retrieves the most relevant papers, analyzes them, and delivers a structured report in under 60 seconds.

**The key difference from tools like ChatGPT or Perplexity:**
- Real-time access to PubMed via the official NCBI Entrez API
- Advanced query optimization with boolean operators and MeSH filters
- Biological domain expertise embedded in every profile and prompt
- Sourced citations with direct PubMed links for every claim

---

## Features

**4 Expert Profiles**
- `student` — simplified explanations, key concepts defined
- `researcher` — detailed protocols, reproducibility analysis, expert recommendations
- `reviewer` — critical evaluation with quality scores, methodology assessment
- `monitoring` — emerging trends, active research groups, 3-level detail based on article count

**Advanced PubMed Query Optimization**
Natural language input is automatically converted into optimized PubMed syntax using boolean operators (`AND`, `OR`, `NOT`), field filters (`[gene]`, `[tiab]`, `[pt]`), and MeSH terms.

**Rich Data Pipeline**
Each analysis combines MEDLINE structured metadata (journal, MeSH keywords, publication type, funding) with full abstracts for deeper, more reliable synthesis.

**Adaptive Detail Levels** *(monitoring profile)*
- ≤10 articles → full individual summaries
- 11–50 articles → short summaries + 5 must-read papers
- >50 articles → macro trends only + 10 representative papers

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| PubMed API | Biopython / NCBI Entrez |
| AI Synthesis | Anthropic Claude API (Haiku) |
| Web Framework | Flask |
| Frontend | HTML/CSS + Jinja2 + Markdown rendering |
| Query Optimization | NLP via Claude API |

---

## Installation

**Prerequisites:** Python 3.11+, Anthropic API key

```bash
# Clone the repository
git clone https://github.com/driss-bensefa/pubmind.git
cd pubmind

# Install dependencies
pip install -r requirements.txt

# Set your API key
setx ANTHROPIC_API_KEY "your-key-here"   # Windows
export ANTHROPIC_API_KEY="your-key-here" # Mac/Linux

# Launch
python app.py
```

Open your browser at `http://localhost:5000`

---

## Usage Examples

```python
# Researcher profile — general subject
lancer_recherche("CRISPR base editing cancer 2024", 25, profil="researcher")

# Researcher profile — specific question (auto-detected)
lancer_recherche("how to transfect human cells into mouse brain?", 10, profil="researcher")

# Monitoring — large-scale trend analysis
lancer_recherche("single cell RNA-seq cancer 2025", 50, profil="monitoring")

# Reviewer — critical quality assessment
lancer_recherche("organoid drug screening", 10, profil="reviewer")
```

---

## Project Structure

```
pubmind/
├── pubmind.py          # Core pipeline (PubMed queries, AI synthesis)
├── app.py              # Flask web server
├── templates/
│   ├── index.html      # Search interface
│   └── resultat.html   # Results page
├── requirements.txt
└── README.md
```

---

## Roadmap

- [x] PubMed search via NCBI Entrez API
- [x] AI synthesis with 4 expert profiles
- [x] Advanced PubMed query optimization (NLP)
- [x] MEDLINE metadata + abstract pipeline
- [x] Flask web interface with markdown rendering
- [ ] Interactive card grid results page
- [ ] Search history (SQLite)
- [ ] Email alerts for new publications
- [ ] ML-based relevance scoring

---

## About

This project was built as part of a learning journey toward a career in bioinformatics and computational biology, targeting the US biotech industry (San Diego / Boston).

Prompts are built around real research workflows — distinguishing clinical trials from reviews, leveraging MeSH controlled vocabulary, separating methodology from conclusions, and flagging conflicts of interest from funding metadata. The 4 profiles reflect how different users actually interact with scientific literature, not just different verbosity levels.

---

*Powered by NCBI/PubMed · Built with Python & Claude API*
