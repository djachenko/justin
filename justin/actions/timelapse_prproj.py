import gzip
import re
import uuid
from pathlib import Path

PREMIERE_TIMEBASE = 254_016_000_000

TEMPLATE_PHOTOSET    = "26.04.09.eggressaince"
TEMPLATE_BASE_PATH   = "/Users/justin/photos/stages/stage1.filter/26.04.09.eggressaince/timelapse"
TEMPLATE_FIRST_FRAME = "ZSC_4847.jpg"
TEMPLATE_FPS         = 9.0
TEMPLATE_N_FRAMES    = 319
TEMPLATE_FRAME_TICKS = int(PREMIERE_TIMEBASE / TEMPLATE_FPS)
TEMPLATE_COVER_END   = TEMPLATE_FRAME_TICKS
TEMPLATE_SEQ_DURATION = (TEMPLATE_N_FRAMES + 1) * TEMPLATE_FRAME_TICKS
TEMPLATE_VS_DURATION  = TEMPLATE_N_FRAMES * TEMPLATE_FRAME_TICKS
TEMPLATE_SOUNDS      = ["caravany.mp3", "gagarin.mp3"]

TEMPLATE_PATH = Path(__file__).parent.parent / "resources" / "timelapse_template.prproj"


def fps_to_ticks(fps: float) -> int:
    return int(PREMIERE_TIMEBASE / fps)


def find_first_frame(frames_dir: Path) -> str:
    frames = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.jpeg"))
    if not frames:
        raise ValueError(f"No JPG files in {frames_dir}")
    return frames[0].name


def count_frames(frames_dir: Path) -> int:
    return len(list(frames_dir.glob("*.jpg")) + list(frames_dir.glob("*.jpeg")))


def find_sound_files(sound_dir: Path) -> list[str]:
    if not sound_dir.exists():
        return []
    return sorted(f.name for f in sound_dir.glob("*.mp3"))


def replace_json_field(xml: str, field: str, old_val: int, new_val: int) -> str:
    return re.sub(
        rf'("{re.escape(field)}":{re.escape(str(old_val))})',
        f'"{field}":{new_val}',
        xml,
    )


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


def remove_blocks_by_positions(xml: str, positions: list[tuple[int, int]]) -> str:
    for start, end in sorted(positions, reverse=True):
        xml = xml[:start] + xml[end:]
    return xml


def blocks_containing(blocks: list, text: str) -> list:
    return [b for b in blocks if text in b[3]]


def clone_sound_blocks(template_blocks: list[tuple], old_name: str, new_name: str, id_offset: int) -> str:
    combined = ''.join(b[3] for b in template_blocks)

    num_ids = sorted(set(re.findall(r'ObjectID="(\d+)"', combined)), key=int)
    id_map = {oid: str(int(oid) + id_offset) for oid in num_ids}

    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uid_map = {uid: str(uuid.uuid4()) for uid in set(re.findall(uuid_pattern, combined))}

    result = combined.replace(old_name, new_name)

    for old_id, new_id in id_map.items():
        result = re.sub(
            rf'((?:ObjectID|ObjectRef)="){re.escape(old_id)}"',
            rf'\g<1>{new_id}"',
            result,
        )

    for old_uid, new_uid in uid_map.items():
        result = result.replace(old_uid, new_uid)

    return result


