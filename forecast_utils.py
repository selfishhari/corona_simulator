import joblib
import numpy as np
import os
import pandas as pd

try:
    from fbprophet import Prophet
except Exception as exp:
    print(exp)

import data.io_utils as io_utils
import data.constants as constants

TIME_STAMP_FORMAT = '%d-%m-%Y-%H-%M-%S'


def prepare_data(df, log_flag=True):
    print("Running data prep for model build- Log transform?:", log_flag)

    if "Australia" in df.columns:

        confirmed = df[['Date', 'Australia']]

    else:

        confirmed = df[['Date', 'Confirmed']]

    confirmed.columns = ["ds", "y"]

    if log_flag:
        confirmed["y"] = np.log(confirmed["y"].astype("float"))

        confirmed["y"] = confirmed["y"].replace([np.inf, -np.inf], np.nan)  # .dropna()

    confirmed.dropna(inplace=True)

    return confirmed


def fit_model(historical_data):
    m = Prophet(interval_width=0.95, daily_seasonality=True)

    m.fit(historical_data)

    return m


def get_predictions_dataframe(model, horizon=7, log_flag=True):
    print("creating forecasts..")

    future = model.make_future_dataframe(periods=7)

    future_confirmed = future.copy()  # for non-baseline predictions later on

    preds = model.predict(future.tail(horizon))[["yhat", "yhat_lower", "yhat_upper"]]

    if log_flag:

        for x in preds.columns:

            if (x == "ds") | (x == "actual"):
                continue

            preds[x] = np.round(np.exp(preds[x]))
    else:

        for x in preds.columns:

            if (x == "ds") | (x == "actual"):
                continue

            preds[x] = np.round(preds[x])

    preds["date"] = future["ds"].tail(horizon).tolist()

    preds.columns = ["confirmed", "lower_bound", "upper_bound", "date"]

    history_df = model.history[["ds", "y"]]

    if log_flag:
        history_df["y"] = np.round(np.exp(history_df["y"]))

    history_df.columns = ["date", "confirmed"]

    history_df["lower_bound"] = history_df["confirmed"]

    history_df["upper_bound"] = history_df["confirmed"]

    df = pd.concat([history_df, preds], axis=0)

    # preds.loc[:55, "lower_bound"] = np.nan

    # preds.loc[:55, "upper_bound"] = np.nan

    return df


def get_ensembled_forecast(log_df, linear_df):
    print("averaging predictions from log and linear models")

    linear_df_sub = linear_df.loc[linear_df["date"].isin(log_df["date"].tolist()), :].reset_index(drop=True).copy()

    log_df = log_df.reset_index(drop=True).copy()

    averaged_result = linear_df_sub.copy()

    for x in averaged_result.columns:

        if (x == "date") | (x == "actual"):
            continue

        averaged_result[x] = ((averaged_result[x] + log_df[x]) / 2).astype(int)

    return averaged_result


def get_forecasts(country, horizon=7):
    stale = io_utils.check_staleness()

    if stale:
        build_all_models()

        forecast(horizon=horizon)

    try:

        forecasted_data = read_forecast(country)

    except:

        # Force rebuild ignoring stale check

        try:

            print("Force building models, ignored staleness")

            build_all_models()

            forecast(horizon=horizon)

            forecasted_data = read_forecast(country)

        except Exception as exc:
            print("Error in getting forecasts", exc)

    return forecasted_data


def forecast(country_data=None, horizon=7):
    if country_data == None:
        country_data = io_utils.load_data()

    for country in country_data.countries:

        try:

            model_log = load_model(country, country_data.timestamp, log_flag=True)

            model_linear = load_model(country, country_data.timestamp, log_flag=False)

        except:

            try:
                # if any model is not present/unreadable force rebuild with the same time stamp
                print("Force rebuilding model for {}".format(country))

                build_model(country, log_flag=True)

                build_model(country, log_flag=False)

                model_log = load_model(country, country_data.timestamp, log_flag=True)

                model_linear = load_model(country, country_data.timestamp, log_flag=False)

            except Exception as exc:

                print("Error in forecasting", exc)

        predictions_log = get_predictions_dataframe(model_log, horizon=horizon, log_flag=True)

        predictions_linear = get_predictions_dataframe(model_linear, horizon=horizon, log_flag=False)

        predictions = get_ensembled_forecast(predictions_log, predictions_linear)

        write_predictions(predictions, country, country_data.timestamp, logname=None)

        write_predictions(predictions_log, country, country_data.timestamp, logname="log")

        write_predictions(predictions_linear, country, country_data.timestamp, logname="linear")


def build_model(country, log_flag=True):
    countries_data = io_utils.load_data()

    hist_data = countries_data.historical_country_data

    hist_data_c = hist_data.loc[hist_data.index == country]

    prep_hist = prepare_data(hist_data_c, log_flag)

    print("building model for " + country)

    model = fit_model(prep_hist)

    print("Model build successful")

    model.stan_backend.logger = None

    if log_flag:

        logname = "log"

    else:

        logname = "linear"

    filename = os.path.join(constants.MODELS_DIR,
                            "model_{}_{}_t_{}.joblib".format(logname,
                                                             country,
                                                             countries_data.timestamp.strftime(TIME_STAMP_FORMAT)))

    print("Saving model to:", filename)

    joblib.dump(model, filename)


def load_model(country, timestamp, log_flag=True):
    if log_flag:

        logname = "log"

    else:

        logname = "linear"

    fname = os.path.join(constants.MODELS_DIR, "model_{}_{}_t_{}.joblib".format(logname,
                                                                                country,
                                                                                timestamp.strftime(TIME_STAMP_FORMAT)))

    print("Loading model from:", fname)

    model = joblib.load(fname)

    return model


def write_predictions(df, country, timestamp, logname=None):
    if logname == None:

        fname = os.path.join(constants.OUTPUTS_DIR,
                             "predictions_{}_t_{}.csv".format(country, timestamp.strftime(TIME_STAMP_FORMAT)))
    else:

        fname = os.path.join(constants.OUTPUTS_DIR,
                             "predictions_{}_{}_t_{}.csv".format(logname,
                                                                 country, timestamp.strftime(TIME_STAMP_FORMAT)))

    df.to_csv(fname, index=False)

    return fname


def read_forecast(country="Australia"):
    timestamp = io_utils.get_latest_timestamp()

    fname = os.path.join(constants.OUTPUTS_DIR,
                         "predictions_{}_t_{}.csv".format(country, timestamp.strftime(TIME_STAMP_FORMAT)))

    return pd.read_csv(fname)


def build_all_models():
    io_utils.fetch_data()

    data = io_utils.load_data()

    try:

        for country in data.countries:
            build_model(country, log_flag=False)

            build_model(country, log_flag=True)

    except Exception as exc:
        print(exc)

    return
