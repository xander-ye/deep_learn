#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by yetongxue<yeli.studio@qq.com> 
# 2018/3/28

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

mnist=input_data.read_data_sets('MNIST_data',one_hot=True)


#输入图片规格28x28
#输入一行，一行有28个数据
n_inputs=28
#一共28行
max_time=28

#隐藏层单元
lstm_size=100
#10个分类
n_classes=10

#每个批次50个样本
batch_size=50
#一共多少个批次
n_batch=mnist.train.num_examples//batch_size


x=tf.placeholder(tf.float32,[None,784])
y=tf.placeholder(tf.float32,[None,10])

weights=tf.Variable(tf.truncated_normal([lstm_size,n_classes],stddev=0.1))
biases=tf.Variable(tf.constant(0.1,shape=[n_classes]))


# RNN网络

def RNN(X, weights, biases):
    inputs = tf.reshape(X, [-1, max_time, n_inputs])
    # 定义LSTM基本cell
    lstm_cell = tf.nn.rnn_cell.BasicLSTMCell(lstm_size)

    # final_state[0]:cell state
    # final_state[1]:hidden_state
    outputs, final_state = tf.nn.dynamic_rnn(lstm_cell, inputs, dtype=tf.float32)

    results = tf.nn.softmax(tf.matmul(final_state[1], weights) + biases)
    return results


prediction = RNN(x, weights, biases)
loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(labels=y, logits=prediction))
train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)
correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(prediction, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for epoch in range(5):
        for batch in range(n_batch):
            batch_xs, batch_ys = mnist.train.next_batch(batch_size)
            sess.run(train_step, feed_dict={x: batch_xs, y: batch_ys})

        acc = sess.run(accuracy, feed_dict={x: mnist.test.images, y: mnist.test.labels})
        print('Tter %s,Test accuracy:%s' % (epoch, acc))

"""
Tter 0,Test accuracy:0.6695
Tter 1,Test accuracy:0.8293
Tter 2,Test accuracy:0.878
Tter 3,Test accuracy:0.9005
Tter 4,Test accuracy:0.9048
"""