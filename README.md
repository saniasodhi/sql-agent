# SQL-Agent

An AI agent that converts natural language questions into executable SQL queries, with self-correction and evaluation against the BIRD benchmark.

## Status
🚧 In active development. Started April 2026.

## Goals
- Build an end-to-end text-to-SQL agent with retries and schema retrieval
- Evaluate on the BIRD-SQL benchmark, comparing prompting strategies
- (Stretch) Fine-tune a small open model that beats GPT-4 on schema-specific queries

## Stack
- Python 3.12
- Anthropic Claude API
- SQLite (dev), BIRD benchmark (eval)
- FastAPI + Streamlit (planned)

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then add your API key
```

## Progress
- [x] Day 1: Dev environment
- [x] Day 2: Project scaffolding
- [ ] Day 3: First LLM call