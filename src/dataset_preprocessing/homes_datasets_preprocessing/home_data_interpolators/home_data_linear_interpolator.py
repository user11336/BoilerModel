import logging

import pandas as pd

import column_names
import time_tick
from preprocess_utils import round_datetime
from .home_data_interpolator import HomeDataInterpolator


class HomeDataLinearInterpolator(HomeDataInterpolator):

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Creating instance of the service")

    def interpolate_boiler_data(self,
                                home_df: pd.DataFrame,
                                start_datetime=None,
                                end_datetime=None,
                                inplace=False) -> pd.DataFrame:
        self._logger.debug("Requested data interpolating")

        time_tick_in_seconds = time_tick.TIME_TICK.total_seconds()

        if not inplace:
            home_df = home_df.copy()

        home_df[column_names.TIMESTAMP] = home_df[column_names.TIMESTAMP].apply(
            lambda datetime_: round_datetime(datetime_, time_tick_in_seconds)
        )
        home_df.drop_duplicates(column_names.TIMESTAMP, inplace=True, ignore_index=True)

        if start_datetime is not None:
            start_datetime = round_datetime(start_datetime, time_tick_in_seconds)
            home_df = self._interpolate_data_start(home_df, start_datetime)
        if end_datetime is not None:
            end_datetime = round_datetime(end_datetime, time_tick_in_seconds)
            home_df = self._interpolate_data_end(home_df, end_datetime)
        home_df.sort_values(by=column_names.TIMESTAMP, ignore_index=True, inplace=True)
        home_df = self._interpolate_passes_of_data(home_df)
        home_df.sort_values(by=column_names.TIMESTAMP, ignore_index=True, inplace=True)

        return home_df

    def _interpolate_passes_of_data(self, home_df: pd.DataFrame):
        self._logger.debug("Interpolating passes of data")

        interpolated_values = []

        previous_datetime = None
        previous_temp = None
        for index, row in home_df.iterrows():

            if previous_datetime is None:
                previous_datetime = row[column_names.TIMESTAMP]
                previous_temp = row[column_names.FORWARD_PIPE_TEMP]
                continue

            next_datetime = row[column_names.TIMESTAMP]
            next_temp = row[column_names.FORWARD_PIPE_TEMP]

            datetime_delta = next_datetime - previous_datetime
            if datetime_delta > time_tick.TIME_TICK:
                number_of_passes = int(datetime_delta // time_tick.TIME_TICK) - 1
                temp_step = (next_temp - previous_temp) / number_of_passes
                for pass_n in range(1, number_of_passes + 1):
                    interpolated_datetime = previous_datetime + (time_tick.TIME_TICK * pass_n)
                    interpolated_temp = previous_temp + (temp_step * pass_n)
                    interpolated_values.append({
                        column_names.TIMESTAMP: interpolated_datetime,
                        column_names.FORWARD_PIPE_TEMP: interpolated_temp,
                    })

            previous_temp = next_temp
            previous_datetime = next_datetime

        home_df = home_df.append(
            interpolated_values,
            ignore_index=True
        )

        return home_df

    def _interpolate_data_start(self, home_df, start_datetime):
        self._logger.debug("Interpolating start of data")

        first_datetime_idx = home_df[column_names.TIMESTAMP].idxmin()
        first_row = home_df.loc[first_datetime_idx]
        first_temp = first_row[column_names.FORWARD_PIPE_TEMP]
        first_datetime = first_row[column_names.TIMESTAMP]
        if first_datetime > start_datetime:
            home_df = home_df.append(
                {
                    column_names.TIMESTAMP: start_datetime,
                    column_names.FORWARD_PIPE_TEMP: first_temp
                },
                ignore_index=True
            )
        return home_df

    def _interpolate_data_end(self, home_df, end_datetime):
        self._logger.debug("Interpolating end of data")

        last_datetime_idx = home_df[column_names.TIMESTAMP].idxmax()
        last_row = home_df.loc[last_datetime_idx]
        last_temp = last_row[column_names.FORWARD_PIPE_TEMP]
        last_datetime = last_row[column_names.TIMESTAMP]
        if last_datetime < end_datetime:
            home_df = home_df.append(
                {
                    column_names.TIMESTAMP: end_datetime,
                    column_names.FORWARD_PIPE_TEMP: last_temp
                },
                ignore_index=True
            )
        return home_df