#!/usr/bin/env python3

from time import strftime, gmtime, sleep
import time
import math
import os.path
from os import path
import csv
import board
import busio
import adafruit_tsl2591
import adafruit_veml7700
import adafruit_mcp9808
import adafruit_mcp9600
import RPi.GPIO as GPIO
import argparse
import sys
import matplotlib.pyplot as plt

ready_led = 17
running_led = 27
complete_led = 22
sensor_ceiling = 88000.0
light_sensor = None
temp_sensor = None


def init(options):
    i2c = busio.I2C(board.SCL, board.SDA)
    if options.light_sensor:
        if options.light_sensor == 'veml7700':
            light_sensor = adafruit_veml7700.VEML7700(i2c)
            light_sensor.light_gain = light_sensor.ALS_GAIN_1_8
            light_sensor.light_integration_time = light_sensor.ALS_100MS
            sensor_ceiling = 120000.0
        elif options.light_sensor == 'tsl2591':
            light_sensor = adafruit_tsl2591.TSL2591(i2c)
            light_sensor.gain = adafruit_tsl2591.GAIN_LOW
            #light_sensor.gain = adafruit_tsl2591.GAIN_HIGH
    else:
        light_sensor = adafruit_tsl2591.TSL2591(i2c)
        light_sensor.gain = adafruit_tsl2591.GAIN_LOW
        #light_sensor.gain = adafruit_tsl2591.GAIN_HIGH

    if options.temp_sensor:
        if options.temp_sensor == 'mcp9808':
            temp_sensor = adafruit_mcp9808.MCP9808(i2c)
        elif options.temp_sensor == 'mcp9600':
            temp_sensor = adafruit_mcp9600.MCP9600(i2c)
    else:
        temp_sensor = None

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ready_led, GPIO.OUT)
    GPIO.setup(running_led, GPIO.OUT)
    GPIO.setup(complete_led, GPIO.OUT)
    GPIO.output(ready_led, GPIO.HIGH)
    GPIO.output(running_led, GPIO.LOW)
    GPIO.output(complete_led, GPIO.LOW)
    return light_sensor, temp_sensor


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o','--outputfile', dest='filename', 
            default=time.strftime('RuTiTe%Y-%m-%d-%H.%M.%S.csv', time.localtime()),
            help = 'filename for the csv output')
    parser.add_argument('-i','--interval', dest='delay', type=float, 
            default = 0.1, 
            help = 'interval between measurements in seconds (halved during the 30s sampling period at the beginning of the test)')
    parser.add_argument('-d','--duration', dest='test_duration', type=float, 
            help = 'maximum duration of the test in minutes')
    parser.add_argument('-tp','--termination-percentage', dest='termination_percentage', type=float, 
            help = 'percent output to stop recording at')
    parser.add_argument('-pp','--print-percentage', dest='percent_change_to_print', type=float, 
            default = 5.0, 
            help = 'percent change between printed updates to the terminal')
    parser.add_argument('-pd','--print-delay', dest='time_between_prints', type=float, 
            help = 'minutes between printed updates to the terminal')
    parser.add_argument('-lf', '--lux-to-lumen-factor', dest='lux_to_lumen_factor', type=float, 
            help = 'lux to lumen conversion factor for use in calibrated integrating enclosures')
    parser.add_argument('-r', '--relative-time', dest='relative_time',
            help = 'record relative time, with the first measurement at t=0', action='store_true')
    parser.add_argument('-g', '--graph-title', dest='graph_title',
            help = 'string to use for a basic plot of the recorded data - only works if you let the script run until it stops based on time or percent output')
    parser.add_argument('-ls', '--light-sensor', dest='light_sensor', choices=['tsl2591', 'veml7700'],
            help = 'light sensor')
    parser.add_argument('-ts', '--temp-sensor', dest='temp_sensor', choices=['mcp9600', 'mcp9808'],
            help = 'temp sensor')
    return parser


def load_options():
    parser = build_parser()
    options = parser.parse_args()
    if options.time_between_prints:
        options.time_between_prints *= 60
    if options.test_duration:
        options.test_duration *= 60
    if os.path.isfile(options.filename):
        print ("{}{} already exists. Checking for an an available name to avoid overwriting something important...".format(current_timestamp(), options.filename))
        options.filename = time.strftime('RuTiTe%Y-%m-%d-%H.%M.%S.csv', time.localtime())
    print ("{}Saving as {}".format(current_timestamp(),options.filename))
    return options


def blink_led(pin):
    GPIO.output(pin, not GPIO.input(pin))


def current_timestamp():
    return time.strftime("%H:%M:%S ", time.localtime())


def add_csv_header(filename):
    with open (filename, "a") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["Time", "Lux", "[relative time]", "Duration", "Lumens", "Temperature (C)"])
        blink_led(running_led)


def write_to_csv(options, t, lux, temp, t_test_start):
    if options.relative_time:
        t_relative = t - t_test_start
        duration = t_relative / 86400
    else:
        t_relative = ''
        duration = ''

    if options.lux_to_lumen_factor:
        lumens = lux / options.lux_to_lumen_factor
    else:
        lumens = ''

    with open (options.filename, "a") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow([t, lux, t_relative, duration, lumens, temp])


