"""Basic tools for dense recursive polynomials in ``K[x]`` or ``K[X]``. """

from sympy.core import igcd, ilcm

from sympy.polys.monomialtools import (
    monomial_key, monomial_min, monomial_div
)

from sympy.polys.groebnertools import sdp_sort

from sympy.utilities import cythonized

import random

def poly_LC(f, K):
    """
    Return leading coefficient of ``f``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import poly_LC

    >>> poly_LC([], ZZ)
    0
    >>> poly_LC([ZZ(1), ZZ(2), ZZ(3)], ZZ)
    1

    """
    if not f:
        return K.zero
    else:
        return f[0]

def poly_TC(f, K):
    """
    Return trailing coefficient of ``f``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import poly_TC

    >>> poly_TC([], ZZ)
    0
    >>> poly_TC([ZZ(1), ZZ(2), ZZ(3)], ZZ)
    3

    """
    if not f:
        return K.zero
    else:
        return f[-1]

dup_LC = dmp_LC = poly_LC
dup_TC = dmp_TC = poly_TC

@cythonized("u")
def dmp_ground_LC(f, u, K):
    """
    Return ground leading coefficient.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_ground_LC

    >>> f = ZZ.map([[[1], [2, 3]]])

    >>> dmp_ground_LC(f, 2, ZZ)
    1

    """
    while u:
        f = dmp_LC(f, K)
        u -= 1

    return dup_LC(f, K)

@cythonized("u")
def dmp_ground_TC(f, u, K):
    """
    Return ground trailing coefficient.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_ground_TC

    >>> f = ZZ.map([[[1], [2, 3]]])

    >>> dmp_ground_TC(f, 2, ZZ)
    3

    """
    while u:
        f = dmp_TC(f, K)
        u -= 1

    return dup_TC(f, K)

@cythonized("u")
def dmp_true_LT(f, u, K):
    """
    Return leading term ``c * x_1**n_1 ... x_k**n_k``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_true_LT

    >>> f = ZZ.map([[4], [2, 0], [3, 0, 0]])

    >>> dmp_true_LT(f, 1, ZZ)
    ((2, 0), 4)

    """
    monom = []

    while u:
        monom.append(len(f) - 1)
        f, u = f[0], u - 1

    if not f:
        monom.append(0)
    else:
        monom.append(len(f) - 1)

    return tuple(monom), dup_LC(f, K)

def dup_degree(f):
    """
    Return leading degree of ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_degree

    >>> f = ZZ.map([1, 2, 0, 3])

    >>> dup_degree(f)
    3

    """
    return len(f) - 1

@cythonized("u")
def dmp_degree(f, u):
    """
    Return leading degree of ``f`` in ``x_0`` in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_degree

    >>> dmp_degree([[[]]], 2)
    -1

    >>> f = ZZ.map([[2], [1, 2, 3]])

    >>> dmp_degree(f, 1)
    1

    """
    if dmp_zero_p(f, u):
        return -1
    else:
        return len(f) - 1

@cythonized("v,i,j")
def _rec_degree_in(g, v, i, j):
    """Recursive helper function for :func:`dmp_degree_in`."""
    if i == j:
        return dmp_degree(g, v)

    v, i = v-1, i+1

    return max([ _rec_degree_in(c, v, i, j) for c in g ])

@cythonized("j,u")
def dmp_degree_in(f, j, u):
    """
    Return leading degree of ``f`` in ``x_j`` in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_degree_in

    >>> f = ZZ.map([[2], [1, 2, 3]])

    >>> dmp_degree_in(f, 0, 1)
    1
    >>> dmp_degree_in(f, 1, 1)
    2

    """
    if not j:
        return dmp_degree(f, u)
    if j < 0 or j > u:
        raise IndexError("-%s <= j < %s expected, got %s" % (u, u, j))

    return _rec_degree_in(f, u, 0, j)

@cythonized("v,i")
def _rec_degree_list(g, v, i, degs):
    """Recursive helper for :func:`dmp_degree_list`."""
    degs[i] = max(degs[i], dmp_degree(g, v))

    if v > 0:
        v, i = v-1, i+1

        for c in g:
            _rec_degree_list(c, v, i, degs)

@cythonized("u")
def dmp_degree_list(f, u):
    """
    Return a list of degrees of ``f`` in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_degree_list

    >>> f = ZZ.map([[1], [1, 2, 3]])

    >>> dmp_degree_list(f, 1)
    (1, 2)

    """
    degs = [-1]*(u+1)
    _rec_degree_list(f, u, 0, degs)
    return tuple(degs)

@cythonized("i")
def dup_strip(f):
    """
    Remove leading zeros from ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.densebasic import dup_strip

    >>> dup_strip([0, 0, 1, 2, 3, 0])
    [1, 2, 3, 0]

    """
    if not f or f[0]:
        return f

    i = 0

    for cf in f:
        if cf:
            break
        else:
            i += 1

    return f[i:]

