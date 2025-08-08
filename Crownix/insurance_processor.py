"""Specialized processor for health insurance policy documents."""

import re
from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class InsurancePolicyProcessor:
    """Process and analyze health insurance policy documents."""
    
    def __init__(self, document_text: str):
        self.document_text = document_text
        self.sections = self._extract_sections()
        self.metadata = self._extract_metadata()
        
    def _extract_sections(self) -> Dict[str, str]:
        """Extract major sections from the insurance policy document."""
        sections = {}
        
        # Common section patterns in insurance policies
        section_patterns = [
            r"(\d+\.\s+[A-Z][A-Za-z\s]+)",  # e.g., "1. PREAMBLE"
            r"(\d+\.\d+\.\s+[A-Z][A-Za-z\s]+)",  # e.g., "3.1. Accident"
        ]
        
        lines = self.document_text.split('\n')
        current_section = "header"
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            is_section_header = False
            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    # Save previous section
                    if current_section and section_content:
                        sections[current_section.lower()] = '\n'.join(section_content)
                    
                    # Start new section
                    current_section = match.group(1).strip()
                    section_content = []
                    is_section_header = True
                    break
            
            if not is_section_header:
                section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            sections[current_section.lower()] = '\n'.join(section_content)
            
        return sections
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract key metadata from the policy document."""
        metadata = {
            'processed_at': datetime.utcnow().isoformat(),
            'document_type': 'health_insurance_policy',
            'sections_found': list(self.sections.keys())
        }
        
        # Extract company information
        company_match = re.search(r"National Insurance Co\. Ltd\.?", self.document_text)
        if company_match:
            metadata['insurer'] = company_match.group(0)
            
        # Extract policy name
        policy_match = re.search(r"([A-Za-z\s]+Policy)", self.document_text)
        if policy_match:
            metadata['policy_name'] = policy_match.group(1).strip()
            
        # Extract registration numbers
        cin_match = re.search(r"CIN\s*-\s*([A-Z0-9]+)", self.document_text)
        if cin_match:
            metadata['cin'] = cin_match.group(1)
            
        iradai_match = re.search(r"IRDAI Regn\. No\.\s*-\s*([0-9]+)", self.document_text)
        if iradai_match:
            metadata['irdai_registration'] = iradai_match.group(1)
            
        return metadata
    
    def _extract_definitions(self) -> Dict[str, str]:
        """Extract definitions from the policy document."""
        definitions = {}
        
        # Look for definitions section
        definitions_text = self.sections.get('3. definitions', '')
        if not definitions_text:
            # Try to find definitions in the full document
            definitions_match = re.search(r"3\.\s*DEFINITIONS(.+?)(?=\d+\.\s*[A-Z]|$)", 
                                        self.document_text, re.DOTALL | re.IGNORECASE)
            if definitions_match:
                definitions_text = definitions_match.group(1)
        
        # Extract individual definitions
        definition_pattern = r"(\d+\.\d+\.\s*)([A-Za-z\s]+)means(.+?)(?=\d+\.\d+\.|$)"
        matches = re.finditer(definition_pattern, definitions_text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            term = match.group(2).strip()
            definition = match.group(3).strip()
            definitions[term.lower()] = definition
            
        return definitions
    
    def _extract_coverage_details(self) -> Dict[str, Any]:
        """Extract coverage details from the policy."""
        coverage = {
            'hospitalization': {},
            'ayush_treatment': {},
            'cataract_treatment': {},
            'pre_hospitalization': {},
            'post_hospitalization': {},
            'modern_treatment': {}
        }
        
        # Extract hospitalization coverage
        hospitalization_text = self.sections.get('4.1. hospitalization', '')
        if not hospitalization_text:
            hospitalization_text = self.sections.get('4. coverage', '')
            
        if hospitalization_text:
            # Extract room rent limits
            room_rent_match = re.search(r"Room Rent.+?(\d+%|Rs\.?\s*[\d,]+)", hospitalization_text, re.IGNORECASE)
            if room_rent_match:
                coverage['hospitalization']['room_rent_limit'] = room_rent_match.group(1)
                
            # Extract ICU limits
            icu_match = re.search(r"ICU.+?(\d+%|Rs\.?\s*[\d,]+)", hospitalization_text, re.IGNORECASE)
            if icu_match:
                coverage['hospitalization']['icu_limit'] = icu_match.group(1)
                
            # Extract ambulance limits
            ambulance_match = re.search(r"Ambulance.+?(Rs\.?\s*[\d,]+)", hospitalization_text, re.IGNORECASE)
            if ambulance_match:
                coverage['hospitalization']['ambulance_limit'] = ambulance_match.group(1)
        
        # Extract cataract treatment details
        cataract_text = self.sections.get('4.3. cataract treatment', '')
        if cataract_text:
            limit_match = re.search(r"(\d+%|Rs\.?\s*[\d,]+)", cataract_text)
            if limit_match:
                coverage['cataract_treatment']['limit'] = limit_match.group(1)
                
        return coverage
    
    def _extract_exclusions(self) -> List[Dict[str, str]]:
        """Extract exclusions from the policy document."""
        exclusions = []
        
        # Look for exclusions section
        exclusions_text = self.sections.get('7. exclusions', '')
        if not exclusions_text:
            exclusions_text = self.sections.get('exclusions', '')
            
        if exclusions_text:
            # Extract individual exclusions
            exclusion_pattern = r"(\d+\.\d+\.\s*)(.+?)(?=\d+\.\d+\.|$)"
            matches = re.finditer(exclusion_pattern, exclusions_text, re.DOTALL)
            
            for match in matches:
                exclusion_number = match.group(1).strip()
                exclusion_text = match.group(2).strip()
                exclusions.append({
                    'number': exclusion_number,
                    'description': exclusion_text
                })
                
        return exclusions
    
    def _extract_waiting_periods(self) -> Dict[str, str]:
        """Extract waiting periods from the policy document."""
        waiting_periods = {}
        
        # Look for waiting periods section
        waiting_text = self.sections.get('6. waiting period', '')
        if not waiting_text:
            waiting_text = self.sections.get('waiting period', '')
            
        if waiting_text:
            # Extract pre-existing diseases waiting period
            ped_match = re.search(r"Pre-Existing Diseases.+?(\d+)\s*months", waiting_text, re.IGNORECASE)
            if ped_match:
                waiting_periods['pre_existing_diseases'] = f"{ped_match.group(1)} months"
                
            # Extract first 30 days waiting period
            first_30_match = re.search(r"first\s+(\d+)\s*days", waiting_text, re.IGNORECASE)
            if first_30_match:
                waiting_periods['first_30_days'] = f"{first_30_match.group(1)} days"
                
            # Extract specified diseases waiting period
            specified_match = re.search(r"specified disease.+?(\d+)\s*months", waiting_text, re.IGNORECASE)
            if specified_match:
                waiting_periods['specified_diseases'] = f"{specified_match.group(1)} months"
                
        return waiting_periods
    
    def get_structured_data(self) -> Dict[str, Any]:
        """Convert policy to structured format."""
        return {
            'metadata': self.metadata,
            'definitions': self._extract_definitions(),
            'coverage': self._extract_coverage_details(),
            'exclusions': self._extract_exclusions(),
            'waiting_periods': self._extract_waiting_periods(),
            'raw_sections': self.sections
        }
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer questions about the policy document."""
        question_lower = question.lower()
        
        # Simple keyword-based response generation
        if 'cover' in question_lower or 'coverage' in question_lower:
            return self._get_coverage_info(question)
        elif 'exclude' in question_lower or 'exclusion' in question_lower:
            return self._get_exclusion_info(question)
        elif 'wait' in question_lower or 'waiting' in question_lower:
            return self._get_waiting_period_info(question)
        elif 'definition' in question_lower or 'mean' in question_lower:
            return self._get_definition_info(question)
        else:
            # General search through document
            return self._search_document(question)
    
    def _get_coverage_info(self, question: str) -> Dict[str, Any]:
        """Get coverage information based on question."""
        coverage = self._extract_coverage_details()
        
        # Simplify coverage for response
        simplified_coverage = {}
        for key, value in coverage.items():
            if value:  # Only include non-empty sections
                simplified_coverage[key] = value
                
        return {
            'answer': 'Coverage information extracted from the policy',
            'details': simplified_coverage,
            'confidence': 0.9,
            'source_section': '4. Coverage'
        }
    
    def _get_exclusion_info(self, question: str) -> Dict[str, Any]:
        """Get exclusion information based on question."""
        exclusions = self._extract_exclusions()
        
        return {
            'answer': 'Exclusions information extracted from the policy',
            'details': exclusions,
            'confidence': 0.9,
            'source_section': '7. Exclusions'
        }
    
    def _get_waiting_period_info(self, question: str) -> Dict[str, Any]:
        """Get waiting period information based on question."""
        waiting_periods = self._extract_waiting_periods()
        
        return {
            'answer': 'Waiting period information extracted from the policy',
            'details': waiting_periods,
            'confidence': 0.9,
            'source_section': '6. Waiting Period'
        }
    
    def _get_definition_info(self, question: str) -> Dict[str, Any]:
        """Get definition information based on question."""
        definitions = self._extract_definitions()
        
        # Try to find specific definition
        question_lower = question.lower()
        found_definition = None
        
        for term, definition in definitions.items():
            if term in question_lower:
                found_definition = {term: definition}
                break
                
        if not found_definition and definitions:
            # Return first few definitions if no specific match
            found_definition = dict(list(definitions.items())[:3])
            
        return {
            'answer': 'Definition information extracted from the policy',
            'details': found_definition,
            'confidence': 0.8 if found_definition else 0.5,
            'source_section': '3. Definitions'
        }
    
    def _search_document(self, query: str) -> Dict[str, Any]:
        """Search through document for relevant information."""
        query_lower = query.lower()
        relevant_sections = {}
        
        # Simple keyword matching in sections
        for section_name, section_content in self.sections.items():
            if query_lower in section_content.lower():
                # Extract relevant sentences
                sentences = section_content.split('.')
                relevant_sentences = [s for s in sentences if query_lower in s.lower()]
                if relevant_sentences:
                    relevant_sections[section_name] = '. '.join(relevant_sentences[:3]) + '.'
        
        return {
            'answer': 'Found relevant information in the policy document',
            'details': relevant_sections,
            'confidence': 0.7 if relevant_sections else 0.3,
            'source_section': 'Multiple sections'
        }
