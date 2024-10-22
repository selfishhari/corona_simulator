import datetime
import os
import pickle
import shutil
import subprocess
from io import BytesIO
from pathlib import Path
from typing import List

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from data import constants

#import forecast_utils

from data.constants import (
    READABLE_DATESTRING_FORMAT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET_NAME,
    S3_DISEASE_DATA_OBJ_NAME,
    DISEASE_DATA_GITHUB_REPO,
    REPO_DIRPATH,
    DAILY_REPORTS_DIRPATH,
    DEMOGRAPHIC_DATA,
    BED_DATA,
    OZ_STATES
)
from data import scrape_utils

def execute_shell_command(command: List[str]):
    return subprocess.run(command, stdout=subprocess.PIPE).stdout.decode("utf-8")


def get_full_and_latest_dataframes_from_csv(csv_filepaths: List[Path]):
    """
    Returns two dataframes - full table (all dates), table of the latest date
    """
    total_df = None

    for fpath in csv_filepaths:
        stem_split = fpath.stem.split("-")
        month = int(stem_split[0])
        day = int(stem_split[1])
        year = int(stem_split[2])

        curr_df = pd.read_csv(fpath)
        
        if "Country_Region" in curr_df.columns:
            curr_df.rename({"Country_Region": "Country/Region"}, axis=1, inplace=True)
        country_stats_df = curr_df.groupby("Country/Region").agg(
            {"Confirmed": "sum", "Deaths": "sum", "Recovered": "sum"}
        )

        country_stats_df.reset_index(inplace=True)
        country_stats_df["Date"] = datetime.datetime(year=year, month=month, day=day)

        if total_df is None:
            total_df = country_stats_df
        else:
            total_df = total_df.append(country_stats_df, ignore_index=True)

    ## Clean data
    # replacing Mainland china with just China
    total_df["Country/Region"] = total_df["Country/Region"].replace(
        "Mainland China", "China"
    )
    total_df["Country/Region"] = total_df["Country/Region"].replace(
        "US", "United States"
    )

    # sort by date, then country name
    total_df = total_df.sort_values(["Date", "Country/Region"])

    # Latest date table
    latest_date_df = total_df[total_df["Date"] == max(total_df["Date"])]

    # Set country as index
    latest_date_df = latest_date_df.set_index("Country/Region")
    total_df = total_df.set_index("Country/Region")

    return total_df, latest_date_df

def get_full_and_latest_dataframes_from_csv_aus(csv_filepaths: List[Path]):
    """
    Returns two dataframes - full table (all dates), table of the latest date
    """
    
    
    total_df = None

    for fpath in csv_filepaths:
        stem_split = fpath.stem.split("-")
        month = int(stem_split[0])
        day = int(stem_split[1])
        year = int(stem_split[2])

        curr_df = pd.read_csv(fpath)
        
        if "Country_Region" in curr_df.columns:
            curr_df.rename({"Country_Region": "Country/Region",
                           "Province_State":"Province/State",
                           }, axis=1, inplace=True)
            
        curr_df = curr_df.loc[curr_df["Country/Region"].str.lower() == "australia", :]
        
        
        
        province_stats_df = curr_df.groupby("Province/State").agg(
            {"Confirmed": "sum", "Deaths": "sum", "Recovered": "sum"}
        )
        
        agg_df = pd.DataFrame({"Confirmed":[province_stats_df["Confirmed"].sum()],
              "Deaths":[province_stats_df["Deaths"].sum()],
              "Recovered":[province_stats_df["Recovered"].sum()],
              "Province/State":["Australia"]
             
             })
        
        province_stats_df.reset_index(inplace=True)
        
        province_stats_df = pd.concat([province_stats_df, agg_df], axis=0)
        
        province_stats_df["Date"] = datetime.datetime(year=year, month=month, day=day)

        if total_df is None:
            total_df = province_stats_df
        else:
            total_df = total_df.append(province_stats_df, ignore_index=True)

    ## Clean data
    # replacing Mainland china with just China
    province_stats_df["Province/State"] = province_stats_df["Province/State"].replace(
        "Mainland China", "China"
    )
    

    # sort by date, then country name
    total_df = total_df.sort_values(["Date", "Province/State"])

    
    #total_df.rename({"Province/State":"Country/Region"}, axis=1, inplace=True)
    
    #latest_date_df.rename({"Province/State":"Country/Region"}, axis=1, inplace=True)
    try:
        
        total_df = scrape_utils.scrape_and_update(total_df)
        
    except Exception as exc:
        print(exc)
        
    # Set country as index
    total_df = total_df.set_index("Province/State")

    
    # Latest date table
    latest_date_df = total_df[total_df["Date"] == max(total_df["Date"])]
    
    
    return total_df, latest_date_df


