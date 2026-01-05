import os
import streamlit as st
import requests
import json
from typing import List

# =====================================================
# CONFIGURATION
# =====================================================
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://dmitriykuramshin-demoapi.hf.space"
)

HEALTH_URL = f"{API_BASE_URL}/deep-health"

st.set_page_config(
    page_title="Hybrid Search & Organization Finder",
    page_icon="🔍",
    layout="wide"
)

# =====================================================
# UI HEADER
# =====================================================
st.title("🔍 Hybrid Search & Organization Finder")
st.markdown(
    """
    This Streamlit app interacts with your **FastAPI hybrid search API**.  
    It performs BM25 or vector-based hybrid searches over your HS code index.
    """
)

# =====================================================
# HELPER FUNCTIONS
# =====================================================
def search_api(
    query: str,
    size: int,
    use_vector: bool,
    alpha: float,
    language: str,
    use_spelling: bool = False
):
    # Apply spelling correction if enabled
    search_query = query
    if use_spelling:
        try:
            spell_response = requests.post(
                f"{API_BASE_URL}/spellingcorrection",
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if spell_response.status_code == 200:
                spell_data = spell_response.json()
                corrected = spell_data.get("corrected_query", query)
                if corrected != query:
                    st.info(f"✨ Using corrected query: `{corrected}`")
                    search_query = corrected
        except Exception as e:
            st.warning(f"Spelling correction unavailable: {e}")
    
    payload = {
        "query": search_query,
        "size": size,
        "alpha": alpha,
        "use_vector": use_vector
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/search/{language}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        return None

def search_organizations(search_term: str, size: int):
    payload = {
        "search_term": search_term,
        "index": "organizations_v3",
        "size": size
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/organizations",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        return None

# =====================================================
# CREATE TABS
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs(["🇦🇿 Search AZ", "🇬🇧 Search EN", "🇷🇺 Search RU", "🏢 Organization Search"])

# =====================================================
# TAB 1: AZERBAIJANI SEARCH
# =====================================================
with tab1:
    st.header("Hybrid Search - Azerbaijani")
    
    with st.form("search_form_az"):
        query_az = st.text_input("Enter your search query:", placeholder="e.g. alüminium lövhələr")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            size_az = st.number_input("Number of results", min_value=1, max_value=50, value=10)
        with col2:
            alpha_az = st.slider("Vector weight (alpha)", 0.0, 1.0, 0.5, step=0.1, key="alpha_az")
        with col3:
            use_vector_az = st.checkbox("Use Vector Search", value=True, key="vector_az")
        with col4:
            use_spelling_az = st.checkbox("Spelling correction", value=False, key="spell_az")
        
        submitted_az = st.form_submit_button("Run Search")
    
    if submitted_az:
        if not query_az.strip():
            st.warning("⚠️ Please enter a query.")
        else:
            with st.spinner("Searching..."):
                result = search_api(query_az, size_az, use_vector_az, alpha_az, "az", use_spelling_az)
            
            if result:
                st.success(f"✅ Found {result.get('total-hits', 0)} hits")
                
                hits: List[dict] = result.get("Ranked-objects", [])
                if not hits:
                    st.info("No results found.")
                else:
                    for i, hit in enumerate(hits, start=1):
                        source = hit.get('_source', hit)
                        name_display = source.get('name_az_d4', source.get('code', 'No Name'))
                        
                        with st.expander(f"#{i} - {name_display}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Code:** `{source.get('code', 'N/A')}`")
                                score = hit.get('_score') or source.get('score')
                                if score:
                                    st.markdown(f"**Score:** {score:.4f}")
                                
                                st.markdown(f"**Category (D1):** {source.get('name_az_d1', 'N/A')}")
                                st.markdown(f"**Subcategory (D2):** {source.get('name_az_d2', 'N/A')}")
                                st.markdown(f"**Sub-subcategory (D3):** {source.get('name_az_d3', 'N/A')}")
                                st.markdown(f"**Product (D4):** {source.get('name_az_d4', 'N/A')}")
                                st.markdown(f"**Full Path:** {source.get('Path', '-')}")
                            
                            with col2:
                                tradings = source.get("tradings", [])
                                if tradings:
                                    st.markdown("**Tradings:**")
                                    for t in tradings:
                                        trade_type = t.get("tradeType", "N/A")
                                        trade_name = t.get("tradeName", "N/A")
                                        st.write(f"• {trade_name} ({trade_type})")
                                        
                                        if t.get("inVehicleId"):
                                            st.write(f"  In: Vehicle {t.get('inVehicleId')}")
                                        if t.get("outVehicleId"):
                                            st.write(f"  Out: Vehicle {t.get('outVehicleId')}")
                                else:
                                    st.markdown("*No trading info*")

# =====================================================
# TAB 2: ENGLISH SEARCH
# =====================================================
with tab2:
    st.header("Hybrid Search - English")
    
    with st.form("search_form_en"):
        query_en = st.text_input("Enter your search query:", placeholder="e.g. aluminium sheets")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            size_en = st.number_input("Number of results", min_value=1, max_value=50, value=10)
        with col2:
            alpha_en = st.slider("Vector weight (alpha)", 0.0, 1.0, 0.5, step=0.1, key="alpha_en")
        with col3:
            use_vector_en = st.checkbox("Use Vector Search", value=True, key="vector_en")
        with col4:
            use_spelling_en = st.checkbox("Spelling correction", value=False, key="spell_en")
        
        submitted_en = st.form_submit_button("Run Search")
    
    if submitted_en:
        if not query_en.strip():
            st.warning("⚠️ Please enter a query.")
        else:
            with st.spinner("Searching..."):
                result = search_api(query_en, size_en, use_vector_en, alpha_en, "en", use_spelling_en)
            
            if result:
                st.success(f"✅ Found {result.get('total-hits', 0)} hits")
                
                hits: List[dict] = result.get("Ranked-objects", [])
                if not hits:
                    st.info("No results found.")
                else:
                    for i, hit in enumerate(hits, start=1):
                        source = hit.get('_source', hit)
                        name_display = source.get('name_en_d4', source.get('code', 'No Name'))
                        
                        with st.expander(f"#{i} - {name_display}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Code:** `{source.get('code', 'N/A')}`")
                                score = hit.get('_score') or source.get('score')
                                if score:
                                    st.markdown(f"**Score:** {score:.4f}")
                                
                                st.markdown(f"**Category (D1):** {source.get('name_en_d1', 'N/A')}")
                                st.markdown(f"**Subcategory (D2):** {source.get('name_en_d2', 'N/A')}")
                                st.markdown(f"**Sub-subcategory (D3):** {source.get('name_en_d3', 'N/A')}")
                                st.markdown(f"**Product (D4):** {source.get('name_en_d4', 'N/A')}")
                                st.markdown(f"**Full Path:** {source.get('Path', '-')}")
                            
                            with col2:
                                tradings = source.get("tradings", [])
                                if tradings:
                                    st.markdown("**Tradings:**")
                                    for t in tradings:
                                        trade_type = t.get("tradeType", "N/A")
                                        trade_name = t.get("tradeName", "N/A")
                                        st.write(f"• {trade_name} ({trade_type})")
                                        
                                        if t.get("inVehicleId"):
                                            st.write(f"  In: Vehicle {t.get('inVehicleId')}")
                                        if t.get("outVehicleId"):
                                            st.write(f"  Out: Vehicle {t.get('outVehicleId')}")
                                else:
                                    st.markdown("*No trading info*")

# =====================================================
# TAB 3: RUSSIAN SEARCH
# =====================================================
with tab3:
    st.header("Hybrid Search - Russian")
    
    with st.form("search_form_ru"):
        query_ru = st.text_input("Enter your search query:", placeholder="e.g. алюминиевые листы")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            size_ru = st.number_input("Number of results", min_value=1, max_value=50, value=10)
        with col2:
            alpha_ru = st.slider("Vector weight (alpha)", 0.0, 1.0, 0.5, step=0.1, key="alpha_ru")
        with col3:
            use_vector_ru = st.checkbox("Use Vector Search", value=True, key="vector_ru")
        with col4:
            use_spelling_ru = st.checkbox("Spelling correction", value=False, key="spell_ru")
        
        submitted_ru = st.form_submit_button("Run Search")
    
    if submitted_ru:
        if not query_ru.strip():
            st.warning("⚠️ Please enter a query.")
        else:
            with st.spinner("Searching..."):
                result = search_api(query_ru, size_ru, use_vector_ru, alpha_ru, "ru", use_spelling_ru)
            
            if result:
                st.success(f"✅ Found {result.get('total-hits', 0)} hits")
                
                hits: List[dict] = result.get("Ranked-objects", [])
                if not hits:
                    st.info("No results found.")
                else:
                    for i, hit in enumerate(hits, start=1):
                        source = hit.get('_source', hit)
                        name_display = source.get('name_ru_d4', source.get('code', 'No Name'))
                        
                        with st.expander(f"#{i} - {name_display}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Code:** `{source.get('code', 'N/A')}`")
                                score = hit.get('_score') or source.get('score')
                                if score:
                                    st.markdown(f"**Score:** {score:.4f}")
                                
                                st.markdown(f"**Category (D1):** {source.get('name_ru_d1', 'N/A')}")
                                st.markdown(f"**Subcategory (D2):** {source.get('name_ru_d2', 'N/A')}")
                                st.markdown(f"**Sub-subcategory (D3):** {source.get('name_ru_d3', 'N/A')}")
                                st.markdown(f"**Product (D4):** {source.get('name_ru_d4', 'N/A')}")
                                st.markdown(f"**Full Path:** {source.get('Path', '-')}")
                            
                            with col2:
                                tradings = source.get("tradings", [])
                                if tradings:
                                    st.markdown("**Tradings:**")
                                    for t in tradings:
                                        trade_type = t.get("tradeType", "N/A")
                                        trade_name = t.get("tradeName", "N/A")
                                        st.write(f"• {trade_name} ({trade_type})")
                                        
                                        if t.get("inVehicleId"):
                                            st.write(f"  In: Vehicle {t.get('inVehicleId')}")
                                        if t.get("outVehicleId"):
                                            st.write(f"  Out: Vehicle {t.get('outVehicleId')}")
                                else:
                                    st.markdown("*No trading info*")

# =====================================================
# TAB 4: ORGANIZATION SEARCH
# =====================================================
with tab4:
    st.header("Organization Search")
    
    with st.form("search_form_org"):
        search_term = st.text_input("Enter organization name or abbreviation:", placeholder="e.g. UN")
        org_size = st.number_input("Number of results", min_value=1, max_value=50, value=10)
        st.info("🔒 Index: organizations_v3 (fixed)")
        
        submitted_org = st.form_submit_button("Search Organizations")
    
    if submitted_org:
        if not search_term.strip():
            st.warning("⚠️ Please enter a search term.")
        else:
            with st.spinner("Searching organizations..."):
                result = search_organizations(search_term, org_size)
            
            if result:
                st.success(f"✅ Found {result.get('total-hits', 0)} organizations")
                
                orgs: List[dict] = result.get("results", [])
                if not orgs:
                    st.info("No results found.")
                else:
                    for i, org in enumerate(orgs, start=1):
                        with st.expander(f"#{i} - {org.get('name', 'N/A')}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown(f"**Name:** {org.get('name', 'N/A')}")
                                st.markdown(f"**Abbreviation:** {org.get('abbreviation', 'N/A')}")
                                st.markdown(f"**ID:** {org.get('id', 'N/A')}")
                            
                            with col2:
                                score = org.get('score')
                                if score:
                                    st.markdown(f"**Score:** {score:.4f}")
                                
                                if org.get('additional_info'):
                                    st.markdown("**Additional Info:**")
                                    st.json(org.get('additional_info'))

# =====================================================
# SIDEBAR - API HEALTH CHECK
# =====================================================
with st.sidebar:
    st.header("API Status")
    
    if st.button("Check API Health"):
        try:
            health_response = requests.get(HEALTH_URL, timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.success("✅ API is reachable")
                st.json(health_data)
            else:
                st.error(f"⚠️ API returned status: {health_response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Cannot connect to API: {e}")
    
    st.markdown("---")
    st.markdown("### Search Tips")
    st.markdown("""
    - **BM25 only**: Uncheck "Use Vector Search"
    - **Hybrid search**: Check "Use Vector Search" and adjust alpha
    - **Alpha = 0.0**: Pure BM25
    - **Alpha = 1.0**: Pure vector similarity
    - **Alpha = 0.5**: Balanced hybrid
    """)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("© 2025 Hybrid Search Demo - FastAPI + Streamlit + Elasticsearch")
