MultiModal AI Studio



An AI-powered platform combining multimodal capabilities, content generation, conversational AI, and agentic research workflows.











🚀 Overview



MultiModal AI Studio is a web-based AI application built with Flask and modern AI tools. It brings multiple AI capabilities together in one platform, helping users interact with AI, analyze images, generate content, and execute research tasks through an agentic workflow.



✨ Features



1\. AI Chat



Conversational AI responses.



Powered by Gemini and Groq integrations.



Designed to explain concepts and answer user questions.



2\. Image Studio



Analyze uploaded images.



Supports JPG, PNG, and WebP formats.



Uses Gemini for image understanding.



3\. Voice Studio



Browser-based speech-to-text using the Web Speech API.



Text-to-speech using browser SpeechSynthesis.



Microphone access is required for voice input.



4\. AI Content Pipeline



Research brief generation.



Content outline creation.



First draft generation.



Content refinement and final output.



5\. ResearchMate Agent



Built using LangChain's create\_agent.



Web research using Tavily Search.



Restricted calculator tool for arithmetic tasks.



Research note-saving tool.



Agent execution traces stored in logs/agent\_traces.jsonl.



6\. Evaluation System



Automated evaluation test cases.



Evaluation report generation.



Latest local evaluation result: 10/10 test cases passed (100%).



The evaluation score reflects the configured test suite, not a guarantee of accuracy for every possible AI response.



🛠️ Technology Stack



Backend: Python, Flask



Frontend: HTML, CSS, JavaScript



AI Models: Google Gemini, Groq



Agent Framework: LangChain



Web Search: Tavily



Voice: Web Speech API, SpeechSynthesis



Deployment: Render



Version Control: Git and GitHub



📁 Project Structure



multimodal-ai-studio/

├── app.py

├── agent\_integration.py

├── evaluate\_agent.py

├── eval/

│   ├── eval\_cases.json

│   ├── latest\_results.json

│   └── EVALUATION\_REPORT.md

├── logs/

│   └── agent\_traces.jsonl

├── static/

│   ├── app.js

│   └── style.css

├── templates/

│   └── index.html

├── .env.example

├── .gitignore

├── requirements.txt

├── Procfile

└── README.md



⚙️ Run Locally (Windows PowerShell)



Clone the repository:



git clone https://github.com/pavanbhusare19/multimodal-ai-studio.git

cd multimodal-ai-studio



Create and activate a virtual environment:



py -3.12 -m venv .venv

.venv\\Scripts\\Activate.ps1



Install dependencies:



pip install -r requirements.txt



Create your environment file:



Copy-Item .env.example .env

notepad .env



Add the required API credentials and configuration to .env. Never share or commit your API keys.



Run the application:



python app.py



Open:



http://127.0.0.1:5000



🌐 Deployment on Render



The application is deployed on Render.



Live Application:

https://multimodal-ai-studio.onrender.com



Typical Render configuration:



Build Command: pip install -r requirements.txt



Start Command: gunicorn app:app



Configure the required environment variables in the Render dashboard:



GEMINI\_API\_KEY



GEMINI\_MODEL



AI\_PROVIDER



GROQ\_API\_KEY



GROQ\_MODEL



TAVILY\_API\_KEY



Use secret environment variables for API keys. Do not place credentials in frontend JavaScript or commit .env.



🔐 Security Notes



API keys are managed through environment variables.



.env should remain excluded from Git.



The calculator tool restricts accepted arithmetic expressions.



Avoid using unrestricted eval() for user input.



Keep API credentials private.



📊 Evaluation



The project includes an automated evaluation suite with 10 configured test cases.



Latest recorded local result:



Passed: 10



Failed: 0



Pass rate: 100%



Evaluation report: eval/EVALUATION\_REPORT.md



👨‍💻 Developer



Pavan Bhusare



B.E. Artificial Intelligence and Data Science



GitHub: https://github.com/pavanbhusare19



LinkedIn: https://in.linkedin.com/in/pavan-bhusare-4b0ab13b5



📌 Project Links



GitHub Repository: https://github.com/pavanbhusare19/multimodal-ai-studio



Live Demo: https://multimodal-ai-studio.onrender.com





