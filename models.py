import itertools

import pandas as pd

import data.constants as constants

_STATUSES_TO_SHOW = [
    "Infected",
    "Dead",
    "Need Hospitalization",
    "Susceptible",
    "Recovered",
    "Total Cases"
]

_DEFAULT_TIME_SCALE = 12 * 3 * 31  # 36 months


def get_predictions(
    cases_estimator,
    sir_model,
    num_diagnosed,
    num_recovered,
    num_deaths,
    area_population,
    max_days
):

    true_cases = cases_estimator.predict(num_diagnosed)
    
    # For now assume removed starts at 0. Doesn't have a huge effect on the model
    predictions = sir_model.predict(
        susceptible=area_population - true_cases - num_recovered - num_deaths,
        infected=true_cases,
        recovered=num_recovered,
        dead=num_deaths,
        num_days=max_days,
    )

    num_entries = max_days + 1
    
    # Have to use the long format to make plotly express happy
    df = pd.DataFrame(
        {
            "Days": list(range(num_entries)) * len(_STATUSES_TO_SHOW),
            "Forecast": list(
                itertools.chain.from_iterable(
                    predictions[status] for status in _STATUSES_TO_SHOW
                )
            ),
            "Status": list(
                itertools.chain.from_iterable(
                    [status] * num_entries for status in _STATUSES_TO_SHOW
                )
            ),
        }
    )
    
    return df


def get_probability_of_infection_give_asymptomatic(
    population, num_infected, asymptomatic_ratio
):
    """
    Get the probability of being infected if you show no symptoms. Use Bayes:
    P(I | A) = P(I) * P(A | I) / (P(A | I)*P(I) + P(A | I')*P(I'))
    :param population: Total population.
    :param num_infected: Number of infections in the population.
    :param asymptomatic_ratio: Proportion of infected people who are asymptomatic. Equivalent to P(A | I).
    """
    p_i = num_infected / population
    
    p = (p_i * asymptomatic_ratio) / (
        asymptomatic_ratio * p_i + 1.0 * (1 - p_i)
    )
    
    return p


def get_status_by_age_group(death_prediction: int, recovered_prediction: int, age_data: pd.DataFrame):
    """
    Get outcomes segmented by age.

    We modify the original percentage death rates from data/age_data.csv to reflect a mortality rate that has been
    adjusted to take into account hospital capacity. The important assumption here is that age groups get infected at
    the same rate; that is, every group is equaly as likely to contract the infection.

    :param death_prediction: Number of deaths predicted.
    :param recovered_prediction: Number of recovered people predicted.
    :return: Outcomes by age in a DataFrame.
    """
    
    #age_data = constants.AgeData.data
    infections_prediction = recovered_prediction + death_prediction

    # Effective mortality rate may be different than the one defined in data/constants.py because once we reach
    # hospital capacity, we increase the death rate. We assume the increase in death rate will be proportional, even
    # though it probably won't be since more old people require medical care, and thus will see increased mortality
    # when the medical system reaches capacity.
    effective_death_rate = death_prediction / infections_prediction
    death_increase_ratio = effective_death_rate / constants.MortalityRate.default

    # Get outcomes by age
    age_data["Infected"] = (age_data.Proportion * infections_prediction).astype(int)
    
    age_data["Need Hospitalization"] = (
        age_data["Hospitalization Rate"] * age_data.Infected
    )
    
    age_data["Dead"] = (
        age_data.Mortality * death_increase_ratio * age_data.Infected
    ).astype(int)
    
    age_data["Recovered"] = (age_data.Infected - age_data.Dead).astype(int)

    return age_data.iloc[:, -4:]


class TrueInfectedCasesModel:
    """
    Used to estimate total number of true infected persons based on either number of diagnosed cases or number of deaths.
    """

    def __init__(self, ascertainment_rate):
        """
        :param ascertainment_rate: Ratio of diagnosed to true number of infected persons.
        """
        self._ascertainment_rate = ascertainment_rate

    def predict(self, diagnosed_cases):
        return diagnosed_cases / self._ascertainment_rate


