"""
A typed view over the project's top-level blocks.

The generator edits the project as raw text, by byte offsets. That is what keeps
it safe: everything it does not understand — the UI state, the dozens of settings
classes — stays byte-for-byte untouched, so Premiere still accepts the file. This
module does *not* change that. It is an **overlay**: it wraps blocks so you can
ask what they are and follow their pointers in typed terms.

Reads are properties (``slot.subclip.clip``). Writes are methods returning an
:class:`Edit` — one block's span plus its new text — which nothing applies but
``Xml``. So a write is a *value*, not a mutation: the model stays a snapshot,
edits stay collectable, and ``Xml`` can still apply them from the end of the
document backwards with the offsets intact. There is deliberately no
serialization back out — a full parse-and-rewrite would risk perturbing bytes we
never meant to touch.

What a class is here
--------------------
A block's ``ClassID`` is a uuid naming its *type* (not the object — the type).
It is a constant compiled into Premiere: every ``MasterClip`` in every project
carries the same one. The tag is just the type's human-readable name.

The mapping is asymmetric, and that is why dispatch keys on ``ClassID``:

  * ``ClassID`` → tag is one-to-one;
  * tag → ``ClassID`` is *not*. ``AudioComponentParam`` exists as two distinct
    classes — a continuous parameter and a toggle — under one tag.

Two identity schemes
--------------------
An object identifies itself in one of two mutually exclusive ways; no object
carries both:

  * ``ObjectID`` — a small number, unique only among objects of the *same class*,
    pointed at by ``ObjectRef``. The key is therefore ``(class, number)``, never
    the number alone. Modelled by :class:`NumericObject`.
  * ``ObjectUID`` — a globally unique uuid, pointed at by ``ObjectURef``. Carried
    by the eight classes referenced across subsystem boundaries (panel ↔ timeline).
    Modelled by :class:`UuidObject`.

Which scheme a class uses is fixed, so it is expressed by which base class the
model class inherits from rather than by a runtime check.

Scope
-----
Only top-level blocks (depth 1) are modelled. The nested objects inside
``Project`` are project-panel UI state, they never touch the media graph, and
they are numbered in a separate counter — merging them in would conflate two
independent id spaces. Classes that are not modelled degrade to
:class:`OpaqueObject`, which still reads its tag and identity but claims no
meaning.

The full class inventory and the measurements behind all of this are kept in the
project's ``.prproj`` format notes (reverse-engineering reference in memory).
"""

import re
from abc import ABC, abstractmethod
from functools import cached_property
from typing import ClassVar, Iterator, NamedTuple, TypeVar

from justin.actions.timelapse_block import Block, Blocks, Edit
from justin.actions.timelapse_re import TimelapseRe, search_group
from justin.actions.timelapse_tags import Tag


class PremiereClass(NamedTuple):
    """A Premiere type: its ``ClassID`` and the tag that names it.

    ``uuid`` is the type's ``ClassID``, not an object's id: a constant compiled into
    Premiere, the same in every project. The values in the ``CLASS`` declarations
    below were read off the template (see the module docstring).
    """

    uuid: str
    tag: str


class AmbiguousReference(Exception):
    """A numeric ref matched more than one object of the requested class.

    Only possible for a base class spanning several ClassIDs (``Clip``): the ids
    collide across its subclasses, so the pointer can't be resolved to one target.
    """

    def __init__(self, model_class: type, object_id: str, matches: list) -> None:
        super().__init__(
            f"{model_class.__name__} id {object_id} matched {len(matches)}: "
            f"{[type(match).__name__ for match in matches]}"
        )


class MissingPointer(Exception):
    """A pointer an edit meant to remove is not written the way it was rebuilt.

    Never expected: the callers only ask for pointers they have already resolved.
    So this says the block's layout is not what the code assumes — a different
    indentation, or a half sitting in the other slot.
    """

    def __init__(self, obj: "PremiereObject", line: str) -> None:
        super().__init__(f"{obj!r} has no {line.strip()}")


_T = TypeVar("_T", bound="PremiereObject")


