import sys
sys.path.append('.')

import os
import re
import torch
import torchvision.transforms as T
from dataloaders.datasets import pose_datasets
from torchvision.models.resnet import  ResNet50_Weights, ResNet18_Weights
import math

def getLatestModel(path):
    """
    Return the path to the latest model in the directory.

    Parameters:
    - path: str, path to the directory

    Returns:
    - path: str, path to the latest model in the directory
    """
    path = path.replace("\\", "/")
    try:
        files = os.listdir(path)
        # print(files)
        #remove non weight files
        files = [file for file in files if '.pt' in file]
        if len(files) > 0:
            epoch = max([int(re.findall(r'\d+', file)[0]) for file in files])
        else:
            raise Exception("No model found")

        path = os.path.join(path, "epoch_"+str(epoch)+".pt").replace("\\", "/")
    except:
        path = None
    
    return path
        

def getDatasetLoader(dataset, batch_size, datasets_dir="datasets", base_model="resnet18", use_cluster="NONE"):
    """
    return the dataloader for the specified dataset.

    Parameters:
    - dataset: str, dataset name
    - batch_size: int, batch size
    - datasets_dir: str, directory to save the datasets, default is 'datasets'
    - base_model: str, base model, default is 'resnet18'
    - use_cluster: str, use cluster, default is 'NONE' to use all the data. 'RANDOM_50' to use 50% of the data randomly

    Returns:
    - train_loader: torch.utils.data.DataLoader, training dataloader
    - val_loader: torch.utils.data.DataLoader, validation dataloader
    - test_loader: torch.utils.data.DataLoader, test dataloader
    """
    # normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    # transforms = T.Compose([T.ToPILImage(),
    #                         T.Resize(256),
    #                         T.CenterCrop(224),
    #                         T.ToTensor(),
    #                         normalize])

    if base_model == "resnet50":
        transforms = ResNet50_Weights.DEFAULT.transforms()
    elif base_model == "resnet18":
        transforms = ResNet18_Weights.DEFAULT.transforms()
    else:
        raise ValueError("Invalid base model")
    transforms = T.Compose([T.ToPILImage(), transforms])

    train, val, test = pose_datasets[dataset](transforms, datasets_dir, use_cluster)
    
    available_workers = math.ceil(os.cpu_count() / 2)

    train_loader = torch.utils.data.DataLoader(train, batch_size, shuffle=True, num_workers=available_workers)
    val_loader = torch.utils.data.DataLoader(val, batch_size, shuffle=False, num_workers=available_workers)
    test_loader = torch.utils.data.DataLoader(test, batch_size, shuffle=False, num_workers=available_workers)

    return train_loader, val_loader, test_loader