class SIRModel:
    def __init__(
        self,
        transmission_rate_per_contact,
        contact_rate,
        recovery_rate,
        normal_death_rate,
        critical_death_rate,
        hospitalization_rate,
        hospital_capacity,
    ):
        """
        :param transmission_rate_per_contact: Prob of contact between infected and susceptible leading to infection.
        :param contact_rate: Mean number of daily contacts between an infected individual and susceptible people.
        :param recovery_rate: Rate of recovery of infected individuals.
        :param normal_death_rate: Average death rate in normal conditions.
        :param critical_death_rate: Rate of mortality among severe or critical cases that can't get access
            to necessary medical facilities.
        :param hospitalization_rate: Proportion of illnesses who need are severely ill and need acute medical care.
        :param hospital_capacity: Max capacity of medical system in area.
        """
        self._infection_rate = transmission_rate_per_contact * contact_rate
        self._recovery_rate = recovery_rate
        # Death rate is amortized over the recovery period
        # since the chances of dying per day are mortality rate / number of days with infection
        self._normal_death_rate = normal_death_rate * recovery_rate
        # Death rate of sever cases with no access to medical care.
        self._critical_death_rate = critical_death_rate * recovery_rate
        self._hospitalization_rate = hospitalization_rate
        self._hospital_capacity = hospital_capacity

    def predict(self, susceptible, infected, recovered, dead, num_days):
        """
        Run simulation.
        :param susceptible: Number of susceptible people in population.
        :param infected: Number of infected people in population.
        :param recovered: Number of recovered people in population.
        :param dead: Number of dead people in the population
        :param num_days: Number of days to forecast.
        :return: List of values for S, I, R over time steps
        """
        
        print("Getting SIR model predictions")
        
        population = susceptible + infected + recovered + dead

        S = [int(susceptible)]
        I = [int(infected)]
        R = [int(recovered)]
        D = [int(dead)]
        H = [round(self._hospitalization_rate * infected)]
        T = [int(infected) + int(recovered) + int(dead)]
        
        if int(dead) > 0:
            
            self._normal_death_rate = int(dead) / int(infected)

        for t in range(num_days):

            # There is an additional chance of dying if people are critically ill
            # and have no access to the medical system.
            if I[-1] > 0:
                underserved_critically_ill_proportion = (
                    max(0, H[-1] - self._hospital_capacity) / I[-1]
                )
            else:
                underserved_critically_ill_proportion = 0
            weighted_death_rate = (
                self._normal_death_rate * (1 - underserved_critically_ill_proportion)
                + self._critical_death_rate * underserved_critically_ill_proportion
            )

            # Forecast

            s_t = S[-1] - self._infection_rate * I[-1] * S[-1] / population
            i_t = (
                I[-1]
                + self._infection_rate * I[-1] * S[-1] / population
                - (weighted_death_rate + self._recovery_rate) * I[-1]
            )
            r_t = R[-1] + self._recovery_rate * I[-1]
            d_t = D[-1] + weighted_death_rate * I[-1]

            h_t = self._hospitalization_rate * i_t
            
            t_c = i_t + r_t + d_t

            S.append(round(s_t))
            I.append(round(i_t))
            R.append(round(r_t))
            D.append(round(d_t))
            H.append(round(h_t))
            T.append(round(t_c))

        # Days with no change in I
        days_to_clip = [I[-i] == I[-i - 1] for i in range(1, len(I))]
        index_to_clip = days_to_clip.index(False)
        if index_to_clip == 0:
            index_to_clip = 1

        # Look at at least a few months
        index_to_clip = min(index_to_clip, _DEFAULT_TIME_SCALE - 3 * 31)

        return {
            "Susceptible": S,
            "Infected": I,
            "Recovered": R,
            "Dead": D,
            "Need Hospitalization": H,
            "Total Cases": T
        }
