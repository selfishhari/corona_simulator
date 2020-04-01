import streamlit as st

import warnings

import streamlit as st

import data.io_utils as io_utils
import data.utils as data_utils
import graphing
import models
import utils
from data import constants
from data.utils import check_if_aws_credentials_present, get_uk_death_mirror
from interface import css
from interface.elements import reported_vs_true_cases
from utils import COLOR_MAP, generate_html

try:
    import forecast_utils

except Exception as Inst:

    print("import forecast utils error", Inst)

NOTION_MODELLING_DOC = (
    "https://www.notion.so/coronahack/Modelling-d650e1351bf34ceeb97c82bd24ae04cc"
)
MEDIUM_BLOGPOST = "https://medium.com/@archydeberker/should-i-go-to-brunch-an-interactive-tool-for-covid-19-curve-flattening-6ab6a914af0"


class Sidebar:
    def __init__(self, countries):
        country = st.sidebar.selectbox(
            "What country/state do you live in?",
            options=countries.countries,
            index=countries.default_selection,
        )
        self.country = country

        transmission_probability = constants.TransmissionRatePerContact.default
        country_data = countries.country_data[country]
        date_last_fetched = countries.last_modified

        st.sidebar.markdown(
            body=generate_html(
                text=f"Statistics refreshed as of ",
                line_height=0,
                font_family="Arial",
                font_size="12px",
            ),
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            body=generate_html(text=f"{date_last_fetched}", bold=True, line_height=0),
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            body=generate_html(
                text=f'Population: {int(country_data["Population"]):,}<br>Infected: {int(country_data["Confirmed"]):,}<br>'
                     f'Recovered: {int(country_data["Recovered"]):,}<br>Dead: {int(country_data["Deaths"]):,}',
                line_height=0,
                font_family="Arial",
                font_size="0.9rem",
                tag="p",
            ),
            unsafe_allow_html=True,
        )
        # Horizontal divider line
        st.sidebar.markdown("-------")
        st.sidebar.markdown(
            body=generate_html(
                text=f"Simulate social distancing",
                line_height=0,
                color=COLOR_MAP["pink"],
                bold=True,
                font_size="16px",
            ),
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            body=generate_html(
                text=f"Change the degree of social distancing to see the effect upon disease "
                     f"spread and access to hospital beds.",
                line_height=0,
                font_size="12px",
            )
                 + "<br>",
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            body=generate_html(
                text=f"General degree of social distancing is in the range 10-20 ",
                line_height=0,
                font_size="12px",
            )
                 + "<br>",
            unsafe_allow_html=True,
        )

        self.contact_rate = st.sidebar.slider(
            label="How many people does an infected individual meet on a daily basis?",
            min_value=constants.AverageDailyContacts.min,
            max_value=constants.AverageDailyContacts.max,
            value=constants.AverageDailyContacts.default,
        )

        horizon = {
            "3  months": 90,
            "6 months": 180,
            "12  months": 365,
            "24 months": 730,
        }
        _num_days_for_prediction = st.sidebar.radio(
            label="Time period for prediction",
            options=list(horizon.keys()),
            index=1,
        )

        self.num_days_for_prediction = horizon[_num_days_for_prediction]

        st.sidebar.markdown(
            body=generate_html(
                text=f"We're using an estimated transmission probability of {transmission_probability * 100:.1f}%,"
                     f" see our <a href='https://www.notion.so/coronahack/Modelling-d650e1351bf34ceeb97c82bd24ae04cc'> methods for details</a>.",
                line_height=0,
                font_size="10px",
            ),
            unsafe_allow_html=True,
        )


@st.cache
def _fetch_country_data():
    """
    Check if the data has not been pulled in last 1 hr
    If not then scrape and fetch it.
    Else, just load it
    """

    check_if_aws_credentials_present()

    stale = io_utils.check_staleness()

    if stale:
        forecast_utils.build_all_models()

    return io_utils.load_data()


@st.cache
def _fetch_global_data():
    """
    Check if the data has not been pulled in last 1 hr
    If not then scrape and fetch it.
    Else, just load it
    """

    check_if_aws_credentials_present()

    stale = io_utils.check_staleness()

    if stale:
        forecast_utils.build_all_models()

    return io_utils.load_data(global_flag=True)


