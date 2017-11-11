"""
The dataloading and processing units.
Di Wu follows the tutorial below. (Di Wu used a lot of customized function,
which in respect may not be the optimal sollution.
http://pytorch.org/tutorials/beginner/data_loading_tutorial.html#dataset-class
"""
from __future__ import print_function, division
import os
import random
from skimage import io, transform
from scipy.misc import imresize
import numpy as np

from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader
import matplotlib
# matplotlib.use('TkAgg')
# from matplotlib import pyplot as plt
# from torchvision import transforms as T
# Ignore warnings
import warnings

warnings.filterwarnings("ignore")


class Rescale(object):
    """Rescale the image in a sample to a given size.

    Args:
        output_size (tuple or tuple): Desired output size. If tuple, output is
            matched to output_size. If int, smaller of image edges is matched
            to output_size keeping aspect ratio the same.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, (int, tuple))
        self.output_size = output_size

    def __call__(self, sample):
        image, label = sample['image'], sample['label']

        h, w = image.shape[:2]
        if isinstance(self.output_size, int):
            if h > w:
                new_h, new_w = self.output_size * h / w, self.output_size
            else:
                new_h, new_w = self.output_size, self.output_size * w / h
        else:
            new_h, new_w = self.output_size

        new_h, new_w = int(new_h), int(new_w)

        image = transform.resize(image, (new_h, new_w))
        label = imresize(label, size=(new_h, new_w), interp='nearest', mode='F')

        return {'image': image, 'label': label}


class RandomCrop(object):
    """Crop randomly the image in a sample.

    Args:
        output_size (tuple or int): Desired output size. If int, square crop
            is made.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, (int, tuple))
        if isinstance(output_size, int):
            self.output_size = (output_size, output_size)
        else:
            assert len(output_size) == 2
            self.output_size = output_size

    def __call__(self, sample):
        image, label = sample['image'], sample['label']

        h, w = image.shape[:2]
        new_h, new_w = self.output_size

        top = np.random.randint(0, h - new_h)
        left = np.random.randint(0, w - new_w)

        image = image[top: top + new_h,
                left: left + new_w]

        label = label[top: top + new_h,
                left: left + new_w]

        return {'image': image, 'label': label}


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample):
        image, label = sample['image'], sample['label']

        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        image = image.transpose((2, 0, 1))
        image_tensor = torch.from_numpy(image)
        image_tensor = image_tensor.float().div(255)
        return {'image': image_tensor,
                'label': torch.from_numpy(label)}


class RandomHorizontalFlip(object):
    """Randomly horizontally flips the given PIL.Image with a probability of 0.5
    """

    def __call__(self, image, label):
        if random.random() < 0.5:
            results = [image.transpose(Image.FLIP_LEFT_RIGHT),
                       label.transpose(Image.FLIP_LEFT_RIGHT)]
        else:
            results = [image, label]
        return results

class Normalize(object):
    """Given mean: (R, G, B) and std: (R, G, B),
    will normalize each channel of the torch.*Tensor, i.e.
    channel = (channel - mean) / std
    """

    def __init__(self, mean, std):
        self.mean = torch.FloatTensor(mean)
        self.std = torch.FloatTensor(std)

    def __call__(self, image, label=None):
        img = image['image']
        label = image['label']
        for t, m, s in zip(img, self.mean, self.std):
            t.sub_(m).div_(s)
        if label is None:
            return image,
        else:
            return {'image': img, 'label': label.long()}

class Dataset_Generators_Synthia():
    """ Initially we use synthia dataset"""

    def __init__(self, cf):
        self.cf = cf
        # Load training set
