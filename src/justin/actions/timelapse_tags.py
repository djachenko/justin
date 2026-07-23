from enum import StrEnum


class Tag(StrEnum):
    # ── project panel ─────────────────────────────────────────────────────────
    RootProjectItem              = "RootProjectItem"               # root of the project panel tree
    BinProjectItem               = "BinProjectItem"                # bin listing clips via <Item ObjectURef>

    # ── clip hierarchy ────────────────────────────────────────────────────────
    ClipProjectItem              = "ClipProjectItem"               # clip's entry in the project panel
    MasterClip                   = "MasterClip"                    # container grouping video+audio sides of one file
    AudioClip                    = "AudioClip"                     # audio half of a master clip
    VideoClip                    = "VideoClip"                     # video half of a master clip
    SubClip                      = "SubClip"                       # timeline slot playing a portion of a master clip

    # ── role tags ─────────────────────────────────────────────────────────────
    # Not a type: names the role a pointer plays, and resolves to either half.
    Clip                         = "Clip"                          # <Clip ObjectRef> → AudioClip or VideoClip

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
    Sequence                     = "Sequence"                      # the timeline itself
    VideoClipTrack               = "VideoClipTrack"                # video track holding frames and cover
    AudioClipTrack               = "AudioClipTrack"                # audio track holding sounds
    AudioClipTrackItem           = "AudioClipTrackItem"            # slot on the audio track referencing an audio clip
    VideoClipTrackItem           = "VideoClipTrackItem"            # slot on the video track referencing a video clip