@cythonized("u,v,i")
def dmp_strip(f, u):
    """
    Remove leading zeros from ``f`` in ``K[X]``.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_strip

    >>> dmp_strip([[], [0, 1, 2], [1]], 1)
    [[0, 1, 2], [1]]

    """
    if not u:
        return dup_strip(f)

    if dmp_zero_p(f, u):
        return f

    i, v = 0, u-1

    for c in f:
        if not dmp_zero_p(c, v):
            break
        else:
            i += 1

    if i == len(f):
        return dmp_zero(u)
    else:
        return f[i:]

@cythonized("i,j")
def _rec_validate(f, g, i, K):
    """Recursive helper for :func:`dmp_validate`."""
    if type(g) is not list:
        if K is not None and not K.of_type(g):
            raise TypeError("%s in %s in not of type %s" % (g, f, K.dtype))

        return set([i-1])
    elif not g:
        return set([i])
    else:
        j, levels = i+1, set([])

        for c in g:
            levels |= _rec_validate(f, c, i+1, K)

        return levels

@cythonized("v,w")
def _rec_strip(g, v):
    """Recursive helper for :func:`_rec_strip`."""
    if not v:
        return dup_strip(g)

    w = v-1

    return dmp_strip([ _rec_strip(c, w) for c in g ], v)

@cythonized("u")
def dmp_validate(f, K=None):
    """
    Return number of levels in ``f`` and recursively strips it.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_validate

    >>> dmp_validate([[], [0, 1, 2], [1]])
    ([[1, 2], [1]], 1)

    >>> dmp_validate([[1], 1])
    Traceback (most recent call last):
    ...
    ValueError: invalid data structure for a multivariate polynomial

    """
    levels = _rec_validate(f, f, 0, K)

    u = levels.pop()

    if not levels:
        return _rec_strip(f, u), u
    else:
        raise ValueError("invalid data structure for a multivariate polynomial")

def dup_reverse(f):
    """
    Compute ``x**n * f(1/x)``, i.e.: reverse ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_reverse

    >>> f = ZZ.map([1, 2, 3, 0])

    >>> dup_reverse(f)
    [3, 2, 1]

    """
    return dup_strip(list(reversed(f)))

def dup_copy(f):
    """
    Create a new copy of a polynomial ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_copy

    >>> f = ZZ.map([1, 2, 3, 0])

    >>> dup_copy([1, 2, 3, 0])
    [1, 2, 3, 0]

    """
    return list(f)

@cythonized("u,v")
def dmp_copy(f, u):
    """
    Create a new copy of a polynomial ``f`` in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_copy

    >>> f = ZZ.map([[1], [1, 2]])

    >>> dmp_copy(f, 1)
    [[1], [1, 2]]

    """
    if not u:
        return list(f)

    v = u-1

    return [ dmp_copy(c, v) for c in f ]

def dup_to_tuple(f):
    """
    Convert `f` into a tuple.

    This is needed for hashing. This is similar to dup_copy().
        **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_copy

    >>> f = ZZ.map([1, 2, 3, 0])

    >>> dup_copy([1, 2, 3, 0])
    [1, 2, 3, 0]

    """
    return tuple(f)

@cythonized("u,v")
def dmp_to_tuple(f, u):
    """
    Convert `f` into a nested tuple of tuples.

    This is needed for hashing.  This is similar to dmp_copy().

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_to_tuple

    >>> f = ZZ.map([[1], [1, 2]])

    >>> dmp_to_tuple(f, 1)
    ((1,), (1, 2))

    """
    if not u:
        return tuple(f)
    v = u - 1

    return tuple(dmp_to_tuple(c, v) for c in f)

def dup_normal(f, K):
    """
    Normalize univariate polynomial in the given domain.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_normal

    >>> dup_normal([0, 1.5, 2, 3], ZZ)
    [1, 2, 3]

    """
    return dup_strip([ K.normal(c) for c in f ])

@cythonized("u,v")
def dmp_normal(f, u, K):
    """
    Normalize multivariate polynomial in the given domain.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_normal

    >>> dmp_normal([[], [0, 1.5, 2]], 1, ZZ)
    [[1, 2]]

    """
    if not u:
        return dup_normal(f, K)

    v = u-1

    return dmp_strip([ dmp_normal(c, v, K) for c in f ], u)

def dup_convert(f, K0, K1):
    """
    Convert ground domain of ``f`` from ``K0`` to ``K1``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.polyclasses import DMP
    >>> from sympy.polys.densebasic import dup_convert

    >>> dup_convert([DMP([1], ZZ), DMP([2], ZZ)], ZZ['x'], ZZ)
    [1, 2]

    >>> dup_convert([ZZ(1), ZZ(2)], ZZ, ZZ['x'])
    [DMP([1], ZZ), DMP([2], ZZ)]

    """
    if K0 is not None and K0 == K1:
        return f
    else:
        return dup_strip([ K1.convert(c, K0) for c in f ])

