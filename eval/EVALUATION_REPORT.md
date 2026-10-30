# AI-C2 Evaluation Report

Run date: 2026-10-30T15:08:42.019858+05:30

Pass rate: 10/10 (100.0%)

## Test results

### TC01 — PASS
Prompt: Calculate 18 * 7 and explain the result briefly.
Expected tools: calculate
Used tools: calculate
Keyword found: True

### TC02 — PASS
Prompt: What is 144 divided by 12? Use a calculation tool.
Expected tools: calculate
Used tools: calculate
Keyword found: True

### TC03 — PASS
Prompt: Calculate (25 + 15) / 4.
Expected tools: calculate
Used tools: calculate
Keyword found: True

### TC04 — PASS
Prompt: Search the web for the official Python website and tell me its domain.
Expected tools: tavily_search
Used tools: tavily_search, tavily_search
Keyword found: True

### TC05 — PASS
Prompt: Search the web for the official LangChain documentation and give me its domain.
Expected tools: tavily_search
Used tools: tavily_search
Keyword found: True

### TC06 — PASS
Prompt: Search the web for current information about retrieval-augmented generation (RAG), then give me a two-sentence summary.
Expected tools: tavily_search
Used tools: tavily_search
Keyword found: True

### TC07 — PASS
Prompt: Save a research note titled 'Evaluation Basics' with this note: RAG evaluation should check retrieval relevance, answer faithfulness, and answer usefulness.
Expected tools: save_research_note
Used tools: save_research_note
Keyword found: True

### TC08 — PASS
Prompt: Search for the official GitHub website, then calculate 19 * 23 and summarize both results.
Expected tools: tavily_search, calculate
Used tools: tavily_search, tavily_search, tavily_search, calculate
Keyword found: True

### TC09 — PASS
Prompt: Calculate 250 * 0.18 to estimate 18 percent of 250.
Expected tools: calculate
Used tools: calculate
Keyword found: True

### TC10 — PASS
Prompt: Search the web for what LangGraph is used for, then calculate 64 / 8. Give me a concise combined answer.
Expected tools: tavily_search, calculate
Used tools: tavily_search, calculate
Keyword found: True
