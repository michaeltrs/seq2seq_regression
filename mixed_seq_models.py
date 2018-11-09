from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from basic_models import BasicModel

from model_utils import stacked_lstm, temp_res_conv_network, cnn_audio_model2d, cnn_audio_model3
from transformer_model import SelfAttentionEncoder


class CNNRNNModel(BasicModel):
    """

    """
    def __init__(self, options):
        super(CNNRNNModel, self).__init__(options=options)
        if self.is_training:
            self.train_era_step = self.options['train_era_step']
            self.build_train_graph()
        else:
            self.build_train_graph()
        self.make_savers()

    def build_train_graph(self):
        # if self.options['has_encoder']:
        with tf.variable_scope('encoder'):
            self.encoder_out = temp_res_conv_network(self.encoder_inputs, self.options)

        # if self.options['has_decoder']:
        with tf.variable_scope('decoder'):
            self.decoder_outputs, _ = stacked_lstm(
                    num_layers=self.options['decoder_num_layers'],
                    num_hidden=self.options['decoder_num_hidden'],
                    input_forw=self.encoder_out,
                    layer_norm=self.options['decoder_layer_norm'],
                    dropout_keep_prob=self.options['decoder_dropout_keep_prob'],
                    is_training=True,
                    residual=self.options['residual_decoder'],
                    use_peepholes=True,
                    return_cell=False)
            self.decoder_outputs = tf.layers.dense(
                    inputs=self.decoder_outputs,
                    units=self.options['num_classes'], activation=None, use_bias=True,
                    kernel_initializer=tf.keras.initializers.he_normal(seed=None),
                    bias_initializer=tf.zeros_initializer(),
                    kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None,
                    kernel_constraint=None, bias_constraint=None, trainable=True,
                    name=None, reuse=None)
        self.define_loss()
        self.define_training_params()


class CNNRNNModel2d(BasicModel):
    """
    cnn + lstm model with cnn kernels similar to nvidia paper
    """
    def __init__(self, options):
        super(CNNRNNModel2d, self).__init__(options=options)
        fmel = tf.reshape(self.noisy_mel_spectr[0], (-1, 21, 128))
        fmel = tf.expand_dims(fmel, 3)
        dfmel = tf.reshape(self.noisy_mel_spectr[1], (-1, 21, 128))
        dfmel = tf.expand_dims(dfmel, 3)
        d2fmel = tf.reshape(self.noisy_mel_spectr[2], (-1, 21, 128))
        d2fmel = tf.expand_dims(d2fmel, 3)
        self.new_encoder_inputs = tf.concat([fmel, dfmel, d2fmel], axis=3)
        if self.is_training:
            self.train_era_step = self.options['train_era_step']
            self.build_train_graph()
        else:
            self.build_train_graph()
        self.make_savers()

    def build_train_graph(self):
        # if self.options['has_encoder']:
        with tf.variable_scope('encoder'):
            self.encoder_out = cnn_audio_model2d(self.new_encoder_inputs, self.options['batch_size'])
            print("enc_out", self.encoder_out)
        # if self.options['has_decoder']:
        with tf.variable_scope('decoder'):
            self.decoder_outputs, _ = stacked_lstm(
                    num_layers=self.options['decoder_num_layers'],
                    num_hidden=self.options['decoder_num_hidden'],
                    input_forw=self.encoder_out,
                    layer_norm=self.options['decoder_layer_norm'],
                    dropout_keep_prob=self.options['decoder_dropout_keep_prob'],
                    is_training=True,
                    residual=self.options['residual_decoder'],
                    use_peepholes=True,
                    return_cell=False)
            print("dec_out", self.decoder_outputs)
            self.decoder_outputs = tf.layers.dense(
                    inputs=self.decoder_outputs,
                    units=self.options['num_classes'], activation=None, use_bias=True,
                    kernel_initializer=tf.keras.initializers.he_normal(seed=None),
                    bias_initializer=tf.zeros_initializer(),
                    kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None,
                    kernel_constraint=None, bias_constraint=None, trainable=True,
                    name=None, reuse=None)
            print("dec_out2", self.decoder_outputs)
        self.define_loss()
        self.define_training_params()


class CNNRNNModel3(BasicModel):
    """
    cnn + lstm model with cnn kernels similar to nvidia paper
    """
    def __init__(self, options):
        super(CNNRNNModel3, self).__init__(options=options)
        self.encoder_inputs = tf.reshape(self.encoder_inputs, (self.options['batch_size'], -1, 128, 3))
        if self.is_training:
            self.train_era_step = self.options['train_era_step']
            self.build_train_graph()
        else:
            self.build_train_graph()
        self.make_savers()

    def build_train_graph(self):
        # if self.options['has_encoder']:
        with tf.variable_scope('encoder'):
            self.encoder_out = cnn_audio_model3(self.encoder_inputs, self.options['batch_size'])
            print("enc_out", self.encoder_out)
        # if self.options['has_decoder']:
        with tf.variable_scope('decoder'):
            self.decoder_outputs, _ = stacked_lstm(
                    num_layers=self.options['decoder_num_layers'],
                    num_hidden=self.options['decoder_num_hidden'],
                    input_forw=self.encoder_out,
                    layer_norm=self.options['decoder_layer_norm'],
                    dropout_keep_prob=self.options['decoder_dropout_keep_prob'],
                    is_training=True,
                    residual=self.options['residual_decoder'],
                    use_peepholes=True,
                    return_cell=False)
            print("dec_out", self.decoder_outputs)
            self.decoder_outputs = tf.layers.dense(
                    inputs=self.decoder_outputs,
                    units=self.options['num_classes'], activation=None, use_bias=True,
                    kernel_initializer=tf.keras.initializers.he_normal(seed=None),
                    bias_initializer=tf.zeros_initializer(),
                    kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None,
                    kernel_constraint=None, bias_constraint=None, trainable=True,
                    name=None, reuse=None)
            print("dec_out2", self.decoder_outputs)
        self.define_loss()
        self.define_training_params()
class TransRNNModel(BasicModel):
    """

    """
    def __init__(self, options):
        super(TransRNNModel, self).__init__(options=options)
        # additional tensors for seq2seq
        self.decoder_inputs = tf.identity(self.target_labels)[:, :-1, :]
        self.decoder_inputs_lengths = tf.identity(self.target_labels_lengths) - 1
        self.target_labels = tf.identity(self.target_labels)[:, 1:, :]
        self.target_labels_lengths = tf.identity(self.target_labels_lengths) - 1
        if self.is_training:
            self.train_era_step = self.options['train_era_step']
            self.build_train_graph()
        else:
            self.build_train_graph()
        self.make_savers()

    def build_train_graph(self):
        # if self.options['has_encoder']:
        with tf.variable_scope('encoder'):
            transformer_encoder = SelfAttentionEncoder(self.options)
            self.encoder_out = transformer_encoder.encoder_outputs

            # if self.options['has_decoder']:
            with tf.variable_scope('decoder'):
                self.decoder_outputs = stacked_lstm(
                    num_layers=self.options['decoder_num_layers'],
                    num_hidden=self.options['decoder_num_hidden'],
                    input_forw=self.encoder_out,
                    layer_norm=self.options['decoder_layer_norm'],
                    dropout_keep_prob=self.options['decoder_dropout_keep_prob'],
                    is_training=True,
                    residual=self.options['residual_decoder'],
                    use_peepholes=True,
                    return_cell=False)

        self.define_loss()
        self.define_training_params()