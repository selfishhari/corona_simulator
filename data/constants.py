"""
Range estimates for various epidemiology constants. Currently only default values are used.
For sources, please visit https://www.notion.so/Modelling-d650e1351bf34ceeb97c82bd24ae04cc
"""

import os
from pathlib import Path

import pandas as pd

from data.preprocessing import preprocess_bed_data

FORECAST_HORIZON = 7

READABLE_DATESTRING_FORMAT = "%A %d %B %Y, %H:%M %Z"
S3_ACCESS_KEY = os.environ.get("AWSAccessKeyId", "").replace("\r", "")
S3_SECRET_KEY = os.environ.get("AWSSecretKey", "").replace("\r", "")
S3_BUCKET_NAME = "coronavirus-calculator-data"
S3_DISEASE_DATA_OBJ_NAME = "full_and_latest_disease_data_dict_v2"
DISEASE_DATA_GITHUB_REPO = "https://github.com/CSSEGISandData/COVID-19.git"
REPO_DIRPATH = "COVID-19"
DAILY_REPORTS_DIRPATH = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"
DATA_DIR = Path(__file__).parent
DEMOGRAPHICS_DATA_PATH = DATA_DIR / "demographics.csv"
BED_DATA_PATH = DATA_DIR / "world_bank_bed_data.csv"
AGE_DATA_PATH = DATA_DIR / "age_data_states.csv"
DEMOGRAPHIC_DATA = pd.read_csv(DEMOGRAPHICS_DATA_PATH, index_col="Country/Region")
BED_DATA = preprocess_bed_data(BED_DATA_PATH)
AGE_DATA = pd.read_csv(AGE_DATA_PATH, index_col="Age Group")


OZ_STATES = pd.DataFrame([{'Province/State': 'New South Wales', 'Population': 7317500, 'Num Hospital Beds': 28391},
             {'Province/State': 'Victoria', 'Population': 5640900, 'Num Hospital Beds': 20025},
             {'Province/State': 'Queensland', 'Population': 4599400, 'Num Hospital Beds': 17063},
             {'Province/State': 'Western Australia', 'Population': 2366900, 'Num Hospital Beds': 8449},
             {'Province/State': 'South Australia', 'Population': 1659800, 'Num Hospital Beds': 6556},
             {'Province/State': 'Tasmania', 'Population': 511000, 'Num Hospital Beds': 2008},
             {'Province/State': 'Australian Capital Territory', 'Population': 366900, 'Num Hospital Beds': 1441},
             {'Province/State': 'Northern Territory', 'Population': 231200, 'Num Hospital Beds': 908},
             {'Province/State': 'From Diamond Princess', 'Population': 0, 'Num Hospital Beds': 0},
             {'Province/State': 'Australia', 'Population': 24600000, 'Num Hospital Beds': 91683},
             ]).set_index('Province/State')


class AgeData:
    data = AGE_DATA


"""
SIR model constants
"""


class RecoveryRate:
    default = 1 / 10  # Recovery period around 10 days


class MortalityRate:
    # Take weighted average of death rate across age groups. This assumes each age group is equally likely to
    # get infected, which may not be exact, but is an assumption we need to make for further analysis,
    # notably segmenting deaths by age group.
    default = (AgeData.data.Proportion * AgeData.data.Mortality).sum()


class CriticalDeathRate:
    # Death rate of critically ill patients who don't have access to a hospital bed.
    # This is the max reported from Wuhan:
    # https://wwwnc.cdc.gov/eid/article/26/6/20-0233_article
    default = 0.122


class TransmissionRatePerContact:
    # Probability of a contact between carrier and susceptible leading to infection.
    # Found using binomial distribution in Wuhan scenario: 14 contacts per day, 10 infectious days, 2.5 average people infected.
    default = 0.018


class AverageDailyContacts:
    min = 0
    max = 50
    default = 15


class AsymptomaticRate:
    # Proportion of true cases showing no symptoms
    # The number comes from a study led on passengers of the Diamond Princess Cruise, in Japan
    # We assume this figure stands true for the rest of the world
    # https://www.eurosurveillance.org/content/10.2807/1560-7917.ES.2020.25.10.2000180
    default = 0.179


"""
Health care constants
"""


class ReportingRate:
    # Proportion of true cases diagnosed
    default = 0.14


class HospitalizationRate:
    # Cases requiring hospitalization. We multiply by the ascertainment rate because our source got their estimate
    # from the reported cases, whereas we will be using it with total cases.
    default = 0.19 * ReportingRate.default


