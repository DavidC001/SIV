import sys
sys.path.append(".")

import torch
import numpy as np
import random
import os
import json
from pose_estimation.models import models, getPoseEstimModel
from pose_estimation.functions import get_optimizer
from dataloaders.datasets import out_joints 
from pose_estimation.train import train
from pose_estimation.utils import getLatestModel, getDatasetLoader

from contrastive_training.clustering import get_selected_images

def parseArgs(args):
    """
    Parse the arguments for the pose estimation model.

    Parameters:
    - args: dict, arguments for the pose estimation model

    Returns:
    - args: dict, updated arguments for the pose estimation model
    """
    assert 'model' in args, 'Need to define the model type (simclr, simsiam, moco, lascon, resnet)'
    assert 'base_model' in args, 'Need to define the model backbone encoder (resnet50 - resnet18)'
    assert 'pretrained_name' in args, 'pretrained model name not found in args'

    default_args = {
        'architecture': [],
        'batch_size': 1024,
        'learning_rate': 0.001,
        'weight_decay': 0.01,
        'epochs': 20,
        'save_every': 10,
        'LN': False,
        'activation': 'gelu',
        'use_cluster': 'NONE'
    }

    args = {**default_args, **args}
    
    return args

def pose_estimation( args, device='cpu', models_dir="trained_models", datasets_dir="datasets"):
    """
    Train the pose estimation models.

    Parameters:
        args: dict, arguments for the pose estimation models
        device: str, device, default is 'cpu'
        models_dir: str, directory to save the trained models, default is 'trained_models'
        datasets_dir: str, directory to save the datasets, default is 'datasets'
        base_model: str, base model, default is 'resnet18'

    """
    #skip if specified
    if "skip" in args and args["skip"]:
        print("Skipping pose estimation training")
        return
    
    assert "dataset" in args, "dataset not found in args"

    dataset = args["dataset"]
    
    print("POSE ESTIMATION TRAINING")

    experiments = args["experiments"]
    print("---------------------------")
    for exp_name in experiments:
        params = parseArgs(experiments[exp_name])
        print(f"Training {exp_name}")

        try:
            np.random.seed(0)
            torch.manual_seed(0)
            random.seed(0)

            #save parameters to file
            with open(f"{models_dir}/{exp_name}_params.json", 'w') as f:
                json.dump(params, f)

            pretrained = getPoseEstimModel(
                    path = getLatestModel(os.path.join(models_dir, params['pretrained_name'])),
                    model_type=params["model"],
                    layers=params['architecture'],
                    out_dim=out_joints[dataset]*3,
                    layer_norm = params['LN'],
                    activation = params['activation'],
                    device=device,
                    base_model=params['base_model']
                )
            # print(pretrained)

            use_cluster = params["use_cluster"]
            if use_cluster!="NONE" and not use_cluster.startswith("RANDOM") and not os.path.exists(use_cluster):
                n_clusters = int(use_cluster.split("_")[-2][:-1])
                percentage = int(use_cluster.split("_")[-1][:-5])
                get_selected_images(pretrained, params['base_model'], dataset, datasets_dir, use_cluster, n_clusters, percentage, device)

            train_loader, val_loader, test_loader = getDatasetLoader(
                dataset=dataset, 
                batch_size=args["batch_size"], 
                datasets_dir=datasets_dir, 
                base_model=params["base_model"],
                use_cluster=use_cluster
                )
             
            optim, scheduler = get_optimizer(
                    net=pretrained,
                    learning_rate=params["learning_rate"],
                    weight_decay=params["weight_decay"],
                )

            train(
                    name=exp_name,
                    model=pretrained,
                    optimizer= optim,
                    scheduler=scheduler,
                    train_loader=train_loader,
                    val_loader=val_loader,
                    test_loader=test_loader,
                    epochs=params["epochs"],
                    save_every=params["save_every"],
                    device=device,
                    model_dir=models_dir,
                )

        except Exception as e:
            print(f"Error training {exp_name}: {e}")

        
        print(f"Finished {exp_name}")
        print("---------------------------")
                    

if __name__ == '__main__':
    args = {
        'dataset': 'skiPose',
        'skip': False,
        'batch_size': 1024,
        'simclr': {
            'architecture': [512, 256],
            'name': 'simclr_estim',
            'pretrained_name': 'simclr',
            'train': True,
            'learning_rate': 0.01,
            'weight_decay': 0.000001,
            'momentum': 0.9,
            'epochs': 20,
            'save_every': 10
        }
    }

    pose_estimation(args, device="cuda")
