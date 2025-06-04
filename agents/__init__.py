"""
Agents package for the multi-agent system.
"""
from .classifier import ClassifierAgent, get_classifier_agent
from .email_agent import EmailAgent, get_email_agent
from .json_agent import JSONAgent, get_json_agent
from .pdf_agent import PDFAgent, get_pdf_agent

__all__ = [
    'ClassifierAgent',
    'get_classifier_agent',
    'EmailAgent', 
    'get_email_agent',
    'JSONAgent',
    'get_json_agent',
    'PDFAgent',
    'get_pdf_agent'
]