def _get_data_from_repo(path, country_flag=False):
    # Go to daily reports directory and fetch all CSV files
    
    
    csv_filepaths = list(Path(path).glob("*.csv"))

    # Get the full and latest table
    if country_flag:
        
        full_df, latest_df = get_full_and_latest_dataframes_from_csv(csv_filepaths)
    else:

        full_df, latest_df = get_full_and_latest_dataframes_from_csv_aus(csv_filepaths)
        
    data_object = {"full_table": full_df, "latest_table": latest_df}

    return data_object

def get_file_age_in_seconds(filename):
    """
    return the file age in whole seconds

    :param filename: the path of the file to valid_password
    :return: number of whole seconds
    """
    return int(os.path.getmtime(filename))


def download_data(cleanup=True, country_flag=False):
    """
     Clone the JHU COVID GitHub repo (takes about a minute) and return paths to CSVs.
    """
    if not os.path.isdir(REPO_DIRPATH):
        cmd = ["git", "clone", DISEASE_DATA_GITHUB_REPO, REPO_DIRPATH]
        execute_shell_command(cmd)

    data_object = _get_data_from_repo(path=DAILY_REPORTS_DIRPATH, country_flag=country_flag)

    if cleanup:
        # Remove GitHub repo directory
        shutil.rmtree(REPO_DIRPATH)
        print("Cleaned up.")

    print("Data fetch complete")

    return data_object


def pull_latest_data(path=REPO_DIRPATH, country_flag=False):

    current_dir = os.path.curdir
    if not os.path.isdir(REPO_DIRPATH):
        download_data(False, country_flag)
    # For some reason when I used subprocess I lost the STDOUT
    git_age = get_file_age_in_seconds(os.path.join(path, '.git'))
    seconds_now = datetime.datetime.now().timestamp()
    if (git_age + 3600) < seconds_now:
        print("Updating the local data storage")
        os.system(f"cd {path} && git pull")

        os.system(f"cd {current_dir}")

    data_object = _get_data_from_repo(path=DAILY_REPORTS_DIRPATH, country_flag=country_flag)

    return data_object


def get_data_locally_or_download(data_path_locally=constants.DATA_DIR, country_flag=False):
    """A helper function for users running locally"""
    if "COVID-19" not in [p.stem for p in data_path_locally.parent.iterdir()]:
        # Don't delete the repo we're cloning if running locally
        
        data_object = download_data(cleanup=False, country_flag=country_flag)
    else:
        # We need to make sure the data is up to date
        
        data_object = pull_latest_data(REPO_DIRPATH, country_flag=country_flag)

    return data_object


def _configure_s3_client():
    # Upload the file
    s3_client = boto3.client(
        "s3", aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY
    )
    return s3_client


def upload_data_to_s3(data: bytes, object_name: str = S3_DISEASE_DATA_OBJ_NAME):
    """
    Upload a file to an S3 bucket
    :param data: Bytes to upload.
    :param object_name: S3 object name.
    :return: True if file was uploaded, else False
    """
    buf = BytesIO(data)
    s3_client = _configure_s3_client()
    try:
        s3_client.put_object(Body=buf, Bucket=S3_BUCKET_NAME, Key=object_name)
    except ClientError as e:
        print(e)
        return False
    return True


def download_data_from_s3(object_name: str = S3_DISEASE_DATA_OBJ_NAME):
    """
    Download a file from S3 bucket.
    :param object_name: Name of object to download.
    :return: Object bytes and date last modified.
    """
    s3_client = _configure_s3_client()
    try:
        download = s3_client.get_object(Key=object_name, Bucket=S3_BUCKET_NAME)
    except ClientError:
        return None
    content = download["Body"].read()

    # e.g. Sunday 30 November 2014
    last_modified = download["LastModified"].strftime(READABLE_DATESTRING_FORMAT)
    return content, last_modified


def build_country_data(demographic_data=DEMOGRAPHIC_DATA, bed_data=BED_DATA):
    # Try to download from S3, else download from JHU
    objects = download_data_from_s3()
    if objects is None:
        data_dict = get_data_locally_or_download(country_flag=True)
        last_modified = datetime.datetime.now().strftime(READABLE_DATESTRING_FORMAT)
    else:
        data_dict_pkl_bytes, last_modified = objects
        data_dict = pickle.loads(data_dict_pkl_bytes)

    full_disease_data, latest_disease_data = (
        data_dict["full_table"],
        data_dict["latest_table"],
    )

    # Rename name "US" to "United States" in demographics data to match bed data
    demographic_data = demographic_data.rename(index={"US": "United States"})
    demographic_data = demographic_data.merge(bed_data, on="Country/Region")
    demographic_data["Num Hospital Beds"] = (
        demographic_data["Latest Bed Estimate"] * demographic_data["Population"]
    )

    country_data = latest_disease_data.merge(demographic_data, on="Country/Region")
    country_data = country_data.loc[
        :, ["Confirmed", "Deaths", "Recovered", "Population", "Num Hospital Beds"]
    ]

    # Check that all of the countries in our selectable dropdown are also present in the full data
    assert set(latest_disease_data.index.unique()).issubset(
        set(full_disease_data.index.unique())
    )

    return country_data.to_dict(orient="index"), last_modified, full_disease_data

