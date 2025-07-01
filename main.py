import os
from utils import *
import json
from const import *

from dq_assessment import DQAssessment


def execute_assessment():
    dq_assessment = DQAssessment(CONFIG_FILE_PATH, 
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
        "num_inst_shapes": dq_assessment.counter_shapes,
        "graph_profile": dq_assessment.graph_profile
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(run_info, f, indent=4)

    with open(f'{PROFILE_DATASETS_FOLDER_PATH}/{dq_assessment.dataset_name}.json', "w", encoding="utf-8") as f:
        json.dump(dq_assessment.graph_profile, f, indent=4)

if "__main__":
    execute_assessment()
    