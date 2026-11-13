# Gas Station Turret Remover

A Cyberpunk 2077 mod for the gas station in the Badlands where Marty sells guns. During the main job Life During Wartime, Kang Tao holds the station and sets up two standing turrets in front of it, by the entrance ramps. In the game as it ships, those two turrets are there from the start of the game and stay after the job is done. With this mod they are only there while Life During Wartime is running.

- The turrets appear when the job reaches the downed AV's crash site, before you are sent to the gas station, and are gone again once the job is over. That is when the game already brings in and clears away the rest of Kang Tao's equipment there: the mines, the explosive tanks and the flares.
- They are the game's own turrets, unchanged and in the same places. The job still switches them on for the fight and off afterwards, as before.
- Only the two standing turrets outside are affected. The ceiling turret inside and everything else at the station stay as they are.
- Works with saves from before, during and after the job. If the job is already done, the turrets are gone the next time the area loads.

## Installation

The mod comes in two editions. Pick the one that matches your game:

- **Phantom Liberty**: if you have the Phantom Liberty expansion installed.
- **Base game**: if you do not.

Phantom Liberty replaces the game's files for this part of the Badlands with its own copies, in which the turrets sit at different places, so each edition only works with its own setup. Install one of them, not both.

Each edition's folder (`phantom-liberty\`, `base-game\`) holds an `archive` folder laid out from the game root, so it can be copied into the game directory or zipped for a mod manager.

Requires:
- [RED4ext](https://github.com/WopsS/RED4ext)
- [ArchiveXL](https://github.com/psiberx/cp2077-archive-xl)

## How it works

The game switches parts of a location on and off with the story through prefab variants. The gas station has a variant named `q104` for Kang Tao's equipment, which the job switches on and off. The two standing turrets were placed outside that variant, so nothing ever took them away.

The mod changes that without touching the job itself:

- `GasStationTurretRemover.archive.xl` removes the two turrets from the always-on part of their world sectors: in `exterior_-29_-67_1_0` node 845 with Phantom Liberty or 840 without it, and in `exterior_-29_-68_1_0` node 251 with Phantom Liberty or 252 without it.
- `GasStationTurretRemover.archive` adds a small sector holding the same two turrets, with the same names and settings, inside the station's `q104` variant.

ArchiveXL checks the node count of each sector and the type of each node before removing anything, and writes a warning to its log if they do not match. That check cannot catch everything: game version 2.5 moved the turrets to new places in their sectors without changing the counts, and Phantom Liberty's copies of the sectors have the same counts as the base game's, so a game update can still mean the mod needs one too.

## Building

The archives are built from the JSON in `source\` with Python 3, the .NET 10 SDK and [WolvenKit](https://github.com/WolvenKit/WolvenKit). Game version 2.5 changed the format of world sectors, and the released WolvenKit command-line tool (9.1.1) cannot read it yet, so `tools\wkjson` converts between JSON and game files with the WolvenKit 10 libraries (10.0.0-beta.1); the 9.1.1 command-line tool only packs the archives:

```
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

This builds `tools\wkjson` and then, for each edition, converts the JSON in `source\<edition>\` to game files, checks that they read back unchanged, packs `<edition>\archive\pc\mod\GasStationTurretRemover.archive` and writes `dist\GasStationTurretRemover-PhantomLiberty.zip` and `dist\GasStationTurretRemover-BaseGame.zip`.

`tools\make_sources.py <edition> <exports> .` regenerates an edition's JSON in `source\<edition>\` and its `.archive.xl` from JSON exports (`wkjson read`) of the two sectors and `base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock`, taken from `basegame_3_nightcity.archive` for the base game and from `ep1\ep1_1_nightcity.archive` for Phantom Liberty. It checks the node counts, types and names first, so a changed game version shows up there.

## Notes

- Updated for game version 2.5 with ArchiveXL 1.28.8. Version 1.0 was built for game version 2.31 and does not work on 2.5.

Built it with Claude (the AI).

## License

[MIT](LICENSE)
