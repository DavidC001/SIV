import os
import torch
from torch.utils.data import Dataset
import cv2
import random

import matplotlib.pyplot as plt
import torchvision.transforms as T


class KinectDataset(Dataset):
    def __init__(self, transform):
        print("KinectDataset")

class ClusterKinectDataset(Dataset):
    def __init__(self, transform):
        print("ClusterKinectDataset")