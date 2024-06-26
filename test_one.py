import time
import torch
import argparse
import torch.nn as nn
from torch.utils.data import DataLoader
from val_data_functions import ValData,Custom_ValData,MyValData
from utils import validation, validation_val,custom_valildation_val,custom_save_image
import os
import numpy as np
import random
from transweather_model import Transweather
from PIL import Image
from torchvision.transforms import Compose, ToTensor,Normalize

# --- Parse hyper-parameters  --- #
# parser = argparse.ArgumentParser(description='Hyper-parameters for network')
# parser.add_argument('-val_batch_size', help='Set the validation/test batch size', default=1, type=int)
# parser.add_argument('-exp_name', help='directory for saving the networks of the experiment', type=str)
# parser.add_argument('-seed', help='set random seed', default=19, type=int)
# args = parser.parse_args()

val_batch_size = 1
exp_name = 'Transweather'

# #set seed
# seed = args.seed
# if seed is not None:
#     np.random.seed(seed)
#     torch.manual_seed(seed)
#     torch.cuda.manual_seed(seed)
#     random.seed(seed) 
#     print('Seed:\t{}'.format(seed))

# --- Set category-specific hyper-parameters  --- #
val_data_dir = 'data/test/test_anything/input/'
     
# --- Gpu device --- #             
device_ids = [Id for Id in range(torch.cuda.device_count())]
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)


# --- Validation data loader --- #

#val_filename = 'model_test.txt' ## This text file should contain all the names of the images and must be placed in ./data/test/ directory

#val_data_loader = DataLoader(Custom_ValData(val_data_dir,val_filename), batch_size=val_batch_size, shuffle=False, num_workers=0)
#val_data_loader = DataLoader(MyValData(val_data_dir), batch_size=val_batch_size, shuffle=False, num_workers=0)

# --- Define the network --- #

#net = Transweather().cuda()
net = Transweather().to(device)


net = nn.DataParallel(net, device_ids=device_ids)


# --- Load the network weight --- #
# net.load_state_dict(torch.load('./{}/best'.format(exp_name)))
net.load_state_dict(torch.load('./TransWeather_weights/best'.format(exp_name),map_location = torch.device('cpu')))


# --- Use the evaluation model in testing --- #
net.eval()
category = "testone"

if os.path.exists('./results/{}/{}/'.format(category,exp_name))==False:     
    os.makedirs('./results/{}/{}/'.format(category,exp_name))   


print('--- Testing starts! ---')
start_time = time.time()
#val_psnr, val_ssim = validation_val(net, val_data_loader, device, exp_name,category, save_tag=True)
img_names = os.listdir(val_data_dir)
img_names.remove('.DS_Store')
#print("Img Names",img_names)
for img_name in img_names:
    #print(img_name)
    #img = os.path.join(val_data_dir,img_name)
    input_img = Image.open(os.path.join(val_data_dir,img_name))
    # gt_img = Image.open(self.val_data_dir + gt_name)

    # Resizing image in the multiple of 16"
    wd_new,ht_new = input_img.size
    if ht_new>wd_new and ht_new>1024:
        wd_new = int(np.ceil(wd_new*1024/ht_new))
        ht_new = 1024
    elif ht_new<=wd_new and wd_new>1024:
        ht_new = int(np.ceil(ht_new*1024/wd_new))
        wd_new = 1024
    wd_new = int(16*np.ceil(wd_new/16.0))
    ht_new = int(16*np.ceil(ht_new/16.0))
    input_img = input_img.resize((wd_new,ht_new),Image.LANCZOS)
    # gt_img = gt_img.resize((wd_new, ht_new), Image.LANCZOS)

    # --- Transform to tensor --- #
    transform_input = Compose([ToTensor(), Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    transform_gt = Compose([ToTensor()])
    input_im = transform_input(input_img)
    input_im = input_im.to(device)
    input_im = input_im.unsqueeze(0)
    pred_image = net(input_im)
    custom_save_image(pred_image, img_name, exp_name,category)

end_time = time.time() - start_time
#print('val_psnr: {0:.2f}, val_ssim: {1:.4f}'.format(val_psnr, val_ssim))
print('validation time is {0:.4f}'.format(end_time))