<<<<<<< HEAD
        print('\n > Loading training, valid, test set, train_rand set')
        dataloaders_single = {x: ImageDataGenerator_Synthia(
            root_dir=os.path.join(cf.dataset_path, x),
            transform=T.Compose([
                RandomCrop(cf.random_size_crop),
                ToTensor(),
                Normalize(self.cf.rgb_mean, self.cf.rgb_std)
            ]),
            error_images=self.cf.error_images)
            # for x in ['train', 'valid', 'test', 'train_rand']}
            for x in ['train_rand']}

        # self.dataloader['train'] = DataLoader(dataset=dataloaders_single['train'],
        #                                       batch_size=cf.batch_size_train,
        #                                       shuffle=cf.shuffle_train,
        #                                       num_workers=cf.dataloader_num_workers_train)
        # self.dataloader['valid'] = DataLoader(dataset=dataloaders_single['valid'],
        #                                       batch_size=cf.batch_size_valid,
        #                                       shuffle=cf.shuffle_valid,
        #                                       num_workers=cf.dataloader_num_workers_valid)
        # self.dataloader['test'] = DataLoader(dataset=dataloaders_single['test'],
        #                                      batch_size=cf.batch_size_test,
        #                                      shuffle=cf.shuffle_test,
        #                                      num_workers=cf.dataloader_num_workers_test)
        self.dataloader['train_rand'] = DataLoader(dataset=dataloaders_single['train_rand'],
                                             batch_size=cf.batch_size_train,
                                             shuffle=cf.shuffle_train,
                                             num_workers=cf.dataloader_num_workers_train)


class ImageDataGenerator_Synthia(Dataset):
    """ Image Data"""

    def __init__(self, root_dir, transform=None, error_images=None):
=======
        print('\n > Loading training, valid, test set')
        train_dataset = ImageDataGenerator_Synthia(cf.dataset_path, 'train', cf=cf, crop=True, flip=True)
        val_dataset = ImageDataGenerator_Synthia(cf.dataset_path, 'valid', cf=cf, crop=False, flip=False)
        self.train_loader = DataLoader(train_dataset, batch_size=cf.batch_size, shuffle=True, num_workers=cf.workers, pin_memory=True)
        self.val_loader = DataLoader(val_dataset, batch_size=1, num_workers=cf.workers, pin_memory=True)


class ImageDataGenerator_Synthia(Dataset):
    def __init__(self, root_dir, dataset_split, cf, crop=True, flip=True):
>>>>>>> 419d28c4e27b82c4cfef6a3aa01425cf29929973
        """
        :param root_dir: Directory will all the images
        :param label_dir: Directory will all the label images
        :param transform:  (callable, optional): Optional tra
        nsform to be applied
        """
<<<<<<< HEAD
        if (root_dir[-10:] == 'train_rand'):
            self.root_dir = root_dir
            self.image_dir = os.path.join(root_dir[:-10], 'RGB')
            self.image_files = os.listdir(self.image_dir)
            if error_images is not None:
                for error in error_images:
                    if os.path.exists(os.path.join(self.image_dir, error)):
                        self.image_files.remove(error)

            self.label_dir = os.path.join(root_dir[:-10], 'GTTXT')
            self.label_files = os.listdir(self.label_dir)
            self.transform = transform
        else:
            self.root_dir = root_dir
            self.image_dir = os.path.join(root_dir, 'images')
            self.image_files = os.listdir(self.image_dir)
            self.label_dir = os.path.join(root_dir, 'masks')
            self.label_files = os.listdir(self.label_dir)
            self.transform = transform

    def __len__(self):
        return len(self.image_files)
