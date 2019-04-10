import os
import tensorflow as tf
from ClassFiles.networks import UNet
import ClassFiles.ut as ut
# from ClassFiles.ut import fftshift_tf
from ClassFiles.ut import normalize_tf

IMAGE_SIZE = (None, 96, 96, 96, 1)
FOURIER_SIZE = (None, 96, 96, 49, 1)


def data_augmentation_default(gt, adv):
    return gt, adv


class Denoiser(object):

    def __init__(self, path, data_augmentation=data_augmentation_default):

        self.path = path
        self.network = UNet()
        self.sess = tf.InteractiveSession()
        self.run_options = tf.RunOptions(report_tensor_allocations_upon_oom=True)

        ut.create_single_folder(self.path + '/Data')
        ut.create_single_folder(self.path + '/Logs')

        ### Training the denoiser ###
        self.data = tf.placeholder(shape=IMAGE_SIZE, dtype=tf.float32)
        self.true = tf.placeholder(shape=IMAGE_SIZE, dtype=tf.float32)
        self.learning_rate = tf.placeholder(dtype=tf.float32)

        # Network outputs
        self.true_normed, self.data_normed = data_augmentation(normalize_tf(self.true),
                                                     normalize_tf(self.data))
        self.denoised = self.network.net(self.data_normed)

        # Loss
        self.loss = 0.5 * tf.reduce_sum((self.true_normed - self.denoised) ** 2)

        # Optimizer
        self.global_step = tf.Variable(0, name='global_step', trainable=False)
        self.optimizer = tf.train.AdamOptimizer().minimize(self.loss, global_step=self.global_step)

        # Logging tools
        summary_list = []
        with tf.name_scope('Network_Optimization'):
            summary_list.append(tf.summary.scalar('Loss', self.loss))
 #           l.append(tf.summary.scalar('Data_Difference', self.wasserstein_loss))
 #           l.append(tf.summary.scalar('Lipschitz_Regulariser', self.regulariser_was))
 #           l.append(tf.summary.scalar('Overall_Net_Loss', self.loss_was))
 #           l.append(tf.summary.scalar('Norm_Input_true', tf.norm(self.true)))
 #           l.append(tf.summary.scalar('Norm_Input_adv', tf.norm(self.gen)))
 #           l.append(tf.summary.scalar('Norm_Gradient', tf.norm(self.gradient)))
            with tf.name_scope('Maximum_Projection'):
                summary_list.append(tf.summary.image('Noisy', tf.reduce_max(self.data_normed, axis=3), max_outputs=1))
                summary_list.append(tf.summary.image('Ground Truth', tf.reduce_max(self.true_normed, axis=3), max_outputs=1))
#                l.append(tf.summary.image('Gradient_Adv', tf.reduce_max(tf.abs(self.gradient), axis=3), max_outputs=1))
#                l.append(tf.summary.image('Gradient_GT', tf.reduce_max(tf.abs(gradient_track), axis=3), max_outputs=1))
            slice = int(IMAGE_SIZE[3]/2)
            with tf.name_scope('Slice_Projection'):
                summary_list.append(tf.summary.image('Noisy', self.data_normed[..., slice, :], max_outputs=1))
                summary_list.append(tf.summary.image('Ground Truth', self.true_normed[..., slice, :], max_outputs=1))
 #               l.append(tf.summary.image('Gradient_Adv', self.gradient[..., slice, :],  max_outputs=1))
 #               l.append(tf.summary.image('Gradient_GT', gradient_track[..., slice, :], max_outputs=1))

            self.merged_network = tf.summary.merge(summary_list)

        # set up the logger
        self.writer = tf.summary.FileWriter(self.path + '/Logs/Network_Optimization/')

        # initialize Variables
        tf.global_variables_initializer().run()

        # load existing saves
        self.load()

    def evaluate(self, data):
        return self.denoised.eval(feed_dict={self.data: data})

    def train(self, groundTruth, noisy, learning_rate=1):
        groundTruth = ut.unify_form(groundTruth)
        noisy = ut.unify_form(noisy)
        self.sess.run(self.optimizer,
                      feed_dict={self.true: groundTruth,
                                 self.data: noisy,
                                 self.learning_rate: learning_rate})

    # Input as in 'train', but writes results to tensorboard instead
    def test(self, groundTruth, noisy):
        groundTruth = ut.unify_form(groundTruth)
        noisy = ut.unify_form(noisy)
        merged, step = self.sess.run([self.merged_network, self.global_step],
                                     feed_dict={self.true: groundTruth,
                                                self.data: noisy})
        self.writer.add_summary(merged, global_step=step)

    def save(self):
        saver = tf.train.Saver()
        saver.save(self.sess, self.path + '/Data/model',
                   global_step=self.global_step)
        print('Progress saved')

    def load(self):
        saver = tf.train.Saver()
        if os.listdir(self.path + '/Data/'):
            saver.restore(self.sess,
                          tf.train.latest_checkpoint(self.path + '/Data/'))
            print('Save restored')
        else:
            print('No save found')

    def end(self):
        tf.reset_default_graph()
        self.sess.close()