class PremiereObject(ABC):
    """One top-level block, seen as the object it represents. Read-only.

    Subclasses declare their type in ``CLASS`` and are registered by ``ClassID``
    automatically, so :meth:`parse` can dispatch on it.
    """

    # None on the abstract bases, which describe an identity scheme rather than a type.
    CLASS: ClassVar[PremiereClass | None] = None

    # ClassID uuid → the model class for it. Values are PremiereObject subclasses;
    # the type can't say so without naming the class inside its own body.
    _BY_CLASS_UUID: ClassVar[dict[str, type]] = {}

    def __init__(self, block: Block, doc: "Document | None" = None) -> None:
        """Wrap ``block``; ``doc`` is the document it belongs to, if any.

        Edges resolve their pointers through ``doc``, so an object parsed on its own
        (no Document) can be read but not navigated. Pointers are followed lazily,
        so ``doc`` may still be filling up while its objects are created.
        """
        self._block = block
        self._doc = doc

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Register every subclass that declares a ``CLASS``, keyed by its ``ClassID``.

        Defining a model class is all it takes to make :func:`parse` produce it; the
        abstract bases (``CLASS = None``) are skipped.
        """
        super().__init_subclass__(**kwargs)

        if cls.CLASS is not None:
            PremiereObject._BY_CLASS_UUID[cls.CLASS.uuid] = cls

    @classmethod
    def class_for(cls, class_uuid: str) -> "type[PremiereObject] | None":
        """The model class registered for ``class_uuid``, or ``None`` if it is not modelled."""
        return PremiereObject._BY_CLASS_UUID.get(class_uuid)

    @property
    def block(self) -> Block:
        """The underlying block — the way back to raw text and byte offsets."""
        return self._block

    @property
    def tag(self) -> str:
        """The block's top-level tag — the class's readable name, not its identity."""
        return self._block.tag

    @property
    def class_uuid(self) -> str | None:
        """The ``ClassID`` as written in the file (absent on non-object elements)."""
        return search_group(TimelapseRe.CLASS_ID, self._block.header)

    @property
    @abstractmethod
    def identity(self) -> str | None:
        """This object's own id, in whichever scheme its class uses."""
        pass

    @property
    def name(self) -> str | None:
        """The object's ``<Name>``, when it has one (clips, media, panel items do)."""
        return search_group(TimelapseRe.BLOCK_NAME, self._block.text)

    @property
    def refs(self) -> set[str]:
        """Numeric ids this object points at. Ambiguous without the target's class."""
        return set(re.findall(TimelapseRe.OBJECT_REF, self._block.text))

    def _ref(self, model_class: type[_T], pattern: str) -> _T | None:
        """Follow a numeric pointer (matched by ``pattern``) to a typed object.

        The target's class must be known — a number alone is ambiguous — so the
        caller names it. ``None`` if there's no such pointer or no document to
        resolve against.
        """
        if self._doc is None:
            return None

        return self._doc.by_ref(model_class, search_group(pattern, self._block.text))

    def _edit(self, text: str) -> Edit:
        """This object's block, rewritten as ``text`` — an edit for ``Xml`` to apply."""
        return Edit(self._block.start, self._block.end, text)

    @staticmethod
    def _pointer(tag: str, **attributes: object) -> str:
        """A pointer element exactly as the file writes it: ``<Tag Attr="v"/>``.

        The one place that knows the shape. Written out by hand in two classes it
        would be two places to fix, and a mismatch fails silently — the text just
        stays as it was.
        """
        written = " ".join(f'{name}="{value}"' for name, value in attributes.items())

        return f"<{tag} {written}/>"

    def _without_pointer(self, tag: str, **attributes: object) -> str:
        """This block's text with that pointer gone — its whole line, indentation and
        trailing newline included, so no blank line is left behind.

        The line is rebuilt and matched literally, so a mismatch means an assumption
        about the layout broke. Raising is the point: ``str.replace`` would return the
        text unchanged, the edit would rewrite the block as itself, and the pointer
        would survive into a file that Premiere then refuses to open — far from here.
        """
        line = f"\t\t{self._pointer(tag, **attributes)}\n"

        if line not in self._block.text:
            raise MissingPointer(self, line)

        return self._block.text.replace(line, "")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.identity})"


class NumericObject(PremiereObject):
    """Identified by ``ObjectID`` — unique only within its own class."""

    @cached_property
    def identity(self) -> str | None:
        """The ``ObjectID`` — a number, so it names the object only together with its class."""
        return self._block.id


class UuidObject(PremiereObject):
    """Identified by ``ObjectUID`` — globally unique. Has no ``ObjectID`` at all."""

    @cached_property
    def identity(self) -> str | None:
        """The ``ObjectUID`` — a uuid, unique across the whole document on its own."""
        return search_group(TimelapseRe.OBJECT_UID, self._block.header)


