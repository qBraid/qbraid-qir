Documentation
==============
   
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
      <img src="_static/logo.png" alt="qbraid logo" style="width:50px;height:50px;">
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

Python package for generating QIR programs from Cirq, and other high-level quantum programming languages.
This project aims to make QIR (Quantum Intermediate Representation) accessible via the qBraid-SDK
`transpiler <https://docs.qbraid.com/en/latest/sdk/transpiler.html>`_, and by doing so, open the door
to language-specific conversions from any and all high-level quantum languages supported by ``qbraid``.

"*Interoperability* opens doors to cross-fields problem-solving." \- QIR Alliance: `Why do we need it? <https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html>`_.


Installation
^^^^^^^^^^^^^

.. code-block:: bash

   pip install qbraid-qir


Test container
^^^^^^^^^^^^^^^^

Docker image providing an environment for testing and executing QIR programs with the `qir-runner <https://github.com/qir-alliance/qir-runner>`_ package.

Clone the ``qbraid-qir`` repository:

.. code-block:: bash

   git clone https://github.com/qBraid/qbraid-qir.git
   cd qbraid-qir


Build the QIR runner image:

.. code-block:: bash

   docker build -t qbraid-test/qir-runner:latest qir_runner

Start the container running a Jupyter Server with the JupyterLab frontend and expose
the container's internal port ``8888`` to port ``8888`` of the host machine:

.. code-block:: bash

   docker run -p 8888:8888 qbraid-test/qir-runner:latest


Visiting ``http://<hostname>:8888/?token=<token>`` in a browser will launch JupyterLab, where:

- The hostname is the name of the computer running Docker (e.g. ``localhost``)
- The token is the secret token printed in the console.

Alternatively, you can open a shell inside the running container directly:

.. code-block:: bash

   docker exec -it <container_name> /bin/bash


.. seealso::

   https://github.com/qBraid/qbraid-qir/tree/main/test-containers


Acknowledgements
^^^^^^^^^^^^^^^^^^

This project was conceived in cooperation with the Quantum Open Source Foundation (`QOSF <https://qosf.org/>`_).

+-------------+-------------+-------------+-------------+
| |qir|       | |qbraid|    | |cirq|      | |qosf|      |
+-------------+-------------+-------------+-------------+

.. |qir| image:: _static/pkg-logos/qir.png
   :align: middle
   :width: 100px
   :target: QIR_

.. |qbraid| image:: _static/pkg-logos/qbraid.png
   :align: middle
   :width: 100px
   :target: qBraid_

.. |cirq| image:: _static/pkg-logos/cirq.png
   :align: middle
   :width: 100px
   :target: Cirq_

.. |qosf| image:: _static/pkg-logos/qosf.png
   :align: middle
   :width: 100px
   :target: QOSF_

.. _QIR: https://www.qir-alliance.org/
.. _qBraid: https://docs.qbraid.com/en/latest/
.. _Cirq: https://quantumai.google/cirq
.. _QOSF: https://qosf.org/

|

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   userguide/cirq_qir
   userguide/qasm3_qir
   userguide/qasm3_supported

.. toctree::
   :maxdepth: 1
   :caption: API Reference
   :hidden:

   api/qbraid_qir
   api/qbraid_qir.cirq
   api/qbraid_qir.qasm3
   api/qbraid_qir.runner


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`