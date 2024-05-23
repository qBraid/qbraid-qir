# OpenQASM 3 to QIR

## Supported conversions status table

| openqasm3.ast Object Type      | Supported   | Comment                |
| -------------------------------| ----------- | ---------------------- |
| QuantumMeasurementStatement    | ✅          | Complete               |
| QuantumReset                   | ✅          | Complete               |
| QuantumBarrier                 | ✅          | Complete               |
| QuantumGateDefinition          | ✅          | Complete               |
| QuantumGate                    | ✅          | Complete               |
| QuantumGateModifier            | ✅          | Complete (pow, inv)    |
| QubitDeclaration               | ✅          | Completed              |
| Clbit Declarations             | ✅          | Completed              |
| BinaryExpression               | ✅          | In progress            | 
| UnaryExpression                | ✅          | In progress            |
| BranchingStatement             | 🔜          | In progress            |
| SubroutineDefinition           | 🔜          | In progress            |
| ClassicalDeclaration           | 🔜          | In progress            |
| ConstantDeclaration            | 🔜          | In progress            |
| ClassicalAssignment            | 🔜          | In progress            |
| Looping statements(eg. for)    | 📋          | Planned                |
| AliasStatement                 | 📋          | Planned                |
| IODeclaration                  | 📋          | Planned                |
| RangeDefinition                | 📋          | Planned                |
| Pragma                         | ❓          | Unsure                 |
| Annotations                    | ❓          | Unsure                 |
| Pulse-level ops (e.g. delay)   | ❌          | Not supported by QIR   |
| Calibration ops                | ❌          | Not supported by QIR   |
| Duration literals              | ❌          | Not supported by QIR   |
| ComplexType                    | ❌          | Not supported by QIR   |
