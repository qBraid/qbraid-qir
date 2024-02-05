.. _sdk_qir_qasm3:

QASM conversions
==================

Example Usage
--------------

Convert an ``OpenQASM 3`` program to ``QIR`` code:

.. code-block:: python

   from qbraid_qir import dumps
   from qbraid_qir.qasm3 import qasm3_to_qir

   # create a test program
   program = """
   OPENQASM 3;
   include "stdgates.inc";
   qubit[2] q;
   h q[0];
   cx q[0], q[1];
   measure q[0] -> c[0];
   measure q[1] -> c[1];
   """

   # convert to QIR
   module = qasm3_to_qir(program, name="bell")

   # saves to .ll and .bc files in working directory
   dumps(module)

   print(module)

.. code-block:: none

   ; ModuleID = 'bell'
   source_filename = "bell"

   %Qubit = type opaque
   %Result = type opaque

   define void @main() #0 {
   entry:
     call void @__quantum__qis__h__body(%Qubit* inttoptr (i64 0 to %Qubit*))  # Corrected %Qubit* null to inttoptr (i64 0 to %Qubit*)
     call void @__quantum__qis__cnot__body(%Qubit* inttoptr (i64 0 to %Qubit*), %Qubit* inttoptr (i64 1 to %Qubit*))  # Corrected %Qubit* null and added correct inttoptr conversion
     call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 0 to %Qubit*), %Result* inttoptr (i64 0 to %Result*))  # Corrected %Qubit* and %Result* null to correct inttoptr conversion
     call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))  # Added correct inttoptr conversion
     ret void
   }

   declare void @__quantum__qis__h__body(%Qubit*)
   declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*)
   declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

   attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="custom" "required_num_qubits"="2" "required_num_results"="2" }
   attributes #1 = { "irreversible" }

   !llvm.module.flags = !{!0, !1, !2, !3}
   !0 = !{i32 1, !"qir_major_version", i32 1}
   !1 = !{i32 7, !"qir_minor_version", i32 0}
   !2 = !{i32 1, !"dynamic_qubit_management", i1 false}
   !3 = !{i32 1, !"dynamic_result_management", i1 false}


Execute the QIR program using the `qir-runner <https://github.com/qir-alliance/qir-runner>`_ command line tool:

.. code-block:: bash

   $ qir-runner -f bell.bc


.. seealso::

   https://github.com/qBraid/qbraid-qir/tree/main/test-containers
