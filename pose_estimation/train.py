import sys
sys.path.append('.')
import os
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter
import torch
import re
from pose_estimation.functions import get_loss
from copy import deepcopy


def training_step(net, data_loader, optimizer, cost_function, device='cuda'):
    """
    Make a training step for the pose estimation model.

    Parameters:
    - net: torch.nn.Module, network model
    - data_loader: torch.utils.data.DataLoader, data loader
    - optimizer: torch.optim.Optimizer, optimizer
    - cost_function: function, cost function
    - device: str, device, default is 'cuda'
    """
    cumulative_loss = 0.0
    samples = 0.0

    net.train()

    for batch in tqdm(data_loader):

        images = batch['image']
        poses = batch['poses_3d']

        images = images.to(device)
        poses = poses.to(device)

        output = net(images)

        loss = cost_function(output, poses, device=device)
        cumulative_loss += loss.item()

        loss.backward()
        # print(loss.item())

        optimizer.step()

        optimizer.zero_grad()

        samples += images.shape[0]

        

    return cumulative_loss / samples


def test_step(net, data_loader, cost_function, device='cuda'):
    """
    Make a test step for the pose estimation model.

    Parameters:
    - net: torch.nn.Module, network model
    - data_loader: torch.utils.data.DataLoader, data loader
    - cost_function: function, cost function
    - device: str, device, default is 'cuda'
    """
    cumulative_loss = 0.
    samples = 0.

    net.eval()

    with torch.no_grad():
        for batch in tqdm(data_loader):
            images = batch['image']
            poses = batch['poses_3d']

            images = images.to(device)
            poses = poses.to(device)

            output = net(images)

            loss = cost_function(output, poses, device=device)
            cumulative_loss += loss.item()

            # #show the two poses
            # from matplotlib import pyplot as plt
            # import cv2
            # from pose_estimation.functions import find_rotation_mat
            # cv2.imshow("image", images[0].cpu().numpy().transpose(1,2,0))
            # poses = poses[0].view(-1,3)
            # poses = poses - poses.mean(dim=0)
            # output = output[0].view(-1,3)
            # output = output - output.mean(dim=0)
            # rotation_matrix = find_rotation_mat(output, poses)
            # # print (rotation_matrix)
            # output = torch.mm(output, rotation_matrix)
            # fig = plt.figure()
            # ax = fig.add_subplot(111, projection='3d')
            # ax.scatter(poses[:,0].cpu().numpy(), poses[:,1].cpu().numpy(), poses[:,2].cpu().numpy(), c='r')
            # #write numbers
            # for i in range(poses.shape[0]):
            #     ax.text(poses[i,0].cpu().numpy(), poses[i,1].cpu().numpy(), poses[i,2].cpu().numpy(), "T"+str(i))
            # #connect the 17 joints
            # connections = [ [0,1], [1,2], [2,3], [0,4], [4,5], [5,6], [8,9], [9,10], [8,11], [11,12], [12,13], [0,7], [14,15], [15,16],[7,8], [14,8]]
            # for connection in connections:
            #     ax.plot([poses[connection[0],0].cpu().numpy(), poses[connection[1],0].cpu().numpy()], [poses[connection[0],1].cpu().numpy(), poses[connection[1],1].cpu().numpy()], [poses[connection[0],2].cpu().numpy(), poses[connection[1],2].cpu().numpy()], c='r')
            # ax.scatter(output[:,0].cpu().numpy(), output[:,1].cpu().numpy(), output[:,2].cpu().numpy(), c='b')
            # for i in range(output.shape[0]):
            #     ax.text(output[i,0].cpu().numpy(), output[i,1].cpu().numpy(), output[i,2].cpu().numpy(), "P"+str(i))
            # for connection in connections:
            #     ax.plot([output[connection[0],0].cpu().numpy(), output[connection[1],0].cpu().numpy()], [output[connection[0],1].cpu().numpy(), output[connection[1],1].cpu().numpy()], [output[connection[0],2].cpu().numpy(), output[connection[1],2].cpu().numpy()], c='b')
            # plt.show()


            samples += images.shape[0]

    return cumulative_loss / samples


