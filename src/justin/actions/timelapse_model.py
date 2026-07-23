"""
A typed, read-only view over the project's top-level blocks.

The generator edits the project as raw text, by byte offsets. That is what keeps
it safe: everything it does not understand — the UI state, the dozens of settings
classes — stays byte-for-byte untouched, so Premiere still accepts the file. This
module does *not* change that. It is an **overlay**: it wraps blocks so you can
ask what they are and follow their pointers in typed terms. Every edit still goes
through ``Xml``. There is deliberately no serialization back out — a full
parse-and-rewrite would risk perturbing bytes we never meant to touch.

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

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import ClassVar, Iterator, NamedTuple, TypeVar

from justin.actions.timelapse_block import Block, Blocks
from justin.actions.timelapse_re import TimelapseRe, search_group
from justin.actions.timelapse_tags import Tag


class PremiereClass(NamedTuple):
    """A Premiere type: its ``ClassID`` and the tag that names it."""

    uuid: str
    tag: str


_T = TypeVar("_T", bound="PremiereObject")


class PremiereObject(ABC):
    """One top-level block, seen as the object it represents. Read-only.

    Subclasses declare their type in ``CLASS`` and are registered by ``ClassID``
    automatically, so :meth:`parse` can dispatch on it.
    """

    # None on the abstract bases, which describe an identity scheme rather than a type.
    CLASS: ClassVar[PremiereClass | None] = None

    _BY_CLASS_UUID: ClassVar[dict[str, type[PremiereObject]]] = {}

    def __init__(self, block: Block) -> None:
        self._block = block
        # The document this object belongs to — set by Document once it has parsed
        # the whole block list. Edges resolve their pointers through it, so an object
        # parsed on its own (no Document) can be read but not navigated.
        self._doc: Document | None = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        if cls.CLASS is not None:
            PremiereObject._BY_CLASS_UUID[cls.CLASS.uuid] = cls

    @property
    def block(self) -> Block:
        """The underlying block — the way back to raw text and byte offsets."""
        return self._block

    @property
    def tag(self) -> str:
        return self._block.tag

    @property
    def class_uuid(self) -> str | None:
        """The ``ClassID`` as written in the file (absent on non-object elements)."""
        return search_group(TimelapseRe.CLASS_ID, self._block.header)

    @property
    @abstractmethod
    def identity(self) -> str | None:
        """This object's own id, in whichever scheme its class uses."""
        ...

    @property
    def name(self) -> str | None:
        """The object's ``<Name>``, when it has one (clips, media, panel items do)."""
        return search_group(TimelapseRe.BLOCK_NAME, self._block.text)

    @property
    def refs(self) -> set[str]:
        """Numeric ids this object points at. Ambiguous without the target's class."""
        return set(re.findall(TimelapseRe.OBJECT_REF, self._block.text))

    @property
    def urefs(self) -> set[str]:
        """Uuids this object points at. Unambiguous."""
        return set(re.findall(TimelapseRe.OBJECT_UREF, self._block.text))

    def _ref(self, model_class: type[_T], pattern: str) -> _T | None:
        """Follow a numeric pointer (matched by ``pattern``) to a typed object.

        The target's class must be known — a number alone is ambiguous — so the
        caller names it. ``None`` if there's no such pointer or no document to
        resolve against.
        """
        if self._doc is None:
            return None

        return self._doc.by_ref(model_class, search_group(pattern, self._block.text))

    @classmethod
    def parse(cls, block: Block) -> PremiereObject:
        """Wrap a block in its model class, falling back to :class:`OpaqueObject`.

        Dispatches on ``ClassID``, not on the tag — see the module docstring.
        """
        class_uuid = search_group(TimelapseRe.CLASS_ID, block.header)

        if class_uuid is None:
            return OpaqueObject(block)

        return cls._BY_CLASS_UUID.get(class_uuid, OpaqueObject)(block)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.identity})"


class NumericObject(PremiereObject):
    """Identified by ``ObjectID`` — unique only within its own class."""

    @property
    def identity(self) -> str | None:
        return self._block.id


class UuidObject(PremiereObject):
    """Identified by ``ObjectUID`` — globally unique. Has no ``ObjectID`` at all."""

    @property
    def identity(self) -> str | None:
        return search_group(TimelapseRe.OBJECT_UID, self._block.header)


class OpaqueObject(PremiereObject):
    """A block outside the modelled media graph — read, never interpreted.

    Also covers top-level elements that are not objects at all, such as the bare
    ``<Project ObjectRef="1"/>`` forward reference.
    """

    @property
    def identity(self) -> str | None:
        if self._block.id is not None:
            return self._block.id

        return search_group(TimelapseRe.OBJECT_UID, self._block.header)


# ── panel and timeline containers (uuid identity) ──────────────────────────────

class RootProjectItem(UuidObject):
    CLASS = PremiereClass("1c307a89-9318-47d7-a583-bf2553736543", Tag.RootProjectItem)


class BinProjectItem(UuidObject):
    CLASS = PremiereClass("dbfd6653-24da-480e-a35e-ba45e9504e4b", Tag.BinProjectItem)


class Sequence(UuidObject):
    CLASS = PremiereClass("6a15d903-8739-11d5-af2d-9b7855ad8974", Tag.Sequence)


class VideoClipTrack(UuidObject):
    CLASS = PremiereClass("f68dcd81-8805-11d5-af2d-9bfa89d4ddd4", Tag.VideoClipTrack)


class AudioClipTrack(UuidObject):
    CLASS = PremiereClass("097f6203-99ae-11d5-84f2-8cf14bde7040", Tag.AudioClipTrack)


# ── clip hierarchy ─────────────────────────────────────────────────────────────

