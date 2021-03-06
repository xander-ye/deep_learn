#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by yetongxue<yeli.studio@qq.com> 
# 2018/6/28


# 获取数据

import os
import glob
import numpy as np
from tensorflow.python.platform import gfile
import tensorflow as tf

FLOWER_PHOTOS_PATH = 'flower_photos'
TRAIN_ACCOUNT = 3000

NUM_CLASS = 5
OUTPUT_FILE_TRAIN = 'flower_photos/train_datasets.npy'
OUTPUT_FILE_TEST = 'flower_photos/test_datasets.npy'

DECODE_JPEG_CONTENTS = 'DecodeJpeg/contents:0'
POOL_3_RESHAPE_NAME = 'pool_3/_reshape:0'

# 读取inception-v3.pd
INCEPTION_V3_PD = 'tmp/inception_v3/classify_image_graph_def.pb'

IS_TEST = False


def get_datasets():
    sub_dirs = [_[0] for _ in os.walk(FLOWER_PHOTOS_PATH)][1:]
    images = []

    """
    flower_photos/daisy 0
    flower_photos/dandelion 1
    flower_photos/roses 2
    flower_photos/sunflowers 3
    flower_photos/tulips 4
    """
    labels = []

    for index, sub_dir in enumerate(sub_dirs):
        file_names = glob.glob(sub_dir + '/*.jpg')
        images.extend(file_names)
        labels.extend(np.full(len(file_names), index))

        if IS_TEST:
            images = images[:5]
            labels = labels[:5]
            break

    # 乱序
    state = np.random.get_state()
    np.random.shuffle(images)
    np.random.set_state(state)
    np.random.shuffle(labels)

    """
    ['flower_photos/tulips/3909355648_42cb3a5e09_n.jpg',
    'flower_photos/tulips/5634767665_0ae724774d.jpg',
    'flower_photos/dandelion/17482158576_86c5ebc2f8.jpg',
    'flower_photos/tulips/16265876844_0a149c4f76.jpg',
    'flower_photos/dandelion/344318990_7be3fb0a7d.jpg']
    """
    return images, labels


# 将数据转化成自定义全连接网络可用数据

def labels2one_hot(labels):
    one_hot = np.eye(NUM_CLASS, dtype=int)
    labels_one_hot = map(lambda x: list(one_hot[x]), labels)
    return labels_one_hot


def get_pool_3_reshape_values(sess, images):
    """
    :param images 图片路径数组
    通过inception-v3，将图片处理成pool_3_reshape数据，以供自定义全连接网络训练使用
    """
    with tf.gfile.FastGFile(INCEPTION_V3_PD, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())

        decode_jpeg_contents_tensor, pool_3_reshape_tensor = tf.import_graph_def(
            graph_def,
            return_elements=[DECODE_JPEG_CONTENTS, POOL_3_RESHAPE_NAME]
        )
    print decode_jpeg_contents_tensor, pool_3_reshape_tensor

    images_2048 = []
    for path in images:
        img = get_pool_3_reshape_sigal_image_values(sess, pool_3_reshape_tensor, path)
        images_2048.append(img)

    return images_2048


def get_pool_3_reshape_sigal_image_values(sess, pool3_reshape_tensor, image_path):
    image_raw_data = gfile.FastGFile(image_path, 'rb').read()
    #     image_data=tf.image.decode_jpeg(image_raw_data)

    """
    注意获取到的tensor会默认加上import/，在feed_dict时候需要加上否则
    计算图上无法找到
    """
    pool3_reshape_value = sess.run(pool3_reshape_tensor, feed_dict={
        'import/DecodeJpeg/contents:0': image_raw_data
    })
    return pool3_reshape_value.tolist()


def get_images_2048(images):
    """
    通过inception-v3获取pool_3_reshape节点特征
    :param images: 图片路径
    :type images: array
    :return: array
    :rtype: [None,1,2048]
    """
    with tf.Session() as sess:
        images_2048 = get_pool_3_reshape_values(sess, images)
    return images_2048


if __name__ == '__main__':
    images, labels = get_datasets()

    images_2048 = get_images_2048(images)
    """
    images_2048.shape=[None,2048]
    labels.shape=[None,1]
    """
    train_datasets = np.asarray([images_2048[:TRAIN_ACCOUNT], labels[:TRAIN_ACCOUNT]])
    test_datasets = np.asarray([images_2048[TRAIN_ACCOUNT:], labels[TRAIN_ACCOUNT:]])

    np.save(OUTPUT_FILE_TRAIN, train_datasets)
    np.save(OUTPUT_FILE_TEST, test_datasets)


# 以下为获取数据代码

class lazy(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        val = self.func(instance)
        setattr(instance, self.func.__name__, val)
        return val


class Datasets(object):
    def __init__(self, is_train):
        self._index_in_epoch = 0
        self._datasets_path = OUTPUT_FILE_TRAIN if is_train else OUTPUT_FILE_TEST
        self._images = self._datasets[0]
        self._labels = self._datasets[1]
        self._num_examples = len(self._labels)

    @property
    def datasets(self):
        images = map(lambda x: np.squeeze(x), self._images)
        labels = labels2one_hot(self._labels)
        return images, labels

    @lazy
    def _datasets(self):
        images, labels = np.load(self._datasets_path)

        # images=map(lambda x: np.squeeze(x), images)
        # labels=labels2one_hot(labels)
        return images, labels

    def next_batch(self, batch_size):
        start = self._index_in_epoch
        self._index_in_epoch += batch_size

        if self._index_in_epoch > self._num_examples:
            perm = np.arange(self._num_examples)
            np.random.shuffle(perm)
            self._images = self._images[perm]
            self._labels = self._labels[perm]

            start = 0
            self._index_in_epoch = batch_size
            assert batch_size <= self._num_examples

        end = self._index_in_epoch
        _images = map(lambda x: np.squeeze(x), self._images[start:end])
        _labels = labels2one_hot(self._labels[start:end])
        return _images, _labels