def train (model, optimizer, scheduler, train_loader, val_loader, test_loader, epochs, save_every=10, device='cuda', model_dir="trained_models", name="model", patience = 3):
    """
    Train the pose estimation model.

    Parameters:
        model: torch.nn.Module, network model
        optimizer: torch.optim.Optimizer, optimizer
        scheduler: torch.optim.lr_scheduler, scheduler
        train_loader: torch.utils.data.DataLoader, training data loader
        val_loader: torch.utils.data.DataLoader, validation data loader
        test_loader: torch.utils.data.DataLoader, test data loader
        epochs: int, number of epochs
        save_every: int, save every n epochs, default is 10
        device: str, device, default is 'cuda'
        model_dir: str, directory to save the trained models, default is 'trained_models'
        name: str, model name, default is 'model'
        patience: int, patience for early stopping, default is 2
    
    """
    net = model
    epoch = 0
    cost_function = get_loss

    tensorboard_tag = "estimator"
    tensorboard_dir = os.path.join(model_dir, "tensorboard", name).replace("\\", "/")
    
    info_file = os.path.join(model_dir, name, "info.txt").replace("\\", "/")
    model_file = os.path.join(model_dir, name, "epoch_").replace("\\", "/")
    model_dir = os.path.join(model_dir, name).replace("\\", "/")
    optimizer_file = os.path.join(model_dir, "optimizer_epoch").replace("\\", "/")
    scheduler_file = os.path.join(model_dir, "scheduler_epoch").replace("\\", "/")

    #create folder for model
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    writer = SummaryWriter(log_dir=tensorboard_dir, filename_suffix="_"+name)

    #load weights
    if os.path.exists(model_dir):
        files = os.listdir(model_dir)
        #remove non weight files
        files = [file for file in files if '.pt' in file]
        if len(files) > 1:
            epoch = max([int(re.findall(r'\d+', file)[0]) for file in files])
            net.load_state_dict(torch.load(model_file+str(epoch)+'.pt', map_location=torch.device('cuda')))
            print("\tLoaded weights from epoch", epoch)
        else:
            print("\tNo weights found")
            f = open(info_file, "w")
            f.close()

        
    if os.path.exists(optimizer_file+str(epoch)+'.pt'):
        optimizer.load_state_dict(torch.load(optimizer_file+str(epoch)+'.pt'))
        print("\tLoaded optimizer from epoch", epoch)
        scheduler.load_state_dict(torch.load(scheduler_file+str(epoch)+'.pt'))
        print("\tLoaded scheduler from epoch", epoch)

    print("\tStarting Training:")
    patience_counter = 0
    min_val_loss = 1000000
    best_model = None
    
    for e in tqdm(range(epoch, epochs)):

        train_loss = training_step(net, train_loader, optimizer, cost_function, device)
        val_loss = test_step(net, val_loader, cost_function, device)

        scheduler.step(val_loss)

        print('Epoch: {:d}'.format(e+1))
        print('\tTraining loss {:.5f}'.format(train_loss))
        print('\tValidation loss {:.5f}'.format(val_loss))
        print('-----------------------------------------------------')

        if (e+1) % save_every == 0:
            torch.save(net.state_dict(), model_file+str(e+1)+'.pt')
            torch.save(optimizer.state_dict(), optimizer_file+str(e+1)+'.pt')
            torch.save(scheduler.state_dict(), scheduler_file+str(e+1)+'.pt')
        
        #write information to file
        f = open(info_file, "a")
        f.write('Epoch: {:d}\n'.format(e+1))
        f.write('\tTraining loss {:.5f}\n'.format(train_loss))
        f.write('\tValidation loss {:.5f}\n'.format(val_loss))
        f.write('-----------------------------------------------------\n')
        f.close()

        writer.add_scalar(tensorboard_tag+'/Loss/train', train_loss, e+1)
        writer.add_scalar(tensorboard_tag+'/Loss/val', val_loss, e+1)
        writer.add_scalar(tensorboard_tag+'/lr', optimizer.param_groups[0]["lr"] , e+1)
        writer.flush()

        if e > 0:
            if val_loss > min_val_loss:
                patience_counter += 1
            else:
                patience_counter = 0
                min_val_loss = val_loss
                best_model = deepcopy(net)
        
        if patience_counter >= patience:
            print("Early stopping")
            break
    
    if (best_model):
        torch.save(best_model.state_dict(), model_file+str(e+1)+'.pt')
    else:
        best_model = net

    print('After training:')
    train_loss = test_step(best_model, train_loader, cost_function, device)
    val_loss = test_step(best_model, val_loader, cost_function, device)
    test_loss = test_step(best_model, test_loader, cost_function, device)

    print('\tTraining loss {:.5f}'.format(train_loss))
    print('\tValidation loss {:.5f}'.format(val_loss))
    print('\tTest loss {:.5f}'.format(test_loss))

    #write information to file
    f = open(info_file, "a")
    f.write('After training:\n')
    f.write('\tTraining loss {:.5f}\n'.format(train_loss))
    f.write('\tValidation loss {:.5f}\n'.format(val_loss))
    f.write('\tTest loss {:.5f}\n'.format(test_loss))
    f.write('-----------------------------------------------------\n')
    f.close()

    
    writer.add_scalar(tensorboard_tag+'/final_train_loss', train_loss, 0)
    writer.add_scalar(tensorboard_tag+'/final_val_loss', val_loss, 0)
    writer.add_scalar(tensorboard_tag+'/final_test_loss', test_loss, 0)
    writer.flush()

    writer.close()
