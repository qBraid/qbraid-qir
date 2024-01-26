from typing import List, Optional
from pyqir import Context, Module

from openqasm3 import parser
import uuid 
  


def generate_module_id(qasm_program):
  """
  Generates a QIR module ID from a given openqasm3 program.
  """

  #TODO: Consider a better approach of generating a unique identifier.
  generated_id = uuid.uuid1()
  return f'circuit-{generated_id}'


class Qasm3Module:
    """
    A module representing an openqasm3 quantum program using QIR.

    Args:
        name (str): Name of the module.
        module (Module): QIR Module instance.
        num_qubits (int): Number of qubits in the circuit.
        elements (List[Statement]): List of openqasm3 Statements.
    """

    def __init__(
        self,
        name: str,
        module: Module,
        num_qubits :int,
        elements
    ):
      self._name = name
      self._module = module
      self._num_qubits = num_qubits
      self._elements = elements


    @property
    def name(self) -> str:
        """Returns the name of the module."""
        return self._name

    @property
    def module(self) -> Module:
        """Returns the QIR Module instance."""
        return self._module

    @property
    def num_qubits(self) -> int:
        """Returns the number of qubits in the circuit."""
        return self._num_qubits


    @classmethod
    def from_program(
        cls, 
        program: openqasm3.ast.Program,
        module: Optional[Module] = None
    ):
      """
      Class method. Construct a Qasm3Module from a given openqasm3.ast.Program object
      and an optional QIR Module.
      """
      elements: List[Statement] = []

      # parsing
      parsed_program = parser.parse(program)
      statements = parsed_program.statements
      for statement in statements:
        if isinstance(statement, QubitDeclaration):
          number_of_qubits = statement.size.value
        elements.append(statement)

      if module is None:
        module = Module(Context(), generate_module_id(parsed_program)) 

      return cls(
          name="main",
          module=module,
          num_qubits=number_of_qubits,
          elements=elements,)
      

    def accept(self, visitor):
      #TODO: implement this method when QASMVisitor is implemented.
      
      # for elem in self._elements:
      #   visitor.visit(elem)
      pass