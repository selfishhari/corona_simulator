import streamlit as st


def reported_vs_true_cases(num_cases_confirmed, num_cases_estimated, lower=10, upper=20):
    _border_color = "light-gray"
    _number_format = "font-size:35px; font-style:bold;"
    _range_string = "(" + str(lower) + " - " +  str(upper) + ")"
    _cell_style = f" border: 2px solid {_border_color}; border-bottom:2px solid white; margin:10px"
    st.markdown(
        f"<table style='width: 100%; font-size:14px;  border: 0px solid gray; border-spacing: 10px;  border-collapse: collapse;'> "
        f"<tr> "
        f"<td style='{_cell_style}'> Confirmed Cases</td> "
        f"<td style='{_cell_style}'> Estimated Cases (1 Week)</td>"
        "</tr>"
        f"<tr style='border: 2px solid {_border_color}'> "
        f"<td style='border-right: 2px solid {_border_color}; border-spacing: 10px; {_number_format + 'font-color:red;'}' > {num_cases_confirmed}</td> "
        f"<td style='{_number_format + 'color:#0068c9'}'> {int(num_cases_estimated):,} <span style='font-size:18px;'>{_range_string}</span></td>"
        #f"<td style= 'font-size:26px; font-style:bold;color:blue;'> {_range_string} </td>"
        "</tr>"
        "</table>"
        "<br>",
        unsafe_allow_html=True,
    )

    # Calls to streamlit render immediately, no need to return anything
