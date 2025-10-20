# 📄 Document Extractor with Ollama + n8n

This project automatically:
- Watches `c:\test\source` for PDFs
- Sends text to local Ollama (`deepseek-r1`) running at http://127.0.0.1:11434
- Extracts these fields: DATE, INVOICE, CUSTOMER ID, SALESPERSON, TO, TOTAL
- Saves results as JSON + CSV in `c:\test\output`

## 🚀 Setup
1. Install [Ollama](https://ollama.com/download) and pull the model:
   ```bash
   ollama pull deepseek-r1
