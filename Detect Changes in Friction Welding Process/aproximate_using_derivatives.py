import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelmax
import os
from scipy.ndimage import gaussian_filter1d


class ProcessValue:
    def __init__(self, data_series):
        # plt.title(data_series.name)
        self.max_idt = None
        self.first_derivative = None
        self.second_derivative = None
        self.data = pd.DataFrame()
        self.data["data_series"] = data_series
        self.series_name = data_series.name
        self.configure_derivatives()

    def configure_derivatives(
            self,
            a_clip=250, b_clip=500,
            c_clip=0, d_clip=500,
            sigma_1=2, sigma_2=2,
            abs_1=True,
            abs_2=False):

        if abs_1:
            self.first_derivative = gaussian_filter1d(
                np.clip(np.abs(np.gradient(self.data["data_series"])), a_clip, b_clip), sigma_1)
        else:
            self.first_derivative = gaussian_filter1d(
                np.clip(np.gradient(self.data["data_series"]), a_clip, b_clip), sigma_1)

        if abs_2:
            self.second_derivative = gaussian_filter1d(
                np.clip(np.abs(np.gradient(self.first_derivative)), c_clip, d_clip), sigma_2)
        else:
            self.second_derivative = gaussian_filter1d(
                np.clip(np.gradient(self.first_derivative), c_clip, d_clip), sigma_2)

        self.data["first_derivative"] = self.first_derivative
        self.data["second_derivative"] = self.second_derivative
        self.max_idt = self.data["data_series"].iloc[argrelmax(self.second_derivative)[0]].index.values.astype(int)

    def configure_plot(self, nrows):
        self.fig, self.axes = plt.subplots(nrows=nrows, ncols=1)

    def plot_1st_derivative(self, row):
        self.data["first_derivative"].plot(ax=self.axes[row])
        self.axes[row].set_title("First derivative")
        self.axes[row].set_xlabel("")

    def plot_2nd_derivative(self, row):
        self.data["second_derivative"].plot(ax=self.axes[row])
        self.axes[row].set_title("Second derivative")
        self.axes[row].set_xlabel("")

    def plot_peaks(self, row):
        plot_value = self.data["data_series"].plot(ax=self.axes[row])
        for line in self.max_idt:
            plot_value.axvline(line, color="red")
        self.axes[row].set_title(f"{self.series_name} Peaks")

    def plot_vanilla(self, row):
        self.data["data_series"].plot(ax=self.axes[row])

    def plot_all(self):
        self.configure_plot(3)
        self.plot_1st_derivative(0)
        self.plot_2nd_derivative(1)
        self.plot_peaks(2)


# Variables and shit
aprox_speed_steps = [
    "speed_starts_spinning",
    "speed_stabilizes",
    "speed_slowing_down",
    "speed_stops"
]

aprox_force_steps = [
    "force_first_rising",
    "force_second_rising",
    "force_falling",
]

aprox_position_steps = [
    "position_ascending",
    "position_first_bump",
    "position_stabilizes",
    "position_descending"
]

final_df = pd.DataFrame()

# Configures pandas' options
pd.set_option('display.max_columns', None)
dirname = r"C:\Stuff\BOB vs WOW after cabezal"
ext = "csv"
errors = []

# Reads csv
i = 0
for files in os.listdir(dirname):
    print(i)

    if files.endswith(ext):
        df = pd.read_csv(
            rf"{dirname}\{files}",
            names=[
                "Time (ms)",
                "Position (um)",
                "Speed (rpm)",
                "Torque (Ncm)",
                "Force (N)"
            ]
        )
        print(rf"{dirname}\{files}")

        report_values = {
            "part_number": df["Position (um)"][0],
            "report_date": df['Position (um)'][1],
            "report_part_contact": df['Position (um)'][2],
            "report_part_reduction": df['Position (um)'][3],
            "flatness_1": df["Torque (Ncm)"][1],
            "flatness_2": df["Torque (Ncm)"][2],
            "angle_deviation": df["Torque (Ncm)"][3],
        }

        # Drops the first unnecessary rows
        df.drop([0, 1, 2, 3, 5], axis=0, inplace=True)
        df.dropna(inplace=True)

        # Sets the values as integers
        df = df.astype({
            'Time (ms)': int,
            'Position (um)': int,
            'Speed (rpm)': int,
            'Torque (Ncm)': int,
            'Force (N)': int
        })

        # Sets the Time (ms) column as index
        df.set_index(df.iloc[:, 0].name, inplace=True)

        # Changes the Torque units from newton*centimeter to newton*millimeter
        df['Torque (Ncm)'] *= 10
        df.rename(columns={'Torque (Ncm)': 'Torque (Nmm)'}, inplace=True)

        # Gets the critical times based on the derivatives.
        force = ProcessValue(df["Force (N)"])
        force.configure_derivatives(
            a_clip=0, b_clip=100,
            c_clip=1.8, d_clip=10,
            abs_1=True, abs_2=False,
            sigma_1=10, sigma_2=4)

        speed = ProcessValue(df["Speed (rpm)"])
        speed.configure_derivatives(
            a_clip=0, b_clip=100,
            c_clip=5, d_clip=10,
            abs_1=True, abs_2=True,
            sigma_1=3, sigma_2=4)

        position = ProcessValue(df["Position (um)"])
        position.configure_derivatives(
            a_clip=0, b_clip=100,
            c_clip=5, d_clip=10,
            abs_1=True, abs_2=True)

        aprox_force_steps = dict(zip(aprox_force_steps, force.max_idt[0:3]))
        aprox_speed_steps = dict(zip(aprox_speed_steps, speed.max_idt))
        aprox_position_steps = dict(zip(aprox_position_steps, position.max_idt))

        temp_data = {
            'part_number': None,
            'report_date': None,
            'report_part_contact': None,
            'report_part_reduction': None,
            'flatness_1': None,
            'flatness_2': None,
            'head_starts_spinning': None,
            'head_starts_descending': None,
            'head_start_ascending': None,
            'first_contact': None,
            'part_contact': None,
            'starts_fixing': None,
            'stops_fixing': None
        }

        part_phases_columns = {
            'head_starts_spinning': [aprox_speed_steps["speed_starts_spinning"]],
            'head_starts_descending': [aprox_position_steps["position_ascending"]],
            'first_contact': [df.loc[(df.index > aprox_position_steps["position_ascending"]) & (
                        df["Torque (Nmm)"] > 1000)].index.values.astype(int)[0]],
            'part_contact': [df.loc[(df.index > aprox_position_steps["position_ascending"]) & (
                        df["Torque (Nmm)"] > 3000)].index.values.astype(int)[0]],
            'starts_fixing': [aprox_position_steps["position_stabilizes"]]
        }

        try:
            part_phases_columns['head_start_ascending'] = [aprox_position_steps["position_descending"]]
        except KeyError:
            part_phases_columns['head_start_ascending'] = None

        try:
            part_phases_columns['stops_fixing'] = [aprox_force_steps["force_falling"]]
        except KeyError:
            part_phases_columns['stops_fixing'] = None

        final_df = pd.concat([final_df, pd.DataFrame.from_dict(report_values | part_phases_columns)], ignore_index=True)

        # print(final_df)
    i += 1

final_df.to_excel(r"some_test.xlsx")

# Todo. Refactor this code.