@cythonized("u,v")
def dmp_convert(f, u, K0, K1):
    """
    Convert ground domain of ``f`` from ``K0`` to ``K1``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.polyclasses import DMP
    >>> from sympy.polys.densebasic import dmp_convert

    >>> f = [[DMP([1], ZZ)], [DMP([2], ZZ)]]
    >>> g = [[ZZ(1)], [ZZ(2)]]

    >>> dmp_convert(f, 1, ZZ['x'], ZZ)
    [[1], [2]]

    >>> dmp_convert(g, 1, ZZ, ZZ['x'])
    [[DMP([1], ZZ)], [DMP([2], ZZ)]]

    """
    if not u:
        return dup_convert(f, K0, K1)
    if K0 is not None and K0 == K1:
        return f

    v = u-1

    return dmp_strip([ dmp_convert(c, v, K0, K1) for c in f ], u)

def dup_from_sympy(f, K):
    """
    Convert ground domain of ``f`` from SymPy to ``K``.

    **Examples**

    >>> from sympy import S
    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_from_sympy

    >>> dup_from_sympy([S(1), S(2)], ZZ) == [ZZ(1), ZZ(2)]
    True

    """
    return dup_strip([ K.from_sympy(c) for c in f ])

@cythonized("u,v")
def dmp_from_sympy(f, u, K):
    """
    Convert ground domain of ``f`` from SymPy to ``K``.

    **Examples**

    >>> from sympy import S
    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_from_sympy

    >>> dmp_from_sympy([[S(1)], [S(2)]], 1, ZZ) == [[ZZ(1)], [ZZ(2)]]
    True

    """
    if not u:
        return dup_from_sympy(f, K)

    v = u-1

    return dmp_strip([ dmp_from_sympy(c, v, K) for c in f ], u)

@cythonized("n")
def dup_nth(f, n, K):
    """
    Return ``n``-th coefficient of ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_nth

    >>> f = ZZ.map([1, 2, 3])

    >>> dup_nth(f, 0, ZZ)
    3
    >>> dup_nth(f, 4, ZZ)
    0

    """
    if n < 0:
        raise IndexError("'n' must be non-negative, got %i" % n)
    elif n >= len(f):
        return K.zero
    else:
        return f[dup_degree(f)-n]

@cythonized("n,u")
def dmp_nth(f, n, u, K):
    """
    Return ``n``-th coefficient of ``f`` in ``K[x]``.

    **Examples**
    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_nth

    >>> f = ZZ.map([[1], [2], [3]])

    >>> dmp_nth(f, 0, 1, ZZ)
    [3]
    >>> dmp_nth(f, 4, 1, ZZ)
    []

    """
    if n < 0:
        raise IndexError("'n' must be non-negative, got %i" % n)
    elif n >= len(f):
        return dmp_zero(u-1)
    else:
        return f[dmp_degree(f, u)-n]

@cythonized("n,u,v")
def dmp_ground_nth(f, N, u, K):
    """
    Return ground ``n``-th coefficient of ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_ground_nth

    >>> f = ZZ.map([[1], [2, 3]])

    >>> dmp_ground_nth(f, (0, 1), 1, ZZ)
    2

    """
    v = u

    for n in N:
        if n < 0:
            raise IndexError("`n` must be non-negative, got %i" % n)
        elif n >= len(f):
            return K.zero
        else:
            f, v = f[dmp_degree(f, v)-n], v-1

    return f

@cythonized("u")
def dmp_zero_p(f, u):
    """
    Return ``True`` if ``f`` is zero in ``K[X]``.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_zero_p

    >>> dmp_zero_p([[[[[]]]]], 4)
    True
    >>> dmp_zero_p([[[[[1]]]]], 4)
    False

    """
    while u:
        if len(f) != 1:
            return False

        f = f[0]
        u -= 1

    return not f

@cythonized("u")
def dmp_zero(u):
    """
    Return a multivariate zero.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_zero

    >>> dmp_zero(4)
    [[[[[]]]]]

    """
    r = []

    for i in xrange(u):
        r = [r]

    return r

@cythonized("u")
def dmp_one_p(f, u, K):
    """
    Return ``True`` if ``f`` is one in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_one_p

    >>> dmp_one_p([[[ZZ(1)]]], 2, ZZ)
    True

    """
    return dmp_ground_p(f, K.one, u)

@cythonized("u")
def dmp_one(u, K):
    """
    Return a multivariate one over ``K``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_one

    >>> dmp_one(2, ZZ)
    [[[1]]]

    """
    return dmp_ground(K.one, u)

