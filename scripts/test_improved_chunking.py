"""
Test script for improved chunking
Run this to verify section-aware chunking is working
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agent.chunking.adaptive_chunker import AdaptiveChunker

# Sample policy document text
sample_policy = """
National Education Policy 2024

Section 1: Introduction
This policy outlines the framework for educational institutions across the country.

Section 2: Objectives
2.1 Primary Objectives
The primary objectives include improving quality of education and ensuring accessibility.

2.2 Secondary Objectives
Secondary objectives focus on infrastructure development and teacher training.

Section 3: Admission Guidelines
3.1 Eligibility Criteria
Students seeking admission must have completed their previous education with minimum 60% marks.
Reserved category students require 55%. Documents needed include mark sheets, caste certificate,
and income proof. As per Section 2.3, verification will be done within 7 days.

3.2 Application Process
Step 1: Submit online application form with required documents
Step 2: Pay application fee of Rs. 500 (Rs. 250 for reserved category)
Step 3: Wait for verification (7 working days)
Step 4: Receive admission confirmation via email
Step 5: Complete enrollment by submitting original documents

Section 4: Fee Structure
4.1 Tuition Fees
General category: Rs. 50,000 per year
Reserved category: Rs. 25,000 per year
Economically weaker section: Rs. 10,000 per year

4.2 Other Fees
Library fee: Rs. 2,000
Sports fee: Rs. 1,500
Development fee: Rs. 5,000
"""

# Sample resume text
sample_resume = """
PRANAV WAIKAR
Senior Software Engineer (5 years)
+91-7066506779 / pranavwaikar@gmail.com / www.linkedin.com/in/pranav-waikar

PROFESSIONAL SUMMARY
Senior Software Engineer with over 5 years of experience in full-stack development, 
automation testing, and cloud solutions across industries like healthcare, finance, and oil & gas.

WORK EXPERIENCE

Velotio Technologies | Senior Software Engineer | May 2022 - Present
• Led development of cloud-based testing infrastructure
• Implemented CI/CD pipelines reducing deployment time by 60%
• Mentored junior developers and conducted code reviews
• Tech Stack: Node.js, React, AWS, Docker, Kubernetes

Accenture | Software Engineer | Jan 2020 - Apr 2022
• Developed healthcare management system for US client
• Reduced patient outreach report generation time by 50% using AWS Lambda
• Ensured HIPAA compliance under Agile workflows
• Tech Stack: TypeScript, React, Redux, Azure, Express

TCS | Junior Developer | Jun 2018 - Dec 2019
• Built automation testing framework for banking application
• Improved test coverage from 40% to 85%
• Collaborated with QA team for test strategy
• Tech Stack: Java, Selenium, Jenkins, MySQL

EDUCATION
Bachelor of Engineering in Computer Science
University of Mumbai | 2014-2018 | CGPA: 8.5/10

SKILLS
Languages: JavaScript, TypeScript, Python, Java
Frameworks: React, Node.js, Express, Redux
Cloud: AWS (S3, Lambda, EC2), Azure
Tools: Docker, Kubernetes, Git, Jenkins, JIRA
"""

def test_chunking():
    """Test the improved chunking"""
    chunker = AdaptiveChunker()
    
    print("=" * 80)
    print("TESTING IMPROVED CHUNKING")
    print("=" * 80)
    
    # Test 1: Policy Document
    print("\n\n📄 TEST 1: POLICY DOCUMENT")
    print("-" * 80)
    policy_chunks = chunker.chunk_text(sample_policy)
    print(f"Total chunks: {len(policy_chunks)}")
    print(f"Document length: {len(sample_policy)} chars")
    
    for i, chunk in enumerate(policy_chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Size: {len(chunk['text'])} chars")
        print(f"Has section: {chunk['metadata'].get('has_section', False)}")
        print(f"Section header: {chunk['metadata'].get('section_header', 'None')}")
        print(f"Preview: {chunk['text'][:200]}...")
    
    # Test 2: Resume
    print("\n\n" + "=" * 80)
    print("📄 TEST 2: RESUME")
    print("-" * 80)
    resume_chunks = chunker.chunk_text(sample_resume)
    print(f"Total chunks: {len(resume_chunks)}")
    print(f"Document length: {len(sample_resume)} chars")
    
    for i, chunk in enumerate(resume_chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Size: {len(chunk['text'])} chars")
        print(f"Has section: {chunk['metadata'].get('has_section', False)}")
        print(f"Section header: {chunk['metadata'].get('section_header', 'None')}")
        print(f"Preview: {chunk['text'][:200]}...")
    
    # Analysis
    print("\n\n" + "=" * 80)
    print("📊 ANALYSIS")
    print("=" * 80)
    
    # Policy analysis
    policy_with_sections = sum(1 for c in policy_chunks if c['metadata'].get('has_section'))
    policy_avg_size = sum(len(c['text']) for c in policy_chunks) / len(policy_chunks)
    
    print(f"\nPolicy Document:")
    print(f"  - Chunks with sections: {policy_with_sections}/{len(policy_chunks)}")
    print(f"  - Average chunk size: {policy_avg_size:.0f} chars")
    print(f"  - Sections detected: {policy_with_sections}")
    
    # Resume analysis
    resume_with_sections = sum(1 for c in resume_chunks if c['metadata'].get('has_section'))
    resume_avg_size = sum(len(c['text']) for c in resume_chunks) / len(resume_chunks)
    
    print(f"\nResume:")
    print(f"  - Chunks with sections: {resume_with_sections}/{len(resume_chunks)}")
    print(f"  - Average chunk size: {resume_avg_size:.0f} chars")
    
    # Check if work experience is in one chunk
    work_exp_chunks = [c for c in resume_chunks if 'Velotio' in c['text'] and 'Accenture' in c['text']]
    if work_exp_chunks:
        print(f"  - ✅ Work experience kept together in {len(work_exp_chunks)} chunk(s)")
    else:
        print(f"  - ❌ Work experience split across chunks")
    
    # Check if eligibility is complete
    eligibility_chunks = [c for c in policy_chunks if '3.1 Eligibility' in c['text']]
    if eligibility_chunks:
        eligibility_text = eligibility_chunks[0]['text']
        has_marks = '60%' in eligibility_text
        has_docs = 'mark sheets' in eligibility_text
        has_verification = 'verification' in eligibility_text
        
        if has_marks and has_docs and has_verification:
            print(f"\nPolicy Eligibility Section:")
            print(f"  - ✅ Complete eligibility info in one chunk")
        else:
            print(f"\nPolicy Eligibility Section:")
            print(f"  - ❌ Incomplete eligibility info")
    
    print("\n" + "=" * 80)
    print("✅ TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_chunking()
