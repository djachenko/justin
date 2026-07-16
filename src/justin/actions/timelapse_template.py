class TimelapseTemplate:
    """Placeholder strings baked into the wolfday ``template.prproj``.

    These are facts about the specific template we clone from — the abstract names
    it uses so we can find and swap them for a real timelapse's values. Kept in a
    neutral module so both the schema (which substitutes them) and Sound (which
    renames its cloned section) can reference one source without a circular import.
    """

    SOUND_NAME  = "TMPL_SOUND.mp4"
    FIRST_FRAME = "TMPL_FIRST_FRAME.jpg"
    PHOTOSET    = "TMPL_PHOTOSET"
