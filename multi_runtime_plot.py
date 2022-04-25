#!/usr/bin/env python3

from time import strftime, gmtime, sleep
from datetime import datetime, timedelta
from string import Template
import time
import math
import os.path
from os import path
import pandas as pd
import argparse
import sys
import matplotlib.pyplot as plt
import copy
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator, FuncFormatter, NullFormatter)
import matplotlib.font_manager

CSV_COUNT = 3
FILE_TURBO = 'flashlight_turbo.csv'
FILE_HIGH = 'flashlight_high.csv'
FILE_MEDIUM = 'flashlight_medium.csv'
FILE_LOW = 'flashlight_low.csv'

plt.rcParams["font.family"] = 'sans-serif'
PX = 1/plt.rcParams['figure.dpi']
TEMP_STEP = 2
SMALL_SIZE = 8
MEDIUM_SIZE = 9 
BIGGER_SIZE = 12
TITLE_SIZE = 14
SUBTITLE_SIZE = 10

# https://xkcd.com/color/rgb/
COLOUR_LUMENS = 'xkcd:bright blue'
COLOUR_TEMP = 'xkcd:bright red'
COLOUR_TURBO = 'xkcd:bright blue'
COLOUR_HIGH = 'xkcd:bright red'
COLOUR_MEDIUM = 'xkcd:goldenrod'
COLOUR_LOW = 'xkcd:kelly green'

class DeltaTemplate(Template):
    delimiter = "%"


