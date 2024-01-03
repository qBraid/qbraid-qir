.. _sdk_qir_cirq:

Cirq conversions
==================

Example Usage
--------------

Convert a ``Cirq`` circuit to ``QIR`` code:

.. code-block:: python

   import cirq
   from qbraid_qir.cirq import cirq_to_qir

   # Create two qubits
   q0, q1 = cirq.LineQubit.range(2)

   # Create bell circuit
   circuit = cirq.Circuit(
       cirq.H(q0),
       cirq.CNOT(q0, q1),
       cirq.measure(q0, q1)
   )

   qir_code = cirq_to_qir(circuit, name="Bell")

   print(qir_code)

.. code-block:: none

   ; ModuleID = 'Bell'
   source_filename = "Bell"

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
