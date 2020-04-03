import streamlit as st

_SUSCEPTIBLE_COLOR = "#0086c9"
_RECOVERED_COLOR = "rgba(180,200,180,.4)"

COLOR_MAP = {
    "default": "#262730",
    "pink": "#E22A5B",
    "purple": "#985FFF",
    "susceptible": _SUSCEPTIBLE_COLOR,
    "recovered": _RECOVERED_COLOR,
}


def generate_html(
    text,
    color=COLOR_MAP["default"],
    bold=False,
    font_family=None,
    font_size=None,
    line_height=None,
    tag="div",
):
    if bold:
        text = f"<strong>{text}</strong>"
    css_style = f"color:{color};"
    if font_family:
        css_style += f"font-family:{font_family};"
    if font_size:
        css_style += f"font-size:{font_size};"
    if line_height:
        css_style += f"line-height:{line_height};"

    return f"<{tag} style={css_style}>{text}</{tag}>"


graph_warning = "Please be aware the scale of this graph changes!"

def img_html(
        src, alt_text, href , attributes, style="float:right;"
):
    attributes_text = ''
    if attributes:
        attributes_text = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])

    body = f"""<div style="{style}"><a href="{href}"><img src="{src}" {attributes_text} title="{alt_text}"></a></div>"""
    return st.markdown(body=body, unsafe_allow_html=True)
