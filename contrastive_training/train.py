import sys
sys.path.append(".")

from contrastive_training.simsiam.train import train_simsiam
from contrastive_training.simclr.train import train_simclr


def contrastive_train(simsiam, simclr, device='cuda', datasets=["panoptic"], models_dir="trained_models", datasets_dir="datasets"):
    if simclr["train"]:
        print("Training SimCLR")
        train_simclr(
            model_dir=models_dir,
            dataset_dir=datasets_dir,
            datasets=datasets,
            name = simclr["name"], 
            batch_size=simclr["batch_size"],
            device=device,
            learning_rate=simclr["learning_rate"],
            weight_decay=simclr["weight_decay"],
            momentum=simclr["momentum"],
            t=simclr["temperature"],
            epochs=simclr["epochs"],
            save_every = simclr["save_every"]
        )
        print("SimCLR training done")
    
    if simsiam["train"]:
        print("Training SimSiam")
        train_simsiam(
            model_dir=models_dir,
            dataset_dir=datasets_dir,
            datasets=datasets,
            name = simsiam["name"],
            batch_size=simsiam["batch_size"],
            device=device,
            learning_rate=simsiam["learning_rate"],
            weight_decay=simsiam["weight_decay"],
            momentum=simsiam["momentum"],
            epochs=simsiam["epochs"],
            save_every = simsiam["save_every"]
        )
        print("SimSiam training done")

def check_arguments_contrastive(args):
    #name is required
    assert 'name' in args, 'name not found for args'

    if 'train' not in args:
        args['train'] = True
    if 'batch_size' not in args:
        args['batch_size'] = 1024
    if 'learning_rate' not in args:
        args['learning_rate'] = 0.01
    if 'weight_decay' not in args:
        args['weight_decay'] = 0.000001
    if 'momentum' not in args:
        args['momentum'] = 0.9
    if 'temperature' not in args:
        args['temperature'] = 0.6
    if 'epochs' not in args:
        args['epochs'] = 100
    if 'save_every' not in args:
        args['save_every'] = 10
    
    return args

#TODO redo
def contrastive_pretraining(args, device='cuda', models_dir="trained_models", datasets_dir="datasets"):
    #skip if specified
    if args['skip']:
        print("Skipping contrastive training")
        return
    
    if 'datasets' not in args:
        args['datasets'] = ["panoptic"]

    print("Contrastive training")

    simsiam = args['simsiam']
    simclr = args['simclr']

    #check if all the required parameters are present, if so use default values
    simsiam = check_arguments_contrastive(simsiam)
    simclr = check_arguments_contrastive(simclr)

    contrastive_train(
        device=device, datasets=args['datasets'], models_dir=models_dir, datasets_dir=datasets_dir,
        simsiam=simsiam,
        simclr=simclr
    )


if __name__ == "__main__":
    contrastive_train()