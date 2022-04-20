#!/usr/bin/env python3

from time import strftime, gmtime, sleep
from datetime import timedelta
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

FILE_TURBO = 'flashlight_turbo.csv'
FILE_HIGH = 'flashlight_high.csv'
FILE_MEDIUM = 'flashlight_medium.csv'
FILE_LOW = 'flashlight_low.csv'

plt.rcParams["font.family"] = 'sans-serif'
PX = 1/plt.rcParams['figure.dpi']
LUMENS_STEP = 100
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
    parser.add_argument('-glmin', '--graph-lumens-min', dest='graph_lumens_min', type=int,
            default = 0,
            help = 'graph lumens min')
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


def runtimeplot(options):
    
    print('Creating plot...')
    data_turbo = pd.read_csv(FILE_TURBO, index_col=2)
    data_high = pd.read_csv(FILE_HIGH, index_col=2)
    data_medium = pd.read_csv(FILE_MEDIUM, index_col=2)
    data_low = pd.read_csv(FILE_LOW, index_col=2)

    #Time,Lux,[relative time],Duration,Lumens,Temperature (C)
    data_turbo.columns = ['time_1', 'rel_time_1', 'Duration', 'Turbo', 'temp_1']
    data_high.columns = ['time_2', 'rel_time_2', 'Duration', 'High', 'temp_2']
    data_medium.columns = ['time_3', 'rel_time_3', 'Duration', 'Medium', 'temp_3']
    data_low.columns = ['time_4', 'rel_time_4', 'Duration', 'Low', 'temp_4']

    data = pd.merge_asof(data_low, data_high)
    data = pd.merge_asof(data, data_medium)
    data = pd.merge_asof(data, data_turbo)
    
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

    # Make Duration start at zero.
    data.Duration = data.Duration.map(lambda x: x * 86400)
    duration_offset = data.Duration.min()
    print(f"duration_offset = {duration_offset}")
    data.Duration = data.Duration.map(lambda x: x - duration_offset)
    duration_offset = data.Duration.min()
    print(f"duration_offset = {duration_offset}")

    ax.plot(data.Duration, data.Turbo, color=COLOUR_TURBO, label='Turbo')
    ax.plot(data.Duration, data.High, color=COLOUR_HIGH, label='High')
    ax.plot(data.Duration, data.Medium, color=COLOUR_MEDIUM, label='Medium')
    ax.plot(data.Duration, data.Low, color=COLOUR_LOW, label='Low')
    ax.set_xlabel('Duration hh:mm:ss')
    ax.set_ylabel('Lumens')
    ax.set_ylim((options.graph_lumens_min, options.graph_lumens_max))
    ax.set_yticks([x for x in range(options.graph_lumens_min, options.graph_lumens_max + LUMENS_STEP, LUMENS_STEP)])
    ax.yaxis.set_minor_locator(MultipleLocator(100))
    ax.yaxis.set_minor_formatter(NullFormatter())

    formatter = FuncFormatter(lambda s, x: time.strftime('%H:%M:%S', time.gmtime(s)))
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
    [ha.set_linewidth(3) for ha in handles]

    fig.legend(handles, labels,
        ncol=4444,
        loc='upper center',
        frameon=False,
        #mode='expand',
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
