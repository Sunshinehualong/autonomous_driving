import os

# Keras imports
from metrics.metrics import cce_flatt, IoU, YOLOLoss, YOLOMetrics, SSDLoss
from keras import backend as K
from keras.utils.vis_utils import plot_model

# Classification models
# from models.lenet import build_lenet
# from models.alexNet import build_alexNet
# from models.resnet import build_resnet50
# from models.inceptionV3 import build_inceptionV3
from models.vgg import build_vgg

# Detection models
from models.yolo import build_yolo

# Segmentation models
from models.fcn8 import build_fcn8
from models.segnet import build_segnet
from models.tiramisu import build_tiramisu
# from models.tiramisu_test import build_tiramisu
from models.ssd import build_ssd
# from models.unet import build_unet
# from models.resnetFCN import build_resnetFCN
# from models.densenetFCN import build_densenetFCN

# Adversarial models
# from models.adversarial_semseg import Adversarial_Semseg
from models.model import One_Net_Model

# Build the model
class Model_Factory():
    def __init__(self):
        pass

    # Define the input size, loss and metrics
    def basic_model_properties(self, cf, variable_input_size):
        # Define the input size, loss and metrics
        if cf.dataset.class_mode == 'categorical':
            if K.image_dim_ordering() == 'th':
                in_shape = (cf.dataset.n_channels,
                            cf.target_size_train[0],
                            cf.target_size_train[1])

            else:
                in_shape = (cf.target_size_train[0],
                            cf.target_size_train[1],
                            cf.dataset.n_channels)

            loss = 'categorical_crossentropy'
            metrics = ['accuracy']

        elif cf.dataset.class_mode == 'detection':
            if 'yolo' in cf.model_name:
                in_shape = (cf.dataset.n_channels,
                            cf.target_size_train[0],
                            cf.target_size_train[1])

                loss = YOLOLoss(in_shape, cf.dataset.n_classes, cf.dataset.priors)
                metrics = [YOLOMetrics(in_shape, cf.dataset.n_classes, cf.dataset.priors)]

            elif cf.model_name == 'ssd':
                in_shape = (cf.target_size_train[0],
                            cf.target_size_train[1],
                            cf.dataset.n_channels)
                loss = SSDLoss(cf.dataset.n_classes, neg_pos_ratio=2.0).compute_loss
                metrics = [] # TODO: There is no metrics for the ssd model

            else:
                raise ValueError('Uknown "' + cf.model_name + '" name for the ' + cf.dataset.class_mode + ' problem type.'
                                'Only is implemented for: {yolo, tiny-yolo, ssd}')

        elif cf.dataset.class_mode == 'segmentation':
            if K.image_dim_ordering() == 'th':
                if variable_input_size:
                    in_shape = (cf.dataset.n_channels, None, None)
                else:
                    in_shape = (cf.dataset.n_channels,
                                cf.target_size_train[0],
                                cf.target_size_train[1])

            else:
                if variable_input_size:
                    in_shape = (None, None, cf.dataset.n_channels)
                else:
                    in_shape = (cf.target_size_train[0],
                                cf.target_size_train[1],
                                cf.dataset.n_channels)


            loss = cce_flatt(cf.dataset.void_class, cf.dataset.cb_weights)
            metrics = [IoU(cf.dataset.n_classes, cf.dataset.void_class)]

            # if cf.model_name == 'fcn8':
            #     loss = cce_flatt(cf.dataset.void_class, cf.dataset.cb_weights)
            #     metrics = [IoU(cf.dataset.n_classes, cf.dataset.void_class)]
            #
            # elif 'segnet' in cf.model_name:
            #     loss = 'categorical_crossentropy'
            #     metrics = []
            #
            # else:
            #     raise ValueError('Uknown "'+cf.model_name+'" name for the '+cf.dataset.class_mode+' problem type.'
            #                     'Only is implemented for: {fc8, segnet}')

        else:
            raise ValueError('Unknown problem type')

        return in_shape, loss, metrics

    # Creates a Model object (not a Keras model)
    def make(self, cf, optimizer=None):
        if cf.model_name in ['lenet', 'alexNet', 'vgg16', 'vgg19', 'resnet50',
                             'InceptionV3', 'fcn8', 'unet', 'segnet_basic', 'segnet_vgg',
                             'resnetFCN', 'yolo', 'tiny-yolo', 'ssd', 'tiramisu']:

            if optimizer is None:
                raise ValueError('optimizer can not be None')

            in_shape, loss, metrics = self.basic_model_properties(cf, True)
            model = self.make_one_net_model(cf, in_shape, loss, metrics, optimizer)

        elif cf.model_name == 'adversarial_semseg':
            if optimizer is None:
                raise ValueError('optimizer is not None')

            # loss, metrics and optimizer are made in class Adversarial_Semseg
            in_shape, _, _ = self.basic_model_properties(cf, False)
            model = Adversarial_Semseg(cf, in_shape)

        else:
            raise ValueError('Unknown model name')

        # Output the model
        return model

    # Creates, compiles, plots and prints a Keras model. Optionally also loads its weights.
    def make_one_net_model(self, cf, in_shape, loss, metrics, optimizer):
        # Create the *Keras* model

        if 'tiramisu' in cf.model_name:
            input_rows, input_cols = cf.target_size_train[0], cf.target_size_train[1]
            multiple = 2 ** 5  # 5 transition blocks
            if input_rows is not None:
                if input_rows % multiple != 0:
                    raise ValueError('The number of rows of the input data must be a multiple of {}'.format(multiple))
            if input_cols is not None:
                if input_cols % multiple != 0:
                    raise ValueError(
                        'The number of columns of the input data must be a multiple of {}'.format(multiple))

        if cf.model_name == 'fcn8':
            model = build_fcn8(in_shape, cf.dataset.n_classes, cf.weight_decay,
                               freeze_layers_from=cf.freeze_layers_from,
                               #path_weights='weights/pascal-fcn8s-dag.mat')
                               path_weights=cf.load_imageNet)

        elif cf.model_name == 'unet':
            model = build_unet(in_shape, cf.dataset.n_classes, cf.weight_decay,
                               freeze_layers_from=cf.freeze_layers_from,
                               path_weights=None)

        elif cf.model_name == 'tiramisu':
            # model = build_tiramisu(in_shape, cf.dataset.n_classes, cf.weight_decay,
            #                        nb_filter=48, dropout=0.4, freeze_layers_from=None)

            model = build_tiramisu(in_shape, cf.dataset.n_classes, cf.weight_decay)

        elif cf.model_name == 'segnet_basic':
            model = build_segnet(in_shape, cf.dataset.n_classes, cf.weight_decay,
                                 freeze_layers_from=cf.freeze_layers_from,
                                 path_weights=None, basic=True)

        elif cf.model_name == 'segnet_vgg':
            model = build_segnet(in_shape, cf.dataset.n_classes, cf.weight_decay,
                                 freeze_layers_from=cf.freeze_layers_from,
                                 path_weights=None, basic=False)

        elif cf.model_name == 'resnetFCN':
            model = build_resnetFCN(in_shape, cf.dataset.n_classes, cf.weight_decay,
                                    freeze_layers_from=cf.freeze_layers_from,
                                    path_weights=None)

        elif cf.model_name == 'densenetFCN':
            model = build_densenetFCN(in_shape, cf.dataset.n_classes, cf.weight_decay,
                                      freeze_layers_from=cf.freeze_layers_from,
                                      path_weights=None)

        elif cf.model_name == 'lenet':
            model = build_lenet(in_shape, cf.dataset.n_classes, cf.weight_decay)

        elif cf.model_name == 'alexNet':
            model = build_alexNet(in_shape, cf.dataset.n_classes, cf.weight_decay)

        elif cf.model_name == 'vgg16':
            model = build_vgg(in_shape, cf.dataset.n_classes, 16, cf.weight_decay,
                              load_pretrained=cf.load_imageNet,
                              freeze_layers_from=cf.freeze_layers_from)

        elif cf.model_name == 'vgg19':
            model = build_vgg(in_shape, cf.dataset.n_classes, 19, cf.weight_decay,
                              load_pretrained=cf.load_imageNet,
                              freeze_layers_from=cf.freeze_layers_from)

        elif cf.model_name == 'resnet50':
            model = build_resnet50(in_shape, cf.dataset.n_classes, cf.weight_decay,
                                   load_pretrained=cf.load_imageNet,
                                   freeze_layers_from=cf.freeze_layers_from)

        elif cf.model_name == 'InceptionV3':
            model = build_inceptionV3(in_shape, cf.dataset.n_classes,
                                      cf.weight_decay,
                                      load_pretrained=cf.load_imageNet,
                                      freeze_layers_from=cf.freeze_layers_from)

        elif cf.model_name == 'yolo':
            model = build_yolo(in_shape, cf.dataset.n_classes,
                               cf.dataset.n_priors,
                               load_pretrained=cf.load_imageNet,
                               freeze_layers_from=cf.freeze_layers_from, tiny=False)

        elif cf.model_name == 'tiny-yolo':
            model = build_yolo(in_shape, cf.dataset.n_classes,
                               cf.dataset.n_priors,
                               load_pretrained=cf.load_imageNet,
                               freeze_layers_from=cf.freeze_layers_from, tiny=True)

        elif cf.model_name == 'ssd':
            print(in_shape)
            model = build_ssd(in_shape, cf.dataset.n_classes,
                               load_pretrained=cf.load_imageNet,
                               freeze_layers_from=cf.freeze_layers_from)
        else:
            raise ValueError('Unknown model')

        # Load pretrained weights
        if cf.load_pretrained:
            print('   loading model weights from: ' + cf.weights_file + '...')
            model.load_weights(cf.weights_file, by_name=True)

        # Compile model
        model.compile(loss=loss, metrics=metrics, optimizer=optimizer)

        # Show model structure
        if cf.show_model:
            model.summary()
            plot_model(model, to_file=os.path.join(cf.savepath, 'model_'+cf.model_name+'.png'))

        # Output the model
        print ('   Model: ' + cf.model_name)
        # model is a keras model, Model is a class wrapper so that we can have
        # other models (like GANs) made of a pair of keras models, with their
        # own ways to train, test and predict

        return One_Net_Model(model, cf, optimizer)