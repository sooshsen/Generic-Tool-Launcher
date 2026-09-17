'''
author: sushmitas

Script to prepare annnotations to be used in simBA analysis (ANYMAZE -> BORIS)

Columns in import file from Anymaze: 
[Time, behav1_active, behav1_inactive, behav2_active, ...]

NOTE: Every video has slightly different FPS!!! (14.986 - 15.002)

ANY-maze CSV → SimBA-compatible BORIS CSV, 
including the exact columns (Observation id, Media file path, Time, Behavior, Event, etc.)

Batch version:
    - Reads multiple videos from a directory
    - Reads multiple ANY-maze annotation files from a directory
    - Matches videos and annotation files based on filename
    - Converts each pair into a SimBA-compatible BORIS CSV
    - Saves one output CSV per video

Expected matching:

    videos/
        mouse01.mp4
        mouse02.mp4
        mouse03.mp4

    annotations/
        mouse01.csv
        mouse02.csv
        mouse03.csv

    output/
        mouse01.csv
        mouse02.csv
        mouse03.csv



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
'''
def valid_input_path(dirname):
	''' check if video and behavior annotation directory exists '''
	filepath = Path(dirname)

	if not filepath.is_dir():
		raise argparse.ArgumentTypeError(f"Directory not found: {dirname}")

	return filepath


def valid_output_path(outpath):
	
	# check if exists, if not create one
	output_path = Path(outpath)
	output_path.mkdir(parents=True, exist_ok=True)

	return output_path



def verify_fps(video):
	# function to check the frame rate of input video (.mp4)
	cap = cv2.VideoCapture(str(video))
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


def find_am_annots(video, annotation_dir):
	''' find the ANYmaze annotation file corresponding to a video file (both have same names)'''
	video_stem = video.stem.lower()
	possible_extensions = ['.csv','.xls','.xlsx']

	for ext in possible_extensions:
		candidate = annotation_dir/(video_stem + ext)
		if candidate.is_file():
			return candidate

	# case sensitivity
	for file in annotation_dir.iterdir():
		if not file.is_file():
			continue
		if file.suffix.lower() not in possible_extensions:
			continue
		if file.stem.lower() == video_stem:
			return file

	return None


def load_annots(annotation_file):
	''' load .csv/.xls/.xlsx files '''

	suffix = annotation_file.suffix.lower()

	if suffix == '.csv':
		return pd.read_csv(annotation_file)

	elif suffix in ['.xls','.xlsx']:
		return pd.read_excel(annotation_file)

	else:
		raise ValueError(f"Unsupported annotation format: {annotation_file}")





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



def convert_am_annots(ref_video, annotation_file, output_path):
	''' convert a ANYmaze annotation file + video to BORIS compatible CSV '''
	print("Converting...")
	print("=" * 80)

	#### STEP 1: EXTRACT VIDEO DETAILS
	vid_fps, vid_duration = verify_fps(ref_video)


	#### STEP 2: LOAD AND PROCESS ANNOTATIONS
	annots_am = load_annots(annotation_file)

	if annots_am.empty:
		print("WARNING: Annotation file is empty. Skipping.")
		return False

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


	#### STEP 3: BEHAVIORS OF INTEREST (to make SimBA classifiers) - add/remove as needed
	search_behaviors = {
	"Freezing": "Freezing",
	"RiskAssessment": "Risk assesment active",
	"Grooming": "grooming active",
	"Rearing": "raring active",
	"Sniffing": "sniffing active"
	}

	#### STEP 4: FIND ACTUAL BEHAVIOR COLUMNS IN ANNOTATION FILE
	available_behaviors = cols

	# behaviors to use from ANYMAZE and actually made into SimBA classifiers
	found_behaviors = find_behavior(
		search_behaviors,
		available_behaviors,
		cutoff = 0.9,
		)
	print("\nBehavior matching:")

	for behavior, column in found_behaviors.items():
		if column is not None:
			print(f"  {behavior:20s} -> {column}")
		else:
			print(f"  {behavior:20s} -> NOT FOUND")


	#### STEP 5: CREATE START/STOP EVENTS
	events = []

	for behavior, column in found_behaviors.items():

		# missing behaviors
		if column == None: continue

		state = pd.to_numeric(annots_am[column], errors="coerce").fillna(0)   # Make sure the column is numeric

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

		# Handling behavior that is still active at the end of annotation file
		if state.iloc[-1] == 1:
			last_time = annots_am["time(s)"].iloc[-1]

			events.append({
				"Time": last_time,
				"Behavior": behavior,
				"Status": "STOP"
			})

	#### STEP 6: CREATE OUTPUT FILE

	events_df = pd.DataFrame(events)

	# if no behaviors found
	if events_df.empty:
		print("WARNING: No behavior events found. No files create!")

	else:
		# Sort chronologically
		events_df = events_df.sort_values(["Time", "Behavior", "Status"]).reset_index(drop=True)
		events_df.rename(columns={'Status': 'Behavior type'}, inplace=True)

	#### STEP 7: ADD BORIS RELEVANT COLUMNS
	events_df['Observation id'] = 'test'
	events_df['Observation date'] = ''
	events_df['Observation duration'] = ''
	events_df['Observation type'] = 'Media file(s)'
	events_df['Description'] = ''
	events_df['Source'] = 'player #1:' + str(ref_video)
	events_df['Image index'] = 'NA'
	events_df['Image file path'] = 'NA'
	events_df['Media file name'] = str(ref_video)
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

	#### STEP 8: SAVE FILE

	to_save = True
	if to_save:
		output_file = output_path /f"{ref_video.stem}.csv"
		events_df.to_csv(output_file, index=False)

		print('---------------------- File saved -------------------')

	else:
		print('---------------------- File not saved -----------------------')

	return True





