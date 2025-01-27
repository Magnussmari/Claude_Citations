"""
PDF Chat Application with Claude AI
This application enables interactive conversations with PDF documents using Anthropic's Claude 3.5 Sonnet.
It processes PDFs in chunks, maintains conversation history, and provides cited responses from the document.
"""

import streamlit as st
import anthropic
import base64
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
import io
import hashlib
import traceback

def main():
    # Configure Streamlit page settings
    st.set_page_config(page_title="PDF Chat with Claude", page_icon="📚")
    st.title("📚 PDF Chat with Claude")
    
    # Initialize environment and API key
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Debug mode toggle in sidebar for troubleshooting
    debug_mode = st.sidebar.checkbox("Enable Debug Mode")
    
    # Sidebar configuration and instructions
    with st.sidebar:
        st.title("⚙️ Settings")
        if not api_key:
            api_key = st.text_input("Enter Anthropic API Key", type="password")
        st.markdown("---")
        st.markdown("📖 **How to use**\n1. Upload PDFs to 'documents' folder\n2. Ask questions about the content\n3. View citations in responses")

    @st.cache_data(show_spinner=False)
    def process_pdf(file_path):
        """
        Process PDF file into chunks suitable for Claude API.
        Uses caching to avoid reprocessing the same file multiple times.
        Splits PDF into 100-page chunks to stay within token limits.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            tuple: (list of document chunks, content hash for cache validation)
        """
        try:
            documents = []
            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Generate hash for cache validation
                content_hash = hashlib.md5(file.read()).hexdigest()
                file.seek(0)
                
                # Process PDF in chunks of 100 pages
                for start in range(0, num_pages, 100):
                    pdf_writer = PdfWriter()
                    page_range = range(start, min(start + 100, num_pages))
                    for page in page_range:
                        pdf_writer.add_page(pdf_reader.pages[page])
                    
                    # Convert PDF chunk to base64 for API
                    pdf_bytes_io = io.BytesIO()
                    pdf_writer.write(pdf_bytes_io)
                    pdf_bytes = pdf_bytes_io.getvalue()
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    
                    # Create document chunk with metadata
                    documents.append({
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64_pdf
                        },
                        "title": f"{os.path.basename(file_path)} (pages {start+1}-{min(start+100, num_pages)})",
                        "citations": {"enabled": True}
                    })
            return documents, content_hash
        except Exception as e:
            st.error(f"PDF Processing Error: {str(e)}")
            if debug_mode:
                st.code(traceback.format_exc())
            raise

    # Load and validate PDF document
    pdf_path = "documents/Dario_Amodai Machines of loving grace.pdf"
    if not os.path.exists(pdf_path):
        st.error(f"📄 PDF file not found at {pdf_path}")
        return

    try:
        documents, content_hash = process_pdf(pdf_path)
    except:
        return

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Ask me anything about the document!",
            "citations": []
        }]

    # Display chat history with citations
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["citations"]:
                st.markdown("---")
                st.markdown("**References:**")
                for idx, cite in enumerate(message["citations"], 1):
                    source = f"`{cite['document']}`" if cite['document'] else "the document"
                    st.markdown(f"{idx}. From {source} (page {cite['start_page']}):  \n`{cite['text']}`")

    # Handle user input and generate response
    if prompt := st.chat_input("Ask about your PDF"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "citations": []})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        try:
            with st.chat_message("assistant"), st.spinner("Analyzing document..."):
                # Prepare message structure for API
                messages = [{
                    "role": "user",
                    "content": [
                        *documents,  # Include PDF chunks
                        {"type": "text", "text": prompt}  # Add user question
                    ]
                }]

                # Add conversation history, excluding empty messages
                history = st.session_state.messages[:-1]  # Exclude current prompt
                if history:  # Only add history if there are previous messages
                    for msg in history:
                        if msg["content"].strip():  # Skip empty messages
                            messages.append({
                                "role": msg["role"],
                                "content": [{"type": "text", "text": msg["content"]}]
                            })

                # Show debug information if enabled
                if debug_mode:
                    st.subheader("Debug Information")
                    st.json({"messages": messages})

                # Make API call to Claude
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=messages,
                    temperature=0.3  # Lower temperature for more focused responses
                )

                # Validate API response
                if not response:
                    raise ValueError("Empty API response - no data received")
                if not hasattr(response, 'content'):
                    raise ValueError("Malformed API response - missing content field")
                
                # Show raw API response in debug mode
                if debug_mode:
                    st.json(response.model_dump())

                # Process response and extract citations
                citations = []
                full_response = ""
                for content_block in getattr(response, 'content', []):
                    if content_block.type == "text":
                        full_response += content_block.text
                        # Extract citations if present
                        if hasattr(content_block, 'citations') and content_block.citations:
                            for cite in content_block.citations:
                                citations.append({
                                    "document": getattr(cite, 'document_title', 'Unknown Document'),
                                    "start_page": getattr(cite, 'start_page_number', 0),
                                    "end_page": getattr(cite, 'end_page_number', 0),
                                    "text": getattr(cite, 'cited_text', '')[:150] + "..."  # Truncate long citations
                                })

                # Display the response and citations
                st.markdown(full_response)
                
                if citations:
                    st.markdown("---")
                    st.markdown("**References:**")
                    for idx, cite in enumerate(citations, 1):
                        source = f"`{cite['document']}`" if cite['document'] else "the document"
                        st.markdown(f"{idx}. From {source} (page {cite['start_page']}):  \n`{cite['text']}`")
                
                # Update chat history with assistant's response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "citations": citations
                })

        except Exception as e:
            # Handle errors and provide debug information
            error_msg = f"🚨 Error processing request: {str(e)}"
            st.error(error_msg)
            if debug_mode:
                st.code(traceback.format_exc())
            st.session_state.messages.pop()  # Remove failed prompt from history

if __name__ == "__main__":
    main()