# OpenQASM 3 to QIR

| openqasm3.ast Object Type      | Supported   | Comment                |
| -------------------------------| ----------- | ---------------------- |
| QuantumMeasurementStatement    | ✅          | Complete               |
| QuantumReset                   | ✅          | Complete               |
| QuantumBarrier                 | ✅          | Complete               |
| QuantumGateDefinition          | ✅          | Complete               |
| QuantumGate                    | ✅          | Complete               |
| QuantumGateModifier            | ✅          | Complete               |
| QubitDeclaration               | ✅          | Completed              |
| Clbit Declarations             | ✅          | Completed              |
| Pulse-level ops (e.g. delay)   | ❌          | Not supported by QIR   |
| BranchingStatement             | 🔜          | In progress            |
| SubroutineDefinition           | 🔜          | In progress            |
| ClassicalDeclaration           | 🔜          | In progress            |
| ConstantDeclaration            | 🔜          | In progress            |
| BinaryExpression               | 🔜          | In progress            |
| UnaryExpression                | 🔜          | In progress            |
| ClassicalAssignment            | 🔜          | In progress            |
| AliasStatement                 | 📋          | Planned                |
| IODeclaration                  | 📋          | Planned                |
| Span                           | 📋          | Planned                |
| RangeDefinition                | 📋          | Planned                |
