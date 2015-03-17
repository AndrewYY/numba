from __future__ import print_function, division, absolute_import

import sys

import numpy as np
from numba import jit, numpy_support, types
from numba import unittest_support as unittest
from numba.compiler import compile_isolated
from numba.lowering import transform_arg_name
from numba.utils import IS_PY3


def get_a(ary, i):
    return ary[i].a


def get_b(ary, i):
    return ary[i].b


def get_c(ary, i):
    return ary[i].c


def get_two_arrays_a(ary1, ary2, i):
    return ary1[i].a + ary2[i].a

def get_two_arrays_b(ary1, ary2, i):
    return ary1[i].b + ary2[i].b

def get_two_arrays_c(ary1, ary2, i):
    return ary1[i].c + ary2[i].c


def get_two_arrays_distinct(ary1, ary2, i):
    return ary1[i].a + ary2[i].f


def set_a(ary, i, v):
    ary[i].a = v


def set_b(ary, i, v):
    ary[i].b = v


def set_c(ary, i, v):
    ary[i].c = v


def set_record(ary, i, j):
    ary[i] = ary[j]


def get_record_a(rec, val):
    x = rec.a
    rec.a = val
    return x


def get_record_b(rec, val):
    x = rec.b
    rec.b = val
    return x


def get_record_c(rec, val):
    x = rec.c
    rec.c = val
    return x


def get_record_rev_a(val, rec):
    x = rec.a
    rec.a = val
    return x


def get_record_rev_b(val, rec):
    x = rec.b
    rec.b = val
    return x


def get_record_rev_c(val, rec):
    x = rec.c
    rec.c = val
    return x


def get_two_records_a(rec1, rec2):
    x = rec1.a + rec2.a
    return x


def get_two_records_b(rec1, rec2):
    x = rec1.b + rec2.b
    return x


def get_two_records_c(rec1, rec2):
    x = rec1.c + rec2.c
    return x


def get_two_records_distinct(rec1, rec2):
    x = rec1.a + rec2.f
    return x


def record_return(ary, i):
    return ary[i]


def record_write_array(ary):
    ary.g = 2
    ary.h[0] = 3.0
    ary.h[1] = 4.0

def record_write_2d_array(ary):
    ary.i = 3
    ary.j[0, 0] = 5.0
    ary.j[0, 1] = 6.0
    ary.j[1, 0] = 7.0
    ary.j[1, 1] = 8.0
    ary.j[2, 0] = 9.0
    ary.j[2, 1] = 10.0


def record_read_array0(ary):
    return ary.h[0]

def record_read_array1(ary):
    return ary.h[1]

def record_read_2d_array00(ary):
    return ary.j[0,0]

def record_read_2d_array10(ary):
    return ary.j[1,0]

def record_read_2d_array01(ary):
    return ary.j[0,1]


def record_read_first_arr(ary):
    return ary.k[2, 2]

def record_read_second_arr(ary):
    return ary.l[2, 2]


recordtype = np.dtype([('a', np.float64),
                       ('b', np.int32),
                       ('c', np.complex64),
                       ('d', (np.str, 5))])

recordtype2 = np.dtype([('e', np.int32),
                        ('f', np.float64)])

recordtype3 = np.dtype([('first', np.float32),
                        ('second', np.float64)])

recordwitharray = np.dtype([('g', np.int32),
                            ('h', np.float32, 2)])

recordwith2darray = np.dtype([('i', np.int32),
                              ('j', np.float32, (3, 2))])

recordwith2arrays = np.dtype([('k', np.int32, (10, 20)),
                              ('l', np.int32, (6, 12))])

