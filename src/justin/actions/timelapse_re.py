# Attribute patterns used throughout Premiere Pro XML blocks.
_OBJECT_ID_RE = r'ObjectID="(\d+)"'        # numeric id, unique within ClassID
_OBJECT_UID_RE = r'ObjectUID="([^"]+)"'    # instance uuid, globally unique
_OBJECT_UREF_RE = r'ObjectURef="([^"]+)"'  # pointer to another block's uuid
_OBJECT_REF_RE = r'ObjectRef="(\d+)"'      # pointer to another block's numeric id

# UUID patterns used when cloning blocks to a fresh identity.
_IDENTITY_UUID_RE = r'Object(?:UID|URef)="([0-9a-f-]{36})"'  # instance uuid in any ObjectUID/URef attr
_BARE_ID_TAG_RE = r'<ID>([0-9a-f-]{36})</ID>'                 # uuid in a bare <ID> element
