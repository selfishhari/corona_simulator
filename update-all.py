import warnings
import data.io_utils as io_utils
from data import constants

try:
    import forecast_utils

except Exception as Inst:

    print("import forecast utils error", Inst)


def update_data():
    """
    Check if the data has not been pulled in last 1 hr
    If not then scrape and fetch it.
    Else, just load it
    """

    stale = io_utils.check_staleness()

    if stale:
        forecast_utils.build_all_models()
    stale = io_utils.check_staleness()

    if stale:
        forecast_utils.build_all_models()

    forecast_utils.forecast(horizon=constants.FORECAST_HORIZON)

if __name__ == "__main__":
    warnings.filterwarnings("ignore")

    update_data()
