from typing import Literal

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.var import PLT_FONT_SIZE


def plot_sunburst(df: pd.DataFrame) -> go.Figure:
    fig = px.sunburst(
        data_frame=df.assign(hole=" "),
        path=["hole", "macro_asset_class", "asset_class", "ticker_yf"],
        values="weight_pf",
    )
    fig.update_traces(hovertemplate="<b>%{value:.1f}%")
    fig.update_layout(
        autosize=False,
        height=620,
        margin=dict(l=0, r=0, t=20, b=20),
        hoverlabel_font_size=PLT_FONT_SIZE,
    )
    return fig


def plot_pnl_by_asset_class(
    df_pnl: pd.DataFrame,
    group_by: Literal["asset_class", "macro_asset_class"],
) -> go.Figure:
    df_pnl = df_pnl.sort_values("pnl", ascending=False)
    df_pnl["color"] = np.where(df_pnl["pnl"].ge(0), "green", "firebrick")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_pnl[group_by],
            y=df_pnl["pnl"],
            marker_color=df_pnl["color"],
            text=df_pnl["pnl"],
            hoverinfo="skip",
        )
    )
    fig.update_traces(texttemplate="%{y:,.1f} €")
    fig.update_layout(
        autosize=False,
        height=550,
        margin=dict(l=0, r=0, t=20, b=20),
        barmode="stack",
        yaxis=dict(title="PnL", showgrid=False, tickformat=",.0f", ticksuffix=" €"),
    )
    return fig


def plot_wealth(df: pd.DataFrame) -> go.Figure:
    fig = px.area(
        data_frame=df, x=df.index, y="ap_daily_value", custom_data=["diff_previous_day"]
    )
    fig.update_traces(
        hovertemplate=(
            "Portfolio value: <b>%{y:,.0f}€</b>"
            "<extra>P&L vs previous day: %{customdata:,.0f}€</extra>"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["ap_cum_spent"],
            mode="lines",
            name="Cumulative Spent",
            line=dict(dash="6px", width=1.5, color="bisque"),
            customdata=df["ap_cum_pnl"],
            hovertemplate=(
                "Invested capital: <b>%{y:,.0f}€</b>"
                "<extra>Ap-/De-preciation: %{customdata:,.0f}€</extra>"
            ),
        )
    )
    fig.update_layout(
        autosize=False,
        height=550,
        hoverlabel_font_size=PLT_FONT_SIZE,
        hovermode="x",
        margin=dict(l=0, r=0, t=20, b=20),
        xaxis=dict(title=""),
        yaxis=dict(title="", showgrid=False, tickformat=",.0f", ticksuffix=" €"),
        showlegend=False,
    )
    return fig


def plot_correlation_map(
    df: pd.DataFrame,
    enhance_correlation: Literal["positive", "null", "negative"],
):
    mask = np.triu(np.ones_like(df, dtype=bool), k=1)

    if enhance_correlation == "positive":
        cuts = [-1, 0, 1]
        colors = ["white", "white", "darkred"]
    elif enhance_correlation == "null":
        cuts = [-1, -0.3, 0, 0.3, 1]
        colors = ["white", "white", "darkgreen", "white", "white"]
    elif enhance_correlation == "negative":
        cuts = [-1, 0, 1]
        colors = ["darkblue", "white", "white"]
    colorscale = [[(cut_ + 1) / 2, col_] for cut_, col_ in zip(cuts, colors)]

    fig = go.Figure(
        go.Heatmap(
            z=df.mask(mask),
            x=df.columns,
            y=df.columns,
            colorscale=colorscale,
            zmin=-1,
            zmax=1,
        )
    )
    fig.update_traces(hovertemplate="%{y} - %{x}: <b>%{z:.2f}</b><extra></extra>")
    fig.update_layout(
        height=500,
        hoverlabel_font_size=PLT_FONT_SIZE,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    return fig


def plot_returns(
    df: pd.DataFrame, annotation_text: str = "", min_resolution: float = 0.005
) -> go.Figure:
    n_bins = int(np.ceil((abs(df.max() - df.min()).div(min_resolution)).max()))

    fig = px.histogram(df, barmode="overlay", nbins=n_bins)
    fig.update_layout(
        autosize=False,
        height=650,
        margin=dict(l=0, r=0, t=35, b=0),
        legend=dict(title=""),
        yaxis=dict(title="Occurrences", showgrid=False, tickformat=","),
        xaxis=dict(title="Daily returns", tickformat=".1%"),
        hoverlabel_font_size=PLT_FONT_SIZE,
    )
    fig.add_annotation(
        xref="x domain",
        yref="y domain",
        x=0.01,
        y=1.03,
        text=annotation_text,
        font_size=14.5,
        showarrow=False,
        align="left",
    )
    fig.update_traces(
        hovertemplate="%{x} return (%{y} occurr.)",
        hoverinfo="skip",
    )
    return fig


def plot_rolling_returns(df_roll_ret: pd.DataFrame, window: int) -> go.Figure:
    fig = px.area(df_roll_ret.replace(0, np.nan).dropna())
    fig.update_traces(
        hovertemplate="%{x}: <b>%{y:.1%}</b>",
        stackgroup=None,
        fill="tozeroy",
    )
    fig.update_layout(
        autosize=False,
        height=600,
        margin=dict(l=0, r=0, t=25, b=0),
        legend=dict(title=""),
        yaxis=dict(title="Rolling return", showgrid=False, tickformat=".1%"),
        xaxis=dict(title=""),
        hoverlabel_font_size=PLT_FONT_SIZE,
    )
    fig.add_annotation(
        xref="x domain",
        yref="y domain",
        x=0.01,
        y=1.01,
        text=f"<b>{window}-trading-day</b> rolling returns",
        font_size=15,
        showarrow=False,
    )
    return fig


def plot_drawdown(df: pd.DataFrame) -> go.Figure:
    fig = px.area(data_frame=df.dropna())
    fig.update_traces(
        hovertemplate="%{x}: <b>%{y:.1%}</b>",
        stackgroup=None,
        fill="tozeroy",
    )
    fig.update_layout(
        autosize=False,
        height=600,
        margin=dict(l=0, r=0, t=35, b=0),
        legend=dict(title=""),
        yaxis=dict(title="Drawdown", showgrid=False, tickformat=".1%"),
        xaxis=dict(title=""),
        hoverlabel_font_size=PLT_FONT_SIZE,
    )
    return fig


def plot_horizontal_bar(
    df: pd.DataFrame, field_to_plot: str, xaxis_title: str = ""
) -> go.Figure:
    df_plt = df.copy()
    df_plt[df_plt[field_to_plot].lt(0)] = 0
    fig = px.bar(
        x=df_plt[field_to_plot],
        y=[1] * df_plt.shape[0],
        orientation="h",
        color=df_plt.index,
        custom_data=[df_plt.index],
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_traces(
        hovertemplate="<b>%{x:.1%}</b><extra>%{customdata[0]}</extra>",
        marker=dict(line=dict(width=1, color="white")),
    )
    fig.update_layout(
        xaxis=dict(
            title=xaxis_title,
            categoryorder="array",
            categoryarray=df_plt.index,
            tickformat=",.0%",
        ),
        yaxis=dict(title="", showticklabels=False),
        showlegend=False,
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
        hoverlabel_font_size=PLT_FONT_SIZE,
    )
    return fig
