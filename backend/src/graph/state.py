import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional, NotRequired


#define the schema for compliance result

class ComplianceIssue(TypedDict):
    category : str
    description : str #specific detail of violation
    severity : str #CRITICAL | WARNING
    timestamp : NotRequired[Optional[str]]
    
class VideoAuditState(TypedDict):
    '''
    Defines the data schema for langgraph execution content
    Main container : holds all the information about the child safety audit
    right from the initial URL to the final report
    '''

    #input parameters
    video_url : str
    video_id : str

    #ingestion and extraction data
    local_file_path : Optional[str]
    video_metadata : Dict[str, Any] #{"duration" : 15, "resolution" : "1080p"}
    transcript : Optional[str] #fully extracted speech-to-text
    ocr_text : List[str]

    #analysis output
    #stores the list of all violations found by AI
    compliance_results : Annotated[List[ComplianceIssue], operator.add]

    # RAG context - stores the policy excerpts retrieved from the knowledge base
    retrieved_policies : List[str]

    #final deliverables
    final_status : str #PASS | FAIL
    final_report : str #markdown format
    

    #system observabilty
    # errors : API timeout, system level errors
    # list of system level carshes
    errors : Annotated[List[str], operator.add]
