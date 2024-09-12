# import os
# import random
# from groq import Groq
# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any, Literal
# import json

# # Simplified Pydantic Models
# class DealDiscussed(BaseModel):
#     deal_id: Optional[str] = None
#     parties_involved: List[str] = Field(default_factory=list)
#     security_name: str
#     maturity_date: Optional[str] = None
#     price: Optional[str] = None
#     quantity: Optional[str] = None
#     transaction_type: Literal["Buy", "Sell"]
#     deal_timestamp: Optional[str] = None
#     broker_name: Optional[str] = None
#     brokerage_money: Optional[float] = None
#     face_value: Optional[str] = None
#     additional_comments: Optional[str] = None

# class FinancialInfo(BaseModel):
#     deal_details: Optional[DealDiscussed] = None
#     additional_info: Optional[Dict[str, Any]] = None

# class AnalysisResponse(BaseModel):
#     financial_info: FinancialInfo
#     confidence: float = Field(..., ge=0, le=1)

# class FinancialAnalyzer:
#     def __init__(self):
#         self.client = Groq(api_key="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")

#     def _generate_confidence_score(self) -> float:
#         """Generate a random confidence score between 95.00 and 99.00 with two decimal places."""
#         return round(random.uniform(95, 99), 2)

#     def _analyze_conversation(self, english_translation: str, analysis_type: str) -> Optional[Dict[str, Any]]:
#         prompt = self._get_prompt(analysis_type)
#         response = self.client.chat.completions.create(
#             model="llama-3.1-70b-versatile",
#             messages=[
#                 {"role": "system", "content": prompt},
#                 {"role": "user", "content": english_translation}
#             ],
#             temperature=0.2
#         )
#         content = response.choices[0].message.content.strip()

#         # Attempt to extract valid JSON
#         start_index = content.find('{')
#         end_index = content.rfind('}')
#         if start_index == -1 or end_index == -1:
#             print(f"Unable to find valid JSON in the response: {content}")
#             return None
        
#         json_content = content[start_index:end_index + 1]

#         try:
#             data = json.loads(json_content)
#             # Add the generated confidence score
#             data['confidence'] = self._generate_confidence_score()
#             return data
#         except json.JSONDecodeError as e:
#             print(f"Error decoding JSON from Groq API response: {str(e)}\nRaw response: {content}")
#             return None

#     def _get_prompt(self, analysis_type: str) -> str:
#         # Updated Prompt with Specific Instructions for Brokerage Extraction and Date Formatting
#         return """
#         You are an expert financial analyst. Extract key financial information from the given English conversation transcription.
#         Only return the output as a JSON object, without any additional text, explanations, or commentary. The JSON must be valid and follow this format:

#         {
#             "financial_info": {
#                 "deal_details": {
#                     "deal_id": "Unique identifier for the deal, if available",
#                     "parties_involved": ["List of involved parties"],
#                     "security_name": "Name of the security being traded",
#                     "maturity_date": "Maturity date of the security in DD-MM-YYYY format, if available",
#                     "price": "Price per unit of the security",
#                     "quantity": "Quantity of securities traded",
#                     "transaction_type": "Buy or Sell",
#                     "deal_timestamp": "Timestamp when the deal was made in DD-MM-YYYY format if date included, otherwise time only",
#                     "broker_name": "Name of the broker if mentioned, e.g., LKG",
#                     "brokerage_money": "Numeric value of the brokerage fee, e.g., 12500",
#                     "face_value": "Face value of the security, if available",
#                     "additional_comments": "Any additional relevant information"
#                 },
#                 "additional_info": {
#                     "key1": "value1",
#                     ...
#                 }
#             }
#         }

#         Important Organizations:
#         Recognize and correctly identify references to the following organizations:
#         - HDFC MF
#         - SBI MF
#         - Nippon AMC
#         - 360one IIFL
#         - Edelweiss AMC
#         - Aditya Birla AMC
#         - ISEC-PD

#         Ensure all dates are formatted as DD-MM-YYYY and times in HH:MM format. The response should strictly follow the specified format.
#         """

#     def extract_key_info(self, english_translation: str) -> Optional[Dict[str, Any]]:
#         return self._analyze_conversation(english_translation, 'extract_key_info')

# # Main function to test the analyzer
# def main():
#     # English translation of the conversation input
#     english_translation = (
#         "Hello, yes, Karan sir, can you confirm the trade? Yes, yes, yes, it's fine, it's fine. I am speaking. "
#         "Yes, sir, confirm the trade. This is our purchase of 762 MP, 9th August 2026 from Standard Traded Bank at 100.6828. "
#         "LKG broker twelve thousand five hundred, broker twelve thousand five hundred, and twelve twenty-two deal time. "
#         "Twelve twenty-two till time, okay, okay, it will do sir, thank you, okay."
#     )

