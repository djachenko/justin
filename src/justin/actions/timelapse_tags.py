from enum import StrEnum


class Tag(StrEnum):
    # ── project panel ─────────────────────────────────────────────────────────
    Project                      = "Project"                       # graph root: the only top-level chunk without an id

    # ── clip hierarchy ────────────────────────────────────────────────────────
    ClipProjectItem              = "ClipProjectItem"               # clip's entry in the project panel
    MasterClip                   = "MasterClip"                    # project material (a file or a sequence) grouping its video+audio sides
    AudioClip                    = "AudioClip"                     # audio half of a master clip
    VideoClip                    = "VideoClip"                     # video half of a master clip
    SubClip                      = "SubClip"                       # which master clip a slot plays, under what name; the range is in its clip

    # ── role tags ─────────────────────────────────────────────────────────────
    # Not a type: names the role a pointer plays, and resolves to either half.
    Clip                         = "Clip"                          # <Clip ObjectRef> → AudioClip or VideoClip

    # ── media / streams ───────────────────────────────────────────────────────
    Media                        = "Media"                         # file reference — path, streams, codec info
    AudioStream                  = "AudioStream"                   # audio stream within the media file
    VideoStream                  = "VideoStream"                   # video stream within the media file
    AudioMediaSource             = "AudioMediaSource"              # audio side of a media file: clips → it → Media
    VideoMediaSource             = "VideoMediaSource"              # video side of a media file: clips → it → Media

    # ── clip metadata ─────────────────────────────────────────────────────────
    Markers                      = "Markers"                       # in/out markers; one block can be shared by several clips
    ClipLoggingInfo              = "ClipLoggingInfo"               # logging metadata (scene, shot, description)
    SecondaryContent             = "SecondaryContent"              # supplementary clip data (waveform cache path, etc.)

    # ── audio processing ──────────────────────────────────────────────────────
    AudioComponentChain          = "AudioComponentChain"           # chain of audio effects on a clip
    ClipChannelSerializer        = "ClipChannelSerializer"         # per-channel clip data serializer
    ClipChannelGroupVectorSerializer = "ClipChannelGroupVectorSerializer"  # group of per-channel serializers
    ClipChannelVectorSerializer  = "ClipChannelVectorSerializer"   # list of per-channel serializers

    # ── timeline ──────────────────────────────────────────────────────────────
    AudioClipTrackItem           = "AudioClipTrackItem"            # slot on the audio track: position, effects, <SubClip> pointer
