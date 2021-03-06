import os
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from code_base.tools.kalman_filtering import kalman_xy
from filterpy.kalman import KalmanFilter


def get_img_list(valid_data, test_data):

    valid_img_list = []
    for d in valid_data:
        item_list = [x[6] for x in d]
        valid_img_list.append(item_list)

    test_img_list = []
    for d in test_data:
        item_list = [x[6] for x in d]
        test_img_list.append(item_list)

    return  valid_img_list, test_img_list


def get_data_with_img_list(valid_data, test_data):
    valid_data_array = np.array(valid_data[:, :, :6]).astype('float')
    test_data_array = np.array(test_data[:, :, :6]).astype('float')
    return  valid_data_array, test_data_array


def prepare_data_image_list(cf):
    import pickle
    with open(os.path.join(cf['trajectory_path'], cf['sequence_name'] + '_valid.npy'), 'rb') as fp:
        valid_data = pickle.load(fp)
    with open(os.path.join(cf['trajectory_path'], cf['sequence_name'] + '_test.npy'), 'rb') as fp:
        test_data = pickle.load(fp)

    valid_data_array, test_data_array = get_data_with_img_list(valid_data, test_data)
    valid_img_list, test_img_list = get_img_list(valid_data, test_data)

    return  valid_data_array, test_data_array, valid_img_list, test_img_list


def ssd_2d(x, y):
    s = 0
    for i in range(2):
        s += (x[i] - y[i]) ** 2
    return np.sqrt(s)


def calc_rect_int_2d(A, B):
    leftA = [a[0] - a[2] / 2 for a in A]
    bottomA = [a[1] - a[3] / 2 for a in A]
    rightA = [a[0] + a[2]/2 for a in A]
    topA = [a[1] + a[3]/2 for a in A]

    leftB = [b[0] - b[2] / 2 for b in B]
    bottomB = [b[1] - b[3] / 2 for b in B]
    rightB = [b[0] + b[2] / 2 for b in B]
    topB = [b[1] + b[3] / 2 for b in B]

    overlap = []
    length = min(len(leftA), len(leftB))
    for i in range(length):
        tmp = (max(0, min(rightA[i], rightB[i]) - max(leftA[i], leftB[i]) + 1)
               * max(0, min(topA[i], topB[i]) - max(bottomA[i], bottomB[i]) + 1))
        areaA = A[i][2] * A[i][3]
        areaB = B[i][2] * B[i][3]
        overlap.append(tmp / float(areaA + areaB - tmp))

    return overlap


def kalman_xy():

    data_array = np.load('/media/samsumg_1tb/synthia/prepared_data_shuffle.npy')
    test_data_array = data_array[2]
    data_mean = data_array[3]
    data_std = data_array[4]
    test_data_array = (test_data_array * data_std) + data_mean

    print('Finish Loading. Test array shape: ' + str(test_data_array.shape))
    test_pred = np.zeros(shape=(len(test_data_array), 8, 6))
    test_pred[:, :, 4:] = test_data_array[:, -8:, 4:]

    for f, data in enumerate(test_data_array):
        if f % 100 == 0:
            print("process batch %d" %f)
        measurements = [[d[0], d[1]] for d in data[:15]]

        kf = KalmanFilter(dim_x=4, dim_z=2)
        # Assign the initial value for the state (position and velocity).
        # You can do this with a two dimensional array like so:
        # pos_x, pos_y, vel_x, vel_y
        kf.x = np.array([measurements[0][0], measurements[0][1], 0, 0])
        # Define the state transition matrix:
        kf.F = np.array([[1., 0., 1., 0.],
                        [0., 1., 0., 1.],
                        [0., 0., 1., 0.],
                        [0., 0., 0., 1.]])
        # Define the measurement function:
        kf.H = np.array([[1., 0., 0., 0.], [0., 1., 0., 0.]])
        # Define the covariance matrix. Here I take advantage of the fact that P already contains np.eye(dim_x),
        # and just multiply by the uncertainty:
        kf.P *= 1

        for t in range(1, 15):
            kf.predict()
            kf.update([measurements[t][0], measurements[t][1]])

        for t in range(8):
            kf.predict()
            next_x = kf.x
            test_pred[f, t, 0] = next_x[0]
            test_pred[f, t, 1] = next_x[1]
            test_pred[f, t, 2] = test_data_array[f, 14, 2]  # we set the width to be fixed
            test_pred[f, t, 3] = test_data_array[f, 14, 3]  # we set the width to be fixed

    totalerrCoverage = 0
    totalerrCenter = 0
    Kalman_valid_errCenter = []
    Kalman_valid_iou_2d = []
    for i in range(len(test_pred)):
        res = test_pred[i]
        anno = test_data_array[i, -8:, :]
        center = [[r[0], r[1]] for r in res]
        centerGT = [[r[0], r[1]] for r in anno]
        seq_length = len(centerGT)
        errCenter = [ssd_2d(center[i], centerGT[i]) for i in range(len(centerGT))]
        Kalman_valid_errCenter.append(errCenter)
        iou_2d = calc_rect_int_2d(res, anno)
        Kalman_valid_iou_2d.append(iou_2d)
        for s in range(seq_length):
            totalerrCenter += errCenter[s]
            totalerrCoverage += iou_2d[s]

    aveErrCoverage = totalerrCoverage / (len(Kalman_valid_errCenter) * float(seq_length))
    aveErrCenter = totalerrCenter / (len(Kalman_valid_errCenter) * float(seq_length))
    print('aveErrCoverage: %.4f, aveErrCenter: %.2f  ' %(aveErrCoverage, aveErrCenter))
    # P: aveErrCoverage: 0.6174, aveErrCenter: 31.11

    result_dir = '/media/samsumg_1tb/cvpr_DTA_Results/kalman_filter'
    np.save(os.path.join(result_dir, 'Kalman_valid_errCenter.npy'), Kalman_valid_errCenter)
    np.save(os.path.join(result_dir, 'Kalman_valid_iou_2d.npy'), Kalman_valid_iou_2d)


