import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import base64

# Add the src directory to the path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from vertex_benchmark.database_utils import (
    get_db_connection,
    get_all_benchmark_results,
    get_all_batches,
    get_results_by_batch_id,
)
from vertex_benchmark.config import EUROPEAN_LOCATIONS, WORLDWIDE_LOCATIONS
from vertex_benchmark.generate_report import generate_pdf_report
import time

# Page settings for better layout
st.set_page_config(
    page_title="Vertex AI Benchmark Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session defaults
if 'selected_lang' not in st.session_state:
    st.session_state.selected_lang = 'sk'
if 'selected_batch_id' not in st.session_state:
    st.session_state.selected_batch_id = None

# Handle language via query params
try:
    qp = st.query_params
    if 'lang' in qp:
        lang_val = qp.get('lang')
        if isinstance(lang_val, list):
            lang_val = lang_val[0]
        if lang_val in ('sk', 'en') and st.session_state.selected_lang != lang_val:
            st.session_state.selected_lang = lang_val
            st.rerun()
except Exception:
    pass

def _img_tag(path: str, width: int) -> str:
    """Return an <img> tag with base64 data URI to avoid file:// placeholders."""
    try:
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return f"<img class='flag-img' src='data:image/png;base64,{b64}' width='{width}'/>"
    except Exception:
        return ""

def _current_plotly_template() -> str:
    return 'plotly_white'

# Translation dictionary
TRANSLATIONS = {
    'title': {'sk': 'Vertex AI Gemini 2.5 Výkonnostné Testy', 'en': 'Vertex AI Gemini 2.5 Performance Tests'},
    'select_region': {'sk': 'Vyberte región', 'en': 'Select Region'},
    'batch_date': {'sk': 'Dátum testu', 'en': 'Test Date'},
    'region': {'sk': 'Región', 'en': 'Region'},
    'cycle': {'sk': 'Cyklus', 'en': 'Cycle'},
    'pro_time': {'sk': 'Gemini Pro Čas (ms)', 'en': 'Gemini Pro Time (ms)'},
    'flash_time': {'sk': 'Gemini Flash Čas (ms)', 'en': 'Gemini Flash Time (ms)'},
    'garden_models': {'sk': 'Garden Modely', 'en': 'Garden Models'},
    'test_prompt': {'sk': 'Test Prompt', 'en': 'Test Prompt'},
    'generate_pdf': {'sk': 'Generovať PDF Report', 'en': 'Generate PDF Report'},
    'select_language': {'sk': 'Vyberte jazyk', 'en': 'Select Language'},
    'slovak': {'sk': 'Slovenčina', 'en': 'Slovak'},
    'english': {'sk': 'Angličtina', 'en': 'English'}
}

def translate(key, lang):
    """Translate a key to the specified language."""
    return TRANSLATIONS.get(key, {}).get(lang, key)

def format_slovak_datetime(iso_datetime):
    """Format ISO datetime to Slovak format (DD.MM.YYYY HH:MM)."""
    try:
        dt = pd.to_datetime(iso_datetime)
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return iso_datetime

def main():
    """Main dashboard function."""
    # Header with title (left) and language buttons (right)
    h1, spacer, lang_sk_col, lang_en_col = st.columns([6, 4, 0.6, 0.6])
    with h1:
        st.title(translate('title', st.session_state.selected_lang))
    # Resolve flag asset paths
    resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'resources'))
    sk_flag = os.path.join(resources_dir, 'sk-flag.png')
    us_flag = os.path.join(resources_dir, 'us-flag.png')
    # Icon-only language "buttons" as clickable flag images (no rectangle)
    st.markdown(
        """
        <style>
        .flag-button button {
            width: 40px;
            height: 40px;
            border-radius: 999px;
            padding: 0;
            border: none;
            background: transparent;
            box-shadow: none;
        }
        .flag-button button:hover {
            box-shadow: none;
            background: rgba(128,128,128,0.2);
        }
        .flag-button img { border-radius: 999px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with lang_sk_col:
        if st.button("🇸🇰", key='lang_sk_btn'):
            st.session_state.selected_lang = 'sk'
    with lang_en_col:
        if st.button("🇺🇸", key='lang_en_btn'):
            st.session_state.selected_lang = 'en'
    # Spacer to keep header height constant across reruns
    st.markdown('<div class="header-spacer"></div>', unsafe_allow_html=True)

    # Sidebar with benchmark run selector only
    with st.sidebar:
        st.header("Benchmark run")
        # Batch selector (date-only, locale-aware)
        try:
            batches = get_all_batches()
        except Exception as e:
            batches = []
            st.error(f"Failed to load batches: {e}")

        if batches:
            def fmt_label(b):
                started = b.get('started_at', '')
                if st.session_state.selected_lang == 'sk':
                    return format_slovak_datetime(started)
                try:
                    dt = pd.to_datetime(started)
                    return dt.strftime('%d %b %Y %H:%M')
                except Exception:
                    return str(started)

            labels = [fmt_label(b) for b in batches]
            indices = list(range(len(batches)))
            selected_index = st.selectbox(
                " ", indices,
                format_func=lambda i: labels[i],
                index=0,
                label_visibility='collapsed'
            )
            sel_batch_id = batches[selected_index]['batch_id']
            if sel_batch_id != st.session_state.selected_batch_id:
                st.session_state.selected_batch_id = sel_batch_id
                st.rerun()
        else:
            st.info("No benchmark runs found.")
        # No duplicate controls in sidebar
    
    # Load data
    try:
        # Prefer selected batch if available
        if st.session_state.selected_batch_id:
            all_data = get_results_by_batch_id(st.session_state.selected_batch_id)
        else:
            all_data = get_all_benchmark_results()
        if not all_data:
            st.info("No benchmark data found.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        # Drop technical columns from table view
        df = df.drop(columns=['id', 'batch_id'], errors='ignore')
        # Ensure proper dtypes
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        for col in ('pro_time_ms', 'flash_time_ms'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Column mapping
        column_mapping = {
            'timestamp': translate('batch_date', st.session_state.selected_lang),
            'region': translate('region', st.session_state.selected_lang),
            'cycle_num': translate('cycle', st.session_state.selected_lang),
            'pro_time_ms': translate('pro_time', st.session_state.selected_lang),
            'flash_time_ms': translate('flash_time', st.session_state.selected_lang),
            'garden_models': translate('garden_models', st.session_state.selected_lang),
            'test_prompt': translate('test_prompt', st.session_state.selected_lang)
        }
        
        # Rename columns
        df_display = df.rename(columns=column_mapping)
        
        # Filters
        st.subheader("Benchmark Results")
        with st.expander("Filters", expanded=False):
            regions = sorted(df['region'].unique().tolist()) if 'region' in df.columns else []
            selected_regions = st.multiselect(
                translate('select_region', st.session_state.selected_lang),
                regions,
                default=regions
            )
        # Apply filters
        if selected_regions:
            df_filtered = df[df['region'].isin(selected_regions)].copy()
        else:
            df_filtered = df.copy()

        # Results table
        with st.expander("Results Table", expanded=True):
            st.dataframe(df_filtered.rename(columns=column_mapping), use_container_width=True)

        # Charts section
        st.subheader("Charts")
        if df_filtered.empty:
            st.info("No data for selected filters.")
            return

        tabs = st.tabs(["Overview", "By Cycle"])

        # Average latency per region (bar)
        with tabs[0]:
            avg_df = df_filtered.groupby('region', as_index=False).agg({
                'pro_time_ms': 'mean',
                'flash_time_ms': 'mean'
            })
            avg_long = avg_df.melt(id_vars='region', value_vars=['pro_time_ms', 'flash_time_ms'],
                                   var_name='model', value_name='avg_ms')
            model_map = {'pro_time_ms': 'Pro', 'flash_time_ms': 'Flash'}
            avg_long['model'] = avg_long['model'].map(model_map)
            bar_fig = px.bar(avg_long, x='region', y='avg_ms', color='model', barmode='group',
                             title='Average Latency by Region (ms)')
            # Remove thin borders in dark theme: disable bar outlines and legend frame
            bar_fig.update_traces(marker_line_width=0, marker_line_color='rgba(0,0,0,0)')
            bar_fig.update_layout(
                template=_current_plotly_template(),
                height=420,
                margin=dict(t=50, b=40),
                legend=dict(borderwidth=0, bgcolor='rgba(0,0,0,0)')
            )
            st.plotly_chart(bar_fig, use_container_width=True)

        # Time series by cycle (line) with region selector (no excessive facets)
        with tabs[1]:
            if {'cycle_num', 'pro_time_ms', 'flash_time_ms'}.issubset(df_filtered.columns):
                selectable_regions = sorted(df_filtered['region'].unique().tolist())
                default_sel = selectable_regions[: min(6, len(selectable_regions))]
                sel_regions = st.multiselect("Regions for cycle chart", selectable_regions, default_sel)
                ts_df = df_filtered[df_filtered['region'].isin(sel_regions)].copy() if sel_regions else df_filtered.copy()
                if ts_df.empty:
                    st.info("No data for selected regions.")
                else:
                    ts_long = ts_df.melt(id_vars=['region', 'cycle_num'],
                                         value_vars=['pro_time_ms', 'flash_time_ms'],
                                         var_name='model', value_name='ms')
                    ts_long['model'] = ts_long['model'].map({'pro_time_ms': 'Pro', 'flash_time_ms': 'Flash'})
                    line_fig = px.line(ts_long.sort_values(['region', 'cycle_num']),
                                       x='cycle_num', y='ms', color='model', line_group='region',
                                       facet_col='region', facet_col_wrap=3,
                                       title='Latency by Cycle (ms)')
                    line_fig.update_layout(
                        template=_current_plotly_template(),
                        height=600,
                        margin=dict(t=50, b=40),
                        legend=dict(borderwidth=0, bgcolor='rgba(0,0,0,0)')
                    )
                    st.plotly_chart(line_fig, use_container_width=True)

        # Generate PDF button
        st.subheader(translate('generate_pdf', st.session_state.selected_lang))
        if st.button(translate('generate_pdf', st.session_state.selected_lang)):
            with st.spinner('Generating PDF...'):
                try:
                    pdf_path = generate_pdf_report()
                    if pdf_path and os.path.exists(pdf_path):
                        st.success(f"PDF generated: {pdf_path}")
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                label="Download PDF",
                                data=f.read(),
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf"
                            )
                except Exception as e:
                    st.error(f"Failed to generate PDF: {e}")
        
    except Exception as e:
        st.error(f"Error loading data: {e}")

# Initialize session state
if 'selected_lang' not in st.session_state:
    st.session_state.selected_lang = 'sk'

if __name__ == "__main__":
    main()