Below is a concise developer-focused document that consolidates the citations and PDF support details for Claude 3.5 Sonnet and Haiku. Use this as a reference for integrating and optimizing these features in your applications.

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
      "citations": [{
        "type": "char_location",
        "cited_text": "The grass is green.",
        "document_index": 0,
        "document_title": "My Document",
        "start_char_index": 0,
        "end_char_index": 20
      }]
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
- **Explore advanced usage**: Merge citations with PDF support to provide both textual and visual references to your end users.
- **Leverage chunking**: Adjust chunk sizes via custom documents to fine-tune citation granularity.
- **Provide Feedback**: Anthropic welcomes improvements or feature suggestions via [this feedback form](https://docs.anthropic.com).

---

### Additional Resources
- [Anthropic Docs: Citations Overview]([https://docs.anthropic.com/claude/docs/citations](https://docs.anthropic.com/en/docs/build-with-claude/citations#example-plain-text-citation))
- [Anthropic Docs: PDF Support]([https://docs.anthropic.com/claude/docs/pdf-suppor](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)t)
- [API Reference]([https://docs.anthropic.com/claude/reference](https://docs.anthropic.com/en/api/getting-started))

---

**Happy building with Claude!**