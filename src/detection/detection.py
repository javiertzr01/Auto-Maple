"""A module for classifying directional arrows using TensorFlow."""

import cv2
import tensorflow as tf
import numpy as np
from src.common import utils # pylint: disable=import-error


#########################
#       Functions       #
#########################
def load_model():
    """
    Loads the saved model's weights into an Tensorflow model.
    :return:    The Tensorflow model object.
    """

    model_dir = 'assets/models/rune_model_rnn_grayed/saved_model'
    return tf.saved_model.load(model_dir)

def gray(image):
    """
    Grayscale the image
    :param image:   The input image.
    :return:        The color-filtered image.
    """

    grayed = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    grayed = cv2.cvtColor(grayed, cv2.COLOR_GRAY2BGR)

    return grayed

def preload_cudnn(model, image):
    """
    Preload cudnn for faster rune processing (javiertzr01)
    :param model:   The model object to use.
    :param image:   The input image.
    """

    image = gray(image)

    input_tensor = tf.convert_to_tensor(image)
    input_tensor = input_tensor[tf.newaxis, ...]

    model_fn = model.signatures['serving_default']
    model_fn(input_tensor)
    print("\nPreload cudNN Completed")

def run_inference_for_single_image(model, image):
    """
    Performs an inference once.
    :param model:   The model object to use.
    :param image:   The input image.
    :return:        The model's predictions including bounding boxes and classes.
    """

    input_tensor = tf.convert_to_tensor(image)
    input_tensor = input_tensor[tf.newaxis, ...]

    model_fn = model.signatures['serving_default']
    print(model_fn.structured_outputs)
    output_dict = model_fn(input_tensor)

    num_detections = int(output_dict.pop('num_detections'))
    output_dict = {key: value[0, :num_detections].numpy()
                   for key, value in output_dict.items()}
    output_dict['num_detections'] = num_detections

    # detection_classes should be ints
    output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)

    return output_dict

def sort_by_confidence(model, image):
    """
    Runs a single inference on the image and returns the best four classifications.
    :param model:   The model object to use.
    :param image:   The input image.
    :return:        The model's top four predictions.
    """

    threshold = 0.8

    output_dict = run_inference_for_single_image(model, image)
    zipped = list(zip(output_dict['detection_scores'],
                      output_dict['detection_boxes'],
                      output_dict['detection_classes']))
    pruned = [t for t in zipped if t[0] > threshold]
    pruned.sort(key=lambda x: x[0], reverse=True)
    result = pruned[:4]
    return result

@utils.run_if_enabled
def merge_detection(model, image):
    """
    Run two inferences: one on the upright image, and one on the image rotated 90 degrees.
    Only considers vertical arrows and merges the results of the two inferences together.
    (Vertical arrows in the rotated image are actually horizontal arrows).
    :param model:   The model object to use.
    :param image:   The input image.
    :return:        A list of four arrow directions.
    """

    label_map = {1: 'up', 2: 'down', 3: 'left', 4: 'right'}
    classes = []

    # Preprocessing
    height, width, channels = image.shape

    cropped = image[150:height//3, width//3:4*width//6]
    grayed = gray(cropped)

    # Isolate the rune box
    height, width, channels = grayed.shape
    lst = sort_by_confidence(model, grayed)
    lst.sort(key=lambda x: x[1][1])
    classes = [label_map[item[2]] for item in lst]

    return classes

# Script for testing the detection module by itself
# Testing script so it doesn't matter (javiertzr01)
if __name__ == '__main__':
    # from src.common import config, utils
    # config.enabled = True

    # MM_TL_TEMPLATE = cv2.imread('assets/minimap_tl_template.png', 0)
    # MM_BR_TEMPLATE = cv2.imread('assets/minimap_br_template.png', 0)

    # MMT_HEIGHT = max(MM_TL_TEMPLATE.shape[0], MM_BR_TEMPLATE.shape[0]) #22
    # MMT_WIDTH = max(MM_TL_TEMPLATE.shape[1], MM_BR_TEMPLATE.shape[1]) #37
    # monitor = {'top': 0, 'left': 0, 'width': 1366, 'height': 768}
    model = load_model()
    frame = cv2.imread('test.jpg')
    preload_cudnn(model, frame)
    while True:
        arrows = merge_detection(model, frame)
        print(arrows)
