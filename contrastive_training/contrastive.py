import os
import json
import sys
sys.path.append(".")

from contrastive_training.train import contrastive_train
from contrastive_training.utils import load_datasets

models = ["simsiam", "simclr", "moco", "lascon"]

def check_arguments_contrastive(args):
    #name is required
    assert 'model' in args, 'model not found in args (simsiam, simclr, moco, lascon)'

    default_args = {
        "base_mode": "resnet50",
        "batch_size": 256,
        "learning_rate_encoder": 0.2,
        "learning_rate_head": 1,
        "weight_decay": 0.000001,
        "momentum": 0.9,
        "temperature": 0.5,
        "epochs": 5,
        "save_every": 10
    }

    args = {**default_args, **args}
    
    return args

def contrastive_pretraining(args, device='cuda', models_dir="trained_models", datasets_dir="datasets"):
    assert "datasets" in args, 'datasets argument is required'
    if 'drop_pairs' in args:
        assert len(args['datasets']) == len(args['drop_pairs']), "Number of datasets and drop pairs should be the same"

    default_args = {
        "skip": False,
        "use_complete_pairs": True,
        "drop_pairs": [0],
        "experiments": {}
    }
    args = {**default_args, **args}

    if len(args['datasets']) != len(args['drop_pairs']):
        args['drop_pairs'] = [0] * len(args['datasets'])
    
    if args['skip']:
        print("Skipping contrastive training")
        return

    datasets = args["datasets"]

    print("CONTRASTIVE TRAINING")

    experiments = args["experiments"]
    print("---------------------------")
    for exp_name in experiments:
        params = check_arguments_contrastive(experiments[exp_name])
        print(f"training {exp_name}")
            
        try:
            load_datasets(datasets, dataset_dir=datasets_dir, base_model=params["base_model"], 
                            use_complete=args['use_complete_pairs'], drop=args['drop_pairs'])
            
            #save parameters to file
            with open(f"{models_dir}/{exp_name}_params.json", 'w') as f:
                json.dump(params, f)
            
            contrastive_train(params=params, 
                              name=exp_name, datasets=datasets, 
                              models_dir=models_dir, datasets_dir=datasets_dir, 
                              device=device)
        except Exception as e:
            print(f"Error in training {exp_name}: {e}") 
        
        print(f"Finished {exp_name}")
        print("---------------------------")
            