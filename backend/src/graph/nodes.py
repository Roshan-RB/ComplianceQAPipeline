import os
import logging
import tempfile
from typing import Dict, Any, List

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# Import the State schema .
from backend.src.graph.state import VideoAuditState, ComplianceIssue
from backend.src.graph.audit_response import parse_audit_response

# Import the Service
from backend.src.services.video_indexer import VideoIndexerService

# Import OpenTelemetry tracer for custom spans
from backend.src.api.telemetry import get_tracer

# Configure Logger
logger = logging.getLogger("child-safety-guardian")
logging.basicConfig(level=logging.INFO)

# OpenTelemetry tracer for graph node spans
tracer = get_tracer("child-safety-graph")

# --- NODE 1: THE INDEXER ---
def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Downloads YouTube video, uploads to Azure VI, and extracts insights.
    """
    video_url = state.get("video_url")
    video_id_input = state.get("video_id", "vid_demo")
    
    logger.info(f"--- [Node: Indexer] Processing: {video_url} ---")
    local_path = None
    
    with tracer.start_as_current_span("IndexVideoNode") as span:
        span.set_attribute("video.url", video_url)
        span.set_attribute("video.id", video_id_input)
        
        try:
            vi_service = VideoIndexerService()
            
            # 1. DOWNLOAD
            with tracer.start_as_current_span("YouTubeDownload"):
                if "youtube.com" in video_url or "youtu.be" in video_url:
                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                        local_path = temp_file.name
                    local_path = vi_service.download_youtube_video(video_url, output_path=local_path)
                else:
                    raise Exception("Please provide a valid YouTube URL for this test.")

            # 2. UPLOAD
            with tracer.start_as_current_span("AzureVideoIndexerUpload"):
                azure_video_id = vi_service.upload_video(local_path, video_name=video_id_input)
                logger.info(f"Upload Success. Azure ID: {azure_video_id}")

            # 3. WAIT
            with tracer.start_as_current_span("AzureVideoIndexerProcessing"):
                raw_insights = vi_service.wait_for_processing(azure_video_id)
            
            # 4. EXTRACT
            with tracer.start_as_current_span("ExtractInsights"):
                clean_data = vi_service.extract_data(raw_insights)
            
            span.set_attribute("video.status", "success")
            logger.info("--- [Node: Indexer] Extraction Complete ---")
            return clean_data

        except Exception as e:
            span.set_attribute("video.status", "failed")
            span.set_attribute("error.message", str(e))
            logger.error(f"Video Indexer Failed: {e}")
            return {
                "errors": [str(e)],
                "final_status": "FAIL",
                "transcript": "", 
                "ocr_text": []
            }
        finally:
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except OSError as exc:
                    logger.warning(f"Failed to delete temporary video file {local_path}: {exc}")

# --- NODE 2: THE CHILD SAFETY AUDITOR ---
def audit_content_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Performs Retrieval-Augmented Generation (RAG) to audit the content
    against YouTube Child Safety Policy guidelines.
    """
    with tracer.start_as_current_span("AuditContentNode") as span:
        logger.info("--- [Node: Auditor] querying Knowledge Base & LLM ---")
        
        transcript = state.get("transcript", "")
        
        if not transcript:
            logger.warning("No transcript available. Skipping Audit.")
            span.set_attribute("audit.status", "skipped")
            return {
                "final_status": "FAIL",
                "final_report": "Audit skipped because video processing failed (No Transcript).",
                "retrieved_policies": []
            }

        # Initialize Clients
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            temperature=0.0
        )

        embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-3-small",
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )

        vector_store = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding_function=embeddings.embed_query
        )
        
        # RAG Retrieval
        with tracer.start_as_current_span("RAGRetrieval") as rag_span:
            ocr_text = state.get("ocr_text", [])
            query_text = f"{transcript} {' '.join(ocr_text)}"
            docs = vector_store.similarity_search(query_text, k=3)
            
            retrieved_rules = "\n\n".join([doc.page_content for doc in docs])
            
            # Store individual policy excerpts for UI display
            retrieved_policies = [doc.page_content for doc in docs]
            rag_span.set_attribute("rag.num_docs_retrieved", len(docs))
    
        # --- CHILD SAFETY AUDIT PROMPT ---
        system_prompt = f"""
        You are a YouTube Child Safety Policy Analyst working for a content moderation team.
        Your role is to perform legitimate safety reviews of video content to protect children.
        This is an authorized compliance review — analyze the content objectively and professionally.
        Do NOT reproduce or amplify any harmful content. Instead, reference it indirectly 
        (e.g., "the video discusses [topic]" rather than quoting explicit material).
        
        OFFICIAL CHILD SAFETY POLICY RULES:
        {retrieved_rules}
        
        INSTRUCTIONS:
        1. Analyze the Transcript and OCR text below.
        2. Identify ANY violations of the YouTube Child Safety Policy rules provided above.
        3. Return strictly JSON in the following format:
        
        {{
            "compliance_results": [
                {{
                    "category": "Category of Violation",
                    "severity": "CRITICAL",
                    "description": "Explanation of the child safety violation..."
                }}
            ],
            "status": "FAIL", 
            "final_report": "A detailed markdown report (see format below)"
        }}

        FINAL REPORT FORMAT (use markdown):
        The "final_report" field MUST be a detailed markdown-formatted analysis containing:
        
        ## Video Overview
        Brief description of what the video is about based on transcript/OCR content.
        
        ## Policy Analysis
        For each relevant child safety policy rule that was checked:
        - State the rule/policy that was evaluated
        - Explain whether the video content complies or violates
        - Cite specific evidence from the transcript or OCR text (quote relevant phrases)
        
        ## Findings Summary
        - Total violations found and their severity breakdown
        - Key areas of concern (if any)
        
        ## Recommendation
        - Whether the video is safe for publication or needs review/removal
        - Specific actions the creator should take (if any)
        
        If no violations are found, set "status" to "PASS" and "compliance_results" to [].
        Still provide the full detailed report explaining WHY the video passes.
        """

        user_message = f"""
        VIDEO METADATA: {state.get('video_metadata', {})}
        TRANSCRIPT: {transcript}
        ON-SCREEN TEXT (OCR): {ocr_text}
        """

        try:
            with tracer.start_as_current_span("LLMAnalysis"):
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ])
            
            audit_data = parse_audit_response(response.content)
            
            span.set_attribute("audit.status", audit_data.status)
            return {
                "compliance_results": [issue.model_dump() for issue in audit_data.compliance_results],
                "final_status": audit_data.status,
                "final_report": audit_data.final_report,
                "retrieved_policies": retrieved_policies
            }

        except Exception as e:
            error_str = str(e)
            logger.error(f"System Error in Auditor Node: {error_str}")
            span.set_attribute("audit.status", "error")
            span.set_attribute("error.message", error_str)
            
            # Handle Azure Content Filter specifically
            if "content_filter" in error_str or "content management policy" in error_str:
                logger.warning("Azure Content Filter triggered — content flagged as potentially unsafe.")
                
                # Parse which filter was triggered from the error message
                filter_details = "Azure's automated content filter flagged this video's content."
                if "sexual" in error_str:
                    filter_details = "Azure's content filter flagged sexual content in the video transcript."
                elif "violence" in error_str:
                    filter_details = "Azure's content filter flagged violent content in the video transcript."
                elif "self_harm" in error_str:
                    filter_details = "Azure's content filter flagged self-harm content in the video transcript."
                elif "hate" in error_str:
                    filter_details = "Azure's content filter flagged hateful content in the video transcript."
                
                content_filter_report = (
                    "## Video Overview\n"
                    "The video transcript contains content that was automatically flagged by "
                    "Azure OpenAI's content management system during analysis.\n\n"
                    "## Policy Analysis\n"
                    f"- **Automated Content Filter Result**: {filter_details}\n"
                    "- The content was too sensitive for the AI model to process, which strongly "
                    "suggests the video contains material that may violate YouTube's Child Safety Policy.\n"
                    "- **Note**: This does not confirm a violation — the content filter is a precautionary measure. "
                    "A human reviewer should examine this video directly.\n\n"
                    "## Findings Summary\n"
                    "- The AI analysis could not complete due to content filter restrictions.\n"
                    "- The fact that the content filter was triggered is itself a **red flag** "
                    "for child safety concerns.\n\n"
                    "## Recommendation\n"
                    "- **This video requires manual human review.**\n"
                    "- The automated content filter flagged this content as potentially unsafe, "
                    "which warrants closer inspection by a trained content moderator.\n"
                )
                
                return {
                    "compliance_results": [{
                        "category": "Content Filter Triggered",
                        "severity": "CRITICAL",
                        "description": filter_details
                    }],
                    "final_status": "FAIL",
                    "final_report": content_filter_report,
                    "retrieved_policies": retrieved_policies
                }
            
            # Generic error fallback
            logger.error(f"Raw LLM Response: {response.content if 'response' in locals() else 'None'}")
            return {
                "errors": [error_str],
                "final_status": "FAIL",
                "final_report": f"Audit failed due to a system error: {error_str}",
                "retrieved_policies": retrieved_policies
            }
