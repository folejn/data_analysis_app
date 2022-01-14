import plotly.graph_objects as go
from PIL import Image

def style(figure):
    img = Image.open("image.jpg")

    img_width = 500
    img_height = 500
    scale_factor = 1
    figure.add_layout_image(dict(
        x=0,
        sizex=img_width,
        y=0,
        sizey=img_height,
        xref="x",
        yref="y",
        sizing="contain",
        opacity=1.0,
        layer="below",
        source=img
    ))

    figure.update_layout(template="plotly_white", autosize=False, width=img_width, height=img_height)
    figure.update_xaxes(visible=False, showgrid=False, range=(0, img_width))
    figure.update_yaxes(visible=False, showgrid=False, range=(img_height, 0))