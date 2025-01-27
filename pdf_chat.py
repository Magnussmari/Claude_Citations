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
    st.set_page_config(page_title="PDF Chat with Claude", page_icon="📚")
    st.title("📚 PDF Chat with Claude")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Debug mode
    debug_mode = st.sidebar.checkbox("Enable Debug Mode")
    
    # Sidebar settings
    with st.sidebar:
        st.title("⚙️ Settings")
        if not api_key:
            api_key = st.text_input("Enter Anthropic API Key", type="password")
        st.markdown("---")
        st.markdown("📖 **How to use**\n1. Upload PDFs to 'documents' folder\n2. Ask questions about the content\n3. View citations in responses")

    if not api_key:
        st.error("🔑 Please enter your Anthropic API key in the sidebar")
        return

    # PDF processing with enhanced error handling
    @st.cache_data(show_spinner=False)
    def process_pdf(file_path):
        try:
            documents = []
            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Create hash for cache validation
                content_hash = hashlib.md5(file.read()).hexdigest()
                file.seek(0)
                
                for start in range(0, num_pages, 100):
                    pdf_writer = PdfWriter()
                    page_range = range(start, min(start + 100, num_pages))
                    for page in page_range:
                        pdf_writer.add_page(pdf_reader.pages[page])
                    
                    pdf_bytes_io = io.BytesIO()
                    pdf_writer.write(pdf_bytes_io)
                    pdf_bytes = pdf_bytes_io.getvalue()
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    
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

    # Document selection
    pdf_path = "documents/Hrd. 2003_4119 nr. 425_2003.pdf"
    if not os.path.exists(pdf_path):
        st.error(f"📄 PDF file not found at {pdf_path}")
        return

    try:
        documents, content_hash = process_pdf(pdf_path)
    except:
        return

    # Initialize chat history with system message
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Ask me anything about the document!",
            "citations": []
        }]

    # Display chat messages with citations
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["citations"]:
                st.markdown("---")
                st.markdown("**References:**")
                for idx, cite in enumerate(message["citations"], 1):
                    source = f"`{cite['document']}`" if cite['document'] else "the document"
                    st.markdown(f"{idx}. From {source} (page {cite['start_page']}):  \n`{cite['text']}`")

    # Chat input
    if prompt := st.chat_input("Ask about your PDF"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt, "citations": []})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare API message with proper content structure
        client = anthropic.Anthropic(api_key=api_key)
        
        try:
            with st.chat_message("assistant"), st.spinner("Analyzing document..."):
                # Construct message with documents and prompt
                messages = [{
                    "role": "user",
                    "content": [
                        *documents,
                        {"type": "text", "text": prompt}
                    ]
                }]

                # Add conversation history
                history = st.session_state.messages[:-1]  # Exclude current prompt
                if history:  # Only add history if there are previous messages
                    for msg in history:
                        if msg["content"].strip():  # Only add messages with non-empty content
                            messages.append({
                                "role": msg["role"],
                                "content": [{"type": "text", "text": msg["content"]}]
                            })

                # Debug: Show raw request payload
                if debug_mode:
                    st.subheader("Debug Information")
                    st.json({"messages": messages})

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=messages,
                    temperature=0.3
                )

                # Validate API response structure
                if not response:
                    raise ValueError("Empty API response - no data received")
                if not hasattr(response, 'content'):
                    raise ValueError("Malformed API response - missing content field")
                
                # Debug: Show raw API response
                if debug_mode:
                    st.json(response.model_dump())

                # Process citations
                citations = []
                full_response = ""
                for content_block in getattr(response, 'content', []):
                    if content_block.type == "text":
                        full_response += content_block.text
                        if hasattr(content_block, 'citations') and content_block.citations:
                            for cite in content_block.citations:
                                citations.append({
                                    "document": getattr(cite, 'document_title', 'Unknown Document'),
                                    "start_page": getattr(cite, 'start_page_number', 0),
                                    "end_page": getattr(cite, 'end_page_number', 0),
                                    "text": getattr(cite, 'cited_text', '')[:150] + "..." 
                                })

                # Display response
                st.markdown(full_response)
                
                if citations:
                    st.markdown("---")
                    st.markdown("**References:**")
                    for idx, cite in enumerate(citations, 1):
                        source = f"`{cite['document']}`" if cite['document'] else "the document"
                        st.markdown(f"{idx}. From {source} (page {cite['start_page']}):  \n`{cite['text']}`")
                
                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "citations": citations
                })

        except Exception as e:
            error_msg = f"🚨 Error processing request: {str(e)}"
            st.error(error_msg)
            if debug_mode:
                st.code(traceback.format_exc())
            st.session_state.messages.pop()  # Remove failed prompt

if __name__ == "__main__":
    main()