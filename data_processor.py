import pandas as pd
from typing import Dict, Any, List
from pydantic import BaseModel

# Fixed company configuration
COMPANY_NAME = "Apple Inc."

class SalesData(BaseModel):
    product_summary: Dict[str, Any]
    region_summary: Dict[str, Any]
    total_sales: float
    key_insights: List[str]

class DataProcessor:
    def __init__(self):
        pass
    
    def process_csv_data(self, csv_file_path: str) -> SalesData:
        """
        Process CSV sales data and create summaries by product and region
        """
        try:
            df = pd.read_csv(csv_file_path)
            
            # Normalize column names
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Auto-detect sales column
            sales_column = None
            possible_sales_cols = ['sales', 'revenue_millions_usd', 'revenue', 'total_sales', 'amount']
            for col in possible_sales_cols:
                if col in df.columns:
                    sales_column = col
                    break
            
            if not sales_column:
                raise ValueError(f"Could not find sales column. Available columns: {list(df.columns)}")
            
            # Rename for consistency
            df = df.rename(columns={sales_column: 'sales'})
            
            # Check required columns
            required_columns = ['product', 'region', 'sales']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}. Available columns: {list(df.columns)}")
            
            # Create product summary
            product_summary = self._create_product_summary(df)
            
            # Create region summary
            region_summary = self._create_region_summary(df)
            
            # Calculate total sales
            total_sales = df['sales'].sum()
            
            # Generate key insights
            key_insights = self._generate_key_insights(df, product_summary, region_summary)
            
            return SalesData(
                product_summary=product_summary,
                region_summary=region_summary,
                total_sales=total_sales,
                key_insights=key_insights
            )
            
        except Exception as e:
            raise Exception(f"Error processing CSV data: {str(e)}")
    
    def _create_product_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary statistics by product"""
        product_stats = df.groupby('product')['sales'].agg([
            'sum', 'mean', 'count', 'std'
        ]).round(2)
        
        # Calculate market share
        total_sales = df['sales'].sum()
        product_stats['market_share'] = (product_stats['sum'] / total_sales * 100).round(2)
        
        # Convert to dictionary for easier handling
        product_summary = {}
        for product in product_stats.index:
            product_summary[product] = {
                'total_sales': product_stats.loc[product, 'sum'],
                'average_sales': product_stats.loc[product, 'mean'],
                'transaction_count': product_stats.loc[product, 'count'],
                'sales_volatility': product_stats.loc[product, 'std'],
                'market_share_percent': product_stats.loc[product, 'market_share']
            }
        
        return product_summary
    
    def _create_region_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary statistics by region"""
        region_stats = df.groupby('region')['sales'].agg([
            'sum', 'mean', 'count', 'std'
        ]).round(2)
        
        # Calculate market share
        total_sales = df['sales'].sum()
        region_stats['market_share'] = (region_stats['sum'] / total_sales * 100).round(2)
        
        # Convert to dictionary for easier handling
        region_summary = {}
        for region in region_stats.index:
            region_summary[region] = {
                'total_sales': region_stats.loc[region, 'sum'],
                'average_sales': region_stats.loc[region, 'mean'],
                'transaction_count': region_stats.loc[region, 'count'],
                'sales_volatility': region_stats.loc[region, 'std'],
                'market_share_percent': region_stats.loc[region, 'market_share']
            }
        
        return region_summary
    
    def _generate_key_insights(self, df: pd.DataFrame, product_summary: Dict, region_summary: Dict) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        # Top performing product
        top_product = max(product_summary.keys(), key=lambda x: product_summary[x]['total_sales'])
        insights.append(f"Top performing product: {top_product} with ${product_summary[top_product]['total_sales']:,.2f} in sales")
        
        # Top performing region
        top_region = max(region_summary.keys(), key=lambda x: region_summary[x]['total_sales'])
        insights.append(f"Top performing region: {top_region} with ${region_summary[top_region]['total_sales']:,.2f} in sales")
        
        # Product diversity
        product_count = len(product_summary)
        insights.append(f"Portfolio consists of {product_count} products")
        
        # Regional presence
        region_count = len(region_summary)
        insights.append(f"Operating in {region_count} regions")
        
        # Market concentration
        top_product_share = product_summary[top_product]['market_share_percent']
        if top_product_share > 50:
            insights.append(f"High product concentration risk: {top_product} represents {top_product_share}% of total sales")
        
        return insights

def create_data_summary_prompt(sales_data: SalesData, company_name: str = None) -> str:
    """Create a formatted prompt with sales data summary"""
    if company_name is None:
        company_name = COMPANY_NAME
    prompt = f"""
Sales Data Summary for {company_name}:

TOTAL SALES: ${sales_data.total_sales:,.2f}

PRODUCT PERFORMANCE:
"""
    for product, stats in sales_data.product_summary.items():
        prompt += f"- {product}: ${stats['total_sales']:,.2f} ({stats['market_share_percent']}% market share)\n"
    
    prompt += "\nREGIONAL PERFORMANCE:\n"
    for region, stats in sales_data.region_summary.items():
        prompt += f"- {region}: ${stats['total_sales']:,.2f} ({stats['market_share_percent']}% of total)\n"
    
    prompt += "\nKEY INSIGHTS:\n"
    for insight in sales_data.key_insights:
        prompt += f"- {insight}\n"
    
    return prompt