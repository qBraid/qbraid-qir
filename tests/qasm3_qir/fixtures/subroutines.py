# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining subroutine tests.

"""

SUBROUTINE_INCORRECT_TESTS = {
    "undeclared_call": (
        """
        OPENQASM 3;
        include "stdgates.inc";
        qubit q;
        my_function(1);
        """,
        "Undefined subroutine 'my_function' was called",
    ),
    "redefinition_raises_error": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit q) -> int[32] {
            h q;
            return;
        }
        def my_function(qubit q) -> float[32] {
            x q;
            return;
        }
        qubit q;
        """,
        "Redefinition of subroutine 'my_function'",
    ),
    "redefinition_raises_error_2": (
        """
        OPENQASM 3;
        include "stdgates.inc";
        def my_function(qubit q) {
            int[32] q = 1;
            return;
        }
        qubit q;
        my_function(q);
        """,
        "Re-declaration of variable q",
    ),
    "incorrect_param_count_1": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit q, qubit r) {
            h q;
            return;
        }
        qubit q;
        my_function(q);
        """,
        "Parameter count mismatch for subroutine 'my_function'. Expected 2 but got 1 in call",
    ),
    "incorrect_param_count_2": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(int[32] q) {
            h q;
            return;
        }
        qubit q;
        my_function(q, q);
        """,
        "Parameter count mismatch for subroutine 'my_function'. Expected 1 but got 2 in call",
    ),
    "return_value_mismatch": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit q) {
            h q;
            int[32] a = 1;
            return a;
        }
        qubit q;
        my_function(q);
        """,
        "Return type mismatch for subroutine 'my_function'.",
    ),
    "return_value_mismatch_2": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit q) -> int[32] {
            h q;
            int[32] a = 1;
            return ;
        }
        qubit q;
        my_function(q);
        """,
        "Return type mismatch for subroutine 'my_function'.",
    ),
    "subroutine_keyword_naming": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def pi(qubit q) {
            h q;
            return;
        }
        qubit q;
        pi(q);
        """,
        "Subroutine name 'pi' is a reserved keyword",
    ),
    "qubit_size_arg_mismatch": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit[3] q) {
            h q;
            return;
        }
        qubit[2] q;
        my_function(q);
        """,
        "Qubit register size mismatch for function 'my_function'.",
    ),
    "subroutine_var_name_conflict": (
        """
        OPENQASM 3;
        include "stdgates.inc";
        const int a = 4;
        def a(qubit q) {
            h q;
            return;
        }
        qubit q;
        a(q);
        """,
        r"Can not declare subroutine with name 'a' .*",
    ),
    "undeclared_register_usage": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit q) {
            h q;
            return;
        }
        qubit q;
        int b;
        my_function(b);
        """,
        "Expecting qubit argument for 'q'. Qubit register 'b' not found for function 'my_function'",
    ),
    "test_invalid_qubit_size": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit[-3] q) {
            h q;
            return;
        }
        qubit[4] q;
        my_function(q);
        """,
        "Invalid qubit size -3 for variable 'q' in function 'my_function'",
    ),
    "test_type_mismatch_for_function": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(int[32] a, qubit q) {
            h q;
            return;
        }
        qubit q;
        int[32] b = 4;
        my_function(q, b);
        """,
        "Expecting classical argument for 'a'. Qubit register 'q' found for function 'my_function'",
    ),
    "test_duplicate_qubit_args": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(qubit[3] p, qubit[1] q) {
            h q;
            return;
        }
        qubit[4] q;
        my_function(q[0:3], q[2]);
        """,
        r"Duplicate qubit argument for register 'q' in function call for 'my_function'",
    ),
    "undefined_variable_in_actual_arg_1": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(int [32] a) {
            h q;
            return;
        }
        qubit q;
        my_function(b);
        """,
        "Undefined variable 'b' used for function call 'my_function'",
    ),
    "undefined_array_arg_in_function_call": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        def my_function(readonly array[int[32], 1, 2] a) {
            return;
        }
        my_function(b);
        """,
        "Undefined variable 'b' used for function call 'my_function'",
    ),
}
