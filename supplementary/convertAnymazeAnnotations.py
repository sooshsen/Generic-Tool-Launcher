'''
author: sushmitas

Script to prepare annnotations to be used in simBA analysis (ANYMAZE -> BORIS)

Columns in import file from Anymaze: 
[Time, behav1_active, behav1_inactive, behav2_active, ...]

NOTE: Every video has slightly different FPS!!! (14.986 - 15.002)

ANY-maze CSV → SimBA-compatible BORIS CSV, 
including the exact columns (Observation id, Media file path, Time, Behavior, Event, etc.)


This script can be run both within DEEPLABCUT and simBA conda environments (in command prompt)
>> cd E:/sushmita/Generic-Tool-Launcher/supplementary
>> python convertAnymazeAnnotations.py -v path/to/videofile.mp4 -b path/to/anymaze-annotations.csv

'''

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
np.set_printoptions(suppress=True)

import os
import sys
from pathlib import Path
import cv2
from datetime import datetime, timedelta
import csv
from difflib import get_close_matches, SequenceMatcher

import argparse




''' --------------------------------------------------------------------------------------------------------
 ************ FUNCTIONS USED ************
    --------------------------------------------------------------------------------------------------------
''' 
def valid_video_file(filename):
	filepath = Path(filename)

	# check if exists
	if not filepath.is_file():
		raise argparse.ArgumentTypeError(f"File not found: {filename}")

	# check if MP4 file
	if filepath.suffix.lower() != '.mp4':
		raise argparse.ArgumentTypeError("Input file must be a MP4 format (.mp4)")

	return filepath


def valid_behavior_file(filename):
	filepath = Path(filename)

	# check if exists
	if not filepath.is_file():
		raise argparse.ArgumentTypeError(f"File not found: {filename}")

	# check if EXCEL file
	if filepath.suffix.lower() not in {'.csv', '.xls', '.xlsx'}:
		raise argparse.ArgumentTypeError("Input file must be a CSV or Excel file (.csv, .xls, .xlsx)")

	return filepath

def valid_output_path(outpath):
	
	# check if exists, if not create one
	output_path = Path(outpath)
	output_path.mkdir(parents=True, exist_ok=True)

	return output_path




def verify_fps(video):
	# function to check the frame rate of input video (.mp4)
	cap = cv2.VideoCapture(video)
	fps = cap.get(cv2.CAP_PROP_FPS)
	n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
	print("FPS:", fps)
	print("Number of frames:", n_frames)
	print("Duration:", n_frames / fps)
	cap.release()
	return fps, n_frames/fps



def time_in_secs(timestamp):
	# each timestamp in column 'Time' should be in seconds
	t_secs = [0]*len(timestamp)
	for ii in range(len(timestamp)):
		# update timestamp format  
		t = datetime.strptime(timestamp[ii], '%H:%M:%S.%f')
		delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
		t_secs[ii] = delta.total_seconds()
	print('Time format corrected...')
	return t_secs


def normalize(text):
	return " ".join(text.lower().strip().split())


def find_behavior(requested, available, cutoff=0.75):
	# identify behaviors actually present in the ANYMAZE data based on closely matched column names
	# NOTE: Essential to deal with occasional typos in behavior names
	available_normalized = {
		normalize(name): name
		for name in available
		}

	available_names = list(available_normalized.keys())

	found = {}

	for key, target in requested.items():
		matches = get_close_matches(
			normalize(target),
			available_names,
			n = 1,
			cutoff = cutoff,
		)

		if matches:
			found[key] = available_normalized[matches[0]]
		else:
			found[key] = None

	return found





''' --------------------------------------------------------------------------------------------------------
 STEP 1: Read video and ANYMAZE annotations
    --------------------------------------------------------------------------------------------------------
''' 
parser = argparse.ArgumentParser(
	description='Transform ANYMAZE-annotated behavior into BORIS annotation format.',
	epilog='NOTE: SimBA cannot import ANYMAZE annotations directly.')

parser.add_argument('-v','--video', type=valid_video_file, help='Path to raw video (.mp4)')
parser.add_argument('-b','--behavior', type=valid_behavior_file, help='Path to ANYMAZE annotations corresponding to the video (.csv/.xls/.xlsx)')
parser.add_argument('-o','--output_dir', type=valid_output_path, help='Path to save updated ANYMAZE annotations corresponding to the videos (.csv)')

# print out help if no arguments provided
if len(sys.argv) == 1:
	parser.print_help()
	sys.exit(0)

args = parser.parse_args()


# Load behavior annotations
if args.behavior.suffix.lower() == ".csv":
    annots_am = pd.read_csv(args.behavior)
else:
    annots_am = pd.read_excel(args.behavior)


# Load video file
ref_video =  args.video


