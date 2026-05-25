# VS Code Runbook

Use this when running ReconMate from Visual Studio Code on Windows.

## 1. Select Interpreter

In VS Code:

1. Press `Ctrl+Shift+P`.
2. Search `Python: Select Interpreter`.
3. Choose either your global Python 3.13 or `.venv\Scripts\python.exe` if VS Code created a virtual environment.

## 2. Install Required Dependencies

Run in the VS Code terminal:

```powershell
python -m pip install -r requirements.txt
```

Do not install `requirements-ocr.txt` unless you need real OCR. The demo works without it.

## 3. Run API Test

```powershell
python scripts/test_api.py
```

This command starts a temporary server on port `8010`, tests it, then stops it. This is expected.

## 4. Run The Browser App

```powershell
python main.py
```

Keep this terminal open. You should see something like:

```text
Uvicorn running on http://127.0.0.1:8000
```

Then open:

```text
http://127.0.0.1:8000/
```

Click `Run Reconciliation`.

## 5. If You See `Will watch for changes`

That is an old reload server. Stop it with `Ctrl+C`.

If it does not stop, run:

```powershell
Get-Process python | Stop-Process -Force
```

Then start again:

```powershell
python main.py
```

## 6. Optional Chutes Key

```powershell
$env:CHUTES_API_KEY="your-key-here"
$env:CHUTES_MODEL="default:latency"
python main.py
```

If Chutes returns `429 Too Many Requests`, ReconMate still works using template fallback.
