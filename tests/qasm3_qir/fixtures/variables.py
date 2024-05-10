# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining QASM3 incorrect variable tests.

"""

DECLARATION_TESTS = {
    "keyword_redeclaration": (
        """
        OPENQASM 3.0;
        include "stddgates.inc";
        int pi;
        """,
        "Can not declare variable with keyword name pi",
    ),
    "const_keyword_redeclaration": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        const int pi = 3;
        """,
        "Can not declare variable with keyword name pi",
    ),
    "variable_redeclaration": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        int x;
        float y = 3.4;
        uint x;
        """,
        "Re-declaration of variable x",
    ),
    "const_variable_redeclaration": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        const int x = 3;
        const float x = 3.4;
        """,
        "Re-declaration of variable x",
    ),
    "invalid_int_size": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        int[32.1] x;
        """,
        "Invalid base size 32.1 for variable x",
    ),
    "invalid_const_int_size": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        const int[32.1] x = 3;
        """,
        "Invalid base size 32.1 for variable x",
    ),
    "invalid_float_size": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        float[23] x;
        """,
        "Invalid base size 23 for float variable x",
    ),
    "imaginary_variable": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        int x = 1 + 3im;
        """,
        "Unsupported expression type <class 'openqasm3.ast.ImaginaryLiteral'>",
    ),
    "invalid_array_dimensions": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        array[int[32], 1, 2.1] x;
        """,
        "Invalid dimension size 2.1 in array declaration for x",
    ),
}

ASSIGNMENT_TESTS = {
    "undefined_variable_assignment": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        
        float k;

        x = 3; 

        """,
        "Undefined variable x in assignment",
    ),
    "assignment_to_constant": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        const int x = 3;
        x = 4;
        """,
        "Assignment to constant variable x not allowed",
    ),
    "invalid_type": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        int x = 3;
        x = 4.3232;
        """,
        (
            "Invalid assignment of type <class 'float'> to variable x "
            "of type <class 'openqasm3.ast.IntType'>"
        ),
    ),
    "int_out_of_range": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        int[32] x = 1<<64;
        """,
        f"Value {2**64} out of limits for variable x with base size 32",
    ),
    "uint_out_of_range": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        uint[32] x = -2;
        """,
        f"Value {-2} out of limits for variable x with base size 32",
    ),
    "float32_out_of_range": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        float[32] x = 123456789123456789123456789123456789123456789.1;
        """,
        "Value .* out of limits for variable x with base size 32",
    ),
    "indexing_non_array": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        int x = 3;
        x[0] = 4;
        """,
        "Indexing error. Variable x is not an array",
    ),
    "incorrect_num_dims": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        array[int[32], 1, 2, 3] x;
        x[0] = 3;
        """,
        "Invalid number of indices for variable x. Expected 3 but got 1",
    ),
    "non_nnint_index": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        array[int[32], 3] x;
        x[0.1] = 3;
        """,
        "Unsupported index type <class 'openqasm3.ast.FloatLiteral'> for classical variable x",
    ),
    "index_out_of_range": (
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        array[int[32], 3] x;
        x[3] = 3;
        """,
        "Index 3 out of bounds for dimension 1 of variable x",
    ),
}
