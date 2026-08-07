from enum import Enum
from logging import exception
from typing import Any, Callable, List, Sequence
import random
import typing
from BaseClasses import Location
from .Item import Item, ItemType, lookup_id_to_name
from .Location import LocationType
from .Region import IReward, RewardType, SMRegion, Z3Region
from .Regions.Zelda.EasternPalace import EasternPalace
from .Regions.Zelda.DesertPalace import DesertPalace
from .Regions.Zelda.TowerOfHera import TowerOfHera
from .Regions.Zelda.PalaceOfDarkness import PalaceOfDarkness
from .Regions.Zelda.SwampPalace import SwampPalace
from .Regions.Zelda.SkullWoods import SkullWoods
from .Regions.Zelda.ThievesTown import ThievesTown
from .Regions.Zelda.IcePalace import IcePalace
from .Regions.Zelda.MiseryMire import MiseryMire
from .Regions.Zelda.TurtleRock import TurtleRock
from .Regions.Zelda.GanonsTower import GanonsTower
from .Regions.SuperMetroid.Brinstar.Kraid import Kraid
from .Regions.SuperMetroid.WreckedShip import WreckedShip
from .Regions.SuperMetroid.Maridia.Inner import Inner
from .Regions.SuperMetroid.NorfairLower.East import East
from .Text.StringTable import StringTable

from .World import World
from .Config import Config, OpenTourian, Goal
from .Text.Texts import Texts
from .Text.Dialog import Dialog

class KeycardPlaque:
    Level1 = 0xe0
    Level2 = 0xe1
    Boss = 0xe2
    Null = 0x00  
    Zero = 0xe3
    One = 0xe4
    Two = 0xe5
    Three = 0xe6
    Four = 0xe7

class KeycardDoors:
    Left = 0xd414
    Right = 0xd41a
    Up = 0xd420
    Down = 0xd426
    BossLeft = 0xc842
    BossRight = 0xc848


class KeycardEvents:
    CrateriaLevel1 = 0x0000
    CrateriaLevel2 = 0x0100
    CrateriaBoss = 0x0200
    BrinstarLevel1 = 0x0300
    BrinstarLevel2 = 0x0400
    BrinstarBoss = 0x0500
    NorfairLevel1 = 0x0600
    NorfairLevel2 = 0x0700
    NorfairBoss = 0x0800
    MaridiaLevel1 = 0x0900
    MaridiaLevel2 = 0x0a00
    MaridiaBoss = 0x0b00
    WreckedShipLevel1 = 0x0c00
    WreckedShipBoss = 0x0d00
    LowerNorfairLevel1 = 0x0e00
    LowerNorfairBoss = 0x0f00

class DropPrize(Enum):
    Heart = 0xD8
    Green = 0xD9
    Blue = 0xDA
    Red = 0xDB
    Bomb1 = 0xDC
    Bomb4 = 0xDD
    Bomb8 = 0xDE
    Magic = 0xDF
    FullMagic = 0xE0
    Arrow5 = 0xE1
    Arrow10 = 0xE2
    Fairy = 0xE3