class TestRecordDtype(unittest.TestCase):

    def _createSampleArrays(self):
        '''
        Set up the data structures to be used with the Numpy and Numba
        versions of functions.

        In this case, both accept recarrays.
        '''
        self.refsample1d = np.recarray(3, dtype=recordtype)
        self.refsample1d2 = np.recarray(3, dtype=recordtype2)
        self.refsample1d3 = np.recarray(3, dtype=recordtype)

        self.nbsample1d = np.recarray(3, dtype=recordtype)
        self.nbsample1d2 = np.recarray(3, dtype=recordtype2)
        self.nbsample1d3 = np.recarray(3, dtype=recordtype)

    def setUp(self):

        self._createSampleArrays()

        for ary in (self.refsample1d, self.nbsample1d):
            for i in range(ary.size):
                x = i + 1
                ary[i]['a'] = x / 2
                ary[i]['b'] = x
                ary[i]['c'] = x * 1j
                ary[i]['d'] = "%d" % x

        for ary2 in (self.refsample1d2, self.nbsample1d2):
            for i in range(ary2.size):
                x = i + 5
                ary2[i]['e'] = x
                ary2[i]['f'] = x / 2

        for ary3 in (self.refsample1d3, self.nbsample1d3):
            for i in range(ary3.size):
                x = i + 10
                ary3[i]['a'] = x / 2
                ary3[i]['b'] = x
                ary3[i]['c'] = x * 1j
                ary3[i]['d'] = "%d" % x

    def get_cfunc(self, pyfunc, argspec):
        cres = compile_isolated(pyfunc, argspec)
        return cres.entry_point

    def test_from_dtype(self):
        rec = numpy_support.from_dtype(recordtype)
        self.assertEqual(rec.typeof('a'), types.float64)
        self.assertEqual(rec.typeof('b'), types.int32)
        self.assertEqual(rec.typeof('c'), types.complex64)
        if IS_PY3:
            self.assertEqual(rec.typeof('d'), types.UnicodeCharSeq(5))
        else:
            self.assertEqual(rec.typeof('d'), types.CharSeq(5))
        self.assertEqual(rec.offset('a'), recordtype.fields['a'][1])
        self.assertEqual(rec.offset('b'), recordtype.fields['b'][1])
        self.assertEqual(rec.offset('c'), recordtype.fields['c'][1])
        self.assertEqual(rec.offset('d'), recordtype.fields['d'][1])
        self.assertEqual(recordtype.itemsize, rec.size)

    def _test_get_equal(self, pyfunc):
        rec = numpy_support.from_dtype(recordtype)
        cfunc = self.get_cfunc(pyfunc, (rec[:], types.intp))
        for i in range(self.refsample1d.size):
            self.assertEqual(pyfunc(self.refsample1d, i), cfunc(self.nbsample1d, i))

    def test_get_a(self):
        self._test_get_equal(get_a)

    def test_get_b(self):
        self._test_get_equal(get_b)

    def test_get_c(self):
        self._test_get_equal(get_c)

    def _test_get_two_equal(self, pyfunc):
        '''
        Test with two arrays of the same type
        '''
        rec = numpy_support.from_dtype(recordtype)
        cfunc = self.get_cfunc(pyfunc, (rec[:], rec[:], types.intp))
        for i in range(self.refsample1d.size):
            self.assertEqual(pyfunc(self.refsample1d, self.refsample1d3, i),
                              cfunc(self.nbsample1d, self.nbsample1d3, i))

    def test_two_distinct_arrays(self):
        '''
        Test with two arrays of distinct record types
        '''
        pyfunc = get_two_arrays_distinct
        rec1 = numpy_support.from_dtype(recordtype)
        rec2 = numpy_support.from_dtype(recordtype2)
        cfunc = self.get_cfunc(pyfunc, (rec1[:], rec2[:], types.intp))
        for i in range(self.refsample1d.size):
            pres = pyfunc(self.refsample1d, self.refsample1d2, i)
            cres = cfunc(self.nbsample1d, self.nbsample1d2, i)
            self.assertEqual(pres,cres)

    def test_get_two_a(self):
        self._test_get_two_equal(get_two_arrays_a)

    def test_get_two_b(self):
        self._test_get_two_equal(get_two_arrays_b)

    def test_get_two_c(self):
        self._test_get_two_equal(get_two_arrays_c)

    def _test_set_equal(self, pyfunc, value, valuetype):
        rec = numpy_support.from_dtype(recordtype)
        cfunc = self.get_cfunc(pyfunc, (rec[:], types.intp, valuetype))

        for i in range(self.refsample1d.size):
            expect = self.refsample1d.copy()
            pyfunc(expect, i, value)

            got = self.nbsample1d.copy()
            cfunc(got, i, value)

            # Match the entire array to ensure no memory corruption
            self.assertTrue(np.all(expect == got))

    def test_set_a(self):
        self._test_set_equal(set_a, 3.1415, types.float64)
        # Test again to check if coercion works
        self._test_set_equal(set_a, 3., types.float32)

    def test_set_b(self):
        self._test_set_equal(set_b, 123, types.int32)
        # Test again to check if coercion works
        self._test_set_equal(set_b, 123, types.float64)

    def test_set_c(self):
        self._test_set_equal(set_c, 43j, types.complex64)
        # Test again to check if coercion works
        self._test_set_equal(set_c, 43j, types.complex128)

    def test_set_record(self):
        pyfunc = set_record
        rec = numpy_support.from_dtype(recordtype)
        cfunc = self.get_cfunc(pyfunc, (rec[:], types.intp, types.intp))

        test_indices = [(0, 1), (1, 2), (0, 2)]
        for i, j in test_indices:
            expect = self.refsample1d.copy()
            pyfunc(expect, i, j)

            got = self.nbsample1d.copy()
            cfunc(got, i, j)

            # Match the entire array to ensure no memory corruption
            self.assertEqual(expect[i], expect[j])
            self.assertEqual(got[i], got[j])
            self.assertTrue(np.all(expect == got))


    def _test_record_args(self, revargs):
        """
        Testing scalar record value as argument
        """
        npval = self.refsample1d.copy()[0]
        nbval = self.nbsample1d.copy()[0]
        attrs = 'abc'
        valtypes = types.float64, types.int32, types.complex64
        values = 1.23, 123432, 132j
        old_refcnt = sys.getrefcount(nbval)

        for attr, valtyp, val in zip(attrs, valtypes, values):
            expected = getattr(npval, attr)
            nbrecord = numpy_support.from_dtype(recordtype)

            # Test with a record as either the first argument or the second
            # argument (issue #870)
            if revargs:
                prefix = 'get_record_rev_'
                argtypes = (valtyp, nbrecord)
                args = (val, nbval)
            else:
                prefix = 'get_record_'
                argtypes = (nbrecord, valtyp)
                args = (nbval, val)

            pyfunc = globals()[prefix + attr]
            cfunc = self.get_cfunc(pyfunc, argtypes)

            got = cfunc(*args)
            self.assertEqual(expected, got)
            self.assertNotEqual(nbval['a'], got)
            del got, expected, args

        # Check for potential leaks (issue #441)
        self.assertEqual(sys.getrefcount(nbval), old_refcnt)


    def test_record_args(self):
        self._test_record_args(False)


    def test_record_args_reverse(self):
        self._test_record_args(True)


    def test_two_records(self):
        '''
        Testing the use of two scalar records of the same type
        '''
        npval1 = self.refsample1d.copy()[0]
        npval2 = self.refsample1d.copy()[1]
        nbval1 = self.nbsample1d.copy()[0]
        nbval2 = self.nbsample1d.copy()[1]
        attrs = 'abc'
        valtypes = types.float64, types.int32, types.complex64

        for attr, valtyp in zip(attrs, valtypes):
            expected = getattr(npval1, attr) + getattr(npval2, attr)

            nbrecord = numpy_support.from_dtype(recordtype)
            pyfunc = globals()['get_two_records_' + attr]
            cfunc = self.get_cfunc(pyfunc, (nbrecord, nbrecord))

            got = cfunc(nbval1, nbval2)
            self.assertEqual(expected, got)


    def test_two_distinct_records(self):
        '''
        Testing the use of two scalar records of differing type
        '''
        nbval1 = self.nbsample1d.copy()[0]
        nbval2 = self.refsample1d2.copy()[0]
        expected = nbval1['a'] + nbval2['f']

        nbrecord1 = numpy_support.from_dtype(recordtype)
        nbrecord2 = numpy_support.from_dtype(recordtype2)
        cfunc = self.get_cfunc(get_two_records_distinct, (nbrecord1, nbrecord2))

        got = cfunc(nbval1, nbval2)
        self.assertEqual(expected, got)


    def test_record_write_array(self):
        '''
        Testing writing to a 1D array within a structured type
        '''
        nbval = np.recarray(1, dtype=recordwitharray)
        nbrecord = numpy_support.from_dtype(recordwitharray)
        cfunc = self.get_cfunc(record_write_array, (nbrecord,))
        cfunc(nbval[0])

        expected = np.recarray(1, dtype=recordwitharray)
        expected[0].g = 2
        expected[0].h[0] = 3.0
        expected[0].h[1] = 4.0
        np.testing.assert_equal(expected, nbval)


    def test_record_write_2d_array(self):
        '''
        Test writing to a 2D array within a structured type
        '''
        nbval = np.recarray(1, dtype=recordwith2darray)
        nbrecord = numpy_support.from_dtype(recordwith2darray)
        cfunc = self.get_cfunc(record_write_2d_array, (nbrecord,))
        cfunc(nbval[0])

        expected = np.recarray(1, dtype=recordwith2darray)
        expected[0].i = 3
        expected[0].j[:] = np.asarray([5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                                      np.float32).reshape(3, 2)
        np.testing.assert_equal(expected, nbval)


    def test_record_read_array(self):
        '''
        Test reading from a 1D array within a structured type
        '''
        nbval = np.recarray(1, dtype=recordwitharray)
        nbval[0].h[0] = 15.0
        nbval[0].h[1] = 25.0
        nbrecord = numpy_support.from_dtype(recordwitharray)
        cfunc = self.get_cfunc(record_read_array0, (nbrecord,))
        res = cfunc(nbval[0])
        np.testing.assert_equal(res, nbval[0].h[0])

        cfunc = self.get_cfunc(record_read_array1, (nbrecord,))
        res = cfunc(nbval[0])
        np.testing.assert_equal(res, nbval[0].h[1])


    def test_record_read_2d_array(self):
        '''
        Test reading from a 2D array within a structured type
        '''
        nbval = np.recarray(1, dtype=recordwith2darray)
        nbval[0].j = np.asarray([1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
                                np.float32).reshape(3, 2)
        nbrecord = numpy_support.from_dtype(recordwith2darray)
        cfunc = self.get_cfunc(record_read_2d_array00, (nbrecord,))
        res = cfunc(nbval[0])
        np.testing.assert_equal(res, nbval[0].j[0, 0])

        cfunc = self.get_cfunc(record_read_2d_array01, (nbrecord,))
        res = cfunc(nbval[0])
        np.testing.assert_equal(res, nbval[0].j[0, 1])

        cfunc = self.get_cfunc(record_read_2d_array10, (nbrecord,))
        res = cfunc(nbval[0])
        np.testing.assert_equal(res, nbval[0].j[1, 0])


    def test_record_return(self):
        """
        Testing scalar record value as return value.
        We can only return a copy of the record.
        """
        pyfunc = record_return
        recty = numpy_support.from_dtype(recordtype)
        cfunc = self.get_cfunc(pyfunc, (recty[:], types.intp))

        attrs = 'abc'
        indices = [0, 1, 2]
        for index, attr in zip(indices, attrs):
            npary = self.refsample1d.copy()
            nbary = self.nbsample1d.copy()
            old_refcnt = sys.getrefcount(nbary)
            res = cfunc(npary, index)
            self.assertEqual(npary[index], res)
            # Prove that this is a by-value copy
            setattr(res, attr, 0)
            self.assertNotEqual(nbary[index], res)
            del res
            # Check for potential leaks
            self.assertEqual(sys.getrefcount(nbary), old_refcnt)

    def test_record_arg_transform(self):
        """
        Testing that transforming the name of a record type argument to a
        function does not result in the fields of the record being used to
        uniquely identify them, and that no other condition results in the
        transformed name being excessively long.
        """
        rec = numpy_support.from_dtype(recordtype3)
        transformed = transform_arg_name(rec)
        self.assertNotIn('first', transformed)
        self.assertNotIn('second', transformed)
        # len(transformed) is generally 10, but could be longer if a large
        # number of typecodes are in use. Checking <16 should provide enough
        # tolerance.
        self.assertLess(len(transformed), 16)

        struct_arr = types.Array(rec, 1, 'C')
        transformed = transform_arg_name(struct_arr)
        self.assertIn('array', transformed)
        self.assertNotIn('first', transformed)
        self.assertNotIn('second', transformed)
        # Length is usually 34 - 5 chars tolerance as above.
        self.assertLess(len(transformed), 40)


    def test_record_two_arrays(self):
        """
        Tests that comparison of NestedArrays by key is working correctly. If
        the two NestedArrays in recordwith2arrays compare equal (same length and
        ndim but different shape) incorrect code will be generated for one of the
        functions.
        """
        nbrecord = numpy_support.from_dtype(recordwith2arrays)
        rec = np.recarray(1, dtype=recordwith2arrays)[0]
        rec.k[:] = np.arange(200).reshape(10,20)
        rec.l[:] = np.arange(72).reshape(6,12)

        pyfunc = record_read_first_arr
        cfunc = self.get_cfunc(pyfunc, (nbrecord,))
        self.assertEqual(cfunc(rec), pyfunc(rec))

        pyfunc = record_read_second_arr
        cfunc = self.get_cfunc(pyfunc, (nbrecord,))
        self.assertEqual(cfunc(rec), pyfunc(rec))

def _get_cfunc_nopython(pyfunc, argspec):
    return jit(argspec, nopython=True)(pyfunc)

class TestRecordDtypeWithDispatcher(TestRecordDtype):
    '''
    Same as TestRecordDtype, but stressing the Dispatcher's type dispatch
    mechanism (issue #384). Note that this does not stress caching of ndarray
    typecodes as the path that uses the cache is not taken with recarrays.
    '''

    def get_cfunc(self, pyfunc, argspec):
        return _get_cfunc_nopython(pyfunc, argspec)

class TestRecordDtypeWithStructArrays(TestRecordDtype):
    '''
    Same as TestRecordDtype, but using structured arrays instead of recarrays.
    '''

    def _createSampleArrays(self):
        '''
        Two different versions of the data structures are required because Numba
        supports attribute access on structured arrays, whereas Numpy does not.

        However, the semantics of recarrays and structured arrays are equivalent
        for these tests so Numpy with recarrays can be used for comparison with
        Numba using structured arrays.
        '''

        self.refsample1d = np.recarray(3, dtype=recordtype)
        self.refsample1d2 = np.recarray(3, dtype=recordtype2)
        self.refsample1d3 = np.recarray(3, dtype=recordtype)

        self.nbsample1d = np.zeros(3, dtype=recordtype)
        self.nbsample1d2 = np.zeros(3, dtype=recordtype2)
        self.nbsample1d3 = np.zeros(3, dtype=recordtype)

class TestRecordDtypeWithStructArraysAndDispatcher(TestRecordDtypeWithStructArrays):
    '''
    Same as TestRecordDtypeWithStructArrays, stressing the Dispatcher's type
    dispatch mechanism (issue #384) and caching of ndarray typecodes for void
    types (which occur in structured arrays).
    '''

    def get_cfunc(self, pyfunc, argspec):
        return _get_cfunc_nopython(pyfunc, argspec)

if __name__ == '__main__':
    unittest.main()