@cythonized("u")
def dmp_ground_p(f, c, u):
    """
    Return True if ``f`` is constant in ``K[X]``.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_ground_p

    >>> dmp_ground_p([[[3]]], 3, 2)
    True
    >>> dmp_ground_p([[[4]]], None, 2)
    True

    """
    if c is not None and not c:
        return dmp_zero_p(f, u)

    while u:
        if len(f) != 1:
            return False
        f = f[0]
        u -= 1

    if c is None:
        return len(f) <= 1
    else:
        return f == [c]

@cythonized("i,u")
def dmp_ground(c, u):
    """
    Return a multivariate constant.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_ground

    >>> dmp_ground(3, 5)
    [[[[[[3]]]]]]
    >>> dmp_ground(1, -1)
    1

    """
    if not c:
        return dmp_zero(u)

    for i in xrange(u+1):
        c = [c]

    return c

@cythonized("n,u")
def dmp_zeros(n, u, K):
    """
    Return a list of multivariate zeros.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_zeros

    >>> dmp_zeros(3, 2, ZZ)
    [[[[]]], [[[]]], [[[]]]]
    >>> dmp_zeros(3, -1, ZZ)
    [0, 0, 0]

    """
    if not n:
        return []

    if u < 0:
        return [K.zero]*n
    else:
        return [ dmp_zero(u) for i in xrange(n) ]

@cythonized("n,u")
def dmp_grounds(c, n, u):
    """
    Return a list of multivariate constants.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_grounds

    >>> dmp_grounds(ZZ(4), 3, 2)
    [[[[4]]], [[[4]]], [[[4]]]]
    >>> dmp_grounds(ZZ(4), 3, -1)
    [4, 4, 4]

    """
    if not n:
        return []

    if u < 0:
        return [c]*n
    else:
        return [ dmp_ground(c, u) for i in xrange(n) ]

@cythonized("u")
def dmp_negative_p(f, u, K):
    """
    Return ``True`` if ``LC(f)`` is negative.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_negative_p

    >>> dmp_negative_p([[ZZ(1)], [-ZZ(1)]], 1, ZZ)
    False
    >>> dmp_negative_p([[-ZZ(1)], [ZZ(1)]], 1, ZZ)
    True

    """
    return K.is_negative(dmp_ground_LC(f, u, K))

@cythonized("u")
def dmp_positive_p(f, u, K):
    """
    Return ``True`` if ``LC(f)`` is positive.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_positive_p

    >>> dmp_positive_p([[ZZ(1)], [-ZZ(1)]], 1, ZZ)
    True
    >>> dmp_positive_p([[-ZZ(1)], [ZZ(1)]], 1, ZZ)
    False

    """
    return K.is_positive(dmp_ground_LC(f, u, K))

@cythonized("n,k")
def dup_from_dict(f, K):
    """
    Create ``K[x]`` polynomial from a ``dict``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_from_dict

    >>> dup_from_dict({(0,): ZZ(7), (2,): ZZ(5), (4,): ZZ(1)}, ZZ)
    [1, 0, 5, 0, 7]
    >>> dup_from_dict({}, ZZ)
    []

    """
    if not f:
        return []

    n, h = max(f.iterkeys()), []

    if type(n) is int:
        for k in xrange(n, -1, -1):
            h.append(f.get(k, K.zero))
    else:
        (n,) = n

        for k in xrange(n, -1, -1):
            h.append(f.get((k,), K.zero))

    return dup_strip(h)

@cythonized("n,k")
def dup_from_raw_dict(f, K):
    """
    Create ``K[x]`` polynomial from a raw ``dict``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_from_raw_dict

    >>> dup_from_raw_dict({0: ZZ(7), 2: ZZ(5), 4: ZZ(1)}, ZZ)
    [1, 0, 5, 0, 7]

    """
    if not f:
        return []

    n, h = max(f.iterkeys()), []

    for k in xrange(n, -1, -1):
        h.append(f.get(k, K.zero))

    return dup_strip(h)

@cythonized("u,v,n,k")
def dmp_from_dict(f, u, K):
    """
    Create ``K[X]`` polynomial from a ``dict``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_from_dict

    >>> dmp_from_dict({(0, 0): ZZ(3), (0, 1): ZZ(2), (2, 1): ZZ(1)}, 1, ZZ)
    [[1, 0], [], [2, 3]]
    >>> dmp_from_dict({}, 0, ZZ)
    []

    """
    if not u:
        return dup_from_dict(f, K)
    if not f:
        return dmp_zero(u)

    coeffs = {}

    for monom, coeff in f.iteritems():
        head, tail = monom[0], monom[1:]

        if head in coeffs:
            coeffs[head][tail] = coeff
        else:
            coeffs[head] = { tail : coeff }

    n, v, h = max(coeffs.iterkeys()), u-1, []

    for k in xrange(n, -1, -1):
        coeff = coeffs.get(k)

        if coeff is not None:
            h.append(dmp_from_dict(coeff, v, K))
        else:
            h.append(dmp_zero(v))

    return dmp_strip(h, u)

