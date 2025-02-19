# Claude Citations Test

## Introduction
On January 23rd, 2025, Anthropic introduced a Citations API feature ([announcement](https://www.anthropic.com/news/introducing-citations-api)) that enables precise source attribution in AI responses. This repository contains a simple test implementation built by Magnus Smari Smarason ([www.smarason.is](https://www.smarason.is/)) to explore and demonstrate these capabilities.

The Citations API allows Claude to:
- Provide accurate page-level citations
- Track quoted content from source documents
- Maintain citation validity across conversation turns
- Support multiple document formats including PDFs (in development)

This implementation serves as both a practical example and a starting point for developers looking to integrate Claude's citation features into their own applications.

---

# PDF Chat with Claude Citations
## Quick Start

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Anthropic API key to `.env`
4. Place PDF files in the `documents` folder (sample included: "Machines of Loving Grace" by Dario Amodei)
5. Run: `streamlit run Claude_citations_v1.py`

## Sample Document
This implementation includes "Machines of Loving Grace" by Dario Amodei (October 2024) as a sample PDF to test the citation capabilities. This thought-provoking essay explores how artificial intelligence could positively transform society while addressing key challenges and considerations.

To try it out:
1. Launch the application
2. Ask questions about AI's potential impact on society
3. Observe how Claude provides cited responses from specific pages

You can replace this with your own PDFs or use it as a reference implementation.


## Overview
This is a simple experiment with Claude Citations using PDF files. The application is built by Magnus Smari Smarason ([www.smarason.is](https://www.smarason.is/)) to explore Claude's citation capabilities.

The application allows users to:
- Upload PDF documents
- Ask questions about the content
- Receive responses with precise citations
- Debug API interactions when needed

## Features
- PDF file processing with chunking for large documents
- Citation tracking and display
- Error handling and debugging mode
- Conversation history management
- Clean, user-friendly interface

---

# Build with Claude: Citations & PDF Support

## Overview
Claude 3.5 introduces two key capabilities to enhance your application’s functionality:
1. **Citations**: Attach precise source references to the model’s responses, increasing reliability and traceability for content drawn from uploaded documents.
2. **PDF Support**: Provide full PDF files for Claude to analyze text, images, charts, and tables within a single request.

This document covers:
- How to enable and use citations.
- Supported document types (plain text, PDF, custom content).
- How PDF processing works and best practices.

---

## 1. Citations

### 1.1 Key Benefits
- **Cost Savings**: Quoted text in `cited_text` does **not** count towards your output tokens.
- **Improved Citation Reliability**: The system automatically parses and standardizes citations, guaranteeing valid pointers to your documents.
- **Better Citation Quality**: Compared to a purely prompt-based approach, Claude is more likely to cite the most relevant portions of a document.

### 1.2 Enabling Citations
To enable citations, embed your documents in the request payload with `citations.enabled = true`.  
> **Important**: All documents in a single request must have citations enabled or disabled—mixing is not currently supported.

For example, to send plain text content:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": "The grass is green. The sky is blue."
                    },
                    "title": "My Document",
                    "context": "This is a trustworthy document.",
                    "citations": {"enabled": True}
                },
                {
                    "type": "text",
                    "text": "What color is the grass and sky?"
                }
            ]
        }
    ]
)
print(response)
```

### 1.3 How It Works

1. **Provide Documents & Enable Citations**  
   - Supply PDFs, plain text, or custom content documents.
   - Set `citations.enabled = true` for each document.

2. **Documents Get Processed**  
   - Text is “chunked” to define the minimum granularity of possible citations.  
     - PDFs/Plain Text: Automatically chunked by sentence.  
     - Custom Content: No further chunking; you define the block structure.

3. **Claude Provides Cited Responses**  
   - The model’s output is broken into text blocks with associated citations.  
   - Citations reference the exact location in the source document.

#### Document Types & Citation Formats
| Type           | Best For                                                                      | Chunking            | Citation Format               |
|----------------|-------------------------------------------------------------------------------|---------------------|--------------------------------|
| **Plain Text** | Simple text documents, prose                                                  | Sentence            | Character indices (0-indexed)  |
| **PDF**        | Documents in PDF format (with extractable text)                               | Sentence            | Page numbers (1-indexed)       |
| **Custom**     | Lists, transcripts, or special formatting where you control citation granularity | No additional chunking | Content block indices (0-indexed) |

### 1.4 Response Structure
A typical cited response has multiple text blocks. Each block’s `citations` array contains references like so:

```json
{
  "content": [
    {
      "type": "text",
      "text": "According to the document, "
    },
    {
      "type": "text",
      "text": "the grass is green",
      "citations": [
        {
          "type": "char_location",
          "cited_text": "The grass is green.",
          "document_index": 0,
          "document_title": "My Document",
          "start_char_index": 0,
          "end_char_index": 20
        }
      ]
    }
  ]
}
```

### 1.5 Performance & Token Costs
- Enabling citations adds minimal overhead to **input** tokens due to document chunking.
- The extracted `cited_text` does **not** count towards **output** tokens, reducing overall cost.

---

## 2. PDF Support

Claude 3.5 Sonnet can process PDFs by extracting text and analyzing page images (e.g., for charts and visuals). This allows you to ask for insights on both textual and non-textual data in a PDF.

### 2.1 Requirements & Limits
- **Maximum request size**: 32MB
- **Maximum pages per request**: 100
- **Format**: Standard PDF (no password/encryption)

> **Note**: For scanned PDFs without extractable text, only the image portion is available; text cannot be extracted.

### 2.2 Sending a PDF to Claude
Below is a minimal example using the Messages API with a base64-encoded PDF:

```python
import anthropic
import base64
import httpx

