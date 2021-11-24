from torch.autograd import Variable
from PIL import Image
from torchvision.transforms import ToTensor
import argparse
import os
from models import *
from torchvision import transforms

import cv2
from math import log10, sqrt
from skimage.metrics import structural_similarity as compare_ssim
from skimage import measure

def toTensor(img):
    img = torch.from_numpy(img.transpose((2, 0, 1)))
    return img.float().div(255)

def cal_psnr(img1, img2):
    img1_np = np.array(img1)
    img2_np = np.array(img2)
    return measure.compare_psnr(img1_np, img2_np)

def PSNR(original, compressed):
    mse = np.mean((original - compressed) ** 2)
    if(mse == 0):  # MSE is zero means no noise is present in the signal .
                  # Therefore PSNR have no importance.
        return 100
    max_pixel = 1.0
    # max_pixel = 255.0
    try:
        psnr = 20 * log10(max_pixel / sqrt(mse))
    except:
        psnr = 38
    return psnr

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--testset_dir', type=str, default='./data/test/')
    parser.add_argument('--scale_factor', type=int, default=4)
    parser.add_argument('--device', type=str, default='cuda:0')
    parser.add_argument('--model_name', type=str, default='PASSRnet_4x')
    return parser.parse_args()


def test(cfg):
    net = PASSRnet(cfg.scale_factor).to(cfg.device)
    pretrained_dict = torch.load('./log/x' + str(cfg.scale_factor) + '/PASSRnet_x' + str(cfg.scale_factor) + '.pth')
    net.load_state_dict(pretrained_dict)

    file_list = os.listdir(cfg.testset_dir + cfg.dataset + '/lr_x' + str(cfg.scale_factor))
    psnr = 0
    score = 0
    fr_counter = 0
    net.eval()

    for idx in range(len(file_list)):
        LR_left1 = cv2.imread(cfg.testset_dir + cfg.dataset + '/lr_x' + str(cfg.scale_factor) + '/' + file_list[idx]  + '/3/'+ '/lr0.png')
        LR_left = Image.open(cfg.testset_dir + cfg.dataset + '/lr_x' + str(cfg.scale_factor) + '/' + file_list[idx]  + '/3/'+ '/lr0.png')
        LR_right = Image.open(cfg.testset_dir + cfg.dataset + '/lr_x' + str(cfg.scale_factor) + '/' + file_list[idx] + '/3/'+ '/lr1.png')
        LR_left, LR_right = ToTensor()(LR_left), ToTensor()(LR_right)
        LR_left, LR_right = LR_left.unsqueeze(0), LR_right.unsqueeze(0)
        LR_left, LR_right = Variable(LR_left).to(cfg.device), Variable(LR_right).to(cfg.device)
        scene_name = file_list[idx]
        SR_left = LR_left
        # SR_left = cv2.resize(LR_left[0].permute(1,2,0).cpu().detach().numpy(), (0,0), fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        SR_left = cv2.resize(LR_left[0].permute(1,2,0).cpu().detach().numpy(), (0,0), fx=4, fy=4)
        SR_right = cv2.resize(LR_right[0].permute(1,2,0).cpu().detach().numpy(), (0,0), fx=4, fy=4)
        # SR_left = np.clip(SR_left, 0, 1)

        print('Running Scene ' + scene_name + ' of ' + cfg.dataset + ' Dataset......')
        # with torch.no_grad():
        #     SR_left = net(LR_left, LR_right, is_training=0)
        #     SR_left = torch.clamp(SR_left, 0, 1)
        # save_path = './results/' + cfg.model_name + '/' + cfg.dataset
        # if not os.path.exists(save_path):
        #     os.makedirs(save_path)
        # SR_left_img = transforms.ToPILImage()(torch.squeeze(SR_left.data.cpu(), 0))
        # SR_left_img.save(save_path + '/' + scene_name + '_L.png')
        # SR_right_img = transforms.ToPILImage()(torch.squeeze(SR_right.data.cpu(), 0))
        # SR_right_img.save(save_path + '/' + scene_name + '_R.png')


        hr0_path = cfg.testset_dir + cfg.dataset + '/hr' + '/'+file_list[idx]+ '/hr0.png'
        hr1_path = cfg.testset_dir + cfg.dataset + '/hr' + '/'+file_list[idx]+ '/hr1.png'
        hr_01 = cv2.imread(hr0_path)
        SR_left1 = cv2.resize(LR_left1, (0,0), fx=4, fy=4)
        # psnr_value03 = PSNR(hr_01, SR_left1)
        # psnr_value03 = cal_psnr(hr_01, SR_left1)

        hr0 = Image.open(hr0_path)
        hr0 = np.array(hr0,  dtype=np.float32)
        hr0 = Variable(toTensor(hr0))

        hr1 = Image.open(hr1_path)
        hr1 = np.array(hr1,  dtype=np.float32)
        hr1 = Variable(toTensor(hr1))

        psnr_value0 = PSNR(hr0.permute(1,2,0).cpu().detach().numpy(), SR_left)
        # psnr_value0 = PSNR(hr1.permute(1,2,0).cpu().detach().numpy(), SR_right)
        # psnr_value1 = PSNR(hr1.cpu().detach().numpy(), SR_right.cpu().detach().numpy())
        psnr += psnr_value0

        grayA = cv2.cvtColor(hr0.permute(1,2,0).cpu().detach().numpy(), cv2.COLOR_BGR2GRAY)
        grayAA = cv2.cvtColor(hr1.permute(1,2,0).cpu().detach().numpy(), cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(SR_left, cv2.COLOR_BGR2GRAY)
        # grayBB = cv2.cvtColor(SR_right[0].permute(1,2,0).cpu().detach().numpy(), cv2.COLOR_BGR2GRAY)

        score0 = compare_ssim(grayA, grayB, data_range=grayA.max() - grayA.min())
        # score2 = compare_ssim(grayAA, grayBB, data_range=grayAA.max() - grayAA.min())
        score += score0




        fr_counter += 1
        final_psnr = psnr / fr_counter
        print("psnr_value: ", (psnr_value0))
        print("avg_psnr_value: ", final_psnr)

        final_ssim = score / fr_counter
        print("ssim_value: ", score0)
        print("avg_ssim_value: ", final_ssim)

if __name__ == '__main__':
    cfg = parse_args()
    dataset_list = ['Flickr1024']
    for i in range(len(dataset_list)):
        cfg.dataset = dataset_list[i]
        test(cfg)
    print('Finished!')