@cythonized("n,k")
def dup_to_dict(f, K=None, zero=False):
    """
    Convert ``K[x]`` polynomial to a ``dict``.

    **Examples**

    >>> from sympy.polys.densebasic import dup_to_dict

    >>> dup_to_dict([1, 0, 5, 0, 7])
    {(0,): 7, (2,): 5, (4,): 1}
    >>> dup_to_dict([])
    {}

    """
    if not f and zero:
        return {(0,): K.zero}

    n, result = dup_degree(f), {}

    for k in xrange(0, n+1):
        if f[n-k]:
            result[(k,)] = f[n-k]

    return result

@cythonized("n,k")
def dup_to_raw_dict(f, K=None, zero=False):
    """
    Convert ``K[x]`` polynomial to a raw ``dict``.

    **Examples**

    >>> from sympy.polys.densebasic import dup_to_raw_dict

    >>> dup_to_raw_dict([1, 0, 5, 0, 7])
    {0: 7, 2: 5, 4: 1}

    """
    if not f and zero:
        return {0: K.zero}

    n, result = dup_degree(f), {}

    for k in xrange(0, n+1):
        if f[n-k]:
            result[k] = f[n-k]

    return result

@cythonized("u,v,n,k")
def dmp_to_dict(f, u, K=None, zero=False):
    """
    Convert ``K[X]`` polynomial to a ``dict````.

    **Examples**

    >>> from sympy.polys.densebasic import dmp_to_dict

    >>> dmp_to_dict([[1, 0], [], [2, 3]], 1)
    {(0, 0): 3, (0, 1): 2, (2, 1): 1}
    >>> dmp_to_dict([], 0)
    {}

    """
    if not u:
        return dup_to_dict(f, K, zero=zero)

    if dmp_zero_p(f, u) and zero:
        return {(0,)*(u + 1): K.zero}

    n, v, result = dmp_degree(f, u), u-1, {}

    for k in xrange(0, n+1):
        h = dmp_to_dict(f[n-k], v)

        for exp, coeff in h.iteritems():
            result[(k,)+exp] = coeff

    return result

@cythonized("u,i,j")
def dmp_swap(f, i, j, u, K):
    """
    Transform ``K[..x_i..x_j..]`` to ``K[..x_j..x_i..]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_swap

    >>> f = ZZ.map([[[2], [1, 0]], []])

    >>> dmp_swap(f, 0, 1, 2, ZZ)
    [[[2], []], [[1, 0], []]]
    >>> dmp_swap(f, 1, 2, 2, ZZ)
    [[[1], [2, 0]], [[]]]
    >>> dmp_swap(f, 0, 2, 2, ZZ)
    [[[1, 0]], [[2, 0], []]]

    """
    if i < 0 or j < 0 or i > u or j > u:
        raise IndexError("0 <= i < j <= %s expected" % u)
    elif i == j:
        return f

    F, H = dmp_to_dict(f, u), {}

    for exp, coeff in F.iteritems():
        H[exp[:i]    + (exp[j],) +
          exp[i+1:j] +
          (exp[i],)  + exp[j+1:]] = coeff

    return dmp_from_dict(H, u, K)

@cythonized("u")
def dmp_permute(f, P, u, K):
    """
    Return a polynomial in ``K[x_{P(1)},..,x_{P(n)}]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_permute

    >>> f = ZZ.map([[[2], [1, 0]], []])

    >>> dmp_permute(f, [1, 0, 2], 2, ZZ)
    [[[2], []], [[1, 0], []]]
    >>> dmp_permute(f, [1, 2, 0], 2, ZZ)
    [[[1], []], [[2, 0], []]]

    """
    F, H = dmp_to_dict(f, u), {}

    for exp, coeff in F.iteritems():
        new_exp = [0]*len(exp)

        for e, p in zip(exp, P):
            new_exp[p] = e

        H[tuple(new_exp)] = coeff

    return dmp_from_dict(H, u, K)

@cythonized("i,l")
def dmp_nest(f, l, K):
    """
    Return multivariate value nested ``l``-levels.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_nest

    >>> dmp_nest([[ZZ(1)]], 2, ZZ)
    [[[[1]]]]

    """
    if not isinstance(f, list):
        return dmp_ground(f, l)

    for i in xrange(l):
        f = [f]

    return f

@cythonized("l,k,u,v")
def dmp_raise(f, l, u, K):
    """
    Return multivariate polynomial raised ``l``-levels.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_raise

    >>> f = ZZ.map([[], [1, 2]])

    >>> dmp_raise(f, 2, 1, ZZ)
    [[[[]]], [[[1]], [[2]]]]

    """
    if not l:
        return f

    if not u:
        if not f:
            return dmp_zero(l)

        k = l-1

        return [ dmp_ground(c, k) for c in f ]

    v = u-1

    return [ dmp_raise(c, l, v, K) for c in f ]

