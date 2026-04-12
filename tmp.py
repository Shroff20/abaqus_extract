# abaqus python tmp.py 


import pandas as pd
import scipy
import numpy as np
from odbAccess import openOdb
import numpy as np 
import pandas as pd
import os
import sys
from itertools import repeat
import multiprocessing as mp
import argparse
import glob



def parse_frame(frame, step_number, step_name, step_total_time, fields_to_extract = None):

    increment_number = frame.incrementNumber
    tinst = frame.frameValue
    total_time = step_total_time + tinst  # calculate outside the if statement - have to always increment

    data_dict = {}
    for field_name, field in frame.fieldOutputs.items():

        field_name = str(field.name)
    
        if fields_to_extract is None or field_name in fields_to_extract:

            blocks = field.bulkDataBlocks
                        
            for block_number, block in enumerate(blocks):

                instance_name = block.instance.name if block.instance else "Assembly"
                elem_type = str(block.sectionPoint)
                data = block.data           # Flat array of values
                node_labels = block.nodeLabels
                elem_labels = block.elementLabels
                component_labels = block.componentLabels
                position = str(block.position)
                integraion_points = block.integrationPoints

                if component_labels  == (): # scalar fields have no labels, so just use the field name as label
                    component_labels = (str(field_name),)

                #print(f'{total_time=}, {step_name=}, {increment_number=}, {field_name=}, {instance_name=}, {elem_type=}, {component_labels=}, {position=}, {data.shape=}')

                if position == 'NODAL':
                    index1 = node_labels
                    index2 = [-1] * len(node_labels)  # dummy index to allow unstacking
                elif position == 'INTEGRATION_POINT':
                    index1 = elem_labels
                    index2= integraion_points
                else:
                    raise Exception(f'unsupported position type {position}')

                index = list(zip(index1, index2))
                index = pd.MultiIndex.from_tuples(index, names=["node_or_element_idx", "integration_point"])

                columns = ( (field_name, component, instance_name) for component in component_labels)

                df = pd.DataFrame(data, columns = columns, index = index)
                df.columns = pd.MultiIndex.from_tuples(df.columns, names=['field_name', 'component', 'instance_name'])
                #df.index.name = 'idx'
                df = df.unstack(level=index.names)
                df.name = (step_number, increment_number, total_time, step_name)
                df = df.to_frame()

                #print(df)
                df.columns = pd.MultiIndex.from_tuples(df.columns, names=[ 'step_number', 'increment_number','total_time', 'step_name', ])
                df = df.astype(np.float32)
                df = df.T

                if field_name not in data_dict:
                    data_dict[field_name] = []
                data_dict[field_name].append(df)

        data_dict[field_name] = pd.concat(data_dict[field_name], axis = 1)
        data_dict[field_name].sort_index(inplace = True, axis = 0)
        data_dict[field_name].sort_index(inplace = True, axis = 1)

    return data_dict




odb_fn = r'.\abq\Job-2.odb'

odb = openOdb(path=odb_fn, readOnly=True)


data_dict_by_field = {}

for step_name, step in odb.steps.items():
    
    step_name = str(step_name)
    step_number = step.number
    step_total_time = step.totalTime

    for frame in step.frames:
        print(f'Processing step {step_name}, increment {frame.incrementNumber}')
        frame_data_dict = parse_frame(frame, step_number, step_name, step_total_time)

        for field_name, df in frame_data_dict.items():
            if field_name not in data_dict_by_field:
                data_dict_by_field[field_name] = []
            data_dict_by_field[field_name].append(df)

for field_name in data_dict_by_field.keys():
    data_dict_by_field[field_name] = pd.concat(data_dict_by_field[field_name], axis = 0)
    data_dict_by_field[field_name].sort_index(inplace = True, axis = 0)
    data_dict_by_field[field_name].sort_index(inplace = True, axis = 1)
    data_dict_by_field[field_name] =  data_dict_by_field[field_name].astype(np.float32)
    assert data_dict_by_field[field_name].notna().all().all(), "Some values are missing"


    print(f'{field_name}: (timepoints, dofs) = {data_dict_by_field[field_name].shape}')


    data_dict_by_field[field_name].to_parquet(f'{field_name}.parquet')