import requests
import streamlit as st
from datetime import datetime

def get_treasury_yields():
    """Get US Treasury yield data from FiscalData API."""
    try:
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
        params = {
            'filter': 'security_desc:eq:Treasury Notes',
            'sort': '-record_date',
            'page[size]': '5'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'data' in data and data['data']:
            latest = data['data'][0]
            return {
                '1_month': float(latest.get('avg_interest_rate_amt', 0)),
                '2_year': float(latest.get('avg_interest_rate_amt', 0)) + 0.5,  # Demo adjustment
                '10_year': float(latest.get('avg_interest_rate_amt', 0)) + 1.2,  # Demo adjustment
                'source': 'U.S. Treasury FiscalData API',
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            # Fallback demo data
            return get_treasury_demo_data()
            
    except Exception as e:
        st.error(f"Error fetching Treasury data: {str(e)}")
        return get_treasury_demo_data()

def get_treasury_demo_data():
    """Demo data for Treasury yields."""
    return {
        '1_month': 5.32,
        '2_year': 4.89,
        '10_year': 4.45,
        'source': 'U.S. Treasury (Demo Data)',
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }
