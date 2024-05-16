# Get usefull data from the sound file

from .generate_nodes import *
import time

# y - amplitude
# sr - sample rate
# d - number of keys per second

def get_music_spectrogram(y, sr, d, n_bins, max_freq=0):
    if max_freq == 0:
        freq = None
    else:
        freq = max_freq
    # Returns 2D array n_bins*X.
    # where X is the amplitude per time slice.
    return librosa.feature.melspectrogram(y=y, sr=sr, hop_length=int(sr/d), n_mels=n_bins, fmax=freq)


def clean_animation(context):
    scene = context.scene
    try:
        fcurves = scene.animation_data.action.fcurves

        i = 0
        while i < len(fcurves):
            if fcurves[i].data_path.startswith("sound_nodes"):
                fcurves.remove(fcurves[i])
                i -= 1
            i += 1
    except:
        pass


import bpy

class RunAnalysis(bpy.types.Operator):
    bl_idname = "sound_nodes.run_analysis"
    bl_label = "Analyze Audio"
    bl_description = "Run analysis of audio file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #progress bar
        wm = context.window_manager
        wm.progress_begin(0, 100)
        wm.progress_update(0)

        # get fps from scene and properties
        fps = context.scene.render.fps
        properties = context.scene.sound_nodes

        # get data from audio file
        if properties.audio_source == "":
            self.report({'ERROR'}, "No audio file selected")
            return {'CANCELLED'}


        global librosa
        import librosa
        global np
        import numpy as np

        y, sr = librosa.load(properties.audio_source)

        offset = 0
        if properties.limit_frames:
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
            y = y[int(start_frame*sr/fps):int((end_frame+0.5)*sr/fps)]
            offset = start_frame

        wm.progress_update(10)
        spectrogram = get_music_spectrogram(y, sr, fps/properties.spect_smoothing, properties.spect_bins, properties.spect_max_freq)
        wm.progress_update(20)
        loudness = get_music_spectrogram(y, sr, fps/properties.loudness_smoothing, 1)
        wm.progress_update(40)

        clean_animation(context)

        # loudness
        loudness = loudness[0]
        if properties.loudness_normalization:
            loudness /= np.amax(loudness)

        for i in range(len(loudness)):
            properties.loudness = loudness[i]
            properties.keyframe_insert(data_path="loudness", frame=i*properties.loudness_smoothing+offset, group="Sound Nodes")
        wm.progress_update(80)

        # spectrogram
        if properties.spectrogram_normalization:
            spectrogram /= np.amax(spectrogram)

        n_bins = spectrogram.shape[0]

        for i in range(spectrogram.shape[1]):
            array = spectrogram[:, i]
            array = np.pad(array, (0, 64-n_bins), mode='constant', constant_values=(0, 0))

            properties.spectrogram1 = array[:32]
            properties.keyframe_insert(data_path='spectrogram1', frame=i*properties.spect_smoothing+offset, group="Sound Nodes")
            properties.spectrogram2 = array[32:]
            properties.keyframe_insert(data_path='spectrogram2', frame=i*properties.spect_smoothing+offset, group="Sound Nodes")


        wm.progress_update(90)

        # generate / refresh nodes
        generate_sound_basic_geo()
        generate_sound_basic_shader()
        generate_spectrogram(n_bins)

        wm.progress_end()

        return {'FINISHED'}
