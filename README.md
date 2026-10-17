# Gas Station Turret Remover

A Cyberpunk 2077 mod for the gas station in the Badlands where Marty sells guns. During the main job Life During Wartime, Kang Tao holds the station and sets up two standing turrets in front of it, by the entrance ramps. In the game as it ships, those two turrets are there from the start of the game and stay after the job is done. With this mod they are only there while Life During Wartime is running.

- The turrets appear when the job reaches the downed AV's crash site, before you are sent to the gas station, and are gone again once the job is over. That is when the game already brings in and clears away the rest of Kang Tao's equipment there: the mines, the explosive tanks and the flares.
- They are the game's own turrets, unchanged and in the same places. The job still switches them on for the fight and off afterwards, as before.
- Only the two standing turrets outside are affected. The ceiling turret inside and everything else at the station stay as they are.
- Works with saves from before, during and after the job. If the job is already done, the turrets are gone the next time the area loads.

## Installation

The `archive` folder is laid out from the game root, so it can be copied into the game directory or zipped for a mod manager.

Requires:
- [RED4ext](https://github.com/WopsS/RED4ext)
- [ArchiveXL](https://github.com/psiberx/cp2077-archive-xl)

## How it works

The game switches parts of a location on and off with the story through prefab variants. The gas station has a variant named `q104` for Kang Tao's equipment, which the job switches on and off. The two standing turrets were placed outside that variant, so nothing ever took them away.

The mod changes that without touching the job itself:

- `GasStationTurretRemover.archive.xl` removes the two turrets from the always-on part of their world sectors (`exterior_-29_-67_1_0`, node 842, and `exterior_-29_-68_1_0`, node 251).
- `GasStationTurretRemover.archive` adds a small sector holding the same two turrets, with the same names and settings, inside the station's `q104` variant.

If a game update changes either of those two sectors, ArchiveXL leaves it alone and writes a warning to its log instead of removing the wrong thing. The mod then needs an update.

## Building

The archive is built from the JSON in `source\` with [WolvenKit](https://github.com/WolvenKit/WolvenKit) 9.1's command-line tool and Python 3:

```
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

This converts the JSON to game files, checks that they read back unchanged, packs `archive\pc\mod\GasStationTurretRemover.archive` and writes `dist\GasStationTurretRemover.zip`.

`tools\make_sources.py` regenerates the JSON in `source\` from WolvenKit JSON exports of the two vanilla sectors and `base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock`. It checks the node counts and names first, so a changed game version shows up there.

## Notes

- Built and tested on game version 2.31 with ArchiveXL 1.27.4.

Built it with Claude (the AI).

## License

[MIT](LICENSE)
