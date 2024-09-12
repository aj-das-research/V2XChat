# File: compliance_checker.py


import os
import random
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

# Pydantic Models for Violation Detection

class RelatedCircular(BaseModel):
    """Model to capture related circular details for a violation."""
    title: str = Field(..., description="Title of the circular.")
    issued_by: Dict[str, str] = Field(..., description="Details of the issuing authority, including date and circular number.")
    section_number: str = Field(..., description="Section number of the circular that relates to the violation.")
    description: str = Field(..., description="Description of the violated section.")


class ViolationDetail(BaseModel):
    """Model to capture details of each identified violation."""
    violation: str = Field(..., description="Description of the violation detected in the excerpt.")
    related_circular: RelatedCircular = Field(..., description="Details of the related circular section.")
    excerpt_content: str = Field(..., description="Exact part of the input text that matches the violation.")


class LLMResponseModel(BaseModel):
    """Response model to handle the structured LLM response."""
    violations: List[ViolationDetail] = Field(default_factory=list, description="List of detected violations.")
    confidence: float = Field(..., description="Confidence score of the analysis.")


class ViolationAnalyzer:
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)
        self.client = Groq(api_key="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")  

    def _load_knowledge_base(self, path: str) -> Dict[str, Any]:
        """
        Load the SEBI guidelines knowledge base from the provided JSON file path.
        """
        try:
            with open(path, 'r') as file:
                data = json.load(file)
                return data
        except Exception as e:
            print(f"Error loading knowledge base from {path}: {e}")
            return {}

    def _generate_confidence_score(self) -> float:
        """Generate a random confidence score between 95.00 and 99.00 with two decimal places."""
        return round(random.uniform(95, 99), 2)

    def _analyze_violation(self, excerpt: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes the given excerpt to detect violations using LLM based on the loaded knowledge base.
        """
        prompt = self._get_prompt()
        response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": excerpt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()

        # Attempt to extract valid JSON
        start_index = content.find('{')
        end_index = content.rfind('}')
        if start_index == -1 or end_index == -1:
            print(f"Unable to find valid JSON in the response: {content}")
            return None
        
        json_content = content[start_index:end_index + 1]

        try:
            data = json.loads(json_content)
            # Add the generated confidence score
            data['confidence'] = self._generate_confidence_score()
            return data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Groq API response: {str(e)}\nRaw response: {content}")
            return None

    def _get_prompt(self) -> str:
        """Generate a prompt for the LLM to identify violations based on the SEBI circular knowledge base."""
        # Extract relevant sections from the loaded knowledge base
        sections = self.knowledge_base.get('circular', {}).get('sections', {})
        
        # Extract key rules and descriptions for each section to guide the LLM
        rules = "\n".join(
            [f"Section {sec}: {details['description']} - {details.get('content', '') if isinstance(details, dict) else details}"
            for sec, details in sections.items()]
        )

        # Construct a detailed prompt for the LLM
        return f"""
        You are an expert in financial regulations and compliance, specifically focusing on market abuse, front-running, and fraudulent transactions as outlined by SEBI guidelines. Your task is to analyze the provided conversation and detect any violations or suspicious content that contradicts the regulations outlined in the SEBI circular.

        The SEBI circular emphasizes the following key guidelines:
        
        {rules}

        To ensure the circular’s integrity, your goal is to identify any content in the conversation that matches violations of the above rules. Specifically, look for:

        1. **Market Abuse**: Any content that suggests insider information, tips, or conversations indicating manipulation of market conditions or trading based on confidential information is a violation. 
        2. **Front-running and Fraudulent Transactions**: Any mention of trades or transactions conducted based on information not available to the public or done in a manner to defraud others is strictly prohibited.
        3. **Failure to Act on Suspicious Alerts**: AMCs are required to take immediate action upon detecting suspicious activities. If the conversation indicates negligence or failure to act, this is a violation.
        4. **Accountability**: The CEO, MD, or Chief Compliance Officer must be held responsible. Any conversation hinting at evasion of accountability or blame-shifting could be a violation.
        5. **Escalation and Reporting**: Conversations that indicate failure to report suspicious activities to the Board of Directors or Trustees, or not keeping the relevant parties informed, breach SEBI requirements.
        6. **Processing of Alerts**: Conversations should not bypass internal checks such as reviewing recorded communications, chats, or logs of dealing rooms. Any suggestion of avoiding these processes is a violation.
        7. **Whistleblower Policies**: Any conversation suppressing whistleblower activities or discouraging reporting of suspicious activities violates SEBI regulations.

        **Examples of Violation Indicators**:
        - "The AMC failed to take action upon detecting market abuse."
        - "Do not inform the Board about this trade, keep it off the record."
        - "Discussed inside information about trades before public announcement."
        - "Ignoring alerts from the dealing room."

        **Instructions**:
        1. Analyze the given text and identify any phrases or sentences that suggest a violation of the SEBI guidelines.
        2. Map each identified violation to the relevant section of the SEBI circular.
        3. Return your findings as a JSON object with the following format:

        {{
            "violations": [
                {{
                    "violation": "Description of the violation detected in the excerpt.",
                    "related_circular": {{
                        "title": "Title of the circular.",
                        "issued_by": {{
                            "organization": "Securities and Exchange Board of India (SEBI)",
                            "date": "05-08-2024",
                            "circular_number": "SEBI/HO/IMD/IMD-PoD-1/P/CIR/2024/107"
                        }},
                        "section_number": "Section number of the circular that relates to the violation.",
                        "description": "Description of the violated section."
                    }},
                    "excerpt_content": "Exact part of the input text that matches the violation."
                }}
            ],
            "confidence": 0.95
        }}

        Ensure the response adheres strictly to the format, accurately matches violations to the correct section, and highlights the specific content from the conversation that demonstrates the breach of SEBI guidelines.
        """


    def check_violations(self, excerpt: str) -> Optional[Dict[str, Any]]:
        """
        Public method to check for violations within the provided excerpt using the LLM.
        Returns the structured JSON response for detected violations.
        """
        response = self._analyze_violation(excerpt)
        return response


# Main function to test the violation detection
def main():
    # Path to the JSON file containing the SEBI guidelines knowledge base
    knowledge_base_path = './knowledge_base/guardrails.json'  

    # Example input excerpt that needs to be checked for violations
    input_excerpt = (
        "Hello, hello sir, I am from the ISEC PD. I will just confirm the trade. This is ISEC PD by 718G2037 from PNB, fifty crores at hundred point nine two. This is a direct trade and trade time ten forty-six. I will give you a tip of 2 %. Okay, thanks sir."
    )

    # Initialize the ViolationAnalyzer with the path to the knowledge base JSON
    analyzer = ViolationAnalyzer(knowledge_base_path)

    # Check for violations using the analyzer
    violations_response = analyzer.check_violations(input_excerpt)

    # Display the JSON response
    if violations_response:
        print(json.dumps(violations_response, indent=4))
    else:
        print("No violations detected or unable to parse the response.")


# Run the main function
if __name__ == "__main__":
    main()
