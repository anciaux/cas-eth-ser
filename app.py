import os
import sys
import streamlit as st
import matplotlib.pyplot as plt
################################################################
plt.rcParams['figure.figsize'] = [10, 10]


sub_apps = [
    'Présentation',
    'plate_hole',
    'stress_intensity_factor',
    'fragmentation_cohesive'
]

tabs = st.tabs(sub_apps)

with tabs[0]:
    st.markdown(
        '## <center> CAS ETH in Seismic Evaluation and Retrofitting (CAS ETH SER)</center>',
        unsafe_allow_html=True)
    st.markdown('''
    ### <center> Numerical Methods for Modeling Dynamic Fracture of Materials, Introduction to the FE software Akantu, Applications of Akantu to Civil Engineering </center>''', unsafe_allow_html=True)
    st.markdown('''
    ##### <center> J.F. Molinari</center>''', unsafe_allow_html=True)
    st.markdown(
        '---\n\n<center><a href="https://akantu.ch"><img src="https://akantu.ch/wp-content/uploads/2018/04/cropped-logo_Akantu.png"><br>https://akantu.ch</a></center>',
        unsafe_allow_html=True)

for name, tab in zip(sub_apps[1:], tabs[1:]):
    with tab:
        try:
            import importlib
            sys.path.append(name)
            spec = importlib.util.spec_from_file_location(
                name, os.path.join(name, name+'.py'))
            foo = importlib.util.module_from_spec(spec)
            sys.modules[name] = foo
            spec.loader.exec_module(foo)
        except Exception as err:
            st.error(err)
            raise err