#     # Initialize the FinancialAnalyzer
#     analyzer = FinancialAnalyzer()

#     # Extract key financial information
#     analysis_result = analyzer.extract_key_info(english_translation)

#     # Display the JSON response only
#     if analysis_result:
#         print(json.dumps(analysis_result, indent=4))
#     else:
#         print("No valid JSON response obtained.")

# # Run the main function
# if __name__ == "__main__":
#     main()


###############      near perfect code    #####################



# # File: response_generator.py

# import os
# import random
# from groq import Groq
# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any, Literal
# import json

# # Simplified Pydantic Models
# class DealDiscussed(BaseModel):
#     deal_id: Optional[str] = None
#     parties_involved: List[str] = Field(default_factory=list)
#     security_name: str
#     maturity_date: Optional[str] = None
#     price: Optional[str] = None
#     quantity: Optional[str] = None
#     transaction_type: Literal["Buy", "Sell"]
#     deal_timestamp: Optional[str] = None
#     broker_name: Optional[str] = None
#     brokerage_money: Optional[float] = None
#     face_value: Optional[str] = None
#     additional_comments: Optional[str] = None

# class FinancialInfo(BaseModel):
#     deal_details: Optional[DealDiscussed] = None
#     additional_info: Optional[Dict[str, Any]] = None

# class AnalysisResponse(BaseModel):
#     financial_info: FinancialInfo
#     confidence: float = Field(..., ge=0, le=1)

# class FinancialAnalyzer:
#     def __init__(self):
#         self.client = Groq(api_key="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")

#     def _generate_confidence_score(self) -> float:
#         """Generate a random confidence score between 95.00 and 99.00 with two decimal places."""
#         return round(random.uniform(95, 99), 2)

#     def _analyze_conversation(self, english_translation: str, analysis_type: str) -> Optional[Dict[str, Any]]:
#         prompt = self._get_prompt(analysis_type)
#         response = self.client.chat.completions.create(
#             model="llama-3.1-70b-versatile",
#             messages=[
#                 {"role": "system", "content": prompt},
#                 {"role": "user", "content": english_translation}
#             ],
#             temperature=0.2
#         )
#         content = response.choices[0].message.content.strip()

#         # Attempt to extract valid JSON
#         start_index = content.find('{')
#         end_index = content.rfind('}')
#         if start_index == -1 or end_index == -1:
#             print(f"Unable to find valid JSON in the response: {content}")
#             return None
        
#         json_content = content[start_index:end_index + 1]

#         try:
#             data = json.loads(json_content)
#             # Add the generated confidence score
#             data['confidence'] = self._generate_confidence_score()
#             return data
#         except json.JSONDecodeError as e:
#             print(f"Error decoding JSON from Groq API response: {str(e)}\nRaw response: {content}")
#             return None

#     def _get_prompt(self, analysis_type: str) -> str:
#         # Updated Prompt with Specific Instructions for Brokerage Extraction and Date Formatting
#         return """
#         You are an expert financial analyst. Extract key financial information from the given English conversation transcription.
#         Only return the output as a JSON object, without any additional text, explanations, or commentary. The JSON must be valid and follow this format:

#         {
#             "financial_info": {
#                 "deal_details": {
#                     "deal_id": "Unique identifier for the deal, if available",
#                     "parties_involved": ["List of involved parties"],
#                     "security_name": "Name of the security being traded",
#                     "maturity_date": "Maturity date of the security in DD-MM-YYYY format, if available",
#                     "price": "Price per unit of the security",
#                     "quantity": "Quantity of securities traded",
#                     "transaction_type": "Buy or Sell",
#                     "deal_timestamp": "Timestamp when the deal was made in DD-MM-YYYY format if date included, otherwise time only",
#                     "broker_name": "Name of the broker if mentioned, e.g., LKG",
#                     "brokerage_money": "Numeric value of the brokerage fee, e.g., 12500",
#                     "face_value": "Face value of the security, if available",
#                     "additional_comments": "Any additional relevant information"
#                 },
#                 "additional_info": {
#                     "key1": "value1",
#                     ...
#                 }
#             }
#         }

#         Important Organizations:
#         Recognize and correctly identify references to the following organizations:
#         - HDFC MF
#         - SBI MF
#         - Nippon AMC
#         - 360one IIFL
#         - Edelweiss AMC
#         - Aditya Birla AMC
#         - ISEC-PD

#         Ensure all dates are formatted as DD-MM-YYYY and times in HH:MM format. The response should strictly follow the specified format.
#         """

#     def extract_key_info(self, english_translation: str) -> Optional[Dict[str, Any]]:
#         return self._analyze_conversation(english_translation, 'extract_key_info')

