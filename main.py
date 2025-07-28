import os
from utils import *
import json
from const import *
import argparse

from dq_assessment import DQAssessment


def execute_assessment(args):

    if not args.d:
        raise Exception("No dataset name provided")
    elif not args.ra and not args.rd and not args.rm and not args.rv:
        raise Exception("Specify assessment to run (ra, rd, rm or rv)")
    else:
        config_file_path = f'config/{args.d}.ini'
        if args.ra:
            metadata_shapes = True
            data_shapes = True
            vocab_shapes = True
        else:
            metadata_shapes = args.rm 
            data_shapes = args.rd
            vocab_shapes = args.rv

        dq_assessment = DQAssessment(config_file_path, 
                                    metadata_shapes=metadata_shapes, 
                                    data_shapes=data_shapes, 
                                    vocab_shapes=vocab_shapes)

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
    parser = argparse.ArgumentParser(description="Run DQA on a dataset")
    parser.add_argument(
        "-d",
        type=str,
        required=True,
        help="Name of the dataset to process. It should also match the name of the config file"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-ra", action="store_true", help="Run the assessment on data, metadata & vocabularies")
    group.add_argument("-rm", action="store_true", help="Run the assessment only on metadata")
    group.add_argument("-rd", action="store_true", help="Run the assessment only on data")
    group.add_argument("-rv", action="store_true", help="Run the assessment only on vocabularies")
    args = parser.parse_args()
    print(args)
    execute_assessment(args)
    