def generate_prproj(timelapse_dir: Path, fps: float = 9.0) -> Path:
    timelapse_dir = timelapse_dir.resolve()
    photoset_name = timelapse_dir.parent.name

    frames_dir = timelapse_dir / "frames"
    sound_dir  = timelapse_dir / "sound"

    first_frame = find_first_frame(frames_dir)
    n_frames    = count_frames(frames_dir)
    sound_files = find_sound_files(sound_dir)

    frame_ticks  = fps_to_ticks(fps)
    cover_end    = frame_ticks
    seq_duration = (n_frames + 1) * frame_ticks
    vs_duration  = n_frames * frame_ticks
    base_path    = str(timelapse_dir)
    output_path  = timelapse_dir / f"{photoset_name}.prproj"

    print(f"Photoset:  {photoset_name}")
    print(f"Frames:    {n_frames} + 1 cover (first: {first_frame})")
    print(f"FPS:       {fps}")
    print(f"Duration:  {seq_duration / PREMIERE_TIMEBASE:.2f}s")
    print(f"Sounds:    {sound_files}")

    with gzip.open(TEMPLATE_PATH, 'rb') as f:
        xml = f.read().decode('utf-8')

    xml = xml.replace(TEMPLATE_BASE_PATH, base_path)
    xml = xml.replace(TEMPLATE_PHOTOSET, photoset_name)
    xml = xml.replace(TEMPLATE_FIRST_FRAME, first_frame)

    if frame_ticks != TEMPLATE_FRAME_TICKS:
        xml = xml.replace(
            f"<OveriddenFrameRate>{TEMPLATE_FRAME_TICKS}</OveriddenFrameRate>",
            f"<OveriddenFrameRate>{frame_ticks}</OveriddenFrameRate>",
        )
        xml = xml.replace(
            f"<FrameRate>{TEMPLATE_FRAME_TICKS}</FrameRate>",
            f"<FrameRate>{frame_ticks}</FrameRate>",
        )
    if cover_end != TEMPLATE_COVER_END:
        xml = xml.replace(f"<End>{TEMPLATE_COVER_END}</End>", f"<End>{cover_end}</End>")
    if seq_duration != TEMPLATE_SEQ_DURATION:
        xml = xml.replace(f"<End>{TEMPLATE_SEQ_DURATION}</End>", f"<End>{seq_duration}</End>")
    if vs_duration != TEMPLATE_VS_DURATION:
        xml = xml.replace(f"<Duration>{TEMPLATE_VS_DURATION}</Duration>", f"<Duration>{vs_duration}</Duration>")
    for field in ("OutPoint", "WorkOut", "CTI"):
        xml = replace_json_field(xml, field, TEMPLATE_SEQ_DURATION, seq_duration)
    xml = re.sub(r'<ConformedAudioPath>[^<]+</ConformedAudioPath>', '<ConformedAudioPath></ConformedAudioPath>', xml)
    xml = re.sub(r'<PeakFilePath>[^<]+</PeakFilePath>', '<PeakFilePath></PeakFilePath>', xml)
    xml = re.sub(
        r'<FilePath>[^<]*/Adobe Premiere Pro Audio Previews/[^<]+</FilePath>',
        '<FilePath></FilePath>', xml,
    )

    blocks = parse_toplevel_blocks(xml)
    tmpl_snd0 = TEMPLATE_SOUNDS[0]
    tmpl_snd1 = TEMPLATE_SOUNDS[1]
    snd0_blocks = blocks_containing(blocks, tmpl_snd0)

    all_ids = re.findall(r'ObjectID="(\d+)"', xml)
    max_id = max(int(i) for i in all_ids) if all_ids else 200

    insert_pos = max(b[1] for b in snd0_blocks)

    extra_blocks_text = ""
    for i, snd_file in enumerate(sound_files[1:], start=1):
        extra_blocks_text += clone_sound_blocks(snd0_blocks, tmpl_snd0, snd_file, id_offset=(max_id + 1) * i)

    xml = xml[:insert_pos] + extra_blocks_text + xml[insert_pos:]

    blocks = parse_toplevel_blocks(xml)
    snd1_blocks_new = blocks_containing(blocks, tmpl_snd1)
    xml = remove_blocks_by_positions(xml, [(b[0], b[1]) for b in snd1_blocks_new])

    if sound_files:
        xml = xml.replace(tmpl_snd0, sound_files[0])
    else:
        blocks = parse_toplevel_blocks(xml)
        snd0_blocks_new = blocks_containing(blocks, tmpl_snd0)
        xml = remove_blocks_by_positions(xml, [(b[0], b[1]) for b in snd0_blocks_new])

    with gzip.open(output_path, 'wb') as f:
        f.write(xml.encode('utf-8'))

    return output_path