@cythonized("g,i")
def dup_deflate(f, K):
    """
    Map ``x**m`` to ``y`` in a polynomial in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_deflate

    >>> f = ZZ.map([1, 0, 0, 1, 0, 0, 1])

    >>> dup_deflate(f, ZZ)
    (3, [1, 1, 1])

    """
    if dup_degree(f) <= 0:
        return 1, f

    g = 0

    for i in xrange(len(f)):
        if not f[-i-1]:
            continue

        g = igcd(g, i)

        if g == 1:
            return 1, f

    return g, f[::g]

@cythonized("u,i,m,a,b")
def dmp_deflate(f, u, K):
    """
    Map ``x_i**m_i`` to ``y_i`` in a polynomial in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_deflate

    >>> f = ZZ.map([[1, 0, 0, 2], [], [3, 0, 0, 4]])

    >>> dmp_deflate(f, 1, ZZ)
    ((2, 3), [[1, 2], [3, 4]])

    """
    if dmp_zero_p(f, u):
        return (1,)*(u+1), f

    F = dmp_to_dict(f, u)
    B = [0]*(u+1)

    for M in F.iterkeys():
        for i, m in enumerate(M):
            B[i] = igcd(B[i], m)

    for i, b in enumerate(B):
        if not b:
            B[i] = 1

    B = tuple(B)

    if all([ b == 1 for b in B ]):
        return B, f

    H = {}

    for A, coeff in F.iteritems():
        N = [ a // b for a, b in zip(A, B) ]
        H[tuple(N)] = coeff

    return B, dmp_from_dict(H, u, K)

@cythonized("G,g,i")
def dup_multi_deflate(polys, K):
    """
    Map ``x**m`` to ``y`` in a set of polynomials in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_multi_deflate

    >>> f = ZZ.map([1, 0, 2, 0, 3])
    >>> g = ZZ.map([4, 0, 0])

    >>> dup_multi_deflate((f, g), ZZ)
    (2, ([1, 2, 3], [4, 0]))

    """
    G = 0

    for p in polys:
        if dup_degree(p) <= 0:
            return 1, polys

        g = 0

        for i in xrange(len(p)):
            if not p[-i-1]:
                continue

            g = igcd(g, i)

            if g == 1:
                return 1, polys

        G = igcd(G, g)

    return G, tuple([ p[::G] for p in polys ])

@cythonized("u,G,g,m,a,b")
def dmp_multi_deflate(polys, u, K):
    """
    Map ``x_i**m_i`` to ``y_i`` in a set of polynomials in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_multi_deflate

    >>> f = ZZ.map([[1, 0, 0, 2], [], [3, 0, 0, 4]])
    >>> g = ZZ.map([[1, 0, 2], [], [3, 0, 4]])

    >>> dmp_multi_deflate((f, g), 1, ZZ)
    ((2, 1), ([[1, 0, 0, 2], [3, 0, 0, 4]], [[1, 0, 2], [3, 0, 4]]))

    """
    if not u:
        M, H = dup_multi_deflate(polys, K)
        return (M,), H

    F, B = [], [0]*(u+1)

    for p in polys:
        f = dmp_to_dict(p, u)

        if not dmp_zero_p(p, u):
            for M in f.iterkeys():
                for i, m in enumerate(M):
                    B[i] = igcd(B[i], m)

        F.append(f)

    for i, b in enumerate(B):
        if not b:
            B[i] = 1

    B = tuple(B)

    if all([ b == 1 for b in B ]):
        return B, polys

    H = []

    for f in F:
        h = {}

        for A, coeff in f.iteritems():
            N = [ a // b for a, b in zip(A, B) ]
            h[tuple(N)] = coeff

        H.append(dmp_from_dict(h, u, K))

    return B, tuple(H)

@cythonized("m")
def dup_inflate(f, m, K):
    """
    Map ``y`` to ``x**m`` in a polynomial in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_inflate

    >>> f = ZZ.map([1, 1, 1])

    >>> dup_inflate(f, 3, ZZ)
    [1, 0, 0, 1, 0, 0, 1]

    """
    if m <= 0:
        raise IndexError("'m' must be positive, got %s" % m)
    if m == 1 or not f:
        return f

    result = [f[0]]

    for coeff in f[1:]:
        result.extend([K.zero]*(m-1))
        result.append(coeff)

    return result

@cythonized("u,v,i,j")
def _rec_inflate(g, M, v, i, K):
    """Recursive helper for :func:`dmp_inflate`."""
    if not v:
        return dup_inflate(g, M[i], K)
    if M[i] <= 0:
        raise IndexError("all M[i] must be positive, got %s" % M[i])

    w, j = v-1, i+1

    g = [ _rec_inflate(c, M, w, j, K) for c in g ]

    result = [g[0]]

    for coeff in g[1:]:
        for _ in xrange(1, M[i]):
            result.append(dmp_zero(w))

        result.append(coeff)

    return result

@cythonized("u,m")
def dmp_inflate(f, M, u, K):
    """
    Map ``y_i`` to ``x_i**k_i`` in a polynomial in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_inflate

    >>> f = ZZ.map([[1, 2], [3, 4]])

    >>> dmp_inflate(f, (2, 3), 1, ZZ)
    [[1, 0, 0, 2], [], [3, 0, 0, 4]]

    """
    if not u:
        return dup_inflate(f, M[0], K)

    if all([ m == 1 for m in M ]):
        return f
    else:
        return _rec_inflate(f, M, u, 0, K)

@cythonized("u,j")
def dmp_exclude(f, u, K):
    """
    Exclude useless levels from ``f``.

    Return the levels excluded, the new excluded ``f``, and the new ``u``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_exclude

    >>> f = ZZ.map([[[1]], [[1], [2]]])

    >>> dmp_exclude(f, 2, ZZ)
    ([2], [[1], [1, 2]], 1)

    """
    if not u or dmp_ground_p(f, None, u):
        return [], f, u

    J, F = [], dmp_to_dict(f, u)

    for j in xrange(0, u+1):
        for monom in F.iterkeys():
            if monom[j]:
                break
        else:
            J.append(j)

    if not J:
        return [], f, u

    f = {}

    for monom, coeff in F.iteritems():
        monom = list(monom)

        for j in reversed(J):
            del monom[j]

        f[tuple(monom)] = coeff

    u -= len(J)

    return J, dmp_from_dict(f, u, K), u

@cythonized("u,j")
def dmp_include(f, J, u, K):
    """
    Include useless levels in ``f``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_include

    >>> f = ZZ.map([[1], [1, 2]])

    >>> dmp_include(f, [2], 1, ZZ)
    [[[1]], [[1], [2]]]

    """
    if not J:
        return f

    F, f = dmp_to_dict(f, u), {}

    for monom, coeff in F.iteritems():
        monom = list(monom)

        for j in J:
            monom.insert(j, 0)

        f[tuple(monom)] = coeff

    u += len(J)

    return dmp_from_dict(f, u, K)

@cythonized("u,v,w")
def dmp_inject(f, u, K, front=False):
    """
    Convert ``f`` from ``K[X][Y]`` to ``K[X,Y]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_inject

    >>> K = ZZ['x', 'y']

    >>> dmp_inject([K([[1]]), K([[1], [2]])], 0, K)
    ([[[1]], [[1], [2]]], 2)
    >>> dmp_inject([K([[1]]), K([[1], [2]])], 0, K, front=True)
    ([[[1]], [[1, 2]]], 2)

    """
    f, h = dmp_to_dict(f, u), {}

    v = len(K.gens) - 1

    for f_monom, g in f.iteritems():
        g = g.to_dict()

        for g_monom, c in g.iteritems():
            if front:
                h[g_monom + f_monom] = c
            else:
                h[f_monom + g_monom] = c

    w = u + v + 1

    return dmp_from_dict(h, w, K.dom), w

@cythonized("u,v")
def dmp_eject(f, u, K, front=False):
    """
    Convert ``f`` from ``K[X,Y]`` to ``K[X][Y]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_eject

    >>> K = ZZ['x', 'y']

    >>> dmp_eject([[[1]], [[1], [2]]], 2, K)
    [DMP([[1]], ZZ), DMP([[1], [2]], ZZ)]

    """
    f, h = dmp_to_dict(f, u), {}

    v = u - len(K.gens) + 1

    for monom, c in f.iteritems():
        if front:
            g_monom, f_monom = monom[:v], monom[v:]
        else:
            f_monom, g_monom = monom[:v], monom[v:]

        if f_monom in h:
            h[f_monom][g_monom] = c
        else:
            h[f_monom] = {g_monom: c}

    for monom, c in h.iteritems():
        h[monom] = K(c)

    return dmp_from_dict(h, v-1, K)

@cythonized("i")
def dup_terms_gcd(f, K):
    """
    Remove GCD of terms from ``f`` in ``K[x]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_terms_gcd

    >>> f = ZZ.map([1, 0, 1, 0, 0])

    >>> dup_terms_gcd(f, ZZ)
    (2, [1, 0, 1])

    """
    if dup_TC(f, K) or not f:
        return 0, f

    i = 0

    for c in reversed(f):
        if not c:
            i += 1
        else:
            break

    return i, f[:-i]

@cythonized("u,g")
def dmp_terms_gcd(f, u, K):
    """
    Remove GCD of terms from ``f`` in ``K[X]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_terms_gcd

    >>> f = ZZ.map([[1, 0], [1, 0, 0], [], []])

    >>> dmp_terms_gcd(f, 1, ZZ)
    ((2, 1), [[1], [1, 0]])

    """
    if dmp_ground_TC(f, u, K) or dmp_zero_p(f, u):
        return (0,)*(u+1), f

    F = dmp_to_dict(f, u)
    G = monomial_min(*F.keys())

    if all([ g == 0 for g in G ]):
        return G, f

    f = {}

    for monom, coeff in F.iteritems():
        f[monomial_div(monom, G)] = coeff

    return G, dmp_from_dict(f, u, K)

@cythonized("v,w,d,i")
def _rec_list_terms(g, v, monom):
    """Recursive helper for :func:`dmp_list_terms`."""
    d, terms = dmp_degree(g, v), []

    if not v:
        for i, c in enumerate(g):
            if not c:
                continue

            terms.append((monom + (d-i,), c))
    else:
        w = v-1

        for i, c in enumerate(g):
            terms.extend(_rec_list_terms(c, v-1, monom + (d-i,)))

    return terms

@cythonized("u")
def dmp_list_terms(f, u, K, order=None):
    """
    List all non-zero terms from ``f`` in the given order ``order``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_list_terms

    >>> f = ZZ.map([[1, 1], [2, 3]])

    >>> dmp_list_terms(f, 1, ZZ)
    [((1, 1), 1), ((1, 0), 1), ((0, 1), 2), ((0, 0), 3)]
    >>> dmp_list_terms(f, 1, ZZ, order='grevlex')
    [((1, 1), 1), ((1, 0), 1), ((0, 1), 2), ((0, 0), 3)]

    """
    terms = _rec_list_terms(f, u, ())

    if not terms:
        return [((0,)*(u+1), K.zero)]

    if order is None:
        return terms
    else:
        return sdp_sort(terms, monomial_key(order))

@cythonized("n,m")
def dup_apply_pairs(f, g, h, args, K):
    """
    Apply ``h`` to pairs of coefficients of ``f`` and ``g``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_apply_pairs

    >>> h = lambda x, y, z: 2*x + y - z

    >>> dup_apply_pairs([1, 2, 3], [3, 2, 1], h, (1,), ZZ)
    [4, 5, 6]

    """
    n, m = len(f), len(g)

    if n != m:
        if n > m:
            g = [K.zero]*(n-m) + g
        else:
            f = [K.zero]*(m-n) + f

    result = []

    for a, b in zip(f, g):
        result.append(h(a, b, *args))

    return dup_strip(result)

@cythonized("u,v,n,m")
def dmp_apply_pairs(f, g, h, args, u, K):
    """
    Apply ``h`` to pairs of coefficients of ``f`` and ``g``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dmp_apply_pairs

    >>> h = lambda x, y, z: 2*x + y - z

    >>> dmp_apply_pairs([[1], [2, 3]], [[3], [2, 1]], h, (1,), 1, ZZ)
    [[4], [5, 6]]

    """
    if not u:
        return dup_apply_pairs(f, g, h, args, K)

    n, m, v = len(f), len(g), u-1

    if n != m:
        if n > m:
            g = dmp_zeros(n-m, v, K) + g
        else:
            f = dmp_zeros(m-n, v, K) + f

    result = []

    for a, b in zip(f, g):
        result.append(dmp_apply_pairs(a, b, h, args, v, K))

    return dmp_strip(result, u)

@cythonized("m,n,k,M,N")
def dup_slice(f, m, n, K):
    """Take a continuous subsequence of terms of ``f`` in ``K[x]``. """
    k = len(f)

    M = k - m
    N = k - n

    f = f[N:M]

    if not f:
        return []
    else:
        return f + [K.zero]*m

@cythonized("m,n,u")
def dmp_slice(f, m, n, u, K):
    """Take a continuous subsequence of terms of ``f`` in ``K[X]``. """
    return dmp_slice_in(f, m, n, 0, u, K)

@cythonized("m,n,j,u,k")
def dmp_slice_in(f, m, n, j, u, K):
    """Take a continuous subsequence of terms of ``f`` in ``x_j`` in ``K[X]``. """
    if j < 0 or j > u:
        raise IndexError("-%s <= j < %s expected, got %s" % (u, u, j))

    if not u:
        return dup_slice(f, m, n, K)

    f, g = dmp_to_dict(f, u), {}

    for monom, coeff in f.iteritems():
        k = monom[j]

        if k < m or k >= n:
            monom = monom[:j] + (0,) + monom[j+1:]

        if monom in g:
            g[monom] += coeff
        else:
            g[monom] = coeff

    return dmp_from_dict(g, u, K)

def dup_random(n, a, b, K):
    """
    Return a polynomial of degree ``n`` with coefficients in ``[a, b]``.

    **Examples**

    >>> from sympy.polys.domains import ZZ
    >>> from sympy.polys.densebasic import dup_random

    >>> dup_random(3, -10, 10, ZZ) #doctest: +SKIP
    [-2, -8, 9, -4]

    """
    f = [ K.convert(random.randint(a, b)) for _ in xrange(0, n+1) ]

    while not f[0]:
        f[0] = K.convert(random.randint(a, b))

    return f
