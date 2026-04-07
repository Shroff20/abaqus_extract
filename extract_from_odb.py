# abaqus python extract_from_odb.py odb_filepath
# abaqus python extract_from_odb.py abq\Job-1.odb

from odbAccess import openOdb
import numpy as np 
import pandas as pd
import os
import sys
from itertools import repeat
import multiprocessing as mp
import argparse



def get_step_frame_list(filename):

    step_frame_list = []

    print("Processing file:", filename)
    odb = openOdb(path=filename, readOnly=True)
    for step_name, step in odb.steps.items():
        step_number = step.number
        n_frames = len(step.frames)

        step_frame_list += list(zip(repeat(step_number), range(n_frames)))

        print(f"Step: {step_name}, Step number: {step_number}, Number of frames: {n_frames}")

    odb.close()

    return step_frame_list



def process_odb(filename, step_numbers = None, increment_numbers = None, field_names = None):

    print("Processing file:", filename)

    odb = openOdb(path=filename, readOnly=True)
    jobname = os.path.basename(filename).rstrip('.odb')
    output_folder = os.path.join(os.path.dirname(filename), jobname)
    os.makedirs(output_folder, exist_ok=True)


    for step_name, step in odb.steps.items():
        
        step_name = str(step_name)
        step_number = step.number
        t1 = step.totalTime

        if step_numbers is None or step_number in step_numbers:
    
            
            for frame in step.frames:
                increment_number = frame.incrementNumber
                tinst = frame.frameValue
                total_time = t1 + tinst  # calculate outside the if statement - have to always increment

                if increment_numbers is None or increment_number in increment_numbers:

                    
                    for field_name, field in frame.fieldOutputs.items():
                        # bulkDataBlocks returns a sequence of blocks
                        # Blocks are grouped by element type/section properties
                        blocks = field.bulkDataBlocks
                        
                        for block_number, block in enumerate(blocks):

                            field_name = str(field.name)

                            if field_names is None or field_name in field_names:

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

                                print(f'{total_time=}, {step_name=}, {increment_number=}, {field_name=}, {instance_name=}, {elem_type=}, {component_labels=}, {position=}, {data.shape=}')

                                if position == 'NODAL':
                                    index = node_labels
                                elif position == 'INTEGRATION_POINT':
                                    index = zip(elem_labels, integraion_points)
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
                                df = df.T
                                fn = f'{jobname}_step_{step_number}_inc_{increment_number}_field_{field_name}_block_{block_number}.pkl'
                                df.to_pickle(os.path.join(output_folder, fn))
                                print(f'saved {fn} with shape {df.shape}')

    #print(f'finished processing file: {filename}')



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Extract data from ABAQUS ODB files')
    parser.add_argument('odb_filepath', help='Path to the ODB file')
    parser.add_argument('--step_numbers', nargs='+', type=int, help='Step numbers to process', default=None)
    parser.add_argument('--field_names', nargs='+', help='Field names to process', default=None)
    parser.add_argument('--processes', help='number of processess to use for multiprocessing', default=1, type=int)

    args = parser.parse_args()
    print(args)

    if args.processes ==1:
        print('using single process')
        process_odb(args.odb_filepath, step_numbers = args.step_numbers, field_names =  args.field_names)
    else:

        num_cpus = mp.cpu_count()
        args.processes = min(args.processes, num_cpus-1)

        step_frame_list = get_step_frame_list(args.odb_filepath)
        step_frame_list = [ (step, frame) for step, frame in step_frame_list if (args.step_numbers is None or step in args.step_numbers) ]
        print(f'(step, frame) = {step_frame_list}')

        starargs = [(args.odb_filepath, [step,], [frame,], args.field_names) for step, frame in step_frame_list]
        print(starargs)

        with mp.Pool(processes=args.processes) as pool:
            pool.starmap(process_odb, starargs)



