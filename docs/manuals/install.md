# How to Install the program

## 1. Clone the repo

First, clone the repository on your local machine. Open a terminal, move to the desired destination folder, and run:

```bash
git clone -b komurcu-yurdakan https://github.com/beyzayurdakan/textqualityanalyzer.git
```

Then enter the project folder:

```bash
cd textqualityanalyzer
```

Alternatively, you can download the `.zip` file from GitHub and extract it.

## 2. Install Python

Install Python 3.10 or later.

Windows: download Python from the official website and install it.

Linux:

```bash
sudo apt install python3 python3-venv python3-pip
```

## 3. Create the virtual environment

From the project root directory, create a virtual environment:

```bash
python -m venv venv
```

Activate it.

Windows:

```powershell
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

## 4. Install backend dependencies

Move to the backend folder:

```bash
cd src/main
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Install the Italian spaCy model:

```bash
python -m spacy download it_core_news_sm
```

## 5. Check the Base Vocabulary file

The Base Vocabulary file must be located here:

```text
src/main/text_quality/data/base_vocabulary.csv
```

The expected format is:

```csv
lemma,category
andare,FO
persona,FO
ragazza,AU
scrittura,AD
```

## 6. Install ngrok

Google Docs cannot directly access a local backend. For this reason, ngrok is needed.

Windows:

```powershell
winget install ngrok.ngrok
```

Then add your ngrok token:

```bash
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

Replace `YOUR_NGROK_TOKEN` with your token from the ngrok website.

## 7. Install the Google Docs add-on code

Open a Google Docs document and go to:

```text
Extensions > Apps Script
```

Then copy the project files into Apps Script:

```text
src/main/google_docs/Code.gs
src/main/google_docs/Sidebar.html
```

In Apps Script:

1. paste `Code.gs` into the Apps Script `Code.gs` file;
2. create a new HTML file named `Sidebar`;
3. paste `Sidebar.html` into that file;
4. save the Apps Script project.

## 8. Configure the backend URL

In `Code.gs`, find:

```javascript
const SPACY_BACKEND_URL = 'YOUR_BACKEND_URL';
```

Replace it with the ngrok HTTPS URL that will be generated when running the program.

Example:

```javascript
const SPACY_BACKEND_URL = 'https://example-name.ngrok-free.app';
```

Do not add `/analyze` at the end.
