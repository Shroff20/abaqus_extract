# abaqus python extract_from_odb.py odb_filepath
# abaqus python extract_from_odb.py abq\Job-1.odb

from odbAccess import openOdb
import numpy as np 
import pandas as pd
import pickle
from collections import defaultdict
import os
import sys


filename = sys.argv[1]

print("Processing file:", filename)

odb = openOdb(path=filename)
jobname = os.path.basename(filename).rstrip('.odb')
output_folder = os.path.dirname(filename)

def nested_dict():
    return defaultdict(nested_dict)

def to_standard_dict(d):
    if isinstance(d, defaultdict):
        # Recursively convert the values, then cast the whole thing to a dict
        return {k: to_standard_dict(v) for k, v in d.items()}
    return d

all_data = nested_dict()

for step_name, step in odb.steps.items():

    step_name = str(step_name)
    step_number = step.number
    t1 = step.totalTime
    
    for frame in step.frames:

        increment_number = frame.incrementNumber
        tinst = frame.frameValue
        total_time = t1 + tinst
        
        for field_name, field in frame.fieldOutputs.items():
            # bulkDataBlocks returns a sequence of blocks
            # Blocks are grouped by element type/section properties
            blocks = field.bulkDataBlocks
            
            for block_number, block in enumerate(blocks):

                field_name = str(field.name)
                instance_name = block.instance.name if block.instance else "Assembly"
                elem_type = str(block.sectionPoint)
                data = block.data           # Flat array of values
                node_labels = block.nodeLabels
                elem_labels = block.elementLabels
                component_labels = block.componentLabels
                position = str(block.position)

                if component_labels  == (): # scalar fields have no labels, so just use the field name as label
                    component_labels = (str(field_name),)

                print(total_time, step_name, increment_number, field_name, instance_name, elem_type, component_labels, position, data.shape)

                if position == 'NODAL':
                    index = node_labels
                elif position == 'INTEGRATION_POINT':
                    index = elem_labels
                else:
                    raise Exception(f'unsupported position type {position}')

                columns = ( (field_name, component, instance_name) for component in component_labels)

                df = pd.DataFrame(data, columns = columns, index = index)
                df.columns = pd.MultiIndex.from_tuples(df.columns, names=['field_name', 'component', 'instance_name'])
                df.index.name = 'idx'
                df = df.unstack(level='idx')
                df.name = (step_number, increment_number, total_time, step_name)
                df = df.to_frame()

                df.columns = pd.MultiIndex.from_tuples(df.columns, names=[ 'step_number', 'increment_number','total_time', 'step_name', ])
                df = df.astype(np.float32)
                all_data[step_number][increment_number][field_name][block_number] = df.T

odb.close()
all_data = to_standard_dict(all_data)


fn = os.path.join(output_folder, jobname+'.pkl')

with open(fn, 'wb') as f:
    pickle.dump(all_data, f)

print('saved file:', fn)




