import pandas as pd, numpy as np

from fbprophet import Prophet

def prepare_data(df):
    
    if "Australia" in df.columns:

        confirmed = df[['Date','Australia']]        
        
    else:
        
        confirmed = df[['Date','Confirmed']]
        
    confirmed.columns = ["ds", "y"]
    
    print("trying to log transform")

    confirmed["y"] = np.log(confirmed["y"].astype("float"))
    
    print("log transform done")

    confirmed["y"] = confirmed["y"].replace([np.inf, -np.inf], np.nan).dropna()
    
    print("trying to replace infs done")

    return confirmed


def build_model(historical_data):
    
    m = Prophet(interval_width=0.95, daily_seasonality=True)

    m.fit(historical_data)

    return m

def get_predictions_dataframe(model, horizon=7):
    
    future = model.make_future_dataframe(periods=7)

    future_confirmed = future.copy() # for non-baseline predictions later on

    preds = model.predict(future.tail(horizon))[["yhat", "yhat_lower", "yhat_upper"]]
    
    for x in preds.columns:
        
        preds[x] = np.round(np.exp(preds[x]))

    preds["date"] = future["ds"].tail(horizon).tolist()

    preds.columns = ["confirmed", "lower_bound", "upper_bound", "date"]
    
    history_df = model.history[["ds", "y"]]
    
    history_df["y"] = np.round(np.exp(history_df["y"]))
    
    history_df.columns = ["date", "confirmed"]
    
    history_df["lower_bound"] = history_df["confirmed"]
    
    history_df["upper_bound"] = history_df["confirmed"]
    
    df = pd.concat([history_df, preds], axis=0)

    #preds.loc[:55, "lower_bound"] = np.nan

    #preds.loc[:55, "upper_bound"] = np.nan

    return df


def get_forecasts(historical_data, horizon=7):
    
    prep_hist = prepare_data(historical_data)
    
    print("Data prep done", prep_hist)
    
    model = build_model(prep_hist)
    
    forecast_df = get_predictions_dataframe(model, horizon=horizon)
    
    return forecast_df

def prep_plotting_data(forecast_df, hist_df):
    
    plot_df = forecast_df.merge(hist_df, left_on="date", right_on="Date", how="outer")

    plot_df.loc[pd.isnull(plot_df["date"]), "date"] = plot_df.loc[pd.isnull(plot_df["date"]), "Date"]

    plot_df.sort_values("date", inplace=True)
    
    return plot_df

