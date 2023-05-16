import pandas as pd
import matplotlib.pyplot as plt
import concurrent.futures
import numpy as np
import os
import re
import seaborn as sns
pd.set_option('display.max_columns', None)


def read_file(path_file: str):
    try:
        df = pd.read_csv(path_file, header=None, sep=r'\r\n', engine='python')
    except pd.errors.ParserError:
        return {
            "date": [None],
            "hour": [None],
            "sub_assy": [None],
            "total_average": [None],
            "peak_pos": [None],
            "lsl": [None],
            "usl": [None],
            "225mm": [None],
            "250mm": [None],
            "275mm": [None],
            "within_average": [None],
            "pass": [None],
            'path': [path_file]
        }

    df = df[0].str.split(',', expand=True)
    df.drop([2, 3, 4], axis=1, inplace=True)
    df[0] = df[0].str.replace('"', "")
    df[1] = df[1].str.replace('"', "")

    meta_delimiter = df.index[df[0] == 'Position'][0]
    meta = df.iloc[:meta_delimiter].copy()

    data = df.iloc[meta_delimiter + 1:].copy()
    data[0] = pd.to_numeric(data[0], errors='coerce')
    data[1] = pd.to_numeric(data[1], errors='coerce')

    plt.plot(data[0], data[1])

    name = meta[1][1]
    name = name.split('\\')[-1].split()[1]

    if len(data) > 500:
        val_225 = data[data[0] >= 225].iloc[0][1]
        val_250 = data[data[0] >= 250].iloc[0][1]
        val_275 = data[data[0] >= 275].iloc[0][1]
        within_average = (val_225 + val_250 + val_275) / 3.0
    else:
        print(path_file)
        val_225 = None
        val_250 = None
        val_275 = None
        within_average = None

    results_dict = {
        "date": [meta[1][3]],
        "hour": [meta[1][4]],
        "sub_assy": [name],
        "total_average": [data[1].mean()],
        "peak_pos": [meta[1][15]],
        "lsl": [meta[1][65]],
        "usl": [meta[1][69]],
        "225mm": [val_225],
        "250mm": [val_250],
        "275mm": [val_275],
        "within_average": [within_average],
        'local_path': [path_file],
        'para_file': [meta[1][2]]
    }

    return results_dict


def graph_samples():
    files_12x35 = r'Input Files\1.2X35'
    files_12x36 = r'Input Files\1.2X36'
    files_10x37 = r'Input Files\1.0X37'

    x = list(range(225, 276))

    # TODO. Implement a parameter to the function so I can change this from the if main
    selected_files = files_12x35
    files_list = []

    for path, subdirs, files in os.walk(selected_files):
        for file in files:
            if file.endswith('csv'):
                file_path = os.path.join(path, file)
                files_list.append(file_path)

    [read_file(file) for file in files_list]

    if selected_files == files_12x35:
        y_ucl = 1.95
        y_nom = 1.75
        y_lcl = 1.55
    elif selected_files == files_12x36:
        y_ucl = 2.3
        y_nom = 2.075
        y_lcl = 1.85
    elif selected_files == files_10x37:
        y_ucl = 1.7
        y_nom = 1.5
        y_lcl = 1.3
    else:
        y_ucl = 0
        y_nom = 0
        y_lcl = 0

    ucl = [y_ucl for _ in range(len(x))]
    lcl = [y_lcl for _ in range(len(x))]
    nom = [y_lcl for _ in range(len(x))]

    plt.plot(x, ucl, color='black', linewidth=2)
    plt.plot(x, lcl, color='black', linewidth=2)

    plt.xticks(np.array(range(0, 500, 10)), rotation='vertical')
    plt.show()


def find_files(some_path, extension):
    file_list = []
    for path, subdirs, files in os.walk(some_path):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(path, file)
                file_list.append(file_path)

    return file_list


if __name__ == '__main__':
    graph_samples()
    
