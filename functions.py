import librosa.display
import librosa
import time
import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import itertools
import scipy as sc
import streamlit_vertical_slider as svs
import wave
import contextlib
from plotly.subplots import make_subplots
import altair as alt
from scipy import signal
#-------------------------------------------------------------------player for audio-------------------------------------------------------------------#
if 'start' not in st.session_state:
    st.session_state.start=0
if 'size1' not in st.session_state:
    st.session_state.size1=0

#-------------------------------------------------------------------audio player-------------------------------------------------------------------#

def audio_player(file,controls_column):
    controls_column.write("Original Audio")
    controls_column.audio(file, format="audio/wav", start_time=0)


def get_audio_duration(file):
    with contextlib.closing(wave.open(file.name, 'r')) as file:
        frames = file.getnframes()
        rate = file.getframerate()
        duration = frames / float(rate)
        return duration


    #-------------------------------------------------------------------reading Audio -------------------------------------------------------------------#


def sound_loading(file,speed_rate):
    loaded_sound_file, sampling_rate = librosa.load(file, sr=None)
    # speed_rate=st.slider(label="speed Rate",min_value= 0.1 , max_value=2.0 ,value=1.0)
    loaded_sound_file = librosa.effects.time_stretch(loaded_sound_file, rate=speed_rate)
    return loaded_sound_file, sampling_rate

    #-------------------------------------------------------------------processing-------------------------------------------------------------------#
fig = make_subplots(
    rows=2, cols=1,shared_xaxes=True,
    subplot_titles=("Original Audio","Modified Audio"))
    


def fourier_transform(loaded_sound_file, sampling_rate):

    fft_file = sc.fft.rfft(loaded_sound_file)
    amplitude = np.abs(fft_file)
    phase = np.angle(fft_file)
    frequency = sc.fft.rfftfreq(len(loaded_sound_file), 1/sampling_rate)
    return amplitude, phase, frequency

#-------------------------------------------------------------------bins_seperation-------------------------------------------------------------------#


def bins_separation(frequency, amplitude):
    frequency_axis_list = []
    amplitude_axis_list = []
    bin_max_frequency_value = int(len(frequency)/10)
    i = 0
    while(i < 10):
        frequency_axis_list.append(
            frequency[i*bin_max_frequency_value: (i+1)*bin_max_frequency_value])
        amplitude_axis_list.append(
            amplitude[i*bin_max_frequency_value:(i+1)*bin_max_frequency_value])
        i = i+1
    return frequency_axis_list, amplitude_axis_list, bin_max_frequency_value

#-------------------------------------------------------------sliders-generation-------------------------------------------------------------------#

def sliders_generation(max_freq_list,main_column,number_of_sliders):
    columns = main_column.columns(number_of_sliders)
    sliders_data = []
    for i in range(0, number_of_sliders):
            with columns[i]:
                value = svs.vertical_slider(key=i, default_value=1, step=1, min_value=0, max_value=20, slider_color= '#3182ce',thumb_color = 'black')
                if value == None:
                    value = 1
                sliders_data.append(value)
                if (number_of_sliders==10):
                    label=int(((i+1)*max_freq_list)+1)
                    st.write(f"{label}Hz")
                elif(number_of_sliders==3):
                    instruments=["Drum","Guitar","Flute"]
                    st.write(instruments[i])
                else:
                    vowels=[" ' SH ' sound","  ' O ' sound","  ' A ' sound","  ' R ' sound","  ' B ' sound"]
                    st.write(vowels[i])
    return sliders_data


def data_preparation(loaded_sound_file,modified_amplitude_axis_list,original_time_axis,ifft_file):
    loaded_sound_file = loaded_sound_file[:len(ifft_file)]
    modified_amplitude_axis_list = modified_amplitude_axis_list[:len(ifft_file)]
    original_time_axis = original_time_axis[:len(ifft_file)]
    resulting_df = pd.DataFrame({'time': original_time_axis[::500], 'amplitude': loaded_sound_file[:: 500], 'modified_amplitude': ifft_file[::500]}, columns=['time', 'amplitude', 'modified_amplitude'])
    return resulting_df , loaded_sound_file

def altair_plot(df):
    num_of_cols = len(df.axes[1])
    if(num_of_cols) ==3: 
        lines = alt.Chart(df).mark_line(color='#3182ce').encode(
                x=alt.X('time', axis=alt.Axis(title='Time'))
            ).properties(
                width=500,
                height=300
            ).interactive()
        figure = lines.encode(y=alt.Y('amplitude',axis=alt.Axis(title='Amplitude'))) | lines.encode(
            y =alt.Y('modified_amplitude', axis=alt.Axis(title='Modified Amplitude')))
    else:
        lines = alt.Chart(df).mark_line(color='#3182ce').encode(
                x=alt.X('time', axis=alt.Axis(title='Time'),scale=alt.Scale(domain=(45, 51)) )
            ).properties(
                width=1200,
                height=700
            ).interactive()
        figure = lines.encode(y=alt.Y('amplitude',axis=alt.Axis(title='Amplitude')))
    return figure