''' --------------------------------------------------------------------------------------------------------
 ARGUMENT PARSER
    --------------------------------------------------------------------------------------------------------
''' 
parser = argparse.ArgumentParser(
	description='Batch transform ANYMAZE-annotated behavior into BORIS annotation format.',
	epilog='ANY-maze CSV/Excel files are matched to videos using their filenames. ')

parser.add_argument('-v','--video_dir', type=valid_input_path, help='Path to raw MP4 videos')
parser.add_argument('-b','--behavior_dir', type=valid_input_path, help='Path to ANYMAZE annotations corresponding to the video (.csv/.xls/.xlsx)')
parser.add_argument('-o','--output_dir', type=valid_output_path, help='Path to save updated ANYMAZE annotations corresponding to the videos (.csv)')


'''---------
MAIN BODY
   ---------
'''

# print out help if no arguments provided
if len(sys.argv) == 1:
	parser.print_help()
	sys.exit(0)

args = parser.parse_args()


video_dir = args.video_dir
behavior_dir = args.behavior_dir
output_path = args.output_dir



# MANUAL TESTING (sample)
# behavior = Path(r"E:\sushmita\vids_from_lab\timestamps_sara\retrieval_original_context_males_control\batch1_original_context_male_test1.csv")
# annots_am = pd.read_csv(behavior)
# ref_video = Path(r"E:\sushmita\TESTING_SIMBA_2_VIDS\vids\batch1_Test 25.mp4")



''' --------------------------------------------------------------------------------------------------------
 FIND VIDEOS
    --------------------------------------------------------------------------------------------------------
''' 

videos = sorted([
	f for f in video_dir.iterdir()
	if f.is_file() and f.suffix.lower() == '.mp4'
	])

print("\n")
print("=" * 80)
print("ANY-MAZE -> BORIS BATCH CONVERSION")
print("=" * 80)

print(f"\nVideo directory:")
print(video_dir)

print(f"\nAnnotation directory:")
print(behavior_dir)

print(f"\nOutput directory:")
print(output_path)

print(f"\nNumber of videos found: {len(videos)}")


if len(videos) == 0:

	print("\nNo MP4 videos found.")
	sys.exit(0)




''' --------------------------------------------------------------------------------------------------------
 PROCESS VIDEOS (one by one)
    --------------------------------------------------------------------------------------------------------
'''

processed = 0
skipped = 0

for video in videos:
	# find matchin annotation file
	annotation_file = find_am_annots(video, behavior_dir)

	if annotation_file is None:
		print("\n")
		print("!" * 80)
		print(f"WARNING: No annotation file found for {video.name}")
		print(f"Expected something like: {video.stem}.csv")
		print("Skipping this video.")
		print("!" * 80)

		skipped += 1
		continue

	try:
		success = convert_am_annots(video, annotation_file, output_path)

		if success:
			processed += 1
		else:
			skipped += 1
	
	except Exception as e:
		print("/n")
		print("!" * 80)
		print(f"ERROR while processing {video.name}")
		print(f"Annotation: {annotation_file.name}")
		print(f"Error: {e}")
		print("Skipping this file and continuing...")
		print("!" * 80)

		skipped += 1





''' --------------------------------------------------------------------------------------------------------
 SUMMARY
    --------------------------------------------------------------------------------------------------------
'''

print("\n")
print("=" * 80)
print("BATCH PROCESSING COMPLETE")
print("=" * 80)

print(f"Videos found:       {len(videos)}")
print(f"Successfully saved: {processed}")
print(f"Skipped/errors:     {skipped}")
print(f"\nOutput directory:")
print(output_path)

print("=" * 80)




