import io
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title='Election Night 2026', page_icon='🗳️', layout='wide')
st.title('2026 Election Night Dashboard')
st.caption('National • Maine • Vermont | Unofficial results • Not a race-calling service')

COLUMNS = ['timestamp_utc','region','state','race','geography','candidate','party','votes']
@st.cache_data(ttl=60, show_spinner=False)
def read_url(url):
    response = requests.get(url, timeout=12, headers={'User-Agent':'ElectionDashboard/1.0'})
    response.raise_for_status()
    if len(response.content) > 8_000_000:
        raise ValueError('CSV exceeds 8 MB')
    return pd.read_csv(io.BytesIO(response.content))

def clean(df):
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    df = df[COLUMNS].copy()
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce')
    if df['votes'].isna().any() or (df['votes'] < 0).any():
        raise ValueError('Votes must be nonnegative numbers')
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True, errors='coerce')
    if df['timestamp_utc'].isna().any():
        raise ValueError('All timestamps must be valid ISO dates')
    for c in ['region','state','race','geography','candidate','party']:
        df[c] = df[c].fillna('').astype(str).str.strip()
    if (df[['region','state','race','geography','candidate']] == '').any().any():
        raise ValueError('Region, state, race, geography and candidate are required')
    # Each snapshot is cumulative; retain latest observation per candidate and geography.
    return df.sort_values('timestamp_utc').drop_duplicates(['region','state','race','geography','candidate'], keep='last')

with st.sidebar:
    st.header('Data source')
    mode = st.radio('Load results', ['Sample data (demo)', 'Upload CSV', 'Public CSV URL'])
    st.caption('Only use a public, authorized CSV feed. Do not paste private API keys.')
    uploaded = st.file_uploader('Results CSV', type=['csv']) if mode == 'Upload CSV' else None
    url = st.text_input('Public CSV URL', placeholder='https://.../results.csv') if mode == 'Public CSV URL' else ''
    if mode == 'Public CSV URL':
        st.caption('Cached for 60 seconds. Use Refresh to request new results.')
    if st.button('Refresh data', use_container_width=True):
        read_url.clear()
        st.rerun()
    st.divider()
    st.download_button('Download CSV template', data=open('data/template.csv', encoding='utf-8').read(), file_name='election_results_template.csv', mime='text/csv', use_container_width=True)

try:
    if mode == 'Sample data (demo)':
        raw = pd.read_csv('data/sample.csv')
    elif mode == 'Upload CSV':
        raw = pd.read_csv(uploaded) if uploaded is not None else None
    else:
        raw = read_url(url) if url else None
    df = clean(raw) if raw is not None else None
except Exception as e:
    st.error(f'Could not load results: {e}')
    df = None

if df is None:
    st.info('Upload a CSV or enter a public CSV URL. You can start with the downloadable template.')
    st.stop()

if mode == 'Sample data (demo)':
    st.warning('DEMONSTRATION DATA ONLY — fictional vote totals, not actual 2026 election results.')
else:
    st.info('User-supplied results. Verify source, timestamps, reporting completeness and official race calls independently.')

latest = df['timestamp_utc'].max()
st.caption('Latest observation in file: ' + latest.strftime('%Y-%m-%d %H:%M UTC') + ' • Results may be partial and may change')

sections = st.tabs(['🇺🇸 National', '🇲🇪 Maine', '🇻🇹 Vermont', '📈 Reporting trends', 'About the data'])
for tab, region in zip(sections[:3], ['National','Maine','Vermont']):
    with tab:
        subset = df[df['region'].str.casefold() == region.casefold()].copy()
        if subset.empty:
            st.info(f'No {region} records loaded yet.')
            continue
        races = sorted(subset['race'].unique())
        race = st.selectbox('Race', races, key=f'race_{region}')
        race_df = subset[subset['race'] == race]
        areas = ['All reported geographies'] + sorted(race_df['geography'].unique().tolist())
        area = st.selectbox('Geography', areas, key=f'area_{region}')
        if area != 'All reported geographies':
            race_df = race_df[race_df['geography'] == area]
        # Aggregating across geography assumes nonoverlapping units and no duplicate statewide totals.
        totals = race_df.groupby(['candidate','party'], as_index=False)['votes'].sum().sort_values('votes', ascending=False)
        total_votes = int(totals['votes'].sum())
        st.metric('Votes in selected reporting units', f'{total_votes:,}')
        if total_votes:
            totals['share_pct'] = 100 * totals['votes'] / total_votes
            fig = px.bar(totals, x='candidate', y='votes', color='party', text='share_pct',
                         labels={'candidate':'Candidate','votes':'Reported votes','party':'Party'})
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(yaxis_rangemode='tozero')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(totals, hide_index=True, use_container_width=True)
        st.caption('Vote share is among listed candidates only. Reporting percentage is unavailable unless supplied separately.')
with sections[3]:
    st.subheader('Snapshots and change over time')
    st.write('The main views show the latest cumulative snapshot for each candidate/geography. For a trend chart, upload a CSV containing multiple timestamped snapshots.')
    try:
        history = raw[COLUMNS].copy()
        history['timestamp_utc'] = pd.to_datetime(history['timestamp_utc'], utc=True, errors='coerce')
        history['votes'] = pd.to_numeric(history['votes'], errors='coerce')
        valid = history.dropna(subset=['timestamp_utc','votes'])
        if valid['timestamp_utc'].nunique() > 1:
            opts = sorted(valid['race'].dropna().unique())
            chosen = st.selectbox('Race for trend', opts)
            h = valid[valid['race'] == chosen]
            h = h.groupby(['timestamp_utc','candidate'], as_index=False)['votes'].sum()
            st.plotly_chart(px.line(h, x='timestamp_utc', y='votes', color='candidate', markers=True,
                                    labels={'timestamp_utc':'Observation time (UTC)','votes':'Cumulative votes'}), use_container_width=True)
            st.caption('Use consistent geography coverage for every snapshot; otherwise trends can be misleading.')
        else:
            st.info('Only one snapshot timestamp is available.')
    except Exception:
        st.info('Trend data is unavailable.')
with sections[4]:
    st.markdown('''**Schema:** `timestamp_utc, region, state, race, geography, candidate, party, votes`.

- Each row represents a candidate's **cumulative** vote total in one geographic reporting unit at a particular time.
- Use `National`, `Maine`, or `Vermont` in the `region` field. `state` is the two-letter abbreviation.
- Never mix statewide totals with their constituent counties or towns in the same race; doing so double-counts votes.
- Keep geographic units mutually exclusive and use consistent naming.
- The app does not automatically discover election results, certify totals, or call races.
- Public CSV URL mode fetches on page rerun/refresh; it is not a background collection service.
- Upload mode data is not persistent across browser sessions or cloud restarts. Save source files elsewhere.
- Do not interpret partial returns as final election outcomes. Ranked-choice tabulations may require separate rounds.
''')