class OpaqueObject(PremiereObject):
    """A block outside the modelled media graph — read, never interpreted.

    Also covers top-level elements that are not objects at all, such as the bare
    ``<Project ObjectRef="1"/>`` forward reference.
    """

    @cached_property
    def identity(self) -> str | None:
        """Whichever id the block carries: ``ObjectID`` first, else ``ObjectUID``.

        An unmodelled class gives no hint which scheme it uses, so both are tried;
        no block carries both, so the order does not matter.
        """
        if self._block.id is not None:
            return self._block.id

        return search_group(TimelapseRe.OBJECT_UID, self._block.header)


# ── clip hierarchy ─────────────────────────────────────────────────────────────

class ClipProjectItem(UuidObject):
    """A clip's entry in the project panel — what the user sees in the bin, by name."""

    CLASS = PremiereClass("cb4e0ed7-aca1-4171-8525-e3658dec06dd", Tag.ClipProjectItem)


class Clip(NumericObject):
    """The audio or video half of a master clip.

    A shared base for AudioClip and VideoClip so a ``<Clip>`` pointer — whose tag
    is a role, not a type — resolves polymorphically: we look it up as a ``Clip``
    and get back whichever half it actually names, already correctly typed by the
    ClassID dispatch in ``parse``.
    """

    def trimmed_to(self, duration: int) -> Edit | None:
        """This clip, playing only ``duration`` ticks of its media.

        ``None`` when the clip has no ``OutPoint`` — then there is nothing to trim,
        and saying so is more honest than handing back an edit that changes nothing.
        """
        if not re.search(TimelapseRe.OUT_POINT, self._block.text):
            return None

        return self._edit(
            re.sub(TimelapseRe.OUT_POINT, f"<OutPoint>{duration}</OutPoint>", self._block.text, count=1)
        )


class AudioClip(Clip):
    """The audio half of a master clip; its ``OutPoint`` is how long the sound plays."""

    CLASS = PremiereClass("b8830d03-de02-41ee-84ec-fe566dc70cd9", Tag.AudioClip)


class VideoClip(Clip):
    """The video half of a master clip — the picture side an audio-only sound drops."""

    CLASS = PremiereClass("9308dbef-2440-4acb-9ab2-953b9a4e82ec", Tag.VideoClip)


# MasterClip and SubClip name Clip in their edges, so they follow it.
class MasterClip(UuidObject):
    """Project material — a file or a sequence — grouping its video and audio halves."""

    CLASS = PremiereClass("fb11c33a-b0a9-4465-aa94-b6d5db2628cf", Tag.MasterClip)

    @property
    def clips(self) -> list[Clip]:
        """Its halves, in the order the slots list them.

        The order is *not* a guarantee: in the shipped template the sound's master
        clip is video-then-audio, while the sequence's own master clip is the other
        way round. Ask the type (``isinstance``), never the position.
        """
        if self._doc is None:
            return []

        ids = re.findall(TimelapseRe.CLIP_SLOT_REFS, self._block.text)

        return [clip for i in ids if (clip := self._doc.by_ref(Clip, i)) is not None]

    def without_video_half(self, video: VideoClip, audio: AudioClip) -> Edit:
        """This master clip with only its audio half, moved up to slot 0 — what it
        looks like once the picture side is stripped for an audio-only file.

        Assumes the media layout the template's sound has: video in slot 0, audio in
        slot 1 (see :meth:`clips` — that order is not universal).
        """
        audio_only = self._without_pointer(Tag.Clip, Index=0, ObjectRef=video.block.id)

        return self._edit(audio_only.replace(
            self._pointer(Tag.Clip, Index=1, ObjectRef=audio.block.id),
            self._pointer(Tag.Clip, Index=0, ObjectRef=audio.block.id),
        ))


class SubClip(NumericObject):
    """What a timeline slot plays: one half of a master clip, under the slot's name.

    The playing range is not stored here but in the clip half it points at.
    """

    CLASS = PremiereClass("e0c58dc9-dbdd-4166-aef7-5db7e3f22e84", Tag.SubClip)

    @property
    def clip(self) -> Clip | None:
        """The clip half this sub-clip plays — Audio- or VideoClip, resolved through
        the shared Clip base since the ``<Clip>`` tag names a role, not a type."""
        return self._ref(Clip, TimelapseRe.CLIP_REF)

    # `.master_clip` (SubClip → MasterClip) is deliberately absent: that pointer runs
    # UP the hierarchy (the child holds it) and nothing navigates it yet — convention
    # A adds edges on demand, not on spec.


# ── media streams ──────────────────────────────────────────────────────────────

