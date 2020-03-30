import datetime

from data.utils import build_province_data


class Countries:
    def __init__(self, timestamp):
        self.country_data, self.last_modified, self.historical_country_data = (
            build_province_data()
        )
        self.country_data = sorted(self.country_data.items(), key=lambda x:x[1]["Population"], reverse=True)
        
        self.country_data = {k:v for k,v in self.country_data}
        
        self.countries = list(self.country_data.keys())
        self.default_selection = self.countries.index("Australia")
        self.timestamp = timestamp

    @property
    def stale(self):
        delta = datetime.datetime.utcnow() - self.timestamp
        return delta > datetime.timedelta(hours=1)
