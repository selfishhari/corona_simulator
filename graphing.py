import pandas as pd, numpy as np
import plotly
import plotly.express as px
import plotly.graph_objects as go
from  data import constants
from datetime import datetime
from utils import COLOR_MAP
import plotly.express as px

TEMPLATE = "plotly_white"


def _set_legends(fig):
    fig.layout.update(legend=dict(x=-0.1, y=1.2))
    fig.layout.update(legend_orientation="h")


def plot_historical_data(df, con_flag=False):
    # Convert wide to long
    
    if con_flag:
        
        df = pd.melt(
            df,
            id_vars="Date",
            value_vars=["Australia", "UK", "Singapore"],
            var_name="Status",
            value_name="Number",
        )


        
    else:
        
        df = pd.melt(
            df,
            id_vars="Date",
            value_vars=["Confirmed", "Deaths", "Recovered"],
            var_name="Status",
            value_name="Number",
        )
    

    fig = px.scatter(
        df, x="Date", y="Number", color="Status", template=TEMPLATE, opacity=0.8
    )

    _set_legends(fig)

    return fig


def plot_true_versus_confirmed(confirmed, predicted):
    df = pd.DataFrame(
        {
            "Status": ["Confirmed", "Predicted"],
            "Cases": [confirmed, predicted],
            "Color": ["b", "r"],
        }
    )
    fig = px.bar(df, x="Status", y="Cases", color="Color", template=TEMPLATE)
    fig.layout.update(showlegend=False)

    return fig


def infection_graph(df, y_max, pop_50, pop_75):
    
    # We cannot explicitly set graph width here, have to do it as injected css: see interface.css
    fig = go.Figure(layout=dict(template=TEMPLATE))

    total, infected, dead = (
        df.loc[df.Status == "Total Cases"],
        df.loc[df.Status == "Infected"],
        df.loc[df.Status == "Recovered"],
    )
    
    total["pop_50"] = abs(total["Forecast"] - pop_50)
    
    total["pop_75"] = abs(total["Forecast"] - pop_75)
    
    pop_50_day = total.loc[total["pop_50"] == total["pop_50"].min(), "Days"].tolist()
    
    pop_75_day = total.loc[total["pop_75"] == total["pop_75"].min(), "Days"].tolist()
    
    annotations = [
            dict(
                x=pop_50_day[0],
                y=pop_50,
                xref='x',
                yref='y',
                text= "<span style='font-size:12px;color:#fea13d;'> 50% Population infected in<br><span style='font-weight:bold;color:#fea13d;'>" + str(pop_50_day[0]) + "</span> days</span>",
                showarrow=True,
                arrowhead=7,
                ax=-60,
                ay=-30
            )
            ]
    
    annotations += [
            dict(
                x=pop_75_day[0],
                y=pop_75,
                xref='x',
                yref='y',
                text= "<span style='font-size:12px;color:#fea13d;'> 75% Population infected in<br><span style='font-weight:bold;color:#fea13d;'>" + str(pop_75_day[0]) + "</span> days</span>",
                showarrow=True,
                arrowhead=7,
                ax=-60,
                ay=-30
            )
            ]
    
    
    fig.add_scatter(
        x=total.Days,
        y=total.Forecast,
        fillcolor=COLOR_MAP["susceptible"],
        fill="tozeroy",
        mode="lines",
        line=dict(width=0),
        name="Total Infected",
        opacity=0.5,
    )

    fig.add_scatter(
        x=dead.Days,
        y=dead.Forecast,
        fillcolor=COLOR_MAP["recovered"],
        fill="tozeroy",
        mode="lines",
        line=dict(width=0),
        name="Deaths",
        opacity=0.5,
    )

    fig.add_scatter(
        x=infected.Days,
        y=infected.Forecast,
        fillcolor="#FFA000",
        fill="tozeroy",
        mode="lines",
        line=dict(width=0),
        name="Active Infections",
        opacity=0.5,
    )
    
    
    ## Adding a horiz line at 50% and 75% of population
    fig.add_trace(go.Scatter(x = pop_50_day + pop_50_day, 
                             y = [0, pop_50], 
                             line=dict(color='#e33734', width=1, dash='dot'), 
                             hoverinfo = "text",
                             text = [ "50% population infected in {} days".format(pop_50_day[0]),
                                     "50% population infected in {} days".format(pop_50_day[0])],
                             showlegend= False
                             )
                 )
    
    fig.add_trace(go.Scatter(x = pop_75_day + pop_75_day, 
                             y = [0, pop_75],  
                             line=dict(color='#e33734', width=1, dash='dot'), 
                             hoverinfo = "text",
                             text = [ "75% population infected in {} days".format(pop_75_day[0]),
                                     "75% population infected in {} days".format(pop_75_day[0])],
                             showlegend= False
                             )
                 )
    
    
    fig.update_yaxes(range=[0, y_max])
    
    fig.layout.update(xaxis_title="Days", annotations=annotations)
    
    _set_legends(fig)
    
    return fig


