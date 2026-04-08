import pandas as pd
import scipy
import numpy as np

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


def process_pkl_files(data_files):

    data =[]
    for data_file in data_files:
        df = pd.read_pickle(data_file)
        data.append(df)
    print(f'processing {len(data)} files')


    inds = [df.index[0]  for df in data]
    field_names = [df.columns.get_level_values(0)[0] for df in data]

    df_meta = pd.DataFrame(inds, columns = df.index.names)
    df_meta['field_name'] = field_names
    G = df_meta.groupby(by=df_meta.columns.tolist())

    data_dict = {}
    for name, group in G:

        indicies = group.index.to_list()

        df_tmp = pd.concat([data[i] for i in indicies], axis = 1)
        field_name = df_tmp.columns.get_level_values(0)[0]

        if field_name not in data_dict:
            data_dict[field_name] = []
        data_dict[field_name].append(df_tmp)

    for field_name, df_list in data_dict.items():

        df_tmp = pd.concat(df_list, axis = 0)
        df_tmp.sort_index(inplace = True, axis = 0)
        df_tmp.sort_index(inplace = True, axis = 1)
        df_tmp = df_tmp.astype(np.float32)
        assert df_tmp.notna().all().all(), "Some values are missing"


        data_dict[field_name] = df_tmp

    for field_name, df in data_dict.items():
        print(f'{field_name}: {df.shape}')

    return data_dict