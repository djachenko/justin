import gzip
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

PREMIERE_TIMEBASE = 254_016_000_000

# Wolfday template constants (step_12: frames + cover + 1 sound at 10fps, 106 frames)
_WD_TIMELAPSE_DIR = "/Users/justin/photos/stages/stage1.filter/26.04.17.wolfday/timelapse"
_WD_FIRST_FRAME   = "26.04.17.wolfday_0001.jpg"
_WD_SOUND_NAME    = "snejnye_volki.mp4"
_WD_PHOTOSET      = "26.04.17.wolfday"
_WD_FPS_TICKS     = 25401600000    # TIMEBASE / 10
_WD_N_FRAMES      = 106
_WD_FRAMES_DUR    = _WD_N_FRAMES * _WD_FPS_TICKS          # 2692569600000
_WD_SEQ_DUR       = (_WD_N_FRAMES + 1) * _WD_FPS_TICKS    # 2717971200000 (with cover)

_TEMPLATE_PATH = (
    Path(__file__).parent.parent
    / "resources"
    / "timelapse_templates"
    / "step_12_sound_in_timeline.prproj"
)

_AUDIO_EXTS = {".mp3", ".mp4", ".wav", ".aac", ".m4a", ".flac", ".ogg"}
_AUDIO_ONLY_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".aiff"}


@dataclass
class TimelapseSettings:
    name: str
    timelapse_dir: Path
    cover: Path | None
    sounds: list[Path]
    fps: float = 10.0


def from_timelapse_dir(timelapse_dir: Path, fps: float = 10.0) -> TimelapseSettings:
    timelapse_dir = timelapse_dir.resolve()
    frames_dir = timelapse_dir / "frames"

    if not frames_dir.exists() or not any(frames_dir.glob("*.jpg")):
        raise ValueError(f"No frames in {frames_dir}")

    cover_path = timelapse_dir / "cover.jpg"
    sound_dir = timelapse_dir / "sound"

    return TimelapseSettings(
        name=timelapse_dir.parent.name,
        timelapse_dir=timelapse_dir,
        cover=cover_path if cover_path.exists() else None,
        sounds=sorted(
            f for f in sound_dir.iterdir()
            if f.is_file() and f.suffix.lower() in _AUDIO_EXTS
        ) if sound_dir.exists() else [],
        fps=fps,
    )


def _count_frames(frames_dir: Path) -> int:
    return len(list(frames_dir.glob("*.jpg")) + list(frames_dir.glob("*.jpeg")))


def _first_frame(frames_dir: Path) -> str:
    frames = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.jpeg"))
    if not frames:
        raise ValueError(f"No JPG files in {frames_dir}")
    return frames[0].name


def parse_toplevel_blocks(xml: str) -> list[tuple[int, int, str, str]]:
    result = []
    for m in re.finditer(r'(?m)^\t<(\w+)([ >])', xml):
        tag = m.group(1)
        start = m.start()
        line_end = xml.index('\n', start)
        first_line = xml[start:line_end]
        if first_line.rstrip().endswith('/>'):
            result.append((start, line_end + 1, tag, xml[start:line_end + 1]))
            continue
        close = f'\n\t</{tag}>'
        close_pos = xml.find(close, start)
        if close_pos == -1:
            continue
        end = close_pos + len(close) + 1
        result.append((start, end, tag, xml[start:end]))
    return result


def _remove_blocks_by_positions(xml: str, positions: list[tuple[int, int]]) -> str:
    for start, end in sorted(positions, reverse=True):
        xml = xml[:start] + xml[end:]
    return xml


def _blocks_containing(blocks: list, text: str) -> list:
    return [b for b in blocks if text in b[3]]


