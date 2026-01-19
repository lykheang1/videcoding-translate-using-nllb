# Translation Web Application

A full-stack translation web application powered by Meta's NLLB-200 (No Language Left Behind) model. Built with FastAPI (backend) and Next.js with Tailwind CSS (frontend), this application provides high-quality translations across 200+ languages.

## 🌟 Features

### Core Functionality
- **Multi-language Translation**: Supports 200+ languages using Meta's NLLB-200-distilled-600M model
- **Intelligent Text Handling**: Automatically detects token length and chunks long texts for accurate translation
- **Smart Chunking**: Preserves sentence boundaries and context when splitting long texts
- **Khmer Language Support**: Specialized handling for Khmer and other complex scripts
- **Real-time Translation**: Fast and responsive translation API

### Backend Features
- **Meta NLLB-200 Model**: Powered by Hugging Face Transformers
- **Token-aware Processing**: Accurate token detection prevents truncation
- **Automatic Chunking**: Handles texts exceeding model limits intelligently
- **Error Handling**: Comprehensive error handling for long texts and model loading
- **Health Monitoring**: Health check endpoints for service monitoring
- **CORS Enabled**: Ready for frontend integration
- **Auto Documentation**: Swagger UI and ReDoc for API exploration

### Frontend Features
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Language Selection**: Easy-to-use dropdowns with 20+ common languages
- **Character Counter**: Real-time character count for source and translated text
- **Auto-clear**: Translated text clears when source text is cleared
- **Loading States**: Visual feedback during translation
- **Error Handling**: User-friendly error messages with retry functionality
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark Mode Support**: Automatic dark mode based on system preferences

## 📁 Project Structure

```
translate-meta/
├── backend/                    # FastAPI Backend
│   ├── main.py                # Main application with NLLB-200 integration
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Docker configuration
│   ├── .dockerignore          # Docker ignore file
│   └── README.md              # Backend documentation
├── frontend/                   # Next.js Frontend
│   ├── app/                   # Next.js App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main translation page
│   │   └── globals.css        # Global styles with Tailwind
│   ├── package.json           # Node.js dependencies
│   ├── Dockerfile             # Docker configuration
│   ├── next.config.js         # Next.js configuration
│   ├── tailwind.config.ts     # Tailwind CSS configuration
│   ├── tsconfig.json          # TypeScript configuration
│   └── README.md              # Frontend documentation
├── docker-compose.yml          # Docker Compose orchestration
├── DOCKER.md                   # Docker setup guide
├── Makefile                    # Helper commands
├── .dockerignore               # Docker ignore file
└── README.md                   # This file
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

The easiest way to get started:

```bash
# Clone the repository (if applicable)
# cd translate-meta

# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

**First Run**: The backend will automatically download the NLLB-200 model (~1.2GB) on first startup. This may take 5-10 minutes depending on your internet connection. The model is cached for subsequent runs.

**Access the Application:**
- 🌐 Frontend: http://localhost:4000
- 🔧 Backend API: http://localhost:8000
- 📚 API Documentation: http://localhost:8000/docs

For detailed Docker instructions, see [DOCKER.md](DOCKER.md).

### Option 2: Using Makefile

```bash
make up-build    # Build and start all services
make logs        # View logs from all services
make logs-backend    # View backend logs only
make logs-frontend   # View frontend logs only
make down        # Stop all services
make restart     # Restart all services
make clean       # Remove containers and volumes
```

See `Makefile` for all available commands.

### Option 3: Manual Setup

#### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment (Python 3.10+):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note**: This will install PyTorch and Transformers, which may take a few minutes.

4. **Run the server:**
   ```bash
   python main.py
   # or with auto-reload
   uvicorn main:app --reload
   ```

   The backend will download the NLLB-200 model on first run (~1.2GB).

5. **Verify it's running:**
   ```bash
   curl http://localhost:8000/health
   ```

#### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to http://localhost:4000

## 🔌 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with API information |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/translate` | Translate text from source to target language |
| `GET` | `/languages` | Get list of supported languages |

### Translation Request

**Endpoint:** `POST /translate`

**Request Body:**
```json
{
  "text": "សួរស្តី",
  "source_lang": "khm_Khmr",
  "target_lang": "eng_Latn"
}
```

**Response:**
```json
{
  "translated_text": "Hello",
  "source_lang": "khm_Khmr",
  "target_lang": "eng_Latn"
}
```

**Default Languages:**
- Source: `khm_Khmr` (Khmer)
- Target: `eng_Latn` (English)

### Supported Languages

The application supports 200+ languages. Common languages include:
- `eng_Latn` - English
- `khm_Khmr` - Khmer
- `spa_Latn` - Spanish
- `fra_Latn` - French
- `deu_Latn` - German
- `zho_Hans` - Chinese (Simplified)
- `jpn_Jpan` - Japanese
- `kor_Hang` - Korean
- `ara_Arab` - Arabic
- `hin_Deva` - Hindi
- And many more...

See `/languages` endpoint for the complete list.

## 🛠 Tech Stack

### Backend
- **Python 3.11+** - Programming language
- **FastAPI 0.115.0** - Modern web framework
- **Uvicorn 0.32.0** - ASGI server
- **PyTorch 2.0+** - Deep learning framework
- **Transformers 4.36+** - Hugging Face Transformers library
- **Meta NLLB-200** - Translation model (facebook/nllb-200-distilled-600M)
- **Pydantic 2.10+** - Data validation

