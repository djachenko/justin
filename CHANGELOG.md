# CHANGELOG

<!-- version list -->

## v0.2.2 (2026-07-08)

### Bug Fixes

- Dropped usage of removed api call
  ([`117b06d`](https://github.com/djachenko/justin/commit/117b06d9c86399ac1045299ef10ee3b608386a59))

- Suppressed error for web syncing cullen sets
  ([`78ba62e`](https://github.com/djachenko/justin/commit/78ba62efa4d2f38fc52ec817fe3e78855092b8ef))

- Tuned upload batch size
  ([`61211d8`](https://github.com/djachenko/justin/commit/61211d8e4de1eea85c1ca87cd2b0ab0398fbd9a5))

### Chores

- [repokit] add Claude skill for repokit integration
  ([`acd8806`](https://github.com/djachenko/justin/commit/acd88063d53696824257b35feb76539db3854394))

- [repokit] update ci workflows
  ([`a87e6f5`](https://github.com/djachenko/justin/commit/a87e6f527e6041818919b2b4f596ccd2383cb7e6))

- Drop mypy overrides for actions removed in this branch (check_ratios, cms, event, fix_metafile,
  get_likers, manage_tags, move, populate)
  ([`d538585`](https://github.com/djachenko/justin/commit/d53858567b3c1eeab11f234b7943e02a49c83a03))

- Drop orphaned mypy override for removed actions/pattern_action.py
  ([`b08e5cc`](https://github.com/djachenko/justin/commit/b08e5ccfb8f2c00942959064d3ff7a74eea7f8c0))

- Remove src/justin/actions/attach_album_action.py, preserved on
  refactor/migrate-attach_album-to-typer
  ([`9d587b1`](https://github.com/djachenko/justin/commit/9d587b17aa05230ad9f4f1f859cfacbb20723218))

- Remove src/justin/actions/check_ratios_action.py, preserved on
  refactor/migrate-check_ratios-to-typer
  ([`3e65804`](https://github.com/djachenko/justin/commit/3e65804c18f5ead1d66116bf2b134e96878853f4))

- Remove src/justin/actions/cms_action.py, preserved on refactor/migrate-cms-to-typer
  ([`19c8ae4`](https://github.com/djachenko/justin/commit/19c8ae44f3dbdd68c43bcab82cc126c9e9a5d3f3))

- Remove src/justin/actions/delay_action.py, preserved on refactor/migrate-delay-to-typer
  ([`3e4be8c`](https://github.com/djachenko/justin/commit/3e4be8c0f8dac58ebc12ff3df4cd39be838d3e76))

- Remove src/justin/actions/delete_posts_action.py, preserved on
  refactor/migrate-delete_posts-to-typer
  ([`b4cec21`](https://github.com/djachenko/justin/commit/b4cec21fcd72752b5584c2aa915e415929629c9d))

- Remove src/justin/actions/drone.py, preserved on refactor/migrate-drone-to-typer
  ([`a4d42b5`](https://github.com/djachenko/justin/commit/a4d42b5d8e42b63c5f7dca00c0e7f0de684f7e5a))

- Remove src/justin/actions/event.py, preserved on refactor/migrate-event-to-typer
  ([`622883d`](https://github.com/djachenko/justin/commit/622883d653d58a1161d4550a544f0b99e5f8dfa2))

- Remove src/justin/actions/fix_metafile_action.py, preserved on
  refactor/migrate-fix_metafile-to-typer
  ([`ec98e78`](https://github.com/djachenko/justin/commit/ec98e7892464bd618ce115ac41ffebf0ec72eded))

- Remove src/justin/actions/get_empty_groups.py, preserved on
  refactor/migrate-get_empty_groups-to-typer
  ([`e7e8b0a`](https://github.com/djachenko/justin/commit/e7e8b0adeee6c1ab075696ae93ac2307dfd1f394))

- Remove src/justin/actions/get_likers_action.py, preserved on refactor/migrate-get_likers-to-typer
  ([`848f6ec`](https://github.com/djachenko/justin/commit/848f6ec7fdfd7db79e9e344fff79a1b8961075b1))

- Remove src/justin/actions/location.py, preserved on refactor/migrate-location-to-typer
  ([`54f84ec`](https://github.com/djachenko/justin/commit/54f84ec8b24c6c701c081ac3dd4993e76b815334))

- Remove src/justin/actions/manage_tags_action.py, preserved on
  refactor/migrate-manage_tags-to-typer
  ([`25b423d`](https://github.com/djachenko/justin/commit/25b423da9903a5354f00b96c10d977842570ec34))

- Remove src/justin/actions/move_action.py, preserved on refactor/migrate-move-to-typer
  ([`49070e4`](https://github.com/djachenko/justin/commit/49070e4ee56ab3b2ae5db73e2b49225349db9b1d))

- Remove src/justin/actions/people.py, preserved on refactor/migrate-people-to-typer
  ([`fffd2ba`](https://github.com/djachenko/justin/commit/fffd2ba79b5ec0c2e98294d23d6c8f9bb490ed4f))

- Remove src/justin/actions/populate_action.py, preserved on refactor/migrate-populate-to-typer
  ([`e361787`](https://github.com/djachenko/justin/commit/e361787e13e8b3007ab29d78fc075d1e44a1f358))

- Remove src/justin/actions/rearrange_action.py, preserved on refactor/migrate-rearrange-to-typer
  ([`7df6c89`](https://github.com/djachenko/justin/commit/7df6c8920d5157df0e3454c4b20859125e5af7e0))

- Remove src/justin/actions/split_action.py, preserved on refactor/migrate-split-to-typer
  ([`6250f58`](https://github.com/djachenko/justin/commit/6250f580bfee5c00785dd4960b2c678d3c4b86dd))

- Remove src/justin/actions/step_sources_action.py, preserved on
  refactor/migrate-step_sources-to-typer
  ([`ee72a8f`](https://github.com/djachenko/justin/commit/ee72a8f5b64dfbd72eceab545f75b87db524a62e))

- Remove unused dependencies (six, py_linq, google-auth-httplib2)
  ([`c48ba8b`](https://github.com/djachenko/justin/commit/c48ba8b836bd8ec03ad2ab72efc51bfd88462e79))

- Removed extra blank line
  ([`ea2c0ee`](https://github.com/djachenko/justin/commit/ea2c0ee82f805e2784daf1fd2722f3395fa97432))

- Updated typer version
  ([`d68167d`](https://github.com/djachenko/justin/commit/d68167d8599dc04267deea84d3758ef69f940ea7))

### Refactoring

- Move Extra type into pattern_command.py, remove dead
  actions/{pattern_action,destinations_aware_action,group_action}.py
  ([`aa9da08`](https://github.com/djachenko/justin/commit/aa9da08fb89b2e967c5c4ed0f1bcc3322e6c70d6))

- Removed filesystem.py and migrated to justin_utils
  ([`90d82c1`](https://github.com/djachenko/justin/commit/90d82c1e4ef62d8f90d03c6719e714c019f437ff))

- Removed sources.py and migrated to justin_utils
  ([`e6bbca1`](https://github.com/djachenko/justin/commit/e6bbca1228c64e3fe3ac559031a37affa0e97bd8))

- Replace RearrangeAction.DEFAULT_STEP import with local constant in UploadCommand
  ([`a9cc61f`](https://github.com/djachenko/justin/commit/a9cc61fd60361a1c9b7d86d14293c925c7841f80))


## v0.2.1 (2026-06-30)


## v0.2.0 (2026-06-30)

### Features

- Add ide_runner and ide_runner_types for PyCharm launch
  ([`2cff24e`](https://github.com/djachenko/justin/commit/2cff24ede532c1ef4c41d75e48bf1daef8cd3185))

### Refactoring

- Move hardcoded spreadsheet_id from app.py into Config
  ([`26a9009`](https://github.com/djachenko/justin/commit/26a9009a645ec15a995170a6a00863ec27eb47f3))


## v0.1.0 (2026-06-25)

- Initial Release

## v1.0.0 (2026-06-25)

- Initial Release