def age_segregated_mortality(df):
    
    df = df.rename(index={ag: "0-30" for ag in ["0-9", "10-19", "20-29"]}).reset_index()
    
    df = pd.melt(df, id_vars="Age Group", var_name="Status", value_name="Forecast")
    
    # Add up values for < 30
    
    df = (
        df.groupby(["Age Group", "Status"])
        .sum()
        .reset_index(1)
        .sort_values(by="Status", ascending=False)
    )

    df['Status'] = df['Status'].apply(lambda x: {'Need Hospitalization': 'Hospitalized'}.get(x, x))


    fig = px.bar(
        df,
        x=df.index,
        y="Forecast",
        color="Status",
        template=TEMPLATE,
        opacity=0.7,
        color_discrete_sequence=["red"],
        barmode="group",
    )
    fig.layout.update(
        xaxis_title="",
        yaxis_title="",
        font=dict(family="Arial", size=15, color=COLOR_MAP["default"]),
    )
    _set_legends(fig)
    return fig


def num_beds_occupancy_comparison_chart(num_beds_available, max_num_beds_needed):
    """
    A horizontal bar chart comparing # of beds available compared to 
    max number number of beds needed
    """
    num_beds_available, max_num_beds_needed = (
        int(num_beds_available),
        int(max_num_beds_needed),
    )

    df = pd.DataFrame(
        {
            "Label": ["Total Beds ", "Peak Occupancy "],
            "Value": [num_beds_available, max_num_beds_needed],
            "Text": [f"{num_beds_available:,}  ", f"{max_num_beds_needed:,}  "],
            "Color": ["b", "r"],
        }
    )
    fig = px.bar(
        df,
        x="Value",
        y="Label",
        color="Color",
        text="Text",
        orientation="h",
        opacity=0.7,
        template=TEMPLATE,
        height=300,
    )

    fig.layout.update(
        showlegend=False,
        xaxis_title="",
        xaxis_showticklabels=False,
        yaxis_title="",
        yaxis_showticklabels=True,
        font=dict(family="Arial", size=15, color=COLOR_MAP["default"]),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)

    return fig


