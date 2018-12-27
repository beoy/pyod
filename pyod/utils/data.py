# -*- coding: utf-8 -*-
"""Utility functions for manipulating data
"""
# Author: Yue Zhao <yuezhao@cs.toronto.edu>
# License: BSD 2 clause

from __future__ import division
from __future__ import print_function

import numpy as np

from sklearn.utils import column_or_1d
from sklearn.utils import check_random_state
from sklearn.utils import check_consistent_length
from sklearn.metrics import roc_auc_score

from .utility import precision_n_scores

MAX_INT = np.iinfo(np.int32).max


def _generate_data(n_inliers, n_outliers, n_features, coef, offset,
                   random_state):
    """Internal function to generate data samples.

    Parameters
    ----------
    n_inliers : int
        The number of inliers.

    n_outliers : int
        The number of outliers.

    n_features : int
        The number of features (dimensions).

    coef : float in range [0,1)+0.001
        The coefficient of data generation.

    offset : int
        Adjust the value range of Gaussian and Uniform.

    random_state : int, RandomState instance or None, optional (default=None)
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by `np.random`.

    Returns
    -------
    X : numpy array of shape (n_train, n_features)
        Data.

    y : numpy array of shape (n_train,)
        Ground truth.
    """

    inliers = coef * random_state.randn(n_inliers, n_features) + offset
    outliers = random_state.uniform(low=-1 * offset, high=offset,
                                    size=(n_outliers, n_features))
    X = np.r_[inliers, outliers]

    y = np.r_[np.zeros((n_inliers,)), np.ones((n_outliers,))]

    return X, y


def get_outliers_inliers(X, y):
    """Internal method to separate inliers from outliers.

    Parameters
    ----------
    X : numpy array of shape (n_samples, n_features)
        The input samples

    y : list or array of shape (n_samples,)
        The ground truth of input samples.

    Returns
    -------
    X_outliers : numpy array of shape (n_samples, n_features)
        Outliers.

    X_inliers : numpy array of shape (n_samples, n_features)
        Inliers.

    """
    X_outliers = X[np.where(y == 1)]
    X_inliers = X[np.where(y == 0)]
    return X_outliers, X_inliers


def generate_data(n_train=1000, n_test=500, n_features=2, contamination=0.1,
                  train_only=False, offset=10, random_state=None):
    """Utility function to generate synthesized data.
    Normal data is generated by a multivariate Gaussian distribution and
    outliers are generated by a uniform distribution.

    Parameters
    ----------
    n_train : int, (default=1000)
        The number of training points to generate.

    n_test : int, (default=500)
        The number of test points to generate.

    n_features : int, optional (default=2)
        The number of features (dimensions).

    contamination : float in (0., 0.5), optional (default=0.1)
        The amount of contamination of the data set, i.e.
        the proportion of outliers in the data set. Used when fitting to
        define the threshold on the decision function.

    train_only : bool, optional (default=False)
        If true, generate train data only.

    offset : int, optional (default=10)
        Adjust the value range of Gaussian and Uniform.

    random_state : int, RandomState instance or None, optional (default=None)
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by `np.random`.

    Returns
    -------
    X_train : numpy array of shape (n_train, n_features)
        Training data.

    y_train : numpy array of shape (n_train,)
        Training ground truth.

    X_test : numpy array of shape (n_test, n_features)
        Test data.

    y_test : numpy array of shape (n_test,)
        Test ground truth.

    """

    # initialize a random state and seeds for the instance
    random_state = check_random_state(random_state)
    offset_ = random_state.randint(low=offset)
    coef_ = random_state.random_sample() + 0.001  # in case of underflow

    n_outliers_train = int(n_train * contamination)
    n_inliers_train = int(n_train - n_outliers_train)

    X_train, y_train = _generate_data(n_inliers_train, n_outliers_train,
                                      n_features, coef_, offset_, random_state)

    if train_only:
        return X_train, y_train

    n_outliers_test = int(n_test * contamination)
    n_inliers_test = int(n_test - n_outliers_test)

    X_test, y_test = _generate_data(n_inliers_test, n_outliers_test,
                                    n_features, coef_, offset_, random_state)

    return X_train, y_train, X_test, y_test


def get_color_codes(y):
    """Internal function to generate color codes for inliers and outliers.
    Inliers (0): blue; Outlier (1): red.

    Parameters
    ----------
    y : list or numpy array of shape (n_samples,)
        The ground truth. Binary (0: inliers, 1: outliers).

    Returns
    -------
    c : numpy array of shape (n_samples,)
        Color codes.

    """
    y = column_or_1d(y)

    # inliers are assigned blue
    c = np.full([len(y)], 'b', dtype=str)
    outliers_ind = np.where(y == 1)

    # outlier are assigned red
    c[outliers_ind] = 'r'

    return c


def evaluate_print(clf_name, y, y_pred):
    """Utility function for evaluating and printing the results for examples.
    Default metrics include ROC and Precision @ n

    Parameters
    ----------
    clf_name : str
        The name of the detector.

    y : list or numpy array of shape (n_samples,)
        The ground truth. Binary (0: inliers, 1: outliers).

    y_pred : list or numpy array of shape (n_samples,)
        The raw outlier scores as returned by a fitted model.

    """

    y = column_or_1d(y)
    y_pred = column_or_1d(y_pred)
    check_consistent_length(y, y_pred)

    print('{clf_name} ROC:{roc}, precision @ rank n:{prn}'.format(
        clf_name=clf_name,
        roc=np.round(roc_auc_score(y, y_pred), decimals=4),
        prn=np.round(precision_n_scores(y, y_pred), decimals=4)))
