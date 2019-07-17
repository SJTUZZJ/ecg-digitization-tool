import sys
import scipy
import cv2 as cv
import numpy as np
from scipy import ndimage
from matplotlib import pyplot as plt


class ECGdigitizer:
    def __init__(self):
        self.digitizer = None

    # Helper function to help display an oversized image
    def display_image(self, image, name):
        if image.shape[0] > 1000:
            image = cv.resize(image, (0, 0), fx=0.85, fy=0.85)
        cv.imshow(name, image)
        cv.waitKey(0)
        cv.destroyAllWindows()

    # Helper function to sharpen the image
    def sharpen(self, img):
        kernel = np.array([[0, -1, 0],
                           [-1, 5.5, -1],
                           [0, -1, 0]], np.float32)
        img = cv.filter2D(img, -1, kernel)
        return img

    # Helper function to increase contrast of an image
    def increase_contrast(self, img):
        lab_img = cv.cvtColor(img, cv.COLOR_RGB2LAB)
        l, a, b = cv.split(lab_img)
        clahe = cv.createCLAHE(clipLimit=4, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        img = cv.merge((cl, a, b))
        img = cv.cvtColor(img, cv.COLOR_LAB2RGB)
        return img

    # Helper function to crop the image and eliminate the borders
    def crop_image(self, image):
        mask = image > 0
        coords = np.argwhere(mask)
        x0, y0 = coords.min(axis=0)
        x1, y1 = coords.max(axis=0) + 1
        image = image[x0 + 200: x1 - 20, y0: y1]
        return image

    # Another helper function to crop and remove the borders
    def crop_image_v2(self, image, tolerance=0):
        mask = image > tolerance
        image = image[np.ix_(mask.any(1), mask.any(0))]
        return image

    # Helper function to distinguish different ECG signals on specific image
    def separate_components(self, image):
        ret, labels = cv.connectedComponents(image, connectivity=8)
        print(type(labels))

        # mapping component labels to hue value
        label_hue = np.uint8(179 * labels / np.max(labels))
        blank_ch = 255 * np.ones_like(label_hue)
        labeled_image = cv.merge([label_hue, blank_ch, blank_ch])
        labeled_image = cv.cvtColor(labeled_image, cv.COLOR_HSV2BGR)

        # set background label to white
        labeled_image[label_hue == 0] = 255
        return labeled_image
    
    # Helper function to display segmented ECG picture
    def display_segments(self, name, item, axis='off'):
        plt.figure(figsize=(12, 9))
        plt.imshow(item)
        plt.title(name)
        plt.axis(axis)
        plt.subplots_adjust(wspace=.05, left=.01, bottom=.01, right=.99, top=.9)
        plt.show()


def main():
    digitizer = ECGdigitizer()
    image_name = 'images/test4.jpeg'  # select image
    image = cv.imread(image_name, flags=cv.IMREAD_GRAYSCALE)  # read the image as GS

    # sanity check
    if image is None:
        print('Cannot open image: ' + image_name)
        sys.exit(0)
    digitizer.display_image(image, 'Original Image')
    
    cropped_image = digitizer.crop_image(image)
    digitizer.display_image(cropped_image, 'CROPPED')

    # blur the image slightly to get rid of some noise
    # blurred_image = cv.GaussianBlur(image, (3, 3), 0)
    # blurred_image = cv.medianBlur(blurred_image, 3)
    # digitizer.display_image(blurred_image, 'blurred')

    # # use adaptive thresholding to transform the image into a binary one
    binary_image = cv.bitwise_not(cropped_image)
    binary_image = cv.adaptiveThreshold(binary_image, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 101, 50)
    binary_image_inverted = cv.bitwise_not(binary_image)
    digitizer.display_image(binary_image, 'Binary Image')

    # # crop out the borders of the image
    # cropped_image = digitizer.crop_image(binary_image_inverted)
    # digitizer.display_image(cropped_image, 'Cropped Image')

    # # use dilation and erosion to fill the gaps and connect broken lines
    # kernel = np.ones((6, 6), np.uint8)
    # dilated_image = cv.dilate(cropped_image, kernel, iterations=1)
    # eroded_image = cv.erode(dilated_image, kernel, iterations=1)
    # digitizer.display_image(eroded_image, 'Processed Image')

    # # display the segmented image
    # labeled_image = digitizer.separate_components(binary_image_inverted)
    # digitizer.display_image(labeled_image, 'Labeled Image')

    structure = np.array([[1, 1, 1],
                          [1, 1, 1],
                          [1, 1, 1]], np.uint8)
    labels, nb = ndimage.label(binary_image_inverted, structure=structure)
    digitizer.display_segments('Labeled Image', labels)

    print('There are ' + str(np.amax(labels) + 1) + ' labeled components.')
    for i in range(np.amax(labels) + 1):
        sl = ndimage.find_objects(labels == i)
        print(sl[0])
        digitizer.display_segments('CCC', binary_image[sl[0]], 'on')
    # sl = ndimage.find_objects(labels == 100)
    # print(len(sl))
    # digitizer.display_segments('Cropped Connected Component', binary_image[sl[0]], 'on')


if __name__ == '__main__':
    main()
