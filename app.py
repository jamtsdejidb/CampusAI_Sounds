import os
import random
import pandas as pd
from pydub import AudioSegment
import streamlit as st
import librosa
import librosa.display
import matplotlib.pyplot as plt

# === Streamlit UI ===
st.title("🎧 Campus AI Sound Mixer")
st.write("Select a mood and remix style to auto-generate a remix:")

# ✅ Updated auto-classification logic
def extract_auto_metadata(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True, duration=10)
        print(f"[DEBUG] Loaded audio: {file_path}, y.shape={y.shape}, sr={sr}")

        if y.size == 0:
            return {"Mood": "unknown", "Type": "unknown"}

        # Extract audio features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        energy = float(librosa.feature.rms(y=y).mean())
        zero_crossing_rate = float(librosa.feature.zero_crossing_rate(y).mean())

        # Mood classification logic
        if energy < 0.01:
            mood = "quiet"
        elif tempo > 110 and energy > 0.05:
            mood = "energetic"
        elif tempo < 90 and energy < 0.04:
            mood = "calm"
        else:
            mood = "neutral"

        # Type classification logic
        filename = os.path.basename(file_path).lower()
        if "ambience" in filename or "classroom" in filename or zero_crossing_rate < 0.05:
            type_ = "ambience"
        elif energy > 0.05:
            type_ = "music"
        else:
            type_ = "ambience"

        return {"Mood": mood, "Type": type_}
    except Exception as e:
        return {"Mood": "unknown", "Type": "unknown"}

# 🔼 File uploader section
uploaded_files = st.file_uploader(
    "Upload new sounds", 
    accept_multiple_files=True, 
    type=["mp3", "wav", "m4a"]
)

# 📝 Upload + classify + update metadata
if uploaded_files:
    st.success("✅ Files uploaded! Classifying and updating metadata...")

    # Load existing metadata or create new one
    if os.path.exists("metadata.csv"):
        existing = pd.read_csv("metadata.csv", delimiter=",")
    else:
        existing = pd.DataFrame(columns=["Filename", "Location", "Time", "Mood", "Type"])

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        save_path = os.path.join(os.path.dirname(__file__), "sounds", filename)

        # Save uploaded file
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Classify metadata
        meta = extract_auto_metadata(save_path)
        new_row = {
            "Filename": filename,
            "Location": "Unknown",
            "Time": "Unknown",
            "Mood": meta["Mood"],
            "Type": meta["Type"]
        }

        # Replace existing row if filename already exists
        existing = existing[existing["Filename"] != filename]
        existing = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
        st.info(f"📁 (Re)Added: {filename} → Mood: *{meta['Mood']}*, Type: *{meta['Type']}*")

    # Save metadata
    existing.to_csv("metadata.csv", index=False)

# === Load metadata ===
metadata_path = os.path.join(os.path.dirname(__file__), "metadata.csv")
metadata = pd.read_csv(metadata_path, delimiter=",")
metadata.columns = metadata.columns.str.strip()

# Mood dropdown
moods = metadata["Mood"].str.strip().str.lower().unique().tolist()
selected_mood = st.selectbox("Choose a mood", moods)

# Remix style dropdown
mixing_style = st.selectbox("Choose mixing style", ["sequential", "overlay", "reversed", "looped", "echo"])

# Remix button
if st.button("🔁 Remix Now"):
    filtered = metadata[metadata["Mood"].str.lower().str.strip() == selected_mood]

    if len(filtered) < 3:
        st.warning(f"❌ Not enough sounds for mood '{selected_mood}'. Found {len(filtered)}.")
    else:
        selected_files = random.sample(list(filtered["Filename"]), 3)

        locations = filtered["Location"].unique()
        types = filtered["Type"].unique()
        title = f"{selected_mood.capitalize()} Mix: " + " + ".join(locations) + " with " + ", ".join(types)

        clips = []
        for file in selected_files:
            path = os.path.join(os.path.dirname(__file__), "sounds", file)
            clip = AudioSegment.from_file(path)
            clip = clip.fade_in(300).fade_out(300)
            clip = clip.apply_gain(random.uniform(-5, 2))
            clips.append(clip)

        # Apply selected mixing style
        if mixing_style == "sequential":
            combined = clips[0]
            for clip in clips[1:]:
                combined = combined.append(clip, crossfade=1000)
        elif mixing_style == "overlay":
            combined = clips[0]
            for clip in clips[1:]:
                combined = combined.overlay(clip)
        elif mixing_style == "reversed":
            combined = clips[0].reverse()
            for clip in clips[1:]:
                combined = combined.append(clip.reverse())
        elif mixing_style == "looped":
            looped = clips * 2
            combined = looped[0]
            for clip in looped[1:]:
                combined = combined.append(clip)
        elif mixing_style == "echo":
            combined = clips[0]
            for clip in clips[1:]:
                echo = clip + clip[-1000:] * 0.6
                combined = combined.append(echo)

        # Export final mix
        output_name = f"{selected_mood}_remix_{mixing_style}.mp3"
        output_path = os.path.join(os.path.dirname(__file__), "sounds", output_name)
        combined.export(output_path, format="mp3")

        # Display waveform
        st.success("✅ Mix created!")
        st.subheader("🎵 " + title)
        st.write("📊 **Waveform of the Remix:**")
        y, sr = librosa.load(output_path, sr=None)
        fig, ax = plt.subplots(figsize=(10, 3))
        librosa.display.waveshow(y, sr=sr, ax=ax, color='steelblue')
        ax.set_title("Waveform")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        st.pyplot(fig)

        # Audio player
        st.audio(output_path)

        # Log used files
        log_df = filtered[filtered["Filename"].isin(selected_files)]
        st.write("📄 **Sounds Used in This Mix:**")
        st.dataframe(log_df[["Filename", "Location", "Mood", "Type"]])

