# AI Reader Digest

An agentic AI-powered news digest system that ingests AI-related articles from RSS feeds, filters and scores them using LLMs, selects the most relevant stories, generates concise summaries, and delivers a curated digest through email.

---

# Overview

AI Reader Digest is designed to demonstrate an agentic workflow.

The system combines:

* Deterministic orchestration pipelines
* LLM-powered relevance scoring
* Multi-stage filtering
* Intelligent article selection
* Automated summarization
* Scheduled email delivery

The project focuses on building a practical production-style AI workflow rather than a simple chatbot.


# Key Features

## RSS-Based AI News Ingestion

Collects articles from multiple AI and technology RSS feeds.

## Multi-Stage Filtering

Reduces noise early in the pipeline using:

* time-based filtering
* article caps
* relevance scoring

## LLM-Powered Relevance Scoring

Uses language models to evaluate:

* topical relevance
* technical importance
* usefulness for digest readers


## Top 7 Selection Layer

A dedicated orchestration layer selects the highest quality articles before summarization.

## Automated Summarization

Generates concise readable summaries for selected articles.

## Email Digest Delivery

Automatically formats and sends the final digest.


# System Design Philosophy

This project demonstrates several important AI engineering concepts:

## Software 2.0 Thinking

Instead of hardcoding every rule, the system delegates semantic reasoning tasks to LLMs.

## Reliability Through Constraints

The workflow constrains LLM behavior using:

* filtering stages
* orchestration logic
* selection caps
* deterministic execution paths

## Agentic Orchestration

The pipeline mimics an agentic workflow where the system:

* evaluates options
* prioritizes information
* selects high-value outputs
* generates final deliverables

---

# Technologies Used

## Backend

* Python
* RSS Feed Parsing
* Email APIs
* LLM APIs

## AI/LLM Capabilities

* Relevance Classification
* Content Ranking
* Summarization
* Digest Generation

---

# Setup

## Clone Repository

```bash
git clone <repository-url>
cd "AI Reader Digest"
```

## Create Virtual Environment

```bash
python -m venv .venv
```

## Activate Virtual Environment

### Linux/macOS

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```


# Running the Project

```bash
python main.py
```

# Notes

This project is intentionally structured to demonstrate practical AI engineering patterns rather than only model interaction.

The focus is on:

* orchestration
* reliability
* modularity
* workflow design
* production thinking

---

# License

This project is for educational and experimentation purposes.
