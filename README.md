# PDF Chat with Claude 📚

A Streamlit application that enables interactive conversations with PDF documents using Anthropic's Claude 3.5 Sonnet AI model. The app provides intelligent responses with precise citations from the source document.

## Features ✨

- 🤖 Powered by Claude 3.5 Sonnet for accurate and contextual responses
- 📑 Automatic citation tracking with page numbers and quoted text
- 💬 Interactive chat interface with message history
- 🔍 Processes PDFs in chunks for optimal performance
- 🎯 Citations linked directly to source pages
- 🛠️ Debug mode for troubleshooting
- 🔒 Secure API key handling

## Setup 🚀

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdf-chat-claude.git
cd pdf-chat-claude
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix/MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

5. Place your PDF documents in the `documents` folder.

## Usage 🎮

1. Start the application:
```bash
streamlit run pdf_chat.py
```

2. Open your browser at `http://localhost:8501`

3. The app will automatically load the PDF from the `documents` folder

4. Start asking questions about your document!

## How It Works 🔧

1. **PDF Processing**: The application chunks PDFs into manageable sections for optimal processing
2. **Conversation Management**: Maintains chat history while preventing common issues with empty messages
3. **Citation Tracking**: Automatically extracts and displays relevant citations with page numbers
4. **Response Generation**: Uses Claude 3.5 Sonnet to generate contextual responses based on the document content

## Requirements 📋

- Python 3.8+
- Anthropic API key
- Required packages (see `requirements.txt`):
  - streamlit
  - anthropic
  - python-docx
  - python-dotenv
  - PyPDF2

## Debug Mode 🐛

Enable debug mode in the sidebar to:
- View raw API requests and responses
- See detailed error messages
- Track conversation state

## Limitations ⚠️

- Currently supports text-based PDFs only
- Maximum token limit applies based on Claude's model constraints
- Single PDF document support per session

## Contributing 🤝

Feel free to open issues or submit pull requests with improvements!

## License 📄

[MIT License](LICENSE) 