def build_province_data(demographic_data=OZ_STATES, bed_data=BED_DATA):
    # Try to download from S3, else download from JHU
    
    #objects = download_data_from_s3()
    objects = None
    
    if objects is None:
        
        data_dict = get_data_locally_or_download(country_flag=False)
        last_modified = datetime.datetime.now().strftime(READABLE_DATESTRING_FORMAT)
    else:
        data_dict_pkl_bytes, last_modified = objects
        data_dict = pickle.loads(data_dict_pkl_bytes)
    

    full_disease_data, latest_disease_data = (
        data_dict["full_table"],
        data_dict["latest_table"],
    )
    
    
    # Rename name "US" to "United States" in demographics data to match bed data
    #demographic_data = demographic_data.rename(index={"US": "United States"})
    #demographic_data = demographic_data.merge(bed_data, on="Country/Region")
    """demographic_data["Num Hospital Beds"] = (
        demographic_data["Latest Bed Estimate"] * demographic_data["Population"]
    )
    """

    country_data = latest_disease_data.merge(demographic_data, on="Province/State")
    
    country_data = country_data.loc[
        :, ["Confirmed", "Deaths", "Recovered", "Population", "Num Hospital Beds"]
    ]

    # Check that all of the countries in our selectable dropdown are also present in the full data
    assert set(latest_disease_data.index.unique()).issubset(
        set(full_disease_data.index.unique())
    )

    return country_data.to_dict(orient="index"), last_modified, full_disease_data
    

def check_if_aws_credentials_present():
    if len(constants.S3_ACCESS_KEY) is 0:
        print(
            "No S3 credentials present, using local file storage. "
            "This make some time the first time you run. We will clone "
            "the John Hopkins data repo (COVID-19) into this one."
        )
    else:
        print("S3 credentials found, using AWS.")
        
        
def make_historical_data(province_data):
    
    con_data = build_country_data()
    
    country_data = con_data[2]
    
    sing_data = country_data.loc[(country_data.index== "Singapore"),["Date", "Confirmed"]].sort_values("Date")
    
    uk_data = country_data.loc[(country_data.index== "United Kingdom") \
                    | (country_data.index== "UK"), ["Date", "Confirmed"]].sort_values("Date")
    
    
    aus_data = province_data.loc[province_data.index.str.lower() == "australia", ["Confirmed", "Date"]].sort_values("Date")
    
    aus_data = aus_data.rename({"Confirmed":"Australia"}, axis="columns")
    
    uk_data = uk_data.rename({"Confirmed":"UK"}, axis="columns")
    
    sing_data = sing_data.rename({"Confirmed":"Singapore"}, axis="columns")
    
    hist_data = aus_data.merge(uk_data, on="Date", how="outer").merge(sing_data, on="Date", how="outer")
    
    #hist_data = hist_data.dropna()
    
    #hist_data["Date"]
    
    return hist_data


def get_closest_death_day(df, curr_death = 17):
    
    df = df.copy()
    
    df["death_diff"] = abs(df["Deaths"] - curr_death)

    closest_day = df.loc[df.death_diff == df.death_diff.min(), "Date"].min()

    return closest_day, df


def get_uk_death_mirror(uk_data, curr_death):
    
    uk_data = uk_data.copy()
    
    uk_data.sort_values("Date", inplace=True)
    
    closest_death_day = get_closest_death_day( uk_data, curr_death)[0]
    
    uk_death_mirror = uk_data.loc[uk_data["Date"] >= closest_death_day, :].copy()

    uk_death_mirror["Days"] = list(range(0, uk_death_mirror.shape[0]))

    return uk_death_mirror[["Days", "Deaths"]]



        
def prep_plotting_data(forecast_df, hist_df):
    
    hist_df["Date"] = pd.to_datetime(hist_df["Date"])
    
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])
    
    plot_df = forecast_df.merge(hist_df, left_on="date", right_on="Date", how="outer")

    plot_df.loc[pd.isnull(plot_df["date"]), "date"] = plot_df.loc[pd.isnull(plot_df["date"]), "Date"]

    plot_df.sort_values("date", inplace=True)
    
    return plot_df
