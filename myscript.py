#abaqus script=myscript.py


from odbAccess import openOdb
import numpy as np 
import scipy
import pandas as pd


filename = 'abq/Job-1.odb'
odb = openOdb(path=filename)


for stepName, step in odb.steps.items():

    print(dir(step))
    print("Step: {}".format(stepName))
    step_number = step.number
    t1 = step.totalTime
    print("  Step Number: {}".format(step_number))
    for frame in step.frames:

        incrementNumber = frame.incrementNumber
        tinst = frame.frameValue
        tcurrent = t1 + tinst

        print("  Frame ID: {}".format(frame.frameId))
        print("  Increment: {} | Time: {}".format(incrementNumber, tcurrent))

        
        for fieldName, field in frame.fieldOutputs.items():
            # bulkDataBlocks returns a sequence of blocks
            # Blocks are grouped by element type/section properties
            blocks = field.bulkDataBlocks
            
            for block in blocks:

                fieldName = str(field.name)
                instance_name = block.instance.name if block.instance else "Assembly"
                elem_type = str(block.sectionPoint)
                data = block.data           # Flat array of values
                node_labels = block.nodeLabels
                elem_labels = block.elementLabels
                componentLabels = block.componentLabels
                position = str(block.position)

                if componentLabels  == (): # scalar fields have no labels, so just use the field name as label
                    componentLabels = (str(fieldName),)


                print(tcurrent, stepName, incrementNumber, fieldName, instance_name, elem_type, componentLabels, position, data.shape)

                print(position)
                if position == 'NODAL':
                    index = node_labels
                elif position == 'INTEGRATION_POINT':
                    index = elem_labels
                else:
                    raise Exception(f'unsupported position type {position}')

                # 'data' is a tuple of floats. 
                # For a vector (U), it's [u1, u2, u3, u1, u2, u3, ...]
                # For a tensor (S), it depends on the invariant/component count
 
                if  node_labels is not None:
                    print(node_labels.shape)  
                if  elem_labels is not None:
                    print(elem_labels.shape)
                print(data.shape)

                columns = ( (instance_name, fieldName, component) for component in componentLabels)
                print(columns)

                df = pd.DataFrame(data, columns = columns, index = index)
                #df['data'] = data
                print(df)


odb.close()