def plot_time_series_forecasts(df, country_flag=False, country_name="Australia"):
    
    forecast_start_date = df.tail(constants.FORECAST_HORIZON)["date"].tolist()[0]
    
    actual_end_date = df.tail(constants.FORECAST_HORIZON + 1)["date"].tolist()[0]
    
    observed_dp = df.shape[0] - constants.FORECAST_HORIZON
    
    obs_text = ["" for x in range(0,observed_dp)]
    
    upper_text = ["upper: "+ abbreviate(x) for x in df.tail(constants.FORECAST_HORIZON)["upper_bound"].tolist()]
    
    lower_text = ["lower: "+ abbreviate(x) for x in df.tail(constants.FORECAST_HORIZON)["lower_bound"].tolist()]
    
    upper_bound = go.Scatter(
                #name='Aus-upper',
                x=df['date'],
                y=df['upper_bound'],
                mode='lines',
                marker=dict(color="#444"),
                line=dict(width=0),
                fillcolor='rgba(68, 68, 68, 0.3)',
                fill='tonexty',
                hoverinfo="text",
                text = obs_text + upper_text,
                showlegend= False
    )

    trace = go.Scatter(
            name= country_name,
            x=df['date'],
            y=df['confirmed'],
            mode='lines+markers',
            line=dict(color='rgb(31, 119, 180)'),
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty')

    lower_bound = go.Scatter(
                name='lower',
                x=df['date'],
                y=df['lower_bound'],
                marker=dict(color="#444"),
                line=dict(width=0),
                mode='lines',
                text = obs_text + lower_text,
                hoverinfo = "text",
                showlegend= False
                )
    
    if country_flag:        

        trace2 = go.Scatter(
                name='UK',
                x=df['date'],
                y=df['UK'],
                mode='lines',
                line=dict(color='#fe346e'),
                )

        trace3 = go.Scatter(
                name='Singapore(Confirmed)',
                x=df['date'],
                y=df['Singapore'],
                mode='lines',
                line=dict(color='#00bdaa'),
                )
    else:
        
        trace2 = go.Scatter(
                name='Recovered',
                x=df['date'],
                y=df['Recovered'],
                mode='lines',
                line=dict(color='#00bdaa'),
            )

        trace3 = go.Scatter(
                name='Dead',
                x=df['date'],
                y=df['Deaths'],
                mode='lines',
                line=dict(color='#fe346e'),
                )
        

    # Trace order can be important
    # with continuous error bars
    if country_flag:
        data = [lower_bound, trace, upper_bound, trace2]
    else:
        data = [lower_bound, trace, upper_bound]
        
    annotations = []
    
    df.reset_index(drop=True, inplace=True)
    
    """
    for rownum, row in df.iterrows():
        
        if (rownum%8 == 7) | (rownum==df.shape[0]):
            
            print(rownum)
            
            if rownum == 0:
                continue;

            annotations += [
            dict(
                x=row["date"],
                y=row["confirmed"],
                xref='x',
                yref='y',
                text=abbreviate(int(row["confirmed"])),
                showarrow=True,
                arrowhead=3,
                ax=0,
                ay=-30
            )
            ]
    """
        
        
    actual_end_date_frmt = actual_end_date.strftime("%b %d")
    
    annotations += [
            dict(
                x=forecast_start_date,
                y=df.tail(constants.FORECAST_HORIZON)["confirmed"].tolist()[0],
                xref='x',
                yref='y',
                text= "<span style='color:#2178b6;'>" + country_name + "</span>" + "<br>" + forecast_start_date.strftime("%b %d") +": " + ": <span style='color:red;'>" + \
                abbreviate(int(df.tail(constants.FORECAST_HORIZON)["confirmed"].tolist()[0])) + "</span>",
                showarrow=True,
                arrowhead=3,
                ax=-100,
                ay=0
            )
            ]
    
    annotations += [
            dict(
                x=df.tail(1)["date"].tolist()[0],
                y=df.tail(1)["confirmed"].tolist()[0],
                xref='x',
                yref='y',
                text= "<span style='color:#2178b6;'>" + country_name + "</span>" + "<br>" + df.tail(1)["date"].tolist()[0].strftime("%b %d") +": " + ": <span style='color:red;'>" + \
                abbreviate(int(df.tail(1)["confirmed"].tolist()[0])) + "</span>",
                showarrow=True,
                arrowhead=3,
                ax=-120,
                ay=0
            )
            ]
    
    if country_flag:
        """
        annotations += [
                dict(
                    x=actual_end_date,
                    y=df.tail(constants.FORECAST_HORIZON + 1)["UK"].tolist()[0],
                    xref='x',
                    yref='y',
                    text= "<span style='color:#f34f78;'>UK</span><br>" + actual_end_date_frmt +": <span style='color:red;'>" + \
                    abbreviate(int(df.tail(constants.FORECAST_HORIZON + 1)["UK"].tolist()[0])) + "</span>",
                    showarrow=True,
                    arrowhead=3,
                    ax=0,
                    ay=-50
                )
            ]
         """
    
    
    layout = go.Layout(
        yaxis=dict(title='Case Counts(Cumulative)'),
        title='Historical Trend of Cases with Forecasts<br>(Select to zoom)',
        annotations=annotations,
        showlegend = True
        )
    
    

    fig = go.Figure(data=data, layout=layout)
    
    fig.add_trace(go.Scatter(x=[str(forecast_start_date), str(forecast_start_date)], 
                             y=[-100, df.tail(1)["upper_bound"].tolist()[0]+2000], 
                             line=dict(color='royalblue', width=1, dash='dot'), 
                             hoverinfo = "text",
                             text = ["", "Forecasting From: "+ str(forecast_start_date).replace(" 00:00:00","")],
                             showlegend= False
                             )
                 )

    return fig

def plot_death_timeseries(df):
    
    #fig = px.line(df, x='Date', y='Dead')
    
    df.reset_index(drop=True, inplace=True)
    
    data = go.Scatter(x=df['Days'], y=df['Forecast'], name="Total Deaths", 
                   mode="lines+markers", line=dict(color="#e33734")
                  )
    
    annotations = []
    
    total_rows = df.shape[0]
    
    factor = total_rows//6
    
    for rownum, row in df.iterrows():
        
        if rownum % factor == 0:
        
            annotations += [
                    dict(
                        x=row["Days"],
                        y=row["Forecast"],
                        xref='x',
                        yref='y',
                        text= "<span style='color:red;'>Day: {} </span>".format(row["Days"])  + "<br><span style='color:red;'>" + \
                        abbreviate(int(row["Forecast"])) + "</span>",
                        showarrow=True,
                        arrowhead=3,
                        ax=0,
                        ay=-50
                    )
                ]
            
    fig = go.Figure(data = [data])
    
    fig.layout.update(annotations=annotations, showlegend=True)
    
    
    return fig


def abbreviate(x, round_factor=2):
    abbreviations = ["", "k", "M", "B", "T", "Qd", "Qn", "Sx", "Sp", "O", "N", 
    "De", "Ud", "DD"]
    thing = "1"
    a = 0
    while len(thing) < len(str(int(x))) - 3:
        
        thing += "000"
        
        a += 1
    
    b = int(thing)
    
    thing = (round(x / b, round_factor))
    
    return str(thing) + abbreviations[a]
    