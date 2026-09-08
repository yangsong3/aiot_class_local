"""RPi.GPIO 장치 제어와 PC 실습용 모의 장치."""
from importlib import import_module
from threading import Lock
from time import monotonic, perf_counter, sleep
from types import ModuleType
from typing import Literal, TypedDict, cast
from pins import (DC_MOTOR_L_PIN, DC_MOTOR_R_PIN, HUMIDITY_TEMPERATURE_PIN,
                  LED_PIN, ULTRASONIC_ECHO_PIN, ULTRASONIC_TRIG_PIN)

MotorDirection = Literal["forward", "reverse", "stop"]
class DeviceState(TypedDict):
    mock: bool
    led: bool
    motor: MotorDirection
    temperature: float | None
    humidity: float | None
    distance: float | None
    ultrasonic_on: bool
    pins: dict[str, int]

class Devices:
    def __init__(self, mock: bool = False) -> None:
        self.mock = mock
        self._gpio: ModuleType | None = None
        self._led = False
        self._motor: MotorDirection = "stop"
        self._ultrasonic_on = True
        self._temperature: float | None = 24.0 if mock else None
        self._humidity: float | None = 50.0 if mock else None
        self._last_dht_read = 0.0
        self._lock = Lock()
        pins = (LED_PIN, DC_MOTOR_L_PIN, DC_MOTOR_R_PIN, HUMIDITY_TEMPERATURE_PIN,
                ULTRASONIC_ECHO_PIN, ULTRASONIC_TRIG_PIN)
        if len(set(pins)) != len(pins) or not all(0 <= pin <= 27 for pin in pins):
            raise ValueError("서로 다른 유효한 BCM GPIO 번호를 지정하세요.")
        if not mock:
            gpio = import_module("RPi.GPIO")
            gpio.setwarnings(False)
            gpio.setmode(gpio.BCM)
            try:
                for pin in (LED_PIN, DC_MOTOR_L_PIN, DC_MOTOR_R_PIN, ULTRASONIC_TRIG_PIN):
                    gpio.setup(pin, gpio.OUT, initial=gpio.LOW)
                gpio.setup(ULTRASONIC_ECHO_PIN, gpio.IN)
                gpio.setup(HUMIDITY_TEMPERATURE_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)
            except Exception:
                gpio.cleanup(list(pins))
                raise
            self._gpio = gpio

    def state(self) -> DeviceState:
        with self._lock:
            self._read_dht_if_due()
            return DeviceState(mock=self.mock, led=self._led, motor=self._motor,
                temperature=self._temperature, humidity=self._humidity,
                distance=(35.0 if self.mock else self._read_distance()) if self._ultrasonic_on else None,
                ultrasonic_on=self._ultrasonic_on,
                pins={"led": LED_PIN, "motor_l": DC_MOTOR_L_PIN, "motor_r": DC_MOTOR_R_PIN,
                      "dht": HUMIDITY_TEMPERATURE_PIN, "ultrasonic_trig": ULTRASONIC_TRIG_PIN,
                      "ultrasonic_echo": ULTRASONIC_ECHO_PIN})

    def set_led(self, on: bool) -> None:
        with self._lock:
            if self._gpio: self._gpio.output(LED_PIN, self._gpio.HIGH if on else self._gpio.LOW)
            self._led = on

    def set_motor(self, direction: str) -> None:
        with self._lock:
            levels = {"forward": (1, 0), "reverse": (0, 1), "stop": (0, 0)}[direction]
            if self._gpio:
                self._gpio.output(DC_MOTOR_L_PIN, levels[0])
                self._gpio.output(DC_MOTOR_R_PIN, levels[1])
            self._motor = cast(MotorDirection, direction)

    def set_ultrasonic(self, on: bool) -> None:
        with self._lock:
            self._ultrasonic_on = on
            if not on and self._gpio:
                self._gpio.output(ULTRASONIC_TRIG_PIN, self._gpio.LOW)

    def _read_distance(self) -> float | None:
        if not self._gpio: return None
        gpio = self._gpio
        gpio.output(ULTRASONIC_TRIG_PIN, gpio.HIGH); sleep(0.00001)
        gpio.output(ULTRASONIC_TRIG_PIN, gpio.LOW)
        deadline = perf_counter() + 0.03
        while gpio.input(ULTRASONIC_ECHO_PIN) == gpio.LOW:
            if perf_counter() >= deadline: return None
        start = perf_counter(); deadline = start + 0.03
        while gpio.input(ULTRASONIC_ECHO_PIN) == gpio.HIGH:
            if perf_counter() >= deadline: return None
        distance = (perf_counter() - start) * 17150
        return round(distance, 1) if 2 <= distance <= 400 else None

    def _read_dht_if_due(self) -> None:
        now = monotonic()
        if self.mock or now - self._last_dht_read < 2: return
        self._last_dht_read = now
        reading = self._read_dht11()
        if reading: self._humidity, self._temperature = reading

    def _read_dht11(self) -> tuple[float, float] | None:
        if not self._gpio: return None
        gpio = self._gpio
        gpio.setup(HUMIDITY_TEMPERATURE_PIN, gpio.OUT)
        gpio.output(HUMIDITY_TEMPERATURE_PIN, gpio.LOW); sleep(0.02)
        gpio.output(HUMIDITY_TEMPERATURE_PIN, gpio.HIGH); sleep(0.00004)
        gpio.setup(HUMIDITY_TEMPERATURE_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)
        changes: list[tuple[int, int]] = []; last = gpio.input(HUMIDITY_TEMPERATURE_PIN)
        started = perf_counter()
        while len(changes) < 83 and perf_counter() - started < 0.01:
            current = gpio.input(HUMIDITY_TEMPERATURE_PIN)
            if current != last:
                changes.append((current, int((perf_counter() - started) * 1_000_000))); last = current
        highs = [changes[i + 1][1] - changes[i][1] for i in range(len(changes) - 1) if changes[i][0] == 1]
        if len(highs) < 40: return None
        bits = [int(width > 50) for width in highs[-40:]]
        data = [sum(bits[n * 8 + k] << (7 - k) for k in range(8)) for n in range(5)]
        if (sum(data[:4]) & 0xFF) != data[4]: return None
        return float(data[0]), float(data[2])

    def cleanup(self) -> None:
        with self._lock:
            if self._gpio:
                try:
                    self._gpio.output([LED_PIN, DC_MOTOR_L_PIN, DC_MOTOR_R_PIN, ULTRASONIC_TRIG_PIN], self._gpio.LOW)
                finally:
                    self._gpio.cleanup(); self._gpio = None
            self._led = False; self._motor = "stop"
