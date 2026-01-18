# Translation API Backend

FastAPI backend for the translation web application.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python main.py
# or
uvicorn main:app --reload
```

The API will be available at `http://localhost:8001`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /translate` - Translate text
- `GET /languages` - Get supported languages

## Notes

This is a demo implementation using a simple translation dictionary. For production use, integrate with a translation service like:
- Google Cloud Translation API
- DeepL API
- Azure Translator
- LibreTranslate (open source)
