import numpy as np
from scipy.interpolate import splev, splrep

import matplotlib.pyplot as plt
from scipy.interpolate import splev, splrep
import itertools

if __name__ == '__main__':

    # x = np.linspace(0, 10, 10)
    # x =  np.array([0, 1.11111111, 2.22222222, 3.33333333, 4.44444444, 5.55555556, 6.66666667, 7.77777778, 8.88888889, 10])
    # y = np.sin(x)
    # tck = splrep(x, y)
    # x2 = np.linspace(0, 10, 200)
    # y2 = splev(x2, tck)
    # plt.plot(x, y, 'o', x2, y2)
    # plt.show()
    #
    # x = np.linspace(0, 10, 10)
    # y = np.sin(x)
    # print('Hello world',x)

    c = 0
    x = np.zeros((10,10))
    for i,j in itertools.product(range(10),range(10)):
        x[i][j] = c
        c += 1

    y = np.zeros((10,10))
    # Rotate matrix
    for i, j in itertools.product(range(10), range(10)):
        y[j][i] = x[i][j]
        # x[j][i] = x[i][j] In place rotation

    print(x)
    print(y)