### Frontend
- **Next.js 14** - React framework with App Router
- **React 18** - UI library
- **TypeScript 5.3** - Type-safe JavaScript
- **Tailwind CSS 3.4** - Utility-first CSS framework

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## 🎯 Key Features Explained

### Intelligent Text Chunking

The application automatically handles long texts by:
1. **Token Detection**: Accurately counts tokens before translation
2. **Smart Splitting**: Splits at sentence boundaries when possible
3. **Language-Aware**: Special handling for languages like Khmer without word boundaries
4. **Sequential Translation**: Translates chunks in order and recombines accurately
5. **No Truncation**: Ensures no content is lost

### Token Limit Handling

- **Input Limit**: 1024 tokens per chunk (with 50 token safety margin)
- **Output Limit**: 2048 tokens per chunk
- **Max Text Length**: 5000 characters per request
- **Automatic Processing**: Long texts are split and processed automatically

### Error Handling

- **Model Loading**: Graceful handling if model isn't loaded yet
- **Network Errors**: Retry logic with exponential backoff
- **Invalid Language Codes**: Clear error messages
- **Text Too Long**: Validation before processing
- **Chunking Errors**: Continues with remaining chunks if one fails

## 📊 Performance Considerations

### Model Size
- **Model**: facebook/nllb-200-distilled-600M
- **Download Size**: ~1.2GB
- **Memory Usage**: ~2-3GB RAM when loaded
- **First Load**: 5-10 minutes (download + loading)
- **Subsequent Loads**: ~30 seconds

### Translation Speed
- **Short Texts** (< 1000 chars): 1-3 seconds
- **Medium Texts** (1000-3000 chars): 3-10 seconds
- **Long Texts** (> 3000 chars): 10-30 seconds (with chunking)

### Optimization Tips
1. **GPU Acceleration**: Use CUDA if available (automatic detection)
2. **Caching**: Model is cached after first download
3. **Chunking**: Automatic chunking prevents timeout errors
4. **Health Checks**: Monitor backend health before heavy use

## 🔧 Configuration

### Environment Variables

#### Backend
- `PYTHONUNBUFFERED=1` - Enable unbuffered Python output

#### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)
- `NODE_ENV` - Environment (production/development)

### Port Configuration

Default ports (can be changed in `docker-compose.yml`):
- **Backend**: 8000 (host) → 8000 (container)
- **Frontend**: 4000 (host) → 3000 (container)

To change ports, modify `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "YOUR_PORT:8000"
  frontend:
    ports:
      - "YOUR_PORT:3000"
```

## 📚 API Documentation

Interactive API documentation is automatically generated:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide:
- Endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Model descriptions

## 🐛 Troubleshooting

### Backend Issues

**Problem**: Model download fails
- **Solution**: Check internet connection and disk space (need ~2GB)

**Problem**: Out of memory errors
- **Solution**: Ensure at least 4GB RAM available, reduce MAX_INPUT_TOKENS

**Problem**: Translation takes too long
- **Solution**: Normal for long texts, check if chunking is working properly

### Frontend Issues

**Problem**: "Failed to fetch languages"
- **Solution**: Ensure backend is running and healthy at http://localhost:8000

**Problem**: Translation doesn't work
- **Solution**: Check browser console for errors, verify API URL is correct

### Docker Issues

**Problem**: Port already in use
- **Solution**: Change ports in `docker-compose.yml` or stop conflicting services

**Problem**: Containers won't start
- **Solution**: Check logs with `docker-compose logs`, ensure Docker has enough resources

**Problem**: Model not persisting
- **Solution**: Ensure volume mount in `docker-compose.yml` is correct

## 🚦 Health Checks

Check backend health:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "tokenizer_loaded": true
}
```

## 📝 Development

### Running in Development Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Code Structure

- **Backend**: Follows FastAPI best practices with async/await
- **Frontend**: Uses Next.js App Router with TypeScript
- **Styling**: Tailwind CSS utility classes
- **State Management**: React hooks (useState, useEffect)

### Adding New Features

1. **Backend**: Add endpoints in `backend/main.py`
2. **Frontend**: Add components in `frontend/app/`
3. **Styling**: Use Tailwind classes, extend `tailwind.config.ts` if needed
4. **Testing**: Test API with Swagger UI, test frontend in browser

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Meta AI** - For the NLLB-200 model
- **Hugging Face** - For the Transformers library
- **FastAPI** - For the excellent web framework
- **Next.js** - For the powerful React framework
- **Tailwind CSS** - For the utility-first CSS framework

## 📞 Support

For issues, questions, or contributions:
1. Check the [DOCKER.md](DOCKER.md) for Docker-specific issues
2. Review API documentation at http://localhost:8000/docs
3. Check backend and frontend README files for detailed setup

## 🔮 Future Enhancements

Potential improvements:
- [ ] Add more language pairs
- [ ] Implement translation history
- [ ] Add batch translation support
- [ ] Implement user authentication
- [ ] Add translation quality scores
- [ ] Support file upload translation
- [ ] Add more UI themes
- [ ] Implement caching for common translations

---

**Made with ❤️ using Meta's NLLB-200 model**
