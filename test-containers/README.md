# Test containers

Docker containers used for testing.

## QIR Runner

[Docker image](./qir_runner/Dockerfile) providing an environment for testing and executing QIR programs
with the [qir-runner](https://github.com/qir-alliance/qir-runner/tree/main) package.

### Build & run image

Build the QIR runner image:

```shell
docker build -t qbraid-test/qir-runner:latest qir_runner
```

Start the container running a Jupyter Server with the JupyterLab frontend and expose the container's internal port `8888` to port `8888` of the host machine:

```shell
docker run -p 8888:8888 qbraid-test/qir-runner:latest
```

Visiting `http://<hostname>:8888/?token=<token>` in a browser will launch JupyterLab, where:

- The hostname is the name of the computer running Docker (e.g. `localhost`)
- The token is the secret token printed in the console.

Alternatively, you can open a shell inside the running container directly:

```shell
docker exec -it <container_name> /bin/bash
```

### Testing

Once inside the container, the `qir-runner` executable is accessible via command-line:

```shell
Usage: qir-runner [OPTIONS] --file <PATH>

Options:
  -f, --file <PATH>        (Required) Path to the QIR file to run
  -e, --entrypoint <NAME>  Name of the entry point function to execute
  -s, --shots <NUM>        The number of times to repeat the execution of the chosen entry point in the program [default: 1]
  -r, --rngseed <NUM>      The value to use when seeding the random number generator used for quantum simulation
  -h, --help               Print help
```

Convert a cirq program and save the output to a file

```python
import cirq

from qbraid_qir import dumps
from qbraid_qir.cirq import cirq_to_qir

# create a test circuit
q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1))

# convert to QIR
module = cirq_to_qir(circuit, name="bell")

# saves to .ll and .bc files in working directory
dumps(module)
```

And then execute the QIR program:

```shell
qir-runner -f bell.bc
```