def remove_dangling_refs(xml: str) -> str:
    """
    Remove blocks with dangling UUID/ID references. Iterates until stable.

    Handles cascading removal:
    - ObjectURef (UUID): Media, VideoClip, AudioClip, MasterClip
    - ObjectRef (numeric ID): SubClip
    Also cleans up TrackItems and BinProjectItem Items entries.
    """
    for _ in range(10):
        uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
        ids = set(re.findall(r'ObjectID="(\d+)"', xml))

        def clean_bin_items(m: re.Match) -> str:
            def keep(item_m: re.Match) -> str:
                uref = re.search(r'ObjectURef="([^"]+)"', item_m.group(0))
                return '' if uref and uref.group(1) not in uids else item_m.group(0)
            return re.sub(r'[^\S\n]*<Item[^/]*/>\n', keep, m.group(0))

        xml = re.sub(r'<Items Version="\d+">.*?</Items>', clean_bin_items, xml, flags=re.DOTALL)

        def clean_track_items(m: re.Match) -> str:
            def keep(item_m: re.Match) -> str:
                ref = re.search(r'ObjectRef="(\d+)"', item_m.group(0))
                return '' if ref and ref.group(1) not in ids else item_m.group(0)
            block = re.sub(r'[^\S\n]*<TrackItem[^/]*/>\n', keep, m.group(0))
            # Re-index remaining items
            remaining = list(re.finditer(r'<TrackItem Index="\d+" ObjectRef="(\d+)"/>', block))
            for new_idx, item_m in enumerate(remaining):
                old = item_m.group(0)
                new = f'<TrackItem Index="{new_idx}" ObjectRef="{item_m.group(1)}"/>'
                block = block.replace(old, new, 1)
            return block

        xml = re.sub(r'<TrackItems Version="\d+">.*?</TrackItems>', clean_track_items, xml, flags=re.DOTALL)

        uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
        ids = set(re.findall(r'ObjectID="(\d+)"', xml))
        blocks = parse_toplevel_blocks(xml)
        to_delete: list[tuple[int, int]] = []
        for s, e, _tag, text in blocks:
            uuid_urefs = re.findall(r'<(?:Media|VideoClip|AudioClip|MasterClip) ObjectURef="([^"]+)"', text)
            if any(uref not in uids for uref in uuid_urefs):
                to_delete.append((s, e))
                continue
            sub_refs = re.findall(r'<SubClip ObjectRef="(\d+)"', text)
            if any(ref not in ids for ref in sub_refs):
                to_delete.append((s, e))

        if not to_delete:
            break
        xml = _remove_blocks_by_positions(xml, to_delete)

    return xml


def _clone_sound_blocks(blocks: list[tuple], old_name: str, new_name: str, id_offset: int) -> str:
    combined = ''.join(b[3] for b in blocks)
    num_ids = sorted(set(re.findall(r'ObjectID="(\d+)"', combined)), key=int)
    id_map = {oid: str(int(oid) + id_offset) for oid in num_ids}
    uid_pat = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uid_map = {u: str(uuid.uuid4()) for u in set(re.findall(uid_pat, combined))}
    result = combined.replace(old_name, new_name)
    for old_id, new_id in id_map.items():
        result = re.sub(rf'((?:ObjectID|ObjectRef)="){re.escape(old_id)}"', rf'\g<1>{new_id}"', result)
    for old_uid, new_uid in uid_map.items():
        result = result.replace(old_uid, new_uid)
    return result


