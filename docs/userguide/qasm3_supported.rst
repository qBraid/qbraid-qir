.. _sdk_qir_qasm3_support:

QASM support
==================

Currently Supported Constructs
------------------------------

The ``qbraid_qir.qasm3.qasm3_to_qir()`` converter supports the following OpenQASM 3 constructs:

1. **Register Declarations** : OpenQASM declarations of all forms ``qreg``, ``qubit``, ``bit`` and ``creg`` are supported. 

2. **QuantumMeasurements** : Openqasm measurements are supported which involve single qubit measurement and full register measurements. Range based measurements are not supported currently.

.. code-block:: c

    OPENQASM 3;

    qubit[2] q1;
    qubit[5] q2;
    qubit q3;

    bit[2] c1;
    bit c2;

    // supported
    c1 = measure q1;
    measure q1 -> c1;
    c2[0] = measure q3[0];

    //ERROR : not supported 
    c1[0:2] = measure q1[0:2]; 

3. **QuantumReset** : Resets are supported on declared quantum registers in all forms.


4. **QuantumGates** : **pyqir._native** gates are supported alongwith support for ``U3`` and ``U2`` gates. The U[x] gates are defined in the terms of existing ``rx`` and ``rz`` gates according to the decomposition present on the qiskit website - https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.UGate, https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.PhaseGate


5. **QuantumBarriers** : Barriers are supported only if they are placed on ALL the qubits in the circuit. For example: 

.. code-block:: c

    qubit q[2];

    U(0.1, 0.2, 0.3) q[0];

    // Barrier on all qubits
    barrier q;
    
    // ERROR : Barrier on a subset of qubits
    barrier q[0];


6. **Custom Quantum Gates** : Gates defined by users are supported as long as they are defined in terms of **pyqir._native** gate set. Identifier mapping in gate parameter expressions is not supported at the moment. Example - 

.. code-block:: c 

    OPENQASM 3.0;
    include "stdgates.inc";

    // Supported
    gate custom2(g) s {
        h s;
        rz(g) s;
    }

    // Supported
    gate custom(a,b,c) p, q{
        custom2(a) q;
        h p;
        cx p,q;
        rx(a) q;
        ry(0.5/0.1) q;
    }
    // ERROR : not supported
    gate custom_error(a) p{
        rx(a + 5*2) p; // error 
    }

    qubit[2] q;
    custom(2 + 3 - 1/5, 0.1, 0.3) q[0], q[1];



7. **Simple Branching Statements** (controlled on 1 bit) : Since QIR supports branching on a measurement result, single bit branching statements are supported at the moment. General boolean expressions and support for branching on full registers will be added in future. For example: 

.. code-block:: c

    OPENQASM 3;
    include "stdgates.inc";
    qubit[4] q;
    bit[4] c;
    h q;
    measure q -> c;
    // supported
    if(c[0]){
        x q[0];
        cx q[0], q[1];    
    }

    if(c[1] == 1){
        cx q[1], q[2];
    }

    if(!c[2]){
        h q[2];
    }

    //ERROR : not supported
    if(c == 8){
        x q[0];
    }
    // ERROR : not supported
    int[4] element;
    if(element > 5){
        y q[1];
    }


8.  **Expressions** : General expression evaluation involving literals and constants is supported. For example: 

.. code-block:: c 

    OPENQASM 3;
    qubit q;

    // supported
    rx(1.57) q;
    rz(3-2*3) q;
    rz(3-2*3*(8/2)) q;
    rx(-1.57) q;
    rx(4%2) q;

    // ERROR : not supported 
    int[4] n = 8;
    ry(2*pi / n) q;
