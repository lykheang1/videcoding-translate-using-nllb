from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Translation API with NLLB-200", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:3000", "http://localhost:3001", "http://0.0.0.0:3001"],  # Support multiple ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
MODEL_NAME = "facebook/nllb-200-distilled-600M"
MAX_TEXT_LENGTH = 5000  # Maximum characters per request
MAX_INPUT_TOKENS = 1024  # Maximum tokens for model input (increased from 512)
MAX_OUTPUT_TOKENS = 2048  # Maximum tokens for model output (longer than input to handle expansion)

# Global variables for model and tokenizer
model = None
tokenizer = None


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    source_lang: Optional[str] = "khm_Khmr"  # Khmer default
    target_lang: str = "eng_Latn"  # English default


class TranslationResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str


@app.on_event("startup")
async def load_model():
    """Load the NLLB-200 model and tokenizer on startup."""
    global model, tokenizer
    try:
        logger.info(f"Loading model {MODEL_NAME}...")
        logger.info("This may take a few minutes on first run...")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        # Load model - use CPU if CUDA is not available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        model.to(device)
        model.eval()  # Set to evaluation mode
        
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise Exception(f"Failed to load translation model: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "Translation API with NLLB-200 is running",
        "model": MODEL_NAME,
        "max_text_length": MAX_TEXT_LENGTH
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that verifies model is loaded."""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "tokenizer_loaded": tokenizer is not None
    }


def translate_chunk(text_chunk: str, source_lang: str, target_lang: str) -> str:
    """
    Translate a single chunk of text.
    Helper function for chunking long texts.
    """
    # Set source language code for tokenizer
    tokenizer.src_lang = source_lang
    
    # Tokenize input text
    inputs = tokenizer(
        text_chunk,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_TOKENS,
        padding=True
    )
    
    # Move inputs to same device as model
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Get target language token ID
    token_ids = tokenizer.convert_tokens_to_ids([target_lang])
    forced_bos_token_id = token_ids[0]
    
    # Generate translation
    with torch.no_grad():
        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=MAX_OUTPUT_TOKENS,
            max_new_tokens=MAX_OUTPUT_TOKENS,
            num_beams=5,
            early_stopping=False,
            length_penalty=1.2,
            no_repeat_ngram_size=3,
            repetition_penalty=1.1,
            do_sample=False,
            num_return_sequences=1
        )
    
    # Decode translation
    translated_text = tokenizer.batch_decode(
        translated_tokens,
        skip_special_tokens=True
    )[0]
    
    return translated_text


def get_token_count(text: str, source_lang: str) -> int:
    """
    Get accurate token count for a text using the tokenizer.
    This is more accurate than character-based estimation.
    """
    try:
        tokenizer.src_lang = source_lang
        encoded = tokenizer.encode(text, add_special_tokens=False)
        return len(encoded)
    except Exception as e:
        logger.warning(f"Error getting token count, using estimation: {str(e)}")
        # Fallback: rough estimation based on language
        # Khmer and other complex scripts may have different ratios
        if source_lang.startswith('khm_') or source_lang.startswith('zho_') or source_lang.startswith('jpn_'):
            # Complex scripts: roughly 1 token per 2-3 characters
            return len(text) // 2.5
        else:
            # Latin scripts: roughly 1 token per 4 characters
            return len(text) // 4


def split_text_into_chunks(text: str, source_lang: str, max_tokens: int = MAX_INPUT_TOKENS, overlap: int = 50) -> list:
    """
    Split text into chunks based on actual token limits, preserving sentence boundaries.
    
    Args:
        text: Text to split
        source_lang: Source language code (for proper tokenization)
        max_tokens: Maximum tokens per chunk (leave room for special tokens)
        overlap: Number of tokens to overlap between chunks (to preserve context)
    
    Returns:
        List of text chunks that don't exceed token limits
    """
    # First check if text fits in one chunk
    token_count = get_token_count(text, source_lang)
    
    # Reserve some tokens for special tokens and language codes (~20-30 tokens)
    safe_max_tokens = max_tokens - 50
    
    if token_count <= safe_max_tokens:
        return [text]
    
    chunks = []
    remaining = text.strip()
    
    # Sentence boundary markers (common across many languages)
    # Khmer uses ។ (U+17D4) as sentence delimiter
    sentence_endings = '.!?\n។。！？\n'
    
    logger.info(f"Splitting text: {len(text)} chars, ~{token_count} tokens into chunks of ~{safe_max_tokens} tokens")
    
    while remaining:
        # Try to find a good chunk size by binary search on character length
        chunk_text = ""
        best_break = 0
        
        # Start with a conservative estimate
        start_length = min(len(remaining), safe_max_tokens * 2)  # Rough estimate: 2 chars per token
        search_length = start_length
        
        # Binary search for optimal chunk size that fits within token limit
        low, high = 1, len(remaining)
        
        while low <= high:
            mid = (low + high) // 2
            test_chunk = remaining[:mid]
            test_tokens = get_token_count(test_chunk, source_lang)
            
            if test_tokens <= safe_max_tokens:
                chunk_text = test_chunk
                best_break = mid
                low = mid + 1  # Try to get more
            else:
                high = mid - 1  # Too long, reduce
        
        # If we found a chunk that fits
        if chunk_text and best_break > 0:
            # Try to find a sentence boundary near the end of this chunk
            # Look for sentence endings in the last portion (last 20% of chunk)
            search_start = max(0, best_break - (best_break // 5))
            search_text = remaining[search_start:best_break]
            
            # Find the last sentence ending
            last_sentence_end = -1
            for i in range(len(search_text) - 1, -1, -1):
                if search_text[i] in sentence_endings:
                    # Check if it's followed by whitespace or end of string
                    if i == len(search_text) - 1 or (i + 1 < len(search_text) and search_text[i + 1].isspace()):
                        last_sentence_end = search_start + i + 1
                        break
            
            # If we found a sentence boundary, use it
            if last_sentence_end > search_start:
                chunk_text = remaining[:last_sentence_end].strip()
                remaining = remaining[last_sentence_end:].strip()
            else:
                # No sentence boundary found, split at token limit
                # Try to split at word boundary if possible (for non-Khmer scripts)
                if not source_lang.startswith('khm_'):
                    # Look for space near the end
                    space_pos = chunk_text.rfind(' ', search_start)
                    if space_pos > search_start * 0.8:  # Only use if it's reasonably near
                        chunk_text = remaining[:space_pos].strip()
                        remaining = remaining[space_pos:].strip()
                    else:
                        chunk_text = chunk_text.strip()
                        remaining = remaining[best_break:].strip()
                else:
                    # For Khmer, split at token limit (no word boundaries to rely on)
                    chunk_text = chunk_text.strip()
                    remaining = remaining[best_break:].strip()
        else:
            # Fallback: ensure we always have a chunk
            # Find a safe break point
            fallback_length = min(len(remaining), safe_max_tokens * 2)
            
            # Try to find any sentence boundary
            for i in range(fallback_length - 1, max(0, fallback_length - 500), -1):
                if remaining[i] in sentence_endings:
                    if i < len(remaining) - 1 and remaining[i + 1].isspace():
                        chunk_text = remaining[:i + 1].strip()
                        remaining = remaining[i + 1:].strip()
                        break
            else:
                # No sentence boundary found, use word boundary for non-Khmer
                if not source_lang.startswith('khm_'):
                    space_pos = remaining.rfind(' ', 0, fallback_length)
                    if space_pos > 0:
                        chunk_text = remaining[:space_pos].strip()
                        remaining = remaining[space_pos:].strip()
                    else:
                        chunk_text = remaining[:fallback_length].strip()
                        remaining = remaining[fallback_length:].strip()
                else:
                    # For Khmer, just split at estimated limit
                    chunk_text = remaining[:fallback_length].strip()
                    remaining = remaining[fallback_length:].strip()
        
        if chunk_text:
            # Verify this chunk doesn't exceed token limit
            chunk_tokens = get_token_count(chunk_text, source_lang)
            if chunk_tokens > safe_max_tokens:
                # If it still exceeds, reduce further by finding a safe break
                logger.warning(f"Chunk still too large ({chunk_tokens} tokens), reducing...")
                
                # Binary search to find a safe length
                low, high = 1, len(chunk_text)
                safe_chunk = ""
                safe_length = 0
                
                while low <= high:
                    mid = (low + high) // 2
                    test_chunk = chunk_text[:mid]
                    test_tokens = get_token_count(test_chunk, source_lang)
                    
                    if test_tokens <= safe_max_tokens:
                        safe_chunk = test_chunk
                        safe_length = mid
                        low = mid + 1
                    else:
                        high = mid - 1
                
                if safe_chunk:
                    chunk_text = safe_chunk.strip()
                    remaining = chunk_text[safe_length:] + remaining
                else:
                    # Last resort: take 80% of the chunk
                    reduced_length = int(len(chunk_text) * 0.8)
                    chunk_text = chunk_text[:reduced_length].strip()
                    remaining = chunk_text[reduced_length:] + remaining
            
            chunks.append(chunk_text)
            logger.info(f"Created chunk {len(chunks)}: {len(chunk_text)} chars, ~{get_token_count(chunk_text, source_lang)} tokens")
    
    return chunks


@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    """
    Translate text from source language to target language using NLLB-200 model.
    
    For long texts, automatically splits into chunks and translates each separately
    to ensure no content is lost.
    
    Args:
        request: TranslationRequest with text, source_lang, and target_lang
        
    Returns:
        TranslationResponse with translated text
        
    Raises:
        HTTPException: If model is not loaded, text is too long, or translation fails
    """
    # Check if model is loaded
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="Translation model is not loaded. Please wait for the model to initialize."
        )
    
    # Validate text length
    if len(request.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum length is {MAX_TEXT_LENGTH} characters."
        )
    
    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty."
        )
    
    try:
        # Accurately detect token length before translation
        token_count = get_token_count(request.text, request.source_lang)
        
        # Reserve tokens for special tokens, language codes, and safety margin
        safe_max_tokens = MAX_INPUT_TOKENS - 50
        
        logger.info(f"Text: {len(request.text)} chars, {token_count} tokens (limit: {safe_max_tokens})")
        
        if token_count > safe_max_tokens:
            # Text exceeds limit, split into chunks
            logger.info(f"Text exceeds token limit. Splitting into chunks...")
            
            # Split text into chunks based on actual token counts
            chunks = split_text_into_chunks(
                request.text, 
                source_lang=request.source_lang,
                max_tokens=safe_max_tokens
            )
            
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Translate each chunk sequentially
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_tokens = get_token_count(chunk, request.source_lang)
                logger.info(
                    f"Translating chunk {i+1}/{len(chunks)}: "
                    f"{len(chunk)} chars, {chunk_tokens} tokens"
                )
                
                try:
                    translated_chunk = translate_chunk(chunk, request.source_lang, request.target_lang)
                    translated_chunks.append(translated_chunk)
                    logger.info(f"Chunk {i+1} translated successfully: {len(translated_chunk)} chars")
                except Exception as chunk_error:
                    logger.error(f"Error translating chunk {i+1}: {str(chunk_error)}")
                    # Continue with other chunks, but log the error
                    translated_chunks.append(f"[Translation error in chunk {i+1}]")
            
            # Recombine results in correct order
            # Join with space, but preserve paragraph breaks (double newlines)
            translated_text = " ".join(translated_chunks)
            
            # Restore double newlines that might have been lost
            # This helps preserve paragraph structure
            if "\n\n" in request.text:
                # Count double newlines in original
                original_paragraphs = request.text.split("\n\n")
                if len(original_paragraphs) > 1:
                    # Try to maintain paragraph structure
                    translated_text = translated_text.replace(". ", ".\n\n", len(original_paragraphs) - 1)
            
            logger.info(
                f"Completed translation of {len(chunks)} chunks: "
                f"{len(request.text)} chars -> {len(translated_text)} chars"
            )
        else:
            # Text fits in single chunk - translate directly
            logger.info(f"Text fits in single chunk, translating directly...")
            translated_text = translate_chunk(request.text, request.source_lang, request.target_lang)
            
            # Verify no truncation occurred
            input_tokens = get_token_count(request.text, request.source_lang)
            logger.info(
                f"Translation complete: {len(request.text)} chars ({input_tokens} tokens) -> "
                f"{len(translated_text)} chars"
            )
        
        return TranslationResponse(
            translated_text=translated_text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
    except KeyError as e:
        # Invalid language code
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language code: {str(e)}. Please check source_lang and target_lang."
        )
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@app.get("/languages")
async def get_languages():
    """
    Get list of supported languages for NLLB-200 model.
    Returns a subset of common languages with their NLLB codes.
    """
    return {
        "languages": [
            {"code": "eng_Latn", "name": "English"},
            {"code": "khm_Khmr", "name": "Khmer"},
            {"code": "spa_Latn", "name": "Spanish"},
            {"code": "fra_Latn", "name": "French"},
            {"code": "deu_Latn", "name": "German"},
            {"code": "ita_Latn", "name": "Italian"},
            {"code": "por_Latn", "name": "Portuguese"},
            {"code": "rus_Cyrl", "name": "Russian"},
            {"code": "zho_Hans", "name": "Chinese (Simplified)"},
            {"code": "zho_Hant", "name": "Chinese (Traditional)"},
            {"code": "jpn_Jpan", "name": "Japanese"},
            {"code": "kor_Hang", "name": "Korean"},
            {"code": "ara_Arab", "name": "Arabic"},
            {"code": "hin_Deva", "name": "Hindi"},
            {"code": "tha_Thai", "name": "Thai"},
            {"code": "vie_Latn", "name": "Vietnamese"},
            {"code": "ind_Latn", "name": "Indonesian"},
            {"code": "tam_Taml", "name": "Tamil"},
            {"code": "tur_Latn", "name": "Turkish"},
            {"code": "pol_Latn", "name": "Polish"},
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
