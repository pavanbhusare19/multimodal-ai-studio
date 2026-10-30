# MultiModal AI Studio

A Flask + Gemini starter app with:
- Gemini image understanding (JPG/PNG/WebP)
- Browser speech-to-text (Web Speech API) and text-to-speech (SpeechSynthesis)
- Automated content pipeline: research brief → outline → draft → refinement
- Restricted calculator tool and starter evaluation checks

## Run locally (Windows PowerShell)

```powershell
cd multimodal-ai-studio
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Add your Gemini API key to `.env`, save, then run:

```powershell
python app.py
```

Open http://127.0.0.1:5000

## Deploy on Render

1. Push this folder to a new GitHub repository.
2. Create a Render **Web Service** from that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variables `GEMINI_API_KEY` and `GEMINI_MODEL`.
6. Deploy and test all tabs on the public URL.

## Important: connect your original AI-C2 agent

This is a runnable integration starter, not a verified copy of your original AI-C2 project. The `run_agent_tool()` function in `app.py` is the adapter seam. Merge your existing agent's tool registry, agent executor, trace logging, and evaluation harness here. Keep your original tests and add them to `/api/evaluate` before claiming the milestone is complete.

## Voice notes

Voice input uses the browser Web Speech API and output uses browser SpeechSynthesis, so there is no separate speech API key. Browser and language support vary; test with Chrome and allow microphone access.

## Security

Never commit `.env` or expose your API key in frontend JavaScript. The calculator accepts only basic arithmetic characters; do not replace it with unrestricted `eval`.
