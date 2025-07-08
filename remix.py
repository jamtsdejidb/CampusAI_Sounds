import os
import random
import pandas as pd
from pydub import AudioSegment

# === Load your metadata (with correct comma delimiter) ===
metadata = pd.read_csv("metadata.csv", delimiter=",")
metadata.columns = metadata.columns.str.strip()  # Clean up column names
print("DEBUG: Column names are:", metadata.columns.tolist())

# === Ask for a mood ===
target_mood = input("Enter a mood (e.g., calm, energetic, busy): ").strip().lower()

# === Filter by mood ===
filtered = metadata[metadata["Mood"].str.lower() == target_mood]

if len(filtered) < 3:
    print(f"❌ Not enough files for mood '{target_mood}'. Found {len(filtered)}.")
    exit()

# === Randomly select up to 3 files ===
selected_files = random.sample(list(filtered["Filename"]), 3)

# === Generate a remix title ===
locations = filtered["Location"].unique()
types = filtered["Type"].unique()
generated_title = f"{target_mood.capitalize()} Mix: " + " + ".join(locations) + " with " + ", ".join(types)
print("🎵 Title:", generated_title)

# === Load and combine audio ===
clips = []
for file in selected_files:
    path = os.path.join("sounds", file)
    if file.endswith(".m4a"):
        clip = AudioSegment.from_file(path, format="m4a")
    else:
        clip = AudioSegment.from_file(path)
    clips.append(clip)

# === Mix with smooth transitions ===
combined = clips[0]
for clip in clips[1:]:
    combined = combined.append(clip, crossfade=1000)

# === Export ===
output_name = target_mood + "_mix.mp3"
combined.export(os.path.join("sounds", output_name), format="mp3")

print(f"✅ Mix created: sounds/{output_name}")


