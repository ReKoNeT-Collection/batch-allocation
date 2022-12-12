from matplotlib import pyplot as plt
from scipy.stats import rv_histogram


def plot_histogram(histogram: rv_histogram):
    """
    Utility method for plotting a histogram.

    Parameters
    ----------
    histogram
        scipy histogram instance.
    """
    plt.hist(histogram._histogram[0], histogram._histogram[1], label='PDF')
    plt.show()
