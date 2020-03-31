import pandas as pd, numpy as np, os, sys, re, joblib

try:
    from fbprophet import Prophet
except Exception as exp:
    print(exp)

import data.io_utils as io_utils

def prepare_data(df):
    
    print("Running data prep for model build")
    
    if "Australia" in df.columns:

        confirmed = df[['Date','Australia']]        
        
    else:
        
        confirmed = df[['Date','Confirmed']]
        
    confirmed.columns = ["ds", "y"]
    
    
    confirmed["y"] = np.log(confirmed["y"].astype("float"))
    
    
    confirmed["y"] = confirmed["y"].replace([np.inf, -np.inf], np.nan)#.dropna()
    
    confirmed.dropna(inplace=True)
    
    
    return confirmed


def fit_model(historical_data):
    
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


def get_forecasts(country, horizon=7):
    
    stale = io_utils.check_staleness()
    
    if stale:
        
        build_all_models()
        
        forecast(horizon=horizon)
        
    try:
        
        forecasted_data = read_forecast(country)
        
    except:
        
        #Force rebuild ignoring stale check
        
        try:
            
            print("Force building models, ignored staleness")
            
            build_all_models()
        
            forecast(horizon=horizon)
            
            forecasted_data = read_forecast(country)
            
        except Exception as exc:
            print("Error in getting forecasts", exc)
            
    
    return forecasted_data

def forecast(country_data=None, horizon=7):
    
    if country_data==None:
        
        country_data = io_utils.load_data()
    
    for country in country_data.countries:
        
        try:

            model = load_model(country, country_data.timestamp)
            
        except:
            
            try:
                print("Force rebuilding model for {}".format(country))

                build_model(country)
                
                model = load_model(country, country_data.timestamp)
                
            except Exception as exc:
                
                print("Error in forecasting", exc)
        
        predictions = get_predictions_dataframe(model, horizon=horizon)
        
        write_predictions(predictions, country, country_data.timestamp)
        
def build_model(country):
    
    countries_data = io_utils.load_data()
    
    hist_data = countries_data.historical_country_data
    
    hist_data_c = hist_data.loc[hist_data.index == country]
    
    prep_hist = prepare_data(hist_data_c)
    
    print("building model for " + country)
    
    model = fit_model(prep_hist)
    
    print("Model build successful")
    
    model.stan_backend.logger = None
    
    filename = os.path.join("data", "model_{}_t_{}.joblib".format(country, countries_data.timestamp))
    
    print("Saving model to:", filename)
    
    joblib.dump(model, filename)
    
def load_model(country, timestamp):
    
    fname = os.path.join("data", "model_{}_t_{}.joblib".format(country, timestamp))
    
    print("Loading model from:", fname)
    
    model = joblib.load(fname)
    
    return model

def write_predictions(df, country, timestamp):
    
    fname = os.path.join("data", "predictions_{}_t_{}.csv".format(country, timestamp))
    
    df.to_csv(fname, index=False)
    
    return fname

def read_forecast(country="Australia"):
    
    timestamp = io_utils.get_latest_timestamp()
    
    fname = os.path.join("data", "predictions_{}_t_{}.csv".format(country, timestamp))
    
    return pd.read_csv(fname)


def build_all_models():
    
    io_utils.fetch_data()
    
    data = io_utils.load_data()
    
    try:


        for country in data.countries:

            build_model(country)
            
    except Exception as exc:        
        print(exc)
        
    return