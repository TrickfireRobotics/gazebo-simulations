import threading

import rclpy
import uvicorn
from fastapi import FastAPI, HTTPException
from rclpy.node import Node
from rosidl_runtime_py.convert import message_to_ordereddict
from rosidl_runtime_py.utilities import get_message


class API(Node):
    def __init__(self) -> None:
        super().__init__("webbridge_api")
        self._app = FastAPI()
        self._lock = threading.Lock()
        self._subs: dict = {}
        self._info: dict = {}
        self._refresh_subscriptions()
        self._app.add_api_route("/topics", self._list_topics)
        self._app.add_api_route("/refresh", self._refresh_subscriptions)
        self._app.add_api_route("/{topic:path}", self._get_info, methods = ["POST", "GET"])


    def _refresh_subscriptions(self) -> dict:
        added = []
        for topic, types in self.get_topic_names_and_types():
            if topic in self._subs or not types:
                continue
            try:
                msg_cls = get_message(types[0])
            except (AttributeError, ModuleNotFoundError, ValueError):
                continue
            self._subs[topic] = self.create_subscription(
                msg_cls,
                topic,
                lambda msg, t=topic: self._update_info(t, msg),
                10,
            )
            added.append(topic)
        return {"subscribed": added, "total": len(self._subs)}

    def _list_topics(self) -> list[str]:
        return sorted(self._subs.keys())

    def _update_info(self, topic: str, msg) -> None:
        with self._lock:
            self._info[topic] = msg

    def _get_info(self, topic: str):
        key = "/" + topic
        with self._lock:
            msg = self._info.get(key)
        if msg is None:
            raise HTTPException(status_code=404, detail=f"no message received on {key}")
        return message_to_ordereddict(msg)


def main():
    rclpy.init()
    node = API()
    executor_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    executor_thread.start()
    try:
        uvicorn.run(node._app, host="0.0.0.0", port=9090)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