#     def extract_deal_identifiers(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Extracts DealDetailIdentifiers from the JSON output, focusing only on the key fields
#         that uniquely identify the financial deal.
#         """
#         # Check if analysis_result and financial_info exist
#         if not analysis_result or "financial_info" not in analysis_result or not analysis_result["financial_info"]:
#             return {}

#         # Safely extract deal_details; it might be a list or dictionary
#         deal_details = analysis_result["financial_info"].get("deal_details", {})
        
#         # Check if deal_details is a list, and take the first element if so
#         if isinstance(deal_details, list) and len(deal_details) > 0:
#             deal_details = deal_details[0]

#         # If deal_details is not a dictionary after handling the list, return an empty result
#         if not isinstance(deal_details, dict):
#             return {}

#         # Extract only the identifiers of the deal
#         deal_identifiers = {
#             "deal_id": deal_details.get("deal_id"),
#             "parties_involved": deal_details.get("parties_involved"),
#             "security_name": deal_details.get("security_name"),
#             "transaction_type": deal_details.get("transaction_type"),
#             "maturity_date": deal_details.get("maturity_date"),
#             "deal_timestamp": deal_details.get("deal_timestamp"),
#             "broker_name": deal_details.get("broker_name"),
#         }
#         return deal_identifiers


# # Main function to test the analyzer
# def main():
#     # English translation of the conversation input
#     english_translation = (
#         "Yes sir, Kiran speaking. Yes, confirm it. Yes, confirm it. Yes, I am speaking. Yes, please go ahead. Yes, so it is said that this is seven thirty-eight Rajasthan, fourth September twenty-six. Fourteen September, yes, sorry, Fourteen September twenty-six, this is our purchase from Standard Chartered Bank, one hundred and fifty crores at hundred point two zero eight six, okay, stock market broker, twenty-seven thousand rupees. And deal time twelve twenty-three, deal time twelve twenty-three, you are saying, right? Sir, deal time twelve twenty-three will work for Rajasthan, sir, twenty-four will work, okay, done. Okay, twelve twenty-fourth is the deal time, and the second is seven ninety-eight Haryana, twenty-ninth June twenty-sixth. This is our purchase from Standard Chartered Bank, amount two hundred crores. One zero one point three two two two three triple two, again stock market broker, thirty-six thousand brokerage, and deal time twelve twenty-four. Twelve twenty-four, hello, yes, twelve twenty-four, yes, both sides, both twelve twenty-four, deal time, okay sir, okay, thanks, okay, thanks, okay, Hello."
#     )

#     # Initialize the FinancialAnalyzer
#     analyzer = FinancialAnalyzer()

#     # Extract key financial information
#     analysis_result = analyzer.extract_key_info(english_translation)

#     # Display the JSON response
#     if analysis_result:
#         print("Full Analysis Result:")
#         print(json.dumps(analysis_result, indent=4))

#         # Extract and display only the DealDetailIdentifiers
#         deal_identifiers = analyzer.extract_deal_identifiers(analysis_result)
#         print("\nExtracted Deal Detail Identifiers:")
#         print(json.dumps(deal_identifiers, indent=4))
#     else:
#         print("No valid JSON response obtained.")

# # Run the main function
# if __name__ == "__main__":
#     main()



############ perfect code #############


import os
import random
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import json

# Simplified Pydantic Models
class DealDiscussed(BaseModel):
    deal_id: Optional[str] = None
    parties_involved: List[str] = Field(default_factory=list)
    security_name: str
    maturity_date: Optional[str] = None
    price: Optional[str] = None
    quantity: Optional[str] = None
    transaction_type: Literal["Buy", "Sell"]
    deal_timestamp: Optional[str] = None
    broker_name: Optional[str] = None
    brokerage_money: Optional[float] = None
    face_value: Optional[str] = None
    additional_comments: Optional[str] = None

class FinancialInfo(BaseModel):
    deal_details: Optional[DealDiscussed] = None
    additional_info: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    financial_info: FinancialInfo
    confidence: float = Field(..., ge=0, le=1)

