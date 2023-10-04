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

CSV_COUNT = 6
FILE_1 = 'imalent_ms12_mini_turbo.csv'
FILE_2 = 'imalent_ms12_mini_high.csv'
FILE_3 = 'imalent_ms12_mini_middle_2.csv'
FILE_4 = 'imalent_ms12_mini_middle_1.csv'
FILE_5 = 'imalent_ms12_mini_middle_low.csv'
FILE_6 = 'imalent_ms12_mini_low.csv'
LABEL_1 = 'Turbo'
LABEL_2 = 'High'
LABEL_3 = 'Middle 2'
LABEL_4 = 'Middle 1'
LABEL_5 = 'Middle Low'
LABEL_6 = 'Low'

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
COLOUR_1 = 'xkcd:bright blue'
COLOUR_2 = 'xkcd:bright red'
COLOUR_3 = 'xkcd:goldenrod'
COLOUR_4 = 'xkcd:kelly green'
COLOUR_5 = 'xkcd:orange'
COLOUR_6 = 'xkcd:light magenta'

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
    parser.add_argument('-ts', '--temp-sensor', dest='temp_sensor', choices=['mcp9600', 'mcp9808'],
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
    if CSV_COUNT >= 6:
      data_6 = pd.read_csv(FILE_6)
      if CSV_COUNT == 6:
        time_start = datetime.fromtimestamp(data_6.Time.min()) # place after first CSV
      data_6.Time = convert_time_to_seconds(data_6)
      data_6.set_index('Time', drop=False)
    if CSV_COUNT >= 5:
      data_5 = pd.read_csv(FILE_5)
      if CSV_COUNT == 5:
        time_start = datetime.fromtimestamp(data_5.Time.min()) # place after first CSV
      data_5.Time = convert_time_to_seconds(data_5)
      data_5.set_index('Time', drop=False)
    if CSV_COUNT >= 4:
      data_4 = pd.read_csv(FILE_4)
      if CSV_COUNT == 4:
        time_start = datetime.fromtimestamp(data_4.Time.min()) # place after first CSV
      data_4.Time = convert_time_to_seconds(data_4)
      data_4.set_index('Time', drop=False)
    if CSV_COUNT >= 3:
      data_3 = pd.read_csv(FILE_3)
      if CSV_COUNT == 3:
        time_start = datetime.fromtimestamp(data_3.Time.min()) # place after first CSV
      data_3.Time = convert_time_to_seconds(data_3)
      data_3.set_index('Time', drop=False)
    if CSV_COUNT >= 2:
      data_2 = pd.read_csv(FILE_2)
      if CSV_COUNT == 2:
        time_start = datetime.fromtimestamp(data_2.Time.min()) # place after first CSV
      data_2.Time = convert_time_to_seconds(data_2)
      data_2.set_index('Time', drop=False)
    if CSV_COUNT >= 1:
      data_1 = pd.read_csv(FILE_1)
      data_1.Time = convert_time_to_seconds(data_1)
      if CSV_COUNT == 1:
        time_start = datetime.fromtimestamp(data_1.Time.min()) # place after first CSV
      data_1.set_index('Time', drop=False)

    #Time,Lux,[relative time],Duration,Lumens,Temperature (C)

    if CSV_COUNT >= 1:
      data_1.columns = ['Time', 'FILE_1', 'rel_time', 'Duration', 'Lumens', 'temp']
    if CSV_COUNT >= 2:
      data_2.columns = ['Time', 'FILE_2', 'rel_time', 'Duration', 'Lumens', 'temp']
    if CSV_COUNT >= 3:
      data_3.columns = ['Time', 'FILE_3', 'rel_time', 'Duration', 'Lumens', 'temp']
    if CSV_COUNT >= 4:
      data_4.columns = ['Time', 'FILE_4', 'rel_time', 'Duration', 'Lumens', 'temp']
    if CSV_COUNT >= 5:
      data_5.columns = ['Time', 'FILE_5', 'rel_time', 'Duration', 'Lumens', 'temp']
    if CSV_COUNT >= 6:
      data_6.columns = ['Time', 'FILE_6', 'rel_time', 'Duration', 'Lumens', 'temp']

    # FIXME iterate over a collection instead....
    if CSV_COUNT == 6:
      data = data_6.join(data_5[['FILE_5']])
    if CSV_COUNT == 5:
      data = data_5.join(data_4[['FILE_4']])
    if CSV_COUNT == 4:
      data = data_4.join(data_3[['FILE_3']])
    if CSV_COUNT == 3:
      data = data_3.join(data_2[['FILE_2']])
    if CSV_COUNT == 2:
      data = data_2.join(data_1[['FILE_1']])
    if CSV_COUNT == 1:
      data = data_1

    if CSV_COUNT >= 6:
      data = data.join(data_4[['FILE_4']])
    if CSV_COUNT >= 5:
      data = data.join(data_3[['FILE_3']])
    if CSV_COUNT >= 4:
      data = data.join(data_2[['FILE_2']])
    if CSV_COUNT >= 3:
      data = data.join(data_1[['FILE_1']])
    
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
    #fig.text(0.01, 0.92, options.graph_subtitle, fontsize=SUBTITLE_SIZE, ha='left', alpha=0.8)
    fig.text(0.011, 0.938, options.graph_subtitle, fontsize=SUBTITLE_SIZE, ha='left', alpha=0.8)

    plt.grid(True, which='both')
    ax.minorticks_on()

    if CSV_COUNT >= 1:
      data.FILE_1 = data.FILE_1 / options.lux_to_lumen_factor 
    if CSV_COUNT >= 2:
      data.FILE_2 = data.FILE_2 / options.lux_to_lumen_factor
    if CSV_COUNT >= 3:
      data.FILE_3 = data.FILE_3 / options.lux_to_lumen_factor
    if CSV_COUNT >= 4:
      data.FILE_4 = data.FILE_4 / options.lux_to_lumen_factor
    if CSV_COUNT >= 5:
      data.FILE_5 = data.FILE_5 / options.lux_to_lumen_factor
    if CSV_COUNT >= 6:
      data.FILE_6 = data.FILE_6 / options.lux_to_lumen_factor

    if CSV_COUNT >= 1:
      ax.plot(data.Time, data.FILE_1, color=COLOUR_1, label=LABEL_1)
    if CSV_COUNT >= 2:
      ax.plot(data.Time, data.FILE_2, color=COLOUR_2, label=LABEL_2)
    if CSV_COUNT >= 3:
      ax.plot(data.Time, data.FILE_3, color=COLOUR_3, label=LABEL_3)
    if CSV_COUNT >= 4:
      ax.plot(data.Time, data.FILE_4, color=COLOUR_4, label=LABEL_4)
    if CSV_COUNT >= 5:
      ax.plot(data.Time, data.FILE_5, color=COLOUR_5, label=LABEL_5)
    if CSV_COUNT >= 6:
      ax.plot(data.Time, data.FILE_6, color=COLOUR_6, label=LABEL_6)
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

    # Hide borders
    ax.spines['left'].set_visible(False)
    #ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    # Hide left ticks lines
    y_ticks = ax.yaxis.get_major_ticks()
    [t.tick1line.set_visible(False) for t in y_ticks]
    #[t.tick2line.set_visible(False) for t in y_ticks]


    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]

    # legend line thickness
    handles = [copy.copy(ha) for ha in lines]
    [ha.set_linewidth(CSV_COUNT - 1) for ha in handles]

    fig.legend(handles, labels,
        ncol=4444,
        loc='upper center',
        frameon=False,
#        bbox_to_anchor=(0.5, 0.92),
        bbox_to_anchor=(0.5, 0.938),
        borderaxespad=0,
        bbox_transform=fig.transFigure,
        handlelength=0.7
    )

    #plt.tight_layout()
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig(options.graph_title.replace(' ', '-').lower()+'.png')
    print('plot saved')


def main():
    options = load_options()
    runtimeplot(options)


if __name__ == "__main__":
    main()