def unscented_kalman_filter():
    from filterpy.kalman import UnscentedKalmanFilter as UKF
    from filterpy.kalman import MerweScaledSigmaPoints
    from filterpy.common import Q_discrete_white_noise
    data_array = np.load('/media/samsumg_1tb/synthia/prepared_data_shuffle.npy')
    test_data_array = data_array[2]
    data_mean = data_array[3]
    data_std = data_array[4]
    test_data_array = (test_data_array * data_std) + data_mean

    print('Finish Loading. Test array shape: ' + str(test_data_array.shape))
    test_pred = np.zeros(shape=(len(test_data_array), 8, 6))
    test_pred[:, :, 4:] = test_data_array[:, -8:, 4:]

    def f_cv(x, dt):
        """ state transition function for a
        constant velocity aircraft"""

        F = np.array([[1, 0, dt, 0],
                      [0, 1, 0, dt],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]])
        return np.dot(F, x)

    def h_cv(x):
        return np.array([x[0], x[1]])

    dt = 1.0
    sigmas = MerweScaledSigmaPoints(4, alpha=.1, beta=2., kappa=1.)
    for f, data in enumerate(test_data_array):
        if f % 100 == 0:
            print("process batch %d" %f)
        measurements = [[d[0], d[1]] for d in data[:15]]

        ukf = UKF(dim_x=4, dim_z=2, fx=f_cv, hx=h_cv, dt=dt, points=sigmas)
        ukf.x = np.array([measurements[0][0], measurements[0][1], 0, 0])
        # ukf.R = np.diag([0.09, 0.09])
        # ukf.Q[0:2, 0:2] = Q_discrete_white_noise(2, dt=1, var=0.02)
        # ukf.Q[2:4, 2:4] = Q_discrete_white_noise(2, dt=1, var=0.02)
        for t in range(1, 15):
            ukf.predict()
            ukf.update([measurements[t][0], measurements[t][1]])

        for t in range(8):
            ukf.predict()
            next_x = ukf.x
            test_pred[f, t, 0] = next_x[0]
            test_pred[f, t, 1] = next_x[1]
            test_pred[f, t, 2] = test_data_array[f, 14, 2]  # we set the width to be fixed
            test_pred[f, t, 3] = test_data_array[f, 14, 3]  # we set the width to be fixed

    totalerrCoverage = 0
    totalerrCenter = 0
    Kalman_valid_errCenter = []
    Kalman_valid_iou_2d = []
    for i in range(len(test_pred)):
        res = test_pred[i]
        anno = test_data_array[i, -8:, :]
        center = [[r[0], r[1]] for r in res]
        centerGT = [[r[0], r[1]] for r in anno]
        seq_length = len(centerGT)
        errCenter = [ssd_2d(center[i], centerGT[i]) for i in range(len(centerGT))]
        Kalman_valid_errCenter.append(errCenter)
        iou_2d = calc_rect_int_2d(res, anno)
        Kalman_valid_iou_2d.append(iou_2d)
        for s in range(seq_length):
            totalerrCenter += errCenter[s]
            totalerrCoverage += iou_2d[s]

    aveErrCoverage = totalerrCoverage / (len(Kalman_valid_errCenter) * float(seq_length))
    aveErrCenter = totalerrCenter / (len(Kalman_valid_errCenter) * float(seq_length))
    print('aveErrCoverage: %.4f, aveErrCenter: %.2f  ' %(aveErrCoverage, aveErrCenter))
    # P: aveErrCoverage: 0.6174, aveErrCenter: 31.11

    result_dir = '/media/samsumg_1tb/cvpr_DTA_Results/kalman_filter'
    np.save(os.path.join(result_dir, 'Kalman_valid_errCenter.npy'), Kalman_valid_errCenter)
    np.save(os.path.join(result_dir, 'Kalman_valid_iou_2d.npy'), Kalman_valid_iou_2d)


