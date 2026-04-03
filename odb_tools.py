import pandas as pd
import scipy


def process_data(data):

    data_by_field = {}

    for step_number, step_data in data.items():
        for increment_number, increment_data in step_data.items():
            for field_name, field_data in increment_data.items():

                block_data = []
                for block_number, df in field_data.items():
                    print(
                        f"      * Step: {step_number}, Increment: {increment_number}, Field: {field_name}, Block: {block_number}"
                    )
                    block_data.append(df)

                df_merged = pd.concat(block_data, axis=1)

                if field_name not in data_by_field:
                    data_by_field[field_name] = []

                data_by_field[field_name].append(df_merged)

    for field_name, dfs in data_by_field.items():
        data_by_field[field_name] = pd.concat(dfs, axis=0)
        data_by_field[field_name].sort_index(inplace=True)
        data_by_field[field_name].sort_index(inplace=True, axis=1)
        assert (
            not data_by_field[field_name].isna().any().any()
        )  # make sure there are no Nans

    return data_by_field


def save_to_hdf5(loadcase, data_by_field, output_hdf5):
    for field_name, df in data_by_field.items():
        df.to_hdf(
            output_hdf5, key=loadcase + "/" + field_name, format="fixed", mode="a", complib='blosc', complevel=5
        )


def save_to_matlab(data_by_field, output_filename):

    data_dict = {}

    for field_name, df in data_by_field.items():
                                        
        print(f"Field: {field_name}, DataFrame shape: {df.shape}")

        row_index =df.index.to_frame()
        col_index =df.columns.to_frame()

        data_dict[field_name] = {'row_index_names': row_index.columns, 'col_index_names': col_index.columns, 'row_index': row_index, 'col_index': col_index, 'data': df.values}


    scipy.io.savemat(output_filename, data_dict, do_compression = True)