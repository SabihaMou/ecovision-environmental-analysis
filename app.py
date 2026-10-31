import io
import pandas as pd
import plotly.express as px
import streamlit as st
from analysis import Scenario, components, compare, monte_carlo, sensitivity

st.set_page_config(page_title='EcoVision | Environmental Scenario Lab', page_icon='🌿', layout='wide')
st.markdown('''<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
[data-testid="stMetric"] {background: rgba(70,140,120,.09); padding: 14px; border-radius: 12px;}
h1 {letter-spacing:-1px;}
</style>''', unsafe_allow_html=True)
st.title('🌿 EcoVision')
st.caption('Environmental Impact & Uncertainty Analysis | Transparent scenario modelling')
st.info('**Educational prototype:** All default emission factors are illustrative placeholders, NOT verified local or lifecycle factors. Replace them with sourced factors before using results for real decisions. This is not a full LCA or a trained AI model.')

with st.sidebar:
    st.header('Activity data')
    electricity = st.number_input('Electricity use (kWh)', min_value=0., value=1000., step=100.)
    transport = st.number_input('Transport activity (km)', min_value=0., value=500., step=50.)
    material = st.number_input('Material quantity (kg)', min_value=0., value=200., step=20.)
    st.header('Illustrative emission factors')
    st.caption('Enter values from a documented source for real-world applications.')
    ef_e = st.number_input('Electricity (kg CO₂e/kWh)', min_value=0., value=.50, step=.05, format='%.3f')
    ef_t = st.number_input('Transport (kg CO₂e/km)', min_value=0., value=.20, step=.01, format='%.3f')
    ef_m = st.number_input('Material (kg CO₂e/kg)', min_value=0., value=1.50, step=.10, format='%.3f')
    st.header('Alternative scenario')
    energy_cut = st.slider('Electricity reduction (%)', 0, 100, 20)
    transport_cut = st.slider('Transport reduction (%)', 0, 100, 15)
    material_cut = st.slider('Material reduction (%)', 0, 100, 10)

base = Scenario(electricity, transport, material, ef_e, ef_t, ef_m)
alt = Scenario(electricity*(1-energy_cut/100), transport*(1-transport_cut/100), material*(1-material_cut/100), ef_e, ef_t, ef_m)
result = compare(base, alt)
a, b, c = st.columns(3)
a.metric('Baseline emissions', f"{result['baseline']:,.1f} kg CO₂e")
b.metric('Alternative emissions', f"{result['alternative']:,.1f} kg CO₂e")
c.metric('Estimated reduction', f"{result['reduction_percent']:.1f}%", f"{result['baseline']-result['alternative']:,.1f} kg CO₂e avoided")

t1, t2, t3 = st.tabs(['📊 Scenario comparison', '🎲 Uncertainty simulation', '🔍 Sensitivity analysis'])
with t1:
    st.subheader('Emissions by source')
    rows = []
    for scenario_name, scenario in [('Baseline', base), ('Alternative', alt)]:
        for source, amount in components(scenario).items():
            rows.append({'Scenario': scenario_name, 'Source': source, 'kg CO₂e': amount})
    chart_data = pd.DataFrame(rows)
    st.plotly_chart(px.bar(chart_data, x='Scenario', y='kg CO₂e', color='Source', barmode='stack', title='Scenario emission breakdown'), use_container_width=True)
    st.dataframe(chart_data, use_container_width=True, hide_index=True)
    st.download_button('Download scenario results (CSV)', chart_data.to_csv(index=False).encode(), 'ecovision_scenarios.csv', 'text/csv')
with t2:
    st.subheader('Monte Carlo uncertainty propagation')
    st.write('The simulation varies the **three emission factors independently** using lognormal distributions, while activity quantities remain fixed. The uncertainty setting is the assumed relative standard deviation of each factor.')
    uncertainty = st.slider('Assumed emission-factor relative standard deviation (%)', 0, 50, 15)
    n = st.select_slider('Simulation samples', options=[1000, 2500, 5000, 10000], value=5000)
    draws = monte_carlo(base, uncertainty/100, n)
    lo, med, hi = np_quantiles = [float(x) for x in __import__('numpy').percentile(draws, [2.5, 50, 97.5])]
    x, y, z = st.columns(3)
    x.metric('Simulation mean', f'{draws.mean():,.1f} kg CO₂e')
    y.metric('2.5th percentile', f'{lo:,.1f} kg CO₂e')
    z.metric('97.5th percentile', f'{hi:,.1f} kg CO₂e')
    st.plotly_chart(px.histogram(pd.DataFrame({'Estimated emissions (kg CO₂e)': draws}), x='Estimated emissions (kg CO₂e)', nbins=60, title='Distribution of simulated baseline emissions'), use_container_width=True)
    st.caption('The 2.5th–97.5th percentile interval is conditional on the chosen distributions and uncertainty assumptions; it is not a validated real-world confidence interval.')
    st.download_button('Download simulation results (CSV)', pd.DataFrame({'emissions_kg_co2e': draws}).to_csv(index=False).encode(), 'ecovision_monte_carlo.csv', 'text/csv')
with t3:
    st.subheader('One-at-a-time sensitivity')
    pct = st.slider('Increase each activity quantity by (%)', 1, 50, 10)
    effects = sensitivity(base, pct/100)
    sensitivity_df = pd.DataFrame({'Input changed': list(effects), 'Increase in emissions (kg CO₂e)': list(effects.values())}).sort_values('Increase in emissions (kg CO₂e)')
    st.plotly_chart(px.bar(sensitivity_df, x='Increase in emissions (kg CO₂e)', y='Input changed', orientation='h', title=f'Impact of +{pct}% change in each activity'), use_container_width=True)
    st.caption('This is a local, one-at-a-time sensitivity test. It does not capture interactions or uncertainty in activity quantities.')

with st.expander('Methodology, units & limitations'):
    st.markdown('''**Formula:** Total emissions (kg CO₂e) = Σ(activity quantity × emission factor). Each source is calculated independently and summed. The activity boundaries are simplified and user-defined.

**Comparison:** The alternative scenario changes activity quantities, not emission factors. Reduction % = (baseline − alternative) / baseline × 100, when baseline > 0.

**Uncertainty:** Emission factors are sampled from independent lognormal distributions with user-selected relative standard deviation. Fixed random seed makes the result reproducible. Correlation, model error, and quantity uncertainty are not represented.

**Sensitivity:** One activity quantity is increased by the selected percentage at a time. Effects are changes in kg CO₂e.

**Limitations:** Default factors are illustrative, not sourced measurements; transport mode, electricity grid mix, material production pathway, lifecycle boundaries, allocation, and temporal variation are not represented. This tool cannot be used as a verified carbon inventory or full life-cycle assessment without suitable factors, boundaries, and validation.''')
st.caption('Built with Python, Streamlit, NumPy, Pandas and Plotly · Research-oriented portfolio demonstration')
