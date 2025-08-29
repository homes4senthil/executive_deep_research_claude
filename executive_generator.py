import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Dict, Any
from data_processor import SalesData, create_data_summary_prompt
from search_tool import IndustryResearch, create_industry_research_prompt

# Fixed company configuration
COMPANY_NAME = "Apple Inc."

class ExecutiveRecommendation(BaseModel):
    category: str
    recommendation: str
    priority: str  # High, Medium, Low
    timeline: str
    expected_impact: str

class ExecutiveSummary(BaseModel):
    executive_summary: str
    key_findings: List[str]
    strategic_recommendations: List[ExecutiveRecommendation]
    risk_assessment: str
    next_steps: List[str]

class ExecutiveReportGenerator:
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.llm = ChatOpenAI(
            api_key=self.openai_api_key,
            model="gpt-4",
            temperature=0.3
        )
    
    def generate_executive_report(
        self, 
        company_name: str = None, 
        executive_role: str = "CEO",
        sales_data: SalesData = None, 
        industry_research: IndustryResearch = None
    ) -> ExecutiveSummary:
        """
        Generate comprehensive executive report with summary and recommendations
        """
        if company_name is None:
            company_name = COMPANY_NAME
            
        # Create data summary
        data_summary = create_data_summary_prompt(sales_data, company_name)
        
        # Create industry research summary
        research_summary = create_industry_research_prompt(industry_research, company_name)
        
        # Generate executive summary and recommendations
        system_prompt = self._create_system_prompt(executive_role)
        human_prompt = self._create_human_prompt(company_name, data_summary, research_summary)
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])
            
            # Parse the response into structured format
            return self._parse_llm_response(response.content)
            
        except Exception as e:
            raise Exception(f"Error generating executive report: {str(e)}")
    
    def _create_system_prompt(self, executive_role: str) -> str:
        """Create system prompt based on executive role"""
        
        role_contexts = {
            "ceo": "chief executive officer focused on overall strategy, growth, and shareholder value",
            "cfo": "chief financial officer focused on financial performance, profitability, and risk management", 
            "coo": "chief operating officer focused on operational efficiency, process optimization, and execution",
            "cmo": "chief marketing officer focused on brand strategy, customer acquisition, and market positioning",
            "cto": "chief technology officer focused on technology strategy, innovation, and digital transformation",
            "head of sales": "sales leader focused on revenue growth, sales performance, and market expansion",
            "head of product": "product leader focused on product strategy, development, and market fit"
        }
        
        role_context = role_contexts.get(executive_role.lower(), f"{executive_role} focused on strategic leadership and business performance")
        
        return f"""You are an expert business analyst creating an executive briefing for a {role_context}.

Your task is to analyze sales data and industry research to provide:
1. A concise executive summary (2-3 paragraphs)
2. Key findings (3-5 bullet points)
3. Strategic recommendations with priority, timeline, and expected impact
4. Risk assessment
5. Next steps

Tailor your analysis and recommendations specifically for the {executive_role} perspective.
Be data-driven, actionable, and strategic in your recommendations.
Focus on insights that would be most relevant and valuable for this executive role.

Format your response as follows:

EXECUTIVE SUMMARY:
[2-3 paragraph summary]

KEY FINDINGS:
• [Finding 1]
• [Finding 2]
• [Finding 3]

STRATEGIC RECOMMENDATIONS:
[Recommendation 1]
Category: [Strategic/Operational/Financial/Marketing]
Priority: [High/Medium/Low]  
Timeline: [Immediate/Short-term/Long-term]
Expected Impact: [Description of expected impact]

[Recommendation 2]
[Same format...]

RISK ASSESSMENT:
[Risk analysis paragraph]

NEXT STEPS:
• [Action 1]
• [Action 2]
• [Action 3]"""
    
    def _create_human_prompt(self, company_name: str, data_summary: str, research_summary: str) -> str:
        """Create the human prompt with all context"""
        
        return f"""Please analyze the following information for {company_name} and create a comprehensive executive briefing:

{data_summary}

{research_summary}

Based on this sales data and industry research, provide strategic insights and actionable recommendations tailored for the executive role specified in the system prompt."""
    
    def _parse_llm_response(self, response_content: str) -> ExecutiveSummary:
        """Parse LLM response into structured ExecutiveSummary object"""
        
        # Simple parsing - in production, you might want more robust parsing
        lines = response_content.split('\n')
        
        executive_summary = ""
        key_findings = []
        strategic_recommendations = []
        risk_assessment = ""
        next_steps = []
        
        current_section = None
        current_recommendation = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("EXECUTIVE SUMMARY:"):
                current_section = "summary"
                continue
            elif line.startswith("KEY FINDINGS:"):
                current_section = "findings"
                continue
            elif line.startswith("STRATEGIC RECOMMENDATIONS:"):
                current_section = "recommendations"
                continue
            elif line.startswith("RISK ASSESSMENT:"):
                current_section = "risk"
                continue
            elif line.startswith("NEXT STEPS:"):
                current_section = "steps"
                continue
            
            if current_section == "summary":
                executive_summary += line + " "
            elif current_section == "findings" and line.startswith("•"):
                key_findings.append(line[1:].strip())
            elif current_section == "recommendations":
                if line and not line.startswith(("Category:", "Priority:", "Timeline:", "Expected Impact:")):
                    if current_recommendation:
                        # Save previous recommendation
                        if all(key in current_recommendation for key in ['recommendation', 'category', 'priority', 'timeline', 'expected_impact']):
                            strategic_recommendations.append(ExecutiveRecommendation(**current_recommendation))
                        current_recommendation = {}
                    current_recommendation['recommendation'] = line
                elif line.startswith("Category:"):
                    current_recommendation['category'] = line.split(":", 1)[1].strip()
                elif line.startswith("Priority:"):
                    current_recommendation['priority'] = line.split(":", 1)[1].strip()
                elif line.startswith("Timeline:"):
                    current_recommendation['timeline'] = line.split(":", 1)[1].strip()
                elif line.startswith("Expected Impact:"):
                    current_recommendation['expected_impact'] = line.split(":", 1)[1].strip()
            elif current_section == "risk":
                risk_assessment += line + " "
            elif current_section == "steps" and line.startswith("•"):
                next_steps.append(line[1:].strip())
        
        # Don't forget the last recommendation
        if current_recommendation and all(key in current_recommendation for key in ['recommendation', 'category', 'priority', 'timeline', 'expected_impact']):
            strategic_recommendations.append(ExecutiveRecommendation(**current_recommendation))
        
        return ExecutiveSummary(
            executive_summary=executive_summary.strip(),
            key_findings=key_findings,
            strategic_recommendations=strategic_recommendations,
            risk_assessment=risk_assessment.strip(),
            next_steps=next_steps
        )