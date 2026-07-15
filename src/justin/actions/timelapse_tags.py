from enum import StrEnum


class Tag(StrEnum):
    # ── clip hierarchy ────────────────────────────────────────────────────────
    ClipProjectItem              = "ClipProjectItem"               # clip's entry in the project panel
    MasterClip                   = "MasterClip"                    # container grouping video+audio sides of one file
    AudioClip                    = "AudioClip"                     # audio half of a master clip
    VideoClip                    = "VideoClip"                     # video half of a master clip
    SubClip                      = "SubClip"                       # timeline slot playing a portion of a master clip

    # ── media / streams ───────────────────────────────────────────────────────
    Media                        = "Media"                         # file reference — path, streams, codec info
    AudioStream                  = "AudioStream"                   # audio stream within the media file
    VideoStream                  = "VideoStream"                   # video stream within the media file
    AudioMediaSource             = "AudioMediaSource"              # raw audio data source for an audio stream
    VideoMediaSource             = "VideoMediaSource"              # raw video data source for a video stream

    # ── clip metadata ─────────────────────────────────────────────────────────
    Markers                      = "Markers"                       # in/out markers attached to a clip
    ClipLoggingInfo              = "ClipLoggingInfo"               # logging metadata (scene, shot, description)
    SecondaryContent             = "SecondaryContent"              # supplementary clip data (waveform cache path, etc.)

    # ── audio processing ──────────────────────────────────────────────────────
    AudioComponentChain          = "AudioComponentChain"           # chain of audio effects on a clip
    ClipChannelSerializer        = "ClipChannelSerializer"         # per-channel clip data serializer
    ClipChannelGroupVectorSerializer = "ClipChannelGroupVectorSerializer"  # group of per-channel serializers
    ClipChannelVectorSerializer  = "ClipChannelVectorSerializer"   # list of per-channel serializers

    # ── timeline ──────────────────────────────────────────────────────────────
    AudioClipTrackItem           = "AudioClipTrackItem"            # slot on the audio track referencing an audio clip
