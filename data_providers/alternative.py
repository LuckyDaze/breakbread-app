import streamlit as st
from datetime import datetime
import random

def get_startup_investments():
    """Demo data for startup investing platforms."""
    platforms = [
        {'name': 'AngelList', 'min_investment': 1000, 'avg_roi': '15-40%', 'liquidity': '2-7 years'},
        {'name': 'StartEngine', 'min_investment': 100, 'avg_roi': '10-30%', 'liquidity': '3-5 years'},
        {'name': 'Republic', 'min_investment': 50, 'avg_roi': '12-35%', 'liquidity': '2-6 years'}
    ]
    
    return {
        'platforms': platforms,
        'source': 'Demo Data (Platform Aggregation)',
        'last_updated': datetime.now()
    }

def get_royalty_investments():
    """Demo data for royalty investing."""
    royalties = [
        {'asset': 'Music Catalog A', 'yield': '8.5%', 'min_investment': 5000, 'term': '10 years'},
        {'asset': 'Film Rights B', 'yield': '12.2%', 'min_investment': 10000, 'term': '15 years'},
        {'asset': 'Patent Portfolio C', 'yield': '15.8%', 'min_investment': 25000, 'term': '20 years'}
    ]
    
    return {
        'royalties': royalties,
        'source': 'Demo Data (Royalty Exchange)',
        'last_updated': datetime.now()
    }

def get_business_listings():
    """Demo data for business marketplaces."""
    businesses = [
        {'name': 'Tech Startup XYZ', 'price': 450000, 'revenue': 120000, 'industry': 'SaaS'},
        {'name': 'Local Restaurant Chain', 'price': 850000, 'revenue': 350000, 'industry': 'Food & Beverage'},
        {'name': 'E-commerce Store', 'price': 275000, 'revenue': 180000, 'industry': 'Retail'}
    ]
    
    return {
        'businesses': businesses,
        'source': 'Demo Data (BizBuySell)',
        'last_updated': datetime.now()
    }