class Patch:
    Major = 11
    Minor = 3
    Patch = 1
    allWorlds: List[World]
    myWorld: World
    seedGuid: str
    seed: int
    rnd: random.Random
    patches: Sequence[Any]
    stringTable: StringTable
    silversWorldID: int

    def __init__(self, myWorld: World, allWorlds: List[World], seedGuid: str, seed: int, rnd: random.Random, playerNames: List[str], silversWorldID: int):
        self.myWorld = myWorld
        self.allWorlds = allWorlds
        self.seedGuid = seedGuid
        self.seed = seed
        self.rnd = rnd
        self.playerNames = playerNames
        self.playerIDToNames = {id:name for name, id in playerNames.items()}
        self.silversWorldID = silversWorldID

    def Create(self, config: Config):
        self.stringTable = StringTable()
        self.patches = []
        self.title = ""

        self.WriteMedallions()
        self.WriteRewards()
        self.WriteDungeonMusic(config.Keysanity)

        self.WriteDiggingGameRng()

        self.WritePrizeShuffle(self.myWorld.WorldState.DropPrizes)

        self.WriteRemoveEquipmentFromUncle( self.myWorld.GetLocation("Link's Uncle").APLocation.item.item if 
                                            self.myWorld.GetLocation("Link's Uncle").APLocation.item.game == "SMZ3" else
                                            Item(ItemType.Something))

        self.WriteGanonInvicible(config.Goal)
        self.WritePreOpenPyramid(config.Goal)
        self.WriteCrystalsNeeded(self.myWorld.TowerCrystals, self.myWorld.GanonCrystals, config.Goal)
        self.WriteBossesNeeded(self.myWorld.TourianBossTokens)
        self.WriteRngBlock()

        self.WriteSaveAndQuitFromBossRoom()
        self.WriteWorldOnAgahnimDeath()

        self.WriteTexts(config)

        self.WriteSMLocations([loc for region in self.myWorld.Regions for loc in region.Locations if isinstance(region, SMRegion)])
        self.WriteZ3Locations([loc for region in self.myWorld.Regions for loc in region.Locations if isinstance(region, Z3Region)])

        self.WriteStringTable()

        self.WriteSMKeyCardDoors()
        self.WriteZ3KeysanityFlags()

        self.WritePlayerNames()
        self.WriteSeedData()
        self.WriteGameTitle()
        self.WriteCommonFlags()

        return {patch[0]:patch[1] for patch in self.patches}
    
    def WriteMedallions(self):
        from .WorldState import Medallion
        turtleRock = next(region for region in self.myWorld.Regions if isinstance(region, TurtleRock))
        miseryMire = next(region for region in self.myWorld.Regions if isinstance(region, MiseryMire))

        turtleRockAddresses = [0x308023, 0xD020, 0xD0FF, 0xD1DE ]
        miseryMireAddresses = [ 0x308022, 0xCFF2, 0xD0D1, 0xD1B0 ]

        if turtleRock.Medallion == Medallion.Bombos:
            turtleRockValues = [0x00, 0x51, 0x10, 0x00]
        elif turtleRock.Medallion == Medallion.Ether:
            turtleRockValues = [0x01, 0x51, 0x18, 0x00]
        elif turtleRock.Medallion == Medallion.Quake:
            turtleRockValues = [0x02, 0x14, 0xEF, 0xC4]
        else:
            raise exception(f"Tried using {turtleRock.Medallion} in place of Turtle Rock medallion")

        if miseryMire.Medallion == Medallion.Bombos:
            miseryMireValues = [0x00, 0x51, 0x00, 0x00]
        elif miseryMire.Medallion == Medallion.Ether:
            miseryMireValues = [0x01, 0x13, 0x9F, 0xF1]
        elif miseryMire.Medallion == Medallion.Quake:
            miseryMireValues = [0x02, 0x51, 0x08, 0x00]
        else:
            raise exception(f"Tried using {miseryMire.Medallion} in place of Misery Mire medallion")

        self.patches += [(Snes(addr), [value]) for addr, value in zip(turtleRockAddresses, turtleRockValues)]
        self.patches += [(Snes(addr), [value]) for addr, value in zip(miseryMireAddresses, miseryMireValues)]

    def WriteRewards(self):
        crystalsBlue = [ 1, 2, 3, 4, 7 ]
        self.rnd.shuffle(crystalsBlue)
        crystalsRed = [ 5, 6 ]
        self.rnd.shuffle(crystalsRed)
        crystalRewards = crystalsBlue + crystalsRed

        pendantsGreen = [ 1 ]
        pendantsBlueRed = [ 2, 3 ]
        self.rnd.shuffle(pendantsBlueRed)
        pendantRewards = pendantsGreen + pendantsBlueRed

        bossTokens = [ 1, 2, 3, 4 ]

        regions = [region for region in self.myWorld.Regions if isinstance(region, IReward)]
        crystalRegions = [region for region in regions if region.Reward == RewardType.CrystalBlue] +  [region for region in regions if region.Reward == RewardType.CrystalRed]
        pendantRegions = [region for region in regions if region.Reward == RewardType.PendantGreen] +  [region for region in regions if region.Reward == RewardType.PendantNonGreen]
        bossRegions =   [region for region in regions if region.Reward == RewardType.BossTokenKraid] + \
                        [region for region in regions if region.Reward == RewardType.BossTokenPhantoon] + \
                        [region for region in regions if region.Reward == RewardType.BossTokenDraygon] + \
                        [region for region in regions if region.Reward == RewardType.BossTokenRidley]

        self.patches += self.RewardPatches(crystalRegions, crystalRewards, self.CrystalValues)
        self.patches += self.RewardPatches(pendantRegions, pendantRewards, self.PendantValues)
        self.patches += self.RewardPatches(bossRegions, bossTokens, self.BossTokenValues)

    def RewardPatches(self, regions: List[IReward], rewards: List[int], rewardValues: Callable):
        addresses = [self.RewardAddresses(region) for region in regions]
        values = [rewardValues(reward) for reward in rewards]
        associations = zip(addresses, values)
        return [(Snes(i), [b]) for association in associations for i,b in zip(association[0], association[1])]

    def RewardAddresses(self, region: IReward):
        regionType = {
                    EasternPalace : [ 0x2A09D, 0xABEF8, 0xABEF9, 0x308052, 0x30807C, 0x1C6FE, 0x30D100],
                    DesertPalace : [ 0x2A09E, 0xABF1C, 0xABF1D, 0x308053, 0x308078, 0x1C6FF, 0x30D101 ],
                    TowerOfHera : [ 0x2A0A5, 0xABF0A, 0xABF0B, 0x30805A, 0x30807A, 0x1C706, 0x30D102 ],
                    PalaceOfDarkness : [ 0x2A0A1, 0xABF00, 0xABF01, 0x308056, 0x30807D, 0x1C702, 0x30D103 ],
                    SwampPalace : [ 0x2A0A0, 0xABF6C, 0xABF6D, 0x308055, 0x308071, 0x1C701, 0x30D104 ],
                    SkullWoods : [ 0x2A0A3, 0xABF12, 0xABF13, 0x308058, 0x30807B, 0x1C704, 0x30D105 ],
                    ThievesTown : [ 0x2A0A6, 0xABF36, 0xABF37, 0x30805B, 0x308077, 0x1C707, 0x30D106 ],
                    IcePalace : [ 0x2A0A4, 0xABF5A, 0xABF5B, 0x308059, 0x308073, 0x1C705, 0x30D107 ],
                    MiseryMire : [ 0x2A0A2, 0xABF48, 0xABF49, 0x308057, 0x308075, 0x1C703, 0x30D108 ],
                    TurtleRock : [ 0x2A0A7, 0xABF24, 0xABF25, 0x30805C, 0x308079, 0x1C708, 0x30D109 ],
                    Kraid : [ 0xF26002, 0xF26004, 0xF26005, 0xF26000, 0xF26006, 0xF26007, 0x82FD36 ],
                    WreckedShip : [ 0xF2600A, 0xF2600C, 0xF2600D, 0xF26008, 0xF2600E, 0xF2600F, 0x82FE26 ],
                    Inner : [ 0xF26012, 0xF26014, 0xF26015, 0xF26010, 0xF26016, 0xF26017, 0x82FE76 ],
                    East : [ 0xF2601A, 0xF2601C, 0xF2601D, 0xF26018, 0xF2601E, 0xF2601F, 0x82FDD6 ]
                    }

        result = regionType.get(type(region), None)
        if result is None:
            raise exception(f"Region {region} should not be a dungeon reward region")
        else:
            return result

    def CrystalValues(self, crystal: int):
        crystalMap = {
                1 : [ 0x02, 0x34, 0x64, 0x40, 0x7F, 0x06, 0x10 ],
                2 : [ 0x10, 0x34, 0x64, 0x40, 0x79, 0x06, 0x10 ],
                3 : [ 0x40, 0x34, 0x64, 0x40, 0x6C, 0x06, 0x10 ],
                4 : [ 0x20, 0x34, 0x64, 0x40, 0x6D, 0x06, 0x10 ],
                5 : [ 0x04, 0x32, 0x64, 0x40, 0x6E, 0x06, 0x11 ],
                6 : [ 0x01, 0x32, 0x64, 0x40, 0x6F, 0x06, 0x11 ],
                7 : [ 0x08, 0x34, 0x64, 0x40, 0x7C, 0x06, 0x10 ],
                }
        result = crystalMap.get(crystal, None)
        if result is None:
            raise exception(f"Tried using {crystal} as a crystal number")
        else:
            return result

    def PendantValues(self, pendant: int):
        pendantMap = {
                        1 : [ 0x04, 0x38, 0x62, 0x00, 0x69, 0x01, 0x12 ],
                        2 : [ 0x01, 0x32, 0x60, 0x00, 0x69, 0x03, 0x14 ],
                        3 : [ 0x02, 0x34, 0x60, 0x00, 0x69, 0x02, 0x13 ]
                    }
        result = pendantMap.get(pendant, None)
        if result is None:
            raise exception(f"Tried using {pendant} as a pendant number")
        else:
            return result

    def BossTokenValues(self, token: int):
        tokenMap = {
                        1 : [ 0x01, 0x38, 0x40, 0x80, 0x69, 0x80, 0x15 ],
                        2 : [ 0x02, 0x34, 0x42, 0x80, 0x69, 0x81, 0x16 ],
                        3 : [ 0x04, 0x34, 0x44, 0x80, 0x69, 0x82, 0x17 ],
                        4 : [ 0x08, 0x32, 0x46, 0x80, 0x69, 0x83, 0x18 ]
                    }
        result = tokenMap.get(token, None)
        if result is None:
            raise exception(f"Tried using {token} as a boss token number")
        else:
            return result
    
    def WriteSMLocations(self, locations: List[Location]):
        def GetSMItemPLM(location:Location):
            itemMap = {
                    ItemType.ETank : 0xEED7,
                    ItemType.Missile : 0xEEDB,
                    ItemType.Super : 0xEEDF,
                    ItemType.PowerBomb : 0xEEE3,
                    ItemType.Bombs : 0xEEE7,
                    ItemType.Charge : 0xEEEB,
                    ItemType.Ice : 0xEEEF,
                    ItemType.HiJump : 0xEEF3,
                    ItemType.SpeedBooster : 0xEEF7,
                    ItemType.Wave : 0xEEFB,
                    ItemType.Spazer : 0xEEFF,
                    ItemType.SpringBall : 0xEF03,
                    ItemType.Varia : 0xEF07,
                    ItemType.Plasma : 0xEF13,
                    ItemType.Grapple : 0xEF17,
                    ItemType.Morph : 0xEF23,
                    ItemType.ReserveTank : 0xEF27,
                    ItemType.Gravity : 0xEF0B,
                    ItemType.XRay : 0xEF0F,
                    ItemType.SpaceJump : 0xEF1B,
                    ItemType.ScrewAttack : 0xEF1F
                    }
            plmId = 0xEFE0 if self.myWorld.Config.Multiworld else \
                                itemMap.get(location.APLocation.item.item.Type, 0xEFE0)
            if (plmId == 0xEFE0):
                plmId += 4 if location.Type == LocationType.Chozo else 8 if location.Type == LocationType.Hidden else 0
            else:
                plmId += 0x54 if location.Type == LocationType.Chozo else 0xA8 if location.Type == LocationType.Hidden else 0
            return plmId

        for location in locations:
            if (self.myWorld.Config.Multiworld):
                self.patches.append((Snes(location.Address), getWordArray(GetSMItemPLM(location))))
                self.patches.append(self.ItemTablePatch(location, self.GetZ3ItemId(location)))
            else:
                plmId = GetSMItemPLM(location)
                self.patches.append((Snes(location.Address), getWordArray(plmId)))
                if (plmId >= 0xEFE0):
                    self.patches.append((Snes(location.Address + 5), [self.GetZ3ItemId(location)]))

    def WriteZ3Locations(self, locations: List[Location]):
        for location in locations:
            if (location.Type == LocationType.HeraStandingKey):
                self.patches.append((Snes(0x9E3BB), [0xEB]))
            elif (location.Type in [LocationType.Pedestal, LocationType.Ether, LocationType.Bombos]):
                text = Texts.ItemTextbox(location.APLocation.item.item if location.APLocation.item.game == "SMZ3" else Item(ItemType.Something))
                if (location.Type == LocationType.Pedestal):
                    self.stringTable.SetPedestalText(text)
                elif (location.Type == LocationType.Ether):
                    self.stringTable.SetEtherText(text)
                elif (location.Type == LocationType.Bombos):
                    self.stringTable.SetBombosText(text)

            if (self.myWorld.Config.Multiworld):
                self.patches.append((Snes(location.Address), [(location.Id - 256)]))
                self.patches.append(self.ItemTablePatch(location, self.GetZ3ItemId(location)))
            else:
                self.patches.append((Snes(location.Address), [self.GetZ3ItemId(location)]))

    def GetZ3ItemId(self, location: Location):
        if (location.APLocation.item.game == "SMZ3"):
            item = location.APLocation.item.item
            itemDungeon = None
            if item.IsKey():
                itemDungeon = ItemType.Key
            elif item.IsBigKey(): 
                itemDungeon = ItemType.BigKey
            elif item.IsMap():
                itemDungeon = ItemType.Map
            elif item.IsCompass():
                itemDungeon = ItemType.Compass

            value = item.Type if location.Type == LocationType.NotInDungeon or \
                not (item.IsDungeonItem() and location.Region.IsRegionItem(item) and item.World == self.myWorld) else itemDungeon
            
            return value.value
        elif (location.APLocation.item.game == "A Link to the Past"):
            if location.APLocation.item.code + 84000 in lookup_id_to_name:
                ALTTPBottleContentCodeToSMZ3ItemCode = {
                    ItemType.RedContent.value: ItemType.BottleWithRedPotion.value,
                    ItemType.GreenContent.value: ItemType.BottleWithGreenPotion.value,
                    ItemType.BlueContent.value: ItemType.BottleWithBluePotion.value,
                    ItemType.BeeContent.value: ItemType.BottleWithBee.value,
                }
                return ALTTPBottleContentCodeToSMZ3ItemCode.get(location.APLocation.item.code, location.APLocation.item.code)
            else:
                return ItemType.Something.value
        elif (location.APLocation.item.game == "Super Metroid"):
            SMNameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile": ItemType.Missile, "Super Missile": ItemType.Super,
                "Power Bomb": ItemType.PowerBomb, "Bomb": ItemType.Bombs, "Charge Beam": ItemType.Charge,
                "Ice Beam": ItemType.Ice, "Hi-Jump Boots": ItemType.HiJump, "Speed Booster": ItemType.SpeedBooster,
                "Wave Beam": ItemType.Wave, "Spazer": ItemType.Spazer, "Spring Ball": ItemType.SpringBall,
                "Varia Suit": ItemType.Varia, "Plasma Beam": ItemType.Plasma, "Grappling Beam": ItemType.Grapple,
                "Morph Ball": ItemType.Morph, "Reserve Tank": ItemType.ReserveTank, "Gravity Suit": ItemType.Gravity,
                "X-Ray Scope": ItemType.XRay, "Space Jump": ItemType.SpaceJump, "Screw Attack": ItemType.ScrewAttack,
                "Nothing": ItemType.Something, "No Energy": ItemType.Something, "Generic": ItemType.Something
            }
            return SMNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Metroid: Zero Mission"):
            MZMNameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile Tank": ItemType.Missile, "Super Missile Tank": ItemType.Super,
                "Power Bomb Tank": ItemType.PowerBomb, "Bomb": ItemType.Bombs, "Charge Beam": ItemType.Charge,
                "Ice Beam": ItemType.Ice, "Hi-Jump": ItemType.HiJump, "Speed Booster": ItemType.SpeedBooster,
                "Wave Beam": ItemType.Wave, "Long Beam": ItemType.Spazer,
                "Varia Suit": ItemType.Varia, "Plasma Beam": ItemType.Plasma, "Power Grip": ItemType.Grapple,
                "Morph Ball": ItemType.Morph, "Gravity Suit": ItemType.Gravity,
                "Space Jump": ItemType.SpaceJump, "Screw Attack": ItemType.ScrewAttack,
                "Nothing": ItemType.Something
            }
            return MZMNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Metroid Prime"):
            MP1NameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile Expansion": ItemType.Missile, "Missile Launcher": ItemType.Missile, "Super Missile": ItemType.Super,
                "Power Bomb Expansion": ItemType.PowerBomb, "Power Bomb (Main)": ItemType.PowerBomb, "Morph Ball Bomb": ItemType.Bombs,
                "Charge Beam": ItemType.Charge, "Progressive Power Beam": ItemType.Charge, "Charge Beam (Power)": ItemType.Charge, "Charge Beam (Ice)": ItemType.Charge, "Charge Beam (Plasma)": ItemType.Charge, "Charge Beam (Wave)": ItemType.Charge, 
                "Ice Beam": ItemType.Ice, "Progressive Ice Beam": ItemType.Ice, "Ice Spreader": ItemType.Ice,
                "Plasma Beam": ItemType.Plasma, "Progressive Plasma Beam": ItemType.Plasma, "Flamethrower": ItemType.Plasma,
                "Wave Beam": ItemType.Wave, "Progressive Wave Beam": ItemType.Wave, "Wavebuster": ItemType.Wave,
                "Varia Suit": ItemType.Varia, "Boost Ball": ItemType.SpeedBooster, "Grappling Beam": ItemType.Grapple,
                "Morph Ball": ItemType.Morph, "Gravity Suit": ItemType.Gravity,
                "X-Ray Visor": ItemType.XRay, "Scan Visor": ItemType.XRay, "Thermal Visor": ItemType.XRay, 
                "Space Jump Boots": ItemType.SpaceJump
            }
            return MP1NameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Super Metroid Map Rando"):
            SMMRNameToSMZ3Code = {
                "ETank": ItemType.ETank, "Missile": ItemType.Missile, "Super": ItemType.Super,
                "PowerBomb": ItemType.PowerBomb, "Bombs": ItemType.Bombs, "Charge": ItemType.Charge,
                "Ice": ItemType.Ice, "HiJump": ItemType.HiJump, "SpeedBooster": ItemType.SpeedBooster,
                "Wave": ItemType.Wave, "Spazer": ItemType.Spazer, "SpringBall": ItemType.SpringBall,
                "Varia Suit": ItemType.Varia, "Plasma": ItemType.Plasma, "Grapple": ItemType.Grapple,
                "Morph": ItemType.Morph, "ReserveTank": ItemType.ReserveTank, "Gravity": ItemType.Gravity,
                "XRayScope": ItemType.XRay, "SpaceJump": ItemType.SpaceJump, "ScrewAttack": ItemType.ScrewAttack
            }
            return SMMRNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Subversion"):
            SVNameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile": ItemType.Missile, "Super Missile": ItemType.Super,
                "Power Bomb": ItemType.PowerBomb, "Bombs": ItemType.Bombs, "Charge Beam": ItemType.Charge,
                "Ice Beam": ItemType.Ice, "HiJump": ItemType.HiJump, "Speed Booster": ItemType.SpeedBooster, "Gravity Boots": ItemType.HiJump,
                "Wave Beam": ItemType.Wave, "Spazer": ItemType.Spazer, "Speed Ball": ItemType.SpringBall,
                "Varia Suit": ItemType.Varia, "Plasma Beam": ItemType.Plasma, "Grappling Beam": ItemType.Grapple,
                "Morph Ball": ItemType.Morph, "Refuel Tank": ItemType.ReserveTank, "Aqua Suit": ItemType.Gravity,
                "X-Ray Scope": ItemType.XRay, "Space Jump": ItemType.SpaceJump, "Screw Attack": ItemType.ScrewAttack,
                "Hypercharge": ItemType.Charge, "Small Ammo": ItemType.ArrowUpgrade5, "Large Ammo": ItemType.ArrowUpgrade10,
                "Accel Charge": ItemType.Charge, "Space Jump Boost": ItemType.SpaceJump
            }
            return SVNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Super Junkoid"):
            SJNameToSMZ3Code = {
                "Heart": ItemType.ETank, "Magic Bolt": ItemType.Missile, "Baseball": ItemType.Super,
                "Sparksuit": ItemType.PowerBomb, "Rat Burst": ItemType.Bombs, "Gem Of Death": ItemType.Charge,
                "Gem Of Ice": ItemType.Ice, "Feather": ItemType.HiJump, "Rat Dasher": ItemType.SpeedBooster,
                "Gem Of Blood": ItemType.Wave, "Wallkicks": ItemType.HiJump, "Dreamer's Crown": ItemType.SpeedBooster,
                "Purple Locket": ItemType.Varia, "Gem Of Storms": ItemType.Plasma, "Magic Soap": ItemType.Missile,
                "Rat Cloak": ItemType.Morph, "Lucky Frog": ItemType.ReserveTank, "Sanguine Fin": ItemType.Gravity,
                "Magic Broom": ItemType.SpaceJump, "Wave Bangle": ItemType.ScrewAttack
            }
            return SJNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "AM2R"):
            AM2RNameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile": ItemType.Missile, "Super Missile": ItemType.Super,
                "Power Bomb": ItemType.PowerBomb, "Bombs": ItemType.Bombs, "Charge Beam": ItemType.Charge,
                "Ice Beam": ItemType.Ice, "Hi Jump": ItemType.HiJump, "Speed Booster": ItemType.SpeedBooster,
                "Wave Beam": ItemType.Wave, "Spazer": ItemType.Spazer, "Spring Ball": ItemType.SpringBall,
                "Varia Suit": ItemType.Varia, "Plasma Beam": ItemType.Plasma,
                "Morph Ball": ItemType.Morph, "Gravity Suit": ItemType.Gravity,
                "Space Jump": ItemType.SpaceJump, "Screw Attack": ItemType.ScrewAttack
            }
            return AM2RNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Metroid Fusion"):
            FusionNameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile Data": ItemType.Missile, "Missile Tank": ItemType.Missile, "Super Missile": ItemType.Super,
                "Power Bomb Data": ItemType.PowerBomb, "Power Bomb Tank": ItemType.PowerBomb, "Bomb Data": ItemType.Bombs, "Charge Beam": ItemType.Charge,
                "Ice Beam": ItemType.Ice, "Hi-Jump": ItemType.HiJump, "Speed Booster": ItemType.SpeedBooster,
                "Wave Beam": ItemType.Wave, "Wide Beam": ItemType.Spazer,
                "Varia Suit": ItemType.Varia, "Plasma Beam": ItemType.Plasma,
                "Morph Ball": ItemType.Morph, "Gravity Suit": ItemType.Gravity,
                "Space Jump": ItemType.SpaceJump, "Screw Attack": ItemType.ScrewAttack,
                "Level 1 Keycard": ItemType.BigKey, "Level 2 Keycard": ItemType.BigKey, "Level 3 Keycard": ItemType.BigKey, "Level 4 Keycard": ItemType.BigKey
            }
            return FusionNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Metroid: Samus Returns"):
            MSRNameToSMZ3Code = {
                "Energy Tank": ItemType.ETank, "Missile Launcher": ItemType.Missile, "Super Missile": ItemType.Super,
                "Power Bomb": ItemType.PowerBomb, "Bomb": ItemType.Bombs, "Charge Beam": ItemType.Charge,
                "Ice Beam": ItemType.Ice, "High Jump Boots": ItemType.HiJump, "Speed Booster": ItemType.SpeedBooster,
                "Wave Beam": ItemType.Wave, "Spazer Beam": ItemType.Spazer, "Spring Ball": ItemType.SpringBall,
                "Varia Suit": ItemType.Varia, "Plasma Beam": ItemType.Plasma,
                "Morph Ball": ItemType.Morph, "Gravity Suit": ItemType.Gravity,
                "Space Jump": ItemType.SpaceJump, "Screw Attack": ItemType.ScrewAttack,
                "Grapple Beam": ItemType.Grapple, "Missile Tank": ItemType.Missile, "Super Missile Tank": ItemType.Super, "Power Bomb Tank": ItemType.PowerBomb,
                "Energy Reserve Tank": ItemType.ReserveTank, "Aeion Reserve Tank": ItemType.ReserveTank, "Missile Reserve Tank": ItemType.ReserveTank
            }
            return MSRNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Metroid Dread"):
            DreadNameToSMZ3Code = {
                "Bomb": ItemType.Bombs, "Charge Beam": ItemType.Charge, "Cross Bomb": ItemType.Bombs,
                "Diffusion Beam": ItemType.Charge, "Energy Part": ItemType.ETank, "Energy Tank": ItemType.ETank,
                "Grapple Beam": ItemType.Grapple, "Gravity Suit": ItemType.Gravity, "Super Missile": ItemType.Super,
                "Morph Ball": ItemType.Morph, "Missile Tank": ItemType.Missile, "Missile+ Tank": ItemType.Missile,
                "Plasma Beam": ItemType.Plasma, "Power Bomb": ItemType.PowerBomb, "Power Bomb Tank": ItemType.PowerBomb,
                "Screw Attack": ItemType.ScrewAttack, "Space Jump": ItemType.SpaceJump, "Speed Booster": ItemType.SpeedBooster,
                "Speed Booster Upgrade": ItemType.SpeedBooster, "Spin Boost": ItemType.SpaceJump, "Varia Suit": ItemType.Varia,
                "Wave Beam": ItemType.Wave, "Wide Beam": ItemType.Spazer,
                "Progressive Charge Beam": ItemType.Charge, "Progressive Bomb": ItemType.Bombs, "Progressive Spin": ItemType.SpaceJump,
                "Progressive Beam": ItemType.Charge, "Progressive Suit": ItemType.Varia
            }
            return DreadNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "The Legend of Zelda"):
            Z1NameToSMZ3Code = {
                "Arrow": ItemType.Arrow, "Silver Arrow": ItemType.SilverArrows,
                "Blue Ring": ItemType.ProgressiveTunic, "Red Ring": ItemType.ProgressiveTunic,
                "Bomb": ItemType.BombUpgrade10, "Book of Magic": ItemType.Book, "Boomerang": ItemType.BlueBoomerang,
                "Bow": ItemType.Bow, "Candle": ItemType.Lamp, "Five Rupees": ItemType.FiveRupees, "Heart Container": ItemType.HeartContainer,
                "Magical Boomerang": ItemType.RedBoomerang, "Magical Key": ItemType.BigKey, "Magical Rod": ItemType.Firerod,
                "Magical Shield": ItemType.ProgressiveShield, "Magical Sword": ItemType.ProgressiveSword, "Power Bracelet": ItemType.ProgressiveGlove,
                "Recorder": ItemType.Flute, "Red Candle": ItemType.Lamp, "Sword": ItemType.ProgressiveSword, "White Sword": ItemType.ProgressiveSword
            }
            return Z1NameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "The Minish Cap"):
            MinishNameToSMZ3Code = {
                "Smith's Sword": ItemType.ProgressiveSword, "White Sword": ItemType.ProgressiveSword, "White Sword (Two Elements)": ItemType.ProgressiveSword,
                "White Sword (Three Elements)": ItemType.ProgressiveSword, "Four Sword": ItemType.ProgressiveSword, "Bomb": ItemType.BombUpgrade10,
                "Remote Bomb": ItemType.BombUpgrade10, "Bow": ItemType.Bow, "Light Arrow": ItemType.SilverArrows, "Boomerang": ItemType.BlueBoomerang,
                "Magic Boomerang": ItemType.RedBoomerang, "Shield": ItemType.ProgressiveShield, "Mirror Shield": ItemType.ProgressiveShield,
                "Lantern": ItemType.Lamp, "Pegasus Boots": ItemType.Boots, "Fire Rod": ItemType.Firerod, "Ocarina": ItemType.Flute,
                "Bottle (Null)": ItemType.Bottle, "Bottle (Empty)": ItemType.Bottle, "Bottle (Lon Lon Butter)": ItemType.Bottle,
                "Bottle (Lon Lon Milk)": ItemType.Bottle, "Bottle (Lon Lon Milk (1/2))": ItemType.Bottle, "Bottle (Red Potion)": ItemType.Bottle,
                "Bottle (Blue Potion)": ItemType.Bottle, "Bottle (Water)": ItemType.Bottle, "Bottle (Mineral Water)": ItemType.Bottle,
                "Bottle (Bottled Fairy)": ItemType.Bottle, "Bottle (Red Picolyte)": ItemType.Bottle, "Bottle (Orange Picolyte)": ItemType.Bottle,
                "Bottle (Yellow Picolyte)": ItemType.Bottle, "Bottle (Green Picolyte)": ItemType.Bottle, "Bottle (Blue Picolyte)": ItemType.Bottle,
                "Bottle (White Picolyte)": ItemType.Bottle, "Bottle (Nayru Charm)": ItemType.Bottle, "Bottle (Farore Charm)": ItemType.Bottle,
                "Bottle (Dins Charm)": ItemType.Bottle,
                "Smith Sword (Quest)": ItemType.ProgressiveSword, "Broken Picori Blade": ItemType.ProgressiveSword, "LonLon Key": ItemType.Key,
                "Wakeup Mushroom": ItemType.Mushroom, "Red Book (Hyrulian Bestiary)": ItemType.Book, "Green Book (Picori Legend)": ItemType.Book,
                "Blue Book (History of Masks)": ItemType.Book, "Graveyard Key": ItemType.Key, "Power Bracelets": ItemType.ProgressiveGlove,
                "Flippers": ItemType.Flippers, "Hyrule Map": ItemType.Map, "1 Rupee": ItemType.OneRupee, "5 Rupees": ItemType.FiveRupees,
                "20 Rupees": ItemType.TwentyRupees, "50 Rupees": ItemType.FiftyRupees, "100 Rupees": ItemType.OneHundredRupees,
                "200 Rupees": ItemType.OneHundredRupees, "Heart Container": ItemType.HeartContainer, "Piece of Heart": ItemType.HeartPiece,
                "5 Bomb Refill": ItemType.ThreeBombs, "10 Bomb Refill": ItemType.ThreeBombs, "30 Bomb Refill": ItemType.ThreeBombs,
                "5 Arrow Refill": ItemType.TenArrows, "10 Arrow Refill": ItemType.TenArrows, "30 Arrow Refill": ItemType.TenArrows,
                "Progressive Sword": ItemType.ProgressiveSword, "Progressive Bow": ItemType.Bow, "Progressive Boomerang": ItemType.RedBoomerang,
                "Progressive Shield": ItemType.ProgressiveShield,
                "Dungeon Map (DWS)": ItemType.Map, "Dungeon Map (CoF)": ItemType.Map, "Dungeon Map (FoW)": ItemType.Map,
                "Dungeon Map (ToD)": ItemType.Map, "Dungeon Map (PoW)": ItemType.Map, "Dungeon Map (DHC)": ItemType.Map,
                "Big Key (DWS)": ItemType.BigKey, "Big Key (CoF)": ItemType.BigKey, "Big Key (FoW)": ItemType.BigKey,
                "Big Key (ToD)": ItemType.BigKey, "Big Key (PoW)": ItemType.BigKey, "Big Key (DHC)": ItemType.BigKey,
                "Dungeon Compass (DWS)": ItemType.Compass, "Dungeon Compass (CoF)": ItemType.Compass, "Dungeon Compass (FoW)": ItemType.Compass,
                "Dungeon Compass (ToD)": ItemType.Compass, "Dungeon Compass (PoW)": ItemType.Compass, "Dungeon Compass (DHC)": ItemType.Compass,
                "Small Key (DWS)": ItemType.Key, "Small Key (CoF)": ItemType.Key, "Small Key FoW)": ItemType.Key,
                "Small Key (ToD)": ItemType.Key, "Small Key (PoW)": ItemType.Key, "Small Key (DHC)": ItemType.Key, "Small Key (RC)": ItemType.Key,
            }
            return MinishNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Five Nights at Fuckboy's"):
            FNaFbNameToSMZ3Code = {
                "Varia Suit": ItemType.Varia, "Moon Pearl": ItemType.MoonPearl, "Hylian Shield": ItemType.ProgressiveShield
            }
            return FNaFbNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Twilight Princess"):
            TPNameToSMZ3Code = {
                "Green Rupee": ItemType.OneRupee, "Blue Rupee": ItemType.FiveRupees, "Yellow Rupee": ItemType.FiveRupees,
                "Red Rupee": ItemType.TwentyRupees, "Purple Rupee": ItemType.FiftyRupees, "Orange Rupee": ItemType.OneHundredRupees,
                "Silver Rupee": ItemType.ThreeHundredRupees, "Links Purple Rupee": ItemType.FiftyRupees,
                "Bombs (5)": ItemType.ThreeBombs, "Bombs (10)": ItemType.ThreeBombs, "Bombs (20)": ItemType.ThreeBombs, "Bombs (20)": ItemType.ThreeBombs,
                "Water Bombs (3)": ItemType.ThreeBombs, "Water Bombs (5)": ItemType.ThreeBombs, "Water Bombs (10)": ItemType.ThreeBombs, "Water Bombs (15)": ItemType.ThreeBombs,
                "Bomblings (3)": ItemType.ThreeBombs, "Bomblings (5)": ItemType.ThreeBombs, "Bomblings (10)": ItemType.ThreeBombs,
                "Piece of Heart": ItemType.HeartPiece, "Heart Container": ItemType.HeartContainer,
                "Progressive Master Sword": ItemType.ProgressiveSword, "Ordon Shield": ItemType.ProgressiveShield, "Hylian Shield": ItemType.ProgressiveShield,
                "Magic Armor": ItemType.ProgressiveTunic, "Zora Armor": ItemType.ProgressiveTunic, "Gale Boomerang": ItemType.RedBoomerang,
                "Progressive Hero's Bow": ItemType.Bow, "Progressive Clawshot": ItemType.Hookshot, "Lantern": ItemType.Lamp,
                "Bomb Bag": ItemType.BombUpgrade10, "Progressive Bottle": ItemType.Bottle,
                "Forest Temple Small Key": ItemType.Key, "Goron Mines Small Key": ItemType.Key, "Lakebed Temple Small Key": ItemType.Key,
                "Arbiters Grounds Small Key": ItemType.Key, "Snowpeak Ruins Small Key": ItemType.Key, "Temple of Time Small Key": ItemType.Key,
                "City in The Sky Small Key": ItemType.Key, "Palace of Twilight Small Key": ItemType.Key, "Hyrule Castle Small Key": ItemType.Key,
                "Gate Keys": ItemType.Key, "Gerudo Desert Bulblin Camp Key": ItemType.Key,
                "Forest Temple Big Key": ItemType.BigKey, "Lakebed Temple Big Key": ItemType.BigKey, "Goron Mines Key Shard": ItemType.BigKey,
                "Arbiters Grounds Big Key": ItemType.BigKey, "Bedroom Key": ItemType.BigKey, "Temple of Time Big Key": ItemType.BigKey,
                "City in The Sky Big Key": ItemType.BigKey, "Palace of Twilight Big Key": ItemType.BigKey, "Hyrule Castle Big Key": ItemType.BigKey,
                "Forest Temple Compass": ItemType.Compass, "Goron Mines Compass": ItemType.Compass, "Lakebed Temple Compass": ItemType.Compass,
                "Arbiters Grounds Compass": ItemType.Compass, "Snowpeak Ruins Compass": ItemType.Compass, "Temple of Time Compass": ItemType.Compass,
                "City in The Sky Compass": ItemType.Compass, "Palace of Twilight Compass": ItemType.Compass, "Hyrule Castle Compass": ItemType.Compass,
                "Forest Temple Map": ItemType.Map, "Goron Mines Map": ItemType.Map, "Lakebed Temple Map": ItemType.Map, "Arbiters Grounds Map": ItemType.Map,
                "Snowpeak Ruins Map": ItemType.Map, "Temple of Time Map": ItemType.Map, "City in The Sky Map": ItemType.Map, "Palace of Twilight Map": ItemType.Map,
                "Hyrule Castle Map": ItemType.Map, "Progressive Sky Book": ItemType.Book, "Giant Bomb Bag": ItemType.BombUpgrade10
            }
            return TPNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "The Wind Waker"):
            TWWNameToSMZ3Code = {
                "Boomerang": ItemType.RedBoomerang, "Magic Armor": ItemType.ProgressiveTunic, "Bombs": ItemType.BombUpgrade10,
                "Hookshot": ItemType.Hookshot, "Skull Hammer": ItemType.Hammer, "Power Bracelets": ItemType.ProgressiveGlove,
                "Progressive Sword": ItemType.ProgressiveSword, "Progressive Shield": ItemType.ProgressiveShield, "Progressive Bow": ItemType.Bow,
                "Progressive Magic Meter": ItemType.HalfMagic, "Quiver Capacity Upgrade": ItemType.ArrowUpgrade10, "Bomb Bag Capacity Upgrade": ItemType.BombUpgrade10,
                "Empty Bottle": ItemType.Bottle, "Green Rupee": ItemType.OneRupee, "Blue Rupee": ItemType.FiveRupees, "Yellow Rupee": ItemType.FiveRupees,
                "Red Rupee": ItemType.TwentyRupees, "Purple Rupee": ItemType.FiftyRupees, "Orange Rupee": ItemType.OneHundredRupees, "Silver Rupee": ItemType.ThreeHundredRupees,
                "Rainbow Rupee": ItemType.ThreeHundredRupees, "Piece of Heart": ItemType.HeartPiece, "Heart Container": ItemType.HeartContainer,
                "DRC Big Key": ItemType.BigKey, "FW Big Key": ItemType.BigKey, "TotG Big Key": ItemType.BigKey, "ET Big Key": ItemType.BigKey, "WT Big Key": ItemType.BigKey,
                "DRC Small Key": ItemType.Key, "FW Small Key": ItemType.Key, "TotG Small Key": ItemType.Key, "ET Small Key": ItemType.Key, "WT Small Key": ItemType.Key,
                "DRC Dungeon Map": ItemType.Map, "FW Dungeon Map": ItemType.Map, "TotG Dungeon Map": ItemType.Map, "FF Dungeon Map": ItemType.Map, "ET Dungeon Map": ItemType.Map, "WT Dungeon Map": ItemType.Map,
                "DRC Compass": ItemType.Compass, "FW Compass": ItemType.Compass, "TotG Compass": ItemType.Compass, "FF Compass": ItemType.Compass, "ET Compass": ItemType.Compass, "WT Compass": ItemType.Compass

            }
            return TWWNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Links Awakening DX" or "Links Awakening DX Beta"):
            LADXNameToSMZ3Code = {
                "Progressive Power Bracelet": ItemType.ProgressiveGlove, "Progressive Shield": ItemType.ProgressiveShield, "Bow": ItemType.Bow,
                "Hookshot": ItemType.Hookshot, "Magic Rod": ItemType.Firerod, "Pegasus Boots": ItemType.Boots, "Ocarina": ItemType.Flute,
                "Shovel": ItemType.Shovel, "Magic Powder": ItemType.Powder, "Bomb": ItemType.BombUpgrade10,
                "Progressive Sword": ItemType.ProgressiveSword, "Flippers": ItemType.Flippers,
                "Tail Key": ItemType.BigKey, "Angler Key": ItemType.BigKey, "Face Key": ItemType.BigKey, "Bird Key": ItemType.BigKey, "Slime Key": ItemType.BigKey,
                "20 Rupees": ItemType.TwentyRupees, "50 Rupees": ItemType.FiftyRupees, "100 Rupees": ItemType.OneHundredRupees,
                "200 Rupees": ItemType.ThreeHundredRupees, "500 Rupees": ItemType.ThreeHundredRupees,
                "Boomerang": ItemType.RedBoomerang, "Heart Piece": ItemType.HeartPiece, "10 Arrows": ItemType.TenArrows,
                "Single Arrow": ItemType.Arrow, "Max Powder Upgrade": ItemType.Powder, "Max Bombs Upgrade": ItemType.BombUpgrade10,
                "Max Arrows Upgrade": ItemType.ArrowUpgrade10, "Red Tunic": ItemType.ProgressiveTunic, "Blue Tunic":ItemType.ProgressiveTunic,
                "Heart Container": ItemType.HeartContainer, "Bad Heart Container": ItemType.HeartContainer, "Toadstool": ItemType.Mushroom,
                "Key": ItemType.Key,
                "Small Key (Tail Cave)": ItemType.Key, "Small Key (Bottle Grotto)": ItemType.Key, "Small Key (Key Cavern)": ItemType.Key,
                "Small Key (Angler's Tunnel)": ItemType.Key, "Small Key (Catfish's Maw)": ItemType.Key, "Small Key (Face Shrine)": ItemType.Key,
                "Small Key (Eagle's Tower)": ItemType.Key, "Small Key (Turtle Rock)": ItemType.KeyTR, "Small Key (Color Dungeon)": ItemType.Key,
                "Nightmare Key": ItemType.BigKey,
                "Nightmare Key (Tail Cave)": ItemType.BigKey, "Nightmare Key (Bottle Grotto)": ItemType.BigKey, "Nightmare Key (Key Cavern)": ItemType.BigKey,
                "Nightmare Key (Angler's Tunnel)": ItemType.BigKey, "Nightmare Key (Catfish's Maw)": ItemType.BigKey, "Nightmare Key (Face Shrine)": ItemType.BigKey,
                "Nightmare Key (Eagle's Tower)": ItemType.BigKey, "Nightmare Key (Turtle Rock)": ItemType.BigKeyTR, "Nightmare Key (Color Dungeon)": ItemType.BigKey,
                "Map": ItemType.Map,
                "Dungeon Map (Tail Cave)": ItemType.Map, "Dungeon Map (Bottle Grotto)": ItemType.Map, "Dungeon Map (Key Cavern)": ItemType.Map,
                "Dungeon Map (Angler's Tunnel)": ItemType.Map, "Dungeon Map (Catfish's Maw)": ItemType.Map, "Dungeon Map (Face Shrine)": ItemType.Map,
                "Dungeon Map (Eagle's Tower)": ItemType.Map, "Dungeon Map (Turtle Rock)": ItemType.MapTR, "Dungeon Map (Color Dungeon)": ItemType.Map,
                "Compass": ItemType.Compass,
                "Compass (Tail Cave)": ItemType.Compass, "Compass (Bottle Grotto)": ItemType.Compass, "Compass (Key Cavern)": ItemType.Compass,
                "Compass (Angler's Tunnel)": ItemType.Compass, "Compass (Catfish's Maw)": ItemType.Compass, "Compass (Face Shrine)": ItemType.Compass,
                "Compass (Eagle's Tower)": ItemType.Compass, "Compass (Turtle Rock)": ItemType.CompassTR, "Compass (Color Dungeon)": ItemType.Compass
            }
            return LADXNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Majora's Mask Recompiled"):
            MMRNameToSMZ3Code = {
                "Progressive Magic": ItemType.HalfMagic, "Bomber's Notebook": ItemType.Book, "Ocarina of Time": ItemType.Flute,
                "Heart Container": ItemType.HeartContainer, "Heart Piece": ItemType.HeartPiece, "Bottle": ItemType.Bottle,
                "Bottle of Milk": ItemType.Bottle, "Bottle of Chateau Romani": ItemType.Bottle,
                "Progressive Sword": ItemType.ProgressiveSword, "Great Fairy Sword": ItemType.ProgressiveSword,
                "Progressive Bow": ItemType.Bow, "Fire Arrow": ItemType.Firerod, "Ice Arrow": ItemType.Icerod,
                "Light Arrow": ItemType.SilverArrows, "Hookshot": ItemType.Hookshot, "Progressive Shield": ItemType.ProgressiveShield,
                "Bottle of Red Potion": ItemType.Bottle,
                "Clock Town Map": ItemType.Map, "Woodfall Map": ItemType.Map, "Snowhead Map": ItemType.Map,
                "Romani Ranch Map": ItemType.Map, "Great Bay Map": ItemType.Map, "Stone Tower Map": ItemType.Map,
                "Small Key (Woodfall)": ItemType.Key, "Small Key (Snowhead)": ItemType.Key, "Small Key (Great Bay)": ItemType.Key,
                "Small Key (Stone Tower)": ItemType.Key,
                "Dungeon Map (Woodfall)": ItemType.Map, "Dungeon Map (Snowhead)": ItemType.Map, "Dungeon Map (Great Bay)": ItemType.Map,
                "Dungeon Map (Stone Tower)": ItemType.Map,
                "Compass (Woodfall)": ItemType.Compass, "Compass (Snowhead)": ItemType.Compass, "Compass (Great Bay)": ItemType.Compass,
                "Compass (Stone Tower)": ItemType.Compass,
                "Boss Key (Woodfall)": ItemType.BigKey, "Boss Key (Snowhead)": ItemType.BigKey, "Boss Key (Great Bay)": ItemType.BigKey,
                "Boss Key (Stone Tower)": ItemType.BigKey,
                "Progressive Bomb Bag": ItemType.BombUpgrade10, "Bundle of 10 Arrows": ItemType.TenArrows, "Bundle of 30 Arrows": ItemType.TenArrows,
                "Bomb Refill 10": ItemType.ThreeBombs, "Bomb Refill 30": ItemType.ThreeBombs, "Progressive Bombchu Bag": ItemType.BombUpgrade10,
                "Bombchu (1)": ItemType.ThreeBombs, "Bombchu (5)": ItemType.ThreeBombs, "Bombchu (10)": ItemType.ThreeBombs,
                "Blue Rupee": ItemType.FiveRupees, "Crimson Rupee": ItemType.ThreeHundredRupees, "Red Rupee": ItemType.TwentyRupees,
                "Purple Rupee": ItemType.FiftyRupees, "Silver Rupee": ItemType.OneHundredRupees, "Gold Rupee": ItemType.ThreeHundredRupees
            }
            return MMRNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "The Legend of Zelda - Oracle of Ages"):
            OoANameToSMZ3Code = {
                "Progressive Shield": ItemType.ProgressiveShield, "Bombs (10)": ItemType.ThreeBombs, "Progressive Sword": ItemType.ProgressiveSword,
                "Boomerang": ItemType.RedBoomerang, "Cane of Somaria": ItemType.Somaria, "Biggoron's Sword": ItemType.ProgressiveSword,
                "Bombchus (10)": ItemType.ThreeBombs, "Ricky's Flute": ItemType.Flute, "Dimitri's Flute": ItemType.Flute, "Moosh's Flute": ItemType.Flute,
                "Shovel": ItemType.Shovel, "Progressive Bracelet": ItemType.ProgressiveGlove, "Rupee (1)": ItemType.OneRupee,
                "Rupees (5)": ItemType.FiveRupees, "Rupees (10)": ItemType.FiveRupees, "Rupees (20)": ItemType.TwentyRupees,
                "Rupees (30)": ItemType.TwentyRupees, "Rupees (50)": ItemType.FiftyRupees, "Rupees (100)": ItemType.OneHundredRupees,
                "Rupees (200)": ItemType.ThreeHundredRupees, "Heart Container": ItemType.HeartContainer, "Piece of Heart": ItemType.HeartPiece,
                "Progressive Flippers": ItemType.Flippers,
                "Small Key (Maku Path)": ItemType.Key, "Small Key (Spirit's Grave)": ItemType.Key, "Small Key (Wing Dungeon)": ItemType.Key,
                "Small Key (Moonlit Grotto)": ItemType.Key, "Small Key (Skull Dungeon)": ItemType.Key, "Small Key (Crown Dungeon)": ItemType.Key,
                "Small Key (Mermaid's Cave Past)": ItemType.Key, "Small Key (Mermaid's Cave Present)": ItemType.Key, "Small Key (Jabu-Jabu's Belly)": ItemType.Key,
                "Small Key (Ancient Tomb)": ItemType.Key, "Small Key (Linked Hero's Cave)": ItemType.Key,
                "Master Key (Maku Path)": ItemType.BigKey, "Master Key (Spirit's Grave)": ItemType.BigKey, "Master Key (Wing Dungeon)": ItemType.BigKey,
                "Master Key (Moonlit Grotto)": ItemType.BigKey, "Master Key (Skull Dungeon)": ItemType.BigKey, "Master Key (Crown Dungeon)": ItemType.BigKey,
                "Master Key (Mermaid's Cave Past)": ItemType.BigKey, "Master Key (Mermaid's Cave Present)": ItemType.BigKey, "Master Key (Jabu-Jabu's Belly)": ItemType.BigKey,
                "Master Key (Ancient Tomb)": ItemType.BigKey, "Master Key (Linked Hero's cave)": ItemType.BigKey,
                "Boss Key (Spirit's Grave)": ItemType.BigKey, "Boss Key (Wing Dungeon)": ItemType.BigKey, "Boss Key (Moonlit Grotto)": ItemType.BigKey,
                "Boss Key (Skull Dungeon)": ItemType.BigKey, "Boss Key (Crown Dungeon)": ItemType.BigKey, "Boss Key (Mermaid's Cave)": ItemType.BigKey,
                "Boss Key (Jabu-Jabu's Belly)": ItemType.BigKey, "Boss Key (Ancient Tomb)": ItemType.BigKey,
                "Compass (Spirit's Grave)": ItemType.Compass, "Compass (Wing Dungeon)": ItemType.Compass, "Compass (Moonlit Grotto)": ItemType.Compass,
                "Compass (Skull Dungeon)": ItemType.Compass, "Compass (Crown Dungeon)": ItemType.Compass, "Compass (Mermaid's Cave Past)": ItemType.Compass,
                "Compass (Mermaid's Cave Present)": ItemType.Compass, "Compass (Jabu-Jabu's Belly)": ItemType.Compass, "Compass (Ancient Tomb)": ItemType.Compass,
                "Dungeon Map (Spirit's Grave)": ItemType.Map, "Dungeon Map (Wing Dungeon)": ItemType.Map, "Dungeon Map (Moonlit Grotto)": ItemType.Map,
                "Dungeon Map (Skull Dungeon)": ItemType.Map, "Dungeon Map (Crown Dungeon)": ItemType.Map, "Dungeon Map (Mermaid's Cave Past)": ItemType.Map,
                "Dungeon Map (Mermaid's Cave Present)": ItemType.Map, "Dungeon Map (Jabu-Jabu's Belly)": ItemType.Map, "Dungeon Map (Ancient Tomb)": ItemType.Map,
                "Broken Sword": ItemType.ProgressiveSword, "Bomb Flower": ItemType.BombUpgrade5, "Book of Seals": ItemType.Book, 
                "Crown Key": ItemType.BigKey, "Fairy Powder": ItemType.Powder, "Library Key": ItemType.BigKey, "Mermaid Key": ItemType.BigKey,
                "Old Mermaid Key": ItemType.BigKey
            }
            return OoANameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "The Legend of Zelda - Oracle of Seasons"):
            OoSNameToSMZ3Code = {
                "Progressive Shield": ItemType.ProgressiveShield, "Bombs (10)": ItemType.ThreeBombs, "Progressive Sword": ItemType.ProgressiveSword,
                "Progressive Boomerang": ItemType.RedBoomerang, "Cane of Somaria": ItemType.Somaria, "Biggoron's Sword": ItemType.ProgressiveSword,
                "Bombchus (10)": ItemType.ThreeBombs, "Ricky's Flute": ItemType.Flute, "Dimitri's Flute": ItemType.Flute, "Moosh's Flute": ItemType.Flute,
                "Shovel": ItemType.Shovel, "Power Bracelet": ItemType.ProgressiveGlove, "Rupee (1)": ItemType.OneRupee,
                "Rupees (5)": ItemType.FiveRupees, "Rupees (10)": ItemType.FiveRupees, "Rupees (20)": ItemType.TwentyRupees,
                "Rupees (30)": ItemType.TwentyRupees, "Rupees (50)": ItemType.FiftyRupees, "Rupees (100)": ItemType.OneHundredRupees,
                "Rupees (200)": ItemType.ThreeHundredRupees, "Heart Container": ItemType.HeartContainer, "Piece of Heart": ItemType.HeartPiece,
                "Flippers": ItemType.Flippers, "Bombs (20)": ItemType.ThreeBombs, "Bombchus (20)": ItemType.ThreeBombs,
                "Magnetic Gloves": ItemType.ProgressiveGlove,
                "Small Key (Hero's Cave)": ItemType.Key, "Small Key (Gnarled Root Dungeon)": ItemType.Key, "Small Key (Snake's Remains)": ItemType.Key,
                "Small Key (Poison Moth's Lair)": ItemType.Key, "Small Key (Dancing Dragon Dungeon)": ItemType.Key, "Small Key (Unicorn's Cave)": ItemType.Key,
                "Small Key (Ancient Ruins)": ItemType.Key, "Small Key (Explorer's Crypt)": ItemType.Key, "Small Key (Sword & Shield Dungeon)": ItemType.Key,
                "Small Key (Linked Hero's Cave)": ItemType.Key,
                "Master Key (Hero's Cave)": ItemType.BigKey, "Master Key (Gnarled Root Dungeon)": ItemType.BigKey, "Master Key (Snake's Remains)": ItemType.BigKey,
                "Master Key (Poison Moth's Lair)": ItemType.BigKey, "Master Key (Dancing Dragon Dungeon)": ItemType.BigKey, "Master Key (Unicorn's Cave)": ItemType.BigKey,
                "Master Key (Ancient Ruins)": ItemType.BigKey, "Master Key (Explorer's Crypt)": ItemType.BigKey, "Master Key (Sword & Shield Dungeon)": ItemType.BigKey,
                "Master Key (Linked Hero's Cave)": ItemType.BigKey,
                "Boss Key (Gnarled Root Dungeon)": ItemType.BigKey, "Boss Key (Snake's Remains)": ItemType.BigKey, "Boss Key (Poison Moth's Lair)": ItemType.BigKey,
                "Boss Key (Dancing Dragon Dungeon)": ItemType.BigKey, "Boss Key (Unicorn's Cave)": ItemType.BigKey, "Boss Key (Ancient Ruins)": ItemType.BigKey,
                "Boss Key (Explorer's Crypt)": ItemType.BigKey, "Boss Key (Sword & Shield Dungeon)": ItemType.BigKey,
                "Compass (Hero's Cave)": ItemType.Compass, "Compass (Gnarled Root Dungeon)": ItemType.Compass, "Compass (Snake's Remains)": ItemType.Compass,
                "Compass (Poison Moth's Lair)": ItemType.Compass, "Compass (Dancing Dragon Dungeon)": ItemType.Compass, "Compass (Unicorn's Cave)": ItemType.Compass,
                "Compass (Ancient Ruins)": ItemType.Compass, "Compass (Explorer's Crypt)": ItemType.Compass, "Compass (Sword & Shield Dungeon)": ItemType.Compass,
                "Dungeon Map (Hero's Cave)": ItemType.Map, "Dungeon Map (Gnarled Root Dungeon)": ItemType.Map, "Dungeon Map (Snake's Remains)": ItemType.Map,
                "Dungeon Map (Poison Moth's Lair)": ItemType.Map, "Dungeon Map (Dancing Dragon Dungeon)": ItemType.Map, "Dungeon Map (Unicorn's Cave)": ItemType.Map,
                "Dungeon Map (Ancient Ruins)": ItemType.Map, "Dungeon Map (Explorer's Crypt)": ItemType.Map, "Dungeon Map (Sword & Shield Dungeon)": ItemType.Map,
                "Mushroom": ItemType.Mushroom, "Gnarled Key": ItemType.BigKey, "Floodgate Key": ItemType.BigKey, "Dragon Key": ItemType.BigKey,
                "Treasure Map": ItemType.Map
            }
            return OoSNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "Ship of Harkinian" or "Ocarina of Time"): # I'm just going to assume these share the same item names for the sake of my own sanity
            SoHNameToSMZ3Code = {
                "Kokiri Sword": ItemType.ProgressiveSword, "Master Sword": ItemType.ProgressiveSword, "Giant's Knife": ItemType.ProgressiveSword,
                "Biggoron's Sword": ItemType.ProgressiveSword, "Deku Shield": ItemType.ProgressiveShield, "Hylian Shield": ItemType.ProgressiveShield,
                "Mirror Shield": ItemType.ProgressiveShield, "Goron Tunic": ItemType.ProgressiveTunic, "Zora Tunic": ItemType.ProgressiveTunic,
                "Boomerang": ItemType.RedBoomerang, "Megaton Hammer": ItemType.Hammer, "Fire Arrows": ItemType.Firerod,
                "Ice Arrows": ItemType.Icerod, "Light Arrows": ItemType.SilverArrows, "Odd Mushroom": ItemType.Mushroom,
                "Broken Goron's Sword": ItemType.ProgressiveSword, "Progressive Hookshot": ItemType.Hookshot, "Strength Upgrade": ItemType.ProgressiveGlove,
                "Progressive Bomb Bag": ItemType.BombUpgrade10, "Progressive Bow": ItemType.Bow, "Progressive Bombchu": ItemType.BombUpgrade10,
                "Progressive Magic Meter": ItemType.HalfMagic, "Progressive Ocarina": ItemType.Flute, "Progressive Goron Sword": ItemType.ProgressiveSword,
                "Empty Bottle": ItemType.Bottle,
                "Bottle with Milk": ItemType.Bottle, "Bottle with Red Potion": ItemType.BottleWithRedPotion, "Bottle with Green Potion": ItemType.BottleWithGreenPotion,
                "Bottle with Blue Potion": ItemType.BottleWithBluePotion, "Bottle with Fairy": ItemType.BottleWithFairy, "Bottle with Fish": ItemType.Bottle,
                "Bottle with Blue Fire": ItemType.Bottle, "Bottle with Bugs": ItemType.BottleWithBee, "Bottle with Poe": ItemType.Bottle,
                "Bottle with Ruto's Letter": ItemType.Bottle, "Bottle with Big Poe": ItemType.Bottle,
                "Great Deku Tree Map": ItemType.Map, "Dodongo's Cavern Map": ItemType.Map, "Jabu-Jabu's Belly Map": ItemType.Map,
                "Forest Temple Map": ItemType.Map, "Fire Temple Map": ItemType.Map, "Water Temple Map": ItemType.Map,
                "Spirit Temple Map": ItemType.Map, "Shadow Temple Map": ItemType.Map, "Bottom of the Well Map": ItemType.Map,
                "Ice Cavern Map": ItemType.Map,
                "Great Deku Tree Compass": ItemType.Compass, "Dodongo's Cavern Compass": ItemType.Compass, "Jabu-Jabu's Belly Compass": ItemType.Compass,
                "Forest Temple Compass": ItemType.Compass, "Fire Temple Compass": ItemType.Compass, "Water Temple Compass": ItemType.Compass,
                "Spirit Temple Compass": ItemType.Compass, "Shadow Temple Compass": ItemType.Compass, "Bottom of the Well Compass": ItemType.Compass,
                "Ice Cavern Compass": ItemType.Compass,
                "Forest Temple Boss Key": ItemType.BigKey, "Fire Temple Boss Key": ItemType.BigKey, "Water Temple Boss Key": ItemType.BigKey,
                "Spirit Temple Boss Key": ItemType.BigKey, "Shadow Temple Boss Key": ItemType.BigKey, "Ganon's Castle Boss Key": ItemType.BigKey,
                "Forest Temple Small Key": ItemType.Key, "Fire Temple Small Key": ItemType.Key, "Water Temple Small Key": ItemType.Key,
                "Spirit Temple Small Key": ItemType.Key, "Shadow Temple Small Key": ItemType.Key, "Bottom of the Well Small Key": ItemType.Key,
                "Training Ground Small Key": ItemType.Key, "Gerudo Fortress Small Key": ItemType.Key, "Ganon's Castle Small Key": ItemType.Key,
                "Treasure Game Small Key": ItemType.Key,
                "Forest Temple Key Ring": ItemType.BigKey, "Fire Temple Key Ring": ItemType.BigKey, "Water Temple Key Ring": ItemType.BigKey,
                "Spirit Temple Key Ring": ItemType.BigKey, "Shadow Temple Key Ring": ItemType.BigKey, "Bottom of the Well Key Ring": ItemType.BigKey,
                "Training Ground Key Ring": ItemType.BigKey, "Gerudo Fortress Key Ring": ItemType.BigKey, "Ganon's Castle Key Ring": ItemType.BigKey,
                "Treasure Game Key Ring": ItemType.BigKey,
                "Green Rupee": ItemType.OneRupee, "Greg the Green Rupee": ItemType.OneRupee, "Blue Rupee": ItemType.FiveRupees,
                "Red Rupee": ItemType.TwentyRupees, "Purple Rupee": ItemType.FiftyRupees, "Huge Rupee": ItemType.OneHundredRupees,
                "Piece of Heart": ItemType.HeartPiece, "Heart Container": ItemType.HeartContainer,
                "Bombs (5)": ItemType.ThreeBombs, "Bombs (10)": ItemType.ThreeBombs, "Bombs (20)": ItemType.ThreeBombs,
                "Bombchus (5)": ItemType.ThreeBombs, "Bombchus (10)": ItemType.ThreeBombs, "Bombchus (20)": ItemType.ThreeBombs,
                "Arrows (5)": ItemType.TenArrows, "Arrows (10)": ItemType.TenArrows, "Arrows (20)": ItemType.TenArrows,
                "Skeleton Key": ItemType.BigKey, "Bombchu Bag": ItemType.BombUpgrade10, "Quiver Inf": ItemType.ArrowUpgrade10,
                "Bomb Bag Inf": ItemType.BombUpgrade10, "Magic Inf": ItemType.HalfMagic, "Bombchu Inf": ItemType.BombUpgrade10,
                "Fairy Ocarina": ItemType.Flute, "Ocarina Of Time": ItemType.Flute, "Bomb Bag": ItemType.BombUpgrade10,
                "Big Bomb Bag": ItemType.BombUpgrade10, "Biggest Bomb Bag": ItemType.BombUpgrade10, "Fairy Bow": ItemType.Bow,
                "Big Quiver": ItemType.Bow, "Biggest Quiver": ItemType.Bow, "Gorons Bracelet": ItemType.ProgressiveGlove,
                "Silver Gauntlets": ItemType.ProgressiveGlove, "Golden Gauntlets": ItemType.ProgressiveGlove, "Hookshot": ItemType.Hookshot,
                "Longshot": ItemType.Hookshot, "Guard House Key": ItemType.BigKey, "Market Bazaar Key": ItemType.BigKey, "Market Potion Shop Key": ItemType.BigKey,
                "Mask Shop Key": ItemType.BigKey, "Market Shooting Gallery Key": ItemType.BigKey, "Bombchu Bowling Alley Key": ItemType.BigKey, 
                "Treasure Chest Game Building Key": ItemType.BigKey, "Bombchu Shop Key": ItemType.BigKey, "Richard's House Key": ItemType.BigKey,
                "Alley House Key": ItemType.BigKey, "Kakariko Bazaar Key": ItemType.BigKey, "Kakariko Potion Shop Key": ItemType.BigKey,
                "Boss's House Key": ItemType.BigKey, "Granny's Potion Shop Key": ItemType.BigKey, "Skulltula House Key": ItemType.BigKey, 
                "Impa's House Key": ItemType.BigKey, "Windmill Key": ItemType.BigKey, "Kakariko Shooting Gallery Key": ItemType.BigKey,
                "Dampe's Hut Key": ItemType.BigKey, "Talon's House Key": ItemType.BigKey, "Stables Key": ItemType.BigKey,
                "Back Tower Key": ItemType.BigKey, "Hylia Laboratory Key": ItemType.BigKey, "Fishing Hole Key": ItemType.BigKey
            }
            return SoHNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "The Legend of Zelda: A Link to the Past"):
            LttPRNameToSMZ3Code = {
                "Bow": ItemType.Bow, "Progressive Bow": ItemType.Bow, "Progressive Bow (Alt)": ItemType.Bow, "Book of Mudora": ItemType.Book,
                "Hammer": ItemType.Hammer, "Hookshot": ItemType.Hookshot, "Magic Mirror": ItemType.Mirror,
                "Ocarina": ItemType.Flute, "Ocarina (Activated)": ItemType.Flute, "Pegasus Boots": ItemType.Boots,
                "Power Glove": ItemType.ProgressiveGlove, "Cape": ItemType.Cape, "Mushroom": ItemType.Mushroom,
                "Shovel": ItemType.Shovel, "Lamp": ItemType.Lamp, "Magic Powder": ItemType.Powder,
                "Moon Pearl": ItemType.MoonPearl, "Cane of Somaria": ItemType.Somaria, "Fire Rod": ItemType.Firerod,
                "Flippers": ItemType.Flippers, "Ice Rod": ItemType.Icerod, "Titans Mitts": ItemType.ProgressiveGlove,
                "Bombos": ItemType.Bombos, "Ether": ItemType.Ether, "Quake": ItemType.Quake,
                "Bottle": ItemType.Bottle, "Bottle (Red Potion)": ItemType.BottleWithRedPotion, "Bottle (Green Potion)": ItemType.BottleWithGreenPotion,
                "Bottle (Blue Potion)": ItemType.BottleWithBluePotion, "Bottle (Fairy)": ItemType.BottleWithFairy, "Bottle (Bee)": ItemType.BottleWithBee,
                "Bottle (Good Bee)": ItemType.BottleWithGoldBee, "Master Sword": ItemType.ProgressiveSword, "Tempered Sword": ItemType.ProgressiveSword,
                "Fighter Sword": ItemType.ProgressiveSword, "Sword and Shield": ItemType.ProgressiveSword, "Golden Sword": ItemType.ProgressiveSword,
                "Progressive Sword": ItemType.ProgressiveSword, "Progressive Glove": ItemType.ProgressiveGlove, "Silver Arrows": ItemType.SilverArrows,
                "Single Arrow": ItemType.Arrow, "Arrows (10)": ItemType.TenArrows, "Arrow Upgrade (+10)": ItemType.ArrowUpgrade10,
                "Arrow Upgrade (+5)": ItemType.ArrowUpgrade5, "Single Bomb": ItemType.ThreeBombs, "Arrows (5)": ItemType.Arrow,
                "Bombs (3)": ItemType.ThreeBombs, "Bombs (10)": ItemType.ThreeBombs, "Bomb Upgrade (+10)": ItemType.BombUpgrade10,
                "Bomb Upgrade (+5)": ItemType.BombUpgrade5, "Blue Mail": ItemType.ProgressiveTunic, "Red Mail": ItemType.ProgressiveTunic,
                "Progressive Armor": ItemType.ProgressiveTunic, "Blue Shield": ItemType.ProgressiveShield, "Red Shield": ItemType.ProgressiveShield,
                "Mirror Shield": ItemType.ProgressiveShield, "Progressive Shield": ItemType.ProgressiveShield, "Bug Catching Net": ItemType.Bugnet,
                "Cane of Byrna": ItemType.Byrna, "Boss Heart Container": ItemType.HeartContainer, "Sanctuary Heart Container": ItemType.HeartContainer,
                "Piece of Heart": ItemType.HeartPiece, "Rupee (1)": ItemType.OneRupee, "Rupees (5)": ItemType.FiveRupees,
                "Rupees (20)": ItemType.TwentyRupees, "Rupees (50)": ItemType.FiftyRupees, "Rupees (100)": ItemType.OneHundredRupees,
                "Rupees (300)": ItemType.ThreeHundredRupees, "Rupoor": ItemType.ThreeHundredRupees, "Magic Upgrade (1/2)": ItemType.HalfMagic,
                "Magic Upgrade (1/4)": ItemType.HalfMagic,
                "Small Key (Eastern Palace)": ItemType.Key, "Small Key (Desert Palace)": ItemType.KeyDP, "Small Key (Tower of Hera)": ItemType.KeyTH,
                "Small Key (Escape)": ItemType.KeyHC, "Small Key (Agahnims Tower)": ItemType.KeyCT, "Small Key (Palace of Darkness)": ItemType.KeyPD,
                "Small Key (Thieves Town)": ItemType.KeyTT, "Small Key (Skull Woods)": ItemType.KeySW, "Small Key (Swamp Palace)": ItemType.KeySP,
                "Small Key (Ice Palace)": ItemType.KeyIP, "Small Key (Misery Mire)": ItemType.KeyMM, "Small Key (Turtle Rock)": ItemType.KeyTR,
                "Small Key (Ganons Tower)": ItemType.KeyGT, "Small Key (Universal)": ItemType.Key,
                "Big Key (Eastern Palace)": ItemType.BigKeyEP, "Big Key (Desert Palace)": ItemType.BigKeyDP, "Big Key (Tower of Hera)": ItemType.BigKeyTH,
                "Big Key (Escape)": ItemType.BigKey, "Big Key (Agahnims Tower)": ItemType.BigKey, "Big Key (Palace of Darkness)": ItemType.BigKeyPD,
                "Big Key (Thieves Town)": ItemType.BigKeyTT, "Big Key (Skull Woods)": ItemType.BigKeySW, "Big Key (Swamp Palace)": ItemType.BigKeySP,
                "Big Key (Ice Palace)": ItemType.BigKeyIP, "Big Key (Misery Mire)": ItemType.BigKeyMM, "Big Key (Turtle Rock)": ItemType.BigKeyTR,
                "Big Key (Ganons Tower)": ItemType.BigKeyGT,
                "Compass (Eastern Palace)": ItemType.CompassEP, "Compass (Desert Palace)": ItemType.CompassDP, "Compass (Tower of Hera)": ItemType.CompassTH,
                "Compass (Escape)": ItemType.Compass, "Compass (Agahnims Tower)": ItemType.Compass, "Compass (Palace of Darkness)": ItemType.CompassPD,
                "Compass (Thieves Town)": ItemType.CompassTT, "Compass (Skull Woods)": ItemType.CompassSW, "Compass (Swamp Palace)": ItemType.CompassSP,
                "Compass (Ice Palace)": ItemType.CompassIP, "Compass (Misery Mire)": ItemType.CompassMM, "Compass (Turtle Rock)": ItemType.CompassTR,
                "Compass (Ganons Tower)": ItemType.CompassGT,
                "Map (Eastern Palace)": ItemType.MapEP, "Map (Desert Palace)": ItemType.MapDP, "Map (Tower of Hera)": ItemType.MapTH,
                "Map (Escape)": ItemType.Map, "Map (Agahnims Tower)": ItemType.Map, "Map (Palace of Darkness)": ItemType.MapPD,
                "Map (Thieves Town)": ItemType.MapTT, "Map (Skull Woods)": ItemType.MapSW, "Map (Swamp Palace)": ItemType.MapSP,
                "Map (Ice Palace)": ItemType.MapIP, "Map (Misery Mire)": ItemType.MapMM, "Map (Turtle Rock)": ItemType.MapTR,
                "Map (Ganons Tower)": ItemType.MapGT
                
            }
            return LttPRNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value
        elif (location.APLocation.item.game == "A Link Between Worlds"):
            ALBWNameToSMZ3Code = {
                "Bow": ItemType.Bow, "Boomerang": ItemType.RedBoomerang, "Hookshot": ItemType.Hookshot,
                "Bombs": ItemType.BombUpgrade10, "Fire Rod": ItemType.Firerod, "Ice Rod": ItemType.Icerod,
                "Hammer": ItemType.Hammer, "Bow of Light": ItemType.Bow, "Pegasus Boots": ItemType.Boots,
                "Flippers": ItemType.Flippers, "Progressive Bracelet": ItemType.ProgressiveGlove, "Hylian Shield": ItemType.ProgressiveShield,
                "Quake": ItemType.Quake, "Green Rupee": ItemType.OneRupee, "Blue Rupee": ItemType.FiveRupees,
                "Red Rupee": ItemType.TwentyRupees, "Purple Rupee": ItemType.FiftyRupees, "Silver Rupee": ItemType.OneHundredRupees,
                "Gold Rupee": ItemType.ThreeHundredRupees, "Piece of Heart": ItemType.HeartPiece, "Heart Container": ItemType.HeartContainer,
                "Bottle": ItemType.Bottle, "Lamp": ItemType.Lamp, "Progressive Sword": ItemType.ProgressiveSword,
                "Progressive Glove": ItemType.ProgressiveGlove, "Bug Net": ItemType.Bugnet, "Progressive Mail": ItemType.ProgressiveTunic,
                "Small Key (Hyrule Sanctuary)": ItemType.Key, "Small Key (Lorule Sanctuary)": ItemType.Key,
                "Compass (Eastern Palace)": ItemType.CompassEP, "Big Key (Eastern Palace)": ItemType.BigKeyEP, "Small Key (Eastern Palace)": ItemType.Key,
                "Compass (House of Gales)": ItemType.Compass, "Big Key (House of Gales)": ItemType.BigKey, "Small Key (House of Gales)": ItemType.Key,
                "Compass (Tower of Hera)": ItemType.CompassTH, "Big Key (Tower of Hera)": ItemType.BigKeyTH, "Small Key (Tower of Hera)": ItemType.KeyTH,
                "Compass (Dark Palace)": ItemType.CompassPD, "Big Key (Dark Palace)": ItemType.BigKeyDP, "Small Key (Dark Palace)": ItemType.KeyPD,
                "Compass (Swamp Palace)": ItemType.CompassSP, "Big Key (Swamp Palace)": ItemType.BigKeySP, "Small Key (Swamp Palace)": ItemType.KeySP,
                "Compass (Skull Woods)": ItemType.CompassSW, "Big Key (Skull Woods)": ItemType.BigKeySW, "Small Key (Skull Woods)": ItemType.KeySW,
                "Compass (Thieves' Hideout)": ItemType.CompassTT, "Big Key (Thieves' Hideout)": ItemType.BigKeyTT, "Small Key (Theives' Hideout)": ItemType.KeyTT,
                "Compass (Ice Ruins)": ItemType.CompassIP, "Big Key (Ice Ruins)": ItemType.BigKeyIP, "Small Key (Ice Ruins)": ItemType.KeyIP,
                "Compass (Desert Palace)": ItemType.CompassDP, "Big Key (Desert Palace)": ItemType.BigKeyDP, "Small Key (Desert Palace)": ItemType.KeyDP,
                "Compass (Turtle Rock)": ItemType.CompassTR, "Big Key (Turtle Rock)": ItemType.BigKeyTR, "Small Key (Turtle Rock)": ItemType.KeyTR,
                "Compass (Lorule Castle)": ItemType.Compass, "Big Key (Lorule Castle)": ItemType.BigKey, "Small Key (Lorule Castle)": ItemType.Key,
                "Ice Rod Upgrade": ItemType.Icerod, "Bomb Upgrade": ItemType.BombUpgrade10, "Fire Rod Upgrade": ItemType.Firerod,
                "Hookshot Upgrade": ItemType.Hookshot, "Boomerang Upgrade": ItemType.RedBoomerang, "Hammer Upgrade": ItemType.Hammer,
                "Bow Upgrade": ItemType.Bow, "Lamp Upgrade": ItemType.Lamp, "Bug Net Upgrade": ItemType.Bugnet
            }
            return ALBWNameToSMZ3Code.get(location.APLocation.item.name, ItemType.Something).value

        else:
            return ItemType.Something.value

    def ItemTablePatch(self, location: Location, itemId: int):
        itemtype = 0 if location.APLocation.item.player == location.Region.world.Id else 1
        owner = location.APLocation.item.player if location.APLocation.item.player < 256 else 0
        return (0x386000 + (location.Id * 8), getWordArray(itemtype) + getWordArray(itemId) + getWordArray(owner))

    def WriteDungeonMusic(self, keysanity: bool):
        if (not keysanity):
            regions = [region for region in self.myWorld.Regions if isinstance(region, Z3Region) and isinstance(region, IReward) and 
                                                                    region.Reward != None and region.Reward != RewardType.Agahnim]
            pendantRegions = [region for region in regions if region.Reward in [RewardType.PendantGreen, RewardType.PendantNonGreen]]
            crystalRegions = [region for region in regions if region.Reward in [RewardType.CrystalBlue, RewardType.CrystalRed]]
            music = [0x11 if (region.Reward == RewardType.PendantGreen or region.Reward == RewardType.PendantNonGreen) else 0x16 for region in regions]
            self.patches += self.MusicPatches(regions, music)

    #IEnumerable<byte> RandomDungeonMusic() {
    #    while (true) yield return rnd.Next(2) == 0 ? (byte)0x11 : (byte)0x16;
    #}

    def MusicPatches(self, regions: List[IReward], music: List[int]):
        addresses = [self.MusicAddresses(region) for region in regions]
        associations = zip(addresses, music)
        return [(Snes(i), [association[1]]) for association in associations for i in association[0]]

    def MusicAddresses(self, region: IReward):
        regionMap = {
                        EasternPalace : [ 0x2D59A ],
                        DesertPalace : [ 0x2D59B, 0x2D59C, 0x2D59D, 0x2D59E ],
                        TowerOfHera : [ 0x2D5C5, 0x2907A, 0x28B8C ],
                        PalaceOfDarkness : [ 0x2D5B8 ],
                        SwampPalace : [ 0x2D5B7 ],
                        SkullWoods : [ 0x2D5BA, 0x2D5BB, 0x2D5BC, 0x2D5BD, 0x2D608, 0x2D609, 0x2D60A, 0x2D60B ],
                        ThievesTown : [ 0x2D5C6 ],
                        IcePalace : [ 0x2D5BF ],
                        MiseryMire : [ 0x2D5B9 ],
                        TurtleRock : [ 0x2D5C7, 0x2D5A7, 0x2D5AA, 0x2D5AB ],
                    }
        result = regionMap.get(type(region), None)
        if result is None:
            raise exception(f"Region {region} should not be a dungeon music region")
        else:
            return result

    def WritePrizeShuffle(self, dropPrizes):
        self.patches.append((Snes(0x6FA78), [e.value for e in dropPrizes.Packs]))
        self.patches.append((Snes(0x1DFBD4), [e.value for e in dropPrizes.TreePulls]))
        self.patches.append((Snes(0x6A9C8), [dropPrizes.CrabContinous.value]))
        self.patches.append((Snes(0x6A9C4), [dropPrizes.CrabFinal.value]))
        self.patches.append((Snes(0x6F993), [dropPrizes.Stun.value]))
        self.patches.append((Snes(0x1D82CC), [dropPrizes.Fish.value]))

        self.patches += self.EnemyPrizePackDistribution()

        #/* Pack drop chance */
        #/* Normal difficulty is 50%. 0 => 100%, 1 => 50%, 3 => 25% */
        nrPacks = 7
        probability = 1
        self.patches.append((Snes(0x6FA62), [probability] * nrPacks))

    def EnemyPrizePackDistribution(self):
        (prizePacks, duplicatePacks) = self.EnemyPrizePacks()

        n = sum(len(x[1]) for x in prizePacks)
        randomization = self.PrizePackRandomization(n, 1)
        patches = []
        for prizepack in prizePacks:
            (packs, randomization) = SplitOff(randomization, len(prizepack[1]))
            patches.append((prizepack[0], [(b | p) for b,p in zip(prizepack[1], packs)]))

        duplicates = [(d[1], p[1])
                        for d in duplicatePacks
                        for p in patches
                        if p[0] == d[0]]
        patches += duplicates

        return [(Snes(x[0]), x[1]) for x in patches]

    #/* Guarantees at least s of each prize pack, over a total of n packs.
    #* In each iteration, from the product n * m, use the guaranteed number
    #* at k, where k is the "row" (integer division by m), when k falls
    #* within the list boundary. Otherwise use the "column" (modulo by m)
    #* as the random element.
    #*/
    def PrizePackRandomization(self, n: int, s: int):
        m = 7
        g = list(range(0, m)) * s

        def randomization(n: int):
            result = []
            n = m * n
            while (n > 0):
                r = self.rnd.randrange(0, n)
                k = r // m
                result.append(g[k] if k < len(g) else r % m)
                if (k < len(g)): del g[k]
                n -= m
            return result

        return [(x + 1) for x in randomization(n)]

    #/* Todo: Deadrock turns into $8F Blob when powdered, but those "onion blobs" always drop prize pack 1. */
    def EnemyPrizePacks(self):
        offset = 0xDB632
        patches = [
            #/* sprite_prep */
            (0x6888D, [ 0x00 ]), #// Keese DW
            (0x688A8, [ 0x00 ]), #// Rope
            (0x68967, [ 0x00, 0x00 ]), #// Crow/Dacto
            (0x69125, [ 0x00, 0x00 ]), #// Red/Blue Hardhat Bettle
            #/* sprite properties */
            (offset+0x01, [ 0x90 ]), #// Vulture
            (offset+0x08, [ 0x00 ]), #// Octorok (One Way)
            (offset+0x0A, [ 0x00 ]), #// Octorok (Four Way)
            (offset+0x0D, [ 0x80, 0x90 ]), #// Buzzblob, Snapdragon
            (offset+0x11, [ 0x90, 0x90, 0x00 ]), #// Hinox, Moblin, Mini Helmasaur
            (offset+0x18, [ 0x90, 0x90 ]), #// Mini Moldorm, Poe/Hyu
            (offset+0x20, [ 0x00 ]), #// Sluggula
            (offset+0x22, [ 0x80, 0x00, 0x00 ]), #// Ropa, Red Bari, Blue Bari
            #// Blue Soldier/Tarus, Green Soldier, Red Spear Soldier
            #// Blue Assault Soldier, Red Assault Spear Soldier/Tarus
            #// Blue Archer, Green Archer
            #// Red Javelin Soldier, Red Bush Javelin Soldier
            #// Red Bomb Soldiers, Green Soldier Recruits,
            #// Geldman, Toppo
            (offset+0x41, [ 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x10, 0x90, 0x90, 0x80 ]),
            (offset+0x4F, [ 0x80 ]), #// Popo 2
            (offset+0x51, [ 0x80 ]), #// Armos
            (offset+0x55, [ 0x00, 0x00 ]), #// Ku, Zora
            (offset+0x58, [ 0x90 ]), #// Crab
            (offset+0x64, [ 0x80 ]), #// Devalant (Shooter)
            (offset+0x6A, [ 0x90, 0x90 ]), #// Ball N' Chain Trooper, Cannon Soldier
            (offset+0x6D, [ 0x80, 0x80 ]), #// Rat/Buzz, (Stal)Rope
            (offset+0x71, [ 0x80 ]), #// Leever
            (offset+0x7C, [ 0x90 ]), #// Initially Floating Stal
            (offset+0x81, [ 0xC0 ]), #// Hover
            #// Green Eyegore/Mimic, Red Eyegore/Mimic
            #// Detached Stalfos Body, Kodongo
            (offset+0x83, [ 0x10, 0x10, 0x10, 0x00 ]),
            (offset+0x8B, [ 0x10 ]), #// Gibdo
            (offset+0x8E, [ 0x00, 0x00 ]), #// Terrorpin, Blob
            (offset+0x91, [ 0x10 ]), #// Stalfos Knight
            (offset+0x99, [ 0x10 ]), #// Pengator
            (offset+0x9B, [ 0x10 ]), #// Wizzrobe
            #// Blue Zazak, Red Zazak, Stalfos
            #// Green Zirro, Blue Zirro, Pikit
            (offset+0xA5, [ 0x10, 0x10, 0x10, 0x80, 0x80, 0x80 ]),
            (offset+0xC7, [ 0x10 ]), #// Hokku-Bokku
            (offset+0xC9, [ 0x10 ]), #// Tektite
            (offset+0xD0, [ 0x10 ]), #// Lynel
            (offset+0xD3, [ 0x00 ]), #// Stal
            ]
        duplicates = [
            #/* Popo2 -> Popo. Popo is not used in vanilla Z3, but we duplicate from Popo2 just to be sure */
            (offset + 0x4F, offset + 0x4E),
        ]
        return (patches, duplicates)

    def WriteTexts(self, config: Config):
        regions = [region for region in self.myWorld.Regions if isinstance(region, IReward)]
        greenPendantDungeon = [region for region in regions if region.Reward == RewardType.PendantGreen][0]
        redCrystalDungeons = [region for region in regions if region.Reward == RewardType.CrystalRed]

        sahasrahla = Texts.SahasrahlaReveal(greenPendantDungeon)
        self.stringTable.SetSahasrahlaRevealText(sahasrahla)

        bombShop = Texts.BombShopReveal(redCrystalDungeons)
        self.stringTable.SetBombShopRevealText(bombShop)

        blind = Texts.Blind(self.rnd)
        self.stringTable.SetBlindText(blind)

        tavernMan = Texts.TavernMan(self.rnd)
        self.stringTable.SetTavernManText(tavernMan)

        ganon = Texts.GanonFirstPhase(self.rnd)
        self.stringTable.SetGanonFirstPhaseText(ganon)

        silversLocation = [loc for world in self.allWorlds for loc in world.Locations if loc.ItemIs(ItemType.SilverArrows, self.myWorld)]
        if len(silversLocation) == 0:      
            silvers = Texts.GanonThirdPhaseMulti(None, self.myWorld, self.silversWorldID, self.playerIDToNames[self.silversWorldID])
        else:
            silvers = Texts.GanonThirdPhaseMulti(silversLocation[0].Region, self.myWorld) if config.Multiworld else \
                        Texts.GanonThirdPhaseSingle(silversLocation[0].Region)
        self.stringTable.SetGanonThirdPhaseText(silvers)

        triforceRoom = Texts.TriforceRoom(self.rnd)
        self.stringTable.SetTriforceRoomText(triforceRoom)

    def WriteStringTable(self):
        #// Todo: v12, base table in asm, use move instructions in seed patch
        self.patches.append((Snes(0x1C8000), self.stringTable.GetPaddedBytes()))

    def WritePlayerNames(self):
        self.patches += [(0x385000 + (0 * 16), self.PlayerNameBytes("Archipelago"))]
        self.patches += [(0x385000 + (id * 16), self.PlayerNameBytes(name)) for name, id in self.playerNames.items() if id < 256]

    def PlayerNameBytes(self, name: str):
        name = (name[:16] if len(name) > 16 else name).center(16)
        return bytearray(name, 'utf8') 

    def WriteSeedData(self):
        configField1 =                                                                           \
            ((1 if self.myWorld.Config.Race else 0) << 15) |                                     \
            ((1 if self.myWorld.Config.Keysanity else 0) << 13) |                                \
            ((1 if self.myWorld.Config.Multiworld else 0) << 12) |                               \
            (self.myWorld.Config.Z3Logic.value << 10) |                                          \
            (self.myWorld.Config.SMLogic.value << 8) |                                           \
            (Patch.Major << 4) |                                                                 \
            (Patch.Minor << 0)

        configField2 =                                                                           \
            ((1 if self.myWorld.Config.SwordLocation else 0) << 14) |                            \
            ((1 if self.myWorld.Config.MorphLocation else 0) << 12) |                            \
            ((1 if self.myWorld.Config.Goal else 0) << 8)     

        self.patches.append((Snes(0x80FF50), getWordArray(self.myWorld.Id)))
        self.patches.append((Snes(0x80FF52), getWordArray(configField1)))
        self.patches.append((Snes(0x80FF54), getDoubleWordArray(self.seed)))
        self.patches.append((Snes(0x80FF58), getWordArray(configField2)))
        #/* Reserve the rest of the space for future use */
        self.patches.append((Snes(0x80FF5A), [0x00] * 6))
        self.patches.append((Snes(0x80FF60), bytearray(self.seedGuid, 'utf8')))
        self.patches.append((Snes(0x80FF80), bytearray(self.myWorld.Guid, 'utf8')))

    def WriteCommonFlags(self):
        #/* Common Combo Configuration flags at [asm]/config.asm */
        if (self.myWorld.Config.Multiworld):
            self.patches.append((Snes(0xF47000), getWordArray(0x0001)))
        if (self.myWorld.Config.Keysanity):
            self.patches.append((Snes(0xF47006), getWordArray(0x0001)))

    def WriteGameTitle(self):
        z3Glitch =  "N" if self.myWorld.Config.Z3Logic == Config.Z3Logic.Nmg else \
                    "O" if self.myWorld.Config.Z3Logic == Config.Z3Logic.Owg else \
                    "C"
        smGlitch =  "N" if self.myWorld.Config.SMLogic == Config.SMLogic.Normal else \
                    "H" if self.myWorld.Config.SMLogic == Config.SMLogic.Hard else \
                    "X"

        from Utils import __version__
        self.title = f"ZSM{Patch.Major}{Patch.Minor}{Patch.Patch}{__version__.replace('.', '')[0:3]}{z3Glitch}{smGlitch}{self.myWorld.Id}{self.seed:08x}".ljust(21)[:21]
        self.patches.append((Snes(0x00FFC0), bytearray(self.title, 'utf8')))
        self.patches.append((Snes(0x80FFC0), bytearray(self.title, 'utf8')))
    
    def WriteZ3KeysanityFlags(self):
        if (self.myWorld.Config.Keysanity):
            self.patches.append((Snes(0x40003B), [ 1 ])) #// MapMode #$00 = Always On (default) - #$01 = Require Map Item
            self.patches.append((Snes(0x400045), [ 0x0f ])) #// display ----dcba a: Small Keys, b: Big Key, c: Map, d: Compass
            self.patches.append((Snes(0x40016A), [ 0x01 ])) #// FreeItemText: db #$01 ; #00 = Off (default) - #$01 = On

    def WriteSMKeyCardDoors(self):
        plaquePlm = 0xd410
        plmTablePos = 0xf800

        if ( self.myWorld.Config.Keysanity):
            doorList = [
                            #// RoomId  Door Facing              yyxx  Keycard Event Type                   Plaque type               yyxx, Address (if 0 a dynamic PLM is created)
                            #// Crateria
                            [ 0x91F8, KeycardDoors.Right,      0x2601, KeycardEvents.CrateriaLevel1,        KeycardPlaque.Level1,   0x2400, 0x0000 ], #// Crateria - Landing Site - Door to gauntlet
                            [ 0x91F8, KeycardDoors.Left,       0x168E, KeycardEvents.CrateriaLevel1,        KeycardPlaque.Level1,   0x148F, 0x801E ], #// Crateria - Landing Site - Door to landing site PB
                            [ 0x948C, KeycardDoors.Left,       0x062E, KeycardEvents.CrateriaLevel2,        KeycardPlaque.Level2,   0x042F, 0x8222 ], #// Crateria - Before Moat - Door to moat (overwrite PB door)
                            [ 0x99BD, KeycardDoors.Left,       0x660E, KeycardEvents.CrateriaBoss,          KeycardPlaque.Boss,     0x640F, 0x8470 ], #// Crateria - Before G4 - Door to G4
                            [ 0x9879, KeycardDoors.Left,       0x062E, KeycardEvents.CrateriaBoss,          KeycardPlaque.Boss,     0x042F, 0x8420 ], #// Crateria - Before BT - Door to Bomb Torizo
                            
                            #// Brinstar
                            [ 0x9F11, KeycardDoors.Left,       0x060E, KeycardEvents.BrinstarLevel1,        KeycardPlaque.Level1,   0x040F, 0x8784 ], #// Brinstar - Blue Brinstar - Door to ceiling e-tank room

                            [ 0x9AD9, KeycardDoors.Right,      0xA601, KeycardEvents.BrinstarLevel2,        KeycardPlaque.Level2,   0xA400, 0x0000 ], #// Brinstar - Green Brinstar - Door to etecoon area                
                            [ 0x9D9C, KeycardDoors.Down,       0x0336, KeycardEvents.BrinstarBoss,          KeycardPlaque.Boss,     0x0234, 0x863A ], #// Brinstar - Pink Brinstar - Door to spore spawn                
                            [ 0xA130, KeycardDoors.Left,       0x161E, KeycardEvents.BrinstarLevel2,        KeycardPlaque.Level2,   0x141F, 0x881C ], #// Brinstar - Pink Brinstar - Door to wave gate e-tank
                            [ 0xA0A4, KeycardDoors.Left,       0x062E, KeycardEvents.BrinstarLevel2,        KeycardPlaque.Level2,   0x042F, 0x0000 ], #// Brinstar - Pink Brinstar - Door to spore spawn super

                            [ 0xA56B, KeycardDoors.Left,       0x161E, KeycardEvents.BrinstarBoss,          KeycardPlaque.Boss,     0x141F, 0x8A1A ], #// Brinstar - Before Kraid - Door to Kraid

                            #// Upper Norfair
                            [ 0xA7DE, KeycardDoors.Right,      0x3601, KeycardEvents.NorfairLevel1,         KeycardPlaque.Level1,   0x3400, 0x8B00 ], #// Norfair - Business Centre - Door towards Ice
                            [ 0xA923, KeycardDoors.Right,      0x0601, KeycardEvents.NorfairLevel1,         KeycardPlaque.Level1,   0x0400, 0x0000 ], #// Norfair - Pre-Crocomire - Door towards Ice

                            [ 0xA788, KeycardDoors.Left,       0x162E, KeycardEvents.NorfairLevel2,         KeycardPlaque.Level2,   0x142F, 0x8AEA ], #// Norfair - Lava Missile Room - Door towards Bubble Mountain
                            [ 0xAF72, KeycardDoors.Left,       0x061E, KeycardEvents.NorfairLevel2,         KeycardPlaque.Level2,   0x041F, 0x0000 ], #// Norfair - After frog speedway - Door to Bubble Mountain
                            [ 0xAEDF, KeycardDoors.Down,       0x0206, KeycardEvents.NorfairLevel2,         KeycardPlaque.Level2,   0x0204, 0x0000 ], #// Norfair - Below bubble mountain - Door to Bubble Mountain
                            [ 0xAD5E, KeycardDoors.Right,      0x0601, KeycardEvents.NorfairLevel2,         KeycardPlaque.Level2,   0x0400, 0x0000 ], #// Norfair - LN Escape - Door to Bubble Mountain
                            
                            [ 0xA923, KeycardDoors.Up,         0x2DC6, KeycardEvents.NorfairBoss,           KeycardPlaque.Boss,     0x2EC4, 0x8B96 ], #// Norfair - Pre-Crocomire - Door to Crocomire

                            #// Lower Norfair
                            [ 0xB4AD, KeycardDoors.Left,       0x160E, KeycardEvents.LowerNorfairLevel1,    KeycardPlaque.Level1,   0x140F, 0x0000 ], #// Lower Norfair - WRITG - Door to Amphitheatre
                            [ 0xAD5E, KeycardDoors.Left,       0x065E, KeycardEvents.LowerNorfairLevel1,    KeycardPlaque.Level1,   0x045F, 0x0000 ], #// Lower Norfair - Exit - Door to "Reverse LN Entry"
                            [ 0xB37A, KeycardDoors.Right,      0x0601, KeycardEvents.LowerNorfairBoss,      KeycardPlaque.Boss,     0x0400, 0x8EA6 ], #// Lower Norfair - Pre-Ridley - Door to Ridley

                            #// Maridia
                            [ 0xD0B9, KeycardDoors.Left,       0x065E, KeycardEvents.MaridiaLevel1,         KeycardPlaque.Level1,   0x045F, 0x0000 ], #// Maridia - Mt. Everest - Door to Pink Maridia
                            [ 0xD5A7, KeycardDoors.Right,      0x1601, KeycardEvents.MaridiaLevel1,         KeycardPlaque.Level1,   0x1400, 0x0000 ], #// Maridia - Aqueduct - Door towards Beach

                            [ 0xD617, KeycardDoors.Left,       0x063E, KeycardEvents.MaridiaLevel2,         KeycardPlaque.Level2,   0x043F, 0x0000 ], #// Maridia - Pre-Botwoon - Door to Botwoon
                            [ 0xD913, KeycardDoors.Right,      0x2601, KeycardEvents.MaridiaLevel2,         KeycardPlaque.Level2,   0x2400, 0x0000 ], #// Maridia - Pre-Colloseum - Door to post-botwoon

                            [ 0xD78F, KeycardDoors.Right,      0x2601, KeycardEvents.MaridiaBoss,           KeycardPlaque.Boss,     0x2400, 0xC73B ], #// Maridia - Precious Room - Door to Draygon

                            [ 0xDA2B, KeycardDoors.BossLeft,   0x164E, 0x00f0,                              KeycardPlaque.Null,     0x144F, 0x0000 ], #// Maridia - Change Cac Alley Door to Boss Door (prevents key breaking)

                            #// Wrecked Ship
                            [ 0x93FE, KeycardDoors.Left,       0x167E, KeycardEvents.WreckedShipLevel1,     KeycardPlaque.Level1,   0x147F, 0x0000 ], #// Wrecked Ship - Outside Wrecked Ship West - Door to Reserve Tank Check
                            [ 0x968F, KeycardDoors.Left,       0x060E, KeycardEvents.WreckedShipLevel1,     KeycardPlaque.Level1,   0x040F, 0x0000 ], #// Wrecked Ship - Outside Wrecked Ship West - Door to Bowling Alley
                            [ 0xCE40, KeycardDoors.Left,       0x060E, KeycardEvents.WreckedShipLevel1,     KeycardPlaque.Level1,   0x040F, 0x0000 ], #// Wrecked Ship - Gravity Suit - Door to Bowling Alley

                            [ 0xCC6F, KeycardDoors.Left,       0x064E, KeycardEvents.WreckedShipBoss,       KeycardPlaque.Boss,     0x044F, 0xC29D ], #// Wrecked Ship - Pre-Phantoon - Door to Phantoon   
            ]

            doorId = 0x0000
            for door in doorList:
                #/* When "Fast Ganon" is set, don't place the G4 Boss key door to enable faster games */
                if (door[0] == 0x99BD and self.myWorld.Config.Goal == Goal.FastGanonDefeatMotherBrain):
                    continue
                doorArgs = doorId | door[3] if door[4] != KeycardPlaque.Null else door[3]
                if (door[6] == 0):
                    #// Write dynamic door
                    doorData = []
                    for x in door[0:3]:
                        doorData += getWordArray(x)
                    doorData += getWordArray(doorArgs)
                    self.patches.append((Snes(0x8f0000 + plmTablePos), doorData))
                    plmTablePos += 0x08
                else:
                    #// Overwrite existing door
                    doorData = []
                    for x in door[1:3]:
                        doorData += getWordArray(x)
                    doorData += getWordArray(doorArgs)
                    self.patches.append((Snes(0x8f0000 + door[6]), doorData))
                    if((door[3] == KeycardEvents.BrinstarBoss and door[0] != 0x9D9C) or door[3] == KeycardEvents.LowerNorfairBoss or door[3] == KeycardEvents.MaridiaBoss or door[3] == KeycardEvents.WreckedShipBoss):
                        #// Overwrite the extra parts of the Gadora with a PLM that just deletes itself
                        self.patches.append((Snes(0x8f0000 + door[6] + 0x06), [ 0x2F, 0xB6, 0x00, 0x00, 0x00, 0x00, 0x2F, 0xB6, 0x00, 0x00, 0x00, 0x00 ]))

                #// Plaque data
                if (door[4] != KeycardPlaque.Null):
                    plaqueData = getWordArray(door[0]) + getWordArray(plaquePlm) + getWordArray(door[5]) + getWordArray(door[4])
                    self.patches.append((Snes(0x8f0000 + plmTablePos), plaqueData))
                    plmTablePos += 0x08
                doorId += 1

        #/* Write plaque showing SM bosses that needs to be killed */
        if (self.myWorld.Config.OpenTourian != OpenTourian.FourBosses):
            plaqueData = getWordArray(0xA5ED) + getWordArray(plaquePlm) + getWordArray(0x044F) + getWordArray(KeycardPlaque.Zero + self.myWorld.TourianBossTokens)
            self.patches.append((Snes(0x8f0000 + plmTablePos), plaqueData))
            plmTablePos += 0x08

        self.patches.append((Snes(0x8f0000 + plmTablePos), [ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ]))

    def WriteDiggingGameRng(self):
        digs = (self.rnd.randrange(30) + 1)
        self.patches.append((Snes(0x308020), [ digs ]))
        self.patches.append((Snes(0x1DFD95), [ digs ]))

    #// Removes Sword/Shield from Uncle by moving the tiles for
    #// sword/shield to his head and replaces them with his head.
    def WriteRemoveEquipmentFromUncle(self, item: Item):
        if (item.Type != ItemType.ProgressiveSword):
            self.patches += [
                    (Snes(0xDD263), [ 0x00, 0x00, 0xF6, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD26B), [ 0x00, 0x00, 0xF6, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD293), [ 0x00, 0x00, 0xF6, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD29B), [ 0x00, 0x00, 0xF7, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD2B3), [ 0x00, 0x00, 0xF6, 0xFF, 0x02, 0x0E ]),
                    (Snes(0xDD2BB), [ 0x00, 0x00, 0xF6, 0xFF, 0x02, 0x0E ]),
                    (Snes(0xDD2E3), [ 0x00, 0x00, 0xF7, 0xFF, 0x02, 0x0E ]),
                    (Snes(0xDD2EB), [ 0x00, 0x00, 0xF7, 0xFF, 0x02, 0x0E ]),
                    (Snes(0xDD31B), [ 0x00, 0x00, 0xE4, 0xFF, 0x08, 0x0E ]),
                    (Snes(0xDD323), [ 0x00, 0x00, 0xE4, 0xFF, 0x08, 0x0E ]),
                ]
        if (item.Type != ItemType.ProgressiveShield):
            self.patches += [
                    (Snes(0xDD253), [ 0x00, 0x00, 0xF6, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD25B), [ 0x00, 0x00, 0xF6, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD283), [ 0x00, 0x00, 0xF6, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD28B), [ 0x00, 0x00, 0xF7, 0xFF, 0x00, 0x0E ]),
                    (Snes(0xDD2CB), [ 0x00, 0x00, 0xF6, 0xFF, 0x02, 0x0E ]),
                    (Snes(0xDD2FB), [ 0x00, 0x00, 0xF7, 0xFF, 0x02, 0x0E ]),
                    (Snes(0xDD313), [ 0x00, 0x00, 0xE4, 0xFF, 0x08, 0x0E ]),
                ]

    def WritePreOpenPyramid(self, goal: Goal):
        if (goal == Goal.FastGanonDefeatMotherBrain):
            self.patches.append((Snes(0x30808B), [0x01]))

    def WriteGanonInvicible(self, goal: Goal):
        #/* Defaults to $00 (never) at [asm]/z3/randomizer/tables.asm */
        valueMap =  {
                        Goal.DefeatBoth : 0x03,
                        Goal.FastGanonDefeatMotherBrain : 0x04,
                        Goal.AllDungeonsDefeatMotherBrain : 0x02
                    }
        value = valueMap.get(goal, None)
        if (value is None):
            raise exception(f"Unknown Ganon invincible value {goal}")
        else:
            self.patches.append((Snes(0x30803E), [value]))

    def WriteBossesNeeded(self, tourianBossTokens):
        self.patches.append((Snes(0xF47200), getWordArray(tourianBossTokens)))

    def WriteCrystalsNeeded(self, towerCrystals, ganonCrystals, goal: Goal):
        self.patches.append((Snes(0x30805E), [towerCrystals]))
        self.patches.append((Snes(0x30805F), [ganonCrystals]))

        self.stringTable.SetTowerRequirementText(f"You need {towerCrystals} crystals to enter Ganon's Tower.")
        if (goal == Goal.AllDungeonsDefeatMotherBrain):
            self.stringTable.SetGanonRequirementText(f"You need to complete all the dungeons and bosses to defeat Ganon.")
        else:
            self.stringTable.SetGanonRequirementText(f"You need {ganonCrystals} crystals to defeat Ganon.")

    def WriteRngBlock(self):
        #/* Repoint RNG Block */
        self.patches.append((0x420000, [self.rnd.randrange(0, 0x100) for x in range(0, 1024)]))

    def WriteSaveAndQuitFromBossRoom(self):
        #/* Defaults to $00 at [asm]/z3/randomizer/tables.asm */
        self.patches.append((Snes(0x308042), [ 0x01 ]))

    def WriteWorldOnAgahnimDeath(self):
        pass
        #/* Defaults to $01 at [asm]/z3/randomizer/tables.asm */
        #// Todo: Z3r major glitches disables this, reconsider extending or dropping with glitched logic later.
        #//patches.Add((Snes(0x3080A3), new byte[] { 0x01 }));