class AudioStream(NumericObject):
    """The audio stream of a media file. No behaviour of its own yet."""

    CLASS = PremiereClass("0b5cf52f-2b85-4863-890b-8844b64ecfe9", Tag.AudioStream)


class VideoStream(NumericObject):
    """The picture stream of a media file — the target of :attr:`Media.video_stream`."""

    CLASS = PremiereClass("a36e4719-3ec6-4a0c-ab11-8b4aab377aa5", Tag.VideoStream)


# Media holds the stream, so it comes after it: its edge names VideoStream
# directly, which only works once that is defined.
class Media(UuidObject):
    """A file reference: path, streams and codec info of one file on disk."""

    CLASS = PremiereClass("7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff", Tag.Media)

    @property
    def video_stream(self) -> VideoStream | None:
        """The picture stream, present only while the media is still an mp4."""
        return self._ref(VideoStream, TimelapseRe.VIDEO_STREAM_REF)

    def without_video_stream(self, stream: VideoStream) -> Edit:
        """This media, audio-only: the pointer to its picture stream taken out.

        The stream is passed in rather than looked up again — the caller has to hold
        it anyway, to decide there is a picture side at all.
        """
        return self._edit(self._without_pointer(Tag.VideoStream, ObjectRef=stream.block.id))


# ── clip metadata ──────────────────────────────────────────────────────────────

class Markers(NumericObject):
    """A clip's in/out markers. One block can be shared by several clips. No behaviour yet."""

    CLASS = PremiereClass("bee50706-b524-416c-9f03-b596ce5f6866", Tag.Markers)


# ── timeline slots ─────────────────────────────────────────────────────────────

class AudioClipTrackItem(NumericObject):
    """A slot on an audio track: where on the timeline a sub-clip plays."""

    CLASS = PremiereClass("064ec682-9ba6-11d5-af2d-9ca32c7d6164", Tag.AudioClipTrackItem)

    @property
    def subclip(self) -> SubClip | None:
        """The sub-clip this timeline slot plays."""
        return self._ref(SubClip, TimelapseRe.SUBCLIP_REF)

    def placed_at(self, start: int | None, end: int) -> Edit:
        """This slot, sitting from ``start`` to ``end`` (ticks) on its track.

        ``start=None`` writes no Start element at all — that is how a slot at tick 0
        is stored, and Premiere reads the absence as 0.
        """
        if start is not None:
            position = f"<Start>{start}</Start>\n\t\t\t\t<End>{end}</End>"
        else:
            position = f"<End>{end}</End>"

        return self._edit(re.sub(TimelapseRe.SLOT_POSITION, position, self._block.text, count=1))


def parse(block: Block, doc: "Document | None" = None) -> PremiereObject:
    """Wrap a block in its model class, falling back to :class:`OpaqueObject`.

    Dispatches on ``ClassID``, not on the tag — see the module docstring. A plain
    function, not a classmethod, so its return type can be named directly. ``doc``
    is passed on to the object, see :class:`PremiereObject`.
    """
    class_uuid = search_group(TimelapseRe.CLASS_ID, block.header)

    if class_uuid is None:
        return OpaqueObject(block, doc)

    model_class = PremiereObject.class_for(class_uuid) or OpaqueObject

    return model_class(block, doc)


class Document:
    """The document's top-level blocks, as model objects.

    A snapshot: valid only until the next mutation of the ``Xml`` it came from,
    exactly like the ``Blocks`` it wraps.
    """

    def __init__(self, blocks: Blocks) -> None:
        """Parse ``blocks``, handing every object a way back to this document."""
        self._objects = [parse(block, self) for block in blocks]

    def __iter__(self) -> Iterator[PremiereObject]:
        return iter(self._objects)

    def of_type(self, model_class: type[_T]) -> list[_T]:
        """Every object that is a ``model_class``, subclasses included, in document order.

        Subclasses count, so asking for ``Clip`` returns both Audio- and VideoClips.
        """
        return [o for o in self._objects if isinstance(o, model_class)]

    def by_ref(self, model_class: type[_T], object_id: str | None) -> _T | None:
        """Resolve a numeric reference — which needs the class to be unambiguous.

        A number is unique only within a ClassID, so a base class spanning several
        (``Clip`` → Audio/VideoClip) could match more than one object — that means
        the ids collide across the family, and rather than guess we fail loud.
        """
        if object_id is None:
            return None

        matches = [o for o in self.of_type(model_class) if o.identity == object_id]

        if len(matches) > 1:
            raise AmbiguousReference(model_class, object_id, matches)

        return next(iter(matches), None)
