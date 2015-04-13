# -*- coding: utf-8 -*-
"""
An implementation of the Principal Component Pursuit algorithm for robust PCA
as described in `Candes, Li, Ma, & Wright <http://arxiv.org/abs/0912.3599>`_.

An alternative Python implementation using non-standard dependencies and
different hyperparameter choices is available at:

http://blog.shriphani.com/2013/12/18/
    robust-principal-component-pursuit-background-matrix-recovery/

"""

from __future__ import division, print_function

__all__ = ["pcp"]

import logging
import numpy as np
from scipy.sparse.linalg import svds


def pcp(M, delta=1e-6, mu=None, maxiter=500, verbose=False):
    shape = M.shape

    # Initialize the tuning parameters.
    lam = 1.0 / np.sqrt(np.max(shape))
    if mu is None:
        mu = 0.25 * np.prod(shape) / np.sum(np.abs(M))

    # Convergence criterion.
    norm = np.sum(M ** 2)

    # Iterate.
    i = 0
    rank = np.min(shape)
    S = np.zeros(shape)
    Y = np.zeros(shape)
    while i < max(maxiter, 1):
        # SVD step.
        if rank >= np.min(shape):
            u, s, v = np.linalg.svd(M - S + Y / mu, full_matrices=False)
        else:
            u, s, v = svds(M - S + Y / mu, k=rank, tol=1.0/mu)

            # The sparse implementation returns the SVs in reverse order.
            u, s, v = u[:, ::-1], s[::-1], v[::-1, :]

        s = shrink(s, 1.0 / mu)
        rank = np.sum(s > 0.0)
        u, s, v = u[:, :rank], s[:rank], v[:rank, :]
        L = np.dot(u, np.dot(np.diag(s), v))

        # Shrinkage step.
        S = shrink(M - L + Y / mu, lam / mu)

        # Lagrange step.
        step = M - L - S
        Y += mu * step

        # Check for convergence.
        err = np.sqrt(np.sum(step ** 2) / norm)
        if verbose:
            print("Iteration {0}: error={1:.3e}, rank={2:d}"
                  .format(i, err, np.sum(s > 0)))
        if err < delta:
            break
        i += 1

    if i >= maxiter:
        logging.warn("convergence not reached in pcp")
    return L, S, (u, s, v)


def shrink(M, tau):
    sgn = np.sign(M)
    S = np.abs(M) - tau
    S[S < 0.0] = 0.0
    return sgn * S
