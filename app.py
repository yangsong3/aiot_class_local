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

    @app.post("/api/<device>")
    def control(device: str) -> tuple[Response, int]:
        if device not in {"led", "button"}:
            return jsonify(error="지원하지 않는 장치입니다."), 404
        if device == "button" and not devices.mock:
            return jsonify(error="실제 버튼은 장치에서 눌러주세요."), 403
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or type(body.get("on")) is not bool:
            return jsonify(error='JSON의 "on"에는 true 또는 false를 입력하세요.'), 400
        if device == "led":
            devices.set_led(body["on"])
        else:
            devices.set_mock_button(body["on"])
        return jsonify(devices.state()), 200

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="라즈베리파이 GPIO 웹 실습")
    parser.add_argument("--mock", action="store_true", help="실제 GPIO 없이 모의 실행")
    parser.add_argument("--host", default="0.0.0.0", help="접속 허용 주소")
    parser.add_argument("--port", type=int, default=5000, help="웹 포트")
    args = parser.parse_args()
    try:
        devices = Devices(mock=args.mock)
    except (ImportError, RuntimeError, OSError, ValueError) as error:
        parser.exit(1, f"GPIO 초기화 실패: {error}\n배선·권한·RPi.GPIO 설치를 확인하세요. PC에서는 --mock을 사용하세요.\n")
    try:
        create_app(devices).run(host=args.host, port=args.port, debug=False, use_reloader=False)
    finally:
        devices.cleanup()


if __name__ == "__main__":
    main()