def plot_animation(df):
        num_of_cols = len(df.axes[1])
        if(num_of_cols) ==3:
            chart1 = alt.Chart(df).mark_line(color="#3182ce").encode(
            x=alt.X('time', axis=alt.Axis(title='Time')),
            # y=alt.Y('amplitude', axis=alt.Axis(title='Amplitude')),
        ).properties(
            width=500,
            height=300
        ).interactive()
            figure = chart1.encode(y=alt.Y('amplitude',axis=alt.Axis(title='Amplitude'))) | chart1.encode( y =alt.Y('modified_amplitude', axis=alt.Axis(title='Modified Amplitude')))
        else:
            chart1 = alt.Chart(df).mark_line(color="#3182ce").encode(
            x=alt.X('time', axis=alt.Axis(title='Time'))
            # y=alt.Y('amplitude', axis=alt.Axis(title='Amplitude')),
        ).properties(
            width=1000,
            height=500
        ).interactive()
            
            figure = chart1.encode(y=alt.Y('amplitude',axis=alt.Axis(title='Amplitude')))
        return figure


def dynamic_plot(line_plot,df,controls_column):
    col1, col2, col3 = controls_column.columns([0.5,0.5,0.5])
    with col1:
        start_btn = st.button('Start',key='start_btn')
    with col2:
        pause_btn = st.button('Pause',key='pause')
    with col3:
        resume_btn = st.button('Resume',key='resume')
    N = df.shape[0] 
    num_of_cols = len(df.axes[1])
    rows_until_45sec = df.loc[df['time'] <= float(47)]
    rows_until_51sec = df.loc[df['time'] <= float(51)]
    if(num_of_cols) ==2:
        df=df.loc[len(rows_until_45sec):len(rows_until_51sec)]

    burst = 150 
    size = burst 
    if start_btn:
        controls_column.write("first start")
        for i in range(1, N-burst):
                    st.session_state.start=i  
                    step_df = df.iloc[i:burst+i]
                    lines = plot_animation(step_df)
                    line_plot.altair_chart(lines)
                    size = i + burst
                    st.session_state.size1 = size
        line_plot = line_plot.altair_chart(lines)
    elif resume_btn: 
            print(st.session_state.start)
            for i in range( st.session_state.start,N):
                st.session_state.start =i 
                step_df = df.iloc[0:size]
                lines = plot_animation(step_df)
                line_plot = line_plot.altair_chart(lines)
                st.session_state.size1 = size
                size = i + burst
                time.sleep(.0000001)
                
    elif pause_btn:
            step_df = df.iloc[0:st.session_state.size1]
            lines = plot_animation(step_df)
            line_plot = line_plot.altair_chart(lines)
            
            

def sound_modification(sliders_data, amplitude_axis_list,controls_column):
    controls_column.write('Modified Audio')
    empty = controls_column.empty()
    empty.empty()
    modified_bins = []
    for i in range(0, 10):
        modified_bins.append((sliders_data[i])  *amplitude_axis_list[i])
    modified_amplitude_axis_list = list(itertools.chain.from_iterable(modified_bins))
    return modified_amplitude_axis_list, empty


def inverse_fourier(modified_amplitude_axis_list, phase):
    mod = np.multiply(modified_amplitude_axis_list, np.exp(1j*phase))
    ifft_file = sc.fft.irfft(mod)
    return ifft_file

def triangle(length_wave):
    window = signal.windows.blackman(length_wave)
    return window

def plot_spectrogram(original_audio, modified_audio,main_column):
    original_spectro, modified_spectro= main_column.columns(2)

    D1     = librosa.stft(original_audio)             # STFT of y
    S_db1  = librosa.amplitude_to_db(np.abs(D1))
    D2     = librosa.stft(modified_audio) #             # STFT of y
    S_db2  = librosa.amplitude_to_db(np.abs(D2))
    font = {'size': 7}

    plt.rc('font', **font)
    fig= plt.figure(figsize=[12,7])

    with original_spectro:
        plt.subplot(2,2,1)
        img1 = librosa.display.specshow(S_db1, x_axis='time', y_axis='linear')
        fig.colorbar(img1, format="%+2.f dB")
    with modified_spectro:
        plt.subplot(2,2,2)
        img2 = librosa.display.specshow(S_db2, x_axis='time', y_axis='linear')
        fig.colorbar(img2, format="%+2.f dB")

    fig.tight_layout(pad=1)
    main_column.pyplot(fig)