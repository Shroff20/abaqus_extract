import pandas as pd
import scipy
import os
from itertools import repeat


def save_to_hdf5(loadcase, data_by_field, output_hdf5):
    for field_name, df in data_by_field.items():
        df.to_hdf(
            output_hdf5, key=loadcase + "/" + field_name, format="fixed", mode="a", complib='blosc', complevel=5
        )


def save_to_matlab(loadcase, data_by_field, output_filename):

    data_dict = {}

    for field_name, df in data_by_field.items():
                                        
        print(f"Field: {field_name}, DataFrame shape: {df.shape}")

        row_index =df.index.to_frame()
        col_index =df.columns.to_frame()

        data_dict[field_name] = {'loadcase': loadcase, 'row_index_names': row_index.columns, 'col_index_names': col_index.columns, 'row_index': row_index, 'col_index': col_index, 'data': df.values}


    scipy.io.savemat(output_filename, data_dict, do_compression = True)