def extended_kalman_filter():
    from filterpy.kalman import ExtendedKalmanFilter

    data_array = np.load('/media/samsumg_1tb/synthia/prepared_data_shuffle.npy')
    test_data_array = data_array[2]
    data_mean = data_array[3]
    data_std = data_array[4]
    test_data_array = (test_data_array * data_std) + data_mean

    print('Finish Loading. Test array shape: ' + str(test_data_array.shape))
    test_pred = np.zeros(shape=(len(test_data_array), 8, 6))
    test_pred[:, :, 4:] = test_data_array[:, -8:, 4:]

    def HJacobian_at(x):
        """ compute Jacobian of H matrix at x """

        return np.array([[0, 1., 0, 1]])

    def hx(x):
        """ compute measurement for slant range that
        would correspond to state x.
        """

        return x

    for f, data in enumerate(test_data_array):
        if f % 100 == 0:
            print("process batch %d" %f)
        measurements = [[d[0], d[1]] for d in data[:15]]

        ekf = ExtendedKalmanFilter(dim_x=4, dim_z=2)
        ekf.x = np.array([measurements[0][0], measurements[0][1], 0, 0])
        ekf.F = np.array([[1., 0., 1., 0.],
                         [0., 1., 0., 1.],
                         [0., 0., 1., 0.],
                         [0., 0., 0., 1.]])
        # Define the measurement function:
        ekf.H = np.array([[1., 0., 0., 0.], [0., 1., 0., 0.]])
        # Define the covariance matrix. Here I take advantage of the fact that P already contains np.eye(dim_x),
        # and just multiply by the uncertainty:
        ekf.P *= 1
        for t in range(1, 15):
            ekf.predict()
            ekf.update([measurements[t][0], measurements[t][1]], HJacobian_at, hx)

        for t in range(8):
            ekf.predict()
            next_x = ekf.x
            test_pred[f, t, 0] = next_x[0]
            test_pred[f, t, 1] = next_x[1]
            test_pred[f, t, 2] = test_data_array[f, 14, 2]  # we set the width to be fixed
            test_pred[f, t, 3] = test_data_array[f, 14, 3]  # we set the width to be fixed

    totalerrCoverage = 0
    totalerrCenter = 0
    Kalman_valid_errCenter = []
    Kalman_valid_iou_2d = []
    for i in range(len(test_pred)):
        res = test_pred[i]
        anno = test_data_array[i, -8:, :]
        center = [[r[0], r[1]] for r in res]
        centerGT = [[r[0], r[1]] for r in anno]
        seq_length = len(centerGT)
        errCenter = [ssd_2d(center[i], centerGT[i]) for i in range(len(centerGT))]
        Kalman_valid_errCenter.append(errCenter)
        iou_2d = calc_rect_int_2d(res, anno)
        Kalman_valid_iou_2d.append(iou_2d)
        for s in range(seq_length):
            totalerrCenter += errCenter[s]
            totalerrCoverage += iou_2d[s]

    aveErrCoverage = totalerrCoverage / (len(Kalman_valid_errCenter) * float(seq_length))
    aveErrCenter = totalerrCenter / (len(Kalman_valid_errCenter) * float(seq_length))
    print('aveErrCoverage: %.4f, aveErrCenter: %.2f  ' %(aveErrCoverage, aveErrCenter))
    # P: aveErrCoverage: 0.6174, aveErrCenter: 31.11

    result_dir = '/media/samsumg_1tb/cvpr_DTA_Results/kalman_filter'
    np.save(os.path.join(result_dir, 'Kalman_valid_errCenter.npy'), Kalman_valid_errCenter)
    np.save(os.path.join(result_dir, 'Kalman_valid_iou_2d.npy'), Kalman_valid_iou_2d)


# Entry point of the script
if __name__ == "__main__":
    extended_kalman_filter()