def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(int(tdelta.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-in','--inputfile', dest='filename', 
            help = 'filename for the csv input')
    parser.add_argument('-lf', '--lux-to-lumen-factor', dest='lux_to_lumen_factor', type=float, 
            help = 'lux to lumen conversion factor for use in calibrated integrating enclosures')
    parser.add_argument('-ts', '--temp-sensor', dest='temp_sensor', choices=['mcp9808'],
            help = 'temp sensor')
    parser.add_argument('-g', '--graph-title', dest='graph_title',
            help = 'graph title')
    parser.add_argument('-gs', '--graph-subtitle', dest='graph_subtitle',
            help = 'graph subtitle')
    parser.add_argument('-yl', '--y-label', dest='y_label',
            default = 'Lumens',
            help = 'y label (e.g. Lumens)')
    parser.add_argument('-glmin', '--graph-lumens-min', dest='graph_lumens_min', type=int,
            default = 0,
            help = 'graph lumens min')
    parser.add_argument('-ls', '--lumens-step', dest='lumens_step', type=int,
            default = 100,
            help = 'lumens step')
    parser.add_argument('-glmax', '--graph-lumens-max', dest='graph_lumens_max', type=int,
            default = 1800,
            help = 'graph lumens max')
    parser.add_argument('-gtmin', '--graph-temp-min', dest='graph_temp_min', type=int,
            default = 18,
            help = 'graph temperature min')
    parser.add_argument('-gtmax', '--graph-temp-max', dest='graph_temp_max', type=int,
            default = 68,
           help = 'graph temperature max')
    parser.add_argument('-dmax', '--duration-max', dest='duration_max', type=int,
            default = 7200,
            help = 'max duration in seconds')
    parser.add_argument('-dminor', '--duration-minor', dest='duration_minor', type=int,
            default = 300,
            help = 'minor gridlines for duration in seconds')
    parser.add_argument('-dmajor', '--duration-major', dest='duration_major', type=int,
            default = 600,
            help = 'major gridlines for duration in seconds')
    parser.add_argument('-wi', '--width', dest='width', type=int,
            default = 1000,
            help = 'width')
    parser.add_argument('-hi', '--height', dest='height', type=int,
            default = 610,
            help = 'height')
    parser.add_argument('-wa', '--watermark', dest='watermark',
            default = '',
            help = 'watermark')
    parser.add_argument('-wx', '--watermark-x', dest='watermark_x', type=float,
            default = 0.08,
            help = 'x location of watermark')
    parser.add_argument('-wy', '--watermark-y', dest='watermark_y', type=float,
            default = 0.3,
            help = 'y location of watermark')
    return parser


def load_options():
    parser = build_parser()
    options = parser.parse_args()
    return options


def convert_time_to_seconds(data):
    # Make Duration start at zero (use Time to calculate duration).
    time_start = datetime.fromtimestamp(data.Time.min())
    data.Time = data.Time.map(lambda x: (datetime.fromtimestamp(x) - time_start).total_seconds())
    return data.Time


def runtimeplot(options):
    
    print('Creating plot...')
    data_low = pd.read_csv(FILE_LOW)
    time_start = datetime.fromtimestamp(data_low.Time.min()) # place after first CSV
    data_low.Time = convert_time_to_seconds(data_low)
    data_low.set_index('Time', drop=False)
    data_medium = pd.read_csv(FILE_MEDIUM)
    data_medium.Time = convert_time_to_seconds(data_medium)
    data_medium.set_index('Time', drop=False)
    data_high = pd.read_csv(FILE_HIGH)
    data_high.Time = convert_time_to_seconds(data_high)
    data_high.set_index('Time', drop=False)
    data_turbo = pd.read_csv(FILE_TURBO)
    data_turbo.Time = convert_time_to_seconds(data_turbo)
    data_turbo.set_index('Time', drop=False)

    #Time,Lux,[relative time],Duration,Lumens,Temperature (C)
    data_turbo.columns = ['Time', 'Turbo', 'rel_time', 'Duration', 'Lumens', 'temp']
    data_high.columns = ['Time', 'High', 'rel_time', 'Duration', 'Lumens', 'temp']
    data_medium.columns = ['Time', 'Medium', 'rel_time', 'Duration', 'Lumens', 'temp']
    data_low.columns = ['Time', 'Low', 'rel_time', 'Duration', 'Lumens', 'temp']

    data = data_low.join(data_medium[['Medium']])
    data = data.join(data_high[['High']])
    data = data.join(data_turbo[['Turbo']])
    
    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    fig, ax = plt.subplots(figsize=(options.width*PX, options.height*PX))
    plt.suptitle(options.graph_title + '\n', fontsize=TITLE_SIZE, x=0.01, ha='left')
    plt.rcParams['axes.titlepad'] = TITLE_SIZE
    fig.text(0.01, 0.92, options.graph_subtitle, fontsize=SUBTITLE_SIZE, ha='left', alpha=0.8)

    plt.grid(True, which='both')
    ax.minorticks_on()

    data.Turbo = data.Turbo / options.lux_to_lumen_factor
    data.High = data.High / options.lux_to_lumen_factor
    data.Medium = data.Medium / options.lux_to_lumen_factor
    data.Low = data.Low / options.lux_to_lumen_factor

    ax.plot(data.Time, data.Turbo, color=COLOUR_TURBO, label='Turbo')
    ax.plot(data.Time, data.High, color=COLOUR_HIGH, label='High')
    ax.plot(data.Time, data.Medium, color=COLOUR_MEDIUM, label='Medium')
    ax.plot(data.Time, data.Low, color=COLOUR_LOW, label='Low')
    ax.set_xlabel('Duration hh:mm:ss')
    ax.set_ylabel(options.y_label)
    ax.set_ylim((options.graph_lumens_min, options.graph_lumens_max))
    ax.set_yticks([x for x in range(options.graph_lumens_min, options.graph_lumens_max + options.lumens_step, options.lumens_step)])
    ax.yaxis.set_minor_locator(MultipleLocator(options.lumens_step))
    ax.yaxis.set_minor_formatter(NullFormatter())

    formatter = FuncFormatter(lambda s, x: strfdelta(((time_start + pd.to_timedelta(s, unit='s')) - time_start), '%H:%M:%S'))
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_minor_locator(MultipleLocator(options.duration_minor))
    ax.set_xticks([x for x in range(0, (options.duration_max * 60) + 1, options.duration_major)])
    x_ticks = ax.xaxis.get_major_ticks()
    x_ticks[0].label1.set_visible(False)
    x_ticks[-1].label1.set_visible(False)

    fig.text(options.watermark_x, options.watermark_y, options.watermark, alpha=0.5, fontsize=TITLE_SIZE, ha='left')

    plt.xlim(left=0)
    plt.xlim(right=options.duration_max)

    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]

    # legend line thickness
    handles = [copy.copy(ha) for ha in lines]
    [ha.set_linewidth(CSV_COUNT - 1) for ha in handles]

    fig.legend(handles, labels,
        ncol=4444,
        loc='upper center',
        frameon=False,
        bbox_to_anchor=(0.5, 0.92),
        borderaxespad=0,
        bbox_transform=fig.transFigure,
        handlelength=0.7
    )

    plt.tight_layout()
    plt.savefig(options.graph_title.replace(' ', '_').lower()+'.png')
    print('plot saved')


def main():
    options = load_options()
    runtimeplot(options)


if __name__ == "__main__":
    main()
