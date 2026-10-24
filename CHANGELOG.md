# CHANGELOG

<!-- version list -->

## v0.6.0 (2026-10-24)

### Bug Fixes

- Apply settings the way VK actually accepts them
  ([`f74291f`](https://github.com/djachenko/justin/commit/f74291fdd6c4a5f66028cc14c865e8aa1c0244a0))

- Click_save waits for the button via found and first
  ([`d53360a`](https://github.com/djachenko/justin/commit/d53360afda7974defbd4dc4a389d013cd86cd4cf))

- Custom select holder by combobox role, add set_custom_select_at
  ([`fdd6491`](https://github.com/djachenko/justin/commit/fdd6491642ae7a90774926664d20b4ac4f0f6927))

- Date check compares the whole date, drop tautological hidden-field check
  ([`f97668c`](https://github.com/djachenko/justin/commit/f97668c4240779ebee248638d02a6fb6d9d4576a))

- Honest types instead of suppressed errors
  ([`3fdf6ac`](https://github.com/djachenko/justin/commit/3fdf6ac0019ca2bf527fc023d0204a41e4440c61))

- New_wait honours a zero timeout
  ([`3477054`](https://github.com/djachenko/justin/commit/34770549dc4b5b5dd1d9aa3d48ce54aac13ba569))

- Open the browser at 1440x900
  ([`3999bc2`](https://github.com/djachenko/justin/commit/3999bc223707fea639d0f2a10d5c224e1c32e8cd))

- Pin Chrome 152 and announce the browser start
  ([`3e9b6e4`](https://github.com/djachenko/justin/commit/3e9b6e4f446eb742000aadfeb084e67eaba4b155))

- Sections schema for the split Content tabs and Sections pages
  ([`5c5f019`](https://github.com/djachenko/justin/commit/5c5f0198d7491ef6938f51599ddf103d862a5e4b))

- Setup-event links the folder before applying settings
  ([`dd74bb2`](https://github.com/djachenko/justin/commit/dd74bb2c07da9bceabc8ed0b7d397b64ce96ce83))

### Build System

- Honest Python floor and a pinned ruff
  ([`5803b9f`](https://github.com/djachenko/justin/commit/5803b9f76905f18b6c6794c20a5ed8b1ca5f5a44))

- Load .env in tests with python-dotenv
  ([`d885dd8`](https://github.com/djachenko/justin/commit/d885dd8f19e3276c1747b1d09b1700475e52c5a3))

- Python-dotenv in the test extra
  ([`069b4e8`](https://github.com/djachenko/justin/commit/069b4e847f639a890a90bb11df6c62d348379d88))

- Require the justin_utils we actually build against
  ([`d58b6b4`](https://github.com/djachenko/justin/commit/d58b6b4507bcf097aa7cc80822a9f2e15eea7943))

- Test markers, timeouts and default selection
  ([`7e30784`](https://github.com/djachenko/justin/commit/7e30784850d9f5ec03f411e14e0f7b5d6a8df786))

### Chores

- Drop probes/dump_page.py
  ([`dc4730f`](https://github.com/djachenko/justin/commit/dc4730f3af927d78c8c4f2a9c5e2f6db25f8f397))

- Drop removed module from mypy overrides
  ([`84805f6`](https://github.com/djachenko/justin/commit/84805f608271971dcc5ed11a8c93f14e40862d3b))

- Placeholder test event id in .env.example
  ([`b195524`](https://github.com/djachenko/justin/commit/b1955244706ef90d039d78cd669b4402da3ae6a5))

- Setuptools package discovery, destructive pytest marker
  ([`5a49f7a`](https://github.com/djachenko/justin/commit/5a49f7a17fe28f5dc449729e640c15295ed1f9d7))

- Test event id via .env
  ([`c611f68`](https://github.com/djachenko/justin/commit/c611f680038f7b67819ed5f4584458f2c49729d8))

### Code Style

- Unused imports and empty f-strings
  ([`c1bfdb0`](https://github.com/djachenko/justin/commit/c1bfdb0ac65238606165d0649dfa978854a126a7))

### Documentation

- Browser shared modules, run mode and Folder location
  ([`ef56e24`](https://github.com/djachenko/justin/commit/ef56e244fb9b0caffa60b41df3104b9845b28609))

- Drop status notes from CLAUDE.md
  ([`7227b8e`](https://github.com/djachenko/justin/commit/7227b8e9a1d8af43b9ae4e6505403ce48310b6ea))

- Refresh project structure
  ([`9b90d02`](https://github.com/djachenko/justin/commit/9b90d02ac421b3b89ec210ed8a83ae31c7d5585f))

### Features

- Add setup-event command with VKBrowser
  ([`1cd3a01`](https://github.com/djachenko/justin/commit/1cd3a01e85b8120bf22dc29584cf1992e2f194ba))

- Debug-aware browser and randomised pauses
  ([`a7b3730`](https://github.com/djachenko/justin/commit/a7b373029e8170b62759f02b41e87f21403b26ba))

- EventCreationSchema — schema-driven 3-step wizard
  ([`8cda18c`](https://github.com/djachenko/justin/commit/8cda18ce9c6a5087ee3a328cc07befb98cd5c086))

- EventSettingsSchema — schema-driven post-creation settings
  ([`a21d54b`](https://github.com/djachenko/justin/commit/a21d54bcdda3e52fe4a8dfdeb595cd30074c588f))

- Invite links
  ([`cbc8885`](https://github.com/djachenko/justin/commit/cbc88852fe9bbb064c352c146f54a4e7eb14dbfb))

- Page explorers and a structure dumper
  ([`679a843`](https://github.com/djachenko/justin/commit/679a8436c3c05231dfcf6a8e87dd089c564a5444))

- Setup-event configures the whole event
  ([`389af3a`](https://github.com/djachenko/justin/commit/389af3a122176556d203f39ddf6a71074f546950))

- Setup-event picks the folder, links it and writes GroupMetafile
  ([`8e6bd83`](https://github.com/djachenko/justin/commit/8e6bd83757df1cd32a2bde42c2d3d951795e02ba))

- VKBrowser — create_event via schema, apply_settings
  ([`73a5f09`](https://github.com/djachenko/justin/commit/73a5f0970aaffc3797a7932bbf033f8e0aafd748))

### Refactoring

- Browser layer on vk.ru with namespaced selectors and verified setters
  ([`8dea847`](https://github.com/djachenko/justin/commit/8dea847286a8f8ec411c2af580d73a1b9846468a))

- Creation wizard after review
  ([`5704672`](https://github.com/djachenko/justin/commit/5704672496304805b2005126a346a7c83d0fee52))

- Deviate a pause by a share of itself
  ([`dd42b91`](https://github.com/djachenko/justin/commit/dd42b91ca13b4d5c254d971c54fc5b141551ead3))

- Drop the dead branches of VKBrowser
  ([`f859fcf`](https://github.com/djachenko/justin/commit/f859fcfacc0109579206a05f1ef9ea377621ee17))

- Drop the unreachable _explore_sub_clicks
  ([`954c273`](https://github.com/djachenko/justin/commit/954c273f19c993b68674706ca7c1618bed816cc7))

- Event settings schema after review
  ([`07bd1e1`](https://github.com/djachenko/justin/commit/07bd1e1f2e06c23ad9171d8b85f22c635a581e18))

- Field base for section controls, section modal nested in SectionSchema
  ([`b31c86d`](https://github.com/djachenko/justin/commit/b31c86d0b250d5900fa2373cead498c8e273a37e))

- Group browser by feature
  ([`da03eb2`](https://github.com/djachenko/justin/commit/da03eb2570dd9fcb9e03a63a0a8afa036e61070e))

- Locator sugar everywhere, debug dump inside Wait
  ([`3afe60d`](https://github.com/djachenko/justin/commit/3afe60d18722c27c5b79d2960e90628862c13367))

- Mypy debt test without nested comprehension
  ([`05e4213`](https://github.com/djachenko/justin/commit/05e4213e7f07c4961d1aa081cf0b62ab5b271883))

- Named pauses and consistent layout across the schemas
  ([`16be688`](https://github.com/djachenko/justin/commit/16be68846bec21560b6542ded62e731c55143714))

- Salvage live logic from the legacy wizard
  ([`85679f0`](https://github.com/djachenko/justin/commit/85679f09d8eff950dc64f72c07ae074e42a51296))

- Schema-driven section configuration with tests
  ([`73b281b`](https://github.com/djachenko/justin/commit/73b281bb37ebee0b77911d62b094317cc095c3b2))

- Setup-event on top of PatternCommand
  ([`687bfaf`](https://github.com/djachenko/justin/commit/687bfaf8ce56c1b535c4376cd210c164f073c0ac))

- Setup_event_command — apply_settings replaces set_sections + API call
  ([`ccb86f8`](https://github.com/djachenko/justin/commit/ccb86f8f79b50e91dc958e286f826445bec53b8c))

- Type browser element and driver parameters
  ([`f4ab5eb`](https://github.com/djachenko/justin/commit/f4ab5eb88883fc1928051752273a63895fb2a970))

- Unique module names inside packages
  ([`2c128ca`](https://github.com/djachenko/justin/commit/2c128ca5c0f6622eae3ed32603618345bc23da65))

- Vary pauses with a function, not a generator
  ([`19db9dc`](https://github.com/djachenko/justin/commit/19db9dca0b95adb6b75ce7c7ccb6a3f64397762a))

- Walrus for album metafile lookup
  ([`5a8960c`](https://github.com/djachenko/justin/commit/5a8960c069e1b6401933f47fe7bba0149cad3f23))

### Testing

- Completion test needs the real config, mark it performance
  ([`2cc3756`](https://github.com/djachenko/justin/commit/2cc37567ee5233a8b6c802005554eec2f3c501c5))

- Group helper tests into classes, English docstrings
  ([`4f5d055`](https://github.com/djachenko/justin/commit/4f5d055b950cf049a23b74817f98376d767dd9f5))

- Integration tests for event creation and apply_settings
  ([`68fa298`](https://github.com/djachenko/justin/commit/68fa298710a985826b3f977332757584ffa2f212))

- Offline coverage for sections, event settings, creation fields and shared helpers
  ([`3a696f1`](https://github.com/djachenko/justin/commit/3a696f11cf66243f54005893d02a646555439ee7))

- Perf tests run justin next to the interpreter, cover completion
  ([`28320d5`](https://github.com/djachenko/justin/commit/28320d56dd90b7fc438c96e9ebe46ce731cad13b))

- Selector contract, fewer VK requests, startup budgets
  ([`e8cc6aa`](https://github.com/djachenko/justin/commit/e8cc6aa186a6645fb379a74a9bac8b0285e38bcf))

- Shared fast_wait and no_pauses for offline browser tests
  ([`0931090`](https://github.com/djachenko/justin/commit/09310907bc6f8f8ff809fbbcaa30a0885cb575eb))


## v0.5.0 (2026-10-18)


## v0.4.1 (2026-10-18)

### Bug Fixes

- Register EditedHook in ourate stage hooks
  ([`416f1dd`](https://github.com/djachenko/justin/commit/416f1dd52a042f207312577e6cf434c3a799158d))


## v0.4.0 (2026-10-18)

### Chores

- Ignore CLAUDE.local.md, add GROUP to ide runner commands
  ([`d68ef8d`](https://github.com/djachenko/justin/commit/d68ef8db5cc3f98a9c71fc6975293e802422ef9d))

### Features

- Name Cullen json by album, drop index.json for Cullen integration
  ([`1463c18`](https://github.com/djachenko/justin/commit/1463c189e5bc2c6cd5f8c224924cab4a0e0720f8))


## v0.3.0 (2026-10-06)

### Bug Fixes

- Resolve mypy errors in fix_metafile command
  ([`73df96c`](https://github.com/djachenko/justin/commit/73df96cc839f893aca7202b75179735fadda3635))

### Code Style

- Clean up rich output whitespace, add handle_common stub
  ([`9613a39`](https://github.com/djachenko/justin/commit/9613a397e88a5d356f68c69b5c5be1441a296177))

### Features

- Add fix_metafile output layer (plain + rich)
  ([`c6aaaab`](https://github.com/djachenko/justin/commit/c6aaaab55c83beae0efe2025c1f09f677969ab7d))

### Refactoring

- Migrate fix_metafile_action to Typer command
  ([`2a4e445`](https://github.com/djachenko/justin/commit/2a4e4457537bcc09dcbf539cf06a785a26f07b35))


## v0.2.3 (2026-10-06)

### Bug Fixes

- Raise requires-python to 3.11 to match StrEnum and justin_utils
  ([`4bf00f4`](https://github.com/djachenko/justin/commit/4bf00f48615e701b2b09413b40929d8cce05df25))

- Rename in two passes so sequence never overwrites unprocessed files
  ([`c3516f6`](https://github.com/djachenko/justin/commit/c3516f694922b1a990dd2e1bcbc728e428860455))

### Build System

- Pin ruff to 0.15.x, 0.16 brings new rules
  ([`d9cf0e4`](https://github.com/djachenko/justin/commit/d9cf0e430418c8e1e8972f0da6187abac2800253))

- Require pyvko 0.1.14 with declared runtime dependencies
  ([`86726cb`](https://github.com/djachenko/justin/commit/86726cb378942590c93ff8516e0f546c1c7397d2))

- Require pyvko 0.1.15 that imports on Python < 3.14
  ([`d445cbf`](https://github.com/djachenko/justin/commit/d445cbf9e2fd5a1b00e39e93549edebfae2be98b))

### Chores

- Add DECISIONS.md to repo root
  ([`e73dc26`](https://github.com/djachenko/justin/commit/e73dc2685c99c624d7357575eae50f8b901cd833))

- Remove skills section from CLAUDE.md
  ([`0f8df43`](https://github.com/djachenko/justin/commit/0f8df43fd373818309f748d1104569e218a6e227))

- Remove VK browser decisions from public DECISIONS.md
  ([`c378469`](https://github.com/djachenko/justin/commit/c3784691b2c2cf6e6edea3f63221f26916bb3a59))

### Refactoring

- Switch sequence to justin_utils.exif, drop local exif module
  ([`4c2add2`](https://github.com/djachenko/justin/commit/4c2add22024aa580cec0aceddb0c67ca59234548))


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
