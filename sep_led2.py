#! /usr/bin/env python
import time
import RPi.GPIO as GPIO

GPIO.cleanup()

led = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT, initial=GPIO.LOW)

try:
    n = 0
    while True:
        GPIO.output(led, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(led, GPIO.LOW)
        time.sleep(1)
        n += 1
        if n == 5:
            break

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

