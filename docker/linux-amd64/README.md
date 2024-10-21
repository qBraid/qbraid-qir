# QIR Runner Docker Container

This Docker image provides an environment for testing and executing Quantum Intermediate Representation (QIR)
bytecode programs with the [qir-runner](https://github.com/qir-alliance/qir-runner/tree/main) package.

## Build & run image

To build the QIR runner image, run the following command:

```bash
./build.sh
```

To start the container, use the following command:

```bash
./run.sh <container_name>
```

To access an interactive shell inside the running container:

```bash
./exec.sh <container_name>
```

## Verify setup with bell circuit example

Once inside the running container, activate the Python virtual environment that contains `qbraid-qir` by running:

```bash
source /work/venv/bin/activate
```

Next, run one of the example scripts to verify the setup:

```bash
python3 /work/examples/cirq_bell.py
```

This should output something similar to:

```bash
Cirq Circuit: 
0: ───H───@───M───
          │   │
1: ───────X───M───

Running on: QirRunner(seed=None, exec_path=/opt/qir-runner/target/release/qir-runner, version=0.7.4)

Result: {...,'measurementCounts': {'00': 5, '11': 5}, 'runnerVersion': '0.7.4', 'runnerSeed': None}
```



