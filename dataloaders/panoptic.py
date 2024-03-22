import os
import torch
from torch.utils.data import Dataset
import cv2
import random

import matplotlib.pyplot as plt
import torchvision.transforms as T


class PanopticDataset(Dataset):
    def __init__(self, transform, data_set='training'):

        # change this to the path where the dataset is stored
        self.data_path = "datasets/ProcessedPanopticDataset/"
        self.training_dir = []

        self.transform = transform

        self.set = data_set

        paths = []

        motion_seq = os.listdir(self.data_path)
        no_dir = ['scripts','python','matlab','.git','glViewer.py','README.md','matlab',
                'README_kinoptic.md', '171204_pose3']

        for dir in motion_seq:
            if dir not in no_dir:
                if 'haggling' in dir:
                    continue
                elif dir == '171204_pose2' or dir =='171204_pose5' or dir =='171026_cello3':
                    if os.path.exists(os.path.join(self.data_path,dir, 'hdJoints')):
                        data_path = os.path.join(self.data_path,dir, 'hdJoints')
                        for lists in (os.listdir(data_path)):
                            paths.append(os.path.join(data_path,lists.split('.json')[0]).replace('\\', '/'))
                elif 'ian' in dir:
                    continue
                else:
                    if os.path.exists(os.path.join(self.data_path,dir,'hdJoints')):
                        data_path = os.path.join(self.data_path,dir,'hdJoints')
                        for lists in (os.listdir(data_path)):
                            paths.append(os.path.join(data_path,lists.split('.json')[0]).replace('\\', '/'))

        self.data = {'paths': paths}

    def __len__(self):
        return len(self.data['paths'])

    def get_second_view(self, image_path):
        """Randomly gets another camera view"""
        split = image_path.split(';')
        camera = split[1].split('_')
        view = int(camera[-1]) # id of the first view

        second_view = random.randint(0, view) if view > 15 else random.randint(view + 1, 30) # randomly get second view id that is smaller or bigger than the first one

        camera[2] = str(second_view) if second_view > 9 else '0' + str(second_view)
        camera = '_'.join(camera)
        split[1] = camera
        second_path = ';'.join(split)

        return second_path


    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        sample = dict()

        path_split = self.data['paths'][idx].split('/hdJoints')
        image1_path = path_split[0] + '/hdImages' + path_split[-1] + '.jpg'
        image2_path = self.get_second_view(image1_path)

        for i in range(0, 10):
            if os.path.isfile(image2_path):
                image2 = cv2.imread(image2_path)
                image2 =cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
                image2 = self.transform(image2)
                break
            else:
                image2_path = self.get_second_view(image1_path)
        else:
            # apply random rotation on the first image if the second view cannot be found in 10 iterations
            image2 = cv2.imread(image1_path)
            image2 =cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
            image2 = self.transform(image2)
            image2 = T.RandomRotation(45)(image2)

        image1 = cv2.imread(image1_path)
        image1 =cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
        image1 = self.transform(image1)

        sample['image1'] = image1
        sample['image2'] = image2

        return sample

class ClusterPanopticDataset(Dataset):
    def __init__(self, transform, data_set='training'):

        # change this to the path where the dataset is stored
        self.data_path = "datasets/ProcessedPanopticDataset/171204_pose3/hdImages"

        images = [os.path.join(self.data_path, f.replace('\\','/')) for f in os.listdir(self.data_path) 
                    if os.path.isfile(os.path.join(self.data_path, f.replace('\\','/')))][0:6000]
        self.transform = transform

        self.data = {'paths': images}


    def __len__(self):
        return len(self.data['paths'])


    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        sample = dict()

        image_path = self.data['paths'][idx]

        image = cv2.imread(image_path)
        image =cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = self.transform(image)

        sample['image'] = image

        return sample