@dataclass(frozen=True)
class TimelapseSchema:

    def __call__(self, output_path: Path, settings: TimelapseSettings) -> Path:
        frames_dir = settings.timelapse_dir / "frames"
        n_frames = _count_frames(frames_dir)
        first_frame = _first_frame(frames_dir)
        fps_ticks = int(PREMIERE_TIMEBASE / settings.fps)
        frames_dur = n_frames * fps_ticks
        seq_dur = (n_frames + (1 if settings.cover else 0)) * fps_ticks

        with gzip.open(_TEMPLATE_PATH, 'rb') as f:
            xml = f.read().decode('utf-8')

        xml = self._substitute_paths(xml, settings, first_frame)
        xml = self._substitute_ticks(xml, fps_ticks, frames_dur, seq_dur)
        xml = self._clear_audio_caches(xml)

        if not settings.sounds:
            xml = self._remove_sound(xml)
        else:
            sound_name = settings.sounds[0].name
            if sound_name != _WD_SOUND_NAME:
                xml = xml.replace(f"./sound/{_WD_SOUND_NAME}", f"./sound/{sound_name}")
                xml = xml.replace(_WD_SOUND_NAME, sound_name)
            if Path(sound_name).suffix.lower() in _AUDIO_ONLY_EXTS:
                xml = self._adapt_sound_to_audio_only(xml, sound_name)
            if len(settings.sounds) > 1:
                xml = self._add_extra_sounds(xml, settings.sounds)

        if not settings.cover:
            xml = self._remove_cover(xml, fps_ticks, frames_dur, seq_dur)

        xml = remove_dangling_refs(xml)

        with gzip.open(output_path, 'wb') as f:
            f.write(xml.encode('utf-8'))
        return output_path

    def _substitute_paths(self, xml: str, settings: TimelapseSettings, first_frame: str) -> str:
        xml = xml.replace(_WD_TIMELAPSE_DIR, str(settings.timelapse_dir))
        xml = xml.replace(f"./frames/{_WD_FIRST_FRAME}", f"./frames/{first_frame}")
        xml = xml.replace(_WD_FIRST_FRAME, first_frame)
        xml = xml.replace(_WD_PHOTOSET, settings.name)
        return xml

    def _substitute_ticks(self, xml: str, fps_ticks: int, frames_dur: int, seq_dur: int) -> str:
        # FPS
        for tag in ("OveriddenFrameRate", "FrameRate"):
            xml = xml.replace(f"<{tag}>{_WD_FPS_TICKS}</{tag}>", f"<{tag}>{fps_ticks}</{tag}>")
        xml = xml.replace(f"<End>{_WD_FPS_TICKS}</End>", f"<End>{fps_ticks}</End>")      # cover End
        xml = xml.replace(f"<Start>{_WD_FPS_TICKS}</Start>", f"<Start>{fps_ticks}</Start>")  # frames Start
        # Durations
        xml = xml.replace(f"<End>{_WD_SEQ_DUR}</End>", f"<End>{seq_dur}</End>")  # frames clip End (with cover)
        for tag in ("OriginalDuration", "OutPoint", "MZ.WorkOutPoint"):
            xml = xml.replace(f"<{tag}>{_WD_FRAMES_DUR}</{tag}>", f"<{tag}>{frames_dur}</{tag}>")
        return xml

    @staticmethod
    def _clear_audio_caches(xml: str) -> str:
        xml = re.sub(r'<ConformedAudioPath>[^<]+</ConformedAudioPath>', '<ConformedAudioPath></ConformedAudioPath>', xml)
        xml = re.sub(r'<PeakFilePath>[^<]+</PeakFilePath>', '<PeakFilePath></PeakFilePath>', xml)
        return xml

    @staticmethod
    def _adapt_sound_to_audio_only(xml: str, sound_name: str) -> str:
        """
        mp4 sound has VideoStream + VideoClip in its structure.
        For audio-only formats (mp3, wav, etc.) strip the video components:
          - Remove <VideoStream ObjectRef> from Media block + top-level VideoStream block
          - Remove VideoClip (and its Markers + VideoMediaSource sub-blocks)
          - Fix MasterClip Clips list: remove VideoClip entry, re-index AudioClip as Index=0
        """
        blocks = parse_toplevel_blocks(xml)

        # Find sound's Media block → get VideoStream ref
        sound_media = next(
            (b for b in _blocks_containing(blocks, sound_name) if b[2] == "Media"),
            None,
        )
        if sound_media is None:
            return xml
        vs_ref = re.search(r'<VideoStream ObjectRef="(\d+)"/>', sound_media[3])
        if vs_ref is None:
            return xml  # already audio-only
        vs_id = vs_ref.group(1)

        # Remove VideoStream ref from Media block
        new_media = sound_media[3].replace(f'\t\t<VideoStream ObjectRef="{vs_id}"/>\n', '')
        xml = xml[:sound_media[0]] + new_media + xml[sound_media[1]:]
        blocks = parse_toplevel_blocks(xml)

        # Find MasterClip → get VideoClip ref (Clip Index=0) and its sub-block IDs
        sound_mc = next(
            (b for b in _blocks_containing(blocks, sound_name) if b[2] == "MasterClip"),
            None,
        )
        vc_id: str | None = None
        vc_sub_ids: set[str] = set()
        if sound_mc:
            vc_m = re.search(r'<Clip Index="0" ObjectRef="(\d+)"/>', sound_mc[3])
            if vc_m:
                vc_id = vc_m.group(1)
                vc_block = next(
                    (b for b in blocks if b[2] == "VideoClip" and f'ObjectID="{vc_id}"' in b[3][:80]),
                    None,
                )
                if vc_block:
                    vc_sub_ids = set(re.findall(r'ObjectRef="(\d+)"', vc_block[3]))

        # Remove top-level blocks: VideoStream + VideoClip + its sub-blocks (Markers, VideoMediaSource)
        remove_ids = {vs_id} | ({vc_id} if vc_id else set()) | vc_sub_ids
        to_delete = [
            (b[0], b[1]) for b in blocks
            if any(f'ObjectID="{oid}"' in b[3][:80] for oid in remove_ids)
        ]
        xml = _remove_blocks_by_positions(xml, to_delete)

        # Fix MasterClip Clips list
        if vc_id and sound_mc:
            blocks = parse_toplevel_blocks(xml)
            sound_mc = next(
                (b for b in _blocks_containing(blocks, sound_name) if b[2] == "MasterClip"),
                None,
            )
            if sound_mc:
                mc_text = sound_mc[3]
                mc_text = mc_text.replace(f'\t\t<Clip Index="0" ObjectRef="{vc_id}"/>\n', '')
                mc_text = re.sub(r'<Clip Index="1" ObjectRef=', '<Clip Index="0" ObjectRef=', mc_text, count=1)
                xml = xml[:sound_mc[0]] + mc_text + xml[sound_mc[1]:]

        return xml

    @staticmethod
    def _remove_sound(xml: str) -> str:
        blocks = parse_toplevel_blocks(xml)
        snd_blocks = _blocks_containing(blocks, _WD_SOUND_NAME)
        xml = _remove_blocks_by_positions(xml, [(b[0], b[1]) for b in snd_blocks])
        return xml

    @staticmethod
    def _add_extra_sounds(xml: str, sounds: list[Path]) -> str:
        # Clone definition blocks for extra sounds (not placed in timeline — TODO: timeline wiring)
        blocks = parse_toplevel_blocks(xml)
        snd0_blocks = _blocks_containing(blocks, sounds[0].name)
        max_id = max(int(i) for i in re.findall(r'ObjectID="(\d+)"', xml))
        insert_pos = max(b[1] for b in snd0_blocks)
        extra = ""
        for i, snd in enumerate(sounds[1:], start=1):
            extra += _clone_sound_blocks(snd0_blocks, sounds[0].name, snd.name, (max_id + 1) * i)
        return xml[:insert_pos] + extra + xml[insert_pos:]

    @staticmethod
    def _remove_cover(xml: str, fps_ticks: int, frames_dur: int, seq_dur: int) -> str:
        # Remove media definition blocks for cover.jpg
        blocks = parse_toplevel_blocks(xml)
        cover_blocks = _blocks_containing(blocks, "cover.jpg")
        xml = _remove_blocks_by_positions(xml, [(b[0], b[1]) for b in cover_blocks])

        # remove_dangling_refs will cascade: SubClip[97] → VideoClipTrackItem[84] → TrackItems entry
        xml = remove_dangling_refs(xml)

        # Adjust frames clip: was [fps_ticks → seq_dur], now [0 → frames_dur]
        xml = xml.replace(f"<Start>{fps_ticks}</Start>", "<Start>0</Start>")
        xml = xml.replace(f"<End>{seq_dur}</End>", f"<End>{frames_dur}</End>")
        return xml


def generate_prproj(timelapse_dir: Path, fps: float = 10.0) -> Path:
    timelapse_dir = timelapse_dir.resolve()
    settings = from_timelapse_dir(timelapse_dir, fps)
    output_path = timelapse_dir / f"{settings.name}.prproj"

    if output_path.exists():
        i = 1

        while (candidate := timelapse_dir / f"{settings.name}_{i}.prproj").exists():
            i += 1

        output_path = candidate

    n_frames = _count_frames(timelapse_dir / "frames")

    print(f"Photoset:  {settings.name}")
    print(f"Frames:    {n_frames}{' + cover' if settings.cover else ''}")
    print(f"Sounds:    {[s.name for s in settings.sounds]}")
    print(f"FPS:       {fps}")

    return TimelapseSchema()(output_path, settings)