=======
        self.root_dir = root_dir
        # with open(os.path.join(root_dir, 'ALL.txt')) as text_file:  # can throw FileNotFoundError
        #     lines = tuple(l.split() for l in text_file.readlines())
        self.image_dir = os.path.join(root_dir, 'RGB')
        self.label_dir = os.path.join(root_dir, 'GTTXT')
        image_files = sorted(os.listdir(self.image_dir))
        # if img_name not in ['ap_000_02-11-2015_18-02-19_000062_3_Rand_2.png',
        #                     'ap_000_02-11-2015_18-02-19_000129_2_Rand_16.png',
        #                     'ap_000_01-11-2015_19-20-57_000008_1_Rand_0.png']
        train_num = int(len(image_files) * cf.train_ratio)
        if dataset_split == 'train':
            self.image_files = image_files[:train_num]
            self.image_num = train_num
            print('Total training number is: %d'%train_num)
        elif dataset_split == 'valid':
            self.image_files = image_files[train_num:]
            self.image_num = len(image_files) - train_num
            print('Total valid number is: %d' % self.image_num)
        self.crop = crop
        self.crop_size = cf.crop_size
        self.flip = flip
        self.mean = cf.rgb_mean
        self.std = cf.rgb_std
        self.ignore_index = cf.ignore_index

    def __len__(self):
        return self.image_num
>>>>>>> 419d28c4e27b82c4cfef6a3aa01425cf29929973

    def __getitem__(self, item):
        # Load images and perform augmentations with PIL
        img_name = os.path.join(self.image_dir, self.image_files[item])
<<<<<<< HEAD
        # print ('-------')
        # print (img_name)
        image = io.imread(img_name)
        label_name = os.path.join(self.label_dir, self.image_files[item][:-4] + '.txt')
=======
>>>>>>> 419d28c4e27b82c4cfef6a3aa01425cf29929973

        try:
            input = Image.open(img_name)
        except IOError:
            # unfortunately, some images are corrupted. Hence, we need to manually exclude them.
            print("Image failed loading: ", img_name)

        label_name = os.path.join(self.label_dir, self.image_files[item][:-4] + '.txt')
        try:
            with open(label_name) as text_file:  # can throw FileNotFoundError
                lines = tuple(l.split() for l in text_file.readlines())
        except IOError:
            # unfortunately, some images are corrupted. Hence, we need to manually exclude them.
            print("Label failed loading: ", img_name)

        target = np.asarray(lines).astype('int32')
        target[target == -1] = 0
        target[target == 0] = self.ignore_index
        target = np.array(target).astype('uint8')
        target = Image.fromarray(target)

        # Random uniform crop
        if self.crop:
            w, h = input.size
            x1, y1 = random.randint(0, w - self.crop_size), random.randint(0, h - self.crop_size)
            try:
                input, target = input.crop((x1, y1, x1 + self.crop_size, y1 + self.crop_size)), \
                                target.crop((x1, y1, x1 + self.crop_size, y1 + self.crop_size))
            except IOError:
                # unfortunately, some images are corrupted. Hence, we need to manually exclude them.
                print("image failed loading: ", img_name)
                # ap_000_01-11-2015_19-20-57_000008_1_Rand_0.png
        # Random horizontal flip
        if self.flip:
            if random.random() < 0.5:
                input, target = input.transpose(Image.FLIP_LEFT_RIGHT), target.transpose(Image.FLIP_LEFT_RIGHT)

        # Convert to tensors
        w, h = input.size
        input_t = torch.ByteTensor(torch.ByteStorage.from_buffer(input.tobytes())).view(h, w, 3).permute(2, 0, 1).float().div(255)
        target_t = torch.ByteTensor(torch.ByteStorage.from_buffer(target.tobytes())).view(h, w).long()
        # Normalise input
        input_t[0].sub_(self.mean[0]).div_(self.std[0])
        input_t[1].sub_(self.mean[1]).div_(self.std[1])
        input_t[2].sub_(self.mean[2]).div_(self.std[2])

<<<<<<< HEAD
        label_tensor = sample['label']
        label_tensor_clone = label_tensor.clone()
        label_tensor_clone[label_tensor == -1] = 0
        return sample['image'], label_tensor_clone
=======
        return input_t, target_t
>>>>>>> 419d28c4e27b82c4cfef6a3aa01425cf29929973