# MANUAL TESTING (sample)
# behavior = Path(r"E:\sushmita\vids_from_lab\timestamps_sara\retrieval_original_context_males_control\batch1_original_context_male_test1.csv")
# annots_am = pd.read_csv(behavior)
# ref_video = Path(r"E:\sushmita\TESTING_SIMBA_2_VIDS\vids\batch1_Test 25.mp4")

output_path = args.output_dir


''' --------------------------------------------------------------------------------------------------------
 STEP 2: Extract details from video file
    --------------------------------------------------------------------------------------------------------
''' 
vid_fps, vid_duration = verify_fps(ref_video)





''' --------------------------------------------------------------------------------------------------------
 STEP 3: Modify ANYMAZE annotations in desired BORIS annotation format
 For reference, check https://github.com/sgoldenlab/simba/blob/master/misc/boris_new_example.csv
    --------------------------------------------------------------------------------------------------------
''' 
cols = annots_am.columns.tolist()

if annots_am.columns[0] == "Time (s)":
	annots_am.sort_values("Time (s)", inplace=True)
	annots_am.rename(columns={"Time (s)": "time(s)"}, inplace=True)
else:
	colname = annots_am.columns[0]
	annots_am.sort_values(colname, inplace=True)
	annots_am.rename(columns={colname : "time(s)"}, inplace=True)


# time format modification from HH:MM:SS to seconds (if necessary)
if not pd.api.types.is_numeric_dtype(annots_am["time(s)"]):
	annots_am["time(s)"] = time_in_secs(annots_am["time(s)"])

# behaviors of interest (to make SimBA classifiers)
search_behaviors = {
    "Freezing": "Freezing",
    "RiskAssessment": "Risk assesment active",
    "Grooming": "grooming active",
    "Rearing": "raring active",
    "Sniffing": "sniffing active"
}


# beahviors actually present in ANYMAZE file
available_behaviors = cols

# behaviors to use from ANYMAZE and actually made into SimBA classifiers
found_behaviors = find_behavior(
		search_behaviors,
		available_behaviors,
		cutoff = 0.9,
	)


# create START/STOP EVENTS for each behavior
events = []

for behavior, column in found_behaviors.items():

	# missing behaviors
	if column == None:
		continue

	state = pd.to_numeric(
		annots_am[column], 
		errors="coerce"
		).fillna(0)   # Make sure the column is numeric

	# Detect changes in state
	previous = state.shift(1, fill_value=0)

	# 0 -> 1 = START
	starts = annots_am[(previous == 0) & (state == 1)]

	# 1 -> 0 = STOP
	stops = annots_am[(previous == 1) & (state == 0)]

	# Add START and STOP events
	for _, row in starts.iterrows():
		events.append({
			"Time": row["time(s)"],
			"Behavior": behavior,
			"Status": "START"
		})

	for _, row in stops.iterrows():
		events.append({
			"Time": row["time(s)"],
			"Behavior": behavior,
			"Status": "STOP"
		})

	#### Handling behavior at the start
	if state.iloc[-1] == 1:
		last_time = annots_am["time(s)"].iloc[-1]

		events.append({
			"Time": last_time,
			"Behavior": behavior,
			"Status": "STOP"
		})


# output df
events_df = pd.DataFrame(events)

# Sort chronologically
events_df = events_df.sort_values(["Time", "Behavior", "Status"]).reset_index(drop=True)
events_df.rename(columns={'Status': 'Behavior type'}, inplace=True)

# add required columns (set relevant values if available)
events_df['Observation id'] = 'test'
events_df['Observation date'] = ''
events_df['Observation duration'] = ''
events_df['Observation type'] = ''
events_df['Description'] = 'Media file(s)'
events_df['Source'] = 'player #1:' + str(ref_video)
events_df['Image index'] = 'NA'
events_df['Image file path'] = 'NA'
events_df['Media file name'] = ref_video
events_df['Media duration (s)'] = vid_duration
events_df['FPS'] = vid_fps
events_df['Subject'] = ''
events_df['Behavioral category'] = ''
events_df['Comment'] = ''
#events_df['FrameNum_AM'] = np.round(events_df["Time (s)"]  * vid_fps)

# Set exact column order
events_df = events_df[
    [
        "Observation id",
        "Observation date",
        "Description",
        "Observation duration",
        "Observation type",
        "Source",
        "Time",
        "Media file name",
        "Media duration (s)",
        "FPS",
        "Subject",
        "Behavior",
        "Behavioral category",
        "Comment",
        "Behavior type",
        "Image index",
        "Image file path",
    ]
]

to_save = True
if to_save:
	filename = Path(os.path.basename(ref_video))
	output_file = output_path /f"{filename.stem}.csv"
	events_df.to_csv(output_file, index=True)
	print('---------------------- File saved -------------------')
else:
	print('---------------------- File not saved -----------------------')