def run_app():
    ############################### Data Load ##################################

    css.hide_menu()

    css.limit_plot_size()

    # Get cached country data
    countries = _fetch_country_data()

    global_data = _fetch_global_data()

    if countries.stale:
        st.caching.clear_cache()

        countries = _fetch_country_data()

    if global_data.stale:
        st.caching.clear_cache()

        global_data = _fetch_global_data()

    ################## Heading Section ####################################

    utils.img_html(alt_text='Fractal', href='https://fractal.ai',
                   src='https://i2.wp.com/fractal.ai/wp-content/uploads/2018/02/header-black-logo.png?fit=126%2C43&ssl=1',
                   attributes=dict(width=125, height=43, target='_blank'
                                   ))

    st.markdown(
        body=generate_html(text=f"Australia COVID-19 Simulator", bold=True, tag="h1"),
        unsafe_allow_html=True,
    )
    st.markdown(
        body=generate_html(
            tag="h2",
            text="A tool to help you visualize the impact of social distancing <br>",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        body=generate_html(
            text="<strong>Disclaimer:</strong> <em>The creators of this application are not healthcare professionals. "
                 "The illustrations provided were estimated using best available data but might not accurately reflect reality.</em>",
            color="gray",
            font_size="12px",
        ),
        unsafe_allow_html=True,
    )

    ### Add side bar
    sidebar = Sidebar(countries)

    ###################### historical and forecast chart ##############################

    ### Get selected country
    country = sidebar.country

    country_data = countries.country_data[country]

    _historical_df = countries.historical_country_data

    if country == "Australia":

        historical_data_custom = data_utils.make_historical_data(_historical_df)

        try:

            forecasted_data = forecast_utils.get_forecasts(country, constants.FORECAST_HORIZON)

            historical_plot_df = data_utils.prep_plotting_data(forecasted_data, historical_data_custom)

            # fig = graphing.plot_historical_data(historical_data_plot, con_flag=True)

            fig = graphing.plot_time_series_forecasts(historical_plot_df, country_flag=True, country_name=country)

        except Exception as exc:

            print("Error", exc)

    else:

        historical_data_custom = _historical_df.loc[_historical_df.index == country]

        try:

            forecasted_data = forecast_utils.get_forecasts(country, constants.FORECAST_HORIZON)

            historical_plot_df = data_utils.prep_plotting_data(forecasted_data, historical_data_custom)

            # fig = graphing.plot_historical_data(historical_data_plot)

            fig = graphing.plot_time_series_forecasts(historical_plot_df, country_flag=False, country_name=country)

        except Exception as exc:

            print(exc)

    historical_data = _historical_df.loc[_historical_df.index == country]

    number_cases_confirmed = country_data["Confirmed"]

    population = country_data["Population"]

    num_hospital_beds = country_data["Num Hospital Beds"]

    age_data = constants.AGE_DATA.loc[constants.AGE_DATA["State"] == country, :]

    st.subheader(f"How is the disease likely to spread in {country} in the next week?")

    # Estimate true cases
    true_cases_estimator = models.TrueInfectedCasesModel(
        constants.ReportingRate.default
    )
    # estimated_true_cases = true_cases_estimator.predict(number_cases_confirmed)

    try:

        week1_est = historical_plot_df.tail(1)

        reported_vs_true_cases(int(number_cases_confirmed), week1_est["confirmed"].tolist()[0],
                               graphing.abbreviate(week1_est["lower_bound"].tolist()[0], round_factor=0),
                               graphing.abbreviate(week1_est["upper_bound"].tolist()[0], round_factor=0))

        # Plot historical data
        st.write(fig)

        print("Historical Data with Forecasts plotted")

    except Exception as exc:

        print(exc)

        st.markdown(
            f"Something went wrong :( Forecasts unavailable. Contact admin"
        )

    ###################### SIR Model and Simulator ##############################

    # Predict infection spread
    sir_model = models.SIRModel(
        transmission_rate_per_contact=constants.TransmissionRatePerContact.default,
        contact_rate=sidebar.contact_rate,
        recovery_rate=constants.RecoveryRate.default,
        normal_death_rate=constants.MortalityRate.default,
        critical_death_rate=constants.CriticalDeathRate.default,
        hospitalization_rate=constants.HospitalizationRate.default,
        hospital_capacity=num_hospital_beds,
    )

    df = models.get_predictions(
        cases_estimator=true_cases_estimator,
        sir_model=sir_model,
        num_diagnosed=number_cases_confirmed,
        num_recovered=country_data["Recovered"],
        num_deaths=country_data["Deaths"],
        area_population=population,
        max_days=sidebar.num_days_for_prediction
    )

    st.subheader("How will my actions affect the spread?")

    st.write(
        "**Use the slider in the sidebar to see how this changes the dynamics of disease spread**"
    )

    df_base = df[~df.Status.isin(["Need Hospitalization", "Recovered", "Susceptible"])]

    base_graph = graphing.infection_graph(df_base, df_base.Forecast.max(), population * 0.5, population * 0.75)
    # st.warning(graph_warning)
    st.write(base_graph)

    print("Infections Graph Plotted")

    ###################### Effect on hospitals ##############################

    st.subheader("How will this affect my healthcare system?")

    # Do some rounding to avoid beds sounding too precise!
    approx_num_beds = round(num_hospital_beds / 100) * 100

    st.write(
        f"{country} has around **{approx_num_beds:,}** beds. Bear in mind that most of these "
        "are probably already in use for people sick for other reasons."
    )

    peak_occupancy = df.loc[df.Status == "Need Hospitalization"]["Forecast"].max()

    percent_beds_at_peak = min(100 * num_hospital_beds / peak_occupancy, 100)

    num_beds_comparison_chart = graphing.num_beds_occupancy_comparison_chart(
        num_beds_available=approx_num_beds, max_num_beds_needed=peak_occupancy
    )

    st.write(num_beds_comparison_chart)

    st.markdown(
        f"At peak, **{int(peak_occupancy):,}** people will need hospital beds. At least ** {100 - percent_beds_at_peak:.1f}% ** of "
        f" people who need a bed in hospital might not have access given historical resources of {country}."
    )

    ###################### Death Charts ##############################

    st.subheader("How severe will the impact be?")

    num_dead = df[df.Status == "Dead"].Forecast.iloc[-1]

    num_recovered = df[df.Status == "Recovered"].Forecast.iloc[-1]

    glob_hist = global_data.historical_country_data

    uk_data = glob_hist.loc[(glob_hist.index == "UK") | \
                            (glob_hist.index == "United Kingdom"), :].copy()

    uk_death_mirror = get_uk_death_mirror(uk_data, country_data["Deaths"])

    death_plot = graphing.plot_death_timeseries(df[df.Status == "Dead"], uk_death_mirror, country_name=country)

    st.markdown(
        f"If the average person in {country} adopts the selected behavior, we estimate that **{int(num_dead):,}** "
        f"people will die."
    )

    st.markdown(
        f"This graph illustrates predicted deaths."
    )

    outcomes_by_age_group = models.get_status_by_age_group(num_dead, num_recovered, age_data)

    fig = graphing.age_segregated_mortality(
        outcomes_by_age_group.loc[:, ["Dead"]]
    )

    st.write(death_plot)

    print("Deaths Graph Plotted")

    ###################### Credits ##############################

    st.subheader("References and Credits:")

    st.markdown(
        body=generate_html(
            tag="h4",
            text=f"<u><a href=\"{NOTION_MODELLING_DOC}\" target=\"_blank\" style=color:{COLOR_MAP['pink']};>"
                 "Methodology</a></u> <span> &nbsp;&nbsp;&nbsp;&nbsp</span>"

                 "<hr>",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        body=generate_html(
            tag="h4",
            text=f"<u><a href=\"https://github.com/CSSEGISandData/COVID-19\" target=\"_blank\" style=color:{COLOR_MAP['pink']};>"
                 "2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE</a></u> <span> &nbsp;&nbsp;&nbsp;&nbsp</span>"

                 "<hr>",
        ),
        unsafe_allow_html=True,
    )

    print("complete....")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")

    run_app()