class Dataset_Generators_Cityscape():
    """ Initially we use synthia dataset"""

    def __init__(self, cf):
        self.cf = cf

        # Load training set
        print('\n > Loading training, valid, test set')
        # train_dataset = CityscapesDataset(cf=cf, split='train', transform=T.Compose([RandomCrop(cf.random_size_crop),
        #                                                                              RandomHorizontalFlip(),
        #                                                                              ToTensor(),
        #                                                                              T.Normalize(mean=cf.mean, std=cf.std)]))
        train_dataset = CityscapesDataset(cf=cf, split='train', crop=True, flip=True)
        val_dataset = CityscapesDataset(cf=cf, split='val', crop=False, flip=False)
        test_dataset = CityscapesDataset(cf=cf, split='test', crop=False, flip=False)
        self.train_loader = DataLoader(train_dataset, batch_size=cf.batch_size, shuffle=True, num_workers=cf.workers, pin_memory=True)
        self.val_loader = DataLoader(val_dataset, batch_size=1, num_workers=cf.workers, pin_memory=True)
        self.test_loader = DataLoader(test_dataset, batch_size=cf.batch_size, num_workers=cf.workers, pin_memory=True)


class CityscapesDataset(Dataset):
    def __init__(self, cf, split='train', crop=True, flip=True):
        super().__init__()
        self.crop = crop
        self.crop_size = cf.crop_size
        self.flip = flip
        self.inputs = []
        self.targets = []
        self.num_classes = cf.num_classes
        self.full_to_train = cf.full_to_train
        self.train_to_full = cf.train_to_full
        self.full_to_colour = cf.full_to_colour
        self.mean = cf.mean
        self.std = cf.std
        #self.transform = transform

        for root, _, filenames in os.walk(os.path.join(cf.dataroot_dir, 'leftImg8bit', split)):
            for filename in filenames:
                if os.path.splitext(filename)[1] == '.png':
                    filename_base = '_'.join(filename.split('_')[:-1])
                    target_root = os.path.join(cf.dataroot_dir, 'gtFine', split, os.path.basename(root))
                    self.inputs.append(os.path.join(root, filename_base + '_leftImg8bit.png'))
                    self.targets.append(os.path.join(target_root, filename_base + '_gtFine_labelIds.png'))

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, i):
        # Load images and perform augmentations with PIL
        input, target = Image.open(self.inputs[i]), Image.open(self.targets[i])
        # Random uniform crop
        if self.crop:
            w, h = input.size
            x1, y1 = random.randint(0, w - self.crop_size), random.randint(0, h - self.crop_size)
            input, target = input.crop((x1, y1, x1 + self.crop_size, y1 + self.crop_size)), \
                            target.crop((x1, y1, x1 + self.crop_size, y1 + self.crop_size))
        # Random horizontal flip
        if self.flip:
            if random.random() < 0.5:
                input, target = input.transpose(Image.FLIP_LEFT_RIGHT), target.transpose(Image.FLIP_LEFT_RIGHT)

        # Convert to tensors
        w, h = input.size

        input = torch.ByteTensor(torch.ByteStorage.from_buffer(input.tobytes())).view(h, w, 3).permute(2, 0, 1).float().div(255)
        target = torch.ByteTensor(torch.ByteStorage.from_buffer(target.tobytes())).view(h, w).long()
        # Normalise input
        input[0].sub_(self.mean[0]).div_(self.std[0])
        input[1].sub_(self.mean[1]).div_(self.std[1])
        input[2].sub_(self.mean[2]).div_(self.std[2])
        # Convert to training labels
        target_clone = target.clone()
        for k, v in self.full_to_train.items():
            target_clone[target == k] = v
        # Create one-hot encoding
        target_one_hot = torch.zeros(self.num_classes, h, w)
        for c in range(self.num_classes):
            target_one_hot[c][target_clone == c] = 1

        # TOD): dangerous hack below
        #target_clone[target == self.num_classes] = 0
        return input, target

