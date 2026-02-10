.. raw:: html

   <html>
   <head>
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <style>
   * {
   box-sizing: border-box;
   }

   body {
   font-family: Arial, Helvetica, sans-serif;
   }

   /* Float four columns side by side */
   .column {
   display: inline-block;
   vertical-align: middle;
   float: none;
   width: 25%;
   padding: 0 10px;
   }

   /* Remove extra left and right margins, due to padding */
   .row {
   text-align: center;
   margin:0 auto;
   }

   /* Clear floats after the columns */
   .row:after {
   content: "";
   display: table;
   clear: both;
   }

   /* Responsive columns */
   @media screen and (max-width: 600px) {
      .column {
         width: 100%;
         margin-bottom: 20px;
      }
   }

   </style>
   </head>
   <body>
   <h1 style="text-align: center">
      <img src="_static/logo.png" alt="qbraid logo" style="width:60px;height:60px;">
      <span> qBraid</span>
      <span style="color:#808080"> | QIR</span>
   </h1>
   <p style="text-align:center;font-style:italic;color:#808080">
      qBraid-SDK extension providing support for QIR conversions.
   </p>
   </body>
   </html>

|

:Release: |release|

Overview
---------

Python package for generating `QIR <https://www.qir-alliance.org/qir-book/concepts/what-is-qir.html>`_ (Quantum Intermediate Representation)
programs from various high-level quantum programming languages. This project acts as an extension to the qBraid-SDK `transpiler <https://docs.qbraid.com/sdk/user-guide/transpiler>`_,
opening the door to language-specific conversions from any of the 10+ quantum program types `supported <https://docs.qbraid.com/sdk/user-guide/overview#supported-frontends>`_
by ``qbraid``.

> "*Interoperability* opens doors to cross-fields problem-solving." \- QIR Alliance: `Why do we need it? <https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html>`_.


Installation
-------------

qBraid-QIR requires Python 3.10 or greater. The base package can be installed with pip as follows:

.. code-block:: bash

   pip install qbraid-qir


To enable specific conversions such as OpenQASM 3 to QIR or Cirq to QIR, you can install one or both extras:

.. code-block:: bash

   pip install 'qbraid-qir[qasm3,cirq]'


Resources
----------

- `User Guide <https://docs.qbraid.com/v2/qir/user-guide>`_
- `Example Notebooks <https://github.com/qBraid/qbraid-lab-demo/tree/main/qbraid_qir>`_
- `API Reference <https://qbraid.github.io/qbraid-qir/api/qbraid_qir.html>`_
- `Source Code <https://github.com/qBraid/qbraid-qir>`_

.. toctree::
   :maxdepth: 1
   :caption: SDK API Reference
   :hidden:

   qbraid <https://qbraid.github.io/qBraid/api/qbraid.html>
   qbraid.programs <https://qbraid.github.io/qBraid/api/qbraid.programs.html>
   qbraid.interface <https://qbraid.github.io/qBraid/api/qbraid.interface.html>
   qbraid.transpiler <https://qbraid.github.io/qBraid/api/qbraid.transpiler.html>
   qbraid.passes <https://qbraid.github.io/qBraid/api/qbraid.passes.html>
   qbraid.runtime <https://qbraid.github.io/qBraid/api/qbraid.runtime.html>
   qbraid.visualization <https://qbraid.github.io/qBraid/api/qbraid.visualization.html>

.. toctree::
   :maxdepth: 1
   :caption: QIR API Reference
   :hidden:

   api/qbraid_qir
   api/qbraid_qir.cirq
   api/qbraid_qir.qasm3
   api/qbraid_qir.squin

.. toctree::
   :caption: CORE API Reference
   :hidden:

   qbraid_core <https://qbraid.github.io/qbraid-core/api/qbraid_core.html>
   qbraid_core.services <https://qbraid.github.io/qbraid-core/api/qbraid_core.services.html>

.. toctree::
   :caption: PYQASM API Reference
   :hidden:

   pyqasm <https://qbraid.github.io/pyqasm/api/pyqasm.html>

.. toctree::
   :caption: ALGOS API Reference
   :hidden:

   qbraid_algorithms <https://qbraid.github.io/qbraid-algorithms/api/qbraid_algorithms.html>
