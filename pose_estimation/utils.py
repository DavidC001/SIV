import sys
sys.path.append('.')

import os
import re
import torch
import torchvision.transforms as T
from dataloaders.datasets import pose_datasets

def getLatestModel(path):
    path = path.replace("\\", "/")
    files = os.listdir(path)
    #remove non weight files
    files = [file for file in files if '.pt' in file]
    if len(files) > 1:
        epoch = max([int(re.findall(r'\d+', file)[0]) for file in files])
    else:
        raise Exception("No model found")
    return os.path.join(path, "epoch_"+str(epoch)+".pth").replace("\\", "/")

def getDatasetLoader(dataset, batch_size, datasets_dir="datasets"):
    transforms = T.Compose(
        [
            T.ToTensor(),
            T.Resize(size=(128, 128)),
        ]
    )

    train, val, test = pose_datasets[dataset](transforms, datasets_dir)
    
    train_loader = torch.utils.data.DataLoader(train, batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val, batch_size, shuffle=False)
    test_loader = torch.utils.data.DataLoader(test, batch_size, shuffle=False)

    return train_loader, val_loader, test_loader