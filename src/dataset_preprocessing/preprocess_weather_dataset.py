
import os
import logging

import config
from weather_dataset_utils.weather_data_interpolators.weather_data_linear_interpolator import \
    WeatherDataLinearInterpolator
from weather_dataset_utils.weather_data_parsers.soft_m_json_weather_data_parser import \
    SoftMJSONWeatherDataParser


def preprocess_weather_dataset():
    parser = SoftMJSONWeatherDataParser()
    parser.set_weather_data_timezone_name(config.WEATHER_DATA_TIMEZONE)
    with open(os.path.abspath(config.WEATHER_SRC_DATASET_PATH), "r") as f:
        weather_df = parser.parse_weather_data(f)

    interpolator = WeatherDataLinearInterpolator()
    interpolator.interpolate_weather_data(weather_df, config.START_DATETIME, config.END_DATETIME, inplace=True)

    weather_df.to_pickle(config.WEATHER_PREPROCESSED_DATASET_PATH)


if __name__ == '__main__':
    logging.basicConfig(level="DEBUG")
    preprocess_weather_dataset()