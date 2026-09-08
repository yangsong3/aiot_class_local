"""실행: python app.py / PC에서 실행: python app.py --mock"""
import argparse
from flask import Flask, Response, jsonify, render_template, request
from gpio_control import Devices

def create_app(devices: Devices) -> Flask:
    app = Flask(__name__)
    @app.get("/")
    def index() -> str:
        return render_template("index.html", state=devices.state())
    @app.get("/api/state")
    def state() -> Response:
        response = jsonify(devices.state())
        response.headers["Cache-Control"] = "no-store"
        return response
    @app.post("/api/led")
    def control_led() -> tuple[Response, int]:
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or type(body.get("on")) is not bool:
            return jsonify(error='"on"에 true 또는 false를 입력하세요.'), 400
        devices.set_led(body["on"])
        return jsonify(devices.state()), 200
    @app.post("/api/motor")
    def control_motor() -> tuple[Response, int]:
        body = request.get_json(silent=True)
        direction = body.get("direction") if isinstance(body, dict) else None
        if direction not in {"forward", "reverse", "stop"}:
            return jsonify(error="모터 방향 값이 올바르지 않습니다."), 400
        devices.set_motor(direction)
        return jsonify(devices.state()), 200
    @app.post("/api/ultrasonic")
    def control_ultrasonic() -> tuple[Response, int]:
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or type(body.get("on")) is not bool:
            return jsonify(error='"on"에 true 또는 false를 입력하세요.'), 400
        devices.set_ultrasonic(body["on"])
        return jsonify(devices.state()), 200
    return app

def main() -> None:
    parser = argparse.ArgumentParser(description="라즈베리파이 센서 제어 대시보드")
    parser.add_argument("--mock", action="store_true", help="실제 GPIO 없이 모의 실행")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    try:
        devices = Devices(mock=args.mock)
    except (ImportError, RuntimeError, OSError, ValueError) as error:
        parser.exit(1, f"GPIO 초기화 실패: {error}\nPC에서는 --mock을 사용하세요.\n")
    try:
        create_app(devices).run(host=args.host, port=args.port, debug=False, use_reloader=False)
    finally:
        devices.cleanup()

if __name__ == "__main__":
    main()
