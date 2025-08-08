"""Test script for the insurance policy processor."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Crownix'))

from Crownix.insurance_processor import InsurancePolicyProcessor

# Sample insurance policy text (excerpt from the provided document)
SAMPLE_POLICY = """National Insurance Company Limited 
CIN - U10200WB1906GOI001713  
IRDAI Regn. No. - 58 
Arogya Sanjeevani Policy - National 
1. PREAMBLE 
This Policy is a contract of insurance issued by National Insurance Co. Ltd. (hereinafter called the 'Company') to the Proposer 
mentioned in the Schedule (hereinafter called the 'Insured') to cover the person(s) named in the schedule (hereinafter called the 
'Insured Persons'). The Policy is based on the statements and declaration provided in the Proposal Form by the Proposer and is 
subject to receipt of the requisite premium. 
2. OPERATIVE CLAUSE 
If during the Policy Period one or more Insured Person (s) is required to be hospitalized for treatment of an Illness or Injury at a 
Hospital/ Day Care Center, following Medical Advice of a duly qualified Medical Practitioner, the Company shall indemnify 
Medically Necessary, expenses towards the Coverage mentioned hereunder. 
3. DEFINITIONS 
3.1. Accident means a sudden, unforeseen and involuntary event caused by external, visible and violent means. 
3.2. Age / Aged means completed years of the Insured person on last birthday as on date of commencement of the Policy. 
3.13. Co-payment means a cost sharing requirement under a health insurance policy that provides that the policyholder/insured 
will bear a specified percentage of the admissible claims amount. A co-payment does not reduce the Sum Insured. 
3.21. Family means the Family that consists of the proposer and anyone or more of the family members as mentioned below: 
4. COVERAGE 
4.1. Hospitalization 
The Company shall indemnify Medical Expense incurred for Hospitalization of the Insured Person during the Policy Period, up to 
the Sum Insured and Cumulative Bonus specified in the Policy Schedule, for, 
i. Room Rent, Boarding, Nursing Expenses all inclusive as provided by the Hospital / Nursing Home up to 2% of the sum insured 
subject to maximum of Rs. 5,000/-per day 
ii. Intensive Care Unit (ICU) / Intensive Cardiac Care Unit (ICCU) expenses up to 5% of the sum insured subject to maximum of 
Rs. 10,000/- per day 
4.3. Cataract Treatment 
The Company shall indemnify medical expenses incurred for treatment of Cataract, subject to a limit of 25% of Sum Insured or INR 
40,000 per eye, whichever is lower, per each eye in one Policy Period. 
5. CUMULATIVE BONUS (CB) 
Cumulative Bonus will be increased by 5% in respect of each claim free Policy Period (where no claims are reported and admitted), 
provided the policy is renewed with the company without a break subject to maximum of 50% of the sum insured under the current 
Policy Period. 
6. WAITING PERIOD 
6.1. Pre-Existing Diseases (Excl 01) 
a) Expenses related to the treatment of a Pre-Existing Disease (PED) and its direct complications shall be excluded until the 
expiry of 36 (thirty six) months of continuous coverage after the date of inception of the first policy with us.  
7. EXCLUSIONS 
7.1. Investigation & Evaluation (Code - Excl 04)  
a) Expenses related to any admission primarily for diagnostics and evaluation purposes only are excluded. 
7.5. Cosmetic or plastic Surgery (Code - Excl 08) 
Expenses for cosmetic or plastic surgery or any treatment to change appearance unless for reconstruction following an Accident, 
Burn(s) or Cancer or as part of medically necessary treatment to remove a direct and immediate health risk to the insured. """

def test_insurance_processor():
    """Test the insurance policy processor."""
    print("Testing Insurance Policy Processor...")
    
    # Create processor
    processor = InsurancePolicyProcessor(SAMPLE_POLICY)
    
    # Test section extraction
    print("\n1. Testing section extraction...")
    sections = processor.sections
    print(f"Found {len(sections)} sections:")
    for name in list(sections.keys())[:5]:  # Show first 5 sections
        print(f"  - {name}")
    
    # Test metadata extraction
    print("\n2. Testing metadata extraction...")
    metadata = processor.metadata
    print(f"Document type: {metadata.get('document_type', 'N/A')}")
    print(f"Insurer: {metadata.get('insurer', 'N/A')}")
    print(f"Policy name: {metadata.get('policy_name', 'N/A')}")
    
    # Test structured data
    print("\n3. Testing structured data extraction...")
    structured_data = processor.get_structured_data()
    print(f"Coverage sections: {list(structured_data['coverage'].keys())}")
    print(f"Number of exclusions: {len(structured_data['exclusions'])}")
    print(f"Waiting periods: {list(structured_data['waiting_periods'].keys())}")
    
    # Test Q&A
    print("\n4. Testing Q&A functionality...")
    questions = [
        "What is covered for hospitalization?",
        "What are the exclusions?",
        "What is the waiting period for pre-existing diseases?",
        "What does co-payment mean?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        answer = processor.answer_question(question)
        print(f"Answer: {answer['answer']}")
        print(f"Confidence: {answer['confidence']}")
        
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_insurance_processor()