client = anthropic.Anthropic()

# Load and encode the PDF
pdf_url = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
pdf_data = base64.standard_b64encode(httpx.get(pdf_url).content).decode("utf-8")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": "What are the key findings in this document?"
                }
            ]
        }
    ],
)

print(message.content)
```

### 2.3 How PDF Analysis Works

1. **Extraction**: Each page is converted into an image; text is extracted from that page.  
2. **Analysis**: Claude combines page text with the page image for a full visual + textual understanding.  
3. **Response**: You receive a standard Claude completion, now informed by PDF data.

### 2.4 Optimizing PDF Processing
- **Place PDFs early** in your request for faster analysis.
- Use standard, legible text and proper orientation.
- If your PDF is large, **split into smaller chunks** to stay under size limits.
- Enable **prompt caching** if you repeatedly query the same PDF.

#### Example: Prompt Caching
```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    },
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": "Analyze this document."
                }
            ]
        }
    ],
)
```

---

## 3. Scaling Your Implementation

### 3.1 Batch Processing
For high-volume use cases, you can send multiple requests simultaneously via the [Message Batches API](https://docs.anthropic.com/claude/reference/message-batches).

```python
message_batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "doc1",
            "params": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text",
                                "text": "Summarize this document."
                            }
                        ]
                    }
                ]
            }
        }
    ]
)
```

### 3.2 Tool Use & Chaining
Combine Claude’s PDF and citations capabilities with external tools to:
- Extract structured data from documents.
- Automate repeated tasks (e.g., financial analysis, contract review).

---

## 4. Next Steps

- **Enhance UI/UX**:
  - Add dark/light mode toggle
  - Implement collapsible citation sections
  - Create a document preview panel
  - Add progress indicators for long operations
- **Expand Features**:
  - Enable multi-document comparison
  - Add document search functionality
  - Implement conversation export
  - Create custom citation display formats
- **Performance Optimization**:
  - Fine-tune chunking parameters
  - Implement caching for repeated queries
  - Add batch processing for multiple documents
  - Optimize memory usage for large PDFs
- **Developer Tools**:
  - Add comprehensive logging
  - Create a testing framework
  - Implement a CI/CD pipeline
  - Add performance monitoring

---

### Additional Resources
- [Anthropic Docs: Citations Overview](https://docs.anthropic.com/en/docs/build-with-claude/citations#example-plain-text-citation)
- [Anthropic Docs: PDF Support](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)
- [API Reference](https://docs.anthropic.com/en/api/getting-started)

![Claude Citations Test](src/img/Claude_citations_test1_260125.png)