def core(options, light_sensor, temp_sensor):
    state = 'set_baseline'
    baseline_sum = 0.0
    baseline_measurement_count = 0
    ceiling_reached = False

    while state != 'exit':
        lux = light_sensor.lux
        t = time.time()
        temp = None
        if temp_sensor:
            temp = temp_sensor.temperature

        if lux == sensor_ceiling and ceiling_reached == False:
            print("{}Sensor is saturated. The light is too bright to measure with your current setup. Consider adding a filter between the source and the sensor. The test will continue, but will be cut off at the high end.".format(current_timestamp()))
            ceiling_reached = True

        if state == 'set_baseline':
            baseline_measurement_count += 1
            baseline_sum += lux

        if state == 'waiting_for_threshold':
            blink_led(ready_led)

        if state in ['sampling_period', 'main_recording']:
            write_to_csv(options, t, lux, temp, t_test_start)
            blink_led(running_led)

        if state == 'sampling_period':
            if lux < sampling_lux_min:
                sampling_lux_min = lux
            if lux > sampling_lux_max:
                sampling_lux_max = lux

        if state == 'main_recording':
            percent_output = lux / lux_at_30s * 100.0

            if options.time_between_prints and (t - last_print_time) > options.time_between_prints:
                print("{}Output is at {:.0f}% ({:.0f} lux)".format(current_timestamp(),percent_output, lux))
                last_print_time = t
                last_printed_percent = percent_output
            elif options.percent_change_to_print and abs(percent_output - last_printed_percent) >= options.percent_change_to_print:
                print("{}Output is at {:.0f}% ({:.0f} lux)".format(current_timestamp(),percent_output, lux))
                last_print_time = t
                last_printed_percent = percent_output

        if state in ['set_baseline', 'waiting_for_threshold', 'sampling_period'] and options.delay > 0.5:
            time.sleep(0.5)
        else:
            time.sleep(options.delay)

        if state == 'set_baseline' and baseline_measurement_count >= 5:
            threshold_lux = baseline_sum / baseline_measurement_count * 3.0
            state = 'waiting_for_threshold'
            print ("{}Ready to start the test. Turn on the light now.".format(current_timestamp()))

        if state == 'waiting_for_threshold' and lux >= threshold_lux:
            state = 'sampling_period'
            GPIO.output(ready_led, GPIO.HIGH)
            t_test_start = time.time()
            t_sampling_complete = t_test_start + 30.0
            if options.test_duration:
                t_test_complete = t_test_complete = t_test_start + options.test_duration
            sampling_lux_min = sensor_ceiling
            sampling_lux_max = 0.0
            print ("{}Light detected. Recording started.".format(current_timestamp()))
            time.sleep(0.1)

        if state == 'sampling_period' and t >= t_sampling_complete:
            state = 'main_recording'
            lux_at_30s = lux
            print("{}Sampling period complete. The output at 30s was {:.1f} lux. Sampling period max = {:.1f} lux, min = {:.1f} lux.".format(current_timestamp(), lux_at_30s, sampling_lux_max, sampling_lux_min))
            text_to_print = '\tThe test will run until you stop it'
            if options.test_duration:
                text_to_print += ', or it has recorded for {:.0f} minutes'.format(options.test_duration/60)
            if options.termination_percentage:
                termination_output = lux_at_30s * options.termination_percentage / 100
                text_to_print += ', or it reaches {:.1f} lux ({:.1f}% of the output at 30s)'.format(termination_output, options.termination_percentage)
            print(text_to_print + '.')
            last_printed_percent = 100.0
            last_print_time = t
            percent_output = 100.0

        if state == 'main_recording':
            if options.test_duration and t >= t_test_complete:
                state = 'exit'
            if options.termination_percentage and percent_output <= options.termination_percentage:
                state = 'checking_termination'
                print("{}Output has reached {:.0f}% ({:.0f} lux), which is at or below your {}% target. The test will stop if output doesn't increase within 5 minutes.".format(current_timestamp(), percent_output, lux, options.termination_percentage))
                last_print_time = t
                last_printed_percent = percent_output
                t_output_termination = t + 5.0 * 60.0
                options.test_duration = True
                
        if state == 'checking_termination':
            if t > t_output_termination:
                state = 'exit'
            elif percent_output > options.termination_percentage:
                state = 'main_recording'
                print('{}Output increased. Continuing to record.'.format(current_timestamp()))

    print("{}Test complete".format(current_timestamp()))
    GPIO.output(ready_led, GPIO.LOW)
    GPIO.output(running_led, GPIO.LOW)
    GPIO.output(complete_led, GPIO.HIGH)


def runtimeplot(options):
    
    print('Creating plot...')
    fig = plt.figure(figsize=(15, 10))

    time = []
    brightness = []
    temperature = []

    with open(options.filename, 'r') as csvfile:
        data = csv.reader(csvfile, delimiter=',')
        next(data)
        for row in data:
            time.append(float(row[0]))
            if options.lux_to_lumen_factor:
                brightness.append(float(row[4]))
                y_label = 'Lumens'
            else:
                brightness.append(float(row[1]))
                y_label = 'Lux'
            if options.temp_sensor:
                temperature.append(float(row[5]))

    t_test_start = time[1]
    time = [(x - t_test_start) / 60 for x in time]
    ax = fig.add_subplot(111)
    ax.plot(time, brightness, color="blue")
    ax.set_xlabel('Duration (minutes)')
    ax.set_ylabel(y_label, color="blue")
    if options.temp_sensor:
        ax2 = ax.twinx()
        ax2.plot(time, temperature, color="red")
        ax2.set_ylabel('Temperature (C)', color="red")
    plt.title(options.graph_title)
    plt.grid(True)
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.savefig(options.graph_title.replace(' ', '_').lower()+'.png')
    print('plot saved')


def main():
    options = load_options()
    light_sensor, temp_sensor = init(options)
    add_csv_header(options.filename)
    core(options, light_sensor, temp_sensor)
    if options.graph_title:
        runtimeplot(options)


if __name__ == "__main__":
    main()