def Snes(addr: int):
    #/* Redirect hi bank $30 access into ExHiRom lo bank $40 */
    if (addr & 0xFF8000) == 0x308000:
        addr = 0x400000 | (addr & 0x7FFF)
    else: #/* General case, add ExHi offset for banks < $80, and collapse mirroring */
        addr = (0x400000 if addr < 0x800000 else 0)| (addr & 0x3FFFFF)
    if (addr > 0x600000):
        raise Exception(f"Unmapped pc address target ${addr:x}")
    return addr

def getWord(w):
    return (w & 0x00FF, (w & 0xFF00) >> 8)

def getWordArray(w):
    return [w & 0x00FF, (w & 0xFF00) >> 8]

def getDoubleWordArray(w):
    return [w & 0x000000FF, (w & 0x0000FF00) >> 8, (w & 0x00FF0000) >> 16, (w & 0xFF000000) >> 24]

"""
    byte[] UintBytes(int value) => BitConverter.GetBytes((uint)value);

    byte[] UshortBytes(int value) => BitConverter.GetBytes((ushort)value);

    byte[] AsAscii(string text) => Encoding.ASCII.GetBytes(text);

}

}
"""
def SplitOff(source: List[Any], count: int):
    head = source[:count]
    tail = source[count:]
    return (head, tail)
