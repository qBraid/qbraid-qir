# sparse_simulator.py

import subprocess
from typing import Dict, List, Optional


class Simulator:
    """A sparse simulator that extends the functionality of the qir-runner.

    This simulator is a Python wrapper for the qir-runner, a command-line tool
    for executing compiled QIR files. It uses sparse matrices to represent quantum
    states and can be used to simulate quantum circuits that have been compiled to QIR.
    The simulator allows for setting a seed for random number generation and specifying
    an entry point for the execution.

    The qir-runner can be found at: https://github.com/qir-alliance/qir-runner

    Attributes:
        seed (optional, int): The value to use when seeding the random number generator used for quantum simulation.
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def run(
        self, file_name: str, entrypoint: Optional[str] = None, shots: Optional[int] = None
    ) -> Dict[str, List[int]]:
        """Runs the qir-runner executable with the given QIR file and shots.

        Args:
            file_name (str): Path to the QIR file to run ('.ll' or '.bc' file extension)
            entrypoint (optional, str): Name of the entrypoint function to execute in the QIR file.
            shots (optional, int): The number of times to repeat the execution of the chosen entry point in the program [default: 1].

        Returns:
            A dictionary mapping 'qubit_i' to a list of measurement results.
        """
        # Build the command with required and optional arguments
        command = ["qir-runner", "--shots", str(shots), "-f", file_name]
        if entrypoint:
            command.extend(["-e", entrypoint])
        if self.seed is not None:
            command.extend(["-r", str(self.seed)])

        # Execute the qir-runner with the built command
        output = subprocess.check_output(command, text=True)

        # Initialize results dictionary
        results: Dict[str, List[int]] = {}
        current_shot_results = []

        # Parse the output for the results
        for line in output.splitlines():
            if line.startswith("METADATA") and "required_num_results" in line:
                num_results = int(line.split("\t")[-1].strip())
            elif line.startswith("OUTPUT\tRESULT"):
                bit = line.split("\t")[-1].strip()
                current_shot_results.append(int(bit))
            elif line.startswith("END"):
                # Distribute the results to the appropriate qubits and reset for next block
                for idx, result in enumerate(current_shot_results):
                    key = f"qubit_{idx}"
                    if key not in results:
                        results[key] = []
                    results[key].append(result)
                current_shot_results = []

        return results

    def __repr__(self):
        return f"Simulator(seed={self.seed})"
