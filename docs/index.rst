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

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   userguide/overview
   userguide/cirq_qir

.. toctree::
   :maxdepth: 1
   :caption: API Reference
   :hidden:

   api/qbraid_qir
   api/qbraid_qir.cirq


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`