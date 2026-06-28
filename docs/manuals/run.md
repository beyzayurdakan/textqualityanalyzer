# How to Run the program

## 1. Start the backend

Open a terminal and move to the project folder:

```bash
cd textqualityanalyzer
```

Activate the virtual environment.

Windows:

```powershell
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Move to the backend folder:

```bash
cd src/main
```

Start the backend with uvicorn:

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

To check that it is working, open:

```text
http://127.0.0.1:8000/health
```

## 2. Start ngrok

Open a second terminal and run:

```bash
ngrok http 8000
```

ngrok will generate a public HTTPS URL, for example:

```text
https://example-name.ngrok-free.app
```

Copy this URL.

## 3. Update the backend URL in Apps Script

Open the Apps Script project connected to Google Docs.

In `Code.gs`, update:

```javascript
const SPACY_BACKEND_URL = 'YOUR_BACKEND_URL';
```

with the ngrok URL.

Example:

```javascript
const SPACY_BACKEND_URL = 'https://example-name.ngrok-free.app';
```

Save the Apps Script project.

## 4. Run the analyzer in Google Docs

Reload the Google Docs document.

Open:

```text
Text Quality Analyzer > Open analyzer
```

The sidebar will appear.

Then:

1. select one or more target audiences;
2. click `Analyze document`;
3. wait for the results;
4. use the export options to generate a PDF report, DOCX report, or analyzed document.

## Notes

If the analysis fails, check that:

1. the backend is running on port `8000`;
2. ngrok is running;
3. the ngrok URL in `Code.gs` is correct;
4. the URL does not include `/analyze`;
5. the Base Vocabulary file is located at:

```text
src/main/text_quality/data/base_vocabulary.csv
```
