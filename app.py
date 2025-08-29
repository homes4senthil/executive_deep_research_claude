import streamlit as st
import pandas as pd
import os
from io import StringIO
import tempfile
from dotenv import load_dotenv

from data_processor import DataProcessor, create_data_summary_prompt
from search_tool import TavilySearchTool, create_industry_research_prompt
from executive_generator import ExecutiveReportGenerator

# Load environment variables
load_dotenv()

# Fixed company configuration
COMPANY_NAME = "Apple Inc."

def main():
    st.set_page_config(
        page_title="Apple Executive Research",
        page_icon="🍎",
        layout="wide"
    )
    
    st.title("🍎 Apple Executive Research Assistant")
    st.markdown("Generate comprehensive Apple executive reports with sales data analysis and industry research")
    
    # Create two columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Input Parameters")
        
        # Display company info
        st.subheader("Company")
        st.info(f"🍎 {COMPANY_NAME}")
        
        executive_roles = [
            "CEO", "CFO", "COO", "CTO", "CMO", 
            "Head of Sales", "Head of Product", "VP Marketing",
            "VP Operations", "Chief Strategy Officer"
        ]
        executive_role = st.selectbox("Executive Role", executive_roles)
        
        # API Keys
        st.subheader("API Configuration")
        openai_key = st.text_input(
            "OpenAI API Key", 
            type="password", 
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Required for generating executive summaries"
        )
        
        tavily_key = st.text_input(
            "Tavily API Key", 
            type="password", 
            value=os.getenv("TAVILY_API_KEY", ""),
            help="Required for industry research"
        )
        
        # File Upload
        st.subheader("Sales Data")
        uploaded_file = st.file_uploader(
            "Upload CSV Sales Data",
            type="csv",
            help="CSV should contain columns: product, region, sales"
        )
        
        # Show sample data format
        if st.checkbox("Show sample data format"):
            sample_data = {
                'product': ['iPhone', 'MacBook', 'iPad', 'iPhone', 'MacBook'],
                'region': ['North America', 'Europe', 'Asia', 'Europe', 'North America'],
                'sales': [1500000, 800000, 600000, 1200000, 900000]
            }
            st.dataframe(pd.DataFrame(sample_data))
        
        # Generate Report Button
        generate_button = st.button(
            "🚀 Generate Executive Report", 
            type="primary",
            use_container_width=True
        )
    
    with col2:
        st.header("Executive Report")
        
        if generate_button:
            # Validate inputs
            if not openai_key:
                st.error("Please provide OpenAI API key")
                return
            
            if not uploaded_file:
                st.error("Please upload a CSV file")
                return
            
            # Process the request
            with st.spinner("Generating your executive report..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue().decode('utf-8'))
                        csv_path = tmp_file.name
                    
                    # Initialize components
                    data_processor = DataProcessor()
                    report_generator = ExecutiveReportGenerator(openai_api_key=openai_key)
                    
                    # Process sales data
                    st.info("📊 Processing sales data...")
                    sales_data = data_processor.process_csv_data(csv_path)
                    
                    # Display sales summary
                    display_sales_summary(sales_data, COMPANY_NAME)
                    
                    # Industry research (optional)
                    industry_research = None
                    if tavily_key:
                        st.info("🔍 Researching industry trends...")
                        try:
                            search_tool = TavilySearchTool(api_key=tavily_key)
                            products = list(sales_data.product_summary.keys())
                            industry_research = search_tool.search_company_trends(COMPANY_NAME, products)
                            st.success("Industry research completed!")
                        except Exception as e:
                            st.warning(f"Industry research failed: {str(e)}")
                            st.info("Continuing with sales data analysis only...")
                    else:
                        st.warning("Tavily API key not provided. Skipping industry research.")
                    
                    # Generate executive report
                    st.info("📝 Generating executive summary...")
                    if not industry_research:
                        # Create empty research object
                        from search_tool import IndustryResearch
                        industry_research = IndustryResearch(
                            company_trends=[],
                            product_trends=[],
                            industry_news=[],
                            competitive_landscape=[]
                        )
                    
                    executive_report = report_generator.generate_executive_report(
                        COMPANY_NAME,
                        executive_role,
                        sales_data,
                        industry_research
                    )
                    
                    # Display executive report
                    display_executive_report(executive_report, executive_role)
                    
                    # Clean up temp file
                    os.unlink(csv_path)
                    
                    st.success("✅ Executive report generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    if 'csv_path' in locals():
                        try:
                            os.unlink(csv_path)
                        except:
                            pass

def display_sales_summary(sales_data, company_name):
    """Display sales data summary"""
    
    st.subheader("📈 Sales Performance Overview")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sales", f"${sales_data.total_sales:,.2f}")
    with col2:
        st.metric("Products", len(sales_data.product_summary))
    with col3:
        st.metric("Regions", len(sales_data.region_summary))
    
    # Product performance
    st.subheader("🛍️ Product Performance")
    product_df = pd.DataFrame([
        {
            'Product': product,
            'Total Sales': f"${stats['total_sales']:,.2f}",
            'Market Share': f"{stats['market_share_percent']:.1f}%",
            'Transactions': stats['transaction_count']
        }
        for product, stats in sales_data.product_summary.items()
    ])
    st.dataframe(product_df, use_container_width=True)
    
    # Regional performance
    st.subheader("🌍 Regional Performance")
    region_df = pd.DataFrame([
        {
            'Region': region,
            'Total Sales': f"${stats['total_sales']:,.2f}",
            'Market Share': f"{stats['market_share_percent']:.1f}%",
            'Transactions': stats['transaction_count']
        }
        for region, stats in sales_data.region_summary.items()
    ])
    st.dataframe(region_df, use_container_width=True)
    
    # Key insights
    st.subheader("💡 Key Insights")
    for insight in sales_data.key_insights:
        st.write(f"• {insight}")

def display_executive_report(executive_report, executive_role):
    """Display the executive report"""
    
    st.subheader(f"📋 Executive Summary for {executive_role}")
    st.write(executive_report.executive_summary)
    
    # Key findings
    st.subheader("🔍 Key Findings")
    for finding in executive_report.key_findings:
        st.write(f"• {finding}")
    
    # Strategic recommendations
    st.subheader("🎯 Strategic Recommendations")
    
    for i, rec in enumerate(executive_report.strategic_recommendations, 1):
        with st.expander(f"Recommendation {i}: {rec.recommendation[:50]}..."):
            st.write(f"**Category:** {rec.category}")
            st.write(f"**Priority:** {rec.priority}")
            st.write(f"**Timeline:** {rec.timeline}")
            st.write(f"**Expected Impact:** {rec.expected_impact}")
            st.write(f"**Details:** {rec.recommendation}")
    
    # Risk assessment
    if executive_report.risk_assessment:
        st.subheader("⚠️ Risk Assessment")
        st.write(executive_report.risk_assessment)
    
    # Next steps
    if executive_report.next_steps:
        st.subheader("✅ Next Steps")
        for step in executive_report.next_steps:
            st.write(f"• {step}")

if __name__ == "__main__":
    main()