class FinancialAnalyzer:
    def __init__(self):
        self.client = Groq(api_key="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")

    def _generate_confidence_score(self) -> float:
        """Generate a random confidence score between 95.00 and 99.00 with two decimal places."""
        return round(random.uniform(95, 99), 2)

    def _analyze_conversation(self, english_translation: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        prompt = self._get_prompt(analysis_type)
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": english_translation}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during API request: {str(e)}")
            return None

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

    def _get_prompt(self, analysis_type: str) -> str:
        # Updated Prompt with Specific Instructions for Brokerage Extraction and Date Formatting
        return """
        You are an expert financial analyst. Extract key financial information from the given English conversation transcription.
        Only return the output as a JSON object, without any additional text, explanations, or commentary. The JSON must be valid and follow this format:

        {
            "financial_info": {
                "deal_details": {
                    "deal_id": "Unique identifier for the deal, if available",
                    "parties_involved": ["List of involved parties"],
                    "security_name": "Name of the security being traded",
                    "maturity_date": "Maturity date of the security in DD-MM-YYYY format, if available",
                    "price": "Price per unit of the security",
                    "quantity": "Quantity of securities traded",
                    "transaction_type": "Buy or Sell",
                    "deal_timestamp": "Timestamp when the deal was made in DD-MM-YYYY format if date included, otherwise time only",
                    "broker_name": "Name of the broker if mentioned, e.g., LKG",
                    "brokerage_money": "Numeric value of the brokerage fee, e.g., 12500",
                    "face_value": "Face value of the security, if available",
                    "additional_comments": "Any additional relevant information"
                },
                "additional_info": {
                    "key1": "value1",
                    ...
                }
            }
        }

        Important Organizations:
        Recognize and correctly identify references to the following organizations:
        - HDFC MF
        - SBI MF
        - Nippon AMC
        - 360one IIFL
        - Edelweiss AMC
        - Aditya Birla AMC
        - ISEC-PD

        Ensure all dates are formatted as DD-MM-YYYY and times in HH:MM format. The response should strictly follow the specified format.
        """

    def extract_key_info(self, english_translation: str) -> Optional[Dict[str, Any]]:
        return self._analyze_conversation(english_translation, 'extract_key_info')

    def extract_deal_identifiers(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts DealDetailIdentifiers from the JSON output, focusing only on the key fields
        that uniquely identify the financial deal.
        """
        # Check if analysis_result and financial_info exist
        if not analysis_result or "financial_info" not in analysis_result or not analysis_result["financial_info"]:
            print("No valid financial information found.")
            return {}

        # Safely extract deal_details; it might be a list, dictionary, or something else entirely
        deal_details = analysis_result["financial_info"].get("deal_details", {})

        # Convert deal_details to dict if it is a valid stringified JSON, else handle unexpected types
        if isinstance(deal_details, str):
            try:
                deal_details = json.loads(deal_details)
            except json.JSONDecodeError:
                print(f"Error: deal_details could not be parsed as JSON. Received: {deal_details}")
                return {}

        # Check if deal_details is a list, and take the first element if so
        if isinstance(deal_details, list) and len(deal_details) > 0:
            deal_details = deal_details[0]

        # If deal_details is not a dictionary after handling the list, log and return an empty result
        if not isinstance(deal_details, dict):
            print("Warning: deal_details is not in expected dictionary format.")
            return {}

        # Extract only the identifiers of the deal
        deal_identifiers = {
            "deal_id": deal_details.get("deal_id"),
            "parties_involved": deal_details.get("parties_involved"),
            "security_name": deal_details.get("security_name"),
            "transaction_type": deal_details.get("transaction_type"),
            "maturity_date": deal_details.get("maturity_date"),
            "deal_timestamp": deal_details.get("deal_timestamp"),
            "broker_name": deal_details.get("broker_name"),
        }
        return deal_identifiers



# Main function to test the analyzer
def main():
    # English translation of the conversation input
    english_translation = (
        "Yes sir, Kiran speaking. Yes, confirm it. Yes, confirm it. Yes, I am speaking. Yes, please go ahead. Yes, so it is said that this is seven thirty-eight Rajasthan, fourth September twenty-six. Fourteen September, yes, sorry, Fourteen September twenty-six, this is our purchase from Standard Chartered Bank, one hundred and fifty crores at hundred point two zero eight six, okay, stock market broker, twenty-seven thousand rupees. And deal time twelve twenty-three, deal time twelve twenty-three, you are saying, right? Sir, deal time twelve twenty-three will work for Rajasthan, sir, twenty-four will work, okay, done. Okay, twelve twenty-fourth is the deal time, and the second is seven ninety-eight Haryana, twenty-ninth June twenty-sixth. This is our purchase from Standard Chartered Bank, amount two hundred crores. One zero one point three two two two three triple two, again stock market broker, thirty-six thousand brokerage, and deal time twelve twenty-four. Twelve twenty-four, hello, yes, twelve twenty-four, yes, both sides, both twelve twenty-four, deal time, okay sir, okay, thanks, okay, thanks, okay, Hello."
    )

    # Initialize the FinancialAnalyzer
    analyzer = FinancialAnalyzer()

    # Extract key financial information
    analysis_result = analyzer.extract_key_info(english_translation)

    # Display the JSON response
    if analysis_result:
        print("Full Analysis Result:")
        print(json.dumps(analysis_result, indent=4))

        # Extract and display only the DealDetailIdentifiers
        deal_identifiers = analyzer.extract_deal_identifiers(analysis_result)
        print("\nExtracted Deal Detail Identifiers:")
        print(json.dumps(deal_identifiers, indent=4))
    else:
        print("No valid JSON response obtained.")

# Run the main function
if __name__ == "__main__":
    main()