class ClipProjectItem(UuidObject):
    CLASS = PremiereClass("cb4e0ed7-aca1-4171-8525-e3658dec06dd", Tag.ClipProjectItem)


class MasterClip(UuidObject):
    CLASS = PremiereClass("fb11c33a-b0a9-4465-aa94-b6d5db2628cf", Tag.MasterClip)


class Media(UuidObject):
    CLASS = PremiereClass("7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff", Tag.Media)

    @property
    def video_stream(self) -> VideoStream | None:
        """The picture stream, present only while the media is still an mp4."""
        return self._ref(VideoStream, TimelapseRe.VIDEO_STREAM_REF)

    @property
    def audio_stream(self) -> AudioStream | None:
        """The sound stream — every media has one."""
        return self._ref(AudioStream, TimelapseRe.AUDIO_STREAM_REF)


class AudioClip(NumericObject):
    CLASS = PremiereClass("b8830d03-de02-41ee-84ec-fe566dc70cd9", Tag.AudioClip)


class VideoClip(NumericObject):
    CLASS = PremiereClass("9308dbef-2440-4acb-9ab2-953b9a4e82ec", Tag.VideoClip)


class SubClip(NumericObject):
    CLASS = PremiereClass("e0c58dc9-dbdd-4166-aef7-5db7e3f22e84", Tag.SubClip)

    # Edges deliberately absent for now:
    #   • `<Clip ObjectRef>` (→ Audio- or VideoClip): its tag names a role, not the
    #     target type, so it needs the ambiguous-pointer resolution — an open design
    #     question (grabli #3).
    #   • `.master_clip` (SubClip → MasterClip): this pointer runs UP the hierarchy
    #     (the child holds it), and nothing navigates it yet. Following-the-pointer
    #     (convention A) means we add edges on demand, not on spec.


# ── media streams ──────────────────────────────────────────────────────────────

class AudioStream(NumericObject):
    CLASS = PremiereClass("0b5cf52f-2b85-4863-890b-8844b64ecfe9", Tag.AudioStream)


class VideoStream(NumericObject):
    CLASS = PremiereClass("a36e4719-3ec6-4a0c-ab11-8b4aab377aa5", Tag.VideoStream)


class AudioMediaSource(NumericObject):
    CLASS = PremiereClass("f588da05-fc2a-4fbc-9383-74d653b379e3", Tag.AudioMediaSource)


class VideoMediaSource(NumericObject):
    CLASS = PremiereClass("e64ddf74-8fac-4682-8aa8-0e0ca2248949", Tag.VideoMediaSource)


# ── clip metadata and audio processing ─────────────────────────────────────────

class Markers(NumericObject):
    CLASS = PremiereClass("bee50706-b524-416c-9f03-b596ce5f6866", Tag.Markers)


class ClipLoggingInfo(NumericObject):
    CLASS = PremiereClass("77ab7fdd-dcdf-465d-9906-7a330ca1e738", Tag.ClipLoggingInfo)


class SecondaryContent(NumericObject):
    CLASS = PremiereClass("f9d004b5-cb04-4e2f-af6f-64fadc2c4be9", Tag.SecondaryContent)


class AudioComponentChain(NumericObject):
    CLASS = PremiereClass("3cb131d1-d3c0-47ae-a19a-bdf75ea11674", Tag.AudioComponentChain)


class ClipChannelSerializer(NumericObject):
    CLASS = PremiereClass("5c89aa7a-89a6-4483-becd-f2b1def42316", Tag.ClipChannelSerializer)


class ClipChannelGroupVectorSerializer(NumericObject):
    CLASS = PremiereClass("a3127a8c-95d4-456e-a7f5-171b3f922426", Tag.ClipChannelGroupVectorSerializer)


class ClipChannelVectorSerializer(NumericObject):
    CLASS = PremiereClass("333d203b-3a53-4195-8894-fc7523ff3dc7", Tag.ClipChannelVectorSerializer)


# ── timeline slots ─────────────────────────────────────────────────────────────

class AudioClipTrackItem(NumericObject):
    CLASS = PremiereClass("064ec682-9ba6-11d5-af2d-9ca32c7d6164", Tag.AudioClipTrackItem)

    @property
    def subclip(self) -> SubClip | None:
        """The sub-clip this timeline slot plays."""
        return self._ref(SubClip, TimelapseRe.SUBCLIP_REF)


class VideoClipTrackItem(NumericObject):
    CLASS = PremiereClass("368b0406-29e3-4923-9fcd-094fbf9a1089", Tag.VideoClipTrackItem)


class Document:
    """The document's top-level blocks, as model objects.

    A snapshot: valid only until the next mutation of the ``Xml`` it came from,
    exactly like the ``Blocks`` it wraps.
    """

    def __init__(self, blocks: Blocks) -> None:
        self._objects = [PremiereObject.parse(block) for block in blocks]

        # Hand every object a way back to the document, so its edges can resolve.
        for obj in self._objects:
            obj._doc = self

    def __iter__(self) -> Iterator[PremiereObject]:
        return iter(self._objects)

    def __len__(self) -> int:
        return len(self._objects)

    def of_type(self, model_class: type[_T]) -> list[_T]:
        return [o for o in self._objects if isinstance(o, model_class)]

    def by_ref(self, model_class: type[_T], object_id: str | None) -> _T | None:
        """Resolve a numeric reference — which needs the class to be unambiguous."""
        if object_id is None:
            return None

        return next((o for o in self.of_type(model_class) if o.identity == object_id), None)

    def by_uref(self, uid: str | None) -> PremiereObject | None:
        """Resolve a uuid reference. Globally unique, so no class needed."""
        if uid is None:
            return None

        return next((o for o in self._objects if o.identity == uid), None)
