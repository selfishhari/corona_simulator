import datetime
import glob
import os
import pickle
import re

import data.constants as constants
from data.countries import Countries, Global

TIME_STAMP_FORMAT = '%d-%m-%Y-%H-%M-%S'


def check_staleness():
    timestamp = datetime.datetime.utcnow()

    fnames = glob.glob(os.path.join(constants.PROCESSED_DIR, "country_data_*.pickle"))

    if len(fnames) < 1:
        return True

    latest_ts = get_latest_timestamp(fnames)

    latest_fname = os.path.join(constants.PROCESSED_DIR,
                                "country_data_{}.pickle".format(latest_ts.strftime(TIME_STAMP_FORMAT)))

    latest_ts = datetime.datetime.strptime(re.search("country_data_(.*).pickle$", latest_fname).group(1),
                                           TIME_STAMP_FORMAT)

    delta = timestamp - latest_ts

    return delta.seconds >= constants.STALE_LIMIT


def fetch_data():
    timestamp = datetime.datetime.utcnow()

    country_data = Countries(timestamp=timestamp)

    global_data = Global(timestamp=timestamp)

    filename = os.path.join(constants.PROCESSED_DIR,
                            "country_data_{}.pickle".format(timestamp.strftime(TIME_STAMP_FORMAT)))

    with open(filename, 'wb') as handle:
        pickle.dump(country_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    global_fname = os.path.join(constants.PROCESSED_DIR,
                                "global_data_{}.pickle".format(timestamp.strftime(TIME_STAMP_FORMAT)))

    with open(global_fname, 'wb') as handle:
        pickle.dump(global_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return filename, global_fname


def get_latest_timestamp(fnames=None):
    if fnames == None:
        fnames = glob.glob(os.path.join(constants.PROCESSED_DIR, "country_data_*.pickle"))

    timestamps = []

    for x in fnames:

        try:

            timestamps += [
                datetime.datetime.strptime(re.search("country_data_(.*).pickle$", x).group(1), TIME_STAMP_FORMAT)]

        except Exception as exc:

            print(exc)

    # fname = os.path.join("data", "country_data_{}.pickle".format(str(max(timestamps))))

    return max(timestamps)


def load_data(global_flag=False):
    country_fnames = glob.glob(os.path.join(constants.PROCESSED_DIR, "country_data_*.pickle"))

    timestamp = get_latest_timestamp(country_fnames)

    if global_flag:

        latest_filename = os.path.join(constants.PROCESSED_DIR,
                                       "global_data_{}.pickle".format(str(timestamp.strftime(TIME_STAMP_FORMAT))))

    else:

        latest_filename = os.path.join(constants.PROCESSED_DIR,
                                       "country_data_{}.pickle".format(str(timestamp.strftime(TIME_STAMP_FORMAT))))

    with open(latest_filename, 'rb') as handle:

        data = pickle.load(handle)

    return data
