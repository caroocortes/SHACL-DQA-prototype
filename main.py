import os
from utils import *
import json
from const import *

from dq_assessment import DQAssessment


def execute_assessment():
    dq_assessment = DQAssessment(CONFIG_FILE_PATH, 
                                 inference_data_shapes=True, 
                                 metadata_shapes=True, 
                                 data_shapes=True, 
                                 vocab_shapes=True)

    dq_assessment.run()

    output_path = "run_info.json"

    # Load existing run_info if it exists
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            run_info = json.load(f)
    else:
        run_info = {}

    run_info[dq_assessment.dataset_name] = {
        "total_elapsed_time": dq_assessment.total_elapsed_time,
        "vocab_shapes_elapsed_time": dq_assessment.vocab_shapes_elapsed_time,
        "data_shapes_elapsed_time": dq_assessment.data_shapes_elapsed_time,
        "metadata_shapes_elapsed_time": dq_assessment.metadata_shapes_elapsed_time,
        "inference_shapes_elapsed_time": dq_assessment.inference_shapes_elapsed_time,
        "num_inst_shapes": dq_assessment.counter_shapes,
        "graph_profile": dq_assessment.graph_profile
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(run_info, f, indent=4)

if "__main__":
    execute_assessment()
    


# TODO: 

# - ver la shape malformed datatypes -> ver el KGHeartBeat para ver el dictionary que ellos usaban
# - correr experimentos en todos los datasets
# - hacer statistics de número de shapes y demás - done
# ver qué pasa si no hay metadata file ni vocabularies, escribo igual el resultado???
# revisar shapes que se ejecutan contra vocabularies
