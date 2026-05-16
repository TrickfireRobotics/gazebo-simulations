from pypresence import Presence
import time


def rpc_start(is_docker: bool = False, robot_name: str = "Unknown Robot") -> None:
    client_id = "1504990746527404063"
    rpc = Presence(client_id)
    rpc.connect()
    rpc.update(
        name="TrickFire Simulation (" + robot_name + ")",
        details="Running TrickFire Simulation on " + robot_name,
        state="Running in Docker" if is_docker else "Running locally",
    )
    print("RPC started")
    while True:
        print("RPC thread alive")
        time.sleep(15)
