import datetime
import json
import os

from keras import Sequential
from keras.layers import (Dense, LSTM)

from config import (
    PREPROCESSED_BOILER_DATASET_PATH,
    PREPROCESSED_HOMES_DATASETS_DIR,
    HOMES_DELTAS_PATH,
    PREPROCESSED_DATASET_FILENAME_SUFFIX,
    MODELS_DIR
)
from utils.dataset_utils import create_sequences_smooth_delta
from utils.io_utils import load_dataset, get_model_save_name
from utils.metrics import relative_error
from utils.preprocess_utils import filter_by_timestamp


# noinspection PyShadowingNames
from utils.train_utils import train_model


# noinspection PyShadowingNames
def get_model(window_size):
    model = Sequential()
    model.add(LSTM(60, return_sequences=True, activation="relu", input_shape=(1, window_size)))
    model.add(LSTM(20, activation="relu"))
    model.add(Dense(1, activation='linear'))
    model.compile(
        optimizer='adam',
        loss='mean_squared_error',
        metrics=['mae', relative_error]
    )
    return model


if __name__ == '__main__':
    window_size = 5
    smooth_size = 2
    epoch_count = 200
    batch_size = 200000
    parent_model_name = "multi_lstm"

    min_date = datetime.datetime(2018, 12, 1, 0, 0, 0)
    max_date = datetime.datetime(2019, 4, 1, 0, 0, 0)

    val_min_date = datetime.datetime(2019, 4, 1, 0, 0, 0)
    val_max_date = datetime.datetime(2019, 5, 1, 0, 0, 0)

    parent_model_name = get_model_save_name(parent_model_name)

    boiler_df = load_dataset(PREPROCESSED_BOILER_DATASET_PATH, min_date, max_date)
    boiler_t = boiler_df["t1"].to_numpy()

    val_boiler_df = filter_by_timestamp(boiler_df, val_min_date, val_max_date)
    val_boiler_t = val_boiler_df["t1"].to_numpy()

    with open(HOMES_DELTAS_PATH) as f:
        homes_deltas = json.load(f)

    for dataset_filename in os.listdir(PREPROCESSED_HOMES_DATASETS_DIR):
        model_name = dataset_filename[:-(len(PREPROCESSED_DATASET_FILENAME_SUFFIX))]
        print("Training model: {}".format(model_name))

        delta = homes_deltas[model_name]

        dataset_path = f"{PREPROCESSED_HOMES_DATASETS_DIR}\\{dataset_filename}"

        home_df = load_dataset(dataset_path, min_date, max_date)
        t_in_home = home_df["t1"].to_numpy()
        x_seq, y_seq = create_sequences_smooth_delta(boiler_t, t_in_home, window_size, delta, smooth_size)

        val_home_df = filter_by_timestamp(home_df, val_min_date, val_max_date)
        val_t_in_home = val_home_df["t1"].to_numpy()
        val_x_seq, val_y_seq = create_sequences_smooth_delta(boiler_t, t_in_home, window_size, delta, smooth_size)

        model = get_model(window_size)
        train_model(
            model,
            x_seq,
            y_seq,
            val_x_seq,
            val_y_seq,
            epoch_count,
            batch_size,
            model_name,
            models_dir=f"{MODELS_DIR}\\{parent_model_name}",
            verbose_mode=0
        )
