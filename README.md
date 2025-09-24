# PDF Document RAG Pipeline

A comprehensive pipeline for parsing PDF documents using IBM Granite's Docling model, with a RAG (Retrieval-Augmented Generation) system powered by Nomic embeddings and FAISS vector storage.

## Features

- **PDF Parsing**: Extract text, tables, and images from PDFs using Docling
- **Markdown Export**: Convert PDFs to structured markdown format
- **Smart Chunking**: Intelligent text splitting that preserves document structure
- **Vector Search**: Fast similarity search using FAISS
- **Embeddings**: Support for both Nomic cloud embeddings and local models
- **LLM Integration**: Optional local LLM answering via Ollama (no paid API required)
- **CLI Interface**: Rich command-line interface with interactive search
- **Batch Processing**: Process entire directories of PDFs

## Installation

1. Clone the repository:
```bash
git clone <your-repo>
cd pdf-rag-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env and add your Nomic API key (optional)
# Optionally set local LLM defaults
# LLM_PROVIDER=ollama
# LLM_MODEL=llama3.2
```

## Configuration

Edit the `.env` file to configure:

- `NOMIC_API_KEY`: Your Nomic API key (get from https://atlas.nomic.ai/)
- `FAISS_INDEX_PATH`: Path to store the FAISS index
- `CHUNK_SIZE`: Maximum size of text chunks (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)

## Usage

### Command Line Interface

The pipeline provides a rich CLI with multiple commands:

```bash
# Show help
python cli.py --help

# Parse a single PDF
python cli.py parse document.pdf

# Parse all PDFs in a directory
python cli.py parse /path/to/pdfs/

# Use local embeddings instead of Nomic
python cli.py parse document.pdf --use-local

# Interactive search
python cli.py search

# Query with questions (generate answer with local Ollama)
python cli.py query --llm-provider ollama --llm-model llama3.2

# Show index statistics
python cli.py stats

# Export index
python cli.py export my_index.faiss

# Load existing index
python cli.py load my_index.faiss

# Clear index
python cli.py clear
```

### Python API

```python
from src.rag_pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline()

# Process a PDF
parsed_doc = pipeline.process_pdf("document.pdf")

# Process multiple PDFs
docs = pipeline.process_directory("/path/to/pdfs/")

# Search for relevant content
results = pipeline.search("What is machine learning?", k=5)

# Query with context retrieval
response = pipeline.query("Explain the main concepts", k=3)

# Save and load index
pipeline.save_index()
pipeline.load_index()

# Get statistics
stats = pipeline.get_statistics()
```

## Example Workflow

1. **Prepare your PDFs**:
   Place your PDF documents in a directory (e.g., `./data/pdfs/`)

2. **Parse and index the documents**:
   ```bash
   python cli.py parse ./data/pdfs/
   ```
   This will:
   - Parse all PDFs using Docling
   - Convert them to markdown (saved in `./data/processed/`)
   - Split into chunks
   - Generate embeddings
   - Build the FAISS index

3. **Search the indexed documents**:
   ```bash
   python cli.py search
   ```
   Enter your search queries interactively

4. **Ask questions**:
   ```bash
   python cli.py query
   ```
   Ask natural language questions about your documents

## Project Structure

```
.
├── cli.py                 # CLI interface
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── src/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── pdf_parser.py     # PDF parsing with Docling
│   ├── text_splitter.py  # Document chunking
│   ├── embeddings.py     # Nomic/local embeddings
│   ├── vector_store.py   # FAISS vector storage
│   └── rag_pipeline.py   # Main RAG pipeline
├── data/
│   ├── pdfs/            # Input PDF files
│   ├── processed/       # Markdown outputs
│   └── faiss_index      # Vector index storage
└── cache/               # Docling cache directory
```

## Advanced Features

### Using Local Embeddings

If you don't have a Nomic API key, you can use local sentence-transformer models:

```bash
python cli.py parse document.pdf --use-local
```

This will use the `all-MiniLM-L6-v2` model by default.

### Using a Local LLM with Ollama

Ensure Ollama is installed and a model is available (`ollama pull llama3.2`). Then:

```bash
python cli.py query --llm-provider ollama --llm-model llama3.2
```

Or set defaults in `.env`:

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

You can also use the Python API and the native `ollama` client directly:

```python
import ollama

response = ollama.generate(model='llama3.2', prompt='Why is the sky blue?')
print(response['response'])

messages = [
    {'role': 'user', 'content': 'Why is the sky blue?'}
]
chat_response = ollama.chat(model='llama3.2', messages=messages)
print(chat_response['message']['content'])
```

### Custom Chunking

Modify chunking parameters in `.env`:

```env
CHUNK_SIZE=1500        # Larger chunks
CHUNK_OVERLAP=300      # More overlap for context
```

### Batch Processing

Process large document collections efficiently:

```python
from src.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# Process in batches
docs = pipeline.process_directory(
    "/large/document/collection/",
    pattern="**/*.pdf"  # Recursive search
)
```

## Performance Tips

1. **Use local embeddings** for faster processing without API calls
2. **Adjust chunk size** based on your documents' structure
3. **Enable caching** to avoid re-parsing documents
4. **Use batch processing** for large collections
5. **Export indexes** for backup and sharing

## Troubleshooting

### Common Issues

1. **Nomic API Key Error**: 
   - Ensure your API key is set in `.env`
   - Check your Nomic account has available credits

2. **Memory Issues with Large PDFs**:
   - Reduce `CHUNK_SIZE` in configuration
   - Process PDFs in smaller batches

3. **Slow Processing**:
   - Use local embeddings (`--use-local`)
   - Enable Docling caching

4. **FAISS Installation Issues**:
   - Install CPU version: `pip install faiss-cpu`
   - For GPU: `pip install faiss-gpu`

## Dependencies

- **Docling**: IBM's document parsing library
- **Nomic**: Cloud embedding service
- **FAISS**: Facebook's similarity search library
- **LangChain**: Document processing utilities
- **Click & Rich**: CLI interface
- **Sentence-Transformers**: Local embeddings

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- IBM Granite team for the Docling library
- Nomic AI for embedding services
- Facebook Research for FAISS
- LangChain community