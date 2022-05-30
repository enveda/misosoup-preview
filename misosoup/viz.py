# misosoup/viz.py

__doc__ = """
Altair modules
"""

import altair as alt
import logging
import numpy as np
import pandas as pd

# import panel as pn

log = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Styling
# ------------------------------------------------------------------------------


alt.data_transformers.disable_max_rows()

ALTAIR_CSS = """
<style>
.vega-bind > label > input {
  -webkit-appearance: none;
  width: 800px;
  border-radius: 20px;
  background: #f4b183;
}
.vega-bind > label > input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;  height: 20px;
  border-radius: 50%;
  border: 2px solid black;
  background: #14eb95;

}
</style>
"""

ALTAIR_JS = ""


def altair_misosoup_theme():
    """Apply appropriate font sizes etc."""
    theme = {
        "config": {
            "axis": {
                "labelFont": "Tahoma",
                "labelFontSize": 13,
                "titleFontSize": 16,
            },
            "legend": {
                "labelFont": "Tahoma",
                "labelFontSize": 14,
                "padding": 12,
                "titleFontSize": 16,
            },
            "title": {"font": "Tahoma", "fontSize": 20, "offset": 15},
        },
        "$schema": "https://vega.github.io/schema/vega-lite/v4.17.0.json",
    }

    return theme


def apply_style(css=None, js=None, theme=None):
    """Applies styles and scripts to the notebook."""

    if not css:
        css = ALTAIR_CSS
    if not js:
        js = ALTAIR_JS
    if not theme:
        theme = altair_misosoup_theme

    try:
        from IPython.display import display, HTML

        display(HTML(css + js))
        alt.themes.register("altair_misosoup_theme", theme)
        alt.themes.enable("altair_misosoup_theme")
    except Exception as e:
        log.error(e)


# ------------------------------------------------------------------------------
# UI
# ------------------------------------------------------------------------------


def add_zoom(chart: alt.Chart, x_axis_key="shift"):
    """Add customized zoom functionality."""

    wheel_zoom_x = alt.selection_interval(
        bind="scales", encodings=["x"], zoom="wheel!"
    )

    wheel_zoom_xy = alt.selection_interval(
        bind="scales", zoom="wheel![event.shiftKey]",
    )

    return chart.add_selection(wheel_zoom_xy, wheel_zoom_x)


# ------------------------------------------------------------------------------
# Plotting functions
# ------------------------------------------------------------------------------


def plot_fims_with_rt_filter(
    df,
    title="FIMS Plot (use slider below to select RT window)",
    figsize=(720, 400),
):
    """FIMS plot with RT filter."""

    apply_style()

    input_slider = alt.binding_range(
        min=min(df.rt),
        max=max(df.rt),
        step=1,
        name="Retention Time ± 10 secs",
    )

    selection_slider = alt.selection_single(
        fields=["rt"], bind=input_slider, init=dict(rt=5)
    )

    chart = (
        alt.Chart(df.sort_values("intensity"), title=title)
        .mark_circle(size=25, opacity=0.5)
        .encode(
            x=alt.X(
                "mz_integer:Q", scale=alt.Scale(domain=(0, 1200), clamp=True)
            ),
            y=alt.Y(
                "mz_fractional:Q",
                scale=alt.Scale(domain=(-0.01, 1.01), nice=False, clamp=True),
            ),
            color=alt.Color(
                "intensity:Q",
                scale=alt.Scale(
                    type="log", domain=(1000, 1_000_000), scheme="viridis"
                ),
                legend=alt.Legend(title="Feature Intensity"),
            ),
            tooltip=[
                alt.Tooltip("mz", format=".4f"),
                alt.Tooltip("intensity"),
                alt.Tooltip("rt", format=".2f"),
            ],
        )
        .transform_calculate(
            mz_integer="floor(datum.mz)", mz_fractional="datum.mz % 1",
        )
        .transform_filter(
            (alt.datum.rt < selection_slider.rt + 10)
            & (selection_slider.rt - 10 < alt.datum.rt)
        )
        .add_selection(selection_slider)
        .properties(width=figsize[0], height=figsize[1])
    )
    return add_zoom(chart)


def plot_xit(
    df: pd.DataFrame,
    title="XIT",
    figsize=(720, 400),
    x="frame",
    y="spectrum",
    z="intensity",
    zlog=True,
    shape="circle",
    size=36,
    opacity=0.75,
    lc="rgba(0,0,0,0.75)",
    lw=0.5,
    clim=None,
    cmap="turbo",
    cbar=True,
    reverse_cmap=False,
    tooltip=[],
):
    """Interactive XIT plot.

    Examples
    --------
    >>> plot_xit(df, x='x', y='y', z='z', tooltip=list('mxyzn'), title="WOWMZ")
    """

    apply_style()
    if not clim:
        domain = df[z].min(), df[z].max()
    else:
        domain = clim
    if reverse_cmap:
        domain = domain[::-1]
    if cbar:
        legend = alt.Legend(title=z)
    else:
        legend = None

    chart = (
        alt.Chart(df.sort_values(z), title=title)
        .mark_point(
            shape=shape, size=size, stroke=lc, strokeWidth=lw, opacity=opacity
        )
        .encode(
            x=x,
            y=y,
            fill=alt.Color(
                z,
                scale=alt.Scale(
                    type="log" if zlog else "linear",
                    domain=domain,
                    scheme=cmap,
                ),
                legend=legend,
            ),
            tooltip=tooltip,
        )
        .properties(width=figsize[0], height=figsize[1])
    )
    return add_zoom(chart)
